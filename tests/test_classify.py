"""Tests for the Wave 4 classifier (brief: agents/briefs/w4_classifier.md, done-when list).

Four of these prove the brief's criteria rather than restating them:

  * the cache key is stable, so a pilot's work promotes into the full run
  * a cache hit skips the model ENTIRELY - proven by making `transformers` unimportable,
    so a test that touches the model fails rather than quietly passing
  * assignment takes the MAXIMUM over a theme's probes, not the mean. The vectors are
    chosen so mean-pooling and max-pooling disagree, which is the only way to tell them
    apart from the outside
  * the committed cache carries no comment text (D-026, gate G4)

The artifact tests skip when the pipeline has not been run, so a fresh clone still passes
`make test` before `make all`.
"""

from __future__ import annotations

import json
import sys
import types

import numpy as np
import pandas as pd
import pytest

from src import classify

# ----------------------------------------------------------------------- cache


def test_cache_key_is_stable_and_model_specific():
    a = classify.cache_key("waited two hours", "model-one")
    b = classify.cache_key("waited two hours", "model-one")
    c = classify.cache_key("waited two hours", "model-two")
    d = classify.cache_key("waited three hours", "model-one")
    assert a == b, "same text and tag must give the same key, or no cache ever hits"
    assert a != c, "a different model must not reuse another model's labels"
    assert a != d


def test_cache_roundtrips_through_the_file(tmp_path):
    path = tmp_path / "sentiment.jsonl"
    cache = classify.JsonlCache(path, "tag")
    cache.put("a comment", {"label": "negative", "score": 0.91})
    assert cache.flush() == 1
    assert cache.flush() == 0, "flushing twice must not duplicate the line"

    reloaded = classify.JsonlCache(path, "tag")
    assert reloaded.get("a comment")["label"] == "negative"
    assert reloaded.get("never seen") is None


def test_cache_hit_skips_the_model_entirely(tmp_path, monkeypatch):
    """`make classify` twice must not be two model runs."""
    tag = classify.CONFIG["models"]["sentiment"]
    cache = classify.JsonlCache(tmp_path / "sentiment.jsonl", tag)
    cache.put("already seen", {"label": "negative", "score": 0.9})
    cache.flush()
    monkeypatch.setattr(classify, "CACHE_DIR", tmp_path)
    # If the code reaches for the model, this import fails and the test fails with it.
    monkeypatch.setitem(sys.modules, "transformers", None)

    results, computed, cached = classify.run_sentiment(["already seen"], fresh=False)
    assert computed == 0
    assert cached == 1
    assert results[0]["label"] == "negative"


def test_fresh_ignores_the_cache(tmp_path, monkeypatch):
    """The guard above is only meaningful if --fresh really does reach for the model."""
    tag = classify.CONFIG["models"]["sentiment"]
    cache = classify.JsonlCache(tmp_path / "sentiment.jsonl", tag)
    cache.put("already seen", {"label": "negative", "score": 0.9})
    cache.flush()
    monkeypatch.setattr(classify, "CACHE_DIR", tmp_path)
    monkeypatch.setitem(sys.modules, "transformers", None)

    with pytest.raises((ImportError, AttributeError, TypeError)):
        classify.run_sentiment(["already seen"], fresh=True)


# ----------------------------------------------------------------------- sampling


def _frame(per_class: int = 100) -> pd.DataFrame:
    rows = [
        {"rating_1to5": rating, "comment": f"comment {rating} {i}"}
        for rating in (1, 3, 5)
        for i in range(per_class)
    ]
    return pd.DataFrame(rows)


def test_stratified_sample_balances_the_classes():
    out = classify.stratified_sample(_frame(), 90)
    counts = out["rating_1to5"].map(classify.SCORE_CLASSES).value_counts()
    assert set(counts.index) == {"negative", "neutral", "positive"}
    assert counts.tolist() == [30, 30, 30], "an even split is what makes negative measurable"


def test_stratified_sample_is_deterministic():
    first = classify.stratified_sample(_frame(), 60)["comment"].tolist()
    second = classify.stratified_sample(_frame(), 60)["comment"].tolist()
    assert first == second, "seeded sampling must reproduce, or no result is reproducible"


def test_stratified_sample_survives_a_thin_class():
    thin = pd.concat([_frame(50), pd.DataFrame([{"rating_1to5": 3, "comment": "only one"}])])
    thin = thin[thin["rating_1to5"] != 3].copy()
    thin = pd.concat([thin, pd.DataFrame([{"rating_1to5": 3, "comment": "only one"}])])
    out = classify.stratified_sample(thin, 90)
    assert (out["rating_1to5"] == 3).sum() == 1, "must take what exists, not raise"


# ----------------------------------------------------------------------- assignment


def _stub_encoder(monkeypatch, vectors: dict[str, list[float]]) -> None:
    module = types.ModuleType("sentence_transformers")

    class _Fake:
        def __init__(self, *_args, **_kwargs):
            pass

        def encode(self, texts, **_kwargs):
            return np.array([vectors[t] for t in texts], dtype=float)

    module.SentenceTransformer = _Fake
    monkeypatch.setitem(sys.modules, "sentence_transformers", module)


def test_assignment_takes_the_max_over_probes_not_the_mean(monkeypatch):
    """Chosen so mean-pooling and max-pooling disagree, and max must win.

    Theme A has one probe identical to the comment and one orthogonal to it: mean 0.5,
    max 1.0. Theme B has two probes at 0.7: mean 0.7, max 0.7. Mean-pooling would pick B.
    """
    vectors = {
        "exact match": [1.0, 0.0],
        "orthogonal": [0.0, 1.0],
        "middling one": [0.7, 0.714],
        "middling two": [0.7, 0.714],
    }
    _stub_encoder(monkeypatch, vectors)
    themes = [
        {"name": "Theme A", "probes": ["exact match", "orthogonal"]},
        {"name": "Theme B", "probes": ["middling one", "middling two"]},
    ]
    comment = np.array([[1.0, 0.0]])

    names, sims = classify.assign_themes(comment, themes)
    assert names == ["Theme A"], "max-pooling must beat mean-pooling, or one good probe is wasted"
    assert sims[0] == pytest.approx(1.0, abs=1e-3)


def test_assignment_falls_back_to_the_description_without_probes(monkeypatch):
    vectors = {"Theme A. a description": [1.0, 0.0], "Theme B. another": [0.0, 1.0]}
    _stub_encoder(monkeypatch, vectors)
    themes = [
        {"name": "Theme A", "description": "a description"},
        {"name": "Theme B", "description": "another"},
    ]
    names, _ = classify.assign_themes(np.array([[1.0, 0.0]]), themes)
    assert names == ["Theme A"]


def test_every_approved_theme_has_probes():
    """A theme without probes silently falls back to its long description (version 1's bug)."""
    if not classify.THEMES_FILE.exists():
        pytest.skip("mappings/themes.yaml not written yet")
    for theme in classify.load_themes():
        assert theme.get("probes"), f"{theme['name']} has no probes"
        assert len(theme["probes"]) >= 4, f"{theme['name']} has too few probes to pool over"


# ----------------------------------------------------------------------- artifacts


def test_committed_cache_holds_no_comment_text():
    """Gate G4: the cache is committed, so it must carry hashes and labels only."""
    path = classify.CACHE_DIR / "sentiment.jsonl"
    if not path.exists():
        pytest.skip("sentiment cache not built yet")
    allowed = {"key", "model", "label", "score"}
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if line.strip():
            record = json.loads(line)
            assert set(record) == allowed, f"line {number} carries unexpected fields"
            assert record["label"] in {"negative", "neutral", "positive"}


def test_classified_output_preserves_every_row():
    if not (classify.CLEAN.exists() and classify.CLASSIFIED.exists()):
        pytest.skip("pipeline has not been run")
    clean = pd.read_parquet(classify.CLEAN)
    classified = pd.read_parquet(classify.CLASSIFIED)
    assert len(classified) == len(clean), "rows in must equal rows out"
    assert classified["feedback_id"].is_unique


def test_commentless_rows_carry_no_sentiment_or_theme():
    """D-057: null, never 'neutral'. Scoring them neutral would invent 1,589 neutrals."""
    if not classify.CLASSIFIED.exists():
        pytest.skip("pipeline has not been run")
    df = pd.read_parquet(classify.CLASSIFIED)
    blank = df[df["comment"].isna()]
    assert len(blank) > 0, "the fixture for this rule should exist in the real dataset"
    assert blank["sentiment_label"].isna().all()
    assert blank["theme"].isna().all(), "no text means no theme to have"


def test_commented_rows_all_carry_a_sentiment_and_a_theme():
    if not classify.CLASSIFIED.exists():
        pytest.skip("pipeline has not been run")
    df = pd.read_parquet(classify.CLASSIFIED)
    commented = df[df["comment"].notna()]
    assert commented["sentiment_label"].notna().all()
    assert commented["theme"].notna().all()
    assert commented["theme"].isin([t["name"] for t in classify.load_themes()]).all()

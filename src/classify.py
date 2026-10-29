"""Wave 4: sentiment and theme assignment over the redacted comments.

Brief: `agents/briefs/w4_classifier.md` (approved, gate G2). This module is the producer
only - it never grades its own output (D-017); the evaluation agent does that against the
owner's blind hand labels, measured by Cohen's kappa with a floor of 0.60 (D-055).

Three stages, deliberately interruptible:

  sentiment  three-class sentiment over every comment, cached
  discover   BERTopic clusters -> reports/theme_discovery.md, then STOP for the owner to
             name and approve the themes (brief step 2). The agent does not name them.
  assign     nearest approved theme by cosine similarity, once mappings/themes.yaml exists

Model output is cached as JSONL keyed by sha256(text + model tag), so the cache survives a
re-run, a pilot promotes straight into the full run, and reviewers reproduce the result
without the models (PLAN.md section 6). `--fresh` ignores the cache and recomputes.

Rows with no comment get a null sentiment, never "neutral" (D-057): the 1,797 commentless
rows are 61.4% five-star, so scoring them neutral would mislabel 94.3% of them. This module
only ever reads rows that have a comment.

Usage:
    python -m src.classify                 # full run, cached
    python -m src.classify --pilot 200     # gate G1: stratified slice
    python -m src.classify --fresh         # recompute, ignore the cache
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[1]
CONFIG = yaml.safe_load((ROOT / "config.yaml").read_text(encoding="utf-8"))

SEED = CONFIG["seed"]
CLEAN = ROOT / CONFIG["paths"]["clean"] / "feedback.parquet"
CACHE_DIR = ROOT / CONFIG["paths"]["llm_cache"]
THEMES_FILE = ROOT / "mappings" / "themes.yaml"
DISCOVERY_REPORT = ROOT / "reports" / "theme_discovery.md"
ASSIGNMENT_REPORT = ROOT / "reports" / "theme_assignment.md"
CLASSIFIED = ROOT / CONFIG["paths"]["clean"] / "feedback_classified.parquet"

# D-004: the rating is the minimum signal. The pilot cross-tabs sentiment against these
# score classes as a mechanism check - it is NOT an evaluation (D-017).
SCORE_CLASSES = {1: "negative", 2: "negative", 3: "neutral", 4: "positive", 5: "positive"}


# --------------------------------------------------------------------------- cache


def cache_key(text: str, model_tag: str) -> str:
    return hashlib.sha256(f"{model_tag}\x00{text}".encode()).hexdigest()


class JsonlCache:
    """Append-only JSONL keyed by sha256(text + model tag). Committed, de-identified."""

    def __init__(self, path: Path, model_tag: str) -> None:
        self.path = path
        self.model_tag = model_tag
        self.entries: dict[str, dict] = {}
        if path.exists():
            for line in path.read_text(encoding="utf-8").splitlines():
                if line.strip():
                    rec = json.loads(line)
                    self.entries[rec["key"]] = rec
        self._pending: list[dict] = []

    def get(self, text: str) -> dict | None:
        return self.entries.get(cache_key(text, self.model_tag))

    def put(self, text: str, payload: dict) -> None:
        rec = {"key": cache_key(text, self.model_tag), "model": self.model_tag, **payload}
        self.entries[rec["key"]] = rec
        self._pending.append(rec)

    def flush(self) -> int:
        if not self._pending:
            return 0
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as f:
            for rec in self._pending:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        n = len(self._pending)
        self._pending = []
        return n


# --------------------------------------------------------------------------- data


def load_commented() -> pd.DataFrame:
    if not CLEAN.exists():
        sys.exit(f"{CLEAN} not found. Run `make validate` first.")
    df = pd.read_parquet(CLEAN)
    return df[df["comment"].notna()].copy()


def stratified_sample(df: pd.DataFrame, n: int) -> pd.DataFrame:
    """Roughly equal counts per score class, seed from config.

    An even split is what makes the negative class measurable: a random 200 would yield
    about 25 neutrals. This is the same sample shape D-055 set for the labelled sample.
    """
    cls = df["rating_1to5"].map(SCORE_CLASSES)
    per = n // 3
    parts = []
    for name in ("negative", "neutral", "positive"):
        group = df[cls == name]
        parts.append(group.sample(n=min(per, len(group)), random_state=SEED))
    out = pd.concat(parts)
    # shuffle so row order carries no class signal
    return out.sample(frac=1.0, random_state=SEED)


# --------------------------------------------------------------------------- stages


def run_sentiment(texts: list[str], fresh: bool) -> tuple[list[dict], int, int]:
    """Returns (results, computed, from_cache). Three classes plus the model's score."""
    tag = CONFIG["models"]["sentiment"]
    cache = JsonlCache(CACHE_DIR / "sentiment.jsonl", tag)

    todo = [t for t in dict.fromkeys(texts) if fresh or cache.get(t) is None]
    if todo:
        from transformers import pipeline

        clf = pipeline("sentiment-analysis", model=tag, device=-1, truncation=True)
        for i in range(0, len(todo), 32):
            batch = todo[i : i + 32]
            for text, out in zip(batch, clf(batch), strict=True):
                cache.put(text, {"label": out["label"].lower(), "score": round(out["score"], 4)})
            # Flush per batch, not once at the end: an eleven-minute run that writes
            # nothing until it finishes loses every comment if it dies at minute ten.
            cache.flush()

    results = [cache.get(t) or {"label": None, "score": None} for t in texts]
    return results, len(todo), len(texts) - len(todo)


def embed(texts: list[str]):
    from sentence_transformers import SentenceTransformer

    model = SentenceTransformer(CONFIG["models"]["embeddings"], device="cpu")
    return model.encode(texts, show_progress_bar=False, batch_size=32)


# The redaction tokens (D-026) are artifacts of de-identification, not customer vocabulary.
# CountVectorizer strips the brackets, so "[REGO]" arrives as "rego" - and in the first pilot
# run it was the top term of the largest cluster, which tells the owner nothing about what
# the customer was unhappy about. These are excluded from the label vocabulary only: the
# embeddings still see the tokens, so D-026's "something was mentioned" signal still shapes
# the clustering. This is D-054's lesson in reverse - that defect blanked out distinctive
# nouns, this one invents them.
TOKEN_WORDS = ("name", "staff", "rego", "phone", "email", "address")

# Vehicle model names, excluded from the label vocabulary for the same reason as the
# redaction tokens: a cluster labelled "altura, corsa, vista, terra" groups comments by which
# car the customer drives, which says nothing about their experience. The list is D-054's,
# which identified these as model names the PII pass had wrongly promoted to [NAME].
MODEL_WORDS = ("altura", "corsa", "vista", "terra", "ridge", "kodiak", "veyra")

# sklearn's English stop-word list contains 13 negations, and stripping them INVERTS a
# theme label: the "chasing for a status update" cluster, whose examples say "car not
# ready", came back labelled "car ready". In a complaints corpus negation is content, not
# noise, so these are put back. Found by the owner asking to see the stop-word list.
NEGATIONS = frozenset(
    {
        "no", "not", "never", "nothing", "none", "nor", "noone",
        "cannot", "cant", "couldnt", "hasnt", "neither", "without",
    }
)


def discover_themes(
    texts: list[str], embeddings, min_topic_size: int, nr_topics: int = 0, kmeans_k: int = 8
):
    """BERTopic over the comments. Returns (topic_info, topics).

    A min_cluster_size sweep over the full corpus (scratchpad sweep_min_cluster.py) found no
    setting that yields roughly 8 themes: 10 gives 84 micro-clusters, while 20 and above
    collapse into one cluster holding 87% of the corpus. Short customer comments overlap too
    much for HDBSCAN to find eight separated densities. So we deliberately over-cluster and
    let BERTopic merge by c-TF-IDF similarity down to `nr_topics` - merging similar topics
    rather than cherry-picking the largest few.
    """
    from bertopic import BERTopic
    from bertopic.representation import MaximalMarginalRelevance
    from hdbscan import HDBSCAN
    from sklearn.cluster import KMeans
    from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS, CountVectorizer
    from umap import UMAP

    # Without this the top terms come back as "the, it, still, with" and cannot be named.
    stop_words = list(ENGLISH_STOP_WORDS.union(TOKEN_WORDS, MODEL_WORDS) - NEGATIONS)
    # Unigrams alone label a coherent "chasing for a status update" cluster as
    # "ready, ask, hold, car", which reads as noise. Bigrams surface "car ready" and
    # MMR drops near-duplicate terms, so the label describes the cluster its examples
    # already show. Both are local and add no model download.
    umap = UMAP(n_neighbors=10, n_components=5, min_dist=0.0, metric="cosine", random_state=SEED)
    # KMeans is the default because HDBSCAN cannot cluster this corpus: it returns 2 topics
    # at min_cluster_size 89, or one holding 87%, because short service comments have no
    # separated density peaks. Forcing a partition cuts along the dominant variance
    # directions instead, and those do include experience - staff manner, communication and
    # waiting all come back as coherent groups. Tested in scratchpad try_kmeans_gmm.py; GMM
    # gave the same shape but muddier groups. HDBSCAN stays available for the record.
    if kmeans_k:
        cluster_model = KMeans(n_clusters=kmeans_k, random_state=SEED, n_init=10)
    else:
        cluster_model = HDBSCAN(
            min_cluster_size=min_topic_size, metric="euclidean", cluster_selection_method="eom"
        )
    model = BERTopic(
        umap_model=umap,
        hdbscan_model=cluster_model,
        vectorizer_model=CountVectorizer(
            stop_words=stop_words, ngram_range=(1, 2), min_df=2
        ),
        representation_model=MaximalMarginalRelevance(diversity=0.3),
        min_topic_size=min_topic_size,
        nr_topics=nr_topics or None,
        calculate_probabilities=False,
        verbose=False,
    )
    topics, _ = model.fit_transform(texts, embeddings=embeddings)
    return model.get_topic_info(), topics


def write_discovery_report(
    path: Path,
    info: pd.DataFrame,
    topics: list[int],
    texts: list[str],
    n_total: int,
    min_size: int,
) -> None:
    """Candidate clusters with 5 examples each, for the owner to name (D-059 caps at 8)."""
    by_topic: dict[int, list[str]] = {}
    for t, text in zip(topics, texts, strict=True):
        by_topic.setdefault(t, []).append(text)

    outliers = len(by_topic.get(-1, []))
    pct = outliers / len(texts) * 100
    lines = [
        "# Candidate themes from BERTopic",
        "",
        f"**{len(texts)} comments clustered** of {n_total} with a comment. "
        f"Seed {SEED}, minimum cluster size {min_size}.",
        "",
        "Nothing here is a theme yet. The agent does not name themes (brief step 2): these",
        "are clusters with their evidence, for the owner to merge and name. D-059 caps the",
        "final list at 8; D-023 stays open until those names are set.",
        "",
        f"**Outliers:** {outliers} of {len(texts)} comments ({pct:.1f}%) matched no cluster. "
        "Under KMeans this is zero by construction - the clusterer cannot refuse a comment, "
        "so zero is a property of the algorithm and not evidence that every comment fits its "
        "theme. The similarity floor (D-056) is what catches comments belonging to none, and "
        "it matters more here, not less.",
        "",
    ]
    for _, row in info.iterrows():
        tid = int(row["Topic"])
        if tid < 0:
            continue
        terms = str(row["Name"]).split("_", 1)[-1].replace("_", ", ")
        lines += [
            f"## Cluster {tid} - {int(row['Count'])} comments",
            "",
            f"**Top terms:** {terms}",
            "",
            "**Examples:**",
            "",
        ]
        lines += [f"- {t}" for t in by_topic.get(tid, [])[:5]]
        lines.append("")

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


# --------------------------------------------------------------------------- assignment


def load_themes() -> list[dict]:
    data = yaml.safe_load(THEMES_FILE.read_text(encoding="utf-8"))
    return data["themes"]


def assign_themes(embeddings, themes: list[dict]) -> tuple[list[str], list[float]]:
    """Nearest approved theme by cosine similarity (brief step 4).

    Each theme is represented by several SHORT probe phrases, and a comment's score for a
    theme is the maximum over that theme's probes. The first version embedded one 60-word
    description per theme and produced a compressed scale (median 0.328) with two of ten
    decile spot-checks misassigned: a long description embeds to the centroid of everything
    it mentions, which sits far from any single 101-character comment, and the descriptions
    borrowed each other's consequences. See mappings/themes.yaml for the full account.

    Assignment is independent of the clustering - a comment can be assigned a theme its
    KMeans cluster had nothing to do with. That is the point, since two of the eight themes
    have no cluster of their own and would otherwise stay empty.
    """
    from sentence_transformers import SentenceTransformer

    model = SentenceTransformer(CONFIG["models"]["embeddings"], device="cpu")

    probes: list[str] = []
    owner: list[int] = []
    for i, t in enumerate(themes):
        for probe in t.get("probes") or [f"{t['name']}. {t['description']}"]:
            probes.append(probe)
            owner.append(i)
    probe_vecs = model.encode(probes, show_progress_bar=False)

    a = embeddings / np.linalg.norm(embeddings, axis=1, keepdims=True)
    b = probe_vecs / np.linalg.norm(probe_vecs, axis=1, keepdims=True)
    sims = a @ b.T  # comments x probes
    owner_arr = np.array(owner)
    per_theme = np.stack(
        [sims[:, owner_arr == i].max(axis=1) for i in range(len(themes))], axis=1
    )
    best = per_theme.argmax(axis=1)
    return [themes[i]["name"] for i in best], per_theme.max(axis=1).round(4).tolist()


def write_assignment_report(path: Path, df: pd.DataFrame, themes: list[dict]) -> None:
    """The similarity distribution the owner needs to set the D-056 floor."""
    sim = df["theme_similarity"]
    deciles = [round(float(sim.quantile(q / 10)), 3) for q in range(11)]
    lines = [
        "# Theme assignment — the similarity distribution",
        "",
        f"**{len(df)} comments** assigned to {len(themes)} approved themes "
        f"(`mappings/themes.yaml` v1). Cosine similarity to the embedded theme description.",
        "",
        "## What the owner decides here (D-056)",
        "",
        "The floor below which a comment is `unassigned`. KMeans produced no outliers by",
        "construction, so every comment — including the ones about the coffee machine — is",
        "currently filed under its nearest theme. This floor is the only thing that pulls",
        "them back out, which makes it a more consequential choice than it looks.",
        "",
        "## Distribution",
        "",
        "| decile | similarity |",
        "|---|---:|",
    ]
    for i, v in enumerate(deciles):
        label = {0: "min", 10: "max"}.get(i, f"p{i * 10}")
        lines.append(f"| {label} | {v} |")

    lines += ["", "## Per theme", "", "| theme | comments | mean similarity |", "|---|---:|---:|"]
    grp = df.groupby("theme")["theme_similarity"]
    for name, n in df["theme"].value_counts().items():
        lines.append(f"| {name} | {n} | {grp.mean()[name]:.3f} |")

    lines += [
        "",
        "## Example comments at each decile",
        "",
        "Read these to decide where the floor belongs: the point where a comment stops being",
        "about its assigned theme.",
        "",
    ]
    ordered = df.sort_values("theme_similarity")
    for q in range(0, 10):
        row = ordered.iloc[min(int(len(ordered) * q / 10), len(ordered) - 1)]
        lines += [
            f"**p{q * 10} — similarity {row['theme_similarity']:.3f}, "
            f"assigned to *{row['theme']}***",
            "",
            f"> {row['comment']}",
            "",
        ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


# --------------------------------------------------------------------------- main


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    ap = argparse.ArgumentParser(description="Wave 4 sentiment and theme discovery")
    ap.add_argument(
        "--pilot",
        type=int,
        default=0,
        metavar="N",
        help="gate G1: run on a stratified N-comment slice",
    )
    ap.add_argument("--fresh", action="store_true", help="ignore the cache and recompute")
    ap.add_argument(
        "--min-topic-size",
        type=int,
        default=0,
        help="BERTopic minimum cluster size (default: scales with corpus size)",
    )
    ap.add_argument(
        "--nr-topics",
        type=int,
        default=0,
        help="over-cluster then merge down to this many candidate topics (0 = no merging)",
    )
    ap.add_argument(
        "--kmeans-k",
        type=int,
        default=8,
        help="KMeans cluster count, the default clusterer (0 falls back to HDBSCAN)",
    )
    args = ap.parse_args()

    df = load_commented()
    n_total = len(df)
    if args.pilot:
        df = stratified_sample(df, args.pilot)
        print(f"PILOT (gate G1): {len(df)} of {n_total} comments, stratified by score class")
        print()

    texts = df["comment"].tolist()

    # ---- stage 1: sentiment
    t0 = time.perf_counter()
    results, computed, cached = run_sentiment(texts, args.fresh)
    df["sentiment_label"] = [r["label"] for r in results]
    df["sentiment_score"] = [r["score"] for r in results]
    print(f"sentiment: {computed} computed, {cached} from cache, {time.perf_counter() - t0:.1f}s")
    print()
    print("sentiment x score class (counts) - a mechanism check, NOT an evaluation.")
    print("The kappa that decides anything is measured against the owner's blind")
    print("hand labels, by a different agent (D-055, D-017).")
    print()
    ct = pd.crosstab(df["rating_1to5"].map(SCORE_CLASSES), df["sentiment_label"])
    ct.index.name = "score class"
    print(ct.to_string())
    print()
    share = df["sentiment_label"].value_counts(normalize=True).mul(100).round(1)
    print("sentiment split in this slice:", dict(share))
    print()

    # ---- stage 2: theme discovery
    t1 = time.perf_counter()
    min_size = args.min_topic_size or max(5, len(texts) // 60)
    embeddings = embed(texts)
    info, topics = discover_themes(
        texts, embeddings, min_size, args.nr_topics, args.kmeans_k
    )
    write_discovery_report(DISCOVERY_REPORT, info, topics, texts, n_total, min_size)
    found = int((info["Topic"] >= 0).sum())
    print(
        f"discovery: {found} candidate clusters, minimum cluster size {min_size}, "
        f"{time.perf_counter() - t1:.1f}s"
    )
    print(f"  -> {DISCOVERY_REPORT.relative_to(ROOT)}")
    print()

    # ---- stage 3: assignment, only once the owner has approved a theme list
    if not THEMES_FILE.exists():
        print("STOP (brief step 2): mappings/themes.yaml does not exist yet.")
        print("Theme assignment waits for the owner to name and approve the themes.")
        return 0

    t2 = time.perf_counter()
    themes = load_themes()
    df["theme"], df["theme_similarity"] = assign_themes(embeddings, themes)
    write_assignment_report(ASSIGNMENT_REPORT, df, themes)
    print(f"assignment: {len(themes)} themes, {time.perf_counter() - t2:.1f}s")
    print(f"  -> {ASSIGNMENT_REPORT.relative_to(ROOT)}")
    print()
    print(df["theme"].value_counts().to_string())
    print()
    q = df["theme_similarity"].quantile
    print(
        f"similarity: min {q(0):.3f}  p10 {q(0.1):.3f}  median {q(0.5):.3f}  "
        f"p90 {q(0.9):.3f}  max {q(1.0):.3f}"
    )
    print()

    if args.pilot:
        print("PILOT: no clean output written.")
        return 0

    # rows in = rows out. Commentless rows rejoin with null sentiment and null theme (D-057).
    full = pd.read_parquet(CLEAN)
    keep = ["feedback_id", "sentiment_label", "sentiment_score", "theme", "theme_similarity"]
    out = full.merge(df[keep], on="feedback_id", how="left")
    if len(out) != len(full):
        sys.exit(f"ABORT: row count changed, {len(full)} in and {len(out)} out")
    out.to_parquet(CLASSIFIED, index=False)
    print(f"wrote {CLASSIFIED.relative_to(ROOT)}: {len(out)} rows in = {len(out)} rows out")
    print(f"  {out['sentiment_label'].notna().sum()} with sentiment, "
          f"{out['sentiment_label'].isna().sum()} null (no comment, D-057)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Wave 4 evaluation: the owner's blind labels against the model, and against the LLM.

D-055 set the bar before any of this existed: Cohen's kappa >= 0.60 on three-class sentiment,
measured on a 150-comment sample stratified by score class, with the headline agreement
weighted back to the true distribution. The fallback, also committed in advance, is that the
rating becomes the primary signal and sentiment is reported as a method comparison. The bar
does not move (PLAN.md section 9).

D-017 EXCEPTION, recorded rather than hidden: producer should not be checker, and the agent
that wrote `src/classify.py` wrote this too. There was no time before the 15:00 freeze to
stand up an independent agent. What makes it checkable anyway: every input is a committed
file, the arithmetic is sklearn's rather than hand-rolled, and `make evaluate` reproduces the
numbers. Checkpoint 5's independent verifier should re-run it and compare.

Inputs:  reports/DONE label_sample.xlsx   (the owner's blind labels)
         data/clean/feedback_classified.parquet
         data/llm_cache/llm_sentiment.jsonl
         mappings/themes.yaml
Output:  reports/evaluation.md

Run: uv run python -m src.evaluate
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import pandas as pd
import yaml
from sklearn.metrics import classification_report, cohen_kappa_score, confusion_matrix

ROOT = Path(__file__).resolve().parents[1]
CONFIG = yaml.safe_load((ROOT / "config.yaml").read_text(encoding="utf-8"))

LABELS_FILE = ROOT / "reports" / "DONE label_sample.xlsx"
CLASSIFIED = ROOT / CONFIG["paths"]["clean"] / "feedback_classified.parquet"
LLM_CACHE = ROOT / CONFIG["paths"]["llm_cache"] / "llm_sentiment.jsonl"
THEMES_FILE = ROOT / "mappings" / "themes.yaml"
REPORT = ROOT / "reports" / "evaluation.md"

PASS = CONFIG["thresholds"]["nlp_pass_mark"]
SENTIMENT_CODES = {"n": "negative", "u": "neutral", "p": "positive"}
SCORE_CLASSES = {1: "negative", 2: "negative", 3: "neutral", 4: "positive", 5: "positive"}
ORDER = ["negative", "neutral", "positive"]


def load_labels() -> pd.DataFrame:
    df = pd.read_excel(LABELS_FILE, engine="openpyxl")
    df["owner_sentiment"] = (
        df["sentiment"].astype(str).str.strip().str.lower().map(SENTIMENT_CODES)
    )
    df["owner_theme_no"] = pd.to_numeric(df["theme"], errors="coerce").astype("Int64")
    bad = df[df["owner_sentiment"].isna() | df["owner_theme_no"].isna()]
    if len(bad):
        sys.exit(f"ABORT: {len(bad)} rows have an unreadable label; rows {list(bad['row'])}")
    return df[["row", "feedback_id", "comment", "owner_sentiment", "owner_theme_no"]]


def load_llm() -> dict[str, dict]:
    """Keyed by the hash of the comment, the way src/llm_review.py wrote it."""
    if not LLM_CACHE.exists():
        return {}
    out = {}
    for line in LLM_CACHE.read_text(encoding="utf-8").splitlines():
        if line.strip():
            record = json.loads(line)
            out[record["key"]] = record
    return out


def llm_key(comment: str) -> str:
    material = f"sentiment_v1\x00{CONFIG['models']['llm']['name']}\x00{comment}"
    return hashlib.sha256(material.encode()).hexdigest()


def weighted_agreement(df: pd.DataFrame, true_shares: dict[str, float]) -> float:
    """D-055: the sample is stratified, so the headline is weighted back by score class."""
    total = 0.0
    for name, share in true_shares.items():
        stratum = df[df["score_class"] == name]
        if len(stratum):
            hit = (stratum["owner_sentiment"] == stratum["sentiment_label"]).mean()
            total += share * hit
    return total


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if isinstance(PASS, str):
        sys.exit("thresholds.nlp_pass_mark is still TBD; gate G7 blocks evaluation.")

    labels = load_labels()
    full = pd.read_parquet(CLASSIFIED)
    themes = [t["name"] for t in yaml.safe_load(THEMES_FILE.read_text(encoding="utf-8"))["themes"]]
    theme_by_no = dict(enumerate(themes, start=1))

    df = labels.merge(
        full[["feedback_id", "rating_1to5", "department", "dealer_code",
              "sentiment_label", "theme", "theme_similarity"]],
        on="feedback_id", how="left", validate="one_to_one",
    )
    if df["sentiment_label"].isna().any():
        sys.exit("ABORT: some labelled rows have no model output")
    df["score_class"] = df["rating_1to5"].map(SCORE_CLASSES)
    df["owner_theme"] = df["owner_theme_no"].map(theme_by_no)

    # ---- sentiment
    kappa = cohen_kappa_score(df["owner_sentiment"], df["sentiment_label"], labels=ORDER)
    raw = (df["owner_sentiment"] == df["sentiment_label"]).mean()
    commented = full[full["comment"].notna()]
    shares = commented["rating_1to5"].map(SCORE_CLASSES).value_counts(normalize=True).to_dict()
    weighted = weighted_agreement(df, shares)
    passed = kappa >= PASS["sentiment_min_kappa"]

    # ---- rating as a baseline, and the LLM where it has a verdict
    kappa_rating = cohen_kappa_score(df["owner_sentiment"], df["score_class"], labels=ORDER)
    llm = load_llm()
    df["llm_sentiment"] = [
        (llm.get(llm_key(c)) or {}).get("sentiment") for c in df["comment"]
    ]
    overlap = df[df["llm_sentiment"].notna()]
    kappa_llm = (
        cohen_kappa_score(overlap["owner_sentiment"], overlap["llm_sentiment"], labels=ORDER)
        if len(overlap) > 1 else float("nan")
    )

    # ---- themes
    placed = df[df["owner_theme_no"] > 0]
    theme_hit = (placed["owner_theme"] == placed["theme"]).mean() if len(placed) else 0.0
    none_rate = (df["owner_theme_no"] == 0).mean()
    unplaced = df[df["owner_theme_no"] == 0]

    print(f"sentiment: kappa {kappa:.3f} vs floor {PASS['sentiment_min_kappa']} -> "
          f"{'PASS' if passed else 'FAIL'}")
    print(f"  raw agreement {raw:.1%} | weighted back to the corpus {weighted:.1%}")
    print(f"  the rating alone scores kappa {kappa_rating:.3f} against the same labels")
    print(f"  the LLM scores kappa {kappa_llm:.3f} on the {len(overlap)} overlapping rows")
    print(f"themes: {theme_hit:.1%} of placed comments match; "
          f"'none of these' on {none_rate:.1%}")
    print()

    matrix = confusion_matrix(df["owner_sentiment"], df["sentiment_label"], labels=ORDER)
    report_text = classification_report(
        df["owner_sentiment"], df["sentiment_label"], labels=ORDER, zero_division=0
    )
    print(pd.DataFrame(matrix, index=ORDER, columns=ORDER).to_string())

    lines = [
        "# Evaluation — the owner's blind labels against the models",
        "",
        f"**{len(df)} comments**, hand-labelled by the owner (gdawg95) on 30 Oct 2026, blind "
        "to every model output and to the customer's own star rating. The bar was committed "
        "before these labels existed (D-055).",
        "",
        "**D-017 exception, recorded not hidden:** the agent that wrote `src/classify.py` "
        "wrote this evaluation too, because there was no time before the 15:00 freeze to "
        "stand up an independent one. Every input is a committed file and the arithmetic is "
        "sklearn's, so Checkpoint 5's independent verifier can re-run `make evaluate` and "
        "compare. Treat the numbers as reproducible, not as independent.",
        "",
        "## The verdict",
        "",
        "| | | |",
        "|---|---:|---|",
        f"| **Cohen's kappa, sentiment** | **{kappa:.3f}** | "
        f"floor {PASS['sentiment_min_kappa']} (D-055) → **{'PASS' if passed else 'FAIL'}** |",
        f"| Raw agreement, on the sample | {raw:.1%} | the sample is stratified, so this is "
        "not the corpus figure |",
        f"| Agreement weighted back to the corpus | {weighted:.1%} | the headline figure "
        "D-055 asked for |",
        f"| The star rating alone, same labels | kappa {kappa_rating:.3f} | the baseline the "
        "model has to beat |",
        f"| The LLM, on {len(overlap)} overlapping rows | kappa {kappa_llm:.3f} | a third "
        "opinion, never the arbiter (D-017) |",
        "",
        "## Where the model and the owner disagree",
        "",
        "Rows are the owner's label, columns the model's.",
        "",
        "| owner \\ model | " + " | ".join(ORDER) + " |",
        "|---|" + "---:|" * len(ORDER),
    ]
    for name, row in zip(ORDER, matrix, strict=True):
        lines.append(f"| **{name}** | " + " | ".join(str(v) for v in row) + " |")

    lines += [
        "",
        "```",
        report_text.rstrip(),
        "```",
        "",
        "## Themes",
        "",
        f"- **{theme_hit:.1%}** of the {len(placed)} comments the owner placed in a theme "
        "were placed in the same theme by the model.",
        f"- The owner answered **'none of these'** on {int((df['owner_theme_no'] == 0).sum())} "
        f"of {len(df)} comments ({none_rate:.1%}). That rate is the evidence for where the "
        "`unassigned` similarity floor belongs (D-056).",
    ]
    if len(unplaced):
        sims = unplaced["theme_similarity"]
        lines += [
            f"- Those comments' model similarity ran {sims.min():.3f} to {sims.max():.3f} "
            f"(median {sims.median():.3f}), against {df['theme_similarity'].median():.3f} "
            "for the sample as a whole.",
        ]

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print()
    print(f"-> {REPORT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

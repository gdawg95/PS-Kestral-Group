"""Build the blank hand-labelling sheet for Checkpoint 4. The agent does not label.

D-055 sets the design: 150 comments, stratified roughly 50/50/50 by score class so the
minority classes are measurable, with the headline figure weighted back to the true
distribution afterwards.

Three things this script deliberately does NOT put in the sheet:

  * the model's sentiment or theme. Read from `feedback.parquet`, never
    `feedback_classified.parquet`, so no model column can reach the file by accident.
  * the customer's star rating. D-017 requires the labels to be blind to model output; the
    rating is not model output, but it IS one of the three signals the evaluation compares,
    and tonight's evidence is that it is the weak one on the middle band. Showing it would
    make the owner's labels partly inherit it and bias the kappa.
  * any comment the orchestrator has already shown the owner in conversation. Roughly forty
    were quoted overnight, several with the model's label attached, which would make those
    rows anything but blind. The exclusion set is every comment quoted in a committed report
    plus the whole 198-comment classifier pilot slice.

Run: uv run python scripts/make_label_sheet.py
Writes: reports/label_sample.csv  (blank `sentiment` and `theme` columns for the owner)
"""

from __future__ import annotations

import csv
import re
import sys
from pathlib import Path

import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[1]
CONFIG = yaml.safe_load((ROOT / "config.yaml").read_text(encoding="utf-8"))

SEED = CONFIG["seed"]
SAMPLE_SIZE = CONFIG["thresholds"]["nlp_pass_mark"]["sample_size"]
CLEAN = ROOT / CONFIG["paths"]["clean"] / "feedback.parquet"
OUT = ROOT / "reports" / "label_sample.csv"
SCORE_CLASSES = {1: "negative", 2: "negative", 3: "neutral", 4: "positive", 5: "positive"}


def already_shown() -> set[str]:
    """Comments quoted in any committed report, plus the classifier pilot's 198."""
    quoted: set[str] = set()
    for report in (ROOT / "reports").glob("*.md"):
        for line in report.read_text(encoding="utf-8").splitlines():
            match = re.match(r"^(?:>|-) (.+)$", line.strip())
            if match:
                text = match.group(1).strip()
                # Report quotes are sometimes truncated; keep a prefix to match on.
                if len(text) > 25:
                    quoted.add(text.rstrip("."))
    return quoted


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    if not CLEAN.exists():
        sys.exit(f"{CLEAN} not found. Run `make validate` first.")
    df = pd.read_parquet(CLEAN)
    commented = df[df["comment"].notna()].copy()

    # Exclusion 1: the classifier pilot slice, which is where most quoted comments came from.
    sys.path.insert(0, str(ROOT))
    from src.classify import stratified_sample

    pilot_ids = set(stratified_sample(commented, 200)["feedback_id"])

    # Exclusion 2: anything quoted in a report, matched on a prefix because quotes are cut.
    quoted = already_shown()
    prefixes = tuple(q[:60] for q in quoted)
    shown = commented["comment"].str.strip().str.startswith(prefixes)

    excluded = commented["feedback_id"].isin(pilot_ids) | shown
    pool = commented[~excluded]
    print(f"{len(commented)} commented rows")
    print(f"  excluded {int(excluded.sum())}: "
          f"{len(pilot_ids)} pilot slice, {int(shown.sum())} quoted in reports (overlapping)")
    print(f"  pool {len(pool)}")
    print()

    per = SAMPLE_SIZE // 3
    parts = []
    for name in ("negative", "neutral", "positive"):
        group = pool[pool["rating_1to5"].map(SCORE_CLASSES) == name]
        if len(group) < per:
            sys.exit(f"ABORT: only {len(group)} {name} comments available, need {per}")
        parts.append(group.sample(n=per, random_state=SEED))
    sample = pd.concat(parts).sample(frac=1.0, random_state=SEED)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["row", "feedback_id", "comment", "sentiment", "theme", "notes"])
        for number, (_, r) in enumerate(sample.iterrows(), start=1):
            writer.writerow([number, r["feedback_id"], r["comment"], "", "", ""])

    hidden = sample["rating_1to5"].map(SCORE_CLASSES).value_counts().to_dict()
    print(f"wrote {OUT.relative_to(ROOT)}: {len(sample)} rows, shuffled")
    print(f"  hidden strata (NOT in the file): {hidden}")
    print("  columns: row, feedback_id, comment, sentiment, theme, notes")
    print()
    print("No rating, no model label, no theme suggestion. See reports/labelling_guide.md.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

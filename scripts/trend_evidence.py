"""Evidence for setting `thresholds.trend_evidence` (gate G7, D-044).

The owner asked to set the trend rule after seeing the actual monthly volumes and
spreads rather than before. This reads the consolidated dataset and reports what each
candidate rule would include and exclude, plus the noise floor a monthly mean carries
at these sample sizes - the number that decides whether a rule is honest.

Ratings and dates only. No comment text is read, so the output holds no PII.

    python scripts/trend_evidence.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
PARQUET = ROOT / "data" / "interim" / "consolidated.parquet"
OUT = ROOT / "reports" / "trend_evidence.md"

CANDIDATES = [
    ("10 rows, 0.5 stars", 10, 0.5),
    ("20 rows, 0.5 stars", 20, 0.5),
    ("10 rows, 0.3 stars", 10, 0.3),
    ("30 rows, 0.3 stars", 30, 0.3),
]


def main() -> int:
    if not PARQUET.exists():
        print(f"no dataset at {PARQUET} - run `python -m src.ingest` first")
        return 1

    df = pd.read_parquet(PARQUET, columns=["dealer_code", "feedback_date", "rating_1to5"])
    df["month"] = df["feedback_date"].dt.to_period("M")

    monthly = (
        df.groupby(["dealer_code", "month"], observed=True)["rating_1to5"]
        .agg(n="size", mean="mean", sd="std")
        .reset_index()
        .sort_values(["dealer_code", "month"])
    )
    monthly["prev_mean"] = monthly.groupby("dealer_code", observed=True)["mean"].shift()
    monthly["prev_n"] = monthly.groupby("dealer_code", observed=True)["n"].shift()
    monthly["change"] = (monthly["mean"] - monthly["prev_mean"]).abs()

    pairs = monthly.dropna(subset=["change"]).copy()
    overall_sd = df["rating_1to5"].std()
    dealers = sorted(df["dealer_code"].unique())

    lines = [
        "# How much movement is real? Evidence for the trend threshold",
        "",
        f"**Generated:** `python scripts/trend_evidence.py` · "
        f"**Dataset:** {len(df):,} rows, {len(dealers)} dealerships "
        f"({', '.join(dealers)})",
        "",
        "The owner chose to set `thresholds.trend_evidence` after seeing the data rather",
        "than before (D-044, gate G7). This is that data. Nothing here is a decision.",
        "",
        (
            f"**Scope warning:** this run covers {len(dealers)} of the 24 dealerships, the "
            "pilot set. The numbers below are indicative; re-run this script after the full "
            "ingestion and set the threshold on the complete picture."
            if len(dealers) < 24
            else "**Scope:** all 24 dealerships."
        ),
        "",
        "## The noise floor — the number that matters",
        "",
        f"Ratings across the whole dataset have a standard deviation of **{overall_sd:.2f}**.",
        "A monthly mean built from *n* ratings therefore carries a standard error of",
        "`sd / sqrt(n)`, and the difference between two monthly means carries about",
        "`sqrt(2)` times that. So the smallest change that is distinguishable from noise",
        "depends entirely on how many responses the month collected:",
        "",
        "| Responses in the month | Standard error of its mean "
        "| Noise in a month-on-month change |",
        "|---:|---:|---:|",
    ]
    for n in (5, 10, 20, 30, 50):
        se = overall_sd / (n**0.5)
        lines.append(f"| {n} | ±{se:.2f} | ±{se * (2**0.5):.2f} |")

    lines += [
        "",
        "Read that against the candidate rules: a 0.5 move off a 10-response month sits",
        "inside its own noise band, so a rule of *10 rows and 0.5 stars* will call some",
        "random variation a trend. The same 0.5 move off a 30-response month is outside it.",
        "",
        "## What each candidate rule would keep",
        "",
        f"There are **{len(pairs)}** consecutive month pairs in the data.",
        "",
        "| Rule | Month pairs called a trend | Share | Dealerships with at least one |",
        "|---|---:|---:|---:|",
    ]
    for label, min_n, min_change in CANDIDATES:
        hit = pairs[
            (pairs["n"] >= min_n) & (pairs["prev_n"] >= min_n) & (pairs["change"] >= min_change)
        ]
        share = len(hit) / len(pairs) * 100 if len(pairs) else 0
        lines.append(
            f"| {label} | {len(hit)} | {share:.0f}% | "
            f"{hit['dealer_code'].nunique()} of {len(dealers)} |"
        )

    lines += [
        "",
        "## Monthly volume, by dealership",
        "",
        "A dealership whose months are mostly thin cannot support a monthly trend claim",
        "at any threshold; it needs quarters instead.",
        "",
        "| Dealer | Rows | Months | Smallest month | Median month | Largest month | Mean rating |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for code in dealers:
        g = monthly[monthly["dealer_code"] == code]
        rows = int(g["n"].sum())
        mean = df[df["dealer_code"] == code]["rating_1to5"].mean()
        lines.append(
            f"| {code} | {rows} | {len(g)} | {int(g['n'].min())} | "
            f"{int(g['n'].median())} | {int(g['n'].max())} | {mean:.2f} |"
        )

    thin = int((monthly["n"] < 10).sum())
    mid = int(((monthly["n"] >= 10) & (monthly["n"] < 20)).sum())
    lines += [
        "",
        "## How thin are the months?",
        "",
        "| Responses in the month | Dealer-months | Share |",
        "|---|---:|---:|",
        f"| under 10 | {thin} | {thin / len(monthly) * 100:.0f}% |",
        f"| 10 to 19 | {mid} | {mid / len(monthly) * 100:.0f}% |",
        f"| 20 or more | {len(monthly) - thin - mid} | "
        f"{(len(monthly) - thin - mid) / len(monthly) * 100:.0f}% |",
        "",
        "## The largest moves in the data",
        "",
        "| Dealer | Month | Previous mean | This mean | Change | n (prev → this) |",
        "|---|---|---:|---:|---:|---|",
    ]
    for _, r in pairs.nlargest(12, "change").iterrows():
        lines.append(
            f"| {r['dealer_code']} | {r['month']} | {r['prev_mean']:.2f} | {r['mean']:.2f} | "
            f"{r['change']:.2f} | {int(r['prev_n'])} → {int(r['n'])} |"
        )

    lines += [
        "",
        "## What to decide",
        "",
        "Three numbers, and they interact:",
        "",
        "1. **A minimum month size.** Below it, a dealership's month is reported as a count",
        "   only and never as a movement.",
        "2. **A minimum change.** It should sit outside the noise band for the month size",
        "   chosen above, or the report will claim trends that are not there.",
        "3. **Whether thin dealerships are compared quarterly instead**, so they appear in",
        "   the trend section at all rather than being silently dropped.",
        "",
        "Once set, the numbers go in `config.yaml` under `thresholds.trend_evidence` and are",
        "committed before any trend result is produced (gate G7).",
        "",
    ]

    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)} ({len(pairs)} month pairs, {len(dealers)} dealers)")
    return 0


if __name__ == "__main__":
    sys.exit(main())

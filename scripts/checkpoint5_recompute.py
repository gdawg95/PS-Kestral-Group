"""Checkpoint 5: recompute the published headline numbers from the reviewer export.

PLAN.md Checkpoint 5 asks the owner to recompute two or three headline numbers by hand.
This is the no-spreadsheet version of that check.

WHAT MAKES IT A CHECK, AND WHAT DOES NOT:

  * It reads ONLY `export/feedback_clean.csv` - the de-identified file published for
    reviewers (D-064, D-067). It does not touch `data/clean/*.parquet`, which is what the
    analysis runs on.
  * It does not import `src/analyse.py`, or anything else from `src/`. Every figure below is
    computed here from the CSV with plain pandas, in one line each.
  * The expected values are typed in as literals, copied by hand out of `reports/analysis.md`
    and `reports/business_report.md`. If the analysis changes and this file is not updated,
    this script FAILS - which is the behaviour you want from a check.

  * It is NOT independent verification. It was written by the same session that wrote the
    analysis, so a mistake in one could in principle appear in the other. Its value is that
    it is 60 lines long and reads a different file by a different route, so you can read
    every line yourself in two minutes. D-017's independent verifier is a separate job.

Run: uv run python scripts/checkpoint5_recompute.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
EXPORT = ROOT / "export" / "feedback_clean.csv"

# (label, published value, tolerance, where it is published)
CHECKS: list[tuple[str, float, float, str]] = []


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if not EXPORT.exists():
        print(f"no export at {EXPORT} - run `make export` first")
        return 1

    d = pd.read_csv(EXPORT)
    d["state"] = d["dealer_code"].str[:3]  # NSW01 -> NSW; the export has no state column
    d["negative"] = d["rating_1to5"] <= 2  # D-004: negative is a rating of 1 or 2
    h2 = d["feedback_month"] >= "2026-04"  # the fixed midpoint of the 12 months
    svc = d["department"] == "Service"
    nsw = d["state"] == "NSW"
    qld = d["state"] == "QLD"
    commented = d["comment"].notna()

    rows = len(d)
    results = [
        ("Rows in the published dataset", rows, 7150, 0, "analysis.md header"),
        (
            "Negative rate, ALL rows (the headline)",
            round(100 * d["negative"].mean(), 1),
            22.5,
            0.05,
            "analysis.md s1, business_report.md s1",
        ),
        (
            "Negative rate, COMMENTED rows only",
            round(100 * d.loc[commented, "negative"].mean(), 1),
            28.1,
            0.05,
            "analysis.md s1 - the 5.6pt gap D-058 exists for",
        ),
        (
            "Commented rows",
            int(commented.sum()),
            5353,
            0,
            "analysis.md header",
        ),
        (
            "Service share of all feedback (%)",
            round(100 * svc.mean(), 1),
            68.6,
            0.05,
            "analysis.md s2, business_report.md s4",
        ),
        (
            "Service negative rate (%)",
            round(100 * d.loc[svc, "negative"].mean(), 1),
            27.2,
            0.05,
            "analysis.md s2",
        ),
        (
            "NSW Service negative rate, 1st half (%)",
            round(100 * d.loc[nsw & svc & ~h2, "negative"].mean(), 1),
            21.7,
            0.05,
            "analysis.md s7.3",
        ),
        (
            "NSW Service negative rate, 2nd half (%)",
            round(100 * d.loc[nsw & svc & h2, "negative"].mean(), 1),
            32.1,
            0.05,
            "analysis.md s7.3 - the load-bearing claim",
        ),
        (
            "QLD negative rate, 1st half (%)",
            round(100 * d.loc[qld & ~h2, "negative"].mean(), 1),
            21.0,
            0.05,
            "analysis.md s7.3 - QLD did not move",
        ),
        (
            "QLD negative rate, 2nd half (%)",
            round(100 * d.loc[qld & h2, "negative"].mean(), 1),
            23.3,
            0.05,
            "analysis.md s7.3 - QLD did not move",
        ),
        (
            "Group mean rating, 1st half",
            round(d.loc[~h2, "rating_1to5"].mean(), 3),
            3.842,
            0.001,
            "analysis.md s7.2 - the trend",
        ),
        (
            "Group mean rating, 2nd half",
            round(d.loc[h2, "rating_1to5"].mean(), 3),
            3.671,
            0.001,
            "analysis.md s7.2 - the trend",
        ),
        (
            "NSW01 Parramatta mean rating, 1st half",
            round(d.loc[(d["dealer_code"] == "NSW01") & ~h2, "rating_1to5"].mean(), 2),
            3.97,
            0.005,
            "analysis.md s7.3",
        ),
        (
            "NSW01 Parramatta mean rating, 2nd half",
            round(d.loc[(d["dealer_code"] == "NSW01") & h2, "rating_1to5"].mean(), 2),
            3.22,
            0.005,
            "analysis.md s7.3 - the largest site fall",
        ),
    ]

    width = max(len(r[0]) for r in results)
    print(f"\nCheckpoint 5 - recomputed from {EXPORT.relative_to(ROOT)}")
    print(f"{'':{width}}   {'recomputed':>11}  {'published':>10}\n")
    failures = 0
    for label, got, want, tol, where in results:
        ok = abs(got - want) <= tol
        failures += not ok
        print(f"{label:{width}}   {got:>11}  {want:>10}   {'OK' if ok else 'MISMATCH'}")
        if not ok:
            print(f"{'':{width}}   ^ published in {where}")

    print()
    if failures:
        print(f"{failures} of {len(results)} do NOT match what the reports publish.")
        print("Do not submit until this is explained.")
        return 1
    print(f"All {len(results)} match the published reports.")
    print("\nWhat this does and does not show:")
    print("  It shows the numbers in the reports are the numbers in the published dataset.")
    print("  It does NOT show the published dataset is a correct read of the 52 source")
    print("  spreadsheets - that is Wave 2's row reconciliation (README section 5) - and it")
    print("  is not independent, because the session that wrote the analysis wrote this too.")
    print("  D-017's independent verifier ran separately on 30 Oct 2026 and DID find a")
    print("  published number these 14 checks missed - see agents/reports/w5_verify.md,")
    print("  finding V-1. That is the argument for keeping both checks, not either one.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

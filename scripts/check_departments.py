"""Cross-check mappings/departments.yaml against the consolidated dataset.

Checks, for the owner's review:
  1. every department_raw value in the dataset has exactly one entry
  2. no entry in the mapping is unused
  3. every entry maps to Service, Sales or Parts
  4. the row counts and means quoted in the file match the data
  5. the totals block adds up

Reads department and rating columns only, so the output holds no PII.

    python scripts/check_departments.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[1]
MAPPING = ROOT / "mappings" / "departments.yaml"
PARQUET = ROOT / "data" / "interim" / "consolidated.parquet"
VALID = {"Service", "Sales", "Parts"}


def main() -> int:
    if not PARQUET.exists():
        print(f"no dataset at {PARQUET} - run `python -m src.ingest` first")
        return 1

    spec = yaml.safe_load(MAPPING.read_text(encoding="utf-8"))
    mapping = spec["mapping"]
    df = pd.read_parquet(PARQUET, columns=["department_raw", "rating_1to5", "dealer_code"])

    problems: list[str] = []
    seen = (
        df.groupby("department_raw", observed=True)
        .agg(rows=("rating_1to5", "size"), mean=("rating_1to5", "mean"))
        .to_dict("index")
    )

    for value in sorted(set(seen) - set(mapping)):
        problems.append(f"dataset value {value!r} has no entry in the mapping")
    for value in sorted(set(mapping) - set(seen)):
        problems.append(f"mapping entry {value!r} does not occur in the dataset")

    for value, entry in mapping.items():
        if entry.get("to") not in VALID:
            problems.append(f"{value!r} maps to {entry.get('to')!r}, not Service/Sales/Parts")
        if value not in seen:
            continue
        if entry.get("rows") != seen[value]["rows"]:
            problems.append(
                f"{value!r}: file says {entry.get('rows')} rows, dataset has "
                f"{seen[value]['rows']}"
            )
        if abs(float(entry.get("mean", 0)) - seen[value]["mean"]) > 0.005:
            problems.append(
                f"{value!r}: file says mean {entry.get('mean')}, dataset has "
                f"{seen[value]['mean']:.2f}"
            )

    totals = spec.get("totals") or {}
    actual = {d: 0 for d in VALID}
    for value, entry in mapping.items():
        if value in seen and entry.get("to") in VALID:
            actual[entry["to"]] += seen[value]["rows"]
    for dept in sorted(VALID):
        if totals.get(dept) != actual[dept]:
            problems.append(
                f"totals.{dept} says {totals.get(dept)}, the mapping gives {actual[dept]}"
            )
    if totals.get("all") != sum(actual.values()) or sum(actual.values()) != len(df):
        problems.append(
            f"totals.all says {totals.get('all')}, the mapping gives {sum(actual.values())}, "
            f"the dataset has {len(df)} rows"
        )

    print(f"dataset values: {len(seen)} | mapping entries: {len(mapping)} | rows: {len(df):,}")
    print(f"Service {actual['Service']:,} · Sales {actual['Sales']:,} · Parts {actual['Parts']:,}")
    print()
    if problems:
        print(f"{len(problems)} PROBLEM(S):")
        for p in problems:
            print("  -", p)
        return 1
    print("OK: every department value is mapped exactly once, and the counts match the data.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

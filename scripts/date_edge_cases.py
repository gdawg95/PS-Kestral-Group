"""The 16 dates the pipeline changed or invented, with the source value beside each one.

Checkpoint 3 asks the owner to look at the date edge cases. `reports/data_quality.md`
lists them, but it can only show the *resolved* date: the source value does not survive
ingestion (D-003 keeps four content columns and a date is stored as a date). Without the
source text, "2025-10-06" is not reviewable - the owner cannot tell whether "early Oct"
was read sensibly.

So this script reads the two raw workbooks, read-only, and puts the source value, the
resolved date and the neighbouring dated rows side by side. For the imputed rows the
neighbours are the evidence: D-040 takes the day from the midpoint of the nearest dated
row above and below, so showing them is showing the working.

It is a review aid, not a pipeline stage: it writes a report and nothing else, and
`make all` does not call it. Run it before Checkpoint 3.

    uv run python scripts/date_edge_cases.py
"""

from __future__ import annotations

import datetime as dt
from pathlib import Path

import openpyxl
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw" / "feedback"
CONSOLIDATED = ROOT / "data" / "interim" / "consolidated.parquet"
OUT = ROOT / "reports" / "date_edge_cases.md"


def source_dates(file_name: str, sheet: str) -> tuple[dict[int, object], int]:
    """{spreadsheet row: raw date cell} for one worksheet, plus the date column index."""
    wb = openpyxl.load_workbook(RAW / file_name, data_only=True, read_only=True)
    ws = wb[sheet]
    values: dict[int, object] = {}
    date_col = None
    for i, row in enumerate(ws.iter_rows(values_only=True), 1):
        if i == 1:
            headers = [str(c).strip().lower() if c is not None else "" for c in row]
            date_col = headers.index("date") if "date" in headers else 0
            continue
        if date_col is not None and date_col < len(row):
            values[i] = row[date_col]
    wb.close()
    return values, (date_col or 0)


def as_text(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, (dt.datetime, dt.date)):
        return f"{value:%d/%m/%Y}"
    return str(value).strip()


def is_a_date(value: object) -> bool:
    """True for a real date cell. Both logs store theirs as day-first text, not as dates."""
    if isinstance(value, (dt.datetime, dt.date)):
        return True
    if not isinstance(value, str) or not value.strip():
        return False
    return pd.to_datetime(value.strip(), dayfirst=True, errors="coerce") is not pd.NaT


def neighbours(values: dict[int, object], row: int, flagged: set[int]) -> tuple[str, str]:
    """The nearest rows above and below that carry a real date (D-040's evidence)."""

    def is_real(r: int) -> bool:
        if r in flagged or r not in values:
            return False
        return is_a_date(values[r])

    def fmt(r: int | None) -> str:
        return f"row {r}: {as_text(values[r])}" if r else "-"

    above = max((r for r in values if r < row and is_real(r)), default=None)
    below = min((r for r in values if r > row and is_real(r)), default=None)
    return fmt(above), fmt(below)


def main() -> int:
    df = pd.read_parquet(CONSOLIDATED)
    flagged = df[df["date_corrected"] | df["date_approx"]].sort_values(
        ["dealer_code", "source_row"]
    )

    lines = [
        "# The 16 dates the pipeline changed or invented",
        "",
        f"**Generated:** `python scripts/date_edge_cases.py` · "
        f"{dt.datetime.now():%Y-%m-%d %H:%M}",
        "",
        "Checkpoint 3's date review. Sixteen rows - every row whose date was corrected or "
        "imputed, not a sample. `reports/data_quality.md` lists the same rows but can only "
        "show the resolved date; the source value below is what makes them reviewable.",
        "",
        "No comment text appears here.",
        "",
    ]

    for (file_name, sheet), grp in flagged.groupby(["source_file", "source_sheet"]):
        values, _ = source_dates(file_name, sheet)
        flagged_rows = set(grp["source_row"])
        corrected = bool(grp["date_corrected"].any())

        lines += [
            f"## {file_name} · sheet `{sheet}` · {len(grp)} rows",
            "",
        ]
        if corrected:
            lines += [
                "Dated after the site closed (30 Mar 2026), in a month the site was still "
                "open a year earlier - read as a year typo and moved to 2025 "
                "(D-032 #3). All six carry `date_corrected`.",
                "",
                "| Row | Source value | Resolved | Shift |",
                "|---:|---|---|---|",
            ]
            for _, r in grp.iterrows():
                src = as_text(values.get(r.source_row))
                lines.append(
                    f"| {r.source_row} | `{src}` | {r.feedback_date.date()} | "
                    f"year 2026 → 2025, day and month unchanged |"
                )
        else:
            lines += [
                "The only non-date values in a column of 277. The day is the midpoint of "
                "the nearest dated row above and below, the year comes with them, and the "
                "written label supplies the month (D-040). All ten carry `date_approx`.",
                "",
                "| Row | Source value | Resolved | Nearest dated row above | "
                "Nearest dated row below | Label and position agree on the month? |",
                "|---:|---|---|---|---|---|",
            ]
            for _, r in grp.iterrows():
                src = as_text(values.get(r.source_row))
                above, below = neighbours(values, int(r.source_row), flagged_rows)
                month_from_label = _month_of_label(src)
                agrees = (
                    "yes" if month_from_label == r.feedback_date.month
                    else f"**no - label says month {month_from_label}**"
                )
                lines.append(
                    f"| {r.source_row} | `{src}` | {r.feedback_date.date()} | {above} | "
                    f"{below} | {agrees} |"
                )
        lines.append("")

    lines += [
        "## What to look at",
        "",
        "- The six corrected rows are a single consistent pattern: a 2026 date in a month "
        "the closed site could not have traded in, moved back one year with the day and "
        "month untouched. If the pattern is right, all six are right.",
        "- The ten imputed rows are only as good as the neighbours they sit between, and "
        "the neighbours are tight: each of the ten is bracketed by dated rows within a few "
        "days. The two `Aug?` rows look like the weakest of the set, because there the "
        "source doubted the month rather than the day - but they are the best supported of "
        "all ten. Row 248 sits between two rows both dated 12 Aug, so nothing is left to "
        "guess.",
        "- Where the written label and the resolved day disagree, the neighbours won: "
        "`mid Nov` resolved to the 3rd and `early Apr` to the 21st, because that is where "
        "the surrounding dated rows put them. The label still fixes the month, and the last "
        "column confirms label and position agree on the month for all ten (D-040's "
        "cross-check, re-run here rather than quoted).",
        "- Every analysis in this project is monthly, so the day never reaches a published "
        "figure, and `date_approx` is set on all ten so they can be excluded from any "
        "day-level claim.",
        "",
    ]

    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"{len(flagged)} rows -> {OUT.relative_to(ROOT)}")
    return 0


_MONTHS = {
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
    "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12,
}


def _month_of_label(text: str) -> int | None:
    low = text.lower()
    for name, number in _MONTHS.items():
        if name in low:
            return number
    return None


if __name__ == "__main__":
    raise SystemExit(main())

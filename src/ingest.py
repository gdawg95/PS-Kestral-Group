"""Wave 2: turn the 52 raw files into one consolidated, de-identified dataset.

Everything this module does is driven by `mappings/columns.yaml`, which the owner
approved line by line at Checkpoint 2 (gate G3). There are no per-file branches in
the code: a new quirk is a change to the mapping, not to this file.

Order of operations per worksheet (agents/briefs/w2_ingest.md step 2):

  1. slice the worksheet to the layout's table (header row, and the next layout's
     start row where one sheet holds two templates)
  2. drop rows that are not feedback - blank, notes and totals, test rows - each
     counted with its reason (D-037, D-039)
  3. dates: the layout's format, plus the Shepparton year fix (D-032 #3) and the
     Ipswich approximate dates (D-040); flags kept
  4. ratings: convert to 1-5 per the owner's table (D-020, D-030); drop rows with
     no usable rating (D-031)
  5. department: kept exactly as the source wrote it, except Bendigo's letter
     codes, which the owner asked to be spelled out (D-036)
  6. PII: src.pii.deidentify with the staff roster, known names and corpus pass
     (D-026). Only date, department, rating and comment survive (D-003)
  7. the Toowoomba pivot expands to one row per response (D-032 #1)
  8. North QLD splits into QLD07 and QLD08 by its Site column (D-042)
  9. feedback_id, lineage columns and flags

Usage:
    python -m src.ingest                      # all 51 files in scope
    python -m src.ingest --dealers VIC06 NSW04 QLD07 QLD08 VIC02 QLD06   # the pilot
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import io
import math
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any

import openpyxl
import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src import schema  # noqa: E402
from src.pii import deidentify, person_candidates, promote_names  # noqa: E402

RAW = ROOT / "data" / "raw" / "feedback"
MAPPING = ROOT / "mappings" / "columns.yaml"
DEALERSHIPS = ROOT / "data" / "raw" / "reference" / "dealerships.csv"
OUT_PARQUET = ROOT / "data" / "interim" / "consolidated.parquet"
RECONCILIATION = ROOT / "reports" / "reconciliation.md"

EXCEL_EPOCH = dt.datetime(1899, 12, 30)  # Excel's day 1 is 1900-01-01, with the 1900 bug

FIVE_POINT_WORDS = {
    "very dissatisfied": 1,
    "dissatisfied": 2,
    "neutral": 3,
    "satisfied": 4,
    "very satisfied": 5,
}
THREE_POINT_WORDS = {  # owner's rule, D-020
    "bad": 1,
    "ok": 3,
    "okay": 3,
    "average": 3,
    "medium": 3,
    "good": 5,
}

MONTHS = {
    m.lower(): i
    for i, m in enumerate(
        ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"], 1
    )
}

SUMMARY_ROW = re.compile(
    r"^\s*(total|grand total|average|avg|mean|count|summary|note|notes|nps|overall|site closed"
    r"|\*\*\*)",
    re.I,
)
TEST_ROW = re.compile(r"^\s*(test\b|testing\b|asdf\b)", re.I)


# --------------------------------------------------------------- pure helpers


def round_half_up(x: float) -> int:
    return int(math.floor(x + 0.5))


def to_1to5(value: Any, scale: str) -> int | None:
    """Convert a source rating to the 1-5 scale. None means 'no usable rating' (D-031).

    Pure function, so the owner's table in D-020 is unit-tested directly.
    """
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return None
    text = str(value).strip()
    if not text:
        return None

    if scale == "stars-5":
        if set(text) <= {"★", "☆"} and len(text) == 5:
            return text.count("★")
        return None
    if scale == "words-5":
        return FIVE_POINT_WORDS.get(text.lower())
    if scale == "words-3":
        return THREE_POINT_WORDS.get(text.lower())

    try:
        n = float(text)
    except ValueError:
        return None
    if n != int(n):
        return None
    n = int(n)

    if scale in ("1-5", "pivot-1-5"):
        return n if 1 <= n <= 5 else None
    if scale == "1-5-reversed":  # D-030: the Geelong 2025 sheet only
        return 6 - n if 1 <= n <= 5 else None
    if scale == "1-10":  # D-020: 1-2->1, 3-4->2, 5-6->3, 7-8->4, 9-10->5
        return round_half_up(1 + (n - 1) * 4 / 9) if 1 <= n <= 10 else None
    raise ValueError(f"unknown rating scale {scale!r}")


def parse_date(value: Any, date_format: str) -> dt.date | None:
    """Parse one source date cell. None means it did not parse at all."""
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return None
    if isinstance(value, dt.datetime):
        return value.date()
    if isinstance(value, dt.date):
        return value
    if date_format == "excel_serial" and isinstance(value, (int, float)):
        return (EXCEL_EPOCH + dt.timedelta(days=float(value))).date()
    text = str(value).strip()
    if not text:
        return None
    if date_format in ("excel", "excel_serial"):
        # a text cell in a column of real dates - try the Australian order
        for fmt in ("%d/%m/%Y", "%d/%m/%y", "%Y-%m-%d"):
            try:
                return dt.datetime.strptime(text, fmt).date()
            except ValueError:
                continue
        return None
    try:
        return dt.datetime.strptime(text, date_format).date()
    except ValueError:
        return None


def month_from_label(text: str) -> int | None:
    """The month an approximate label names, e.g. 'early Oct' -> 10 (D-040)."""
    for token in re.findall(r"[A-Za-z]+", str(text)):
        m = MONTHS.get(token[:3].lower())
        if m:
            return m
    return None


def midpoint(before: dt.date | None, after: dt.date | None) -> dt.date | None:
    """The date halfway between the nearest dated rows either side (D-040)."""
    if before and after:
        return before + (after - before) / 2
    return before or after


def parse_month_pivot(text: str) -> dt.date | None:
    """'Oct-25' -> 2025-10-15, the 15th because the real day is gone (D-032 #1)."""
    m = re.match(r"\s*([A-Za-z]{3})[\s-]*(\d{2,4})\s*$", str(text))
    if not m:
        return None
    month = MONTHS.get(m.group(1).lower())
    if not month:
        return None
    year = int(m.group(2))
    year += 2000 if year < 100 else 0
    return dt.date(year, month, 15)


def classify_junk(cells: list[Any], layout: dict) -> str | None:
    """'blank', 'summary_or_note', 'test_row', or None for a real feedback row."""
    values = [c for c in cells if c is not None and str(c).strip() != ""]
    if not values:
        return "blank"
    allowed = set(layout.get("drop_rows") or []) | {"blank", "summary_or_note", "test_row"}
    head = [str(c).strip() for c in cells[:3] if c is not None and str(c).strip()]
    for text in head:
        if TEST_ROW.match(text) and "test_row" in allowed:
            return "test_row"
        if SUMMARY_ROW.match(text) and "summary_or_note" in allowed:
            return "summary_or_note"
    # a row whose only content is one long note in the first cell
    if len(values) == 1 and isinstance(values[0], str) and len(values[0].strip()) > 20:
        if "summary_or_note" in allowed:
            return "summary_or_note"
    return None


# ------------------------------------------------------------- reading sheets


def read_rows(path: Path, sheet: str | None, layout: dict) -> list[list[Any]]:
    """Every row of a worksheet as a list of cells, in sheet order."""
    if path.suffix.lower() == ".csv":
        cfg = layout.get("csv") or {}
        raw = path.read_bytes()
        text = raw.decode(cfg.get("encoding", "utf-8"))
        reader = csv.reader(io.StringIO(text, newline=""), delimiter=cfg.get("delimiter", ","))
        return [list(r) for r in reader]
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    try:
        return [list(r) for r in wb[sheet].iter_rows(values_only=True)]
    finally:
        wb.close()


def sheet_base_and_start(sheet_key: str | None) -> tuple[str | None, int | None]:
    """'Feedback [layout 2, from row 37]' -> ('Feedback', 37). A CSV's key is None."""
    if sheet_key is None:
        return None, None
    m = re.match(r"^(.*?) \[layout \d+, from row (\d+)\]$", sheet_key)
    if m:
        return m.group(1), int(m.group(2))
    return sheet_key, None


def _is_blank(cells: list[Any]) -> bool:
    return all(c is None or str(c).strip() == "" for c in cells)


def slice_table(
    rows: list[list[Any]], layout: dict, next_start: int | None
) -> tuple[list[str], list[tuple[int, list[Any]]]]:
    """Return (header names, [(spreadsheet row number, cells)]) for one layout's table.

    Trailing empty rows are trimmed: openpyxl's read-only mode reports the sheet's
    used range, which can run past the data, and those rows are not source rows.
    """
    while rows and _is_blank(list(rows[-1])):
        rows = rows[:-1]
    header_row = layout.get("header_row", 1)
    width = max((len(r) for r in rows), default=0)
    header = [
        str(c).strip() if c is not None else "" for c in list(rows[header_row - 1]) + [None] * width
    ][:width]
    last = (next_start - 1) if next_start else len(rows)
    body = [
        (i + 1, list(rows[i]) + [None] * (width - len(rows[i]))) for i in range(header_row, last)
    ]
    return header, body


# ------------------------------------------------------------------- the pass


class Reconciliation:
    """Rows in, rows out and every drop with its reason - the D-002 (c) evidence."""

    def __init__(self) -> None:
        self.rows_read: Counter = Counter()
        self.rows_out: Counter = Counter()
        self.drops: dict[str, Counter] = {}
        self.tokens: Counter = Counter()
        self.notes: list[str] = []
        self.pivot_source_rows = 0      # counts rows that leave the arithmetic
        self.pivot_expanded_rows = 0    # the feedback rows they become

    def drop(self, key: str, reason: str, n: int = 1) -> None:
        self.drops.setdefault(key, Counter())[reason] += n

    def total_drops(self) -> Counter:
        out: Counter = Counter()
        for counts in self.drops.values():
            out.update(counts)
        return out


def load_mapping() -> dict:
    return yaml.safe_load(MAPPING.read_text(encoding="utf-8"))


def dealer_codes() -> set[str]:
    with DEALERSHIPS.open(encoding="utf-8") as fh:
        return {r["dealer_code"] for r in csv.DictReader(fh)}


def sheets_in_scope(mapping: dict, dealers: set[str] | None):
    """Yield (file name, sheet key, layout name, dealer code) for everything to ingest."""
    for fname, spec in mapping["files"].items():
        if spec.get("skip"):
            continue
        code = spec.get("dealer_code")
        if dealers is not None:
            codes = (
                set(mapping["layouts"]["northqld"]["split"])
                if code == "split_by_site"
                else {code}
            )
            if not (codes & dealers):
                continue
        for sheet_key, ref in (spec.get("sheets") or {}).items():
            if isinstance(ref, dict):  # a skipped sheet
                continue
            yield fname, sheet_key, ref, code


def collect_names(mapping: dict, scope: list[tuple]) -> tuple[set[str], set[str]]:
    """Staff first names and all known first names, from the mapped columns only.

    Held in memory and never written (D-003 exception, D-026, D-041). Built from the
    files in scope, which for the full run is all of them.
    """
    staff: set[str] = set()
    known: set[str] = set()
    for fname, sheet_key, ref, _code in scope:
        layout = mapping["layouts"][ref]
        base, _start = sheet_base_and_start(sheet_key)
        rows = read_rows(RAW / fname, base if base else None, layout)
        if not rows:
            continue
        next_start = _next_start(mapping, fname, sheet_key)
        header, body = slice_table(rows, layout, next_start)
        staff_cols = [header.index(c) for c in (layout.get("redact_staff") or []) if c in header]
        name_cols = [
            header.index(c)
            for c, role in (layout.get("columns") or {}).items()
            if role == "redact_name" and c in header
        ]
        for _row_no, cells in body:
            for j in staff_cols:
                v = cells[j]
                if isinstance(v, str) and v.strip():
                    staff.add(re.split(r"[\s.]+", v.strip())[0])
            for j in name_cols:
                v = cells[j]
                if isinstance(v, str) and v.strip():
                    known.add(re.split(r"[\s.]+", v.strip())[0])
    staff.discard("Staff")
    return staff, known | staff


def _next_start(mapping: dict, fname: str, sheet_key: str) -> int | None:
    """Where the next layout starts, for a sheet that holds two templates."""
    base, start = sheet_base_and_start(sheet_key)
    if start is None:
        return None
    starts = sorted(
        s
        for k in (mapping["files"][fname].get("sheets") or {})
        for b, s in [sheet_base_and_start(k)]
        if b == base and s is not None and s > start
    )
    return starts[0] if starts else None


def ingest_sheet(
    mapping: dict,
    fname: str,
    sheet_key: str,
    ref: str,
    code: str,
    names: tuple[set[str], set[str], set[str]],
    rec: Reconciliation,
) -> pd.DataFrame:
    """One worksheet (or one layout within one worksheet) -> schema rows."""
    layout = mapping["layouts"][ref]
    base, _start = sheet_base_and_start(sheet_key)
    key = fname if sheet_key is None else f"{fname} :: {sheet_key}"
    rows = read_rows(RAW / fname, base if base else None, layout)
    header, body = slice_table(rows, layout, _next_start(mapping, fname, sheet_key))
    rec.rows_read[key] = len(body)

    if layout.get("expand_pivot"):
        return _expand_pivot(layout, header, body, fname, sheet_key, code, rec, key)

    # --- 2. rows that are not feedback -------------------------------------
    named = _named_junk(layout, header, key)
    _verify_named_junk(layout, header, body, key)
    kept: list[tuple[int, list[Any]]] = []
    for row_no, cells in body:
        reason = named.get(row_no) or classify_junk(cells, layout)
        if reason:
            rec.drop(key, reason)
        else:
            kept.append((row_no, cells))
    unseen = set(named) - {r for r, _c in body}
    if unseen:
        raise ValueError(f"{key}: junk_rows names rows that are not in the sheet: {sorted(unseen)}")
    if not kept:
        return pd.DataFrame(columns=list(schema.COLUMNS))

    cols = layout.get("columns") or {}
    present = {c: r for c, r in cols.items() if c in header}
    missing = [c for c in cols if c not in header]
    if missing:
        raise KeyError(f"{key}: mapped columns not in the sheet: {missing}")
    unmapped = [
        c
        for c in header
        if c
        and c not in cols
        and c not in (layout.get("dropped") or [])
        and c not in (layout.get("redact_staff") or [])
        and c != layout.get("site_column")
    ]
    if unmapped and layout.get("unnamed_columns") != "drop":
        raise KeyError(f"{key}: source columns the mapping does not account for: {unmapped}")

    frame = pd.DataFrame(
        {c: [cells[header.index(c)] for _r, cells in kept] for c in present},
        index=[r for r, _cells in kept],
    )
    site_col = layout.get("site_column")
    sites = (
        [cells[header.index(site_col)] for _r, cells in kept]
        if site_col and site_col in header
        else None
    )

    # --- 6. PII: only the four content columns survive ---------------------
    staff, known, extra = names
    clean, tokens = deidentify(
        frame, present, fname, staff_names=staff, known_names=known, extra_names=extra
    )
    rec.tokens.update(tokens)
    clean.index = frame.index

    # --- 3. dates ----------------------------------------------------------
    dates, corrected, approx = _resolve_dates(clean["date"], layout, key, rec)

    # --- 4. ratings --------------------------------------------------------
    scale = layout["rating_scale"]
    mapped = [to_1to5(v, scale) for v in clean["rating"]]

    # --- 5. department -----------------------------------------------------
    dmap = layout.get("department_map") or {}
    if layout.get("department_from_sheet_name"):
        departments = [base] * len(clean)
    else:
        departments = [
            dmap.get(str(v).strip(), v) if v is not None else v for v in clean["department"]
        ]

    out_rows = []
    for pos, (row_no, _cells) in enumerate(kept):
        if mapped[pos] is None:
            rec.drop(key, "no_rating")
            continue
        if dates[pos] is None:
            rec.drop(key, "no_date")
            continue
        dealer = code
        if sites is not None:
            dealer = _site_to_code(layout, sites[pos], key)
        out_rows.append(
            {
                "feedback_id": None,
                "dealer_code": dealer,
                "feedback_date": dates[pos],
                "department_raw": _text(departments[pos]),
                "department": None,
                "rating_raw": _text(clean["rating"].iloc[pos]),
                "rating_scale": scale,
                "rating_1to5": mapped[pos],
                "comment": clean["comment"].iloc[pos],
                "source_file": fname,
                "source_sheet": base or None,
                "source_row": row_no,
                "from_summary": False,
                "date_corrected": bool(corrected[pos]),
                "date_approx": bool(approx[pos]),
            }
        )

    df = pd.DataFrame(out_rows, columns=list(schema.COLUMNS))
    _assert_date_range(layout, df, key)
    rec.rows_out[key] = len(df)
    return df


def _named_junk(layout: dict, header: list[str], key: str) -> dict[int, str]:
    """Spreadsheet row -> drop reason, for rows the owner identified individually.

    Two of Southport's four junk rows do not look like junk from their first cells -
    one has an empty date and a real-looking rating, the other a date of 01/01/1900 -
    so the mapping names them by row (D-037). The comment is checked as well as the
    row number: if the file is ever re-sent with rows inserted, the run fails here
    instead of dropping somebody's real feedback.
    """
    named: dict[int, str] = {}
    for reason, rows in (layout.get("junk_rows") or {}).items():
        for entry in rows:
            named[int(entry["xl_row"])] = reason
    if named and "comment" not in (layout.get("columns") or {}).values():
        raise ValueError(f"{key}: junk_rows needs a comment column to verify against")
    return named


def _verify_named_junk(layout: dict, header: list[str], body, key: str) -> None:
    """Fail if a named junk row no longer holds the comment the owner approved."""
    cols = layout.get("columns") or {}
    comment_col = next((c for c, r in cols.items() if r == "comment"), None)
    if comment_col is None or comment_col not in header:
        return
    j = header.index(comment_col)
    by_row = {r: c for r, c in body}
    for _reason, rows in (layout.get("junk_rows") or {}).items():
        for entry in rows:
            row_no = int(entry["xl_row"])
            expected = str(entry.get("comment", "")).strip()
            if row_no not in by_row:
                raise ValueError(
                    f"{key} row {row_no}: junk_rows names a row the sheet no longer has. "
                    "The file has changed - re-check it with the owner (D-037)."
                )
            found = str(by_row[row_no][j] or "").strip()
            if expected and found != expected:
                raise ValueError(
                    f"{key} row {row_no}: junk_rows expects comment {expected!r} but the sheet "
                    f"now holds {found[:40]!r}. The file has changed - re-check it with the "
                    "owner before ingesting (D-037)."
                )


def _text(v: Any) -> str | None:
    if v is None or (isinstance(v, float) and math.isnan(v)):
        return None
    s = str(v).strip()
    return s or None


def _site_to_code(layout: dict, value: Any, key: str) -> str:
    site_map = layout.get("site_map") or {}
    code = site_map.get(str(value).strip())
    if code is None:
        raise KeyError(f"{key}: site {value!r} is not in the layout's site_map")
    return code


def _resolve_dates(series, layout: dict, key: str, rec: Reconciliation):
    """Parse the dates, then apply the year fix and the approximate-date rule."""
    fmt = layout.get("date_format", "excel")
    values = list(series)
    dates = [parse_date(v, fmt) for v in values]
    corrected = [False] * len(dates)
    approx = [False] * len(dates)
    fixes = layout.get("date_fixes") or {}

    if "year_typo" in fixes:  # D-032 #3: Shepparton
        for i, d in enumerate(dates):
            if d and d > schema.DATE_MAX:
                dates[i] = d.replace(year=d.year - 1)
                corrected[i] = True

    if "approximate" in fixes:  # D-040: Ipswich
        for i, d in enumerate(dates):
            if d is not None:
                continue
            label = values[i]
            month = month_from_label(label)
            if month is None:
                continue
            before = next((dates[j] for j in range(i - 1, -1, -1) if dates[j]), None)
            after = next((dates[j] for j in range(i + 1, len(dates)) if dates[j]), None)
            guess = midpoint(before, after)
            if guess is None:
                continue
            if guess.month != month:
                raise ValueError(
                    f"{key} row {i}: approximate date {label!r} names month {month} but the "
                    f"rows around it put it in month {guess.month} (D-040 cross-check)"
                )
            dates[i] = guess
            approx[i] = True
        rec.notes.append(f"{key}: {sum(approx)} approximate dates resolved (D-040)")

    return dates, corrected, approx


def _assert_date_range(layout: dict, df: pd.DataFrame, key: str) -> None:
    bounds = layout.get("assert_date_range")
    if not bounds or df.empty:
        return
    lo, hi = (dt.date.fromisoformat(b) for b in bounds)
    dates = pd.to_datetime(df["feedback_date"]).dt.date
    outside = int(((dates < lo) | (dates > hi)).sum())
    if outside:
        raise ValueError(
            f"{key}: {outside} rows fall outside the asserted range {lo}..{hi} - the file's "
            "date format has probably changed (D-032 #2)"
        )


def _expand_pivot(
    layout: dict,
    header: list[str],
    body: list[tuple[int, list[Any]]],
    fname: str,
    sheet_key: str,
    code: str,
    rec: Reconciliation,
    key: str,
) -> pd.DataFrame:
    """Counts of each score -> one row per response (D-032 #1)."""
    cfg = layout["expand_pivot"]
    month_j = header.index(cfg["month_column"])
    dept_j = header.index(cfg["department_column"])
    score_js = {s: header.index(s) for s in cfg["count_columns"]}
    day = cfg.get("day_of_month", 15)

    out_rows = []
    for row_no, cells in body:
        month = parse_month_pivot(cells[month_j])
        if month is None:  # the "Grand Total" row
            rec.drop(key, "summary_or_note")
            continue
        month = month.replace(day=day)
        for score, j in score_js.items():
            n = cells[j] or 0
            for _ in range(int(n)):
                out_rows.append(
                    {
                        "feedback_id": None,
                        "dealer_code": code,
                        "feedback_date": month,
                        "department_raw": _text(cells[dept_j]),
                        "department": None,
                        "rating_raw": str(score),
                        "rating_scale": layout["rating_scale"],
                        "rating_1to5": int(score),
                        "comment": None,
                        "source_file": fname,
                        "source_sheet": sheet_base_and_start(sheet_key)[0] or None,
                        "source_row": row_no,
                        "from_summary": True,
                        "date_corrected": False,
                        "date_approx": False,
                    }
                )

    expected = cfg.get("expected_rows")
    if expected is not None and len(out_rows) != expected:
        raise ValueError(f"{key}: pivot expanded to {len(out_rows)} rows, expected {expected}")
    rec.rows_out[key] = len(out_rows)
    rec.pivot_source_rows += len(body) - sum(rec.drops.get(key, Counter()).values())
    rec.pivot_expanded_rows += len(out_rows)
    return pd.DataFrame(out_rows, columns=list(schema.COLUMNS))


# ----------------------------------------------------------------- the driver


def ingest(
    dealers: set[str] | None = None, use_ner: bool = True
) -> tuple[pd.DataFrame, Reconciliation]:
    mapping = load_mapping()
    rec = Reconciliation()
    scope = list(sheets_in_scope(mapping, dealers))

    staff, known = collect_names(mapping, scope)
    comments = _all_comments(mapping, scope)
    candidates = person_candidates(comments) if use_ner else Counter()
    extra = (promote_names(comments, candidates) - staff) if use_ner else set()
    rec.notes.append(
        f"name lists built in memory from {len(scope)} worksheets: {len(staff)} staff first "
        f"names, {len(known)} known first names, {len(extra)} promoted by the corpus pass "
        f"over {len(comments)} comments (nothing written - D-003, D-041)"
    )

    frames = [
        ingest_sheet(mapping, f, s, r, c, (staff, known, extra), rec) for f, s, r, c in scope
    ]
    df = pd.concat([f for f in frames if not f.empty], ignore_index=True)
    df = df.sort_values(["dealer_code", "feedback_date", "source_file", "source_row"])
    df = df.reset_index(drop=True)
    df["feedback_id"] = [f"F{i + 1:06d}" for i in range(len(df))]
    df["feedback_date"] = pd.to_datetime(df["feedback_date"])
    for col, dtype in schema.DTYPES.items():
        df[col] = df[col].astype(dtype)
    return df[list(schema.COLUMNS)], rec


def _all_comments(mapping: dict, scope: list[tuple]) -> list[str]:
    """Every comment in scope, raw, in memory only - the corpus pass needs them all."""
    texts: list[str] = []
    for fname, sheet_key, ref, _code in scope:
        layout = mapping["layouts"][ref]
        comment_cols = [c for c, role in (layout.get("columns") or {}).items() if role == "comment"]
        if not comment_cols:
            continue
        base, _start = sheet_base_and_start(sheet_key)
        rows = read_rows(RAW / fname, base if base else None, layout)
        if not rows:
            continue
        header, body = slice_table(rows, layout, _next_start(mapping, fname, sheet_key))
        for col in comment_cols:
            if col not in header:
                continue
            j = header.index(col)
            texts += [c[j] for _r, c in body if isinstance(c[j], str) and c[j].strip()]
    return texts


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dealers", nargs="*", help="dealer codes to ingest (default: all)")
    ap.add_argument("--no-ner", action="store_true", help="skip spaCy (faster; weaker redaction)")
    ap.add_argument("--out", default=str(OUT_PARQUET))
    args = ap.parse_args(argv)

    dealers = set(args.dealers) if args.dealers else None
    df, rec = ingest(dealers, use_ner=not args.no_ner)

    problems = schema.validate_frame(df, dealer_codes())
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(out, index=False)

    write_reconciliation(df, rec, problems, dealers)
    print(f"{len(df)} rows -> {out}")
    print(f"reconciliation -> {RECONCILIATION.relative_to(ROOT)}")
    if problems:
        print("\nSCHEMA PROBLEMS:")
        for p in problems:
            print("  -", p)
        return 1
    print("schema: OK")
    return 0


def write_reconciliation(
    df: pd.DataFrame, rec: Reconciliation, problems: list[str], dealers: set[str] | None
) -> None:
    drops = rec.total_drops()
    read = sum(rec.rows_read.values())
    # A pivot's source rows are counts, not feedback: they leave the arithmetic and the
    # rows they expand into come back in. Same identity as row_budget in columns.yaml.
    pivot_kept = rec.pivot_source_rows
    pivot_out = rec.pivot_expanded_rows
    expected = read - sum(drops.values()) - pivot_kept + pivot_out
    closes = expected == len(df)
    lines = [
        "# Reconciliation: rows in, rows out, every drop with a reason",
        "",
        f"**Run:** {dt.datetime.now():%Y-%m-%d %H:%M} · "
        f"**Scope:** {'pilot - ' + ', '.join(sorted(dealers)) if dealers else 'all dealers'}",
        "",
        "Generated by `python -m src.ingest`. The arithmetic below has to close:",
        "rows read = rows out + rows dropped. Every drop carries its reason (D-002 (c)).",
        "",
        "## Totals",
        "",
        "| | Rows |",
        "|---|---:|",
        f"| Read from the worksheets in scope | {read} |",
        f"| Dropped, with a reason each | −{sum(drops.values())} |",
        f"| Pivot source rows (counts, not feedback) | −{pivot_kept} |",
        f"| Rows those counts expand into | +{pivot_out} |",
        f"| **Expected out** | **{expected}** |",
        f"| Written to the dataset | {len(df)} |",
        f"| **Arithmetic closes** | **{'YES' if closes else 'NO'}** |",
        "",
        "## Drops by reason",
        "",
        "| Reason | Rows |",
        "|---|---:|",
    ]
    for reason, n in sorted(drops.items(), key=lambda kv: -kv[1]):
        lines.append(f"| `{reason}` | {n} |")

    lines += [
        "",
        "## Per dealer",
        "",
        "| Dealer | Rows | First | Last | Mean rating |",
        "|---|---:|---|---|---:|",
    ]
    for code, g in df.groupby("dealer_code", observed=True):
        lines.append(
            f"| {code} | {len(g)} | {g['feedback_date'].min():%Y-%m-%d} | "
            f"{g['feedback_date'].max():%Y-%m-%d} | {g['rating_1to5'].mean():.2f} |"
        )

    lines += [
        "",
        "## Per worksheet",
        "",
        "| Worksheet | Read | Out | Dropped |",
        "|---|---:|---:|---|",
    ]
    for key in sorted(rec.rows_read):
        d = rec.drops.get(key, Counter())
        detail = ", ".join(f"{r} {n}" for r, n in sorted(d.items())) or "-"
        lines.append(f"| {key} | {rec.rows_read[key]} | {rec.rows_out.get(key, 0)} | {detail} |")

    lines += [
        "",
        "## Redaction (D-026, D-033)",
        "",
        "| Token | Times applied |",
        "|---|---:|",
    ]
    for token, n in sorted(rec.tokens.items(), key=lambda kv: -kv[1]):
        lines.append(f"| `{token}` | {n} |")

    lines += ["", "## Notes", ""]
    lines += [f"- {n}" for n in rec.notes]
    lines += [
        "",
        "## Schema check",
        "",
        ("No problems: the frame matches `src/schema.py` and nothing outside the allowlist "
         "reached the output." if not problems else "**PROBLEMS:**"),
    ]
    lines += [f"- {p}" for p in problems]
    lines.append("")

    RECONCILIATION.parent.mkdir(parents=True, exist_ok=True)
    RECONCILIATION.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())

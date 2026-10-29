"""Profile the structure of raw feedback files (Wave 1, brief agents/briefs/w1_profilers.md).

Writes one JSON per file to reports/profiles/ plus reports/profiles/_index.csv.

Privacy rule (D-003): values are only listed for category-like columns (department, rating,
site, and short low-cardinality "other" columns whose names don't look personal). Comment,
identifier, name, contact and vehicle columns are described by type, null % and length only.

Usage:
    python scripts/profile_file.py data/raw/feedback/FILE [FILE ...]
    python scripts/profile_file.py --all
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import io
import json
import re
import sys
from collections import Counter
from pathlib import Path

import openpyxl

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw" / "feedback"
OUT = ROOT / "reports" / "profiles"

ROLE_PATTERNS = [  # first match wins; checked against the lower-cased header
    ("comment", r"comment|feedback|verbatim|remark|note|text|what could|why"),
    ("rating", r"rating|score|satisf|nps|stars?\b|csat|out of|/\s*10|/\s*5"),
    ("date", r"date|when|day|time|period|month|submitted|received"),
    ("department", r"dept|department|area|division|team|section|^svc$"),
    ("site", r"site|branch|location|dealer|store|outlet"),
    ("contact", r"phone|mobile|email|e-mail|contact|address|postcode|suburb"),
    ("name", r"name|customer$|client$|surname|first|last"),
    ("vehicle", r"model|make|vehicle|car\b|vin|rego|registration|plate"),
    ("identifier", r"\bid\b|_id|id$|no\.?$|number|ref|dms|job|ro\b|invoice|account|cust"),
]
LISTABLE_ROLES = {"department", "rating", "site"}
PERSONAL_HINT = re.compile(r"name|phone|mobile|email|address|cust|client|rego|vin|staff|advisor", re.I)
SUMMARY_ROW = re.compile(r"^\s*(total|average|avg|mean|count|summary|note|notes|nps|overall)\b", re.I)
DATE_FORMATS = [
    "%Y-%m-%d", "%d/%m/%Y", "%d/%m/%y", "%d-%m-%Y", "%d.%m.%Y", "%m/%d/%Y", "%Y/%m/%d",
    "%d %b %Y", "%d %B %Y", "%b %d %Y", "%d-%b-%Y", "%d-%b-%y", "%Y-%m-%d %H:%M:%S",
    "%d/%m/%Y %H:%M", "%d/%m/%Y %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%Y%m%d",
]
MAX_LISTED = 40


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


# ---------- reading ----------

def read_csv(path: Path) -> tuple[list[dict], dict]:
    raw = path.read_bytes()
    meta: dict = {"bom": raw.startswith(b"\xef\xbb\xbf")}
    for enc in ("utf-8-sig", "cp1252", "latin-1"):
        try:
            text = raw.decode(enc)
            meta["encoding"] = enc
            break
        except UnicodeDecodeError:
            continue
    sample = text[:20000]
    try:
        delim = csv.Sniffer().sniff(sample, delimiters=",;\t|").delimiter
    except csv.Error:
        delim = ","
    meta["delimiter"] = {"\t": "tab"}.get(delim, delim)
    rows = list(csv.reader(io.StringIO(text), delimiter=delim))
    rows = [[c if c != "" else None for c in r] for r in rows]
    return [{"name": None, "state": "n/a (csv)", "rows": rows, "merged": 0}], meta


def read_xlsx(path: Path) -> tuple[list[dict], dict]:
    wb = openpyxl.load_workbook(path, data_only=True)
    sheets = []
    for ws in wb.worksheets:
        rows = [list(r) for r in ws.iter_rows(values_only=True)]
        sheets.append({
            "name": ws.title,
            "state": ws.sheet_state,
            "rows": rows,
            "merged": len(ws.merged_cells.ranges),
        })
    return sheets, {}


# ---------- structure ----------

def is_blank(row) -> bool:
    return all(v is None or (isinstance(v, str) and not v.strip()) for v in row)


def find_header(rows: list[list]) -> tuple[int | None, str]:
    """Header = first row (within the top 20) with >=2 short text cells, followed by data rows."""
    for i, row in enumerate(rows[:20]):
        cells = [v for v in row if v is not None and not (isinstance(v, str) and not v.strip())]
        texts = [v for v in cells if isinstance(v, str) and len(v.strip()) <= 60]
        if len(texts) >= 2 and len(texts) >= 0.6 * len(cells):
            following = [r for r in rows[i + 1 : i + 6] if not is_blank(r)]
            if following:
                why = f"row {i + 1}: {len(texts)} text cells, followed by data"
                return i, why
    return None, "no header-like row in the first 20 rows"


def classify_role(header: str | None) -> str:
    h = (header or "").strip().lower()
    for role, pat in ROLE_PATTERNS:
        if re.search(pat, h):
            return role
    return "other"


# ---------- value parsing ----------

def parse_date(v) -> tuple[dt.date | None, str | None]:
    if v is None:
        return None, None
    if isinstance(v, dt.datetime):
        return v.date(), "excel datetime"
    if isinstance(v, dt.date):
        return v, "excel date"
    if isinstance(v, (int, float)) and not isinstance(v, bool):
        if 30000 <= v <= 60000:  # Excel serial day number
            return (dt.date(1899, 12, 30) + dt.timedelta(days=int(v))), "excel serial number"
        if 19000101 <= v <= 21001231:
            try:
                return dt.datetime.strptime(str(int(v)), "%Y%m%d").date(), "yyyymmdd number"
            except ValueError:
                return None, None
        return None, None
    s = str(v).strip()
    for fmt in DATE_FORMATS:
        try:
            return dt.datetime.strptime(s, fmt).date(), fmt
        except ValueError:
            continue
    return None, None


def to_number(v):
    if isinstance(v, bool):
        return None
    if isinstance(v, (int, float)):
        return v
    if isinstance(v, str):
        s = v.strip()
        try:
            return float(s) if "." in s else int(s)
        except ValueError:
            return None
    return None


def value_type(v) -> str:
    if v is None:
        return "null"
    if isinstance(v, bool):
        return "bool"
    if isinstance(v, (dt.datetime, dt.date)):
        return "date"
    if isinstance(v, (int, float)):
        return "number"
    s = str(v).strip()
    if to_number(s) is not None:
        return "numeric text"
    if parse_date(s)[0] is not None:
        return "date text"
    return "text"


def norm_listed(v):
    if isinstance(v, float) and v.is_integer():
        return int(v)
    if isinstance(v, (dt.datetime, dt.date)):
        return v.isoformat()
    return v if not isinstance(v, str) else v


def profile_column(name, values: list, n_rows: int) -> dict:
    role = classify_role(name)
    non_null = [v for v in values if v is not None and not (isinstance(v, str) and not v.strip())]
    types = Counter(value_type(v) for v in non_null)
    col: dict = {
        "name": name,
        "proposed_role": role,
        "null_pct": round(100 * (1 - len(non_null) / n_rows), 1) if n_rows else None,
        "n_distinct": len({str(v).strip() for v in non_null}),
        "types": dict(types.most_common()),
    }

    # content-based nudges where the header was unhelpful
    if role == "other" and non_null:
        dates = sum(parse_date(v)[0] is not None for v in non_null)
        if dates / len(non_null) > 0.9:
            col["proposed_role"] = role = "date"
            col["role_note"] = "inferred from content (values parse as dates)"

    if role == "date":
        parsed = [parse_date(v) for v in non_null]
        ok = [d for d, _ in parsed if d is not None]
        col["date_formats"] = dict(Counter(f for _, f in parsed if f).most_common())
        col["date_min"] = min(ok).isoformat() if ok else None
        col["date_max"] = max(ok).isoformat() if ok else None
        col["unparseable"] = len(non_null) - len(ok)
        if ok:
            col["ambiguous_day_month"] = sum(
                1 for v in non_null if isinstance(v, str) and re.match(r"^\s*(0?[1-9]|1[0-2])[/-](0?[1-9]|1[0-2])[/-]", v)
            )
    if role == "rating":
        nums = [to_number(v) for v in non_null]
        good = [x for x in nums if x is not None]
        col["numeric_share"] = round(len(good) / len(non_null), 3) if non_null else None
        if good:
            col["min"], col["max"] = min(good), max(good)

    listable = role in LISTABLE_ROLES or (
        role == "other"
        and col["n_distinct"] <= 12
        and not PERSONAL_HINT.search(str(name or ""))
        and all(len(str(v)) <= 25 for v in non_null)
    )
    if listable:
        counts = Counter(norm_listed(v.strip() if isinstance(v, str) else v) for v in non_null)
        col["values"] = {str(k): c for k, c in counts.most_common(MAX_LISTED)}
        if len(counts) > MAX_LISTED:
            col["values_truncated"] = len(counts) - MAX_LISTED
    else:
        lengths = [len(str(v)) for v in non_null]
        if lengths:
            lengths.sort()
            col["length"] = {
                "min": lengths[0],
                "median": lengths[len(lengths) // 2],
                "max": lengths[-1],
            }
        col["values"] = "withheld (privacy rule)"
    return col


def profile_sheet(sheet: dict) -> tuple[dict, list[tuple]]:
    rows = sheet["rows"]
    out: dict = {
        "name": sheet["name"],
        "state": sheet["state"],
        "merged_cells": sheet["merged"],
        "dimensions_raw": {"rows": len(rows), "cols": max((len(r) for r in rows), default=0)},
    }
    oddities: list[str] = []
    if sheet["state"] not in ("visible", "n/a (csv)"):
        oddities.append(f"sheet is {sheet['state']}")
    if sheet["merged"]:
        oddities.append(f"{sheet['merged']} merged cell ranges")

    h, why = find_header(rows)
    out["header_row"] = (h + 1) if h is not None else None
    out["header_reason"] = why
    if h is None:
        out["data_rows"] = 0
        oddities.append("no tabular data found")
        out["oddities"] = oddities
        return out, []
    if h > 0:
        oddities.append(f"{h} row(s) above the header (titles or notes)")

    width = max(len(r) for r in rows[h:])
    header = list(rows[h]) + [None] * (width - len(rows[h]))
    header = [str(c).strip() if c is not None else None for c in header]
    body = [list(r) + [None] * (width - len(r)) for r in rows[h + 1 :]]

    blank_idx = [i for i, r in enumerate(body) if is_blank(r)]
    summary_idx = [
        i for i, r in enumerate(body)
        if not is_blank(r) and any(isinstance(v, str) and SUMMARY_ROW.match(v) for v in r[:3])
    ]
    data = [r for i, r in enumerate(body) if i not in set(blank_idx) | set(summary_idx)]

    # trailing vs interior blank rows
    if blank_idx:
        last_data = max((i for i, r in enumerate(body) if not is_blank(r)), default=-1)
        interior = [i for i in blank_idx if i < last_data]
        if interior:
            oddities.append(f"{len(interior)} blank row(s) inside the data")
    if summary_idx:
        oddities.append(f"{len(summary_idx)} summary/notes-like row(s) (e.g. Total, Average, Note)")

    # drop fully empty columns but record them
    empty_cols = [header[j] or f"col{j + 1}" for j in range(width) if all(r[j] is None for r in data)]
    keep = [j for j in range(width) if not all(r[j] is None for r in data)]
    if empty_cols:
        oddities.append(f"{len(empty_cols)} empty column(s)")
    unnamed = [j for j in keep if not header[j]]
    if unnamed:
        oddities.append(f"{len(unnamed)} column(s) with data but no header")
    dupes = [n for n, c in Counter(header[j] for j in keep if header[j]).items() if c > 1]
    if dupes:
        oddities.append(f"duplicate header names: {dupes}")

    out["data_rows"] = len(data)
    out["columns"] = [profile_column(header[j], [r[j] for r in data], len(data)) for j in keep]

    roles = Counter(c["proposed_role"] for c in out["columns"])
    for need in ("date", "department", "rating", "comment"):
        if roles.get(need, 0) == 0:
            oddities.append(f"no column proposed as '{need}'")
        elif roles[need] > 1:
            oddities.append(f"{roles[need]} columns proposed as '{need}' (pick one)")
    site_cols = [c for c in out["columns"] if c["proposed_role"] == "site"]
    if site_cols and isinstance(site_cols[0].get("values"), dict) and len(site_cols[0]["values"]) > 1:
        oddities.append(f"site column has {len(site_cols[0]['values'])} distinct spellings (possibly more than one site)")
    out["oddities"] = oddities

    # row fingerprints for cross-file duplicate checks (kept in memory only, never written)
    fps = [tuple(str(r[j]).strip() if r[j] is not None else "" for j in keep) for r in data]
    return out, fps


def profile_file(path: Path) -> tuple[dict, dict]:
    if path.suffix.lower() == ".csv":
        sheets, meta = read_csv(path)
        ftype = "csv"
    else:
        sheets, meta = read_xlsx(path)
        ftype = "xlsx"
    prof: dict = {
        "file": path.name,
        "type": ftype,
        "bytes": path.stat().st_size,
        "sha256": sha256(path),
        **meta,
        "sheets": [],
    }
    fingerprints: dict = {}
    for s in sheets:
        sp, fps = profile_sheet(s)
        prof["sheets"].append(sp)
        fingerprints[s["name"] or "csv"] = fps
    prof["data_rows_total"] = sum(s.get("data_rows", 0) for s in prof["sheets"])
    prof["oddities"] = [f"[{s['name'] or 'csv'}] {o}" for s in prof["sheets"] for o in s["oddities"]]
    return prof, fingerprints


# ---------- cross-file checks ----------

def overlap_report(fp_by_file: dict[str, dict]) -> list[dict]:
    """Pairs of files that share data rows (exact match on all kept cells)."""
    flat = {f: {row for fps in sheets.values() for row in fps} for f, sheets in fp_by_file.items()}
    names = sorted(flat)
    out = []
    for i, a in enumerate(names):
        for b in names[i + 1 :]:
            if not flat[a] or not flat[b]:
                continue
            shared = len(flat[a] & flat[b])
            if shared:
                out.append({
                    "file_a": a, "file_b": b, "shared_rows": shared,
                    "rows_a": len(flat[a]), "rows_b": len(flat[b]),
                    "a_contained_in_b": flat[a] <= flat[b],
                    "b_contained_in_a": flat[b] <= flat[a],
                })
    return out


def write_index(profiles: list[dict], overlaps: list[dict]) -> None:
    with open(OUT / "_index.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["file", "type", "sheets", "hidden_sheets", "data_rows", "date_min", "date_max",
                    "rating_values", "n_oddities"])
        for p in sorted(profiles, key=lambda x: x["file"].lower()):
            cols = [c for s in p["sheets"] for c in s.get("columns", [])]
            dmins = [c["date_min"] for c in cols if c.get("date_min")]
            dmaxs = [c["date_max"] for c in cols if c.get("date_max")]
            rvals = sorted({k for c in cols if c["proposed_role"] == "rating" and isinstance(c.get("values"), dict)
                            for k in c["values"]})
            w.writerow([
                p["file"], p["type"], len(p["sheets"]),
                sum(s["state"] not in ("visible", "n/a (csv)") for s in p["sheets"]),
                p["data_rows_total"], min(dmins) if dmins else "", max(dmaxs) if dmaxs else "",
                "|".join(rvals[:15]), len(p["oddities"]),
            ])
    (OUT / "_overlaps.json").write_text(json.dumps(overlaps, indent=2))


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="*")
    ap.add_argument("--all", action="store_true")
    args = ap.parse_args(argv)
    paths = sorted(p for p in RAW.iterdir() if p.suffix.lower() in (".csv", ".xlsx")
                   and not p.name.startswith("~$")) if args.all else [Path(f) for f in args.files]
    OUT.mkdir(parents=True, exist_ok=True)
    profiles, fps = [], {}
    for p in paths:
        prof, fp = profile_file(p)
        profiles.append(prof)
        fps[p.name] = fp
        (OUT / f"{p.stem}.json").write_text(json.dumps(prof, indent=2, default=str), encoding="utf-8")
        print(f"{p.name}: {prof['data_rows_total']} rows, {len(prof['sheets'])} sheet(s), "
              f"{len(prof['oddities'])} oddities")
    overlaps = overlap_report(fps)
    write_index(profiles, overlaps)
    for o in overlaps:
        print(f"OVERLAP {o['file_a']} <-> {o['file_b']}: {o['shared_rows']} shared rows")
    return 0


if __name__ == "__main__":
    sys.exit(main())

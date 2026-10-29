# ruff: noqa: E501  (long lines are Markdown table rows in the report output)
"""Rating sanity check across every sheet (Wave 1 follow-up; feeds D-020).

For each file / sheet / layout: finds the rating column, identifies its scale, applies the proposed
mapping to 1-5 and reports anything that does not map. Reads ratings only, so the output holds no PII.

    python scripts/check_ratings.py            # writes reports/rating_check.md
"""

from __future__ import annotations

import math
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import profile_file as pf  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw" / "feedback"
OUT = ROOT / "reports" / "rating_check.md"
EXCLUDED = {"Chermside Q1 2026 FINAL.xlsx"}  # D-027
# Found by the profiler's within-file overlap check; excluded from the totals below.
DUPLICATE_SHEETS = {("Penrith Feedback.xlsx", "Jun 26"): "Jul 26"}

# Word scales (lower-cased keys)
FIVE_POINT_WORDS = {
    "very dissatisfied": 1,
    "dissatisfied": 2,
    "neutral": 3,
    "satisfied": 4,
    "very satisfied": 5,
}
THREE_POINT_WORDS = {
    "bad": 1,
    "ok": 3,
    "okay": 3,
    "average": 3,
    "medium": 3,
    "good": 5,
}  # owner rule


def to_num(v):
    if isinstance(v, bool) or v is None:
        return None
    if isinstance(v, (int, float)):
        return float(v)
    s = str(v).strip()
    try:
        return float(s)
    except ValueError:
        return None


def round_half_up(x: float) -> int:
    return int(math.floor(x + 0.5))


def detect_scale(values: list) -> str:
    vals = [v for v in values if v is not None and str(v).strip() != ""]
    texts = [str(v).strip() for v in vals]
    if texts and all(set(t) <= {"★", "☆"} for t in texts):
        return "stars"
    low = {t.lower() for t in texts}
    if low and low <= set(FIVE_POINT_WORDS):
        return "5-point words"
    if low and low <= set(THREE_POINT_WORDS):
        return "3-point words"
    nums = [to_num(v) for v in vals]
    good = [n for n in nums if n is not None]
    if not good:
        return "unknown"
    if max(good) <= 5 and min(good) >= 1:
        return "1-5"
    if max(good) <= 10 and min(good) >= 1:
        return "1-10"
    if max(good) <= 10 and min(good) >= 0:
        return "0-10"
    return "unknown"


def map_value(v, scale: str):
    """Return (mapped 1-5 int or None, problem or None)."""
    if v is None or str(v).strip() == "":
        return None, "blank"
    t = str(v).strip()
    if scale == "stars":
        if set(t) <= {"★", "☆"} and len(t) == 5:
            return t.count("★"), None
        return None, f"bad star string {t!r}"
    if scale == "5-point words":
        m = FIVE_POINT_WORDS.get(t.lower())
        return (m, None) if m else (None, f"unknown word {t!r}")
    if scale == "3-point words":
        m = THREE_POINT_WORDS.get(t.lower())
        return (m, None) if m else (None, f"unknown word {t!r}")
    n = to_num(v)
    if n is None:
        return None, f"non-numeric {t[:20]!r}"
    if n != int(n):
        return None, f"fractional {n}"
    if scale == "1-5":
        return (int(n), None) if 1 <= n <= 5 else (None, f"out of range {n}")
    if scale == "1-10":  # linear 1..10 -> 1..5, identical to ceil(x/2)
        return (
            (round_half_up(1 + (n - 1) * 4 / 9), None)
            if 1 <= n <= 10
            else (None, f"out of range {n}")
        )
    if scale == "0-10":
        return (
            (round_half_up(1 + n * 4 / 10), None) if 0 <= n <= 10 else (None, f"out of range {n}")
        )
    return None, "unknown scale"


def rating_blocks():
    """Yield (file, sheet label, header, values) for every rating column in every layout block."""
    for path in sorted(RAW.iterdir(), key=lambda p: p.name.lower()):
        if path.name.startswith("~$") or path.name in EXCLUDED:
            continue
        sheets, _ = pf.read_csv(path) if path.suffix.lower() == ".csv" else pf.read_xlsx(path)
        for whole in sheets:
            for block in pf.split_blocks(whole):
                rows = block["rows"]
                h, _ = pf.find_header(rows)
                if h is None:
                    continue
                hdr = [str(c).strip() if c is not None else "" for c in rows[h]]
                body = [r for r in rows[h + 1 :] if not pf.is_blank(r)]
                # drop summary/notes rows the same way the profiler does
                body = [
                    r
                    for r in body
                    if not any(isinstance(v, str) and pf.SUMMARY_ROW.match(v) for v in r[:3])
                ]
                cols = [j for j, c in enumerate(hdr) if pf.classify_role(c) == "rating"]
                if path.name.startswith("Toowoomba Q4"):
                    yield path.name, block["name"], "(pivot of counts)", None, rows[h:]
                    continue
                above = " ".join(str(v) for r in rows[:h] for v in r if isinstance(v, str))
                reversed_scale = bool(pf.REVERSED_SCALE.search(above))
                for j in cols:
                    vals = [r[j] if j < len(r) else None for r in body]
                    label = (block["name"] or "csv") + (
                        " ⚠ REVERSED (1 = best)" if reversed_scale else ""
                    )
                    if (path.name, block["name"]) in DUPLICATE_SHEETS:
                        label += " ⚠ COPY OF " + DUPLICATE_SHEETS[(path.name, block["name"])]
                    yield path.name, label, hdr[j], vals, None


def main() -> int:
    lines = [
        "# Rating sanity check",
        "",
        "Every rating column in every sheet and layout, its detected scale, and the proposed mapping",
        "to 1-5. Generated by `scripts/check_ratings.py`. Ratings only; no PII.",
        "",
        "**Proposed mappings**",
        "- 1-5: unchanged",
        "- 1-10: linear, `round(1 + (x-1) * 4/9)` = 1,1,2,2,3,3,4,4,5,5 for x = 1..10",
        "- Stars: number of filled stars (★)",
        "- 5-point words: Very dissatisfied 1 · Dissatisfied 2 · Neutral 3 · Satisfied 4 · Very satisfied 5",
        "- 3-point words (owner rule): Bad 1 · OK 3 · Good 5",
        "- Reversed 1-5 (a note above the header says 1 = best): 6 − x",
        "",
        "| File | Sheet / layout | Column | Scale | Rows | Blank | Problems | Raw mean | Mapped 1-5 distribution (1/2/3/4/5) | Mapped mean |",
        "|---|---|---|---|---:|---:|---|---:|---|---:|",
    ]
    by_scale: Counter = Counter()
    problems_all = []
    for fname, sheet, col, vals, pivot in rating_blocks():
        if pivot is not None:
            hdr = [str(c).strip() if c is not None else "" for c in pivot[0]]
            idx = {k: hdr.index(str(k)) for k in range(1, 6) if str(k) in hdr}
            dist = Counter()
            for r in pivot[1:]:
                label = str(r[0] or "")
                if not r[1] or "total" in label.lower():  # skip month subtotals / grand total
                    continue
                for k, j in idx.items():
                    n = to_num(r[j])
                    if n:
                        dist[k] += int(n)
            n = sum(dist.values())
            mean = sum(k * c for k, c in dist.items()) / n if n else float("nan")
            d = "/".join(str(dist.get(k, 0)) for k in range(1, 6))
            lines.append(
                f"| {fname} | {sheet} | {col} | 1-5 (counts) | {n} | 0 | none | {mean:.2f} | {d} | {mean:.2f} |"
            )
            by_scale["1-5 (counts)"] += n
            continue
        scale = detect_scale(vals)
        flip = "REVERSED" in sheet
        mapped, probs = [], Counter()
        for v in vals:
            m, p = map_value(v, scale)
            if m is not None and flip:
                m = 6 - m
            if m is not None:
                mapped.append(m)
            elif p == "blank":
                probs["blank"] += 1
            else:
                probs[p] += 1
        blanks = probs.pop("blank", 0)
        nums = [to_num(v) for v in vals if to_num(v) is not None]
        raw_mean = (
            f"{sum(nums) / len(nums):.2f}" if nums and scale in ("1-5", "1-10", "0-10") else "–"
        )
        dist = Counter(mapped)
        d = "/".join(str(dist.get(k, 0)) for k in range(1, 6))
        mm = f"{sum(mapped) / len(mapped):.2f}" if mapped else "–"
        ptxt = "; ".join(f"{k} ×{c}" for k, c in probs.items()) or "none"
        shown_scale = scale + (" reversed → 6−x" if flip else "")
        lines.append(
            f"| {fname} | {sheet} | {col} | {shown_scale} | {len(vals)} | {blanks} | {ptxt} | {raw_mean} | {d} | {mm} |"
        )
        if "COPY OF" in sheet:
            problems_all.append((fname, sheet, f"duplicate sheet, {len(vals)} rows excluded"))
            continue
        by_scale[scale + (" (reversed)" if flip else "")] += len(vals)
        if probs:
            problems_all.append((fname, sheet, ptxt))

    lines += ["", "## Rows by scale", ""]
    lines += [f"- {k}: {v}" for k, v in by_scale.most_common()]
    lines += ["", "## Values that do not map, and sheets excluded", ""]
    lines += [f"- {f} / {s}: {p}" for f, s, p in problems_all] or ["- none"]
    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    sys.exit(main())

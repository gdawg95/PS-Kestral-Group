"""PII pilot (agents/briefs/w1_pii.md): run the redactor over two real files and print a sample
for the owner to eyeball. Prints only redacted text and counts. Nothing is written to disk.

Run on the laptop (needs spaCy):
    uv run python scripts/pii_pilot.py *> logs\\pii_pilot.log
"""

from __future__ import annotations

import random
import re
import sys
from collections import Counter
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
import profile_file as pf  # noqa: E402

from src.pii import deidentify, person_candidates, promote_names  # noqa: E402

RAW = ROOT / "data" / "raw" / "feedback"
PILOT = {
    # file: source column -> role (from the Wave 1 profiles)
    "liverpool_q1_2026.csv": {
        "Date": "date", "Department": "department", "Rating": "rating", "Feedback": "comment",
        "Customer": "redact_name", "Rego": "redact_rego",
        # "Phone" is deliberately unmapped: the allowlist drops it
    },
    "bendigo feedback.csv": {
        "Date": "date", "Dept": "department", "Stars": "rating", "What did they say?": "comment",
    },
}
SAMPLE = 20
STAFF_COLUMN = re.compile(r"taken by|logged by|given by|^staff$|handled by|advisor", re.I)


def all_comments() -> list[str]:
    """Every comment in the pack, for the corpus name pass (in memory only)."""
    out: list[str] = []
    for path in sorted(RAW.iterdir()):
        if path.name.startswith("~$") or path.suffix.lower() not in (".csv", ".xlsx"):
            continue
        sheets, _ = pf.read_csv(path) if path.suffix.lower() == ".csv" else pf.read_xlsx(path)
        for whole in sheets:
            for block in pf.split_blocks(whole):
                rows = block["rows"]
                h, _ = pf.find_header(rows)
                if h is None:
                    continue
                header = [str(c).strip() if c is not None else "" for c in rows[h]]
                for j, col in enumerate(header):
                    if pf.classify_role(col) == "comment":
                        out += [r[j] for r in rows[h + 1 :] if j < len(r) and isinstance(r[j], str)]
    return out


def collect_names() -> tuple[set[str], set[str]]:
    """Staff first names (from staff columns) and all first names seen in name/staff columns.

    Held in memory only; never printed or written.
    """
    staff: set[str] = set()
    known: set[str] = set()
    for path in sorted(RAW.iterdir()):
        if path.name.startswith("~$") or path.suffix.lower() not in (".csv", ".xlsx"):
            continue
        sheets, _ = pf.read_csv(path) if path.suffix.lower() == ".csv" else pf.read_xlsx(path)
        for whole in sheets:
            for block in pf.split_blocks(whole):
                rows = block["rows"]
                h, _ = pf.find_header(rows)
                if h is None:
                    continue
                header = [str(c).strip() if c is not None else "" for c in rows[h]]
                for j, col in enumerate(header):
                    vals = [r[j].strip() for r in rows[h + 1 :]
                            if j < len(r) and isinstance(r[j], str) and r[j].strip()]
                    if not vals:
                        continue
                    if STAFF_COLUMN.search(col) or (not col and pf._mostly_first_names(vals)):
                        staff.update(v for v in vals if pf.FIRST_NAME_LIKE.match(v))
                    elif pf.classify_role(col) == "name":
                        known.update(re.split(r"[\s.]+", v)[0] for v in vals)
    staff.discard("Staff")
    return staff, known | staff


def main() -> int:
    rng = random.Random(42)
    staff, known = collect_names()
    comments = all_comments()
    candidates = person_candidates(comments)
    extra = promote_names(comments, candidates) - staff
    print(f"Name lists built in memory (not printed): {len(staff)} staff first names, "
          f"{len(known)} known first names, {len(extra)} names promoted from "
          f"{len(comments)} comments by the corpus pass\n")
    grand: Counter = Counter()
    pool: list[tuple[str, str, bool]] = []
    for fname, mapping in PILOT.items():
        df = pd.read_csv(RAW / fname, sep=None, engine="python", encoding="utf-8-sig", dtype=str)
        out, counts = deidentify(df, mapping, fname, staff_names=staff, known_names=known,
                                 extra_names=extra)
        grand.update(counts)
        n_comments = out["comment"].notna().sum()
        print(f"{fname}: {len(out)} rows, {n_comments} comments, tokens: {dict(counts) or 'none'}")
        print(f"  columns kept: {list(out.columns)}")
        for c in out["comment"].dropna():
            pool.append((fname, c, "[" in c))
    print(f"\nTOTAL tokens: {dict(grand) or 'none'}")

    # Leak counter: known first names still present (case-sensitive), counts only.
    names = sorted(known | extra, key=len, reverse=True)
    leak_pat = re.compile(r"(?<!\w)(?:" + "|".join(re.escape(n) for n in names if len(n) >= 3)
                          + r")(?!\w)")
    staff_pat = re.compile(r"(?<!\w)(?:" + "|".join(re.escape(n) for n in staff) + r")(?!\w)", re.I)
    still_known = sum(1 for _, c, _ in pool if leak_pat.search(c))
    still_staff = sum(1 for _, c, _ in pool if staff_pat.search(c))
    print(f"LEAK CHECK: comments still containing a staff first name (any case): {still_staff}")
    print(f"LEAK CHECK: comments still containing a known first name (exact case): {still_known} "
          "(may include ordinary words that are also first names, e.g. 'Will')\n")

    with_tokens = [p for p in pool if p[2]]
    without = [p for p in pool if not p[2]]
    pick = rng.sample(with_tokens, min(10, len(with_tokens)))
    pick += rng.sample(without, min(SAMPLE - len(pick), len(without)))
    print(f"SAMPLE of {len(pick)} redacted comments ({min(10, len(with_tokens))} contain a token).")
    print("Check each one: is any name, phone, email, address or plate still visible?\n")
    for i, (fname, text, _) in enumerate(pick, 1):
        print(f"{i:>2}. [{fname}] {text}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

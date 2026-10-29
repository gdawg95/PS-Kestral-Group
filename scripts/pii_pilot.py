"""PII pilot (agents/briefs/w1_pii.md): run the redactor over two real files and print a sample
for the owner to eyeball. Prints only redacted text and token counts. Nothing is written to disk.

Run on the laptop (needs spaCy):
    uv run python scripts/pii_pilot.py *> logs\\pii_pilot.log
"""

from __future__ import annotations

import random
import sys
from collections import Counter
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.pii import deidentify  # noqa: E402

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


def main() -> int:
    rng = random.Random(42)
    grand: Counter = Counter()
    pool: list[tuple[str, str, bool]] = []
    for fname, mapping in PILOT.items():
        df = pd.read_csv(RAW / fname, sep=None, engine="python", encoding="utf-8-sig", dtype=str)
        out, counts = deidentify(df, mapping, fname)
        grand.update(counts)
        n_comments = out["comment"].notna().sum()
        print(f"{fname}: {len(out)} rows, {n_comments} comments, tokens: {dict(counts) or 'none'}")
        print(f"  columns kept: {list(out.columns)}")
        for c in out["comment"].dropna():
            pool.append((fname, c, "[" in c))
    print(f"\nTOTAL tokens: {dict(grand) or 'none'}\n")

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

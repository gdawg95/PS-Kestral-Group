"""Scan every blob in the whole git history for personal information.

    uv run python -I scripts/scan_history_pii.py

Not HEAD - every version of every file in every commit on every branch and tag. Making the
repository public publishes all of it, and `git` keeps what a later commit removed, so the
question "is there PII in this repository" is a question about history, not about the
working tree. `PUBLIC_RELEASE.md` item 3 is this script's output.

Run it again before publishing if any commit has been added since.

Two classes of hit are excluded by construction, because including them buries the signal:

  * dealer codes. `VIC01`, `QLD02` and friends match the three-letters-two-digits plate
    shape. They are the project's own site identifiers, they appear in nearly every file,
    and they identify a dealership rather than a person.
  * the synthetic fixtures. `src/pii.py` contains the redaction patterns themselves and
    worked examples in its docstrings; `tests/` contains `b@t.com`, `ABC123`,
    `0412 345 678` and the rest. Those are the test suite doing its job.

Anything else is reported with the blob, the path and the commits that carry it.

Exit 0 means clean. Exit 1 means read the output before making anything public.
"""

from __future__ import annotations

import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src import pii  # noqa: E402
from src.export import PERSON_SHAPE  # noqa: E402

SKIP_SUFFIX = {".xlsx", ".xls", ".parquet", ".png", ".pyc", ".lock", ".whl"}
DEALER_CODE = re.compile(r"^(VIC|NSW|QLD)\s?\d{2}$")
TOKEN = re.compile(r"^\[(NAME|STAFF|REGO|PHONE|EMAIL|ADDRESS)\]$")
NOQA = re.compile(r"#\s*noqa:?[^\n]*")

# Fixture values that exist only to prove the redactor works.
TEST_EMAIL_DOMAINS = ("t.com", "l.com", "example.com", "example.org", "x.com", "test.com")
TEST_PHONES = {"0412345678", "0412 345 678", "0400 000 000", "0298765432"}
TEST_PLATES = {"ABC123", "XYZ999", "ABC12D", "AB12CD", "NSW99", "1AB2CD", "1ABC234", "123ABC"}

# Files that carry real comment text, and so earn the slow spaCy pass.
COMMENT_BEARING = re.compile(
    r"(export/feedback_clean\.(csv|json)"
    r"|reports/(label_sample|labels_done)\.csv"
    r"|reports/(llm_review|theme_discovery|theme_proposal|theme_assignment"
    r"|formatting_changes|data_quality|date_edge_cases)\.md)"
)
# Paths whose whole purpose is to hold redaction patterns and fixtures.
PATTERN_SOURCES = re.compile(r"^(src/pii\.py|tests/|agents/(briefs|reports)/w1_pii\.md)")

# Name-shaped surfaces read in full and judged not to be people, so that a *new* one makes
# this script fail rather than being lost in two permanent hits. Each needs its reason, and
# the reason has to come from reading the text, not from the surface looking harmless.
ADJUDICATED_NOT_PEOPLE = {
    # Row 3256: "...surcharge' on a plain old Corsa Rubbish" - the customer ran a car model
    # and a complaint together with no full stop between them, so spaCy read one name.
    "Corsa Rubbish",
    # reports/formatting_changes.md: the Box Hill dealership's date formats. A suburb.
    "Box Hill's",
}


def git(*args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(ROOT), *args], capture_output=True, text=True, errors="replace"
    ).stdout


def real_pii(text: str) -> dict[str, list[str]]:
    """Pattern hits with dealer codes, redaction tokens and fixtures removed."""
    findings: dict[str, list[str]] = {}
    # A ruff rule code is three or four letters and three digits - `BLE001`, `SLF001` - which
    # is exactly an Australian plate shape. Strip the suppression comments rather than listing
    # the codes, so a rule suppressed for the first time next week does not reopen this.
    text = NOQA.sub("", text)

    emails = {e for e in pii.EMAIL.findall(text) if not e.lower().endswith(TEST_EMAIL_DOMAINS)}
    if emails:
        findings["email"] = sorted(emails)[:6]

    phones = {
        found.strip()
        for p in pii.PHONE.findall(text)
        for found in [p if isinstance(p, str) else p[0]]
        if found.strip() not in TEST_PHONES and found.replace(" ", "") not in TEST_PHONES
    }
    if phones:
        findings["phone"] = sorted(phones)[:6]

    addresses = {a.strip() for a in pii.ADDRESS.findall(text)}
    if addresses:
        findings["address"] = sorted(addresses)[:6]

    plates = set()
    for p in pii.REGO_SHAPE.findall(text):
        found = (p if isinstance(p, str) else p[0]).strip()
        bare = found.replace(" ", "").replace("-", "").upper()
        if DEALER_CODE.match(found) or TOKEN.match(found):
            continue
        if bare in pii.NOT_REGO or bare in TEST_PLATES:
            continue
        plates.add(found)
    if plates:
        findings["plate"] = sorted(plates)[:6]

    return findings


def person_names(text: str) -> list[str]:
    """spaCy person candidates shaped like a real name (two or more capitalised words)."""
    nlp = pii._nlp()  # noqa: SLF001 - deliberately the same model the redactor used
    found = set()
    for start in range(0, min(len(text), 900_000), 90_000):
        for ent in nlp(text[start:start + 90_000]).ents:
            if ent.label_ != "PERSON" or not PERSON_SHAPE.match(ent.text):
                continue
            words = [w for w in re.split(r"[\s'’-]+", ent.text.lower()) if len(w) > 1]
            if words and all(w in pii.NOT_NAMES for w in words):
                continue
            if ent.text in ADJUDICATED_NOT_PEOPLE:
                continue
            found.add(ent.text)
    return sorted(found)


def main() -> int:
    blobs: dict[str, set[str]] = defaultdict(set)
    for line in git("rev-list", "--all", "--objects").splitlines():
        parts = line.split(maxsplit=1)
        if len(parts) == 2:
            blobs[parts[0]].add(parts[1])

    commits = git("rev-list", "--all", "--count").strip()
    print(f"Scanning every blob across {commits} commits, all branches and tags.\n")

    pattern_hits: dict[tuple[str, str], dict[str, list[str]]] = {}
    name_hits: dict[tuple[str, str], list[str]] = {}
    checked = 0

    for sha, paths in blobs.items():
        if not paths or all(Path(p).suffix.lower() in SKIP_SUFFIX for p in paths):
            continue
        if git("cat-file", "-t", sha).strip() != "blob":
            continue
        raw = subprocess.run(
            ["git", "-C", str(ROOT), "cat-file", "blob", sha], capture_output=True
        ).stdout
        if b"\0" in raw[:4096]:
            continue
        text = raw.decode("utf-8", errors="replace")
        checked += 1
        path = sorted(paths)[0]

        if not PATTERN_SOURCES.match(path):
            found = real_pii(text)
            if found:
                pattern_hits[(sha, path)] = found
        if COMMENT_BEARING.search(path):
            names = person_names(text)
            if names:
                name_hits[(sha, path)] = names

    print(f"{checked} text blobs read.\n")

    def report(title: str, hits: dict) -> None:
        print(f"== {title} ==")
        if not hits:
            print("  none\n")
            return
        for (sha, path), detail in sorted(hits.items(), key=lambda kv: kv[0][1]):
            print(f"  {path}  (blob {sha[:10]})")
            if isinstance(detail, dict):
                for label, examples in detail.items():
                    print(f"      {label}: {examples}")
            else:
                print(f"      names: {detail}")
            for line in git("log", "--all", "--oneline", "--find-object", sha).splitlines()[:3]:
                print(f"      in {line}")
        print()

    report("Email / phone / address / plate, outside the pattern sources", pattern_hits)
    report("Person-shaped names in comment-bearing files", name_hits)

    if pattern_hits or name_hits:
        print("NOT CLEAN - read the hits above before making anything public.")
        print("A hit is not automatically a leak. Read the surrounding text: if it is a false")
        print("positive, add it to ADJUDICATED_NOT_PEOPLE with the reason, the way")
        print("`Corsa Rubbish` (a missing full stop) and `Box Hill's` (a suburb) are. If it is")
        print("a real name, it has to come out of the data and the history, not out of here.")
        return 1

    print("CLEAN: no real personal information in any version of any text file in the")
    print(f"history, beyond {len(ADJUDICATED_NOT_PEOPLE)} adjudicated false positives.")
    print("PUBLIC_RELEASE.md item 3.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

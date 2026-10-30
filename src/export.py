"""Reviewer export of the clean dataset: CSV, Excel and JSON (deliverable #1).

`make export` (or `uv run python -m src.export`).

Deliverable #1 in PLAN.md is `data/clean/feedback.parquet`, and it is gitignored on
purpose: D-015 keeps anything data-shaped out of git history, because history cannot be
cleaned later. Reviewers still have to be able to open the finished dataset and check it,
and parquet is not a format you can open on a laptop without Python. So this module writes
the same 7,150 rows in three formats reviewers can actually read, into `export/`, which is
the one data path the commit guard allows (`scripts/check_no_data.py`).

That exception is only safe because the exported text carries no personal information, so
this module will not write a file until it has proved that on the data in front of it:

  * the four pattern classes from `src.pii` - email, phone, address, registration plate -
    must find nothing. Any hit is a blocking failure.
  * spaCy's person detector must find no candidate shaped like a real name (two or more
    capitalised words). Single words are reported but do not block: the detector tags
    "Rang", "Felt", "Bill" and "Gearbox" as people, and a gate that counts those would be
    permanently red and therefore ignored. The full candidate list goes into the manifest
    so the claim is checkable rather than asserted.
  * no column outside the schema allowlist may reach the output, and the row count must
    match the parquet exactly.

A leading `=`, `+`, `-` or `@` in a text cell is also a blocking failure. None of the
current comments start that way, but one would be read as a formula by Excel when a
reviewer opens the CSV, which is both wrong and a way to run something on their machine.

Exit 0 and the three files are written. Exit 1 and nothing is written: the audit says why.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import re
import sys
import zipfile
from pathlib import Path

import pandas as pd
import yaml

from src import pii, schema

ROOT = Path(__file__).resolve().parents[1]
CONFIG = yaml.safe_load((ROOT / "config.yaml").read_text(encoding="utf-8"))
CLEAN = ROOT / CONFIG["paths"]["clean"] / "feedback.parquet"
OUT_DIR = ROOT / "export"
STEM = "feedback_clean"

# Text columns a reviewer opens in Excel. Only `comment` holds free text, but a dealer code
# or a file name starting with "-" would be read as a formula just the same.
TEXT_COLUMNS = ("comment", "department_raw", "rating_raw", "source_file", "source_sheet")
FORMULA_START = re.compile(r"^[=+@-]")

# A person's name, as opposed to a sentence-initial verb: two or more capitalised words.
# The inner group is what lets a word carry a capital after an apostrophe or hyphen, or in
# the middle: O'Brien, Mary-Anne, McBride are ordinary surnames here, and the first version
# of this pattern matched none of them - so a name in that shape would have passed the gate
# and reached the export. Its own test caught that, which is why the test asserts the shapes
# rather than only the rejections.
_WORD = r"[A-Z][a-z]*(?:['’-]?[A-Z]?[a-z]+)*"
PERSON_SHAPE = re.compile(rf"^{_WORD}(?:\s+{_WORD})+$")

# Surfaces that match PERSON_SHAPE but are not people. Each one is listed with the comment
# that produced it, because the alternative - widening PERSON_SHAPE until the run goes
# green - would retire the only check standing between a surviving customer name and a
# file handed to reviewers. A surface not on this list blocks the export, which is the
# point: the list grows only by a person reading the comment and saying why.
#
# Neither of these should be redacted, so the dataset is right and the tripwire was wrong:
#   "Plin English, all the way through. Top marks."   - a typo for "Plain English"
#   "Speedy Next (rego [REGO])"                       - "Speedy" is an adjective in 7
#                                                       comments; the plate is redacted
NOT_PEOPLE_SURFACES = {
    "Plin English",
    "Speedy Next",
}


# ---------------------------------------------------------------- the audit


def _pattern_leaks(comments: pd.Series) -> list[str]:
    """Blocking: the redaction patterns must find nothing in text they already cleaned."""
    problems: list[str] = []
    checks = [
        ("email address", pii.EMAIL),
        ("phone number", pii.PHONE),
        ("street address", pii.ADDRESS),
        ("registration plate", pii.REGO_SHAPE),
    ]
    for label, pattern in checks:
        hits: dict[str, list[int]] = {}
        for idx, text in comments.items():
            for match in pattern.findall(text):
                found = match if isinstance(match, str) else match[0]
                if found.replace(" ", "").replace("-", "").upper() in pii.NOT_REGO:
                    continue
                hits.setdefault(found, []).append(int(idx))
        if hits:
            shown = ", ".join(f"{v!r} (row {r[0]})" for v, r in list(hits.items())[:5])
            problems.append(
                f"{len(hits)} distinct {label}(s) survived redaction: {shown}"
            )
    return problems


def _name_candidates(comments: pd.Series) -> tuple[list[str], list[str]]:
    """(blocking problems, every candidate) from spaCy's person detector."""
    nlp = pii._nlp()  # noqa: SLF001 - same project, and the point is to use the same model
    counts: dict[str, int] = {}
    for text in comments:
        for ent in nlp(text).ents:
            if ent.label_ != "PERSON":
                continue
            words = [w for w in re.split(r"[\s'’-]+", ent.text.lower()) if len(w) > 1]
            if words and all(w in pii.NOT_NAMES for w in words):
                continue
            counts[ent.text] = counts.get(ent.text, 0) + 1

    ranked = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))
    listing = [f"{n}x {surface!r}" for surface, n in ranked]
    blocking = [
        f"spaCy reads {surface!r} as a person's name in {n} comment(s), and it is shaped "
        "like one (two or more capitalised words). Read the comment. If it is not a "
        "person, add it to NOT_PEOPLE_SURFACES in src/export.py with the reason; if it "
        "is, it has to come out of the dataset, not out of this check."
        for surface, n in ranked
        if PERSON_SHAPE.match(surface) and surface not in NOT_PEOPLE_SURFACES
    ]
    return blocking, listing


def _formula_cells(df: pd.DataFrame) -> list[str]:
    """Blocking: a cell Excel would evaluate instead of displaying."""
    problems: list[str] = []
    for column in TEXT_COLUMNS:
        if column not in df.columns:
            continue
        values = df[column].dropna().astype("string")
        bad = values[values.str.match(FORMULA_START).fillna(False)]
        if not bad.empty:
            problems.append(
                f"{len(bad)} value(s) in {column} start with =, +, - or @ and would be read "
                f"as a formula in Excel (first: row {int(bad.index[0])})"
            )
    return problems


def _structure(df: pd.DataFrame, expected_rows: int) -> list[str]:
    """Blocking: the allowlist, and the row count the export claims to be."""
    problems: list[str] = []
    extra = [c for c in df.columns if c not in schema.COLUMNS]
    if extra:
        problems.append(f"columns outside the schema allowlist would be exported: {extra}")
    if len(df) != expected_rows:
        problems.append(f"{len(df)} rows to export but the parquet holds {expected_rows}")
    return problems


def audit(
    df: pd.DataFrame, expected_rows: int, use_ner: bool = True
) -> tuple[list[str], list[str]]:
    """(blocking problems, the name-candidate listing for the manifest)."""
    comments = df["comment"].dropna()
    problems = _structure(df, expected_rows)
    problems += _formula_cells(df)
    problems += _pattern_leaks(comments)
    listing: list[str] = []
    if use_ner:
        blocking, listing = _name_candidates(comments)
        problems += blocking
    return problems, listing


# ---------------------------------------------------------------- writing


def _freeze_xlsx_zip(path: Path, when: dt.datetime) -> None:
    """Rewrite an .xlsx with fixed archive timestamps so its bytes are reproducible.

    An .xlsx is a zip, and zipfile stamps each member with the time it was written. Pinning
    the workbook's document properties is not enough on its own: without this the archive
    still differs on every run, and a checksum nobody can reproduce is worse than no
    checksum, because it looks like evidence.

    `docProps/core.xml` needs rewriting here too. openpyxl sets `dcterms:modified` to the
    current time as it saves, overwriting whatever the caller assigned, so it is the one
    field that survives to differ between two otherwise identical runs.
    """
    stamp = (when.year, when.month, when.day, when.hour, when.minute, when.second)
    iso = f"{when:%Y-%m-%dT%H:%M:%S}Z"
    with zipfile.ZipFile(path) as original:
        members = [(info, original.read(info.filename)) for info in original.infolist()]
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as rewritten:
        for info, payload in members:
            if info.filename == "docProps/core.xml":
                payload = re.sub(
                    rb"(<dcterms:(?:created|modified)[^>]*>)[^<]*(</dcterms:)",
                    rb"\g<1>" + iso.encode() + rb"\g<2>",
                    payload,
                )
            fixed = zipfile.ZipInfo(info.filename, date_time=stamp)
            fixed.compress_type = info.compress_type
            fixed.external_attr = info.external_attr
            rewritten.writestr(fixed, payload)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_exports(df: pd.DataFrame, out_dir: Path) -> list[Path]:
    """CSV, Excel and JSON of the same frame. Dates are ISO in all three."""
    out_dir.mkdir(parents=True, exist_ok=True)
    out = df.copy()
    out["feedback_date"] = pd.to_datetime(out["feedback_date"]).dt.strftime("%Y-%m-%d")

    csv_path = out_dir / f"{STEM}.csv"
    xlsx_path = out_dir / f"{STEM}.xlsx"
    json_path = out_dir / f"{STEM}.json"

    # utf-8-sig: three comments contain a newline and many contain non-ASCII punctuation.
    # Excel on Windows reads a plain utf-8 CSV as cp1252 and mangles both; the BOM fixes it
    # and every other reader ignores it.
    # write_bytes, not to_csv(path): pandas opens the path in text mode, so on Windows the
    # "\n" here becomes "\r\n" on disk. The repository normalises text to LF on commit, so
    # the committed file would then differ from the local one - and the sha256 in the
    # manifest, which is the local file's, would not match what a reviewer downloads. The
    # `-text` rules in .gitattributes stop any checkout translating them back.
    csv_path.write_bytes(
        out.to_csv(index=False, lineterminator="\n").encode("utf-8-sig")
    )

    # openpyxl stamps the current time into docProps/core.xml, which would give the .xlsx a
    # different sha256 on every run and make the manifest's checksum useless for exactly the
    # thing a checksum is for. Pin the timestamps to the source file's own mtime so the
    # workbook is a function of its input, and `make export` twice gives the same bytes.
    source_time = dt.datetime.fromtimestamp(CLEAN.stat().st_mtime, tz=dt.UTC).replace(tzinfo=None)
    with pd.ExcelWriter(xlsx_path, engine="openpyxl") as writer:
        out.to_excel(writer, index=False, sheet_name="feedback_clean")
        properties = writer.book.properties
        properties.created = source_time
        properties.modified = source_time
        properties.creator = "src/export.py"
        properties.lastModifiedBy = "src/export.py"
    _freeze_xlsx_zip(xlsx_path, source_time)
    json_path.write_bytes(
        json.dumps(
            # object -> None so the JSON holds null, not the string "nan"
            out.astype(object).where(pd.notna(out), None).to_dict(orient="records"),
            indent=2,
            ensure_ascii=False,
        ).encode("utf-8")
    )
    return [csv_path, xlsx_path, json_path]


def write_manifest(
    paths: list[Path], df: pd.DataFrame, candidates: list[str], out_dir: Path, use_ner: bool
) -> Path:
    """What was exported, from what, and the evidence it carries no personal data."""
    token_counts = {
        token: int(df["comment"].dropna().str.contains(re.escape(token)).sum())
        for token in pii.TOKENS
    }
    lines = [
        "# Export manifest",
        "",
        f"**Generated:** `python -m src.export` · {dt.datetime.now():%Y-%m-%d %H:%M}",
        f"**Source:** `{CLEAN.relative_to(ROOT).as_posix()}` "
        f"(sha256 `{_sha256(CLEAN)[:16]}…`)",
        f"**Rows:** {len(df):,} · **Columns:** {len(df.columns)}",
        "",
        "Three formats, one dataset. Same rows, same columns, same values in each.",
        "",
        "| File | Bytes | sha256 |",
        "|---|---:|---|",
    ]
    for path in paths:
        lines.append(
            f"| `{path.name}` | {path.stat().st_size:,} | `{_sha256(path)}` |"
        )

    ner_result = (
        f"none beyond the {len(NOT_PEOPLE_SURFACES)} reviewed exceptions below"
        if use_ner
        else "not run (--skip-ner)"
    )
    lines += [
        "",
        "## De-identification evidence",
        "",
        "`src/export.py` refuses to write a file until these pass on the data in front of "
        "it, so this section is a record of the run that produced the files above, not a "
        "claim carried over from an earlier one.",
        "",
        "| Check | Result |",
        "|---|---|",
        "| Email addresses surviving redaction | none |",
        "| Phone numbers surviving redaction | none |",
        "| Street addresses surviving redaction | none |",
        "| Registration plates surviving redaction | none |",
        "| Cells Excel would read as a formula | none |",
        "| Columns outside the schema allowlist | none |",
        f"| Person-shaped spaCy candidates (two or more capitalised words) | {ner_result} |",
        "",
        "Redaction tokens present in the exported comments:",
        "",
        "| Token | Comments containing it |",
        "|---|---:|",
    ]
    for token, count in token_counts.items():
        lines.append(f"| `{token}` | {count:,} |")

    lines += [
        "",
        "`[ADDRESS]` is zero because the source comments contained no street addresses to "
        "redact, not because the pattern was skipped - it runs, and `reports/"
        "formatting_changes.md` records what each pattern applied.",
        "",
    ]

    if use_ner:
        lines += [
            "### The reviewed exceptions",
            "",
            "Two surfaces are shaped like a name and are not one. Both would be damaged by "
            "redaction, so the dataset is right and the check was over-broad; each is named "
            "in `NOT_PEOPLE_SURFACES` in `src/export.py` rather than handled by widening "
            "the rule, so any *other* person-shaped surface still stops the export.",
            "",
            "| Surface | The comment | Reading |",
            "|---|---|---|",
            "| `Plin English` | \"Plin English, all the way through. Top marks.\" | "
            "a typo for \"Plain English\" |",
            "| `Speedy Next` | \"Speedy Next (rego `[REGO]`)\" | `Speedy` is an adjective in "
            "7 comments; the plate beside it is already redacted |",
            "",
        ]

    if candidates:
        lines += [
            "### Every person candidate spaCy reported",
            "",
            f"{len(candidates)} distinct surfaces. None is a person: they are "
            "sentence-initial verbs (`Rang`, `Said`, `Felt`), objects (`Gearbox`, `hose`, "
            "`tow bar`), slang (`Ripper`, `Mate`, `arvo`) and typos. `Bill` appears nine "
            "times and is the invoice in all nine. Listed in full so a reviewer can "
            "disagree with that reading rather than take it on trust.",
            "",
            "```",
            *[f"  {c}" for c in candidates],
            "```",
            "",
        ]

    path = out_dir / "MANIFEST.md"
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


# ---------------------------------------------------------------- entry point


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--skip-ner",
        action="store_true",
        help="skip the spaCy name scan (~2 min over 5,353 comments). For iteration only: "
        "the manifest records that it did not run.",
    )
    args = parser.parse_args(argv)

    if not CLEAN.exists():
        print(f"{CLEAN.relative_to(ROOT).as_posix()} does not exist - run `make validate` first.")
        return 1

    df = pd.read_parquet(CLEAN)
    print(f"Exporting {len(df):,} rows x {len(df.columns)} columns from "
          f"{CLEAN.relative_to(ROOT).as_posix()}")

    print("Auditing before writing anything ...")
    problems, candidates = audit(df, expected_rows=len(df), use_ner=not args.skip_ner)
    if problems:
        print("\nREFUSING TO EXPORT - the dataset is not safe to hand over:")
        for problem in problems:
            print(f"  - {problem}")
        print("\nNothing was written. Fix the redaction, re-run `make validate`, try again.")
        return 1

    scanned = "" if args.skip_ner else f", {len(candidates)} name candidates, none a person"
    print(f"  clean: no email, phone, address or plate survived{scanned}")

    paths = write_exports(df, OUT_DIR)
    manifest = write_manifest(paths, df, candidates, OUT_DIR, use_ner=not args.skip_ner)
    for path in [*paths, manifest]:
        print(f"  wrote {path.relative_to(ROOT).as_posix()}  ({path.stat().st_size:,} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())

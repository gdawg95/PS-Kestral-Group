"""Tests for src/export.py - the audit that gates the export, and the three writers.

Two things are worth testing here and they are not the same thing. The writers have to
produce the same values in CSV, Excel and JSON, reproducibly. The audit has to *refuse*,
and refusing is the whole point: `export/` is the one data path the commit guard allows,
so a leak that slips past this module is a leak in a file handed to reviewers and then
committed to history that cannot be cleaned. So every blocking check gets a test that
makes it fire, not just a test that it passes on clean data.

No test reads the real dataset: each check is tested against the check.
"""

from __future__ import annotations

import datetime as dt
import json

import pandas as pd
import pytest

from src import schema
from src.export import (
    NOT_PEOPLE_SURFACES,
    PERSON_SHAPE,
    audit,
    write_exports,
    write_manifest,
)


def frame(**overrides) -> pd.DataFrame:
    """One valid exportable row, with any field overridden. Dtypes match src/schema.py."""
    row = {
        "feedback_id": "F000001",
        "dealer_code": "VIC01",
        "feedback_date": dt.date(2026, 1, 15),
        "department_raw": "Service",
        "department": "Service",
        "rating_raw": "4",
        "rating_scale": "1-5",
        "rating_1to5": 4,
        "comment": "All good, thanks.",
        "source_file": "x.xlsx",
        "source_sheet": "Sheet1",
        "source_row": 2,
        "from_summary": False,
        "date_corrected": False,
        "date_approx": False,
    }
    row.update(overrides)
    df = pd.DataFrame([row])[list(schema.COLUMNS)]
    for column, dtype in schema.DTYPES.items():
        df[column] = df[column].astype(dtype)
    return df


def problems(df: pd.DataFrame, expected_rows: int | None = None) -> list[str]:
    """The blocking problems only, with the slow spaCy pass off."""
    found, _ = audit(df, expected_rows if expected_rows is not None else len(df), use_ner=False)
    return found


# ---------------------------------------------------------------- the audit refuses


def test_clean_frame_passes():
    assert problems(frame()) == []


@pytest.mark.parametrize(
    ("label", "comment"),
    [
        ("email", "Email me at dave.smith@example.com next time."),
        ("phone", "Call me on 0412 345 678."),
        ("phone in brackets", "Ring (02) 9123 4567 instead."),
        ("address", "I live at 14 George Street and nobody came."),
        ("plate", "My car ABC123 was not ready."),
    ],
)
def test_surviving_pii_blocks_the_export(label, comment):
    """Each pattern class has to stop the export on its own."""
    found = problems(frame(comment=comment))
    assert found, f"a surviving {label} did not block the export"


def test_redacted_comment_does_not_trip_the_patterns():
    """The tokens themselves must not read as the thing they replaced."""
    tokens = "[NAME] rang about [REGO], left [PHONE] and [EMAIL], lives at [ADDRESS]."
    assert problems(frame(comment=tokens)) == []


@pytest.mark.parametrize("prefix", ["=", "+", "-", "@"])
def test_formula_leading_cell_blocks_the_export(prefix):
    """Excel would evaluate these instead of showing them."""
    found = problems(frame(comment=f"{prefix}HYPERLINK('http://x','click')"))
    assert any("formula" in p for p in found), found


def test_formula_check_covers_every_text_column():
    found = problems(frame(source_sheet="=cmd"))
    assert any("source_sheet" in p for p in found), found


def test_column_outside_the_allowlist_blocks_the_export():
    df = frame()
    df["customer_name"] = "Dave Smith"
    found = problems(df)
    assert any("allowlist" in p for p in found), found


def test_row_count_mismatch_blocks_the_export():
    """The export must not claim to be a dataset it is not."""
    found = problems(frame(), expected_rows=7150)
    assert any("rows" in p for p in found), found


def test_rows_without_comments_are_fine():
    assert problems(frame(comment=None)) == []


# ---------------------------------------------------------------- the name tripwire


def test_person_shape_matches_a_name_and_not_a_sentence_opener():
    assert PERSON_SHAPE.match("Dave Smith")
    assert PERSON_SHAPE.match("Mary-Anne O’Brien")
    for not_a_name in ("Rang", "Felt", "Bill", "GREAT COMMS", "Rang 3x", "tow bar", "Veyra S4"):
        assert not PERSON_SHAPE.match(not_a_name), not_a_name


def test_reviewed_exceptions_are_person_shaped():
    """If one stopped matching, it would be dead weight hiding a live check."""
    for surface in NOT_PEOPLE_SURFACES:
        assert PERSON_SHAPE.match(surface), f"{surface} no longer needs an exception"


def test_a_person_shaped_name_blocks_the_export():
    found, _ = audit(frame(comment="Dave Smith was great."), expected_rows=1, use_ner=True)
    assert any("Dave Smith" in p for p in found), found


def test_a_reviewed_exception_does_not_block_the_export():
    df = frame(comment="Plin English, all the way through. Top marks.")
    found, candidates = audit(df, expected_rows=1, use_ner=True)
    assert found == []
    assert any("Plin English" in c for c in candidates), candidates


# ---------------------------------------------------------------- the writers


def two_rows() -> pd.DataFrame:
    return pd.concat(
        [frame(), frame(feedback_id="F000002", comment=None, rating_1to5=2, source_row=3)],
        ignore_index=True,
    )


def test_all_three_formats_hold_the_same_values(tmp_path):
    df = two_rows()
    write_exports(df, tmp_path)

    def normalise(series):
        return [None if pd.isna(v) else str(v) for v in series.tolist()]

    expected = df.copy()
    expected["feedback_date"] = pd.to_datetime(expected["feedback_date"]).dt.strftime("%Y-%m-%d")

    csv = pd.read_csv(tmp_path / "feedback_clean.csv", dtype=str)
    xlsx = pd.read_excel(tmp_path / "feedback_clean.xlsx", dtype=str, engine="openpyxl")
    js = pd.DataFrame(json.loads((tmp_path / "feedback_clean.json").read_text(encoding="utf-8")))

    for name, other in (("csv", csv), ("xlsx", xlsx), ("json", js)):
        assert list(other.columns) == list(schema.COLUMNS), name
        for column in schema.COLUMNS:
            assert normalise(expected[column]) == normalise(other[column]), f"{name}.{column}"


def test_json_holds_null_not_the_string_nan(tmp_path):
    write_exports(two_rows(), tmp_path)
    records = json.loads((tmp_path / "feedback_clean.json").read_text(encoding="utf-8"))
    assert records[1]["comment"] is None


def test_dates_are_iso_in_every_format(tmp_path):
    write_exports(two_rows(), tmp_path)
    csv = pd.read_csv(tmp_path / "feedback_clean.csv", dtype=str)
    assert csv["feedback_date"].iloc[0] == "2026-01-15"
    records = json.loads((tmp_path / "feedback_clean.json").read_text(encoding="utf-8"))
    assert records[0]["feedback_date"] == "2026-01-15"


def test_csv_quotes_a_comment_containing_a_newline(tmp_path):
    df = frame(comment="Lovely lot.\n\nBill wrong though.")
    write_exports(df, tmp_path)
    back = pd.read_csv(tmp_path / "feedback_clean.csv", dtype=str)
    assert len(back) == 1
    assert "\n" in back["comment"].iloc[0]


def test_the_export_is_byte_for_byte_reproducible(tmp_path):
    """The manifest publishes a sha256; a checksum nobody can reproduce is not evidence."""
    df = two_rows()
    first = {p.name: p.read_bytes() for p in write_exports(df, tmp_path)}
    second = {p.name: p.read_bytes() for p in write_exports(df, tmp_path)}
    assert first.keys() == second.keys()
    for name in first:
        assert first[name] == second[name], f"{name} differs between two identical runs"


def test_manifest_records_a_skipped_name_scan(tmp_path):
    """A manifest that quietly implied the scan ran would be the worst failure here."""
    df = two_rows()
    paths = write_exports(df, tmp_path)
    text = write_manifest(paths, df, [], tmp_path, use_ner=False).read_text(encoding="utf-8")
    assert "--skip-ner" in text
    for path in paths:
        assert path.name in text

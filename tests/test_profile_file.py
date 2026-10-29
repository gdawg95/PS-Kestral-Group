"""Regression tests for scripts/profile_file.py header detection (synthetic rows only)."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import profile_file as pf  # noqa: E402


def sheet(rows):
    return {"name": "S", "state": "visible", "rows": rows, "merged": 0}


def test_text_date_row_is_not_a_header():
    # Tamworth: text dates; "27/10/2025" once matched the "/10" rating pattern
    row = ["27/10/2025", "Svc", "Bad", "Rang twice. No call back."]
    assert not pf._header_like(row)


def test_header_with_question_mark_is_a_header():
    # Ballarat row 2 and Bendigo
    assert pf._header_like(["Date", "Dept", "Name", "Phone", "How satisfied?", "Comments"])
    assert pf._header_like(["Date", "Dept", "Stars", "What did they say?"])


def test_second_header_splits_sheet():
    rows = [
        ["Date", "Department", "Score (1-5)", "Customer comments"],
        ["03/01/2026", "Sales", "4", "fine"],
        ["Date", "Department", "Model", "Score (out of 10)", "Customer comments"],
        ["02/02/2026", "Service", "Vista", "9", "good"],
    ]
    blocks = pf.split_blocks(sheet(rows))
    assert len(blocks) == 2
    assert blocks[1]["row_offset"] == 2


def test_text_dates_do_not_split_sheet():
    rows = [["DATE", "DEPT", "HOW WAS IT", "COMMENTS"]] + [
        [f"{d:02d}/10/2025", "Svc", "Good", "ok"] for d in range(1, 20)
    ]
    assert len(pf.split_blocks(sheet(rows))) == 1


def test_two_row_header_uses_lower_row():
    rows = [
        ["Visit", None, "Customer", None, "Feedback", None],
        ["Date", "Dept", "Name", "Phone", "How satisfied?", "Comments"],
        ["2025-10-01", "Parts", "x", "y", "Satisfied", "z"],
    ]
    blocks = pf.split_blocks(sheet(rows))
    assert len(blocks) == 1 and blocks[0].get("two_row_header")
    prof, _ = pf.profile_sheet(blocks[0])
    assert [c["name"] for c in prof["columns"]][:2] == ["Date", "Dept"]


def test_how_was_it_is_a_rating():
    assert pf.classify_role("HOW WAS IT") == "rating"

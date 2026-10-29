"""Tests for src/ingest.py — one per rule the owner decided (D-020, D-030 — D-044).

Synthetic frames only: no test here reads a spreadsheet, so the suite runs anywhere and
the owner's rules are checked against the rule, not against the data that produced it.
The mapping file itself is read, because the rules it carries (the Geelong reversal on one
sheet only, the row budget, the North QLD split) are part of the contract.
"""

from __future__ import annotations

import datetime as dt

import pandas as pd
import pytest

from src import schema
from src.ingest import (
    _named_junk,
    _site_to_code,
    _verify_named_junk,
    classify_junk,
    load_mapping,
    midpoint,
    month_from_label,
    parse_date,
    parse_month_pivot,
    sheet_base_and_start,
    slice_table,
    to_1to5,
)

# --------------------------------------------------------------- D-020 ratings


@pytest.mark.parametrize(
    ("raw", "scale", "expected"),
    [
        # 1-5: unchanged
        (1, "1-5", 1),
        (5, "1-5", 5),
        ("4", "1-5", 4),
        (0, "1-5", None),
        (6, "1-5", None),
        # 1-10 -> the owner's table: 1-2->1, 3-4->2, 5-6->3, 7-8->4, 9-10->5
        (1, "1-10", 1),
        (2, "1-10", 1),
        (3, "1-10", 2),
        (4, "1-10", 2),
        (5, "1-10", 3),
        (6, "1-10", 3),
        (7, "1-10", 4),
        (8, "1-10", 4),
        (9, "1-10", 5),
        (10, "1-10", 5),
        (11, "1-10", None),
        # reversed (D-030)
        (1, "1-5-reversed", 5),
        (2, "1-5-reversed", 4),
        (3, "1-5-reversed", 3),
        (5, "1-5-reversed", 1),
        # five satisfaction words (Ballarat)
        ("Very satisfied", "words-5", 5),
        ("very satisfied", "words-5", 5),
        ("Neutral", "words-5", 3),
        ("Very dissatisfied", "words-5", 1),
        ("Delighted", "words-5", None),
        # three words (Tamworth) — the owner's rule: no 2 and no 4 are possible
        ("Good", "words-3", 5),
        ("OK", "words-3", 3),
        ("Bad", "words-3", 1),
        # stars (Bendigo)
        ("★★★★★", "stars-5", 5),
        ("★☆☆☆☆", "stars-5", 1),
        ("★★☆", "stars-5", None),
        # no usable rating -> None, which D-031 turns into a drop
        (None, "1-5", None),
        ("", "1-5", None),
        ("   ", "1-5", None),
        ("n/a", "1-5", None),
        (4.5, "1-5", None),
        (float("nan"), "1-5", None),
    ],
)
def test_to_1to5(raw, scale, expected):
    assert to_1to5(raw, scale) == expected


def test_ten_point_scale_is_monotonic_and_covers_1_to_5():
    """Every 1-10 value maps somewhere, in order, and all five outputs are reachable."""
    mapped = [to_1to5(n, "1-10") for n in range(1, 11)]
    assert mapped == sorted(mapped)
    assert set(mapped) == {1, 2, 3, 4, 5}


def test_reversal_is_an_involution():
    """6 - x twice is the identity, so the reversal cannot be applied twice unnoticed."""
    for n in range(1, 6):
        assert to_1to5(to_1to5(n, "1-5-reversed"), "1-5-reversed") == n


def test_unknown_scale_raises_rather_than_guessing():
    with pytest.raises(ValueError, match="unknown rating scale"):
        to_1to5(3, "1-7")


# ------------------------------------------------- D-030: Geelong, one sheet only


def test_geelong_reversal_applies_to_the_2025_sheet_only():
    files = load_mapping()["files"]["Geelong Feedback.xlsx"]["sheets"]
    layouts = load_mapping()["layouts"]
    assert layouts[files["2025"]]["rating_scale"] == "1-5-reversed"
    assert layouts[files["2026"]]["rating_scale"] == "1-5"


def test_no_other_layout_uses_the_reversed_scale():
    reversed_layouts = [
        name
        for name, lay in load_mapping()["layouts"].items()
        if lay.get("rating_scale") == "1-5-reversed"
    ]
    assert reversed_layouts == ["geelong_2025"]


# ------------------------------------------------------------------ D-003 allowlist


def test_no_column_outside_the_allowlist_reaches_the_output():
    row = {c: None for c in schema.COLUMNS}
    row.update(
        feedback_id="F000001",
        dealer_code="VIC06",
        feedback_date=dt.date(2026, 1, 15),
        department_raw="Service",
        rating_raw="4",
        rating_scale="1-5",
        rating_1to5=4,
        source_file="x.xlsx",
        source_row=2,
        from_summary=False,
        date_corrected=False,
        date_approx=False,
    )
    clean = pd.DataFrame([row])
    assert schema.validate_frame(clean) == []

    leaked = clean.assign(customer_mobile="0400 000 000")
    problems = schema.validate_frame(leaked)
    assert problems and "outside the allowlist" in problems[0]
    assert "customer_mobile" in problems[0]


# ------------------------------------------------------------------- dates


@pytest.mark.parametrize(
    ("value", "fmt", "expected"),
    [
        (dt.datetime(2026, 3, 4), "excel", dt.date(2026, 3, 4)),
        ("04/03/2026", "%d/%m/%Y", dt.date(2026, 3, 4)),
        ("04/03/26", "%d/%m/%y", dt.date(2026, 3, 4)),
        ("04-Mar-26", "%d-%b-%y", dt.date(2026, 3, 4)),
        ("04 Mar 26", "%d %b %y", dt.date(2026, 3, 4)),
        ("2026-03-04 09:30:00", "%Y-%m-%d %H:%M:%S", dt.date(2026, 3, 4)),
        (45932, "excel_serial", dt.date(2025, 10, 2)),
        ("", "%d/%m/%Y", None),
        (None, "%d/%m/%Y", None),
        ("early Oct", "%d/%m/%Y", None),
    ],
)
def test_parse_date(value, fmt, expected):
    assert parse_date(value, fmt) == expected


def test_liverpool_q3_is_month_first_and_the_two_orders_disagree():
    """The one file that is mm/dd/yyyy. 03/04 must be 4 March one way, 3 April the other."""
    assert parse_date("03/04/2026", "%m/%d/%Y") == dt.date(2026, 3, 4)
    assert parse_date("03/04/2026", "%d/%m/%Y") == dt.date(2026, 4, 3)


def test_liverpool_q3_asserts_its_date_range():
    """The guard that fails the run if the file is ever re-sent day-first (D-032 #2)."""
    layouts = load_mapping()["layouts"]
    assert layouts["liverpool_q3"]["date_format"] == "%m/%d/%Y"
    assert layouts["liverpool_q3"]["assert_date_range"] == ["2026-07-01", "2026-09-30"]
    assert layouts["liverpool"]["date_format"] == "%d/%m/%Y"


# -------------------------------------------------- D-040: Ipswich approximate dates


@pytest.mark.parametrize(
    ("label", "expected"),
    [
        ("early Oct", 10),
        ("mid Nov", 11),
        ("early Jan", 1),
        ("wk1 Feb", 2),
        ("wk5 Mar", 3),
        ("early Apr", 4),
        ("mid Jun", 6),
        ("Aug?", 8),
        ("mid Sep", 9),
        ("sometime", None),
        ("", None),
    ],
)
def test_month_from_label(label, expected):
    assert month_from_label(label) == expected


def test_midpoint_of_the_neighbouring_rows():
    assert midpoint(dt.date(2025, 10, 4), dt.date(2025, 10, 9)) == dt.date(2025, 10, 6)
    assert midpoint(dt.date(2026, 5, 30), dt.date(2026, 6, 4)) == dt.date(2026, 6, 1)
    assert midpoint(dt.date(2026, 3, 27), dt.date(2026, 4, 1)) == dt.date(2026, 3, 29)


def test_midpoint_copes_with_one_sided_neighbours():
    assert midpoint(dt.date(2026, 1, 1), None) == dt.date(2026, 1, 1)
    assert midpoint(None, dt.date(2026, 1, 1)) == dt.date(2026, 1, 1)
    assert midpoint(None, None) is None


def test_the_cross_check_the_owner_relies_on():
    """Label month and neighbour midpoint agree for every one of Ipswich's 10 rows.

    This is the claim D-040 makes. The pairs are the real neighbours of each vague
    value, read from the file on 29 Oct 2026.
    """
    cases = [
        ("early Oct", dt.date(2025, 10, 4), dt.date(2025, 10, 9)),
        ("mid Nov", dt.date(2025, 11, 3), dt.date(2025, 11, 4)),
        ("early Jan", dt.date(2026, 1, 10), dt.date(2026, 1, 15)),
        ("wk1 Feb", dt.date(2026, 2, 3), dt.date(2026, 2, 5)),
        ("wk5 Mar", dt.date(2026, 3, 27), dt.date(2026, 4, 1)),
        ("early Apr", dt.date(2026, 4, 20), dt.date(2026, 4, 23)),
        ("mid Jun", dt.date(2026, 5, 30), dt.date(2026, 6, 4)),
        ("Aug?", dt.date(2026, 8, 12), dt.date(2026, 8, 12)),
        ("Aug?", dt.date(2026, 8, 25), dt.date(2026, 8, 29)),
        ("mid Sep", dt.date(2026, 9, 11), dt.date(2026, 9, 13)),
    ]
    for label, before, after in cases:
        guess = midpoint(before, after)
        assert guess.month == month_from_label(label), label


# -------------------------------------------------- D-032 #1: the Toowoomba pivot


@pytest.mark.parametrize(
    ("label", "expected"),
    [
        ("Oct-25", dt.date(2025, 10, 15)),
        ("Nov-25", dt.date(2025, 11, 15)),
        ("Dec-25", dt.date(2025, 12, 15)),
        ("Grand Total", None),
        ("", None),
    ],
)
def test_parse_month_pivot(label, expected):
    assert parse_month_pivot(label) == expected


def test_the_pivot_expects_71_rows_and_mid_month_dates():
    cfg = load_mapping()["layouts"]["toowoomba_summary"]["expand_pivot"]
    assert cfg["expected_rows"] == 71
    assert cfg["day_of_month"] == 15
    assert cfg["comment"] is None  # a summary has no text (D-032 #1)
    assert cfg["count_columns"] == ["1", "2", "3", "4", "5"]


# ------------------------------------------------- D-039/D-037: rows that are not feedback


@pytest.mark.parametrize(
    ("cells", "expected"),
    [
        ([None, None, None], "blank"),
        (["", "  ", None], "blank"),
        (["Total Oct 2025", None, 3.74], "summary_or_note"),
        (["Grand Total", None, 9], "summary_or_note"),
        (["*** NEW TEMPLATE FROM FEB 2026 ***", None, None], "summary_or_note"),
        (["Site closed 31/3/26. Any further feedback goes to Bendigo.", None, None],
         "summary_or_note"),
        (["asdf", None, None], "test_row"),
        (["TEST", "Service", 5], "test_row"),
        ([dt.datetime(2026, 1, 2), "Service", 4], None),
        (["02/01/2026", "Sales", 5], None),
    ],
)
def test_classify_junk(cells, expected):
    layout = {"drop_rows": ["blank", "summary_or_note", "test_row"]}
    assert classify_junk(cells, layout) == expected


def test_a_real_comment_that_mentions_a_total_is_not_a_summary_row():
    """The keyword only counts in the first cells, never in the comment."""
    layout = {"drop_rows": ["blank", "summary_or_note"]}
    cells = [dt.datetime(2026, 2, 2), "Service", 4, "Total cost came in under the quote, noted."]
    assert classify_junk(cells, layout) is None


def test_southports_four_junk_rows_are_named_individually():
    layout = load_mapping()["layouts"]["southport"]
    named = _named_junk(layout, ["Date", "Department", "Rating", "Comments"], "southport")
    assert named == {23: "test_row", 167: "test_row", 196: "test_row", 192: "summary_or_note"}


SOUTHPORT_HEADER = ["Date", "Department", "Rating", "Comments"]
SOUTHPORT_JUNK = [
    (23, ["01/01/1900", "Parts", 1, "TEST TEST"]),
    (167, [None, "Sales", 3, "testing new form"]),
    (192, ["asdf", None, None, "asdf"]),
    (196, ["TEST", "Service", 5, "test - ignore"]),
]


def test_the_four_named_junk_rows_verify_against_their_cell_values():
    layout = load_mapping()["layouts"]["southport"]
    _verify_named_junk(layout, SOUTHPORT_HEADER, SOUTHPORT_JUNK, "southport")  # no exception


def test_a_named_junk_row_whose_comment_changed_stops_the_run():
    """If the file is re-sent with rows shifted, we must not drop real feedback."""
    layout = load_mapping()["layouts"]["southport"]
    body = [(23, [None, "Parts", 1, "Actually a real complaint about the invoice"])]
    body += SOUTHPORT_JUNK[1:]
    with pytest.raises(ValueError, match="junk_rows expects comment"):
        _verify_named_junk(layout, SOUTHPORT_HEADER, body, "southport")


def test_a_named_junk_row_that_has_vanished_stops_the_run():
    layout = load_mapping()["layouts"]["southport"]
    with pytest.raises(ValueError, match="no longer has"):
        _verify_named_junk(layout, SOUTHPORT_HEADER, SOUTHPORT_JUNK[1:], "southport")


# ------------------------------------------------------- D-042: the North QLD split


@pytest.mark.parametrize(
    ("site", "code"),
    [
        ("Rockhampton", "QLD07"),
        ("Rocky", "QLD07"),
        ("ROK", "QLD07"),
        ("Townsville", "QLD08"),
        ("TSV", "QLD08"),
        ("Tsv", "QLD08"),
        ("  Rocky  ", "QLD07"),
    ],
)
def test_north_qld_site_to_dealer_code(site, code):
    assert _site_to_code(load_mapping()["layouts"]["northqld"], site, "k") == code


def test_an_unknown_site_stops_the_run_rather_than_guessing():
    with pytest.raises(KeyError, match="site_map"):
        _site_to_code(load_mapping()["layouts"]["northqld"], "Mackay", "k")


def test_the_split_counts_are_asserted_in_the_mapping():
    lay = load_mapping()["layouts"]["northqld"]
    assert lay["assert_split_counts"] is True
    assert lay["split"]["QLD07"]["expected_rows"] == 202
    assert lay["split"]["QLD08"]["expected_rows"] == 354
    total = sum(s["expected_rows"] for s in lay["split"].values())
    northqld = load_mapping()["files"]["North QLD feedback (Rocky + TSV).xlsx"]
    assert total == northqld["expected_rows"]


# -------------------------------------------------------- D-036: Bendigo's letter codes


def test_bendigo_letter_codes_are_spelled_out():
    dmap = load_mapping()["layouts"]["bendigo"]["department_map"]
    assert dmap == {"SV": "Service", "S": "Sales", "P": "Parts"}
    assert set(dmap.values()) <= set(schema.Department.__args__)


def test_bendigo_is_the_only_layout_that_rewrites_a_source_value():
    """D-035 keeps department_raw raw; D-036 is the single owner-approved exception."""
    with_map = [n for n, lay in load_mapping()["layouts"].items() if lay.get("department_map")]
    assert with_map == ["bendigo"]


# ------------------------------------------------------------- slicing worksheets


def test_sheet_base_and_start():
    assert sheet_base_and_start("Feedback") == ("Feedback", None)
    assert sheet_base_and_start("Feedback [layout 2, from row 37]") == ("Feedback", 37)
    assert sheet_base_and_start("Tracker [layout 1, from row 1]") == ("Tracker", 1)
    assert sheet_base_and_start(None) == (None, None)


def test_slice_table_numbers_rows_as_the_spreadsheet_does():
    rows = [
        ["Date", "Dept", "Rating"],
        ["01/01/2026", "Service", 4],
        ["02/01/2026", "Sales", 5],
    ]
    header, body = slice_table(rows, {"header_row": 1}, None)
    assert header == ["Date", "Dept", "Rating"]
    assert [r for r, _c in body] == [2, 3]  # row 1 is the header


def test_slice_table_stops_where_the_next_layout_starts():
    rows = [["Date", "Score (1-5)"], ["01/01/2026", 4], ["02/01/2026", 5]]
    rows += [["Date", "Score (out of 10)"], ["01/02/2026", 9]]
    first_header, first_body = slice_table(rows, {"header_row": 1}, next_start=4)
    second_header, second_body = slice_table(rows, {"header_row": 4}, None)
    assert first_header[1] == "Score (1-5)"
    assert [r for r, _c in first_body] == [2, 3]
    assert second_header[1] == "Score (out of 10)"
    assert [r for r, _c in second_body] == [5]


def test_slice_table_trims_trailing_empty_rows():
    rows = [["Date"], ["01/01/2026"], [None], [None]]
    _header, body = slice_table(rows, {"header_row": 1}, None)
    assert [r for r, _c in body] == [2]


def test_slice_table_pads_short_rows_to_the_header_width():
    rows = [["Date", "Dept", "Rating", "Comments"], ["01/01/2026", "Service", 4]]
    header, body = slice_table(rows, {"header_row": 1}, None)
    assert len(body[0][1]) == len(header) == 4
    assert body[0][1][3] is None


# --------------------------------------------------------- the mapping's own arithmetic


def test_the_row_budget_identity_closes():
    """7162 - 51 - 7 + 71 - 16 = 7159, the number the full run has to produce (D-039)."""
    b = load_mapping()["row_budget"]
    candidates = (
        b["source_rows_in_scope"]
        - sum(b["excluded_whole_sheet"].values())
        - b["pivot"]["toowoomba_summary_source_rows"]
        + b["pivot"]["toowoomba_summary_expanded_rows"]
    )
    assert candidates == 7175
    drops = b["dropped_rows"]
    assert drops["total"] == drops["no_rating"] + drops["summary_or_note"] + drops["test_row"]
    assert candidates - drops["total"] == b["rows_out_expected"] == 7159


def test_expected_rows_sum_to_the_budgets_source_total():
    mapping = load_mapping()
    total = sum(
        spec.get("expected_rows") or 0
        for spec in mapping["files"].values()
        if not spec.get("skip")
    )
    assert total == mapping["row_budget"]["source_rows_in_scope"] == 7162


def test_d031s_thirteen_rows_are_still_thirteen_rows():
    """The owner re-labelled 3 of D-031's 13 rows; the total must not have moved."""
    drops = load_mapping()["row_budget"]["dropped_rows"]
    assert drops["no_rating"] + drops["summary_or_note"] == 13


def test_every_layout_declares_a_scale_the_schema_knows():
    for name, lay in load_mapping()["layouts"].items():
        assert lay["rating_scale"] in schema.RatingScale.__args__, name


def test_every_role_is_one_src_pii_accepts():
    from src.pii import KEEP_ROLES, TRANSIENT_ROLES

    allowed = set(KEEP_ROLES) | set(TRANSIENT_ROLES)
    for name, lay in load_mapping()["layouts"].items():
        assert set((lay.get("columns") or {}).values()) <= allowed, name


def test_staff_columns_are_never_a_role():
    """D-041: staff columns are read for redaction, never mapped as data."""
    for name, lay in load_mapping()["layouts"].items():
        staff = set(lay.get("redact_staff") or [])
        assert not (staff & set(lay.get("columns") or {})), name

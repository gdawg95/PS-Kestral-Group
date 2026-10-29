"""Tests for src/validate.py - one per rule, on synthetic frames.

No test here reads the dataset: each rule is checked against the rule, not against the
data that happened to produce it. The two tests the brief asks for by name are
`test_reject_rule_rejects_rather_than_fixing` and `test_department_fill_is_total`.
"""

from __future__ import annotations

import datetime as dt

import pandas as pd
import pandera.pandas as pa
import pytest

from src import schema
from src.validate import (
    FIX,
    KEEP,
    REJECT,
    Rule,
    build_schema,
    date_edge_cases,
    declare_rules,
    double_entry_duplicates,
    failures_by_check,
    fill_department,
    fix_empty_comments,
)

CODES = {"VIC01", "QLD02"}
DEPTS = {"Service": "Service", "Workshop": "Service", "Sales": "Sales", "Parts": "Parts"}


def frame(**overrides) -> pd.DataFrame:
    """One valid row, with any field overridden. Dtypes match src/schema.py."""
    row = {
        "feedback_id": "F000001",
        "dealer_code": "VIC01",
        "feedback_date": dt.date(2026, 1, 15),
        "department_raw": "Service",
        "department": None,
        "rating_raw": "4",
        "rating_scale": "1-5",
        "rating_1to5": 4,
        "comment": "All good.",
        "source_file": "x.xlsx",
        "source_sheet": "Sheet1",
        "source_row": 2,
        "from_summary": False,
        "date_corrected": False,
        "date_approx": False,
    }
    row.update(overrides)
    df = pd.DataFrame([row])
    return rows(df)


def rows(df: pd.DataFrame) -> pd.DataFrame:
    """Apply the canonical dtypes and column order to a synthetic frame."""
    df = df[list(schema.COLUMNS)].copy()
    df["feedback_date"] = pd.to_datetime(df["feedback_date"])
    for col, dtype in schema.DTYPES.items():
        if dtype != "datetime64[ns]":
            df[col] = df[col].astype(dtype)
    return df.reset_index(drop=True)


def many(records: list[dict]) -> pd.DataFrame:
    base = frame().iloc[0].to_dict()
    return rows(pd.DataFrame([{**base, **r} for r in records]))


def check(df: pd.DataFrame) -> dict[str, list[int]]:
    """Structural failures only: dtypes, column allowlist and order."""
    return failures_by_check(df, build_schema(CODES))


def caught(key: str, df: pd.DataFrame) -> list[int]:
    """Indices the named rule catches. This, not pandera, is what the waterfall counts:
    pandera reports the kind of check that failed ("isin"), not the name given to it."""
    return declare_rules(CODES)[key].apply(df)


# ------------------------------------------------------------------ the declarations


def test_every_rule_has_a_class_and_a_decision():
    rules = declare_rules()
    assert rules, "no rules declared"
    for rule in rules.values():
        assert rule.kind in {REJECT, FIX, KEEP}, rule.key
        assert rule.decisions.strip(), f"{rule.key} cites no decision"
        assert rule.what.strip()


def test_a_fresh_rule_has_not_fired():
    assert Rule("x", REJECT, "w", "D-000").fired is False


# ------------------------------------------------------------------------ the rules


def test_valid_row_passes_every_rule():
    df = fill_department(frame(), DEPTS, declare_rules()["department_filled"])
    assert check(df) == {}


def test_unknown_dealer_code_rejected():
    df = fill_department(frame(dealer_code="NSW99"), DEPTS, Rule("d", FIX, "w", "D-050"))
    assert caught("dealer_code_known", df) == [0]


@pytest.mark.parametrize("bad", [dt.date(2025, 9, 30), dt.date(2026, 10, 1)])
def test_date_outside_the_window_rejected(bad):
    df = fill_department(frame(feedback_date=bad), DEPTS, Rule("d", FIX, "w", "D-050"))
    assert caught("date_in_window", df) == [0]


def test_dates_on_the_window_edges_are_kept():
    """Oct 1 2025 and Sep 30 2026 are inside the study window, not outside it."""
    for edge in (dt.date(2025, 10, 1), dt.date(2026, 9, 30)):
        df = fill_department(frame(feedback_date=edge), DEPTS, Rule("d", FIX, "w", "D-050"))
        assert caught("date_in_window", df) == []


@pytest.mark.parametrize("bad", [0, 6, -1])
def test_rating_outside_1_to_5_rejected(bad):
    df = fill_department(frame(rating_1to5=bad), DEPTS, Rule("d", FIX, "w", "D-050"))
    assert caught("rating_in_1_to_5", df) == [0]


@pytest.mark.parametrize("bad", ["F1", "f000001", "F0000001", "", "X000001"])
def test_malformed_feedback_id_rejected(bad):
    df = fill_department(frame(feedback_id=bad), DEPTS, Rule("d", FIX, "w", "D-050"))
    assert caught("feedback_id_well_formed", df) == [0]


def test_duplicate_feedback_id_rejected():
    """The second occurrence is rejected; the first is kept, so the id survives once."""
    df = many([{"feedback_id": "F000001"}, {"feedback_id": "F000001", "source_row": 3}])
    df = fill_department(df, DEPTS, Rule("d", FIX, "w", "D-050"))
    assert caught("feedback_id_unique", df) == [1]


def test_summary_row_with_a_comment_rejected():
    df = fill_department(
        frame(from_summary=True, comment="should not be here"), DEPTS,
        Rule("d", FIX, "w", "D-050"),
    )
    assert caught("summary_rows_have_no_comment", df) == [0]


def test_summary_row_without_a_comment_is_fine():
    df = fill_department(
        frame(from_summary=True, comment=None), DEPTS, Rule("d", FIX, "w", "D-050")
    )
    assert caught("summary_rows_have_no_comment", df) == []
    assert check(df) == {}


def test_reject_rule_rejects_rather_than_fixing():
    """The brief asks for this by name: a reject rule must not silently repair the row."""
    bad = fill_department(frame(rating_1to5=9), DEPTS, Rule("d", FIX, "w", "D-050"))
    assert caught("rating_in_1_to_5", bad) == [0]
    # the value is still 9: nothing clamped it into range behind the report's back
    assert int(bad.at[0, "rating_1to5"]) == 9


def test_every_row_level_rule_reports_zero_on_clean_data():
    """A rule that fires zero times has to be a measured zero, not an unmapped one: this
    is the bug the first version of this module had, where pandera's failure names never
    matched the rule keys and every reject rule reported 0 by accident."""
    df = fill_department(frame(), DEPTS, Rule("d", FIX, "w", "D-050"))
    rules = declare_rules(CODES)
    for key, rule in rules.items():
        if rule.test is None or rule.kind == KEEP:
            continue
        assert rule.apply(df) == [], key
        assert rule.count == 0 and rule.fired is False


def test_each_declared_reject_rule_can_actually_fire():
    """Every reject rule with a mask is shown catching at least one row, so none of them
    is a rule that could never fire whatever the data said."""
    cases = {
        "dealer_code_known": frame(dealer_code="NSW99"),
        "date_in_window": frame(feedback_date=dt.date(2024, 1, 1)),
        "rating_in_1_to_5": frame(rating_1to5=9),
        "department_raw_present": frame(department_raw=""),
        "feedback_id_well_formed": frame(feedback_id="nope"),
        "feedback_id_unique": many(
            [{"feedback_id": "F000001"}, {"feedback_id": "F000001", "source_row": 3}]
        ),
        "summary_rows_have_no_comment": frame(from_summary=True, comment="x"),
    }
    declared = {k for k, r in declare_rules(CODES).items()
                if r.kind == REJECT and r.test is not None}
    assert declared == set(cases), declared.symmetric_difference(set(cases))
    for key, df in cases.items():
        assert caught(key, df), key


# ------------------------------------------------------------------- fix-and-flag


def test_empty_comment_becomes_null_and_is_counted():
    rule = declare_rules()["empty_comment_to_null"]
    out = fix_empty_comments(many([{"comment": ""}, {"comment": "real", "source_row": 3}]), rule)
    assert rule.count == 1
    assert rule.examples == [0]
    assert pd.isna(out.at[0, "comment"])
    assert out.at[1, "comment"] == "real"


def test_empty_comment_rule_can_fire_zero_times():
    rule = declare_rules()["empty_comment_to_null"]
    fix_empty_comments(frame(comment="fine"), rule)
    assert rule.count == 0 and rule.fired is False


def test_department_fill_is_total():
    """The brief asks for this by name: no null department may survive the fill."""
    rule = declare_rules()["department_filled"]
    out = fill_department(
        many([{"department_raw": "Workshop"}, {"department_raw": "Parts", "source_row": 3}]),
        DEPTS, rule,
    )
    assert out["department"].isna().sum() == 0
    assert list(out["department"]) == ["Service", "Parts"]
    assert rule.count == 2


def test_department_fill_raises_on_an_unmapped_value():
    with pytest.raises(ValueError, match="no department after the fill"):
        fill_department(
            frame(department_raw="Detailing"), DEPTS, declare_rules()["department_filled"]
        )


def test_workshop_folds_into_service(tmp_path):
    """D-048, the mapping's substantive call, asserted rather than assumed."""
    rule = declare_rules()["department_filled"]
    out = fill_department(frame(department_raw="Workshop"), DEPTS, rule)
    assert out.at[0, "department"] == "Service"


# --------------------------------------------------------------- double entry (D-047)


def _pair(comment: str, rows_: tuple[int, int], **over) -> pd.DataFrame:
    return many([
        {"feedback_id": "F000001", "source_row": rows_[0], "comment": comment, **over},
        {"feedback_id": "F000002", "source_row": rows_[1], "comment": comment, **over},
    ])


def test_adjacent_identical_commented_rows_are_double_entry():
    assert double_entry_duplicates(_pair("Same words.", (18, 19))) == [1]


def test_non_adjacent_identical_rows_are_kept():
    """Two customers can honestly say the same short thing on the same day."""
    assert double_entry_duplicates(_pair("Great service.", (18, 140))) == []


def test_identical_rows_without_a_comment_are_kept():
    df = many([
        {"feedback_id": "F000001", "source_row": 18, "comment": None},
        {"feedback_id": "F000002", "source_row": 19, "comment": None},
    ])
    assert double_entry_duplicates(df) == []


def test_a_different_rating_is_not_double_entry():
    df = many([
        {"feedback_id": "F000001", "source_row": 18, "comment": "Same words.", "rating_1to5": 4},
        {"feedback_id": "F000002", "source_row": 19, "comment": "Same words.", "rating_1to5": 2},
    ])
    assert double_entry_duplicates(df) == []


def test_a_different_dealer_is_not_double_entry():
    df = many([
        {"feedback_id": "F000001", "source_row": 18, "comment": "Same.", "dealer_code": "VIC01"},
        {"feedback_id": "F000002", "source_row": 19, "comment": "Same.", "dealer_code": "QLD02"},
    ])
    assert double_entry_duplicates(df) == []


def test_a_run_of_three_keeps_only_the_first():
    df = many([
        {"feedback_id": "F000001", "source_row": 18, "comment": "Same."},
        {"feedback_id": "F000002", "source_row": 19, "comment": "Same."},
        {"feedback_id": "F000003", "source_row": 20, "comment": "Same."},
    ])
    assert double_entry_duplicates(df) == [1, 2]


# ------------------------------------------------------------------- flag-and-keep


def test_date_edge_cases_lists_only_flagged_rows_with_a_reason():
    df = many([
        {"feedback_id": "F000001", "source_row": 2, "date_corrected": True},
        {"feedback_id": "F000002", "source_row": 3, "date_approx": True},
        {"feedback_id": "F000003", "source_row": 4},
    ])
    edges = date_edge_cases(df)
    assert len(edges) == 2
    assert set(edges["feedback_id"]) == {"F000001", "F000002"}
    assert edges["why"].str.contains("D-032 #3").any()
    assert edges["why"].str.contains("D-040").any()
    # no comment text reaches the edge-case table
    assert "comment" not in edges.columns


def test_flagged_rows_are_not_rejected():
    df = fill_department(
        frame(date_corrected=True, date_approx=True), DEPTS, Rule("d", FIX, "w", "D-050")
    )
    assert check(df) == {}


# ----------------------------------------------------------------------- structure


def test_a_column_outside_the_allowlist_is_a_failure():
    df = fill_department(frame(), DEPTS, Rule("d", FIX, "w", "D-050"))
    df["staff_name"] = "Aroha"
    with pytest.raises(pa.errors.SchemaErrors):
        build_schema(CODES).validate(df, lazy=True)


def test_a_missing_column_is_a_failure():
    df = fill_department(frame(), DEPTS, Rule("d", FIX, "w", "D-050")).drop(columns=["comment"])
    with pytest.raises(pa.errors.SchemaErrors):
        build_schema(CODES).validate(df, lazy=True)

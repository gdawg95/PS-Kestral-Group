"""Tests for Wave 5's analysis module.

These are guard tests, not coverage tests. Each one pins a rule that a Wave 4 decision made
binding on this analysis, because every one of them is the kind of rule that is easy to
restate in prose and easy to break in code:

  * the committed trend threshold is applied to the unrounded change (the bug this file
    exists for);
  * denominators are not silently swapped (D-058);
  * theme tables come out alphabetical, never ordered by rate (D-065, D-066);
  * the rating, not sentiment, is what `negative_by_rating` means (D-065);
  * the three-way drivers cut stays uncomputed, and the site split uses the project's own
    floor rather than a new one (D-059, D-060).
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src import analyse

# --------------------------------------------------------------- the rounding guard


def _two_months(mean_a: float, mean_b: float, n: int = 20) -> pd.DataFrame:
    """A single dealership with two adjacent months of n responses at the given means.

    Ratings are built as floats so a mean can be placed exactly; `month_pairs` only ever
    averages the column, so the integer scale is not what is under test here.
    """
    rows = []
    for month, mean in (("2026-01", mean_a), ("2026-02", mean_b)):
        for i in range(n):
            rows.append(
                {
                    "dealer_code": "TEST1",
                    "month": pd.Period(month),
                    "rating_1to5": mean,
                    "feedback_date": pd.Timestamp(f"{month}-05"),
                    "_i": i,
                }
            )
    return pd.DataFrame(rows)


def test_threshold_is_applied_to_the_unrounded_change():
    """A 0.496-star move must NOT clear a 0.5-star rule.

    It did, for one run: the change was rounded to two decimals for display and the
    threshold was then tested against the rounded value, which turned 0.496 into 0.50. That
    put the flag count at 34 of 256 against the 33 the committed evidence file predicted - a
    threshold committed in advance, loosened by a formatting decision.
    """
    df = _two_months(4.000, 4.000 - 0.496)
    pairs = analyse.month_pairs(df)
    assert len(pairs) == 1
    assert pairs["change"].iloc[0] == -0.5, "still rounded to -0.50 for display"
    assert not pairs["clears D-052"].iloc[0], "0.496 < 0.5 and must not be flagged"


def test_threshold_still_flags_a_real_move():
    df = _two_months(4.000, 4.000 - 0.500)
    assert analyse.month_pairs(df)["clears D-052"].iloc[0]


def test_thin_months_are_never_called_a_movement():
    """D-052: below `min_month_responses` a month is a count, never a move - however large
    the change. VIC09's +1.40 on 5 -> 10 responses is the case this protects."""
    df = _two_months(3.20, 4.60, n=analyse.MIN_MONTH_N - 1)
    pairs = analyse.month_pairs(df)
    assert abs(pairs["change"].iloc[0]) > analyse.MIN_CHANGE
    assert not pairs["both months >= floor"].iloc[0]
    assert not pairs["clears D-052"].iloc[0]


def test_non_adjacent_months_are_not_a_pair():
    """Penrith has no June 2026 sheet (D-029). May and July are not a month-on-month pair,
    and treating them as one is the single difference from `scripts/trend_evidence.py`."""
    df = pd.concat([_two_months(4.0, 4.0)])
    df.loc[df["month"] == pd.Period("2026-02"), "month"] = pd.Period("2026-04")
    assert len(analyse.month_pairs(df)) == 0


# ------------------------------------------------------------------- D-058 denominators


@pytest.fixture(scope="module")
def real() -> pd.DataFrame:
    df, _, _ = analyse.load()
    return df


def test_rating_denominators_differ_and_both_are_reported(real):
    """The two rates D-058 exists for. If these ever coincide, the fixture has changed and
    the 5.6-point warning in both reports needs rewriting, not deleting."""
    all_rows = 100 * real["negative_by_rating"].mean()
    commented = 100 * real.loc[real["has_comment"], "negative_by_rating"].mean()
    assert commented > all_rows
    assert round(all_rows, 1) == 22.5
    assert round(commented, 1) == 28.1


def test_commentless_rows_carry_no_sentiment_and_no_theme(real):
    """D-057: null, never 'neutral'. A guessed label here would inject 1,589 invented
    positives into every sentiment total and every theme denominator."""
    blank = real[~real["has_comment"]]
    assert len(blank) == 1797
    assert blank["sentiment_label"].isna().all()
    assert blank["theme"].isna().all()


def test_rate_block_denominator_columns_are_consistent(real):
    t = analyse.rate_block(real, "department", "Department")
    assert t["rows (all)"].sum() == len(real)
    assert t["commented rows"].sum() == int(real["has_comment"].sum())
    for _, row in t.iterrows():
        assert row["commented rows"] <= row["rows (all)"]


# ------------------------------------------------------- D-065 / D-066 theme handling


def test_theme_table_is_alphabetical_not_ranked(real):
    """A sorted bar chart is a ranking whatever the caption says, and so is a sorted table.
    At 44.1% model-owner agreement a theme rate is reportable and an ordering is not."""
    section = analyse.section_theme(real)
    themes = sorted(real.loc[real["has_comment"], "theme"].dropna().unique())
    positions = [section.index(f"| {t} |") for t in themes]
    assert positions == sorted(positions)
    assert str(analyse.THEME_AGREEMENT) in section


def test_every_theme_section_states_the_agreement_figure(real):
    for section in (
        analyse.section_theme(real),
        analyse.section_theme_department(real),
        analyse.section_theme_dealership(real),
    ):
        assert f"{analyse.THEME_AGREEMENT}%" in section


def test_negative_by_rating_ignores_sentiment(real):
    """D-065's fallback in one line: the primary signal is the customer's star rating, and
    nothing about the model's label may leak into it."""
    assert (real["negative_by_rating"] == (real["rating_1to5"] <= analyse.NEG_MAX)).all()
    sentiment_negative_but_rated_well = real[
        (real["sentiment_label"] == "negative") & (real["rating_1to5"] > analyse.NEG_MAX)
    ]
    assert len(sentiment_negative_but_rated_well) > 0, "fixture no longer exercises this"
    assert not sentiment_negative_but_rated_well["negative_by_rating"].any()


# ------------------------------------------------------------- D-059 / D-060 the cuts


def test_site_split_uses_the_projects_own_floor(real):
    """D-059 measured theme capacity against `trend_evidence.min_month_responses`, so two
    parts of the project do not run on different ideas of 'enough'. The five that fail are
    the same five D-052 names for quarterly trends."""
    capable, thin = analyse.theme_capable_sites(real)
    assert len(capable) == 19
    assert thin == ["NSW07", "QLD05", "QLD07", "VIC08", "VIC09"]


def test_theme_by_dealership_covers_only_capable_sites(real):
    section = analyse.section_theme_dealership(real)
    capable, thin = analyse.theme_capable_sites(real)
    table = section.split("### The five thin sites")[0]
    for site in capable:
        assert f"| {site} |" in table
    for site in thin:
        assert f"| {site} |" not in table


# ------------------------------------------------------------------- small statistics


def test_wilson_interval_brackets_the_point_estimate():
    lo, hi = analyse.wilson_ci(1, 49)  # QLD05: one negative row in 49
    assert lo < 100 / 49 < hi
    assert lo >= 0 and hi <= 100
    narrow = analyse.wilson_ci(100, 1000)
    assert (narrow[1] - narrow[0]) < (hi - lo), "more data must give a tighter interval"


def test_wilson_handles_an_empty_group():
    assert all(np.isnan(v) for v in analyse.wilson_ci(0, 0))


def test_noise_band_matches_the_committed_calibration():
    """D-052 chose 0.5 stars because the noise on a change between two 20-response months
    is +/-0.46. If this formula drifts, the justification for the threshold drifts with it."""
    assert round(analyse.noise_band(1.44, 20, 20), 2) == 0.46


def test_markdown_table_prints_a_rate_at_its_own_precision():
    """A rate rounded to 23.1 must not reappear as 23.10, and a boolean must not print as 1."""
    df = pd.DataFrame([{"rate": 23.1, "mean": 4.0, "n": 1234, "flag": True, "miss": None}])
    rendered = analyse.table(df)
    assert "| 23.1 |" in rendered
    assert "| 4.0 |" in rendered
    assert "| 1,234 |" in rendered
    assert "| yes |" in rendered
    assert "| — |" in rendered

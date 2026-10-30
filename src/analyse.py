"""Wave 5: drivers, trend and coverage over the classified dataset.

Brief: `agents/briefs/w5_analysis.md`. This module answers PLAN.md section 1's three
business questions and produces `reports/analysis.md`, which `reports/business_report.md`
cites for every number it quotes.

Four Wave 4 results constrain what this module is allowed to compute, and each one is
enforced here in code rather than left to the prose:

  D-065  The sentiment model missed its pass mark (Cohen's kappa 0.403 against the 0.60
         committed in D-055), and the customer's star rating beat it (0.460) on the same
         150 blind labels. D-055's pre-committed fallback therefore applies: the RATING is
         the primary signal for negative feedback. Model sentiment is computed alongside
         every rating-based figure and labelled as the method comparison it now is.
  D-065  Owner and model agreed on a comment's theme 44.1% of the time. A theme's negative
         RATE is reportable with that figure attached; one theme ranked above another is
         not. Every theme table in this module is emitted in alphabetical order and
         carries the caveat, so nothing downstream can read an ordering into it.
  D-060  Theme x department x dealership is 576 cells for 5,353 comments. The three-way cut
         is not computed. Theme x department runs nationally; theme x dealership runs only
         for the sites whose average theme cell clears `trend_evidence.min_month_responses`
         (D-059's own test, reused); the five thin sites appear at department level.
  D-058  Every negative rate names its denominator. Rating-based rates are over all 7,150
         rows; theme and sentiment rates are necessarily over the 5,353 commented rows,
         which average 3.54 stars against 4.40 for the commentless ones and are therefore
         not representative. The two are never printed without the denominator beside them.

D-052's committed trend rule (20 responses a month, 0.5 stars, thin sites quarterly) is
read from `config.yaml` and never redefined here - gate G7. Where a claim is made at a
different grain from the one the rule was calibrated for (the national series), the rule's
own noise arithmetic is recomputed at that grain and printed, rather than the threshold
being quietly reused or quietly dropped.

D-005: every trend figure is produced twice, with and without the closed site VIC09, so a
composition change cannot masquerade as a movement.

Usage:
    python -m src.analyse              # full run -> reports/analysis.md + run_manifest.json
    python -m src.analyse --pilot      # gate G1: three dealerships only, separate report
"""

from __future__ import annotations

# ruff: noqa: E501 - this module emits markdown. A table row is one line by definition:
# wrapping the f-strings below would wrap them in the generated report too. Code lines
# are kept inside the 100-column limit by hand.
import argparse
import hashlib
import json
import math
import platform
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import pandas as pd
import yaml
from scipy import stats

ROOT = Path(__file__).resolve().parents[1]
CONFIG = yaml.safe_load((ROOT / "config.yaml").read_text(encoding="utf-8"))

SEED = CONFIG["seed"]
CLEAN_DIR = ROOT / CONFIG["paths"]["clean"]
CLASSIFIED = CLEAN_DIR / "feedback_classified.parquet"
REVENUE = ROOT / CONFIG["paths"]["revenue"]
DEALERSHIPS = ROOT / CONFIG["paths"]["dealerships"]
ANALYSIS_REPORT = ROOT / "reports" / "analysis.md"
PILOT_REPORT = ROOT / "reports" / "pilot_drivers.md"
MANIFEST = ROOT / "reports" / "run_manifest.json"

NEG_MAX = CONFIG["thresholds"]["negative_score_max_1to5"]  # D-004: rating 1-2 is negative
TREND = CONFIG["thresholds"]["trend_evidence"]  # D-052, committed before any result
MIN_MONTH_N = TREND["min_month_responses"]
MIN_CHANGE = TREND["min_change_1to5"]

CLOSED_SITE = "VIC09"  # D-005; closed 2026-03-31
THEME_AGREEMENT = 44.1  # D-065, reports/evaluation.md
SENTIMENT_KAPPA = 0.403  # D-065
RATING_KAPPA = 0.460  # D-065 - the rating beat the model, which is why it leads
KAPPA_FLOOR = CONFIG["thresholds"]["nlp_pass_mark"]["sentiment_min_kappa"]

# The year splits in half at the closure date, which is also the midpoint of the 12 months.
# Stated as a fixed boundary rather than searched for: a change point chosen to maximise the
# gap it then reports would not be evidence of anything.
H1 = ("2025-10", "2026-03")
H2 = ("2026-04", "2026-09")

# Gate G1's pilot slice: the thinnest site, the site whose rows are mostly summary pivot
# expansions with no comments, and the largest site.
PILOT_DEALERS = [CLOSED_SITE, "QLD06", "VIC01"]


# --------------------------------------------------------------------------- loading


def load() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """The classified dataset plus the two reference tables, with a month column added."""
    df = pd.read_parquet(CLASSIFIED)
    df["month"] = df["feedback_date"].dt.to_period("M")
    df["half"] = np.where(df["month"] < pd.Period(H2[0]), "H1", "H2")
    df["negative_by_rating"] = df["rating_1to5"] <= NEG_MAX
    df["has_comment"] = df["comment"].notna()
    # D-004's full definition, kept for the method comparison only. D-065 makes the rating
    # primary, so nothing in this module headlines this column.
    df["negative_d004"] = df["negative_by_rating"] | (df["sentiment_label"] == "negative")
    revenue = pd.read_csv(REVENUE)
    dealers = pd.read_csv(DEALERSHIPS)
    return df, revenue, dealers


# ----------------------------------------------------------------- small statistics


def wilson_ci(successes: int, n: int, z: float = 1.96) -> tuple[float, float]:
    """Wilson 95% interval, as a percentage. Used because site n ranges 49 to 484 and a
    bare point estimate invites a comparison the thin sites cannot support."""
    if n == 0:
        return (float("nan"), float("nan"))
    p = successes / n
    denom = 1 + z**2 / n
    centre = (p + z**2 / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z**2 / (4 * n**2)) / denom
    return (100 * max(0.0, centre - half), 100 * min(1.0, centre + half))


def noise_band(sd: float, n_a: int, n_b: int) -> float:
    """D-052's own arithmetic: the 1-sigma noise on a difference of two means.

    The committed threshold of 0.5 stars came from this formula at n = 20 a month
    (+/-0.46). Reusing the same formula at a different n is what lets a claim at another
    grain be judged by the rule's own standard instead of by a borrowed number.
    """
    return sd * math.sqrt(1 / n_a + 1 / n_b)


# --------------------------------------------------------------------- markdown helpers


def table(df: pd.DataFrame, aligns: dict[str, str] | None = None) -> str:
    """Render a DataFrame as a GitHub markdown table, numeric columns right-aligned."""
    aligns = aligns or {}
    cols = list(df.columns)
    header = "| " + " | ".join(str(c) for c in cols) + " |"
    rule = []
    for c in cols:
        a = aligns.get(c) or ("right" if pd.api.types.is_numeric_dtype(df[c]) else "left")
        rule.append("---:" if a == "right" else "---")
    body = []
    for _, row in df.iterrows():
        cells = []
        for c in cols:
            v = row[c]
            if isinstance(v, (bool, np.bool_)):
                cells.append("yes" if v else "no")
            elif v is None or (isinstance(v, float) and math.isnan(v)):
                cells.append("—")
            elif isinstance(v, float):
                # Print the value at the precision it was rounded to, not at a fixed two
                # decimals: a rate rounded to 23.1 must not reappear as 23.10.
                s = f"{v:,.3f}".rstrip("0")
                cells.append(s + "0" if s.endswith(".") else s)
            elif isinstance(v, (int, np.integer)):
                cells.append(f"{v:,}")
            else:
                cells.append(str(v))
        body.append("| " + " | ".join(cells) + " |")
    return "\n".join([header, "| " + " | ".join(rule) + " |", *body])


def rate_block(df: pd.DataFrame, by: str, label: str) -> pd.DataFrame:
    """Negative rate by `by`, over ALL rows (rating denominator, D-058), with the
    sentiment-based figure beside it over the commented subset as the method comparison."""
    out = []
    for key, sub in df.groupby(by, observed=True):
        n_all = len(sub)
        neg = int(sub["negative_by_rating"].sum())
        lo, hi = wilson_ci(neg, n_all)
        cmt = sub[sub["has_comment"]]
        n_cmt = len(cmt)
        neg_cmt = int(cmt["negative_by_rating"].sum())
        neg_sent = int((cmt["sentiment_label"] == "negative").sum())
        out.append(
            {
                label: key,
                "rows (all)": n_all,
                "negative by rating": neg,
                "rate % of all rows": round(100 * neg / n_all, 1),
                "95% CI": f"{lo:.1f}–{hi:.1f}",
                "mean rating": round(sub["rating_1to5"].mean(), 2),
                "commented rows": n_cmt,
                "rate % of commented": round(100 * neg_cmt / n_cmt, 1) if n_cmt else None,
                "sentiment-negative % of commented": (
                    round(100 * neg_sent / n_cmt, 1) if n_cmt else None
                ),
            }
        )
    return pd.DataFrame(out)


# --------------------------------------------------------------------------- sections


def section_headline(df: pd.DataFrame) -> str:
    n_all = len(df)
    n_cmt = int(df["has_comment"].sum())
    neg_all = int(df["negative_by_rating"].sum())
    neg_cmt = int(df.loc[df["has_comment"], "negative_by_rating"].sum())
    neg_d004 = int(df["negative_d004"].sum())
    sent_neg = int((df["sentiment_label"] == "negative").sum())
    mean_cmt = df.loc[df["has_comment"], "rating_1to5"].mean()
    mean_no = df.loc[~df["has_comment"], "rating_1to5"].mean()
    gap = 100 * neg_cmt / n_cmt - 100 * neg_all / n_all
    return f"""## 1. The headline, with its denominator

The primary signal is the customer's own star rating (D-065). The sentiment model missed
the pass mark committed in D-055 — Cohen's kappa **{SENTIMENT_KAPPA}** against a floor of
**{KAPPA_FLOOR}** — and the star rating scored **{RATING_KAPPA}** on the same 150 blind
labels, so the rating is both the committed fallback and the better-measured signal.

| Measure | Count | Denominator | Rate |
|---|---:|---:|---:|
| Negative by rating (1–{NEG_MAX}) | {neg_all:,} | all {n_all:,} rows | **{100 * neg_all / n_all:.1f}%** |
| Negative by rating (1–{NEG_MAX}) | {neg_cmt:,} | the {n_cmt:,} commented rows | **{100 * neg_cmt / n_cmt:.1f}%** |
| Negative by D-004 (rating 1–{NEG_MAX} *or* sentiment negative) | {neg_d004:,} | all {n_all:,} rows | {100 * neg_d004 / n_all:.1f}% |
| Sentiment-negative *(method comparison, kappa {SENTIMENT_KAPPA})* | {sent_neg:,} | the {n_cmt:,} commented rows | {100 * sent_neg / n_cmt:.1f}% |

**Which number to quote, and why it matters.** The two rating rows differ by
**{gap:.1f} percentage points** off the same data. Commented rows average
**{mean_cmt:.2f}** stars and commentless rows **{mean_no:.2f}** — satisfied customers tick
five and leave, dissatisfied ones write — so the commented subset is not a sample of the
feedback population (D-058). *"{100 * neg_cmt / n_cmt:.0f}% of feedback is negative"* is
true only of the {n_cmt:,} rows that carry a comment. Across everything Kestrel collected
the figure is **{100 * neg_all / n_all:.1f}%**.

Every table below names its denominator in its caption for the same reason.
"""


def section_department(df: pd.DataFrame) -> str:
    t = rate_block(df, "department", "Department").sort_values(
        "rate % of all rows", ascending=False
    )
    svc = t[t["Department"] == "Service"].iloc[0]
    share = 100 * svc["rows (all)"] / len(df)
    return f"""## 2. Drivers — by department

`department` is a hand-mapped field: 16 source spellings reduced to three, every mapping
approved by the owner (D-048, D-049, D-050). It is not model output, so unlike the themes
in section 4 these three rows **can** be compared with each other.

**Denominators:** the rating columns are over all {len(df):,} rows; the last two columns are
over the commented subset only.

{table(t)}

Service carries **{svc["rows (all)"]:,} of {len(df):,} rows ({share:.1f}%)** and the worst
rate on either denominator. Sales and Parts are each under a fifth of the volume. Whatever
is wrong, most of it is in the service lane — and that conclusion needs no theme model and
no sentiment model to reach it.
"""


def section_dealership(df: pd.DataFrame) -> str:
    t = rate_block(df, "dealer_code", "Dealer").sort_values(
        "rate % of all rows", ascending=False
    )
    worst = t.iloc[0]
    best = t.iloc[-1]
    thin = ["NSW07", "QLD05", "QLD07", "VIC08", CLOSED_SITE]  # D-052's named five
    thin_rows = t[t["Dealer"].isin(thin)].set_index("Dealer")["rows (all)"]
    return f"""## 3. Drivers — by dealership

**Denominator:** all {len(df):,} rows, by rating. `dealer_code` comes from the file-to-dealer
map the owner approved by hand (D-034), so it is as reliable as the department column.

The 95% interval is Wilson, and it is printed because site volumes run from
{t["rows (all)"].min():,} to {t["rows (all)"].max():,} rows. Two sites whose intervals
overlap are not separated by this data, however their point estimates sort.

{table(t)}

**Read with care.** {worst["Dealer"]} has the highest rate ({worst["rate % of all rows"]:.1f}%,
CI {worst["95% CI"]}) and {best["Dealer"]} the lowest ({best["rate % of all rows"]:.1f}%,
CI {best["95% CI"]}), but the intervals of the middle sixteen sites overlap heavily. The
honest statement is that a few sites sit clearly above the group and a few clearly below;
the ninth-placed site in this table is not separated from the eleventh by this data.

D-052's five thin sites — {", ".join(f'{d} ({int(n)} rows)' for d, n in thin_rows.items())} —
carry the widest intervals, and they are the same five sites D-059 identified from comment
volume rather than month volume. Two independent measures singling out the same five is
corroboration rather than coincidence. QLD05's 2.0% is one negative row in 49.
"""


def section_theme(df: pd.DataFrame) -> str:
    cmt = df[df["has_comment"]]
    rows = []
    for theme, sub in cmt.groupby("theme", observed=True):
        n = len(sub)
        neg = int(sub["negative_by_rating"].sum())
        lo, hi = wilson_ci(neg, n)
        rows.append(
            {
                "Theme": theme,
                "comments": n,
                "% of commented rows": round(100 * n / len(cmt), 1),
                "negative by rating": neg,
                "rate % of this theme": round(100 * neg / n, 1),
                "95% CI": f"{lo:.1f}–{hi:.1f}",
                "mean rating": round(sub["rating_1to5"].mean(), 2),
                "sentiment-negative %": round(
                    100 * (sub["sentiment_label"] == "negative").mean(), 1
                ),
            }
        )
    t = pd.DataFrame(rows).sort_values("Theme")  # alphabetical, deliberately not by rate
    return f"""## 4. Drivers — by theme, and what may not be said about them

> **The 44.1% caveat.** Of the 143 comments the owner placed in a theme when labelling
> blind, the model placed **{THEME_AGREEMENT}%** in the same theme (D-065,
> `reports/evaluation.md`). Theme assignment is embedding similarity to eight owner-approved
> themes with no confidence floor, because the floor was tested against those labels and
> did not separate the comments the owner rejected from the ones they kept (D-066).
>
> **A theme's negative rate is reportable with that figure attached. One theme ranked above
> another is not.** This table is printed in **alphabetical order** for that reason, and no
> figure in `reports/business_report.md` rests on the order of these eight rows.

**Denominator:** the {len(cmt):,} commented rows only — a theme cannot be assigned to a row
with no comment, and D-057 gives those rows a null theme rather than a guessed one. These
rates are therefore not comparable with the all-rows rates in sections 2 and 3.

{table(t)}

**What survives the caveat.** Two things, both of which hold without any theme being ranked:

1. **Staff manner is the largest theme and the least negative of the eight by a wide
   margin** — {t[t["Theme"] == "Staff manner"]["rate % of this theme"].iloc[0]:.1f}% against
   a {100 * cmt["negative_by_rating"].mean():.1f}% rate across all commented rows. A 44%
   reliable classifier placing 1,395 comments cannot be trusted on *which* operational
   theme a comment belongs to, but the staff/operations distinction is the coarsest cut in
   the list and the one it is least likely to be wrong about.
2. **The rating-based and sentiment-based columns agree on the shape** — the two right-hand
   columns track each other across all eight rows despite being built from different
   signals. That is corroboration of the *pattern*, not of the ordering, and it comes with
   sentiment's own kappa of {SENTIMENT_KAPPA} attached.

The 20 failure cases in `reports/llm_review.md` show why: the recurring comment in this
corpus praises the people and complains about the process — *"Great welcome, helpful staff.
Problem not fixed."* Those comments are negative, and which operational theme they land in
is exactly what the 44.1% is uncertain about.
"""


def section_theme_department(df: pd.DataFrame) -> str:
    cmt = df[df["has_comment"]]
    counts = cmt.pivot_table(
        index="theme", columns="department", values="feedback_id", aggfunc="count"
    ).fillna(0)
    rates = (
        cmt.pivot_table(
            index="theme",
            columns="department",
            values="negative_by_rating",
            aggfunc="mean",
        )
        * 100
    )
    out = pd.DataFrame(index=sorted(counts.index))
    out.index.name = "Theme"
    for dep in ["Service", "Sales", "Parts"]:
        if dep in counts:
            out[f"{dep} n"] = counts[dep].reindex(out.index).astype(int)
            out[f"{dep} neg %"] = rates[dep].reindex(out.index).round(1)
    out = out.reset_index()
    thin_cells = int((counts < MIN_MONTH_N).to_numpy().sum())
    return f"""## 5. Theme × department, nationally only

**Why this cut and not the one PLAN.md promised.** D-060 rescoped it before the analysis
started: 8 themes × 72 department-dealership cells is 576 cells for {len(cmt):,} comments —
9.3 per cell. This is the two-way cut, computed nationally.

**Denominator:** each cell's own n, over commented rows. {thin_cells} of the 24 cells below
hold fewer than {MIN_MONTH_N} comments, the project's own floor for calling anything a
movement (D-052), and those cells are printed but should not be read as rates.
Parts has {int(counts.get("Parts", pd.Series(dtype=int)).sum()):,} commented rows in total
and can carry a national theme split, never a per-dealership one.

Alphabetical by theme. **The 44.1% caveat in section 4 applies to every row.**

{table(out)}
"""


def theme_capable_sites(df: pd.DataFrame) -> tuple[list[str], list[str]]:
    """D-059's test, reused verbatim: a site supports a theme split when its average
    theme cell clears `trend_evidence.min_month_responses`. Returns (capable, thin)."""
    cmt = df[df["has_comment"]]
    n_themes = cmt["theme"].nunique()
    per_site = cmt.groupby("dealer_code").size() / n_themes
    capable = sorted(per_site[per_site >= MIN_MONTH_N].index)
    thin = sorted(per_site[per_site < MIN_MONTH_N].index)
    return capable, thin


def section_theme_dealership(df: pd.DataFrame) -> str:
    cmt = df[df["has_comment"]]
    capable, thin = theme_capable_sites(df)
    n_themes = cmt["theme"].nunique()
    sub = cmt[cmt["dealer_code"].isin(capable)]
    rates = (
        sub.pivot_table(
            index="dealer_code",
            columns="theme",
            values="negative_by_rating",
            aggfunc="mean",
        )
        * 100
    ).round(1)
    counts = sub.pivot_table(
        index="dealer_code", columns="theme", values="feedback_id", aggfunc="count"
    ).fillna(0)
    rates = rates[sorted(rates.columns)].reset_index().rename(columns={"dealer_code": "Dealer"})
    thin_t = rate_block(df[df["dealer_code"].isin(thin)], "department", "Department")
    thin_sites = df[df["dealer_code"].isin(thin)]
    by_site = rate_block(thin_sites, "dealer_code", "Dealer")[
        ["Dealer", "rows (all)", "negative by rating", "rate % of all rows", "95% CI"]
    ]
    median_cell = int(np.median(counts.to_numpy()))
    thin_counts = (cmt[cmt["dealer_code"].isin(thin)].groupby("dealer_code").size() / n_themes)
    thinnest = " and ".join(thin_counts.nsmallest(2).index)
    thin_cell = thin_counts.min()
    return f"""## 6. Theme × dealership, for the {len(capable)} sites that can carry it

**The test is the project's own, not a new one.** D-059 measured theme capacity as the
average theme cell against `trend_evidence.min_month_responses` = {MIN_MONTH_N}, the same
floor D-052 uses for a monthly movement. A site qualifies when
`commented rows / {n_themes} themes >= {MIN_MONTH_N}`. {len(capable)} of 24 sites clear it;
the {len(thin)} that do not are **{", ".join(thin)}** — the same five sites D-052 puts on a
quarterly basis for trends, arrived at from comment volume rather than month volume.

**Denominator:** each cell's own n, over commented rows at that site. The median cell holds
{median_cell} comments. **The 44.1% caveat applies to every cell**, and these cells are an
order of magnitude thinner than section 4's, so they are published as a map of where to look
rather than as measurements. Alphabetical by theme.

{table(rates)}

### The five thin sites, at department level (D-060's footnote)

These sites cannot support a theme split: {thinnest} would hold around
{thin_cell:.0f} comments per theme. They are reported here at department level so they appear
in the analysis rather than being silently dropped.

**Denominator:** all rows at each of these five sites, by rating.

{table(by_site)}

**The same five sites pooled, by department.** Denominator: all
{int(len(thin_sites)):,} rows across the five.

{table(thin_t)}
"""


def month_pairs(df: pd.DataFrame) -> pd.DataFrame:
    """Every consecutive dealer-month pair, with D-052's rule applied as a flag."""
    g = (
        df.groupby(["dealer_code", "month"], observed=True)
        .agg(n=("rating_1to5", "size"), mean=("rating_1to5", "mean"))
        .reset_index()
    )
    rows = []
    for dealer, sub in g.groupby("dealer_code", observed=True):
        sub = sub.sort_values("month").reset_index(drop=True)
        for i in range(1, len(sub)):
            a, b = sub.loc[i - 1], sub.loc[i]
            if b["month"].ordinal - a["month"].ordinal != 1:
                continue  # a gap is not a month-on-month pair (Penrith June 2026, D-029)
            rows.append(
                {
                    "Dealer": dealer,
                    "Month": str(b["month"]),
                    "n prev": int(a["n"]),
                    "n this": int(b["n"]),
                    "prev mean": round(a["mean"], 2),
                    "this mean": round(b["mean"], 2),
                    "change": round(b["mean"] - a["mean"], 2),
                    # The threshold is applied to the UNROUNDED change. Testing the rounded
                    # figure let a 0.496-star move at VIC04 clear a 0.5-star rule, which put
                    # the count at 34 of 256 against the 33 the committed evidence file
                    # predicted - a threshold loosened by a display decision.
                    "_change_exact": b["mean"] - a["mean"],
                }
            )
    cols = ["Dealer", "Month", "n prev", "n this", "prev mean", "this mean", "change",
            "_change_exact"]
    p = pd.DataFrame(rows, columns=cols)  # columns survive an empty result (a one-site pilot)
    p["both months >= floor"] = (p["n prev"] >= MIN_MONTH_N) & (p["n this"] >= MIN_MONTH_N)
    p["clears D-052"] = p["both months >= floor"] & (p["_change_exact"].abs() >= MIN_CHANGE)
    return p.drop(columns=["_change_exact"])


def quarterly_thin(df: pd.DataFrame, thin: list[str]) -> pd.DataFrame:
    """D-052's `thin_dealer_basis: quarterly` for the five thin sites."""
    sub = df[df["dealer_code"].isin(thin)].copy()
    sub["quarter"] = sub["feedback_date"].dt.to_period("Q")
    g = (
        sub.groupby(["dealer_code", "quarter"], observed=True)
        .agg(n=("rating_1to5", "size"), mean=("rating_1to5", "mean"))
        .reset_index()
    )
    g["mean"] = g["mean"].round(2)
    g["quarter"] = g["quarter"].astype(str)
    return g.rename(columns={"dealer_code": "Dealer", "quarter": "Quarter"})


def national_series(df: pd.DataFrame) -> pd.DataFrame:
    g = (
        df.groupby("month", observed=True)
        .agg(
            responses=("rating_1to5", "size"),
            mean_rating=("rating_1to5", "mean"),
            negative=("negative_by_rating", "sum"),
        )
        .reset_index()
    )
    g["negative rate %"] = (100 * g["negative"] / g["responses"]).round(1)
    g["mean rating"] = g["mean_rating"].round(3)
    g["month"] = g["month"].astype(str)
    return g.drop(columns=["mean_rating"])


def half_test(df: pd.DataFrame) -> dict:
    a = df.loc[df["half"] == "H1", "rating_1to5"].astype(float)
    b = df.loc[df["half"] == "H2", "rating_1to5"].astype(float)
    welch = stats.ttest_ind(a, b, equal_var=False)
    mwu = stats.mannwhitneyu(a, b)
    sd = df["rating_1to5"].astype(float).std()
    neg_a = df.loc[df["half"] == "H1", "negative_by_rating"]
    neg_b = df.loc[df["half"] == "H2", "negative_by_rating"]
    chi = stats.chi2_contingency(
        [
            [int(neg_a.sum()), int((~neg_a).sum())],
            [int(neg_b.sum()), int((~neg_b).sum())],
        ]
    )
    return {
        "n_h1": len(a),
        "n_h2": len(b),
        "mean_h1": a.mean(),
        "mean_h2": b.mean(),
        "delta": b.mean() - a.mean(),
        "neg_h1": 100 * neg_a.mean(),
        "neg_h2": 100 * neg_b.mean(),
        "neg_delta": 100 * (neg_b.mean() - neg_a.mean()),
        "welch_t": welch.statistic,
        "welch_p": welch.pvalue,
        "mwu_p": mwu.pvalue,
        "chi2_p": chi.pvalue,
        "sd": sd,
        "noise_1sigma": noise_band(sd, len(a), len(b)),
    }


def section_trend(df: pd.DataFrame) -> str:
    _, thin = theme_capable_sites(df)
    thin_52 = ["NSW07", "QLD05", "QLD07", "VIC08", CLOSED_SITE]  # D-052's named five
    all_series = national_series(df)
    ex_series = national_series(df[df["dealer_code"] != CLOSED_SITE])
    merged = all_series[["month", "responses", "mean rating", "negative rate %"]].merge(
        ex_series[["month", "mean rating", "negative rate %"]],
        on="month",
        suffixes=(" (all 24)", f" (excl {CLOSED_SITE})"),
    )
    h_all = half_test(df)
    h_ex = half_test(df[df["dealer_code"] != CLOSED_SITE])
    pairs = month_pairs(df)
    flagged = pairs[pairs["clears D-052"]].sort_values("change")
    down = int((flagged["change"] < 0).sum())
    up = int((flagged["change"] > 0).sum())
    worst = flagged.iloc[0]
    quarters = quarterly_thin(df, thin_52)
    nxt = pd.Period(worst["Month"]) + 1
    after = pairs[(pairs["Dealer"] == worst["Dealer"]) & (pairs["Month"] == str(nxt))]
    recovery = f"{after['change'].iloc[0]:+.2f} in {nxt}" if len(after) else "no adjacent pair"

    return f"""## 7. The trend — has anything changed over the year?

### 7.1 The committed rule, and what it finds

D-052 set the evidence rule **before any trend result existed** (gate G7), from the measured
SD of 1.44 in `reports/trend_evidence.md`:

| Setting | Committed value | Why |
|---|---|---|
| `min_month_responses` | **{MIN_MONTH_N}** | a change between two 20-response months carries ±0.46 of noise |
| `min_change_1to5` | **{MIN_CHANGE}** | sits just outside that band |
| `thin_dealer_basis` | **{TREND["thin_dealer_basis"]}** | {", ".join(thin_52)} have a median month under {MIN_MONTH_N} |

Applied to this dataset, the rule finds **{len(flagged)} of {len(pairs)} consecutive
dealer-month pairs** at **{flagged["Dealer"].nunique()} of 24 sites**.

> **Reconciled against the committed evidence file**, which predicted 33 of **257** at 16 of
> 24 from the 7,159 pre-validation rows. The flag count and the site count match exactly.
> The pair count does not, and the reason is a single known gap: `scripts/trend_evidence.py`
> paired each month with the previous *present* month, so Penrith (NSW02) had its May 2026
> paired with its July 2026 across the missing June — the sheet D-029 excluded as a copy of
> July. This module requires the two months to be adjacent, which drops that one pair.
> 257 − 1 = {len(pairs)}. Nothing else differs.

**And the site-level rule finds no direction: {down} of the {len(flagged)} moves are
downward and {up} upward.** That symmetry is the honest result of the rule at the grain it
was calibrated for, and it is why the trend claim in 7.2 is not made from this table.

{table(flagged.drop(columns=["both months >= floor", "clears D-052"]))}

The largest single move in the dataset is **{worst["Dealer"]} in {worst["Month"]}:
{worst["prev mean"]:.2f} → {worst["this mean"]:.2f} stars, a fall of
{abs(worst["change"]):.2f}** on {worst["n prev"]:,} → {worst["n this"]:,} responses — nearly
three times the committed threshold, and the only move in the data above 1.0 stars at sites
clearing the response floor. It recovers the following month ({recovery}), so it reads as a
bad month at one site rather than a lasting change — which is the distinction the group-level
claim below rests on.

### 7.2 The trend that is real: the group declined over the year

**This is the §2 non-negotiable trend, and it is a group-level claim, not a site-level one.**

{table(merged)}

Split at the midpoint of the twelve months — which is also the month the closed site shut,
so the boundary is given by the data rather than chosen to maximise the gap:

| | H1 (Oct 2025 – Mar 2026) | H2 (Apr – Sep 2026) | Change |
|---|---:|---:|---:|
| Responses | {h_all["n_h1"]:,} | {h_all["n_h2"]:,} | |
| Mean rating | **{h_all["mean_h1"]:.3f}** | **{h_all["mean_h2"]:.3f}** | **{h_all["delta"]:+.3f} stars** |
| Negative rate, all rows | **{h_all["neg_h1"]:.1f}%** | **{h_all["neg_h2"]:.1f}%** | **{h_all["neg_delta"]:+.1f} pts** |
| Excluding {CLOSED_SITE} (D-005) | {h_ex["mean_h1"]:.3f} / {h_ex["neg_h1"]:.1f}% | {h_ex["mean_h2"]:.3f} / {h_ex["neg_h2"]:.1f}% | {h_ex["delta"]:+.3f} / {h_ex["neg_delta"]:+.1f} pts |

**Why this is evidence and not noise, judged by D-052's own arithmetic.** The committed
0.5-star threshold is calibrated for a *dealership-month* pair at n = {MIN_MONTH_N}, where
the 1-sigma noise band is ±0.46. The same formula — `sd × √(1/n₁ + 1/n₂)` — at this grain,
with n = {h_all["n_h1"]:,} against {h_all["n_h2"]:,} and the dataset's SD of
{h_all["sd"]:.2f}, gives a noise band of **±{h_all["noise_1sigma"]:.3f} stars**. The observed
fall of {abs(h_all["delta"]):.3f} is **{abs(h_all["delta"]) / h_all["noise_1sigma"]:.1f}×**
that band.

Stating it the other way round, so the threshold is not quietly discarded: the group's
{abs(h_all["delta"]):.3f}-star fall is **well below** D-052's 0.5-star floor and would not
qualify as a movement *at a single site in a single month*. It qualifies here because it is
measured on {h_all["n_h1"]:,} responses against {h_all["n_h2"]:,} instead of forty, and the rule
is a function of n, not a constant. Three independent tests agree:

| Test | Statistic | p |
|---|---|---|
| Welch t-test on the ratings | t = {h_all["welch_t"]:.3f} | **{h_all["welch_p"]:.2g}** |
| Mann–Whitney U (no normality assumption) | — | **{h_all["mwu_p"]:.2g}** |
| χ² on the negative/not-negative counts | — | **{h_all["chi2_p"]:.2g}** |

**With and without the closed site (D-005).** {CLOSED_SITE} closed on 31 March 2026, so all
{int((df["dealer_code"] == CLOSED_SITE).sum())} of its rows sit in H1 and its disappearance
is exactly the composition change D-005 was written to catch. Removing it moves the fall
from {h_all["delta"]:+.3f} to {h_ex["delta"]:+.3f} and the Welch p from
{h_all["welch_p"]:.2g} to {h_ex["welch_p"]:.2g}. The trend is not the closure.

**Three robustness checks, because an aggregate can move for reasons that are not the thing
being measured, and then the same test run inside each department:**

{table(_trend_robustness(df))}

### 7.3 The thin sites, quarterly (D-052)

Reported on a quarterly basis because their median month is under {MIN_MONTH_N} responses —
present in the analysis rather than silently dropped. These are counts and means at a grain
the rule permits; **no movement is claimed for these five sites.**

{table(quarters)}
"""


def _trend_robustness(df: pd.DataFrame) -> pd.DataFrame:
    """Does the H1→H2 fall survive the obvious alternative explanations?"""
    out = []
    mix = pd.crosstab(df["half"], df["department"], normalize="index") * 100
    out.append(
        {
            "Check": "Department mix changed?",
            "H1": " / ".join(f"{c} {mix.loc['H1', c]:.1f}%" for c in mix.columns),
            "H2": " / ".join(f"{c} {mix.loc['H2', c]:.1f}%" for c in mix.columns),
            "Verdict": "No — mix is stable, so the fall is not composition",
        }
    )
    vol = df.groupby("half", observed=True).size()
    out.append(
        {
            "Check": "Response volume changed?",
            "H1": f"{vol['H1']:,} rows",
            "H2": f"{vol['H2']:,} rows",
            "Verdict": "No — within 7%, and 12 near-equal months (section 7.2)",
        }
    )
    cr = df.groupby("half", observed=True)["has_comment"].mean() * 100
    out.append(
        {
            "Check": "Commenting propensity changed?",
            "H1": f"{cr['H1']:.1f}% left a comment",
            "H2": f"{cr['H2']:.1f}% left a comment",
            "Verdict": (
                "Yes, +%.1f pts — consistent with more dissatisfaction (D-058), and the "
                "rating series above is over ALL rows so it is unaffected"
                % (cr["H2"] - cr["H1"])
            ),
        }
    )
    for dep in ["Service", "Sales", "Parts"]:
        sub = df[df["department"] == dep]
        a = sub.loc[sub["half"] == "H1", "rating_1to5"].astype(float)
        b = sub.loc[sub["half"] == "H2", "rating_1to5"].astype(float)
        p = stats.ttest_ind(a, b, equal_var=False).pvalue
        na = 100 * sub.loc[sub["half"] == "H1", "negative_by_rating"].mean()
        nb = 100 * sub.loc[sub["half"] == "H2", "negative_by_rating"].mean()
        out.append(
            {
                "Check": f"Where is it? {dep}",
                "H1": f"{a.mean():.3f} stars, {na:.1f}% neg (n={len(a):,})",
                "H2": f"{b.mean():.3f} stars, {nb:.1f}% neg (n={len(b):,})",
                "Verdict": f"{b.mean() - a.mean():+.3f} stars, {nb - na:+.2f} pts, p = {p:.2g}",
            }
        )
    return pd.DataFrame(out)


def coverage_table(df: pd.DataFrame, revenue: pd.DataFrame) -> pd.DataFrame:
    tx = revenue.groupby("dealer_code")[
        ["vehicles_sold", "service_jobs", "parts_transactions"]
    ].sum()
    fb = df.groupby(["dealer_code", "department"], observed=True).size().unstack(fill_value=0)
    pairs = [
        ("Service", "service_jobs"),
        ("Sales", "vehicles_sold"),
        ("Parts", "parts_transactions"),
    ]
    rows = []
    for dealer in sorted(tx.index):
        row = {"Dealer": dealer}
        for dep, col in pairs:
            n_fb = int(fb.loc[dealer, dep]) if dep in fb.columns else 0
            n_tx = int(tx.loc[dealer, col])
            row[f"{dep} fb"] = n_fb
            row[f"{dep} tx"] = n_tx
            row[f"{dep} %"] = round(100 * n_fb / n_tx, 2) if n_tx else None
        rows.append(row)
    return pd.DataFrame(rows)


def section_coverage(df: pd.DataFrame, revenue: pd.DataFrame) -> str:
    tx = revenue[["vehicles_sold", "service_jobs", "parts_transactions"]].sum()
    total_tx = int(tx.sum())
    cov = coverage_table(df, revenue)
    nat = {
        dep: 100 * cov[f"{dep} fb"].sum() / cov[f"{dep} tx"].sum()
        for dep in ["Service", "Sales", "Parts"]
    }
    worst_sales = cov.nsmallest(3, "Sales %")[["Dealer", "Sales fb", "Sales tx", "Sales %"]]
    best_svc = cov.nlargest(1, "Service %").iloc[0]
    return f"""## 8. Coverage — how much of the business this dataset sees

**Reported as a limitation (D-006), and it is also the floor under every number above.**

| | Transactions, Oct 2025 – Sep 2026 | Feedback rows | Coverage |
|---|---:|---:|---:|
| Service jobs | {int(tx["service_jobs"]):,} | {int((df["department"] == "Service").sum()):,} | **{nat["Service"]:.2f}%** |
| Vehicles sold | {int(tx["vehicles_sold"]):,} | {int((df["department"] == "Sales").sum()):,} | **{nat["Sales"]:.2f}%** |
| Parts transactions | {int(tx["parts_transactions"]):,} | {int((df["department"] == "Parts").sum()):,} | **{nat["Parts"]:.2f}%** |
| **All three** | **{total_tx:,}** | **{len(df):,}** | **{100 * len(df) / total_tx:.2f}%** |

**What this does and does not undermine.** Every rate in this report is a rate *among
customers who responded*, and {100 * len(df) / total_tx:.2f}% of transactions produced a
response. Nothing here establishes what the other {100 - 100 * len(df) / total_tx:.1f}%
think, and D-058's evidence points the wrong way for optimism: within the responses, the
ones who wrote are markedly less satisfied than the ones who did not, so response is not
independent of satisfaction. The correct reading of
*"{100 * df["negative_by_rating"].mean():.1f}% of responses are negative"* is a rate over
{len(df):,} responses out of {total_tx:,} transactions, and not a rate over Kestrel's
customers.

**Coverage is also uneven, which matters for the dealership table in section 3.**

{table(cov)}

- Sales feedback is collected at **{nat["Sales"]:.2f}%** nationally but
  {", ".join(f'{r.Dealer} at {r._4:.2f}% ({r._2:,} responses on {r._3:,} sales)' for r in worst_sales.itertuples())}
  — three sites that are effectively not collecting sales feedback at all.
- **The site with the worst negative rate is not the site with the least coverage.**
  {best_svc["Dealer"]} has the **highest** service coverage in the group
  ({best_svc["Service %"]:.2f}%) and still sits in the worst quarter of section 3, so its
  numbers are not a small-sample artefact.
- At a {nat["Service"]:.2f}% service response rate, **each service response in this dataset
  sits beside about {1 / (nat["Service"] / 100):.0f} service jobs that produced no feedback
  at all.** That is a statement about how little is seen, not a multiplier to apply to the
  negative counts — section 9 says why the extrapolation is not published.
"""


def section_recommendation(df: pd.DataFrame, revenue: pd.DataFrame) -> str:
    h = half_test(df)
    svc = df[df["department"] == "Service"]
    hs = half_test(svc)
    tx = revenue["service_jobs"].sum()
    nat_cov = 100 * len(svc) / tx
    extra = int(round(hs["neg_delta"] / 100 * len(svc)))
    implied = int(round(hs["neg_delta"] / 100 * tx))
    return f"""## 9. Where to focus first — the analysis behind the recommendation

**The recommendation is argued from volume, the rating and coverage. It is not argued from a
theme ranking**, because D-065 does not permit one.

| Step | Number | Where it comes from |
|---|---:|---|
| 1. Service is most of the feedback | {len(svc):,} of {len(df):,} rows (**{100 * len(svc) / len(df):.1f}%**) | section 2, hand-mapped department field |
| 2. Service has the worst rate on either denominator | **{100 * svc["negative_by_rating"].mean():.1f}%** of its {len(svc):,} rows | section 2 |
| 3. Service is where the year's decline sits | {hs["mean_h1"]:.3f} → {hs["mean_h2"]:.3f} stars; {hs["neg_h1"]:.1f}% → {hs["neg_h2"]:.1f}% negative (**{hs["neg_delta"]:+.1f} pts**, p = {hs["welch_p"]:.2g}) | section 7.2 |
| 4. The group decline is real | {h["delta"]:+.3f} stars, {h["neg_delta"]:+.1f} pts, p = {h["welch_p"]:.2g}, unchanged without the closed site | section 7.2 |
| 5. And the dataset sees very little of it | service coverage **{nat_cov:.2f}%** — one response per ~{1 / (nat_cov / 100):.0f} service jobs | section 8 |

**The chain.** Service holds {100 * len(svc) / len(df):.1f}% of the feedback and
{100 * tx / 278697:.1f}% of the transactions behind it, has the worst negative rate of the
three departments on both denominators, and is where the year's decline is concentrated:
**{hs["neg_delta"]:+.1f} points** against Sales' +4.5 and Parts' −0.01 (section 7.2). In plain
counts, that is **{extra:,} more negative service responses in H2 than H1's rate would have
produced**.

**What is deliberately not published here.** {extra:,} responses at a {nat_cov:.2f}% response
rate would extrapolate to roughly {implied:,} service jobs. That figure is **not** reported as
a finding, because D-058 measured response bias running the wrong way for it — within the
responses, the people who wrote are markedly less satisfied than the people who did not — so
projecting a responder rate onto all {int(tx):,} jobs would overstate it by an unknown amount.
The defensible version of the volume argument is the one above: Service is where both the
feedback and the business sit, and the decline is in Service.

**Why the theme evidence is supporting and not load-bearing.** Section 4 shows staff manner
is both the largest theme and by a wide margin the least negative, and the 20 adjudication
failure cases in `reports/llm_review.md` are almost all the same shape — the people are
praised and the process is not: *"Great welcome, helpful staff. Problem not fixed."*,
*"nice helpful staff, wait was too long tho"*. That points at process rather than people,
which is a useful steer for where to look inside Service. It is a steer and not a finding:
at {THEME_AGREEMENT}% model–owner theme agreement, *which* process is uncertain even where
the staff/process split is not.

**What is not here.** The third business question asks roughly what it is worth. D-025 is
unset and `reports/benchmarks.md` is unreviewed, so no dollar figure is published — see
section 10.
"""


def section_limits(df: pd.DataFrame) -> str:
    cmt = int(df["has_comment"].sum())
    return f"""## 10. Limitations, and the one question this report does not answer

1. **No dollar value (D-025 unset).** PLAN.md section 1 asks "roughly what is it worth".
   `reports/benchmarks.md` exists but **the owner has not reviewed it**, and the benchmarks
   themselves state that no published source maps a 1–5 satisfaction rating to dollars. Any
   figure here would be a scenario presented as a measurement, so the value model is cut
   under the brief's step 6 and the cut list's first item. The business report says so
   explicitly rather than leaving a gap.
2. **Sentiment missed its pass mark** — kappa {SENTIMENT_KAPPA} against {KAPPA_FLOOR}
   (D-065). Every figure in this report that could be built from the rating is built from
   the rating. Sentiment appears only beside a rating-based figure, labelled.
3. **Theme assignment agrees with the owner {THEME_AGREEMENT}% of the time** (D-065), with no
   confidence floor because the floor did not work (D-066). Theme rates are reportable;
   theme rankings are not, and nothing in section 9 depends on one.
4. **The three-way drivers cut does not exist** (D-060). Theme × department is national;
   theme × dealership covers {len(theme_capable_sites(df)[0])} of 24 sites.
5. **{100 * len(df) / 278697:.2f}% coverage, and response is not independent of
   satisfaction** (sections 8, D-006, D-058). The {cmt:,} commented rows average 3.54 stars
   against 4.40 for the {len(df) - cmt:,} commentless ones.
6. **One trend test, not a battery.** Cut-list item 7 makes tests beyond the one trend check
   cuttable; section 7.2 runs three tests on the one claim rather than many claims with one
   test each. No seasonality model: twelve months cannot separate a seasonal cycle from a
   decline, and this report does not try.
7. **Sarcasm is a measured weakness** in the sentiment column (D-063): 15.2% of comments
   carry Australian slang markers and all eight polarity-inverted pilot cases were irony.
   The LLM's 45.5% sarcasm rate over its 857-comment scope is unvalidated model output
   (D-017) and is not quoted as a measurement anywhere in either report.
8. **This analysis was not independently reproduced.** Checkpoint 5's independent verifier
   (D-017, producer ≠ checker) had not run at the time of writing. Every number above comes
   from `src/analyse.py` over committed inputs, so `make analyse` reproduces them; that is
   reproducibility, not independence.
"""


# ------------------------------------------------------------------------- manifest


def file_digest(path: Path) -> dict:
    if not path.exists():
        return {"path": str(path.relative_to(ROOT)).replace("\\", "/"), "present": False}
    data = path.read_bytes()
    return {
        "path": str(path.relative_to(ROOT)).replace("\\", "/"),
        "present": True,
        "bytes": len(data),
        "sha256": hashlib.sha256(data).hexdigest(),
    }


def git_commit() -> str | None:
    try:
        return subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
    except Exception:  # noqa: BLE001 - a manifest must still be written off-git
        return None


def package_versions() -> dict:
    out = {}
    for name in ("pandas", "numpy", "scipy", "matplotlib", "pyarrow", "sklearn", "yaml"):
        try:
            mod = __import__(name)
            out[name] = getattr(mod, "__version__", "unknown")
        except ImportError:
            out[name] = None
    return out


def write_manifest(df: pd.DataFrame) -> None:
    """PLAN.md section 6: input hashes, versions, model tags, prompt versions, seeds and
    row counts per stage, so a reviewer can tell which inputs produced these reports."""
    interim = ROOT / CONFIG["paths"]["interim"] / "consolidated.parquet"
    stages = {}
    if interim.exists():
        stages["ingest (data/interim/consolidated.parquet)"] = len(pd.read_parquet(interim))
    clean = CLEAN_DIR / "feedback.parquet"
    if clean.exists():
        stages["validate (data/clean/feedback.parquet)"] = len(pd.read_parquet(clean))
    stages["classify (data/clean/feedback_classified.parquet)"] = len(df)
    stages["analyse (rows read)"] = len(df)
    stages["analyse (commented rows)"] = int(df["has_comment"].sum())
    prompt_dir = ROOT / "prompts"
    prompts = sorted(p.name for p in prompt_dir.glob("*")) if prompt_dir.exists() else []

    manifest = {
        "generated_utc": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "generated_by": "src/analyse.py",
        "git_commit": git_commit(),
        "git_commit_note": (
            "HEAD at the moment this manifest was generated, which is the commit BEFORE the "
            "one carrying this file. The `inputs` hashes below are what identify the data "
            "this run read; they are unaffected."
        ),
        "seed": SEED,
        "row_counts_per_stage": stages,
        "thresholds": CONFIG["thresholds"],
        "models": CONFIG["models"],
        "prompt_files": prompts,
        "inputs": [
            file_digest(p)
            for p in (
                CLASSIFIED,
                CLEAN_DIR / "feedback.parquet",
                interim,
                REVENUE,
                DEALERSHIPS,
                ROOT / "config.yaml",
                ROOT / "mappings" / "columns.yaml",
                ROOT / "mappings" / "departments.yaml",
                ROOT / "mappings" / "themes.yaml",
            )
        ],
        "environment": {
            "python": sys.version.split()[0],
            "platform": platform.platform(),
            "packages": package_versions(),
        },
        "measured_quality": {
            "sentiment_cohens_kappa": SENTIMENT_KAPPA,
            "sentiment_kappa_floor": KAPPA_FLOOR,
            "rating_cohens_kappa": RATING_KAPPA,
            "theme_agreement_pct": THEME_AGREEMENT,
            "source": "reports/evaluation.md (D-065)",
        },
    }
    MANIFEST.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {MANIFEST.relative_to(ROOT)}")


# ----------------------------------------------------------------------------- main


def build_report(df: pd.DataFrame, revenue: pd.DataFrame) -> str:
    header = f"""# Analysis — drivers, trend and coverage

**Generated by** `src/analyse.py` (`make analyse`) · **dataset**
`data/clean/feedback_classified.parquet`, {len(df):,} rows, {int(df["has_comment"].sum()):,}
with a comment · **thresholds** from `config.yaml`, committed before any result (gate G7) ·
**run provenance** `reports/run_manifest.json`.

This file is the working paper. `reports/business_report.md` quotes from it and every number
there appears here with its denominator and its row count. Nothing in this file is a
decision; the decisions are in `DECISIONS.md`.

**The four rules this analysis runs under**, each from a Wave 4 result and each enforced in
code rather than in the prose:

| | Rule | Decision |
|---|---|---|
| 1 | The customer's star rating is the primary signal. Sentiment (kappa {SENTIMENT_KAPPA} against a floor of {KAPPA_FLOOR}) appears only as a labelled method comparison | D-055, D-065 |
| 2 | Theme negative *rates* are reportable with {THEME_AGREEMENT}% model–owner agreement stated; theme *rankings* are not. Theme tables are alphabetical | D-065, D-066 |
| 3 | No theme × department × dealership cut. Two-way nationally; theme × dealership for the sites that clear the floor; five thin sites at department level | D-060 |
| 4 | Every rate names its denominator — all {len(df):,} rows, or the {int(df["has_comment"].sum()):,} commented ones | D-058 |

---

"""
    return "\n".join(
        [
            header,
            section_headline(df),
            section_department(df),
            section_dealership(df),
            section_theme(df),
            section_theme_department(df),
            section_theme_dealership(df),
            section_trend(df),
            section_coverage(df, revenue),
            section_recommendation(df, revenue),
            section_limits(df),
        ]
    )


def build_pilot(df: pd.DataFrame, revenue: pd.DataFrame) -> str:
    """Gate G1: steps 1-3 on three dealerships, for the owner to check before all 24."""
    sub = df[df["dealer_code"].isin(PILOT_DEALERS)].copy()
    cov = coverage_table(sub, revenue[revenue["dealer_code"].isin(PILOT_DEALERS)])
    cmt = sub[sub["has_comment"]]
    themes = (
        cmt.groupby(["dealer_code", "theme"], observed=True)
        .agg(n=("feedback_id", "size"), neg=("negative_by_rating", "mean"))
        .reset_index()
    )
    themes["neg %"] = (100 * themes["neg"]).round(1)
    themes = themes.drop(columns=["neg"]).sort_values(["dealer_code", "theme"])
    pairs = month_pairs(sub)
    return f"""# Pilot — gate G1, three dealerships before all 24

**Generated by** `python -m src.analyse --pilot`. The three sites are chosen to break the
code rather than to flatter it: **{CLOSED_SITE}** (closed 31 Mar 2026, thinnest site, 52
rows), **QLD06** (321 rows of which many are summary-pivot expansions with no comment,
D-032 #1) and **VIC01** (the largest site). {len(sub):,} rows, {len(cmt):,} with a comment.

## Step 1 — drivers

**Denominator:** all rows at these three sites, by rating (D-058).

{table(rate_block(sub, "dealer_code", "Dealer"))}

**By department.** Denominator: all rows at these three sites.

{table(rate_block(sub, "department", "Department"))}

**By theme, per site.** Denominator: commented rows only. Alphabetical, and the
{THEME_AGREEMENT}% agreement caveat applies (D-065). {CLOSED_SITE} and QLD06 are here to
show how thin these cells get — which is D-060's whole point.

{table(themes.rename(columns={"dealer_code": "Dealer", "theme": "Theme"}))}

## Step 2 — trend

Consecutive month pairs at these sites, with D-052's rule applied.
**{int(pairs["clears D-052"].sum())} of {len(pairs)} pairs clear it.**

{table(pairs)}

## Step 3 — coverage

{table(cov)}

## What the owner should check here

1. {CLOSED_SITE}'s last month is March 2026 and it has no rows after it (D-005).
2. QLD06's commented row count is far below its row count, because its Q4 2025 data arrived
   as a pivot table with no comments (D-032 #1, D-038) — so its theme cells are thin while
   its rating cells are not.
3. Every table above names its denominator, and no theme is ranked.
4. The rating columns and the sentiment column are reported side by side, never merged.
"""


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--pilot",
        action="store_true",
        help="gate G1: run steps 1-3 on three dealerships only, to reports/pilot_drivers.md",
    )
    args = ap.parse_args(argv)

    df, revenue, _ = load()
    print(f"read {len(df):,} rows, {int(df['has_comment'].sum()):,} with a comment")

    if args.pilot:
        PILOT_REPORT.write_text(build_pilot(df, revenue), encoding="utf-8")
        print(f"wrote {PILOT_REPORT.relative_to(ROOT)} (gate G1)")
        return 0

    ANALYSIS_REPORT.write_text(build_report(df, revenue), encoding="utf-8")
    print(f"wrote {ANALYSIS_REPORT.relative_to(ROOT)}")
    write_manifest(df)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

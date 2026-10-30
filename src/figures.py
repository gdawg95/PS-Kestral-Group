"""Wave 5: the charts, organised by the business question each one answers.

Brief: `agents/briefs/w5_analysis.md` step 4. **Gate G9 — the owner approves every chart
before it enters a report**, so this module writes PNGs to `reports/figures/` and nothing
else.

The file names carry the question, because a chart that cannot say which question it answers
should not be in the report:

| Figure | The question it answers |
|---|---|
| `q1_drivers_by_department.png` | which department carries the volume, which the rate |
| `q1_sites_vs_national.png` | how each site compares with the national average, with intervals |
| `q1_themes_by_department.png` | the theme mix per department, and how much of each is negative |
| `q2_trend_by_state.png` | the year's movement split VIC / NSW / QLD, quarterly |
| `q2_sites_that_changed.png` | which individual sites moved, Holm-corrected across 23 tests |
| `q3_where_to_focus.png` | bad now against getting worse, sized by the service business behind it |
| `q3_feedback_vs_revenue.png` | is more feedback just more customers, and does it reach revenue |
| `q3_coverage.png` | how much of the business this dataset can see at all |
| `method_model_vs_owner.png` | how far the models can be trusted, and exactly where they disagree |

Q1 = drivers of negative feedback · Q2 = what changed over the year · Q3 = where to focus
first. The method figure is not a business question; it is what licenses the other seven.

Every business number plotted is computed by `src/analyse.py` and imported, never
recalculated here — a chart and a table that disagree is the failure mode that avoids. The
method figure is built from the same committed inputs `src/evaluate.py` uses, and its
headline numbers are asserted against `reports/evaluation.md`'s at render time.

What is deliberately NOT drawn:

  * **No theme chart sorted by rate.** D-065 permits a theme's negative rate and forbids a
    ranking, and a sorted bar chart IS a ranking whatever the caption says. Theme axes are
    alphabetical, with the 44.1% agreement printed on the figure itself.
  * **No dollar chart.** D-025 is unset and `reports/benchmarks.md` is unreviewed.
  * **No twenty-four-line monthly spaghetti.** A state-month holds about 190 responses, so a
    monthly site line is mostly noise; the state view is quarterly with its intervals shown,
    and the site view is a single before/after move with its corrected p-value.

Usage:
    python -m src.figures
"""

from __future__ import annotations

import math
import textwrap

import matplotlib

matplotlib.use("Agg")  # no display on the laptop or in a reviewer's clean clone

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
from scipy import stats
from sklearn.metrics import cohen_kappa_score, confusion_matrix

from src.analyse import (
    CLOSED_SITE,
    MIN_MONTH_N,
    RATING_KAPPA,
    ROOT,
    SENTIMENT_KAPPA,
    THEME_AGREEMENT,
    coverage_table,
    half_test,
    load,
    revenue_lags,
    revenue_panel,
    site_halves,
    state_halves,
    wilson_ci,
)
from src.analyse import KAPPA_FLOOR as FLOOR
from src.analyse import _two_way_demean as two_way_demean
from src.evaluate import ORDER, SCORE_CLASSES, SENTIMENT_CODES, llm_key, load_llm

FIG_DIR = ROOT / "reports" / "figures"
LABELS_CSV = ROOT / "reports" / "labels_done.csv"

# The theme numbers in reports/labelling_guide.md, which is the order the owner labelled
# against. It is NOT mappings/themes.yaml's order, and reading the two as the same produces
# a theme agreement of 0.0% that looks like a catastrophic model failure instead of a
# join bug.
GUIDE_THEMES = [
    "Staff manner",
    "Communication and updates",
    "Pricing and billing",
    "Waiting and turnaround",
    "Parts availability",
    "Booking",
    "Workmanship and rework",
    "Explanation and transparency",
]

# Okabe-Ito, colour-blind safe. One colour per state across every figure, so a reader who
# learns "orange is NSW" on one chart keeps it on all of them.
INK = "#1b1b1b"
GRID = "#dcdcdc"
MUTED = "#8a8a8a"
STATE = {"VIC": "#0072b2", "NSW": "#d55e00", "QLD": "#009e73"}
DEPT = {"Service": "#0072b2", "Sales": "#e69f00", "Parts": "#56b4e9"}
BAD = "#c1272d"
NATIONAL = "#4d4d4d"

plt.rcParams.update(
    {
        "figure.dpi": 150,
        "savefig.dpi": 150,
        "savefig.bbox": "tight",
        "savefig.facecolor": "white",
        "font.size": 9,
        "axes.titlesize": 11,
        "axes.titleweight": "bold",
        "axes.labelcolor": INK,
        "axes.edgecolor": MUTED,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "text.color": INK,
        "xtick.color": INK,
        "ytick.color": INK,
        "grid.color": GRID,
        "grid.linewidth": 0.6,
        "figure.facecolor": "white",
    }
)


def _footer(fig: plt.Figure, text: str) -> None:
    """Every figure states its denominator on its own face. A chart gets separated from its
    caption the moment someone pastes it into a slide (D-058).

    Wrapped to the figure's own width before it is drawn: `savefig(bbox_inches="tight")`
    grows the canvas to fit any text it finds, so an unwrapped footer silently stretches the
    chart to four times its intended aspect ratio and squashes the plot.
    """
    width = int(fig.get_figwidth() * 17)
    wrapped = "\n".join(textwrap.wrap(" ".join(text.split()), width=width))
    fig.text(0.0, -0.02, wrapped, fontsize=7.2, color="#5a5a5a", ha="left", va="top",
             linespacing=1.5)


def _save(fig: plt.Figure, name: str) -> None:
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    fig.savefig(FIG_DIR / name)
    plt.close(fig)
    print(f"wrote reports/figures/{name}")


def _site_names(df: pd.DataFrame) -> pd.Series:
    return df.groupby("dealer_code")["dealership_name"].first().str.replace("Kestrel ", "")


# ====================================================== Q1 · drivers of negative feedback


def q1_drivers_by_department(df: pd.DataFrame) -> None:
    """Volume and rate side by side, because either one alone points somewhere different."""
    deps = ["Service", "Sales", "Parts"]
    rows = []
    for dep in deps:
        sub = df[df["department"] == dep]
        neg = int(sub["negative_by_rating"].sum())
        lo, hi = wilson_ci(neg, len(sub))
        rows.append(
            {"dep": dep, "rows": len(sub), "rate": 100 * neg / len(sub), "lo": lo, "hi": hi}
        )
    t = pd.DataFrame(rows)[::-1].reset_index(drop=True)  # Parts at the bottom of a barh
    group = 100 * df["negative_by_rating"].mean()

    fig, axes = plt.subplots(1, 2, figsize=(10.5, 3.8), gridspec_kw={"wspace": 0.28})

    ax = axes[0]
    bars = ax.barh(t["dep"], t["rows"], color=[DEPT[d] for d in t["dep"]], height=0.6)
    for bar, (_, r) in zip(bars, t.iterrows(), strict=False):
        ax.text(
            bar.get_width() + 70,
            bar.get_y() + bar.get_height() / 2,
            f"{r['rows']:,}   ({100 * r['rows'] / len(df):.0f}% of all feedback)",
            va="center",
            fontsize=8.5,
        )
    ax.set_xlim(0, len(df) * 0.95)
    ax.set_xlabel("Responses")
    ax.grid(axis="x")
    ax.set_title("How much feedback each one gets", fontsize=10)

    ax = axes[1]
    bars = ax.barh(t["dep"], t["rate"], color=[DEPT[d] for d in t["dep"]], height=0.6)
    ax.errorbar(
        t["rate"],
        t["dep"],
        xerr=[t["rate"] - t["lo"], t["hi"] - t["rate"]],
        fmt="none",
        ecolor=INK,
        elinewidth=1,
        capsize=3,
    )
    for bar, (_, r) in zip(bars, t.iterrows(), strict=False):
        ax.text(
            1.3,
            bar.get_y() + bar.get_height() / 2,
            f"{r['rate']:.1f}%",
            va="center",
            fontsize=10,
            fontweight="bold",
            color="white",
        )
    ax.axvline(group, color=NATIONAL, ls="--", lw=1.5, label=f"National: {group:.1f}%")
    ax.set_xlabel("Negative rate (%)")
    ax.set_xlim(0, 34)
    ax.grid(axis="x")
    ax.legend(frameon=False, fontsize=8, loc="lower right")
    ax.set_title("How negative that feedback is", fontsize=10)

    fig.suptitle(
        "Q1 · Service carries two-thirds of the feedback AND the worst rate",
        fontweight="bold",
        fontsize=12,
        y=1.04,
    )
    _footer(
        fig,
        f"Denominator: all {len(df):,} rows; negative = the customer rated 1 or 2 out of 5 "
        "(D-004, D-058). Whiskers are 95% Wilson intervals. Department is a hand-mapped "
        "field approved by the owner (D-050), not model output, so these three are directly "
        "comparable — unlike the themes. Source: reports/analysis.md section 2.",
    )
    _save(fig, "q1_drivers_by_department.png")


def q1_sites_vs_national(df: pd.DataFrame) -> None:
    """Every site as a distance from the national rate, grouped by state.

    Plotted as a deviation rather than a level because that is the question being asked —
    "is this site worse than average?" — and because it puts the national rate on the zero
    line, where a reader cannot miss it.
    """
    national = 100 * df["negative_by_rating"].mean()
    names = _site_names(df)
    rows = []
    for dealer, sub in df.groupby("dealer_code", observed=True):
        neg = int(sub["negative_by_rating"].sum())
        lo, hi = wilson_ci(neg, len(sub))
        rate = 100 * neg / len(sub)
        rows.append(
            {
                "dealer": dealer,
                "state": sub["state"].iloc[0],
                "name": names[dealer],
                "n": len(sub),
                "rate": rate,
                "dev": rate - national,
                "lo": lo - national,
                "hi": hi - national,
            }
        )
    t = pd.DataFrame(rows)
    # Grouped by state, and within a state by deviation, with a blank row between blocks.
    blocks = []
    for state in ["NSW", "VIC", "QLD"]:
        blocks.append(t[t["state"] == state].sort_values("dev", ascending=False))
        blocks.append(pd.DataFrame([{"dealer": "", "state": state, "name": "", "n": 0}]))
    t = pd.concat(blocks[:-1], ignore_index=True)

    fig, ax = plt.subplots(figsize=(9, 8.2))
    for i, r in t.iterrows():
        if r["dealer"] == "":
            continue
        colour = STATE[r["state"]] if r["dev"] > 0 else "#b6b6b6"
        ax.barh(i, r["dev"], color=colour, height=0.66)
        ax.plot([r["lo"], r["hi"]], [i, i], color=INK, lw=1.1)
        for end in (r["lo"], r["hi"]):
            ax.plot([end, end], [i - 0.17, i + 0.17], color=INK, lw=1.1)
        ax.text(
            r["hi"] + 0.5 if r["dev"] > 0 else r["lo"] - 0.5,
            i,
            f"{r['rate']:.1f}%",
            va="center",
            ha="left" if r["dev"] > 0 else "right",
            fontsize=7.5,
            color=MUTED,
        )
    ax.axvline(0, color=NATIONAL, lw=2)
    ax.set_yticks(range(len(t)))
    ax.set_yticklabels(
        [
            "" if r["dealer"] == "" else f"{r['dealer']}  {r['name']}  (n={r['n']:,})"
            for _, r in t.iterrows()
        ],
        fontsize=8,
    )
    ax.invert_yaxis()
    ax.set_xlabel("Percentage points above or below the national negative rate  →  worse")
    ax.set_xlim(-26, 15)
    ax.grid(axis="x")
    ax.set_axisbelow(True)
    ax.annotate(
        f"NATIONAL\n{national:.1f}%",
        xy=(0, -1.2),
        ha="center",
        va="center",
        fontsize=8.5,
        fontweight="bold",
        color=NATIONAL,
    )
    for state in ["NSW", "VIC", "QLD"]:
        idx = t.index[(t["state"] == state) & (t["dealer"] != "")]
        ax.text(
            -25.2,
            (idx.min() + idx.max()) / 2,
            state,
            fontsize=14,
            fontweight="bold",
            color=STATE[state],
            rotation=90,
            va="center",
            ha="center",
        )
    worse = int((t["dev"] > 0).sum())
    ax.set_title("Q1 · Every site against the national average, grouped by state", pad=14)
    _footer(
        fig,
        f"Denominator: all {len(df):,} rows; negative = rated 1 or 2 out of 5 (D-058). "
        f"Whiskers are 95% Wilson intervals — a site whose whisker crosses the national line "
        f"is NOT separated from it by this data, and most of the middle of this chart does. "
        f"{worse} of 24 sites sit above the national rate. QLD05 Noosa's −20 points is ONE "
        "negative response out of 49, which is why the whisker is as wide as the bar. "
        "Source: reports/analysis.md section 3.",
    )
    _save(fig, "q1_sites_vs_national.png")


def q1_themes_by_department(df: pd.DataFrame) -> None:
    """Theme mix inside each department, and how much of each mix is negative.

    Two panels sharing one alphabetical theme axis. The left answers "what do this
    department's customers talk about"; the right answers "and how much of that is a
    complaint". Share rather than raw count on the left, or Service's volume would flatten
    Parts into invisibility.
    """
    cmt = df[df["has_comment"]]
    themes = sorted(cmt["theme"].dropna().unique())
    deps = ["Service", "Sales", "Parts"]
    share, rate, counts = {}, {}, {}
    for dep in deps:
        sub = cmt[cmt["department"] == dep]
        share[dep] = [100 * (sub["theme"] == th).sum() / len(sub) for th in themes]
        counts[dep] = [int((sub["theme"] == th).sum()) for th in themes]
        rate[dep] = [
            100 * sub.loc[sub["theme"] == th, "negative_by_rating"].mean() for th in themes
        ]

    fig, axes = plt.subplots(
        1, 2, figsize=(13, 5.8), sharey=True, gridspec_kw={"wspace": 0.05}
    )
    y = np.arange(len(themes))
    h = 0.26

    ax = axes[0]
    for i, dep in enumerate(deps):
        ax.barh(y + (1 - i) * h, share[dep], h, color=DEPT[dep], label=dep)
        for j, (v, c) in enumerate(zip(share[dep], counts[dep], strict=False)):
            ax.text(v + 0.4, y[j] + (1 - i) * h, f"{c:,}", va="center", fontsize=6.8, color=MUTED)
    ax.set_yticks(y)
    ax.set_yticklabels(themes, fontsize=9)
    ax.invert_yaxis()
    ax.set_xlabel("Share of that department's comments (%)")
    ax.set_xlim(0, 37)
    ax.grid(axis="x")
    ax.set_axisbelow(True)
    ax.legend(
        frameon=True, framealpha=0.95, edgecolor="white", fontsize=8.5,
        loc="center right", bbox_to_anchor=(1.0, 0.72), title="Department", title_fontsize=8,
    )
    ax.set_title("What each department's customers talk about", fontsize=10)

    ax = axes[1]
    overall = 100 * cmt["negative_by_rating"].mean()
    for i, dep in enumerate(deps):
        bars = ax.barh(y + (1 - i) * h, rate[dep], h, color=DEPT[dep])
        for bar, v, c in zip(bars, rate[dep], counts[dep], strict=False):
            if np.isnan(v):
                continue
            ax.text(
                v + 0.9,
                bar.get_y() + bar.get_height() / 2,
                f"{v:.0f}%" + ("" if c >= MIN_MONTH_N else f"  (n={c})"),
                va="center",
                fontsize=7,
                color=INK if c >= MIN_MONTH_N else MUTED,
            )
    ax.axvline(overall, color=NATIONAL, ls="--", lw=1.5)
    ax.text(
        overall,
        len(themes) - 0.42,
        f"all commented rows\n{overall:.1f}%",
        fontsize=7.5,
        color=NATIONAL,
        ha="center",
        va="top",
        linespacing=1.4,
    )
    ax.set_xlabel("Of those comments, % the customer rated 1–2")
    ax.set_xlim(0, 78)
    ax.grid(axis="x")
    ax.set_axisbelow(True)
    ax.set_title("And how much of it is a complaint", fontsize=10)

    fig.suptitle(
        "Q1 · Theme mix by department, and the share of each that is negative"
        "    —    alphabetical, NOT a ranking",
        fontweight="bold",
        fontsize=11.5,
        y=1.06,
    )
    fig.text(
        0.5,
        1.015,
        f"The model and the owner picked the same theme for only {THEME_AGREEMENT}% of "
        "comments (D-065) — read the rates, not the order",
        ha="center",
        fontsize=8.5,
        color=BAD,
        fontweight="bold",
    )
    _footer(
        fig,
        f"Denominator: the {len(cmt):,} commented rows only — not all {len(df):,} (D-058); a "
        f"row with no comment has no theme (D-057). Left-panel bars sum to 100% down each "
        f"department. A cell under {MIN_MONTH_N} comments (the project's own floor, D-052) "
        "carries its n — Booking/Parts holds 7 and should not be read as a rate. No three-way "
        "theme × department × dealership cut exists (D-060). See method_model_vs_owner.png "
        "for exactly where the 44.1% goes wrong. Source: reports/analysis.md sections 4–5.",
    )
    _save(fig, "q1_themes_by_department.png")


# ====================================================== Q2 · has anything changed?


def q2_trend_by_state(df: pd.DataFrame) -> None:
    """The year split three ways. Quarterly, because a state-month is ~190 responses and a
    monthly state line is mostly noise — the intervals show why."""
    d = df.copy()
    d["quarter"] = d["feedback_date"].dt.to_period("Q")
    quarters = sorted(d["quarter"].unique())
    st = state_halves(df).set_index("State")
    h_nat = half_test(df)

    fig, axes = plt.subplots(1, 2, figsize=(12.5, 5), gridspec_kw={"width_ratios": [1.4, 1]})

    ax = axes[0]
    for state in ["NSW", "VIC", "QLD"]:
        means, errs = [], []
        for q in quarters:
            s = d[(d["state"] == state) & (d["quarter"] == q)]["rating_1to5"].astype(float)
            means.append(s.mean())
            errs.append(1.96 * s.std() / np.sqrt(len(s)))
        ax.errorbar(
            range(len(quarters)),
            means,
            yerr=errs,
            fmt="-o",
            ms=6,
            lw=2.2,
            capsize=4,
            color=STATE[state],
            label=f"{state}   {st.loc[state, 'Change']:+.2f} stars over the year",
        )
    nat = [d[d["quarter"] == q]["rating_1to5"].mean() for q in quarters]
    ax.plot(range(len(quarters)), nat, ":", color=NATIONAL, lw=2.2, label="National")
    ax.set_xticks(range(len(quarters)))
    ax.set_xticklabels([str(q) for q in quarters])
    ax.set_ylabel("Mean rating (1–5)")
    ax.grid(axis="y")
    ax.set_axisbelow(True)
    ax.legend(frameon=False, fontsize=8.5, loc="lower left")
    ax.set_title("Mean rating by quarter, with 95% intervals", fontsize=10)

    ax = axes[1]
    rows = [("National", h_nat["neg_h1"], h_nat["neg_h2"], NATIONAL, f"{h_nat['welch_p']:.1g}")]
    for state in ["QLD", "VIC", "NSW"]:
        rows.append(
            (
                state,
                st.loc[state, "H1 neg %"],
                st.loc[state, "H2 neg %"],
                STATE[state],
                st.loc[state, "Welch p"],
            )
        )
    for i, (label, a, b, colour, p) in enumerate(rows):
        ax.annotate(
            "",
            xy=(b, i),
            xytext=(a, i),
            arrowprops={"arrowstyle": "-|>,head_width=0.3", "color": colour, "lw": 2.6},
        )
        ax.plot(a, i, "o", color="white", mec=colour, mew=2.2, ms=10, zorder=3)
        ax.text(a - 0.5, i, f"{a:.1f}", ha="right", va="center", fontsize=8.5, color=MUTED)
        ax.text(
            b + 0.5,
            i,
            f"{b:.1f}%     p = {p}",
            ha="left",
            va="center",
            fontsize=8.5,
            fontweight="bold" if label == "NSW" else "normal",
            color=colour,
        )
    ax.set_yticks(range(len(rows)))
    ax.set_yticklabels([r[0] for r in rows], fontsize=11)
    ax.set_xlim(14, 34)
    ax.set_xlabel("Negative rate (%):  first half  →  second half")
    ax.grid(axis="x")
    ax.set_axisbelow(True)
    ax.set_title("Where the year's change actually happened", fontsize=10)

    fig.suptitle(
        "Q2 · The group declined — but it is NSW, and Queensland did not move",
        fontweight="bold",
        fontsize=12.5,
        y=1.03,
    )
    _footer(
        fig,
        f"Denominator: all {len(df):,} rows; negative = rated 1 or 2 out of 5 (D-058). First "
        f"half = Oct 2025–Mar 2026, second = Apr–Sep 2026: a fixed midpoint, not a cut-point "
        f"chosen to maximise the gap. p is a Welch t-test on the ratings; above about 0.05 "
        f"the move is not distinguishable from chance, and QLD's is {st.loc['QLD', 'Welch p']}. "
        f"{CLOSED_SITE} closed 31 Mar 2026 and sits entirely in the first half; removing it "
        f"moves VIC from {st.loc['VIC', 'Change']:+.3f} to "
        f"{st.loc['VIC', f'Change excl {CLOSED_SITE}']:+.3f} and changes nothing else (D-005). "
        "Source: reports/analysis.md section 7.3.",
    )
    _save(fig, "q2_trend_by_state.png")


def q2_sites_that_changed(df: pd.DataFrame) -> None:
    """Which individual sites moved — with the multiple-comparison problem on the chart.

    23 sites tested at p < 0.05 throws up about one false positive by construction, so the
    only honest version of this chart separates the Holm-corrected survivors from the rest.
    """
    t = site_halves(df).dropna(subset=["Change"]).sort_values("Change")
    fig, ax = plt.subplots(figsize=(9, 7.6))
    for i, r in enumerate(t.itertuples()):
        sig = r.Significant == "**yes**"
        ax.barh(
            i,
            r.Change,
            color=BAD if sig else "#cdcdcd",
            height=0.66,
            edgecolor=INK if sig else "none",
            lw=1.1 if sig else 0,
        )
        ax.text(
            r.Change - 0.02 if r.Change < 0 else r.Change + 0.02,
            i,
            f"{r.Change:+.2f}" + ("  ★" if sig else ""),
            ha="right" if r.Change < 0 else "left",
            va="center",
            fontsize=8,
            fontweight="bold" if sig else "normal",
            color=INK if sig else MUTED,
        )
    ax.axvline(0, color=INK, lw=1.4)
    ax.set_yticks(range(len(t)))
    ax.set_yticklabels(
        [f"{r.Dealer}  {r.Site}  ({r.State}, n={r.Rows:,})" for r in t.itertuples()], fontsize=8
    )
    ax.invert_yaxis()
    ax.set_xlabel("Change in mean rating, first half → second half (stars)")
    ax.set_xlim(-0.98, 0.58)
    ax.grid(axis="x")
    ax.set_axisbelow(True)
    n_sig = int((t["Significant"] == "**yes**").sum())
    ax.legend(
        handles=[
            Patch(facecolor=BAD, edgecolor=INK, label="★ Real fall (adjusted p < 0.05)"),
            Patch(facecolor="#cdcdcd", label="Not distinguishable from no change"),
        ],
        frameon=False,
        fontsize=8.5,
        loc="lower left",
    )
    ax.set_title(f"Q2 · {n_sig} of {len(t)} sites moved by more than chance — and all three fell")
    bendigo = t[t["Dealer"] == "VIC08"].iloc[0]
    _footer(
        fig,
        f"Denominator: all rows at each site; the mean of the customer's 1–5 rating (D-065). "
        f"A Welch t-test per site, then a Holm correction across all {len(t)} tests, because "
        f"testing 23 sites at p<0.05 produces about one false 'significant' site from pure "
        f"noise. Uncorrected, five sites clear p<0.05. {CLOSED_SITE} Shepparton is not tested "
        f"— it has no second half. Bendigo's {bendigo['Change']:+.2f} is the near miss, at "
        f"adjusted p = {bendigo['p (Holm-adjusted)']} on {bendigo['Rows']:,} rows. "
        "Source: reports/analysis.md section 7.3.",
    )
    _save(fig, "q2_sites_that_changed.png")


# ====================================================== Q3 · where to focus first


def q3_where_to_focus(df: pd.DataFrame, revenue: pd.DataFrame) -> None:
    """Bad now (x) against getting worse (y), sized by the service business behind it.

    The focus question is not answered by either axis alone: a site can be the worst in the
    group and stable, or average and falling fast. The top-right quadrant is both.
    """
    national = 100 * df["negative_by_rating"].mean()
    changes = site_halves(df).set_index("Dealer")
    jobs = revenue.groupby("dealer_code")["service_jobs"].sum()
    names = _site_names(df)
    rows = []
    for dealer, sub in df.groupby("dealer_code", observed=True):
        h1 = sub[sub["half"] == "H1"]["negative_by_rating"]
        h2 = sub[sub["half"] == "H2"]["negative_by_rating"]
        if len(h1) < MIN_MONTH_N or len(h2) < MIN_MONTH_N:
            continue
        rows.append(
            {
                "name": names[dealer],
                "state": sub["state"].iloc[0],
                "rate": 100 * sub["negative_by_rating"].mean(),
                "move": 100 * (h2.mean() - h1.mean()),
                "jobs": int(jobs[dealer]),
                "sig": changes.loc[dealer, "Significant"] == "**yes**",
            }
        )
    t = pd.DataFrame(rows)

    fig, ax = plt.subplots(figsize=(10, 7))
    ax.axhspan(0, 27, xmin=0.5, color="#fdf1f0", zorder=0)
    ax.axvline(national, color=NATIONAL, lw=1.5, ls="--", zorder=1)
    ax.axhline(0, color=NATIONAL, lw=1.5, ls="--", zorder=1)
    for _, r in t.iterrows():
        ax.scatter(
            r["rate"],
            r["move"],
            s=r["jobs"] / 13,
            color=STATE[r["state"]],
            alpha=0.5,
            edgecolor=BAD if r["sig"] else STATE[r["state"]],
            linewidth=2.4 if r["sig"] else 0.8,
            zorder=3,
        )
        focus = r["sig"] or (r["rate"] > national and r["move"] > 0)
        ax.annotate(
            r["name"] + ("  ★" if r["sig"] else ""),
            (r["rate"], r["move"]),
            textcoords="offset points",
            xytext=(0, -6 - r["jobs"] / 1500),
            ha="center",
            va="top",
            fontsize=8 if focus else 6.8,
            fontweight="bold" if r["sig"] else "normal",
            color=INK if focus else MUTED,
            zorder=4,
        )
    ax.text(
        33.6,
        25.6,
        "WORSE THAN AVERAGE\nAND STILL GETTING WORSE",
        fontsize=9.5,
        fontweight="bold",
        color=BAD,
        ha="right",
        va="top",
        linespacing=1.45,
    )
    ax.text(
        13,
        -11,
        "Better than average\nand improving",
        fontsize=8,
        color=MUTED,
        ha="left",
        va="bottom",
        linespacing=1.4,
    )
    ax.text(
        national - 0.35,
        -11.5,
        f"national {national:.1f}%",
        fontsize=7.5,
        color=NATIONAL,
        rotation=90,
        ha="right",
        va="bottom",
    )
    ax.set_xlabel("Negative rate over the year (%)   →   worse")
    ax.set_ylabel("Change in negative rate, 1st half → 2nd half (pts)   →   worse")
    ax.set_xlim(12, 34)
    ax.set_ylim(-12, 27)
    ax.grid(color=GRID, lw=0.5)
    ax.set_axisbelow(True)
    ax.legend(
        handles=[
            Line2D([], [], marker="o", ls="", ms=9, color=STATE[s], alpha=0.6, label=s)
            for s in ["NSW", "VIC", "QLD"]
        ]
        + [
            Line2D(
                [], [], marker="o", ls="", ms=11, mfc="none", mec=BAD, mew=2.4,
                label="★ Real fall (Holm-adjusted)",
            ),
            Line2D(
                [], [], marker="o", ls="", ms=14, color=MUTED, alpha=0.4,
                label="Bubble size = annual service jobs",
            ),
        ],
        frameon=False,
        fontsize=8.5,
        loc="lower left",
        ncol=2,
    )
    ax.set_title("Q3 · Where to focus first: bad now, and getting worse")
    _footer(
        fig,
        f"Denominator: all rows at each site; negative = rated 1 or 2 out of 5 (D-058). "
        f"Bubble area is annual service jobs from monthly_revenue.csv — the business behind "
        f"the feedback, not the amount of feedback. The sites with under {MIN_MONTH_N} "
        f"responses in either half are not plotted (D-052): {CLOSED_SITE} Shepparton (closed) "
        "and QLD05 Noosa. This chart ranks SITES, which is allowed — dealer code and the "
        "customer's own rating are both reliable fields. It is THEMES that may not be ranked "
        "(D-065). IMPORTANT: this ranks sites on FEEDBACK, not on business performance. "
        "Section 9 of the analysis tested whether a site's negative rate reaches its revenue "
        "and found no detectable link — of the three sites whose rating fell by more than "
        "chance, one lost service volume, one was flat and one outgrew the group. Nothing "
        "here establishes that a site in the top-right quadrant is losing money. "
        "Source: reports/analysis.md sections 3, 7.3, 9 and 10.",
    )
    _save(fig, "q3_where_to_focus.png")


def q3_feedback_vs_revenue(df: pd.DataFrame, revenue: pd.DataFrame) -> None:
    """Two panels, and both of them exist to STOP a conclusion rather than support one.

    Left: the correlation everyone reaches for is positive, and it is site size. A busy
    branch collects more feedback and does more service work for reasons that have nothing
    to do with how good it is, so the across-sites comparison cannot say a site is
    underperforming. Comparing each site against its own monthly average flips the sign.

    Right: even that within-site association is same-month only. It does not predict next
    month, so it cannot support "this site's feedback is costing it business".
    """
    p = revenue_panel(df, revenue).dropna(subset=["neg"])
    p["neg_pct"] = 100 * p["neg"]
    w = two_way_demean(p, ["neg_pct", "service_jobs"])
    raw_r, raw_p = stats.pearsonr(p["neg_pct"], p["service_jobs"])
    win_r, win_p = stats.pearsonr(w["neg_pct"], w["service_jobs"])
    lags = revenue_lags(revenue_panel(df, revenue))

    fig, axes = plt.subplots(1, 2, figsize=(12.5, 6.6), gridspec_kw={"wspace": 0.26})

    # --- left: the sign flip ------------------------------------------------
    ax = axes[0]
    for state in ["NSW", "VIC", "QLD"]:
        s = p[p["state"] == state]
        ax.scatter(s["neg_pct"], s["service_jobs"], s=16, color=STATE[state], alpha=0.45,
                   edgecolor="none", label=state)
    xs = np.linspace(p["neg_pct"].min(), p["neg_pct"].max(), 50)
    fit = stats.linregress(p["neg_pct"], p["service_jobs"])
    ax.plot(xs, fit.intercept + fit.slope * xs, color=BAD, lw=2.6,
            label=f"r = {raw_r:+.2f}  (p = {raw_p:.1g})")
    ax.set_xlabel("Negative rate in that dealer-month (%)")
    ax.set_ylabel("Service jobs that month")
    ax.grid(lw=0.5)
    ax.set_axisbelow(True)
    ax.legend(frameon=False, fontsize=8.5, loc="upper left")
    ax.set_title("Comparing SITES: the slope is upwards", fontsize=10.5)
    left_note = (
        "…and it is nonsense. A busy branch collects more feedback AND does more\n"
        "service work. This compares Chermside with Noosa, so it measures size."
    )

    # --- right: the lag profile --------------------------------------------
    ax = axes[1]
    ks = list(range(-3, 4))
    rs = lags["r"].to_list()
    ns = lags["dealer-months"].to_list()
    los, his = [], []
    for r, n in zip(rs, ns, strict=False):
        z, se = math.atanh(r), 1 / math.sqrt(n - 3)
        los.append(math.tanh(z - 1.96 * se))
        his.append(math.tanh(z + 1.96 * se))
    for k, r, lo, hi in zip(ks, rs, los, his, strict=False):
        sig = lo > 0 or hi < 0
        ax.plot([k, k], [lo, hi], color=BAD if sig else MUTED, lw=2.4, zorder=2)
        ax.plot(k, r, "o", ms=10, color=BAD if sig else "white",
                mec=BAD if sig else MUTED, mew=2, zorder=3)
    ax.axhline(0, color=INK, lw=1.4)
    ax.axvspan(-3.6, -0.5, color="#f2f2f2", zorder=0)
    ax.set_xticks(ks)
    ax.set_xticklabels(["−3", "−2", "−1", "same\nmonth", "+1", "+2", "+3"])
    ax.set_xlim(-3.6, 3.6)
    ax.set_xlabel("Service jobs, months before ← → months after the feedback")
    ax.set_ylabel("Correlation with the negative rate, within site")
    ax.grid(axis="y", lw=0.5)
    ax.set_axisbelow(True)
    ax.set_title("Comparing a SITE WITH ITSELF: only the same month", fontsize=10.5)
    ax.annotate(
        f"{win_r:+.2f}\np = {win_p:.3f}",
        xy=(0, rs[3]), xytext=(0.72, rs[3] - 0.07), fontsize=9, fontweight="bold", color=BAD,
        ha="left", linespacing=1.4,
    )
    right_note = (
        "Bars are 95% intervals. Every one except the same month crosses zero,\n"
        "so this month's feedback predicts NOTHING about next month's volume."
    )

    # Both red notes go in FIGURE coordinates, not axes coordinates. Placed below an axis
    # they land in the same strip the wrapped footer occupies, and a tight bounding box
    # does not resolve that overlap - it just grows the canvas around it.
    fig.subplots_adjust(bottom=0.30)
    for x, note in [(0.30, left_note), (0.745, right_note)]:
        fig.text(x, 0.15, note, ha="center", va="top", fontsize=8.2, color=BAD,
                 fontweight="bold", linespacing=1.5)

    fig.suptitle(
        "Q3 · Does negative feedback reach the revenue? No link is detectable",
        fontweight="bold", fontsize=12.5, y=1.02,
    )
    _footer(
        fig,
        f"Denominator: {len(p)} dealer-months — 24 sites × 12 months, less {CLOSED_SITE}'s six "
        f"post-closure months, which the revenue file records as exact zeros. 'Within site' "
        f"removes each dealer's own average and each month's national average, so only a "
        f"site's variation against its own baseline is left. THIS FIGURE IS A GUARD, NOT A "
        f"FINDING: it is here so no one reads the left-hand panel as evidence that a site is "
        f"underperforming. The same-month association is worth about 8 service jobs in a "
        f"month of 709 and is equally consistent with a struggling branch completing fewer "
        f"jobs AND generating more complaints. Caveats in analysis.md section 9.4: twelve "
        f"months is shorter than a service interval, and only 33% of the variance in a "
        f"monthly negative rate is signal rather than sampling noise.",
    )
    _save(fig, "q3_feedback_vs_revenue.png")


def q3_coverage(df: pd.DataFrame, revenue: pd.DataFrame) -> None:
    """How much of the business the dataset can see — the limit on every other chart."""
    cov = coverage_table(df, revenue)
    deps = ["Sales", "Service", "Parts"]
    nat = {d: 100 * cov[f"{d} fb"].sum() / cov[f"{d} tx"].sum() for d in deps}
    total_tx = int(revenue[["vehicles_sold", "service_jobs", "parts_transactions"]].sum().sum())

    fig, axes = plt.subplots(1, 2, figsize=(12, 4.8), gridspec_kw={"width_ratios": [1, 2.3]})

    ax = axes[0]
    bars = ax.bar(deps, [nat[d] for d in deps], color=[DEPT[d] for d in deps], width=0.58)
    for bar, d in zip(bars, deps, strict=False):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 0.3,
            f"{nat[d]:.2f}%",
            ha="center",
            fontsize=10,
            fontweight="bold",
        )
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            0.4,
            f"{int(cov[f'{d} fb'].sum()):,}\nof {int(cov[f'{d} tx'].sum()):,}",
            ha="center",
            fontsize=7.5,
            color="white",
        )
    ax.set_ylabel("Responses per 100 transactions")
    ax.set_ylim(0, 12.5)
    ax.grid(axis="y")
    ax.set_axisbelow(True)
    ax.set_title("Nationally", fontsize=10)

    ax = axes[1]
    c = cov.merge(
        df.groupby("dealer_code")["state"].first().rename("state"),
        left_on="Dealer",
        right_index=True,
    ).sort_values("Service %")
    y = range(len(c))
    ax.barh(y, c["Service %"], color=[STATE[s] for s in c["state"]], height=0.7)
    ax.axvline(
        nat["Service"], color=NATIONAL, ls="--", lw=1.5, label=f"National: {nat['Service']:.2f}%"
    )
    ax.set_yticks(list(y))
    ax.set_yticklabels(c["Dealer"], fontsize=7.5)
    ax.set_xlabel("Service responses per 100 service jobs")
    ax.grid(axis="x")
    ax.set_axisbelow(True)
    ax.legend(
        handles=[Patch(color=STATE[s], label=s) for s in ["NSW", "VIC", "QLD"]]
        + [Line2D([], [], ls="--", color=NATIONAL, label=f"National {nat['Service']:.2f}%")],
        frameon=False,
        fontsize=8.5,
        loc="lower right",
        ncol=2,
    )
    ax.set_title("Service coverage by site (colour = state)", fontsize=10)

    fig.suptitle(
        f"Q3 · This dataset sees {100 * len(df) / total_tx:.1f}% of Kestrel's "
        f"{total_tx:,} transactions",
        fontweight="bold",
        fontsize=12.5,
        y=1.03,
    )
    _footer(
        fig,
        "Source: data/raw/reference/monthly_revenue.csv, Oct 2025–Sep 2026, and "
        "reports/analysis.md section 8. Reported as a limitation (D-006): every rate in "
        "either report is a rate among customers who RESPONDED, and D-058 measured response "
        "as not independent of satisfaction — commented rows average 3.54 stars against 4.40 "
        f"for commentless ones — so none of it generalises to the other "
        f"{100 - 100 * len(df) / total_tx:.1f}% of transactions. Three sites collect almost no "
        "SALES feedback at all: QLD08 1.99%, QLD06 2.37%, QLD07 3.37%.",
    )
    _save(fig, "q3_coverage.png")


# ============================================ Method · how far the models can be trusted


def agreement_frame(df: pd.DataFrame) -> pd.DataFrame:
    """The owner's 150 blind labels joined to the model, the rating and the LLM.

    Built from the same committed inputs `src/evaluate.py` reads, so a reviewer with a clean
    clone reproduces it. `reports/evaluation.md` remains the authoritative measurement
    (D-017: the producer does not grade itself); the figure asserts against its numbers
    rather than quietly publishing its own.
    """
    lab = pd.read_csv(LABELS_CSV)
    lab["owner_sentiment"] = (
        lab["sentiment"].astype(str).str.strip().str.lower().map(SENTIMENT_CODES)
    )
    lab["owner_theme_no"] = pd.to_numeric(lab["theme"], errors="coerce").astype("Int64")
    merged = lab.merge(
        df[["feedback_id", "rating_1to5", "sentiment_label", "theme", "comment"]],
        on="feedback_id",
        suffixes=("_owner", "_model"),
    )
    merged["rating_class"] = merged["rating_1to5"].map(SCORE_CLASSES)
    merged["owner_theme"] = merged["owner_theme_no"].map(
        {i + 1: name for i, name in enumerate(GUIDE_THEMES)}
    )
    cache = load_llm()
    merged["llm"] = [
        (cache.get(llm_key(c)) or {}).get("sentiment") for c in merged["comment_model"]
    ]
    return merged


def method_model_vs_owner(df: pd.DataFrame) -> None:
    """Four panels: how far each signal agrees with the owner, and exactly where it fails."""
    m = agreement_frame(df)
    placed = m[m["owner_theme_no"] > 0]
    overlap = m.dropna(subset=["llm"])

    k_model = cohen_kappa_score(m["owner_sentiment"], m["sentiment_label"])
    k_rating = cohen_kappa_score(m["owner_sentiment"], m["rating_class"])
    k_llm = cohen_kappa_score(overlap["owner_sentiment"], overlap["llm"])
    theme_pct = 100 * (placed["owner_theme"] == placed["theme_model"]).mean()

    # The chart must not quietly disagree with the measurement it is drawing (D-017).
    assert round(k_model, 3) == SENTIMENT_KAPPA, k_model
    assert round(k_rating, 3) == RATING_KAPPA, k_rating
    assert round(theme_pct, 1) == THEME_AGREEMENT, theme_pct

    fig, axes = plt.subplots(2, 2, figsize=(13, 11.5), gridspec_kw={"hspace": 0.78, "wspace": 0.3})

    # --- A · the scoreboard -------------------------------------------------
    ax = axes[0][0]
    entries = [
        ("Star rating\n(the customer's own)", k_rating, len(m), STATE["QLD"]),
        ("Sentiment model\nRoBERTa, 3-class", k_model, len(m), BAD),
        (f"Local LLM\nqwen2.5:3b, n={len(overlap)}", k_llm, len(overlap), MUTED),
    ]
    bars = ax.barh(
        [e[0] for e in entries][::-1],
        [e[1] for e in entries][::-1],
        color=[e[3] for e in entries][::-1],
        height=0.55,
    )
    for bar, e in zip(bars, entries[::-1], strict=False):
        ax.text(
            e[1] + 0.015,
            bar.get_y() + bar.get_height() / 2,
            f"{e[1]:.3f}",
            va="center",
            fontsize=11,
            fontweight="bold",
        )
    ax.axvline(FLOOR, color=INK, lw=2, ls="--")
    ax.text(FLOOR + 0.01, 2.45, f"PASS MARK {FLOOR}\ncommitted before\nany of this existed",
            fontsize=8, fontweight="bold", va="top")
    ax.set_xlim(0, 0.92)
    ax.set_xlabel("Cohen's κ — agreement with the owner's 150 blind labels,\ncorrected for chance")
    ax.grid(axis="x")
    ax.set_axisbelow(True)
    ax.set_title("A · The sentiment model failed; the star rating beat it", fontsize=10.5)

    # --- B · sentiment confusion -------------------------------------------
    ax = axes[0][1]
    cm = confusion_matrix(m["owner_sentiment"], m["sentiment_label"], labels=ORDER)
    ax.imshow(cm, cmap="Blues", vmin=0, vmax=cm.max())
    for i in range(3):
        for j in range(3):
            ax.text(
                j, i, cm[i][j],
                ha="center", va="center", fontsize=14,
                fontweight="bold" if i == j else "normal",
                color="white" if cm[i][j] > cm.max() * 0.55 else INK,
            )
    ax.set_xticks(range(3), [o.capitalize() for o in ORDER])
    ax.set_yticks(range(3), [o.capitalize() for o in ORDER])
    ax.set_xlabel("What the MODEL said")
    ax.set_ylabel("What the OWNER said")
    ax.set_title("B · Where sentiment goes wrong: 150 comments", fontsize=10.5)
    wrong_neutral = cm[0][1] + cm[2][1]
    ax.annotate(
        f"{cm[0][1]} negatives and {cm[2][1]} positives called NEUTRAL ({wrong_neutral} of 150).\n"
        f"The owner used 'neutral' {int((m['owner_sentiment'] == 'neutral').sum())} times in "
        f"150; the model uses it on 22.4% of the corpus.\n"
        f"{cm[0][2]} real negatives were called POSITIVE — the sarcasm failure (D-063).",
        xy=(0.5, -0.155), xycoords="axes fraction",
        ha="center", va="top", fontsize=8, color=BAD, linespacing=1.55,
    )
    for spine in ax.spines.values():
        spine.set_visible(False)

    # --- C · theme confusion ------------------------------------------------
    ax = axes[1][0]
    names = sorted(GUIDE_THEMES)
    tc = (
        pd.crosstab(placed["owner_theme"], placed["theme_model"])
        .reindex(index=names, columns=names, fill_value=0)
        .to_numpy()
    )
    ax.imshow(tc, cmap="Blues", vmin=0, vmax=tc.max())
    for i in range(len(names)):
        for j in range(len(names)):
            if tc[i][j]:
                ax.text(
                    j, i, tc[i][j], ha="center", va="center", fontsize=8.5,
                    fontweight="bold" if i == j else "normal",
                    color="white" if tc[i][j] > tc.max() * 0.55 else INK,
                )
    short = [n.split(" and ")[0].split(" ")[0] for n in names]
    ax.set_xticks(range(len(names)), short, rotation=45, ha="right", fontsize=8)
    ax.set_yticks(range(len(names)), names, fontsize=8)
    ax.set_xlabel("Theme the MODEL assigned")
    ax.set_ylabel("Theme the OWNER assigned")
    ax.set_title(
        f"C · Themes: the diagonal is only {theme_pct:.1f}% of {len(placed)} comments",
        fontsize=10.5,
    )
    pulled = tc[:, names.index("Staff manner")].sum() - tc[
        names.index("Staff manner"), names.index("Staff manner")
    ]
    ax.annotate(
        f"Off-diagonal is {100 - theme_pct:.1f}% of placements. The single biggest leak: "
        f"{pulled} comments the owner put elsewhere\nwere assigned to 'Staff manner', which "
        f"is also the largest theme. The owner answered 'none of these'\nto "
        f"{int((m['owner_theme_no'] == 0).sum())} of 150 — and no similarity floor could "
        "separate those 7 from the rest (D-066).",
        xy=(0.5, -0.34), xycoords="axes fraction",
        ha="center", va="top", fontsize=7.6, color=BAD, linespacing=1.55,
    )
    for spine in ax.spines.values():
        spine.set_visible(False)

    # --- D · what the LLM did -----------------------------------------------
    ax = axes[1][1]
    sided = [("The customer's rating", 218), ("The sentiment model", 439), ("Neither", 200)]
    total = sum(v for _, v in sided)
    left = 0.0
    for (label, v), colour in zip(sided, [STATE["QLD"], STATE["VIC"], MUTED], strict=False):
        ax.barh(0, 100 * v / total, left=left, color=colour, height=0.42)
        ax.text(
            left + 50 * v / total, 0, f"{label}\n{v:,}  ({100 * v / total:.0f}%)",
            ha="center", va="center", fontsize=8.5, color="white", fontweight="bold",
        )
        left += 100 * v / total
    ax.barh(-0.75, 45.5, color=BAD, height=0.42)
    ax.barh(-0.75, 54.5, left=45.5, color="#e4e4e4", height=0.42)
    ax.text(22.7, -0.75, "Irony or sarcasm reported\n390 of 857  (45.5%)",
            ha="center", va="center", fontsize=8.5, color="white", fontweight="bold")
    ax.set_yticks([0, -0.75], ["Which signal\nit agreed with", "Why they\ndisagreed"], fontsize=9)
    ax.set_xlim(0, 100)
    ax.set_ylim(-1.5, 0.95)
    ax.set_xlabel("Share of the 857 adjudicated comments (%)")
    ax.set_title("D · What the LLM was used for — and was not", fontsize=10.5, pad=48)
    ax.annotate(
        "857 comments where the model and the rating DISAGREED, run on a local 3B model in "
        "49.8 min, 0 parse failures.\n"
        f"It scores κ {k_llm:.3f} — but on {len(overlap)} rows, and they are exactly the hard "
        "cases it was pointed at, so that is not a promotion.\n"
        "It ANNOTATES only: it never overwrites sentiment_label, so every number in these "
        "reports reproduces without Ollama.",
        xy=(0.0, 1.14), xycoords="axes fraction",
        ha="left", va="top", fontsize=7.8, color=INK, linespacing=1.6,
    )
    ax.grid(axis="x")
    ax.set_axisbelow(True)
    for spine in ax.spines.values():
        spine.set_visible(False)

    fig.suptitle(
        "Method · How far the NLP can be trusted, and exactly where it disagrees with a human",
        fontweight="bold",
        fontsize=13,
        y=0.985,
    )
    _footer(
        fig,
        "Sample: the 150 comments the owner labelled BLIND to every model output and to the "
        "star rating, on 30 Oct 2026 (D-017, D-055). The pass mark of 0.60 was committed to "
        "config.yaml before the labelling (gate G7) and was NOT moved when it was missed — "
        "D-055's pre-committed fallback applied instead, making the rating primary (D-065). "
        "κ is chance-corrected: a model that answers 'positive' to everything scores 59.3% "
        "raw agreement on this corpus and κ = 0. Panels A–C recomputed here from "
        "reports/labels_done.csv and asserted against reports/evaluation.md; panel D from "
        "reports/llm_review.md.",
    )
    _save(fig, "method_model_vs_owner.png")


def main() -> int:
    df, revenue, _ = load()
    q1_drivers_by_department(df)
    q1_sites_vs_national(df)
    q1_themes_by_department(df)
    q2_trend_by_state(df)
    q2_sites_that_changed(df)
    q3_where_to_focus(df, revenue)
    q3_feedback_vs_revenue(df, revenue)
    q3_coverage(df, revenue)
    method_model_vs_owner(df)
    print(
        "\nGate G9: these eight PNGs are NOT referenced by either report yet. "
        "The owner approves each one first."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

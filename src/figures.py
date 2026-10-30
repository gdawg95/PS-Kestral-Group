"""Wave 5: the charts for both reports.

Brief: `agents/briefs/w5_analysis.md` step 4. **Gate G9 — the owner approves every chart
before it enters a report**, so this module writes PNGs to `reports/figures/` and nothing
else. Neither `reports/analysis.md` nor `reports/business_report.md` embeds an image until
that approval exists; both carry a figure index instead, and the markdown `![...]` lines go
in afterwards.

Every number plotted here is computed by `src/analyse.py` and imported, never recalculated.
A chart and a table that disagree is the failure mode this avoids: there is one definition of
the negative rate, one trend series and one coverage figure in this project, and they live in
`analyse.py`.

What is deliberately NOT drawn:

  * No theme chart with the bars sorted by rate. D-065 permits a theme's negative rate and
    forbids a ranking, and a sorted bar chart IS a ranking whatever the caption says. The
    theme chart is alphabetical, with the 44.1% agreement printed on the figure itself so
    the caveat cannot be separated from the picture.
  * No dollar chart. D-025 is unset and `reports/benchmarks.md` is unreviewed (section 10 of
    the analysis).
  * No trend line per dealership. The site-level rule finds 16 falls and 17 rises (D-052 at
    its calibrated grain); twenty-four noisy lines would invite a reader to see a pattern
    the data does not support.

Usage:
    python -m src.figures
"""

from __future__ import annotations

import matplotlib

matplotlib.use("Agg")  # no display on the laptop or in a reviewer's clean clone

import matplotlib.pyplot as plt
import pandas as pd

from src.analyse import (
    CLOSED_SITE,
    H1,
    H2,
    MIN_CHANGE,
    MIN_MONTH_N,
    ROOT,
    THEME_AGREEMENT,
    coverage_table,
    half_test,
    load,
    month_pairs,
    national_series,
    rate_block,
    wilson_ci,
)

FIG_DIR = ROOT / "reports" / "figures"

# One palette for both reports, colour-blind safe (Okabe-Ito), so a figure in the business
# report and the same figure in the technical report are visibly the same figure.
INK = "#1b1b1b"
GRID = "#d9d9d9"
BLUE = "#0072b2"
ORANGE = "#d55e00"
GREY = "#999999"
GREEN = "#009e73"

plt.rcParams.update(
    {
        "figure.dpi": 150,
        "savefig.dpi": 150,
        "savefig.bbox": "tight",
        "font.size": 9,
        "axes.titlesize": 11,
        "axes.titleweight": "bold",
        "axes.labelcolor": INK,
        "axes.edgecolor": GREY,
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
    """Every figure states its denominator on its face. A chart gets separated from its
    caption the moment someone pastes it into a slide (D-058)."""
    fig.text(0.0, -0.04, text, fontsize=7, color="#555555", ha="left", va="top", wrap=True)


def _save(fig: plt.Figure, name: str) -> None:
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    path = FIG_DIR / name
    fig.savefig(path)
    plt.close(fig)
    print(f"wrote {path.relative_to(ROOT)}")


# --------------------------------------------------------------------------- figures


def fig_trend_national(df: pd.DataFrame) -> None:
    """The §2 trend. Two panels: the rating the claim is made on, and the negative rate the
    business report quotes. Both with and without the closed site (D-005)."""
    a = national_series(df)
    b = national_series(df[df["dealer_code"] != CLOSED_SITE])
    h = half_test(df)
    x = range(len(a))
    fig, axes = plt.subplots(2, 1, figsize=(8, 6), sharex=True)

    ax = axes[0]
    ax.plot(x, a["mean rating"], "-o", color=BLUE, ms=4, lw=1.8, label="All 24 dealerships")
    ax.plot(
        x,
        b["mean rating"],
        "--",
        color=ORANGE,
        lw=1.4,
        label=f"Excluding {CLOSED_SITE} (closed 31 Mar 2026)",
    )
    ax.hlines(h["mean_h1"], -0.4, 5.4, color=GREEN, lw=2, label="Half-year mean")
    ax.hlines(h["mean_h2"], 5.6, 11.4, color=GREEN, lw=2)
    ax.annotate(
        f"{h['mean_h1']:.2f}  →  {h['mean_h2']:.2f}\n"
        f"{h['delta']:+.3f} stars, p = {h['welch_p']:.1g}",
        xy=(8.3, h["mean_h2"]),
        xytext=(7.4, 3.38),
        fontsize=8,
        color=GREEN,
        fontweight="bold",
    )
    ax.axvline(5.5, color=GREY, lw=0.8, ls=":")
    ax.set_ylabel("Mean rating (1–5)")
    ax.set_title("Kestrel's rating fell over the year, and the fall is not the closed site")
    ax.set_ylim(3.3, 4.05)
    ax.grid(axis="y")
    ax.legend(frameon=False, fontsize=8, loc="lower left")

    ax = axes[1]
    ax.bar(x, a["negative rate %"], color=BLUE, width=0.62)
    ax.plot(x, b["negative rate %"], "o", color=ORANGE, ms=4, label=f"Excluding {CLOSED_SITE}")
    ax.axhline(h["neg_h1"], xmin=0.02, xmax=0.49, color=GREEN, lw=2)
    ax.axhline(h["neg_h2"], xmin=0.51, xmax=0.98, color=GREEN, lw=2)
    ax.axvline(5.5, color=GREY, lw=0.8, ls=":")
    ax.annotate(
        f"{h['neg_h1']:.1f}%  →  {h['neg_h2']:.1f}%   ({h['neg_delta']:+.1f} pts)",
        xy=(5.9, 31.2),
        fontsize=8,
        color=GREEN,
        fontweight="bold",
    )
    ax.set_ylabel("Negative rate (%)")
    ax.set_xticks(list(x))
    ax.set_xticklabels([m[2:] for m in a["month"]], rotation=45, ha="right")
    ax.set_ylim(0, 34)
    ax.grid(axis="y")
    ax.legend(frameon=False, fontsize=8, loc="upper left")
    ax.set_title(
        f"Negative = rating 1–2, over ALL rows in the month ({len(df):,} rows in total)",
        fontsize=9,
        fontweight="normal",
    )

    _footer(
        fig,
        f"Denominator: all {len(df):,} rows (D-058) — not the {int(df['has_comment'].sum()):,} "
        f"commented ones. Rating is the primary signal (D-065). "
        f"H1 = {H1[0]}..{H1[1]}, H2 = {H2[0]}..{H2[1]}. Source: reports/analysis.md section 7.",
    )
    _save(fig, "trend_national.png")


def fig_department_halves(df: pd.DataFrame) -> None:
    """Where the decline sits. The whole recommendation rests on this chart."""
    rows = []
    for dep in ["Service", "Sales", "Parts"]:
        sub = df[df["department"] == dep]
        for half in ["H1", "H2"]:
            s = sub[sub["half"] == half]
            rows.append(
                {
                    "dep": dep,
                    "half": half,
                    "rate": 100 * s["negative_by_rating"].mean(),
                    "n": len(s),
                }
            )
    t = pd.DataFrame(rows)
    fig, ax = plt.subplots(figsize=(7, 4))
    width = 0.36
    for i, (half, colour) in enumerate([("H1", GREY), ("H2", ORANGE)]):
        s = t[t["half"] == half]
        pos = [j + (i - 0.5) * width for j in range(3)]
        bars = ax.bar(
            pos,
            s["rate"],
            width,
            color=colour,
            label=f"{half}  ({'Oct 2025 – Mar 2026' if half == 'H1' else 'Apr – Sep 2026'})",
        )
        for bar, (_, r) in zip(bars, s.iterrows(), strict=False):
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height() + 0.5,
                f"{r['rate']:.1f}%\nn={r['n']:,}",
                ha="center",
                fontsize=7.5,
            )
    ax.set_xticks(range(3))
    ax.set_xticklabels(
        [
            f"{dep}\n{int(t[t['dep'] == dep]['n'].sum()):,} rows"
            for dep in ["Service", "Sales", "Parts"]
        ]
    )
    ax.set_ylabel("Negative rate (%)")
    ax.set_ylim(0, 38)
    ax.grid(axis="y")
    ax.legend(frameon=False, fontsize=8)
    ax.set_title("The year's decline is in Service, which is also two-thirds of the volume")
    _footer(
        fig,
        f"Denominator: all {len(df):,} rows, negative = rating 1–2 (D-058, D-065). "
        "Service -0.204 stars p=1.8e-06; Sales -0.167 p=0.0043; Parts -0.031 p=0.75. "
        "Department is a hand-mapped field (D-050), not model output, so these three are "
        "comparable. Source: reports/analysis.md sections 2 and 7.2.",
    )
    _save(fig, "negative_by_department.png")


def fig_dealership(df: pd.DataFrame) -> None:
    """Sites with Wilson intervals, because sorting 24 point estimates invites a comparison
    the thin sites cannot support."""
    t = rate_block(df, "dealer_code", "Dealer").sort_values("rate % of all rows")
    los, his = [], []
    for _, r in t.iterrows():
        lo, hi = wilson_ci(int(r["negative by rating"]), int(r["rows (all)"]))
        los.append(r["rate % of all rows"] - lo)
        his.append(hi - r["rate % of all rows"])
    group = 100 * df["negative_by_rating"].mean()
    fig, ax = plt.subplots(figsize=(7.5, 7))
    y = range(len(t))
    colours = [ORANGE if v >= group else BLUE for v in t["rate % of all rows"]]
    ax.barh(y, t["rate % of all rows"], color=colours, height=0.68)
    ax.errorbar(
        t["rate % of all rows"],
        y,
        xerr=[los, his],
        fmt="none",
        ecolor=INK,
        elinewidth=1,
        capsize=2.5,
    )
    ax.axvline(group, color=GREEN, lw=1.6, ls="--", label=f"Group: {group:.1f}%")
    ax.set_yticks(list(y))
    ax.set_yticklabels([f"{r.Dealer}  (n={int(r._2):,})" for r in t.itertuples()], fontsize=8)
    ax.set_xlabel("Negative rate (%), with 95% Wilson interval")
    ax.set_xlim(0, 40)
    ax.grid(axis="x")
    ax.legend(frameon=False, fontsize=8, loc="lower right")
    ax.set_title("Negative rate by dealership — the intervals matter more than the order")
    _footer(
        fig,
        f"Denominator: all {len(df):,} rows, negative = rating 1–2 (D-058). Dealer code is "
        "the owner's hand-approved file map (D-034). Sites whose intervals overlap are not "
        "separated by this data: QLD05 (n=49) and VIC09 (n=52, closed) are the extreme "
        "cases. Source: reports/analysis.md section 3.",
    )
    _save(fig, "negative_by_dealership.png")


def fig_themes(df: pd.DataFrame) -> None:
    """Alphabetical, and the agreement figure is printed ON the chart (D-065, D-066)."""
    cmt = df[df["has_comment"]]
    rows = []
    for theme, sub in cmt.groupby("theme", observed=True):
        rows.append(
            {
                "theme": theme,
                "n": len(sub),
                "rate": 100 * sub["negative_by_rating"].mean(),
                "sent": 100 * (sub["sentiment_label"] == "negative").mean(),
            }
        )
    t = pd.DataFrame(rows).sort_values("theme", ascending=False)  # alphabetical top-to-bottom
    fig, ax = plt.subplots(figsize=(8.5, 5.2))
    y = range(len(t))
    ax.barh(y, t["rate"], color=BLUE, height=0.56, label="Negative by rating (primary, D-065)")
    ax.plot(t["sent"], y, "D", color=ORANGE, ms=5, label="Sentiment-negative (method comparison)")
    overall = 100 * cmt["negative_by_rating"].mean()
    ax.axvline(overall, color=GREEN, ls="--", lw=1.5, label=f"All commented rows: {overall:.1f}%")
    ax.set_yticks(list(y))
    ax.set_yticklabels([f"{r.theme}  (n={r.n:,})" for r in t.itertuples()], fontsize=8)
    ax.set_xlabel("Negative rate within the theme (%)")
    ax.set_xlim(0, 58)
    ax.grid(axis="x")
    ax.legend(frameon=True, framealpha=0.95, edgecolor="white", fontsize=8,
              loc="center right", bbox_to_anchor=(1.0, 0.38))
    ax.set_title("Negative rate by theme — alphabetical, NOT a ranking", pad=22)
    ax.text(
        0.5,
        1.015,
        f"Model and owner agreed on a comment's theme {THEME_AGREEMENT}% of the time",
        transform=ax.transAxes,
        ha="center",
        fontsize=8.5,
        color=ORANGE,
        fontweight="bold",
    )
    _footer(
        fig,
        f"Denominator: the {len(cmt):,} commented rows only — not all {len(df):,} (D-058). "
        f"Bars are alphabetical by design: at {THEME_AGREEMENT}% model-owner theme agreement "
        "(D-065) a rate is reportable and a ranking is not, and a sorted bar chart is a "
        "ranking. Sentiment kappa 0.403 against a 0.60 floor. Source: analysis.md section 4.",
    )
    _save(fig, "theme_negative_rates.png")


def fig_coverage(df: pd.DataFrame, revenue: pd.DataFrame) -> None:
    """How little of the business this dataset sees (D-006)."""
    cov = coverage_table(df, revenue)
    deps = ["Sales", "Service", "Parts"]
    nat = {d: 100 * cov[f"{d} fb"].sum() / cov[f"{d} tx"].sum() for d in deps}
    fig, axes = plt.subplots(1, 2, figsize=(10, 4.2), gridspec_kw={"width_ratios": [1.2, 2.4]})

    ax = axes[0]
    bars = ax.bar(deps, [nat[d] for d in deps], color=[GREY, ORANGE, GREY], width=0.6)
    for bar, d in zip(bars, deps, strict=False):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 0.2,
            f"{nat[d]:.2f}%\n{int(cov[f'{d} fb'].sum()):,} / {int(cov[f'{d} tx'].sum()):,}",
            ha="center",
            fontsize=8,
        )
    ax.set_ylabel("Feedback per transaction (%)")
    ax.set_ylim(0, 13)
    ax.grid(axis="y")
    ax.set_title("Nationally", fontsize=10)

    ax = axes[1]
    c = cov.sort_values("Service %")
    y = range(len(c))
    ax.barh(y, c["Service %"], color=BLUE, height=0.7)
    ax.axvline(nat["Service"], color=GREEN, ls="--", lw=1.5, label=f"Group: {nat['Service']:.2f}%")
    ax.set_yticks(list(y))
    ax.set_yticklabels(c["Dealer"], fontsize=7.5)
    ax.set_xlabel("Service feedback per service job (%)")
    ax.grid(axis="x")
    ax.legend(frameon=False, fontsize=8, loc="lower right")
    ax.set_title("Service coverage by dealership", fontsize=10)

    fig.suptitle(
        f"{len(df):,} pieces of feedback against "
        f"{int(revenue[['vehicles_sold', 'service_jobs', 'parts_transactions']].sum().sum()):,} "
        "transactions — 2.57%",
        fontweight="bold",
        fontsize=11,
    )
    _footer(
        fig,
        "Source: data/raw/reference/monthly_revenue.csv, Oct 2025 - Sep 2026, and "
        "analysis.md section 8. Reported as a limitation (D-006): every rate in either "
        "report is a rate among the customers who responded, and D-058 measured response "
        "as NOT independent of satisfaction, so these rates do not generalise to the other "
        "97.4% of transactions.",
    )
    _save(fig, "coverage.png")


def fig_site_move(df: pd.DataFrame) -> None:
    """The largest single move in the data, and why one site-month is not the trend."""
    pairs = month_pairs(df)
    flagged = pairs[pairs["clears D-052"]].sort_values("change")
    dealer = flagged.iloc[0]["Dealer"]
    sub = df[df["dealer_code"] == dealer]
    g = (
        sub.groupby("month", observed=True)
        .agg(n=("rating_1to5", "size"), mean=("rating_1to5", "mean"))
        .reset_index()
    )
    fig, ax = plt.subplots(figsize=(8, 4.2))
    x = range(len(g))
    ax.plot(x, g["mean"], "-o", color=BLUE, ms=5, lw=1.8)
    # Response counts on one baseline row rather than beside each marker: at this site the
    # line crosses itself often enough that per-point labels collide with it.
    base = g["mean"].min() - 0.22
    for i, r in g.iterrows():
        ax.text(i, base, f"n={int(r['n'])}", ha="center", fontsize=7, color=GREY)
    ax.set_ylim(base - 0.12, g["mean"].max() + 0.18)
    lo = g["mean"].min()
    k = int(g["mean"].idxmin())
    ax.annotate(
        f"{flagged.iloc[0]['change']:+.2f} stars\non {flagged.iloc[0]['n prev']} → "
        f"{flagged.iloc[0]['n this']} responses",
        xy=(k, lo),
        xytext=(k - 2.6, lo + 0.45),
        fontsize=8,
        fontweight="bold",
        color=ORANGE,
        arrowprops={"arrowstyle": "->", "color": ORANGE, "lw": 1.2},
    )
    group = df.groupby("month", observed=True)["rating_1to5"].mean().to_numpy()
    ax.plot(x, group, ":", color=GREY, lw=1.6, label="Group mean, all 24 sites")
    ax.set_xticks(list(x))
    ax.set_xticklabels([str(m)[2:] for m in g["month"]], rotation=45, ha="right")
    ax.set_ylabel("Mean rating (1–5)")
    ax.grid(axis="y")
    ax.legend(frameon=False, fontsize=8, loc="lower right")
    ax.set_title(f"{dealer}: the largest single move in the data — and it recovered")
    _footer(
        fig,
        f"D-052's committed rule, set before any result (gate G7): both months need "
        f">= {MIN_MONTH_N} responses and the change must reach {MIN_CHANGE} stars. This move "
        f"is nearly three times the threshold; it reverses the next month, which is why the "
        f"trend claim in analysis.md section 7.2 is made at group level and not here. "
        f"Denominator: all {len(sub):,} rows at this site.",
    )
    _save(fig, "largest_site_move.png")


def main() -> int:
    df, revenue, _ = load()
    fig_trend_national(df)
    fig_department_halves(df)
    fig_dealership(df)
    fig_themes(df)
    fig_coverage(df, revenue)
    fig_site_move(df)
    print(
        "\nGate G9: these six PNGs are NOT referenced by either report yet. "
        "The owner approves each one first."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

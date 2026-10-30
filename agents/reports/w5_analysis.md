# Report: w5_analysis

**Brief:** `agents/briefs/w5_analysis.md` · **Branch:** `w1-wrapup` · **Date:** 30 Oct 2026,
before the 15:00 code freeze · **Environment:** laptop repository, project virtual
environment (D-013 revision 2).

---

## What I did

All eight steps in the brief ran except step 6 (the value model), which was cut under its own
condition. The three §2 non-negotiables Wave 5 owns are delivered.

| Step | Output | State |
|---|---|---|
| 1. Drivers | `src/analyse.py` → `reports/analysis.md` §§2–6 | Done |
| 2. Trend | `reports/analysis.md` §7, with and without VIC09 | Done |
| 3. Coverage | `reports/analysis.md` §8 | Done |
| 4. Charts | `src/figures.py` → six PNGs in `reports/figures/` | Done, **unapproved (G9)** |
| 5. Business report | `reports/business_report.md` | **Draft**, recommendations to be rewritten |
| 6. Value model | — | **Cut**: D-025 unset, `benchmarks.md` unreviewed |
| 7. Technical report | `README.md` §§10–11 new, §§8, 13, 14 updated | Done |
| 8. Independent verifier | — | **Not done.** See "Unresolved" |
| Pilot (G1) | `python -m src.analyse --pilot` → `reports/pilot_drivers.md` | Ran first, on VIC09 / QLD06 / VIC01 |
| (not in brief) | `tests/test_analyse.py`, 16 guard tests | Added — see below |
| (not in brief) | `reports/run_manifest.json` | Done (it was in the brief's outputs) |

**The trend, which is the protected output.** The group's mean rating fell from **3.842**
(Oct 2025 – Mar 2026) to **3.671** (Apr – Sep 2026) and the negative rate rose **19.9% →
24.9%**, over all 7,150 rows. The committed threshold is cited and then applied at the right
grain: D-052's 0.5 stars is calibrated for a dealership-month at n = 20 (±0.46 noise); the
same formula at n = 3,457 against 3,693 gives ±0.034, and the observed 0.171 fall is five
times that. Welch p = 4.9e-07, Mann–Whitney p = 1.6e-05, χ² p = 4e-07. Removing the closed
site moves the fall to −0.169.

**The recommendation**, traceable to §9 of `analysis.md`: focus on Service — 68.6% of the
feedback, 71.9% of the transactions behind it, the worst negative rate on either denominator
(27.2% of all its rows), and where the year's decline sits (24.0% → 30.2%, p = 1.8e-06).
Nothing in that chain uses the sentiment model or a theme ranking.

---

## Assumptions

Three of the brief's four owner questions were answered by the handoff or by a decision
already recorded. I proceeded on them rather than blocking with 90 minutes to the freeze.
**Each is reversible and none changes a number that has been published.**

1. **Q1 — the similarity floor is retired.** D-066 is written and the handoff lists it as
   applying, so I treated it as settled. `theme` is reported for every commented row with
   the 44.1% agreement attached.
2. **Q2 — the value model is cut.** D-025 is still open in `DECISIONS.md` and
   `reports/benchmarks.md` is unreviewed, so the brief's own condition for cutting it is met.
   Both reports state the gap explicitly and `business_report.md` §5 names the three
   assumptions that would unblock an estimate. **If D-025 is set today, this is an afternoon's
   work on top of what exists and nothing already written needs changing.**
3. **Q3 — the business report leads with the rating**, per D-065. Sentiment appears once, as
   a method comparison with κ 0.403 beside the rating's 0.460.

Four more, all stated in the reports themselves:

4. **The half-year split is fixed at the midpoint of the twelve months**, which is also the
   month VIC09 closed. It was not searched for. A change point chosen to maximise the gap it
   then reports would not be evidence of anything, and this is the one methodological choice
   in the trend that a sceptical reviewer should push on.
5. **Department and dealer code are treated as reliable and comparable**; themes are not.
   Both came from hand-approved mappings (D-034, D-050) rather than from a model.
6. **Parts transactions are included in the coverage denominator.** The brief quoted
   200,249 service jobs and 16,011 vehicles sold; `monthly_revenue.csv` also has 62,437 parts
   transactions, so the total is 278,697 and overall coverage is 2.57%, not the 3.3% the
   service-plus-sales figures alone would give.
7. **No seasonality model.** Twelve months cannot separate a seasonal cycle from a decline.
   The fall is reported as a fall, with that limitation stated.

---

## Unresolved, and what I did not do

1. **Gate G9 is open.** Six charts exist and **neither report embeds any of them.** Both
   carry a figure index saying where each belongs. This is the only gate still blocking
   between here and a finished report, and it is a five-minute read.
2. **Checkpoint 5 is open on two counts:** 2–3 headline numbers recomputed by hand, and the
   recommendations rewritten in the owner's voice. `business_report.md` is marked DRAFT at
   the top and at section 4 for exactly that.
3. **The independent verifier did not run (step 8, D-017).** The brief said not to cut it if
   there was any way to keep it, and the freeze arrived first. This is now the single largest
   outstanding item in the project, and it compounds: `reports/evaluation.md` already records
   its own D-017 exception, so **two of the three Wave 4–5 measurement artefacts were written
   by the agent that produced what they measure.** Reproducible is not independent. A fresh
   agent with a clean clone, `make all`, and `reports/analysis.md` beside the code is worth
   more than anything else that could be added now.
4. **`DECISIONS.md` has no Wave 5 entry.** The brief says it is the orchestrator's file and I
   did not write to it. Three things in this wave are decisions in substance and should be
   recorded as such: the fixed half-year boundary (assumption 4), the choice to publish the
   group trend rather than a site-level one, and the decision not to extrapolate the negative
   rate onto non-responders (below).
5. **`tests/test_llm_review.py` still does not exist**, carried over from Wave 4.
6. **`config.yaml` unchanged** (gate G7), including `theme_bar: TBD`.

---

## One number I computed and deliberately did not publish

305 more negative service responses in H2 than H1's rate would have produced, at a 2.45%
service response rate, extrapolates to roughly **12,445 service jobs**. It is arithmetic and
it would have been the most quotable figure in the business report.

It is not published, and the arithmetic is shown in `analysis.md` §9 followed by the reason:
D-058 measured response as **not** independent of satisfaction — commented rows average 3.54
stars against 4.40 for commentless ones — so projecting a responder rate onto all 200,249
service jobs overstates it by an unknown amount. An unknown amount is not an error bar. The
defensible version of the volume argument is that Service is where both the feedback and the
business sit, and that is what both reports use.

---

## Errors found and fixed in this wave

**1. The committed trend threshold was being applied to a rounded number.** `month_pairs`
rounded each change to two decimals for display and then tested the *rounded* value against
`min_change_1to5: 0.5`, so a 0.496-star move at VIC04 cleared a 0.5-star rule. The flag count
came out at **34 of 256 at 17 sites** against the 33 of 257 at 16 sites that
`reports/trend_evidence.md` committed, and my first draft of §7.1 explained that gap with the
wrong cause — the nine rows D-031 drops at validation.

Caught by not accepting the discrepancy: I recomputed the old script's method on
`data/interim/consolidated.parquet` and the new method on the classified dataset, which
showed 33 flags at the same 16 sites both ways. The threshold now tests the unrounded value,
and the only remaining difference is the pair count: `scripts/trend_evidence.py` paired each
month with the previous *present* month, so Penrith's May 2026 paired with its July across
the June gap D-029 excluded. `src/analyse.py` requires adjacency. 257 − 1 = 256.

This is worth recording beyond the fix: **a threshold committed in advance under gate G7 can
still be loosened by accident, by a decision about how to display a number.** The guard is
now a test.

**2. `month_pairs` lost its columns on an empty result** — a single-site slice with one month
returned a `DataFrame` with no columns and the next line raised `KeyError`. Found by the test
for non-adjacent months.

**3. Smaller things found by reading the generated output rather than the code:** rates
rounded to 23.1 printed as "23.10"; booleans printed as 1/0; a sentence naming "the same five
thin sites" listed four, because it filtered on row count rather than using D-052's named
five; the thin-site sentence said "4 to 5 comments per theme" of two sites that hold 11.8 and
4.6.

---

## Rows in / out per stage

Nothing in this wave adds, drops or modifies a row. It is read-only over the classified
dataset.

| Stage | Rows |
|---|---:|
| `data/interim/consolidated.parquet` (Wave 2) | 7,159 |
| `data/clean/feedback.parquet` (Wave 3, after validation) | 7,150 |
| `data/clean/feedback_classified.parquet` (Wave 4) | 7,150 |
| **Read by `src/analyse.py`** | **7,150** |
| — of which carry a comment, sentiment and theme | 5,353 |
| — of which carry null sentiment and theme by design (D-057) | 1,797 |
| **Rows written** | **0** |

Every table's own denominator is stated in its caption, and the two totals above are the only
two denominators used anywhere in either report. `reports/run_manifest.json` records the
sha256 of each input and the row count at each stage.

**Files written:** `src/analyse.py`, `src/figures.py`, `tests/test_analyse.py`,
`reports/analysis.md`, `reports/business_report.md`, `reports/pilot_drivers.md`,
`reports/run_manifest.json`, `reports/figures/*.png` (6), `README.md` (sections 8, 10, 11,
12, 13, 14, 15), `agents/reports/w5_analysis.md`.

**Files deliberately not touched:** `config.yaml` (G7), `DECISIONS.md` and `AI_LOG.md` (the
orchestrator's), `src/export.py` and `tests/test_export.py` (another session's — D-064,
D-067), every Wave 1–4 pipeline module (G3), `mappings/`, `data/`, and `Makefile`, whose
`analyse` and `figures` targets already existed and already work.

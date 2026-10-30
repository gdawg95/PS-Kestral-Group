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
| 4. Charts | `src/figures.py` → eight PNGs in `reports/figures/` | Done, **unapproved (G9)** |
| 5. Business report | `reports/business_report.md` | **Draft**, recommendations to be rewritten |
| 6. Value model | — | **Cut**: D-025 unset, `benchmarks.md` unreviewed |
| 7. Technical report | `README.md` §§10–11 new, §§8, 13, 14 updated | Done |
| 8. Independent verifier | — | **Not done.** See "Unresolved" |
| Pilot (G1) | `python -m src.analyse --pilot` → `reports/pilot_drivers.md` | Ran first, on VIC09 / QLD06 / VIC01 |
| (not in brief) | `tests/test_analyse.py`, 16 guard tests | Added — see below |
| (not in brief) | `reports/run_manifest.json` | Done (it was in the brief's outputs) |

**The trend, which is the protected output.** *(Revised after the owner's review — see
"The chart rebuild" below. The group-level claim stands; the state split is what makes it
actionable.)* The group's mean rating fell from **3.842**
(Oct 2025 – Mar 2026) to **3.671** (Apr – Sep 2026) and the negative rate rose **19.9% →
24.9%**, over all 7,150 rows. The committed threshold is cited and then applied at the right
grain: D-052's 0.5 stars is calibrated for a dealership-month at n = 20 (±0.46 noise); the
same formula at n = 3,457 against 3,693 gives ±0.034, and the observed 0.171 fall is five
times that. Welch p = 4.9e-07, Mann–Whitney p = 1.6e-05, χ² p = 4e-07. Removing the closed
site moves the fall to −0.169.

**The decline is NSW, not the group.** Splitting the trend by state — asked for at review —
changed what the recommendation says:

| | Rating change | Negative rate | Welch p |
|---|---:|---:|---:|
| **NSW** | **−0.330** | 18.1% → **26.4%** | **7.9e-08** |
| VIC | −0.166 | 20.5% → 25.1% | 0.0028 |
| **QLD** | **−0.015** | 21.0% → 23.3% | **0.80 — no change at all** |

Inside NSW it is Service (**+10.3 points**, p = 3.1e-07) and Sales (+8.5); NSW Parts improved.
Per-site, with a Holm correction across all 23 tests, **three sites moved by more than chance
— Parramatta −0.75, Dandenong −0.72, Liverpool −0.58 — and every one is a fall.** Uncorrected,
five clear p < 0.05 and about one of those is noise.

**The recommendation**, traceable to §9 of `analysis.md`, now separates two things that were
conflated: the **standing** problem is Service everywhere (68.6% of the feedback, 71.9% of the
transactions, 27.2% negative), and the **new** problem is NSW Service, six months old, with
Parramatta and Liverpool named on their own evidence. Nothing in that chain uses the sentiment
model or a theme ranking.

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

1. **Gate G9 is closed.** The owner approved all nine charts on 30 Oct 2026. They are
   embedded in `reports/business_report.md` and three of them in `README.md`. Until that
   approval both reports carried a figure index instead of the images, which is the
   evidence the gate was observed rather than asserted.
2. **Checkpoint 5 is half closed.** The owner recomputed the headline numbers on 30 Oct
   (`reports/checkpoint5_recompute.md`): 14 figures, including all three the recommendation
   rests on, recomputed from `export/feedback_clean.csv` by a route that imports nothing
   from `src/`. All 14 match. **Still open:** the recommendations rewritten in the owner's
   voice — `business_report.md` is marked DRAFT at the top and at section 4 for that.
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

156 more negative service responses in H2 than H1's rate would have produced, at a 2.45%
service response rate, extrapolates to roughly **6,341 service jobs**. It is arithmetic and
it would have been the most quotable figure in the business report.

It is not published, and the arithmetic is shown in `analysis.md` §9 followed by the reason:
D-058 measured response as **not** independent of satisfaction — commented rows average 3.54
stars against 4.40 for commentless ones — so projecting a responder rate onto all 200,249
service jobs overstates it by an unknown amount. An unknown amount is not an error bar. The
defensible version of the volume argument is that Service is where both the feedback and the
business sit, and that is what both reports use.

---

## The chart rebuild

The first chart set was rejected at review as hard to read and not aimed at the business
questions. It had been organised around the *decisions that constrained the analysis* rather
than around what the challenge asks, which is a real failure of framing and not a styling
complaint. Rebuilt as eight figures named `q1_*`, `q2_*`, `q3_*` and one `method_*`, so a
chart that cannot say which question it answers does not exist.

Three of the owner's asks drove it: trends grouped by state, each site against the national
average, and the theme distribution by department with the negative share of each. The first
of those produced the NSW finding above — **the single highest-value change made to this
analysis, and it came from the review rather than from the analysis.**

A fourth ask, added mid-review, produced `method_model_vs_owner.png`: both confusion matrices
(sentiment 3×3 and themes 8×8), the three kappas against the committed 0.60 floor, and what
the LLM was and was not used for. The theme matrix is new information — the 44.1% was a
headline figure until now, and the matrix shows *where* it goes: 21 comments the owner filed
elsewhere were pulled into `Staff manner`, the largest theme.

## The revenue question, added at review

The owner asked whether negative feedback actually affects revenue and customer behaviour, or
whether customers complain without consequence — and suggested basic EDA on
`monthly_revenue.csv`, which had never been profiled. Both were fair. The brief treated the
revenue file as a coverage denominator and section 8 used it for nothing else. **It is the
only behavioural record in the project and it was being used to count transactions.**

`analysis.md` section 9 now tests it. The result is a **null**, reported as one: the raw
cross-site correlation has the wrong sign (+0.22 — site size, not service), the within-site
correlation is −0.19 but **contemporaneous rather than leading** (not significant at any lag
from −3 to +3 months), and the NSW-versus-QLD natural experiment comes out at p = 0.41 with
NSW's service volume *growing* 4.9% while its satisfaction collapsed.

Three caveats are published with it rather than after it: twelve months is shorter than a
service interval; only 33% of the variance in a site's monthly negative rate is signal rather
than sampling noise, which attenuates every correlation shown; and the pack is fictional, so
the relationship may never have been there. The panel could have detected |r| ≥ 0.166 at 80%
power, which is what makes the null worth stating at all.

**This strengthens the D-025 cut rather than weakening it.** A dollar figure from published
retention benchmarks assumes the mechanism Kestrel's own revenue declines to corroborate.
Both reports now say so.

It also produced a free check: the revenue file records exactly zero activity for VIC09 in
all six months after closure, which independently corroborates D-005's closure date across
two files produced separately.

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

**3. The national trend was published before it was split by state.** The group's
−0.171-star fall is real and survives every robustness check, and it is still an average over
three states that did different things. Both reports recommended acting on a figure that does
not describe QLD at all. Found by the owner asking for the state cut, not by this agent.

**4. Every chart rendered at roughly four times its intended aspect ratio**, plot squashed
into a strip, because `savefig(bbox_inches="tight")` grows the canvas to fit any text it finds
and the figure footers were single unwrapped lines. Found by reading the rendered PNGs rather
than trusting the code that wrote them. The same habit caught four label collisions.

**5. Smaller things found by reading the generated output rather than the code:** rates
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
`reports/run_manifest.json`, `reports/figures/*.png` (8), `README.md` (sections 8, 10, 11,
12, 13, 14, 15), `agents/reports/w5_analysis.md`.

**Files deliberately not touched:** `config.yaml` (G7), `DECISIONS.md` and `AI_LOG.md` (the
orchestrator's), `src/export.py` and `tests/test_export.py` (another session's — D-064,
D-067), every Wave 1–4 pipeline module (G3), `mappings/`, `data/`, and `Makefile`, whose
`analyse` and `figures` targets already existed and already work.

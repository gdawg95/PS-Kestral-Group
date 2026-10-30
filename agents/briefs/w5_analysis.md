# Brief: w5_analysis
**Status:** draft, awaiting owner approval (gate G2).
**Drafted:** 30 Oct 2026, 13:05, at the end of the Wave 4 conversation.
**Hard deadline: code freeze Friday 30 Oct 15:00**, then proofread until COB. Under two hours.

This brief is written to be handed to a fresh conversation. Read `PLAN.md` and `DECISIONS.md`
first, then this.

---

## What Wave 4 changed about Wave 5, before you plan anything

Four results from last night and this morning narrow this wave. They are not optional context;
two of them change which numbers you are allowed to publish.

1. **The sentiment model failed its pass mark (D-065).** Cohen's κ 0.403 against a floor of
   0.60 committed in advance. **The customer's star rating scored 0.460 on the same labels —
   it beats the model.** D-055's pre-committed fallback therefore applies: **the rating is the
   primary signal for negative feedback, and model sentiment is reported as a method
   comparison with its κ stated.** D-004 already defined negative as rating 1–2 *or* negative
   sentiment, so nothing downstream redefines — but the headline must rest on the rating.
2. **Theme rankings are not safe (D-065).** The owner and the model agreed on a comment's
   theme only **44.1%** of the time. A theme's negative *rate* is reportable with that stated.
   **One theme ranked above another is not.** "Focus here first" must be argued from volume
   and the rating, not from a 44%-reliable theme ordering.
3. **The planned three-way drivers cut does not exist (D-060).** Theme × department ×
   dealership is 576 cells for 5,353 comments — 9.3 per cell. Do theme × department
   nationally, theme × dealership only for the 19 sites that clear 20 responses, and the five
   thin sites (VIC09, QLD05, NSW07, VIC08, QLD07) at department level with a footnote.
4. **Every negative rate must name its denominator (D-058).** 28.1% of *commented* rows are
   negative by rating; ~22.5% of *all 7,150* rows are. Commentless rows average 4.40 stars
   against 3.54 for commented ones, so the commented subset is not representative. A report
   that says "28% of feedback is negative" without saying which denominator is wrong by 5.6
   points.

---

Goal:            The three business questions answered with numbers a reviewer can trace to
                 code, at least one trend with evidence that it is real, and at least one
                 recommendation — the three §2 non-negotiables Wave 5 owns.
Inputs:          `data/clean/feedback_classified.parquet` (7,150 rows; 5,353 with a comment,
                 sentiment and theme; 1,797 with nulls by design, D-057)
                 `data/raw/reference/monthly_revenue.csv` (24 dealers × 12 months)
                 `data/raw/reference/dealerships.csv`
                 `reports/benchmarks.md` (**unreviewed by the owner** — see the value model)
                 `reports/evaluation.md`, `reports/llm_review.md`, `reports/trend_evidence.md`
                 `config.yaml` thresholds — all committed, none to be changed (gate G7)
Outputs:         `src/analyse.py` → `reports/analysis.md`
                 `src/figures.py` → `reports/figures/*.png`
                 `reports/business_report.md` (deliverable #2)
                 `README.md` Wave 4 and Wave 5 sections (deliverable #3)
                 `reports/run_manifest.json` (PLAN.md §6; does not exist yet)
                 `agents/reports/w5_analysis.md`
Allowed to touch: the outputs above, plus `Makefile` (`analyse`, `figures` targets)
Not allowed:     `src/ingest.py`, `src/pii.py`, `src/schema.py`, `src/validate.py`,
                 `src/classify.py`, `src/evaluate.py`, `src/llm_review.py` (gate G3 — propose,
                 do not edit), `mappings/`, `data/` (read-only), and every `thresholds:` key in
                 `config.yaml` (gate G7). `DECISIONS.md` and `AI_LOG.md` are the
                 orchestrator's.
Decisions that apply: D-004 (negative), D-005 (closed site), D-006 (coverage as a limitation),
                 D-017 (producer ≠ checker), D-025 (value benchmarks — **still open**),
                 D-052 (trend threshold), D-055 (pass mark), D-056 (similarity floor —
                 **still open**), D-057 (null sentiment), D-058 (denominators), D-059 (8
                 themes), D-060 (drivers rescope), D-063 (sarcasm), D-065 (fallback)
Runs in:         the laptop repository with the project virtual environment (D-013 rev 2).

## Steps, in the order they should be done if time runs out

**1. Drivers — `src/analyse.py` (do this first).**
Negative rate by theme, by department, and by dealership, with the rating as the primary
signal per D-065. Every table states its denominator (D-058) and its row count. No theme
ranked against another. Report the sentiment-based figures alongside, labelled as the method
comparison they now are.

**2. Trend (second — this is a protected §2 output).**
Month-on-month movement using `thresholds.trend_evidence`, already committed in D-052: a
dealership-month needs ≥ 20 responses to be called a movement, the smallest reportable change
is 0.5 stars, and the five thin sites go on a quarterly basis. The evidence file says this rule
finds 33 of 257 month-pairs at 16 of 24 sites, so there *is* a trend to report. Show it with
and without the closed site VIC09 (D-005).

**3. Coverage (third, cheap).**
Feedback per transaction from `monthly_revenue.csv`: 200,249 service jobs and 16,011 vehicles
sold against 7,150 pieces of feedback. Report as a limitation (D-006), and it is also what
makes the volume argument for the recommendation.

**4. Charts — `src/figures.py`.** Consistent static PNGs for both reports. **Gate G9: the owner
approves every chart before it enters a report.**

**5. Business report (protected §2 output).** Draft only — the owner rewrites the
recommendations in their own voice. One recommendation, traceable to a number in
`reports/analysis.md`. Argue it from volume, the rating, and coverage; not from a theme
ranking.

**6. Value model — only if D-025 is set.** `reports/benchmarks.md` is written and cited but
**the owner has not reviewed it**, and its own agent asks for spot-checks of five load-bearing
figures. The benchmarks say plainly that **no published source maps a 1–5 rating to dollars**,
so any dollar figure is a labelled scenario, never a measurement. If D-025 is not set, cut this
and say so in the report.

**7. Technical report sections.** `README.md`'s Wave 4 and Wave 5 sections. Wave 4's story is
unusually strong and should be told: a pass mark committed in advance, a model that missed it,
a fallback applied rather than a bar moved, and two clustering methods replaced on evidence
(D-061, D-062). The decisions are already written; this is assembly, not analysis.

**8. Independent verifier — do not cut this if there is any way to keep it.** A fresh agent,
clean clone, `make all`, every reported number checked against the code (D-017, Checkpoint 5).
It is worth more to the grade than a second significance test.

Pilot (G1):      Run steps 1–3 on three dealerships before the full set — VIC09 (closed,
                 thinnest), QLD06 Toowoomba (71 summary rows, no comments), and the largest
                 site — and show the owner those tables before computing all 24.

Done when:
  - [ ] At least one trend identified, with its evidence and the committed threshold cited
  - [ ] At least one recommendation, traceable to a number in `reports/analysis.md`
  - [ ] Every rate names its denominator (D-058)
  - [ ] No theme ranked above another without the 44.1% caveat attached
  - [ ] Trends shown with and without the closed site (D-005)
  - [ ] *(owner)* Every chart approved before it enters a report (gate G9)
  - [ ] *(owner)* 2–3 headline numbers recomputed by hand (Checkpoint 5)
  - [ ] *(owner)* Recommendations rewritten in the owner's voice
  - [ ] Report written to `agents/reports/w5_analysis.md`

Report back:     what you did · assumptions · unresolved · rows in / out per stage

## Cut list, in order (PLAN.md §10, with Wave 4's items already spent)

Already cut or spent: Streamlit, Quarto, Docker-for-everything, CI, and the LLM step (which
ran at a reduced 857-comment scope). Next to go, in this order: **the value model** if D-025
is not set, then **statistical tests beyond the one trend check**, then **the baseline model
comparison**. Protect the independent verifier and the two §2 outputs.

## If you have only 90 minutes

Steps 1, 2, 3 and 5. A trend and a recommendation are non-negotiable; charts, the value model
and the technical report sections are not. Say in the report what was cut and why — a stated
cut reads as judgement, an unstated one reads as an omission.

## Questions for the owner (answer when approving)

  Q1. **D-056's similarity floor should be retired, not set — see D-066.** The owner's labels
      were used to test the mechanism and it does not work. Their 7 "none of these" comments
      had similarities 0.220–0.396; the 143 they placed ran 0.180–0.740 with a median of
      0.438, so the two groups overlap almost completely. A floor at the 4.7th percentile
      (0.259) that reproduces the owner's own none-rate catches **2 of their 7** rejections;
      catching all 7 needs 0.400, which marks **40.8% of the corpus** unassigned. Similarity
      also barely predicts correctness (38.3% theme match below 0.40, 44.8% at 0.40–0.50,
      42.3% at 0.50–0.60). **Proposed default:** retire it the way D-052 retired
      `dealer_match_min_confidence` — not set, with the evidence recorded — and report theme
      assignment with its 44.1% agreement as a stated limitation. **Owner confirms** (gate
      G7 applies to retiring a threshold as much as to setting one).

  Q2. **Is D-025 set, and has `benchmarks.md` been reviewed?** If not, the value model is cut
      (see step 6). **Proposed default:** cut it, and state in the business report that the
      value of fixing each driver was not quantified because the benchmarks were not verified
      before freeze. An honest gap beats an unreviewed dollar figure in a client report.

  Q3. **Does the business report lead with the rating or with sentiment?**
      **Proposed default: the rating**, per D-065. Sentiment appears once, as a method
      comparison with its κ of 0.403 stated beside the rating's 0.460.

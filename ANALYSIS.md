# Analysis detail

This document carries the full methodology and results for the NLP work (Wave 4) and the
data analysis (Wave 5). The [README](README.md) summarises the key findings; everything
below is the evidence behind them.

---

## Thresholds, set before the results

Gate G7: the owner sets every threshold and commits it before any result that depends on it
exists. Current state of [config.yaml](config.yaml):

| Threshold | Value | Basis |
|---|---|---|
| `negative_score_max_1to5` | 2 | D-004, provisional |
| `trend_evidence.min_month_responses` | 20 | ratings have SD 1.44, so a change between two 20-response months carries ±0.46 of noise |
| `trend_evidence.min_change_1to5` | 0.5 | sits just outside that band; the rejected "10 rows, 0.5 stars" rule would have called noise a trend |
| `trend_evidence.thin_dealer_basis` | quarterly | five sites have a median month under 20 and are compared by quarter rather than dropped |
| `llm_max_projected_hours` | 2 | the cut-off for keeping the optional LLM step |
| `nlp_pass_mark.sentiment_min_kappa` | 0.60 | Cohen's κ on a 150-comment stratified sample, committed before the owner labelled anything. Raw agreement was rejected: the commented rows are 59.3% positive, so an always-positive model scores 59.3% (D-055) |
| `nlp_pass_mark.fallback` | `score_only` | named in advance — if κ < 0.60 the rating is primary and sentiment is a method comparison. **It was invoked**: measured κ 0.403 (D-065) |

The trend rule calls 33 of 257 consecutive month pairs a trend, at 16 of 24 sites. Working
in [reports/trend_evidence.md](reports/trend_evidence.md); it was produced before the
threshold was chosen, so the choice is visible rather than retrofitted (D-052). Wave 5's
`src/analyse.py` reproduces 33 flags at the same 16 sites over 256 pairs — one fewer, because
it requires the two months to be adjacent and the evidence script did not.

**One threshold was retired rather than set, for the second time in this project.** D-056
planned an `unassigned` similarity floor for theme assignment; tested against the owner's
blind labels it caught 2 of their 7 rejections at the 4.7th percentile, and catching all
seven required marking 40.8% of the corpus unassigned. D-066 retires it and makes the 44.1%
theme agreement a stated limitation instead.

`dealer_match_min_confidence` was removed rather than set. It was the confidence floor for
a fuzzy dealership-name matcher that turned out to have nothing to match: the file → dealer
code map is approved by hand (D-034) and no free-text dealership column survives ingestion.

---

## NLP methodology

This is the part of the project with the clearest result, and the result is a failure. It is
written up at length because **how a failed model was handled is better evidence of control
than a model that happened to work.**

### What was built

| Stage | Method | Output |
|---|---|---|
| Sentiment | `cardiffnlp/twitter-roberta-base-sentiment-latest`, three classes, cached by `sha256(text + model tag)` | 5,353 commented rows labelled; the 1,797 commentless rows carry **null**, never "neutral" (D-057) |
| Theme discovery | **KMeans k=12** over UMAP-reduced MiniLM embeddings, seed 42 | [reports/theme_discovery.md](reports/theme_discovery.md), five example comments per cluster |
| Theme list | The owner named and approved eight themes from the clusters; capped at 8 by D-059 | [mappings/themes.yaml](mappings/themes.yaml) |
| Theme assignment | Cosine similarity to **6–7 short probe phrases per theme, max-pooled** (D-062) | Every commented row assigned, with its similarity recorded |
| LLM adjudication | `qwen2.5:3b` in Docker, prompt `sentiment_v1`, temperature 0, seed 42 | 857 comments, 49.8 minutes, **0 parse failures** ([reports/llm_review.md](reports/llm_review.md)) |
| Evaluation | scikit-learn, against 150 comments the owner labelled **blind** | [reports/evaluation.md](reports/evaluation.md) |

### Two methods did not survive contact with the data

Both are recorded with the evidence that replaced them, because a method chosen in a plan and
a method that works on the data are different things.

- **BERTopic/HDBSCAN cannot cluster this corpus (D-061).** A `min_cluster_size` sweep over all
  5,353 comments returned either 84 micro-clusters with 27% outliers, or — at every setting
  from 20 upwards — a single cluster holding 87% of the data. BERTopic's own topic reduction
  did not fix it: the merged result still had one cluster of 3,191 comments. Short service
  comments averaging 101 characters have no separated density peaks; what varies most in the
  embedding space is which car the customer drives and how happy they are. **KMeans replaced
  it**, on the owner's suggestion, after the orchestrator predicted it would not help and was
  wrong. The cost is stated rather than glossed: KMeans cannot refuse a comment, so its 0%
  outlier rate is a property of the algorithm, not a quality result. HDBSCAN stays reachable
  via `--kmeans-k 0`, so the failure is reproducible.
- **One long description per theme embeds badly (D-062).** Assignment first ran against a
  50–80 word description per theme. The similarity scale came out compressed (median 0.328)
  and two of ten decile spot-checks were misassigned — **one at the median**, where no
  confidence floor could have caught it. The cause was in the wording, not the model: a
  60-word description embeds to the centroid of everything it mentions, and the descriptions
  borrowed each other's consequences. Short probes fixed it: median 0.328 → **0.424**, p90
  0.475 → **0.582**, nine of ten deciles correct with the single remaining error at p0.

### The pass mark, and what happened to it

`thresholds.nlp_pass_mark` was committed to [config.yaml](config.yaml) **before the owner
labelled anything** (gate G7, D-055): Cohen's κ ≥ 0.60 on a 150-comment stratified sample,
with a named fallback — `score_only` — if it missed. κ rather than raw agreement because the
commented rows are 59.3% positive, so a model that answers "positive" every time scores 59.3%
raw agreement and κ = 0.

The owner then labelled 150 comments blind to the model's output **and blind to the star
rating**, which D-017 does not require but which would otherwise have let the labels inherit
the signal they were measuring. 263 comments were excluded from the draw because they had
already been quoted in conversation, several with the model's label attached.

| Signal, same 150 labels | Cohen's κ |
|---|---:|
| **The sentiment model** | **0.403** — floor 0.60, **FAIL** |
| **The customer's star rating alone** | **0.460** |
| The local LLM, 45 overlapping rows | 0.727 |

**The customer's star rating beat the model.** D-055's pre-committed fallback was applied and
the bar was not moved (D-065): the rating is the primary signal in every Wave 5 figure, and
model sentiment appears only beside a rating-based number with its κ stated. PLAN.md §9's stop
rule — *"NLP misses the pass mark → apply the planned fallback; don't move the bar"* — is the
rule this followed.

**Why it failed, from the confusion matrix. Both causes had been identified before the labels
existed, which is the part worth noting:**

1. **It over-uses `neutral`.** The owner used neutral **3 times in 150**; the model assigns it
   to 22.4% of the corpus. 34 of the sample's comments were called neutral by the model while
   the owner called them negative (22) or positive (12).
2. **It reads sarcasm and praise-then-complaint as positive** — *"Wow, what a well oiled
   machine"* on a 1-star. 812 of 5,353 comments (15.2%) carry Australian slang markers, and
   all eight of the pilot's polarity-inverted cases were irony or idiom (D-063).

**The LLM's κ of 0.727 does not promote it.** It is measured on 45 rows, and those 45 are
exactly the disagreement cases the LLM was pointed at. It annotates and never overwrites
`sentiment_label`, so every Wave 5 number reproduces for a reviewer who never starts Ollama.

![Agreement between the models and the owner's blind labels](reports/figures/method_model_vs_owner.png)

*Panel A: the three signals against the pass mark committed before the labelling. Panel B:
where sentiment goes wrong — 34 of 150 called neutral, 15 real negatives called positive.
Panel C: the full theme confusion matrix behind the 44.1%. Panel D: what the LLM was and was
not used for.*

### The theme result, and the floor that was retired

Model and owner agreed on a comment's theme **44.1%** of the time. D-056 had planned to set an
`unassigned` similarity floor from the observed distribution; tested against the owner's
labels, **no floor works** (D-066):

| Floor | Catches the owner's 7 rejections | Marks unassigned |
|---:|---:|---|
| 0.259 — reproduces the owner's own 4.7% none-rate | **2 of 7** | 248 (4.6%) |
| 0.400 — catches all 7 | **7 of 7** | **2,185 (40.8%)** |

Similarity barely predicts correctness either: 38.3% theme agreement below 0.40, 44.8% at
0.40–0.50, 42.3% at 0.50–0.60. A floor at the 4.7th percentile would have reproduced the
owner's own none-rate exactly — a figure that reads as validation — while catching two of
their seven rejections, so **the threshold was retired rather than set**, the way
`dealer_match_min_confidence` was. The consequence is a reporting rule, enforced in
[src/analyse.py](src/analyse.py) rather than in prose: **theme negative rates are reportable
with the 44.1% attached; theme rankings are not.**

---

## Data analysis

[src/analyse.py](src/analyse.py) → [reports/analysis.md](reports/analysis.md), and
[src/figures.py](src/figures.py) → `reports/figures/`. The working paper carries every table;
[reports/business_report.md](reports/business_report.md) quotes it and adds nothing of its
own.

### The four rules the analysis runs under

Each comes from a Wave 4 result, and each is enforced in code rather than left to the prose.

| | Rule | From |
|---|---|---|
| 1 | The star rating is primary; sentiment appears only as a labelled method comparison | D-055, D-065 |
| 2 | Theme tables are **alphabetical** — a rate is reportable, an ordering is not | D-065, D-066 |
| 3 | No theme × department × dealership cut: 576 cells for 5,353 comments is 9.3 per cell | D-060 |
| 4 | Every rate names its denominator | D-058 |

Rule 4 is the one a reader of the raw figures is most likely to get wrong. **28.1% of
commented rows are negative by rating; 22.5% of all 7,150 are.** Commentless rows average
**4.40** stars against **3.54** for commented ones, so the commented subset is not
representative — "28% of feedback is negative" overstates it by 5.6 points by silently
excluding the group that is overwhelmingly satisfied.

Rule 3's replacement cut is theme × department nationally, theme × dealership for the **19
sites whose average theme cell clears 20 comments**, and the five thin sites at department
level. Those five — NSW07, QLD05, QLD07, VIC08, VIC09 — are exactly the five D-052 put on a
quarterly basis for trends, reached from comment volume rather than month volume.

### The trend, and why it is believable

**The group's mean rating fell from 3.842 (Oct 2025 – Mar 2026) to 3.671 (Apr – Sep 2026),
and the negative rate rose 19.9% → 24.9%.**

The trend rule was committed before any trend result existed (D-052): 20 responses in a month,
0.5 stars, thin sites quarterly. Applied here it finds **33 of 256 consecutive dealer-month
pairs at 16 of 24 sites** — and those 33 split **16 down, 17 up**, so at the grain it was
calibrated for, *the rule finds no direction at all*. The group claim is therefore made at the
grain that has the data, and judged by the same rule's own arithmetic rather than by borrowing
its number:

> `min_change_1to5: 0.5` came from `sd × √(1/n₁ + 1/n₂)` at n = 20 a month, which is ±0.46.
> The same formula at n = 3,457 against 3,693 gives **±0.034**. The observed fall of 0.171 is
> five times that band. Welch p = 4.9e-07, Mann–Whitney p = 1.6e-05, and χ² on the
> negative/not-negative counts p = 4e-07.

Three alternative explanations were tested and none holds: the department mix is stable
(Service 69.3% → 67.9%), monthly volume is within 7%, and **removing the closed site moves the
fall from −0.171 to −0.169** (D-005). The decline is concentrated in **Service: 24.0% → 30.2%
negative, p = 1.8e-06**, against Sales +4.5 points and Parts unchanged.

**And the group figure is an average over three states that did different things** (section
7.3 of the analysis). Splitting it was the single highest-value thing done to this result:

| | Rating change | Negative rate | Welch p |
|---|---:|---:|---:|
| **NSW** (7 sites) | **−0.330** | 18.1% → **26.4%** | **7.9e-08** |
| VIC (9 sites) | −0.166 | 20.5% → 25.1% | 0.0028 |
| **QLD** (8 sites) | **−0.015** | 21.0% → 23.3% | **0.80 — no change** |

Reporting only the national figure would have told Queensland's eight sites to fix a problem
they do not have and understated New South Wales' by more than half. Inside NSW the move is
**+10.3 points in Service** (p = 3.1e-07) and +8.5 in Sales, while NSW Parts improved.

**Per-site testing, with the multiple-comparison problem handled rather than ignored.**
Testing 23 sites at p < 0.05 produces roughly one false positive by construction, so a Holm
step-down correction is applied across the whole family of tests. **Three sites survive it —
Parramatta (−0.75), Dandenong (−0.72) and Liverpool (−0.58) — and every one is a fall. No
site improved significantly.** That asymmetry is itself evidence; 23 noisy tests would not
produce three one-sided results. Uncorrected, five sites clear p < 0.05, and the corrected
table is what the report publishes. This is the full extent of per-site testing in the
project: cut-list item 7 makes tests beyond the one trend check cuttable, and the one kept is
the one the recommendation needs — *which* sites, not *whether* something changed.

![The year's movement split by state](reports/figures/q2_trend_by_state.png)

*The group figure is an average over three states that did different things.*

**Reconciliation against the committed evidence file.**
[reports/trend_evidence.md](reports/trend_evidence.md) predicted 33 of **257** pairs at 16 of
24 sites. The flag count and the site count match exactly; the pair count differs by one
because `scripts/trend_evidence.py` paired each month with the previous *present* month, so
Penrith's May 2026 was paired with its July across the June gap D-029 excluded.
`src/analyse.py` requires the two months to be adjacent. 257 − 1 = 256, and nothing else
differs.

### Coverage

7,150 responses against **278,697 transactions — 2.57%** (200,249 service jobs at 2.45%,
16,011 vehicles sold at 9.62%, 62,437 parts transactions at 1.13%). Reported as a limitation
(D-006), and it also bounds every rate in both reports: these are rates *among responders*,
and D-058 measured response as **not** independent of satisfaction. The analysis therefore
does **not** extrapolate the negative rate onto the 97.4% of transactions that produced no
feedback — section 9 of the analysis shows the arithmetic for that extrapolation and then
explicitly declines to publish it.

### Does satisfaction reach the revenue? A reported null result

`monthly_revenue.csv` (288 dealer-months) is the only behavioural data in the project, and
the analysis tests it against the feedback. **No link is detectable.**

- The raw cross-site correlation between negative rate and service volume is **+0.22** — the
  wrong sign, and it is site size, not service. Two-way demeaning by dealer and by month
  flips it to **−0.19 (p = 0.0018)**, worth about 8 service jobs in a month of 709.
- **It is contemporaneous, not leading.** The association is strongest at lag 0 and is not
  significant at ±1, ±2 or ±3 months. A month's negative rate predicts nothing about the
  next month's volume, which is equally consistent with a struggling branch producing both
  fewer completed jobs and more complaints.
- **The natural experiment is flat.** NSW's negative rate rose 8.3 points while QLD's did not
  move; NSW service volume still **grew 4.9%** against QLD's 6.6%, a per-site difference of
  1.5 points at **p = 0.41**. Of the three sites whose rating fell by more than chance, one
  lost volume, one was flat and one outgrew the group.

The null is reported with its own limits rather than as a conclusion: twelve months is
shorter than a service interval, only **33%** of the variance in a site's monthly negative
rate is signal rather than sampling noise (which attenuates every correlation shown), and the
challenge pack is fictional, so the relationship may never have been in the data. What the
panel *does* establish is that it could have detected **|r| ≥ 0.166** at 80% power, so a
large short-term effect is ruled out.

![Feedback against revenue: the across-sites correlation, and the lag profile](reports/figures/q3_feedback_vs_revenue.png)

*Left: the correlation a reader reaches for first, which is site size. Right: only the same
month is significant, so feedback predicts nothing about next month's volume.*

**A free data-quality check falls out of it:** the revenue file records exactly zero activity
for VIC09 in all six months from April 2026. The feedback and revenue files were produced
separately, so that is independent corroboration of D-005's closure date rather than an
assumption carried between them.

### The value model was cut

PLAN.md's third business question asks roughly what it is worth. [reports/benchmarks.md](reports/benchmarks.md)
exists but **has not been reviewed, D-025 is unset, and the benchmarks themselves state that
no published source maps a 1–5 rating to dollars.** It is item 1 on the cut list for this wave
(PLAN.md §10), and both reports state the gap rather than publishing a scenario dressed as a
measurement.

**The revenue test above is the second and stronger reason.** Retention benchmarks work by
assuming dissatisfied customers leave and that their leaving costs money. Kestrel's own
revenue cannot detect that mechanism operating, so a dollar figure derived from those
benchmarks would rest on an assumption the client's own data declines to corroborate. The
null result strengthens the decision to cut the value model rather than weakening it.

### Figures and gate G9

`src/figures.py` writes nine PNGs, named for the business question each answers. Gate G9
makes every chart the owner's to approve before it enters a report; **that approval was
given on 30 October 2026**, and all nine are now embedded in
[reports/business_report.md](reports/business_report.md). Until then
both reports carried a figure index instead, which is the evidence the gate was observed
rather than asserted.

| Figure | Answers |
|---|---|
| `q1_drivers_by_department.png` | which department carries the volume, which the rate |
| `q1_sites_vs_national.png` | every site as a deviation from the national rate, grouped by state, with Wilson intervals |
| `q1_themes_by_department.png` | theme mix within each department, beside the negative share of each |
| `q2_trend_by_state.png` | the year's movement split VIC / NSW / QLD, quarterly with intervals |
| `q2_sites_that_changed.png` | which sites moved, Holm-corrected across 23 tests |
| `q3_where_to_focus.png` | negative rate against its own change, bubble-sized by annual service jobs |
| `q3_feedback_vs_revenue.png` | the across-sites correlation and why it is site size, then the lag profile that shows no predictive link |
| `q3_coverage.png` | feedback per transaction, nationally and per site |
| `method_model_vs_owner.png` | both confusion matrices, the three kappas against the committed floor, and what the LLM was used for |

**Two of the nine exist to prevent a conclusion rather than support one.** `q3_feedback_vs_revenue.png` shows the naive across-sites correlation first, because it is positive and it is site size, and a reader who has not seen that cannot judge the rest; its footer says in terms that it is a guard, not a finding. `q3_where_to_focus.png` ranks sites on feedback, so its footer records that the analysis found no link between a site's negative rate and its revenue, and that nothing in the chart establishes a site in the top-right quadrant is losing money.

Three rules are enforced in the plotting code rather than in the captions. **The theme chart
is alphabetical and prints the 44.1% agreement on its own face**, so a sorted bar chart cannot
smuggle in the ranking D-065 forbids and the caveat cannot be separated from the picture in a
slide. **Every figure states its denominator in its own footer**, for the same reason. And
**no chart is drawn from a number this module computed** — every business figure is imported
from `src/analyse.py`, so a chart and a table cannot disagree; the method figure recomputes
the three kappas from the committed labels and `assert`s them against `reports/evaluation.md`
before it will render.

A twenty-four-line monthly chart was deliberately not drawn. A state-month holds about 190
responses, so a monthly site line is mostly noise, and twenty-four of them would invite a
reader to see patterns the data cannot support.

### Run provenance

[reports/run_manifest.json](reports/run_manifest.json) (PLAN.md §6) records the sha256 of
every input, the row count at each pipeline stage, the thresholds in force, the model and
prompt tags, the seed, the git commit and the package versions, so a reviewer can tell which
inputs produced which report.

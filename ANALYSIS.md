# Customer feedback analysis — insights and recommendations

This document answers the three business questions posed in the challenge brief, drawing on
7,150 customer feedback responses collected across 24 dealerships from October 2025 to
September 2026. The full working paper is [reports/analysis.md](reports/analysis.md);
methodology and thresholds are in the appendices at the end.

**Important context on coverage.** These 7,150 responses represent **2.57%** of Kestrel's
278,697 transactions in the period. Every finding below is a finding about *customers who
responded*, not about all customers. Customers who leave a comment are measurably less
satisfied than those who don't (3.54 vs 4.40 average stars), so the responding group is not
representative of the whole. This does not make the findings useless — it means they show
where dissatisfied customers are concentrating, which is exactly what a satisfaction team
needs.

---

## 1. What are the main drivers of negative feedback, and how do they vary across dealerships and departments?

### The short answer

**Service is the problem department.** It carries 68.6% of all feedback (4,903 of 7,150
rows) and has the worst negative rate: **27.2%** of Service responses are rated 1–2 stars,
compared to 16.0% for Parts and 10.6% for Sales. This is the clearest finding in the
dataset and requires no modelling to reach — it comes from the customer's own star rating
and a hand-verified department field.

**Across dealerships, a few sites sit clearly above the group average and a few clearly
below, but the middle sixteen overlap.** NSW01 (Parramatta) has the highest negative rate at
27.8%, and QLD05 (Noosa) the lowest at 2.0%. However, the confidence intervals for sites
ranked roughly 4th through 20th overlap heavily — the data does not separate them. The
honest reading is that there is a clearly worse tier and a clearly better tier, but the
middle is not ranked by this data.

| Department | Responses | Negative (1–2 stars) | Rate | Mean rating |
|---|---:|---:|---:|---:|
| **Service** | 4,903 | 1,333 | **27.2%** | 3.57 |
| Parts | 706 | 113 | 16.0% | 3.95 |
| Sales | 1,541 | 163 | 10.6% | 4.26 |

![Drivers by department](reports/figures/q1_drivers_by_department.png)

![Every site as a deviation from the national negative rate](reports/figures/q1_sites_vs_national.png)

### What the themes tell us (with a caveat)

An NLP theme model assigned each of 5,353 comments to one of eight owner-approved themes.
The model agrees with the owner **44.1%** of the time, so individual theme assignments are
uncertain — but one finding survives that uncertainty clearly:

**People are praised; processes are complained about.** Staff manner is the largest theme
(26.1% of comments) and by far the least negative at 8.6%. The operational themes — booking,
parts availability, workmanship and rework — each run above 43% negative. The recurring
pattern in the failure cases is *"Great welcome, helpful staff. Problem not fixed."*

This means the driver of negative feedback is not staff attitude but operational execution:
wait times, parts delays, rework, and communication gaps during the service process.

![Theme mix by department](reports/figures/q1_themes_by_department.png)

### Resolution

The data answers this question clearly at the department level: **Service is where the
problem is**, and it is a process problem, not a people problem. At the dealership level,
the data separates the extremes but not the middle pack.

### Suggestion

1. **Focus improvement effort on Service department processes** — not on staff training or
   manner, which customers already rate well.
2. **Investigate the specific operational pain points** at the three to five worst-performing
   sites (Parramatta, Chatswood, Essendon, Southport), starting with booking, communication
   during repairs, and rework/comeback rates.
3. **Use the theme × dealership heatmap** (section 6 of the working paper) as a map of where
   to look — which process issue is worst at which site — rather than as a league table.

---

## 2. Has anything changed over the year?

### The short answer

**Yes. The group got worse, but the decline is not uniform — it is concentrated in NSW and
specifically in Service.**

| Half | Responses | Mean rating | Negative rate |
|---|---:|---:|---:|
| H1 (Oct 2025 – Mar 2026) | 3,457 | **3.842** | **19.9%** |
| H2 (Apr – Sep 2026) | 3,693 | **3.671** | **24.9%** |

The fall of 0.171 stars is statistically robust (Welch p = 4.9e-07) and is not explained by
the closure of VIC09 (Shepparton), a shift in department mix, or a change in response volume.

**But the national number hides three different stories:**

| State | Rating change | Negative rate change | Significant? |
|---|---:|---:|---|
| **NSW** (7 sites) | **−0.330** | 18.1% → **26.4%** (+8.3 pts) | **Yes** (p = 7.9e-08) |
| VIC (9 sites) | −0.166 | 20.5% → 25.1% (+4.6 pts) | Yes (p = 0.003) |
| **QLD** (8 sites) | **−0.015** | 21.0% → 23.3% (+2.2 pts) | **No** (p = 0.80) |

**Queensland did not change.** Reporting only the national figure would tell Queensland's
eight sites to fix a problem they don't have and understate NSW's by more than half.

Inside NSW, the deterioration is in Service: negative rate rose from 21.7% to **32.1%**
(+10.3 points, p = 3.1e-07). NSW Sales also worsened (+8.5 pts), while NSW Parts
actually improved.

### Which sites changed?

Testing all 23 open sites with correction for multiple comparisons (Holm step-down), **three
sites show a statistically significant decline:**

| Site | State | Rating fall | Holm-adjusted p |
|---|---|---:|---|
| **Parramatta** (NSW01) | NSW | −0.75 stars | 1.4e-06 |
| **Dandenong** (VIC01) | VIC | −0.72 stars | 1.3e-06 |
| **Liverpool** (NSW04) | NSW | −0.58 stars | 0.006 |

No site improved significantly. That asymmetry — three falls, no rises — is itself evidence
that the decline is real, not noise.

![The year's movement split by state](reports/figures/q2_trend_by_state.png)

![Which sites changed — Holm-corrected across 23 tests](reports/figures/q2_sites_that_changed.png)

### Resolution

The data answers this question with high confidence. The group declined, but the decline is
overwhelmingly a NSW Service problem. Queensland is stable. The three named sites —
Parramatta, Dandenong and Liverpool — are the ones where the data is strong enough to make a
site-level claim.

### Suggestion

1. **Treat Parramatta, Dandenong and Liverpool as priority cases for operational review** —
   these are the sites where the data is unambiguous about a decline.
2. **Do not apply a blanket "fix" across all 24 sites.** Queensland's sites do not have the
   same problem, and a national programme would waste effort there while diluting focus where
   it matters.
3. **Investigate what changed at NSW Service sites in early 2026** — the shift begins around
   January and is sustained, not a one-month spike. Was there a process change, a staffing
   change, or a policy change that coincided?
4. **Watch Victoria.** VIC's decline is moderate and only Dandenong is individually
   significant, but the state-level trend is heading the same direction as NSW. Early
   intervention may prevent it from reaching NSW's level.

---

## 3. Where should Kestrel focus first, and roughly what is it worth?

### Where to focus

The evidence chains together in a single direction:

1. **Department:** Service carries 68.6% of feedback, 71.9% of transactions behind it, and
   the worst negative rate.
2. **State:** NSW drove the year's decline (−0.330 stars, +8.3 pts negative).
3. **Specific cell:** NSW Service went from 21.7% to 32.1% negative (+10.3 pts, p = 3.1e-07).
4. **Named sites:** Parramatta (−0.75 stars), Liverpool (−0.58 stars), and Dandenong
   (−0.72 stars, VIC but evidence-matched) survived correction across all 23 tests.

**The standing problem is Service everywhere. The new problem is NSW Service, and
specifically Parramatta, Liverpool and Dandenong.**

In plain counts, the national Service move is **156 more negative service responses in H2
than H1's rate would have produced**. At a 2.45% service response rate, those 156 sit beside
a much larger number of unheard service jobs — but the analysis deliberately does not
extrapolate that number, because response is not independent of satisfaction (see coverage
note above).

### What is it worth?

**Honestly: we cannot put a reliable dollar figure on it from this data.**

The analysis tested whether negative feedback predicts revenue loss, using 288 dealer-months
of service jobs, vehicle sales, parts transactions and revenue. The finding is a null result:

- A same-month association exists (r = −0.19, p = 0.002) — about 8 fewer service jobs in a
  month of 709, roughly −1.1% — but it is contemporaneous, not leading.
- **Feedback in one month predicts nothing about the next month's volume** at ±1, ±2 or ±3
  months.
- **The natural experiment is flat.** NSW's satisfaction collapsed and its service volume
  still grew by 4.9%. The ordering across states is in the predicted direction (NSW grew
  least, QLD grew most), but the difference is p = 0.41 — indistinguishable from chance.
- Of the three named declining sites, one lost volume, one was flat, and one outgrew the
  group. No pattern.

This does not mean negative feedback has no consequences. It means this dataset — twelve
months, monthly granularity, no customer-level tracking — cannot detect one. A service
interval is six to twelve months, so a customer who gave up on Parramatta in April 2026 may
simply not have been due back before the data ends in September. **The single most valuable
thing Kestrel could add to the next round of this work is customer-level repeat-visit data:**
did the individual who left a 1-star come back?

A value model based on external retention benchmarks was planned but **cut** (D-025 unset):
publishing a dollar figure that assumes dissatisfied customers leave, while Kestrel's own
revenue data declines to corroborate that mechanism, would be the least defensible number in
the project.

![Where to focus — negative rate vs change, sized by service volume](reports/figures/q3_where_to_focus.png)

![Feedback coverage per site](reports/figures/q3_coverage.png)

![Feedback against revenue — the lag profile](reports/figures/q3_feedback_vs_revenue.png)

### Resolution

The data tells Kestrel *where* to focus with high confidence: Service, NSW, and three named
sites. It cannot tell Kestrel *what the problem costs* in dollars, and saying so honestly is
more useful than publishing a number that cannot be defended.

### Suggestion

1. **Start with Parramatta, Liverpool and Dandenong Service departments.** These are the
   sites with the strongest statistical evidence of decline. A targeted operational review
   at these three sites will have more impact than a broad programme.
2. **Increase feedback collection rates.** At 2.45% of service jobs, the feedback system
   sees very little. Three QLD sites collect sales feedback at under 4% — effectively
   nothing. Higher collection rates would narrow the confidence intervals, separate the
   middle-pack sites, and make the next round of analysis far more precise.
3. **Add customer-level repeat-visit tracking.** This is the missing piece for answering the
   value question. Without knowing whether a dissatisfied customer came back, no amount of
   analysis on this data can connect satisfaction to revenue.
4. **Don't wait for a dollar figure to act.** The operational issues — particularly in
   booking, communication during service, and rework — are visible now. The three worst
   sites have clear, measurable declines. Process improvements at those sites can be
   measured directly in next year's feedback without needing a revenue model.

---

## Appendix A — NLP methodology

This section covers the NLP work (Wave 4). The sentiment model failed its pass mark, and how
that failure was handled is the key methodological point.

### What was built

| Stage | Method | Output |
|---|---|---|
| Sentiment | `cardiffnlp/twitter-roberta-base-sentiment-latest`, three classes | 5,353 commented rows labelled |
| Theme discovery | KMeans k=12 over UMAP-reduced MiniLM embeddings, seed 42 | [reports/theme_discovery.md](reports/theme_discovery.md) |
| Theme list | Owner named and approved 8 themes from the clusters (D-059) | [mappings/themes.yaml](mappings/themes.yaml) |
| Theme assignment | Cosine similarity to 6–7 short probe phrases per theme, max-pooled (D-062) | Every commented row assigned with similarity recorded |
| LLM adjudication | `qwen2.5:3b`, prompt `sentiment_v1`, temperature 0, seed 42 | 857 comments reviewed ([reports/llm_review.md](reports/llm_review.md)) |
| Evaluation | scikit-learn, against 150 owner-blind-labelled comments | [reports/evaluation.md](reports/evaluation.md) |

### The pass mark, and what happened

The pass mark was committed before any labelling (gate G7, D-055): Cohen's κ ≥ 0.60 on a
150-comment stratified sample, with a named fallback (`score_only`) if it missed.

| Signal | Cohen's κ |
|---|---:|
| **The sentiment model** | **0.403 — FAIL** (floor 0.60) |
| **The star rating alone** | **0.460** |
| The local LLM (45 overlapping rows) | 0.727 |

**The customer's star rating beat the model.** The pre-committed fallback was applied
(D-065): the rating is the primary signal in every analysis figure. Sentiment appears only
beside a rating-based number with its κ stated.

**Why it failed:** (1) the model over-uses "neutral" — the owner used it 3 times in 150
while the model assigns it to 22.4% of the corpus; (2) it reads sarcasm and
praise-then-complaint as positive — 15.2% of comments carry Australian slang markers and all
eight polarity-inverted pilot cases were irony (D-063).

![Agreement between the models and the owner's blind labels](reports/figures/method_model_vs_owner.png)

### Theme agreement: 44.1%

The model agreed with the owner on theme assignment 44.1% of the time (D-065). A planned
similarity floor was tested and retired (D-066) — no threshold separated the comments the
owner rejected from the ones they kept. The consequence is a reporting rule enforced in code:
**theme negative rates are reportable with the 44.1% caveat attached; theme rankings are
not.** Theme tables are printed in alphabetical order.

### Two methods that did not survive contact with the data

- **BERTopic/HDBSCAN could not cluster this corpus** (D-061). Short service comments
  averaging 101 characters have no separated density peaks. KMeans replaced it on the
  owner's suggestion.
- **Long theme descriptions embed badly** (D-062). Replaced with 6–7 short probe phrases per
  theme, which raised median similarity from 0.328 to 0.424 and corrected nine of ten decile
  spot-checks.

---

## Appendix B — Thresholds

Gate G7 requires every threshold to be committed to [config.yaml](config.yaml) before any
result that depends on it exists.

| Threshold | Value | Basis |
|---|---|---|
| `negative_score_max_1to5` | 2 | D-004, provisional — ratings of 1–2 are "negative" |
| `trend_evidence.min_month_responses` | 20 | SD 1.44, so ±0.46 noise at n = 20 |
| `trend_evidence.min_change_1to5` | 0.5 | Just outside the noise band |
| `trend_evidence.thin_dealer_basis` | quarterly | 5 sites have median month under 20 |
| `llm_max_projected_hours` | 2 | Cut-off for the optional LLM step |
| `nlp_pass_mark.sentiment_min_kappa` | 0.60 | Cohen's κ, committed before labelling |
| `nlp_pass_mark.fallback` | `score_only` | **Invoked**: measured κ 0.403 (D-065) |

The trend rule found 33 of 256 consecutive month pairs at 16 of 24 sites — split 16 down
and 17 up, which is why the group-level trend claim uses the pooled half-year comparison
rather than site-level movements.

One threshold was retired rather than set: D-056's `unassigned` similarity floor for theme
assignment caught only 2 of 7 owner rejections at the natural threshold, and catching all
seven required marking 40.8% of the corpus unassigned (D-066).

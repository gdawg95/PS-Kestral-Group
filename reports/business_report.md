# Customer feedback, October 2025 – September 2026

**For:** the Head of Customer Experience, Kestrel Motor Group
**From:** gdawg95 · **Date:** 30 October 2026
**Status: DRAFT.** The recommendations in section 4 are written to be **rewritten in the
owner's own voice** before this report is sent (PLAN.md Checkpoint 5). Nothing here is
approved copy.

Every number in this report comes from [`reports/analysis.md`](analysis.md), which shows the
working, and from code a reviewer can run (`make analyse`). The method, the data-quality
record and the limitations are in the technical report, [`README.md`](../README.md).

---

## 1. The short version

**52 spreadsheets from 24 dealerships became one dataset of 7,150 responses**, of which 5,353
carry a written comment. Three things in it are worth your time.

**One. Across the whole year, 22.5% of responses were negative** — a rating of 1 or 2 out of
5, over all 7,150 responses. You will see a higher number quoted elsewhere in this project:
28.1%. That is the same measure over only the 5,353 responses that carry a comment, and the
two are 5.6 points apart because unhappy customers write and happy ones tick five and leave.
**Both are true; they answer different questions.** This report uses the 7,150 figure
throughout, and says so wherever a rate appears.

**Two. The group got worse over the year, and the evidence says it is real.** The mean rating
fell from **3.84 in the first six months to 3.67 in the second**, and the negative rate rose
from **19.9% to 24.9% — five percentage points**. That is not a seasonal wobble or an artefact
of the site that closed: it survives removing that site, the department mix did not change,
and three separate statistical tests put the odds of seeing this by chance at under one in a
million. The detail is in section 3.

**Three. It is a Service problem.** Service is 68.6% of the feedback and 72% of the
transactions behind it. Its negative rate went from **24.0% to 30.2%** across the two halves,
against Sales 8.2% → 12.7% and Parts flat at 16.0%. Service is where the volume is and where
the deterioration is.

**And one thing this report does not tell you.** It does not say what the problem is worth in
dollars. See section 5 — that is a deliberate omission, not an oversight.

---

## 2. What drives negative feedback

### By department — the reliable cut

**Denominator: all 7,150 responses. Negative = a rating of 1 or 2.**

| Department | Responses | Negative | Rate | Mean rating |
|---|---:|---:|---:|---:|
| **Service** | 4,903 | 1,333 | **27.2%** | 3.57 |
| Parts | 706 | 113 | 16.0% | 3.95 |
| Sales | 1,541 | 163 | 10.6% | 4.26 |

Service is both the largest department by feedback volume and the worst performing. A customer
who comes in for a service is roughly **two and a half times as likely** to leave a 1 or 2 as
a customer who buys a car.

This cut is trustworthy: the department label was mapped by hand from 16 source spellings and
every mapping was signed off. It is not a guess by a model.

### By dealership

Twelve sites sit above the group's 22.5% and twelve below it.
[`analysis.md` section 3](analysis.md) has all 24 with confidence intervals; the important
reading is that **the middle of that table is not meaningfully ordered**. The sites that
genuinely stand apart are the ones at the ends:

- **Parramatta (NSW01), 27.8% on 479 responses** — the highest rate at a site with enough
  volume to be sure of it.
- **Noosa (QLD05), 2.0%** — but that is **one** negative response out of 49, and 49 responses
  against 4,108 service jobs. It is the thinnest site in the dataset, not a model site.

### By theme — with a warning attached

Comments were assigned to eight themes using a local language model. **When the same comments
were labelled by hand, the model agreed on the theme only 44.1% of the time.** That number
governs what may be said here:

- A theme's negative rate **is** reportable, with the 44.1% stated — which is what the table
  in [`analysis.md` section 4](analysis.md) does, in alphabetical order.
- **"Theme X is a bigger problem than theme Y" is not reportable**, and this report does not
  say it. A 44%-reliable classifier cannot order eight categories.

**What does survive that caveat** is the coarsest split in the list, and it is consistent
across every site: **staff manner is the largest theme (1,395 comments) and by a wide margin
the least negative (8.6%, against 28.1% across all commented responses).** The complaints are
not about the people. The recurring comment in this dataset praises the staff and criticises
the process:

> *"Great welcome, helpful staff. Problem not fixed."*
> *"nice helpful staff, wait was too long tho"*
> *"Good people, very nice to deal with. Slow, slow, slow."*

Which part of the process is less certain — that is exactly what the 44.1% is uncertain about.

---

## 3. What changed over the year

**This is the trend, and it is a group-level finding.**

| | Oct 2025 – Mar 2026 | Apr – Sep 2026 | Change |
|---|---:|---:|---:|
| Responses | 3,457 | 3,693 | |
| **Mean rating** | **3.84** | **3.67** | **−0.17 stars** |
| **Negative rate** (all responses) | **19.9%** | **24.9%** | **+5.0 points** |

**Why you can believe it.** The project set its evidence rule for trends *before* producing
any trend result, and wrote it into the configuration: a month needs 20 responses before any
movement is claimed from it, and the smallest change worth calling a trend is half a star.
That rule was calibrated for one site in one month, where the noise on a change is about
±0.46 stars. This finding is measured on 3,457 responses against 3,693, where the same
arithmetic puts the noise at **±0.034 stars** — the observed fall is five times that. Three
tests agree, each at p < 0.0001.

**What it is not.**

- **It is not the closed site.** Shepparton (VIC09) shut on 31 March 2026, so all of its
  responses fall in the first half — precisely the kind of change that can fake an improvement
  or a decline. Removing it entirely moves the fall from −0.171 to −0.169 stars. Every trend
  figure in the analysis is published both ways.
- **It is not a change in who is responding.** The department mix is stable (Service 69.3% →
  67.9%), and the monthly response volume is within 7% across the two halves.
- **It is not one bad site dragging the group.** At individual site level the rule finds 33
  movements across 16 sites, and they split **16 down, 17 up** — no direction at all. The
  group decline only becomes visible when the data is pooled, which is why this is stated as a
  group finding and not as a list of failing branches.

**Where it sits.**

| | H1 | H2 | Change | Significance |
|---|---:|---:|---:|---|
| **Service** | 24.0% negative | 30.2% | **+6.2 pts** | p = 0.0000018 |
| Sales | 8.2% | 12.7% | +4.5 pts | p = 0.0043 |
| Parts | 16.0% | 16.0% | −0.01 pts | p = 0.75 (no change) |

One site is worth naming separately: **Essendon (VIC03) fell from 4.09 to 2.62 stars in April
2026**, the largest single month-on-month move in the entire dataset and nearly three times
the threshold. It recovered to 3.57 the following month, so it reads as one bad month rather
than a lasting change — but it is the clearest example in the data of something going wrong
and being visible in the feedback within weeks.

---

## 4. Recommendation

> **DRAFT — to be rewritten in the owner's voice.** The reasoning and the numbers are
> settled; the wording is not.

### Focus first on the service lane, and treat the cause as process rather than people.

**The case, in five numbers, each traceable to [`analysis.md`](analysis.md):**

| | Number | Section |
|---|---:|---|
| Service's share of all feedback | **68.6%** (4,903 of 7,150) | 2 |
| Service's share of the transactions behind it | **71.9%** (200,249 of 278,697) | 8 |
| Service's negative rate | **27.2%**, worst of the three departments | 2 |
| Service's deterioration across the year | **+6.2 points** (24.0% → 30.2%), p = 0.0000018 | 7.2 |
| In plain counts | **305 more negative service responses** in H2 than H1's rate would have produced | 9 |

Nothing in that chain depends on the sentiment model, which failed its accuracy test, or on
the theme model, which is 44% reliable. It rests on the customer's own star rating, a
hand-mapped department field, and the transaction counts in the revenue file.

**The supporting steer, offered as a steer and not as a finding:** the comments praise the
people and criticise the process. If that holds when you read them yourself, the useful
interventions are operational — turnaround time, keeping customers informed, and whether the
job is right first time — rather than customer-service training for staff who are already
being thanked by name.

### A second, cheaper recommendation: fix the collection, not just the service.

**This dataset sees 2.57% of Kestrel's transactions** — 7,150 responses against 278,697
service jobs, vehicle sales and parts transactions. Worse, the coverage is wildly uneven:

- Service feedback runs at **2.45%** of jobs nationally, from 0.66% (Noosa) to 2.94%
  (Essendon).
- Sales feedback runs at **9.62%** of vehicles sold nationally — but **Townsville collects 8
  responses on 403 sales (1.99%), Toowoomba 9 on 379 (2.37%) and Rockhampton 7 on 208
  (3.37%)**. Those three sites are not measuring their sales experience at all.

Three sites with effectively no sales feedback is a cheap fix, and it costs nothing to the
service work above. Until it is fixed, any comparison that includes those sites' Sales numbers
is comparing a measurement with an absence.

**One caution that applies to both recommendations.** Every rate in this report is a rate
*among the customers who responded*. The data shows response is not independent of
satisfaction — people who left a comment average 3.54 stars against 4.40 for people who did
not. So these rates should not be read as the view of Kestrel's customers generally, and this
report deliberately does not scale them up to the 97.4% of transactions that produced no
feedback.

---

## 5. What this report does not answer, and why

**"Roughly what is it worth?" is not answered.** That was the third business question, and the
honest position is that it cannot be answered to a standard worth putting in front of you.

Industry benchmarks for automotive service retention and customer lifetime value were
researched and written up (`reports/benchmarks.md`), but **that research has not been reviewed
and signed off**, and it says plainly that **no published source maps a 1–5 satisfaction
rating to dollars**. Any figure built on it would be a scenario wearing the clothes of a
measurement. The choice was between publishing a number that would not survive a question and
stating the gap, and this report states the gap.

**If you want a value estimate**, the missing piece is a decision on three assumptions —
what a lost service customer is worth, what share of 1–2 star customers actually leave, and
what share of those are recoverable. Give those three numbers and the estimate is an
afternoon's work on top of what is already here.

---

## 6. How far to trust this

The technical report ([`README.md`](../README.md)) has the full account. The four things that
most affect how you read the numbers above:

1. **The star rating is the primary signal, and that was a measured choice.** The sentiment
   model was tested against 150 comments labelled by hand, blind. It scored a Cohen's kappa of
   **0.403** against a pass mark of **0.60 that was committed in writing before the test** —
   and the customer's own star rating scored **0.460** on the same comments. The rating beat
   the model, so the rating is what this report uses. The pass mark was not lowered to let the
   model through.
2. **Theme assignment agrees with a human 44.1% of the time.** Theme rates are reported with
   that figure attached; no theme is ranked against another anywhere in this report.
3. **Coverage is 2.57%,** and response is not independent of satisfaction.
4. **Nobody independent has reproduced these numbers yet.** Every figure comes from committed
   code over committed inputs and `make analyse` regenerates them, but reproducible is not the
   same as independently checked.

---

### Figures

Six charts have been produced for this report and are held in `reports/figures/`. **They are
not embedded above because every chart needs sign-off before it enters a report** (gate G9).
Once approved they belong at these points:

| Figure | File | Goes in |
|---|---|---|
| The group's monthly rating and negative rate, with and without the closed site | `trend_national.png` | Section 3, top |
| Negative rate by department, first half against second | `negative_by_department.png` | Section 3, "Where it sits" |
| Negative rate by dealership with confidence intervals | `negative_by_dealership.png` | Section 2, "By dealership" |
| Negative rate by theme, alphabetical, with the 44.1% on the chart | `theme_negative_rates.png` | Section 2, "By theme" |
| Feedback per transaction, nationally and by site | `coverage.png` | Section 4, second recommendation |
| Essendon's April 2026 drop against the group mean | `largest_site_move.png` | Section 3, final paragraph |

# Customer feedback, October 2025 – September 2026

**For:** the Head of Customer Experience, Kestrel Motor Group
**From:** gdawg95 · **Date:** 30 October 2026
**Status: DRAFT.** The recommendations in section 4 are written to be **rewritten in the
owner's own voice** before this report is sent (PLAN.md Checkpoint 5). Nothing here is
approved copy.

Every number comes from [`reports/analysis.md`](analysis.md), which shows the working, and
from code a reviewer can run (`make analyse`). Method, data quality and limitations are in
the technical report, [`README.md`](../README.md).

---

## 1. The short version

**52 spreadsheets from 24 dealerships became one dataset of 7,150 responses**, 5,353 of them
carrying a written comment. Four things in it are worth your time.

**One. Across the year, 22.5% of responses were negative** — a rating of 1 or 2 out of 5,
over all 7,150 responses. You will see 28.1% quoted elsewhere in this project: that is the
same measure over only the 5,353 responses that carry a comment. The two are 5.6 points apart
because unhappy customers write and happy ones tick five and leave. **Both are true; they
answer different questions.** This report uses the 7,150 figure throughout and says so
wherever a rate appears.

**Two. Satisfaction fell over the year, and the evidence says it is real.** Mean rating
**3.84 → 3.67** across the two halves; negative rate **19.9% → 24.9%**. Not seasonal noise,
not the site that closed: three separate statistical tests put the odds of seeing this by
chance at under one in a million.

**Three — and this is the part that changes what you do about it. The decline is New South
Wales. Queensland did not move at all.**

| | Mean rating | Negative rate | Is the change real? |
|---|---|---|---|
| **NSW** (7 sites) | 3.95 → **3.62** | 18.1% → **26.4%** | **Yes — overwhelmingly** (p = 0.000000079) |
| **VIC** (9 sites) | 3.81 → 3.65 | 20.5% → 25.1% | Yes, but half the size (p = 0.0028) |
| **QLD** (8 sites) | 3.77 → 3.76 | 21.0% → 23.3% | **No** (p = 0.80) |

A single national number would have told your eight Queensland sites to fix a problem they do
not have, and understated New South Wales' by more than half.

**Four. Underneath the state picture, it is Service.** Service is 68.6% of the feedback and
72% of the transactions behind it, and has the worst negative rate of the three departments
(27.2%). In NSW specifically, Service went from **21.7% to 32.1% negative** — ten points in
six months. NSW Sales also worsened by 8.5 points. NSW Parts improved.

**And one thing this report does not tell you.** It does not say what the problem is worth in
dollars. Section 5 — a deliberate omission, not an oversight.

---

## 2. What drives negative feedback

### By department — the reliable cut

**Denominator: all 7,150 responses. Negative = a rating of 1 or 2.**

| Department | Responses | Negative | Rate | Mean rating |
|---|---:|---:|---:|---:|
| **Service** | 4,903 | 1,333 | **27.2%** | 3.57 |
| Parts | 706 | 113 | 16.0% | 3.95 |
| Sales | 1,541 | 163 | 10.6% | 4.26 |

A customer coming in for a service is roughly **two and a half times** as likely to leave a 1
or 2 as a customer buying a car. This cut is trustworthy: the department label was mapped by
hand from 16 source spellings and every mapping was signed off. It is not a model's guess.

### By dealership

Twelve sites sit above the national 22.5% and twelve below. The important reading is that
**the middle of that list is not meaningfully ordered** — the confidence intervals overlap.
The sites that genuinely stand apart:

- **Parramatta (NSW01), 27.8% on 479 responses** — the highest rate at a site with the volume
  to be sure of it.
- **Noosa (QLD05), 2.0%** — but that is **one** negative response out of 49, collected against
  4,108 service jobs. The thinnest site in the dataset, not a model site.

`q1_sites_vs_national.png` plots all 24 as a distance from the national line, grouped by
state, with the intervals shown.

### By theme — with a warning attached

Comments were sorted into eight themes by a local language model. **When the same comments
were sorted by hand, the model agreed on the theme only 44.1% of the time.** That governs what
may be said:

- A theme's negative rate **is** reportable, with the 44.1% stated.
- **"Theme X is a bigger problem than theme Y" is not**, and this report does not say it. A
  44%-reliable classifier cannot rank eight categories.

**What survives that caveat** is the coarsest split in the list: **staff manner is the largest
theme (1,395 comments) and by a wide margin the least negative (8.6%, against 28.1% across all
commented responses).** The complaints are not about the people. The recurring comment praises
the staff and criticises the process:

> *"Great welcome, helpful staff. Problem not fixed."*
> *"nice helpful staff, wait was too long tho"*
> *"Good people, very nice to deal with. Slow, slow, slow."*

*Which* part of the process is exactly what the 44.1% is uncertain about.

---

## 3. What changed over the year

| | Oct 2025 – Mar 2026 | Apr – Sep 2026 | Change |
|---|---:|---:|---:|
| Responses | 3,457 | 3,693 | |
| **Mean rating** | **3.84** | **3.67** | **−0.17 stars** |
| **Negative rate** (all responses) | **19.9%** | **24.9%** | **+5.0 points** |

**Why you can believe it.** The rule for calling a movement real was written into the project's
configuration *before* any trend result existed: a month needs 20 responses, and the smallest
change worth reporting is half a star. That rule was calibrated for one site in one month,
where random noise on a change is about ±0.46 stars. This finding is measured on 3,457
responses against 3,693, where the same arithmetic puts the noise at **±0.034 stars** — the
observed fall is five times that. Three different tests agree, each at p < 0.0001.

**What it is not.**

- **Not the closed site.** Shepparton (VIC09) shut on 31 March 2026, so all its responses fall
  in the first half — exactly the kind of change that can fake a trend. Removing it moves the
  fall from −0.171 to −0.169 stars.
- **Not a change in who responds.** Department mix is stable (Service 69.3% → 67.9%) and
  monthly volume is within 7% across the halves.
- **Not one bad site dragging the group.** At site-month level the committed rule finds 33
  movements across 16 sites, splitting **16 down, 17 up** — no direction at all. The decline
  only appears when the data is pooled.

### Where it actually is

**By state** — see section 1. NSW −0.33 stars, VIC −0.17, QLD −0.01 and not significant.

**Inside NSW, by department:**

| | First half | Second half | Change |
|---|---:|---:|---:|
| **NSW Service** | 21.7% negative | **32.1%** | **+10.3 points** (p = 0.0000003) |
| NSW Sales | 7.8% | 16.4% | +8.5 points (p = 0.0007) |
| NSW Parts | 19.2% | 14.7% | −4.5 points — improved |

**By individual site.** Testing 23 sites for a change creates a trap: at the usual threshold,
roughly one site in twenty looks "significant" with nothing happening. After correcting for
that, **three sites moved by more than chance — and all three fell. None improved.**

| Site | Change | Adjusted p |
|---|---:|---:|
| **NSW01 Parramatta** | −0.75 stars | 0.0000014 |
| **VIC01 Dandenong** | −0.72 stars | 0.0000013 |
| **NSW04 Liverpool** | −0.58 stars | 0.0057 |

Bendigo (VIC08) is the near miss at −0.62 and adjusted p = 0.15 on 144 responses — worth a
look, not worth a claim.

---

## 4. Recommendation

> **DRAFT — to be rewritten in the owner's voice.** The reasoning and the numbers are settled;
> the wording is not.

### There are two different problems here, and conflating them wastes the effort.

**The standing problem is Service, everywhere.** 68.6% of the feedback, 72% of the
transactions, and the worst negative rate of the three departments at 27.2%. That is true in
all three states and it has been true all year. It is a structural issue with the service
experience, not an incident.

**The new problem is New South Wales, and it is six months old.** NSW Service went from 21.7%
to 32.1% negative while Queensland did not move. Something changed in NSW between March and
April 2026, and the data says *where* without saying *what*.

### Focus first: NSW Service, starting with Parramatta and Liverpool.

| | Number | Section |
|---|---:|---|
| Service's share of all feedback | **68.6%** (4,903 of 7,150) | 2 |
| Service's share of the transactions behind it | **71.9%** (200,249 of 278,697) | 8 |
| Service's negative rate | **27.2%**, worst of three departments | 2 |
| NSW Service's deterioration | **+10.3 points** (21.7% → 32.1%), p = 0.0000003 | 7.3 |
| Sites that fell by more than chance | **Parramatta, Dandenong, Liverpool** — all falls | 7.3 |

Parramatta and Liverpool are both NSW and both survive the statistical correction, so they are
where the state story and the site story agree. **Dandenong (VIC01) is the third and sits
outside NSW** — it belongs on the list on its own evidence, not because of the state pattern.

Nothing in that chain depends on the sentiment model, which failed its accuracy test, or on
the theme model, which is 44% reliable. It rests on the customer's own star rating, a
hand-mapped department field, and your transaction counts.

**The supporting steer, offered as a steer and not a finding:** the comments praise the people
and criticise the process. If that holds when you read them, the useful interventions are
operational — turnaround time, keeping customers informed, whether the job is right first time
— rather than customer-service training for staff who are being thanked by name.

### Second, cheaper recommendation: fix the collection, not just the service.

**This dataset sees 2.57% of Kestrel's transactions** — 7,150 responses against 278,697
service jobs, vehicle sales and parts transactions. The coverage is also wildly uneven:

- Service feedback runs at **2.45%** of jobs nationally, from 0.66% (Noosa) to 2.94%
  (Essendon).
- Sales feedback runs at **9.62%** nationally — but **Townsville collects 8 responses on 403
  sales (1.99%), Toowoomba 9 on 379 (2.37%) and Rockhampton 7 on 208 (3.37%)**. Those three
  sites are not measuring their sales experience at all.

Three sites with effectively no sales feedback is a cheap fix. Until it is fixed, any
comparison involving their Sales numbers compares a measurement with an absence.

**One caution on both recommendations.** Every rate here is a rate *among customers who
responded*, and response is not independent of satisfaction — people who left a comment
average 3.54 stars against 4.40 for those who did not. These rates are not the view of
Kestrel's customers generally, and this report deliberately does not scale them onto the 97.4%
of transactions that produced no feedback.

---

## 5. What this report does not answer, and why

**"Roughly what is it worth?" is not answered.** That was the third business question, and the
honest position is that it cannot be answered to a standard worth putting in front of you.

Industry benchmarks for automotive service retention and customer lifetime value were
researched and written up (`reports/benchmarks.md`), but **that research has not been reviewed
and signed off**, and it states plainly that **no published source maps a 1–5 satisfaction
rating to dollars**. Any figure built on it would be a scenario wearing the clothes of a
measurement.

**If you want a value estimate**, the missing piece is a decision on three assumptions — what
a lost service customer is worth, what share of 1–2 star customers actually leave, and what
share of those are recoverable. Give those three numbers and the estimate is an afternoon's
work on top of what already exists.

---

## 6. How far to trust this

The technical report ([`README.md`](../README.md)) has the full account; `method_model_vs_owner.png`
shows it in one picture. The four things that most affect how you read the numbers above:

1. **The star rating is the primary signal, and that was a measured choice.** The sentiment
   model was tested against 150 comments labelled by hand, blind. It scored a Cohen's kappa of
   **0.403** against a pass mark of **0.60 committed in writing before the test** — and the
   customer's own star rating scored **0.460** on the same comments. The rating beat the
   model, so the rating is what this report uses. **The pass mark was not lowered to let the
   model through.**
2. **Theme assignment agrees with a human 44.1% of the time.** Theme rates are reported with
   that figure attached; no theme is ranked against another anywhere in this report.
3. **Coverage is 2.57%,** and response is not independent of satisfaction.
4. **Nobody independent has reproduced these numbers yet.** Every figure comes from committed
   code over committed inputs and `make analyse` regenerates them — but reproducible is not the
   same as independently checked.

---

### Figures

Eight charts are held in `reports/figures/`, named for the question each answers. **They are
not embedded above, because every chart needs sign-off before it enters a report** (gate G9).
Once approved they belong at these points:

| Figure | Answers | Goes in |
|---|---|---|
| `q1_drivers_by_department.png` | which department carries the volume and the rate | §2, "By department" |
| `q1_sites_vs_national.png` | every site against the national average, by state | §2, "By dealership" |
| `q1_themes_by_department.png` | theme mix per department, and the negative share of each | §2, "By theme" |
| `q2_trend_by_state.png` | the year's movement split VIC / NSW / QLD | §1 and §3, top |
| `q2_sites_that_changed.png` | which sites moved by more than chance | §3, "By individual site" |
| `q3_where_to_focus.png` | bad now against getting worse, sized by service volume | §4, top |
| `q3_coverage.png` | how much of the business this dataset sees | §4, second recommendation |
| `method_model_vs_owner.png` | where the models disagree with a human, and by how much | §6 |

# Labelling guide — Checkpoint 4

**File:** `reports/label_sample.csv` · **150 rows** · open it in Excel.
Fill the `sentiment` and `theme` columns. Leave `row`, `feedback_id` and `comment` alone.

These labels are the reference every model figure is measured against (D-055: Cohen's
κ ≥ 0.60). Nothing else in the project can correct them, so they are worth more care than
speed — but use the short codes below, which make 150 rows a typing job rather than a writing
one.

## sentiment — one letter

| Code | Means |
|---|---|
| `n` | negative — the customer is unhappy |
| `u` | neutral — no clear feeling either way: a bare fact, a question, a request |
| `p` | positive — the customer is happy |

Three rules, in order of precedence:

1. **Judge what the customer actually feels**, not the words in isolation. *"Oh brilliant,
   another day of silence"* is `n`, not `p`.
2. **Praise plus a complaint** is whichever is the point. *"Staff were lovely. Still waiting
   on the part three weeks later though"* is `n` — the complaint is why they wrote.
3. **If you genuinely cannot tell, use `u`.** Do not guess between `n` and `p`; a wrong
   confident label is worse than an honest neutral, because κ is measured against these.

## theme — one number

| # | Theme | Shorthand |
|---|---|---|
| 1 | Staff manner | how they were treated, separate from the work |
| 2 | Communication and updates | being told what was happening, or chasing for it |
| 3 | Pricing and billing | what it cost, quote vs invoice, unapproved charges |
| 4 | Waiting and turnaround | time: queues, waiting, ready when promised |
| 5 | Parts availability | the part was or wasn't on hand |
| 6 | Booking | getting an appointment, lost or bumped bookings |
| 7 | Workmanship and rework | was the fault actually fixed; damage; coming back |
| 8 | Explanation and transparency | was the work and the invoice explained |
| `0` | **none of these** | use this, don't force a fit |

Two rules:

1. **Pick the one the comment is mainly about.** Many touch two; choose the one that would
   have to change for the customer to feel differently.
2. **`0` is a real answer.** A comment about the coffee machine or a bare "Thanks!" is `0`.
   Forcing it into a theme is the error this is measuring — and how many `0`s you give is
   itself evidence for where the `unassigned` floor belongs (D-056).

## What is deliberately not in the file

- **No star rating.** It is one of the three signals being compared, and tonight's evidence
  is that it is the weak one on the middle band. Seeing it would make your labels partly
  inherit it.
- **No model output**, of any kind. Not hidden — absent, so there is nothing to peek at.
- **No comment I have already shown you.** 263 were excluded: the whole 198-comment
  classifier pilot slice, plus 67 quoted in reports. Several of those I quoted *with the
  model's label attached*, which would have made those rows anything but blind.

## When you're done

Save the CSV in place and tell me. I'll report:

- Cohen's κ on sentiment against the 150, weighted back to the true distribution, and whether
  it clears the 0.60 you committed in D-055
- the share of theme assignments you judged defensible, and your `0` rate, which is what
  informs the D-056 floor
- where the LLM agreed with you against the deterministic model, and vice versa

The evaluation is a **separate agent** — D-017 forbids the agent that produced the labels
being graded from grading them. If κ misses 0.60, the planned fallback is already committed
in D-055: the rating becomes the primary signal and sentiment is reported as a method
comparison, with its κ stated. **The bar does not move.**

## If you are short of time

150 was chosen because the 95% confidence half-width is ±6.4pp there, against ±7.8pp at 100 —
at 100 comments the ruler cannot distinguish 80% agreement from 72%. Stopping early breaks
the 50/50/50 stratification, so **a partial sheet is not a smaller sample, it is a biased
one**. If you cannot do 150, say so and I will re-draw a smaller stratified sheet and record
the wider interval honestly — that is a worse measurement, but an honest one.

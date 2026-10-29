# What the NLP pass mark has to beat

**Dataset:** `data/interim/consolidated.parquet` — 7,159 rows, 5,362 with a comment.
**Status:** evidence only. `thresholds.nlp_pass_mark` is still `TBD`; the owner chose on
29 Oct 2026 to set it in Wave 4, before hand-labelling (D-022, gate G7). Nothing here is
a decision. This file exists so the numbers are not re-derived at 9pm on Thursday.

## The text available to evaluate

| | |
|---|---|
| Rows with a comment | 5,362 of 7,159 |
| Rows without one | 1,797, including the 71 Toowoomba summary rows (no comment by design, D-032 #1) |
| Median comment length | 101 characters (p10 41, p90 181, max 601) |
| Comments under 25 characters | 3.3% |
| By department | Service 3,749 · Sales 1,105 · Parts 508 |

Comments are long enough for both sentiment and themes; almost nothing is too short to label.

## The majority-class baseline — the number that matters

Using D-004's definition as a proxy for sentiment (negative ≤ 2, neutral 3, positive ≥ 4),
the commented rows split:

| Class | Share |
|---|---:|
| Positive (4–5) | 59.3% |
| Negative (1–2) | 28.1% |
| Neutral (3) | 12.7% |

**A model that answers "positive" to every comment scores 59.3%.** So a bar of 80% raw
agreement sits only 21 points above a model that does not read the text, and it can be
cleared while getting the negative class — the whole business question — badly wrong.
Raw agreement alone is the wrong instrument on a distribution this skewed.

Chance agreement on these marginals is 0.447, so **80% raw agreement corresponds to
Cohen's κ ≈ 0.64**. A κ floor of 0.60 is therefore nearly free if the model genuinely
works, and it is what fails the always-positive model (κ = 0).

## How precisely a hand-labelled sample can measure agreement

95% confidence half-width on an agreement estimate near 80%:

| Sample size | Half-width |
|---:|---:|
| 100 | ±7.8 pp |
| 150 | ±6.4 pp |
| 200 | ±5.5 pp |
| 300 | ±4.5 pp |

A 100-comment sample cannot distinguish 80% from 72% — the ruler is wider than the
margin being judged. Drawn at random, 100 comments also yield only ~13 neutral and ~28
negative examples, so the minority classes would be measured off a handful of rows.
Stratifying the sample by sentiment class (roughly 50/50/50) makes the negative class
measurable; the headline figure is then weighted back to the real distribution.

## On theme quality

D-022 mentions a theme F1. A credible per-theme F1 across roughly 8 themes is not
available from 150 comments — some themes would have three examples. A bar that can be
defended from a sample this size is the share of assigned themes judged defensible
(accept / reject on the same comments), set after the theme list is fixed (D-023). A real
theme F1 needs its own sample, sized after Wave 4's theme discovery, and is a candidate
for the cut list.

## Open risk, unrelated to the threshold

Neither NLP model has ever been downloaded or run. `config.yaml` names
`cardiffnlp/twitter-roberta-base-sentiment-latest` and
`sentence-transformers/all-MiniLM-L6-v2`; the laptop's Hugging Face cache holds three
unrelated `timm` models and nothing else. The Wave 1 environment check proved only that
Ollama works (D-013). `sentence-transformers`, `transformers`, `torch` and `bertopic` are
installed, so this is likely a short download — but Wave 4 rests on it and it is untested.

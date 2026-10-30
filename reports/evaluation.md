# Evaluation — the owner's blind labels against the models

**150 comments**, hand-labelled by the owner (gdawg95) on 30 Oct 2026, blind to every model output and to the customer's own star rating. The bar was committed before these labels existed (D-055).

**D-017 exception, recorded not hidden:** the agent that wrote `src/classify.py` wrote this evaluation too, because there was no time before the 15:00 freeze to stand up an independent one. Every input is a committed file and the arithmetic is sklearn's, so Checkpoint 5's independent verifier can re-run `make evaluate` and compare. Treat the numbers as reproducible, not as independent.

## The verdict

| | | |
|---|---:|---|
| **Cohen's kappa, sentiment** | **0.403** | floor 0.6 (D-055) → **FAIL** |
| Raw agreement, on the sample | 64.0% | the sample is stratified, so this is not the corpus figure |
| Agreement weighted back to the corpus | 65.5% | the headline figure D-055 asked for |
| The star rating alone, same labels | kappa 0.460 | the baseline the model has to beat |
| The LLM, on 45 overlapping rows | kappa 0.727 | a third opinion, never the arbiter (D-017) |

## Where the model and the owner disagree

Rows are the owner's label, columns the model's.

| owner \ model | negative | neutral | positive |
|---|---:|---:|---:|
| **negative** | 61 | 22 | 15 |
| **neutral** | 1 | 2 | 0 |
| **positive** | 4 | 12 | 33 |

```
              precision    recall  f1-score   support

    negative       0.92      0.62      0.74        98
     neutral       0.06      0.67      0.10         3
    positive       0.69      0.67      0.68        49

    accuracy                           0.64       150
   macro avg       0.56      0.65      0.51       150
weighted avg       0.83      0.64      0.71       150
```

## Themes

- **44.1%** of the 143 comments the owner placed in a theme were placed in the same theme by the model.
- The owner answered **'none of these'** on 7 of 150 comments (4.7%). That rate is the evidence for where the `unassigned` similarity floor belongs (D-056).
- Those comments' model similarity ran 0.220 to 0.396 (median 0.301), against 0.437 for the sample as a whole.

# How much movement is real? Evidence for the trend threshold

**Generated:** `python scripts/trend_evidence.py` · **Dataset:** 1,946 rows, 6 dealerships (NSW04, QLD06, QLD07, QLD08, VIC02, VIC06)

The owner chose to set `thresholds.trend_evidence` after seeing the data rather
than before (D-044, gate G7). This is that data. Nothing here is a decision.

**Scope warning:** this run covers 6 of the 24 dealerships, the pilot set. The numbers below are indicative; re-run this script after the full ingestion and set the threshold on the complete picture.

## The noise floor — the number that matters

Ratings across the whole dataset have a standard deviation of **1.42**.
A monthly mean built from *n* ratings therefore carries a standard error of
`sd / sqrt(n)`, and the difference between two monthly means carries about
`sqrt(2)` times that. So the smallest change that is distinguishable from noise
depends entirely on how many responses the month collected:

| Responses in the month | Standard error of its mean | Noise in a month-on-month change |
|---:|---:|---:|
| 5 | ±0.64 | ±0.90 |
| 10 | ±0.45 | ±0.64 |
| 20 | ±0.32 | ±0.45 |
| 30 | ±0.26 | ±0.37 |
| 50 | ±0.20 | ±0.28 |

Read that against the candidate rules: a 0.5 move off a 10-response month sits
inside its own noise band, so a rule of *10 rows and 0.5 stars* will call some
random variation a trend. The same 0.5 move off a 30-response month is outside it.

## What each candidate rule would keep

There are **66** consecutive month pairs in the data.

| Rule | Month pairs called a trend | Share | Dealerships with at least one |
|---|---:|---:|---:|
| 10 rows, 0.5 stars | 14 | 21% | 6 of 6 |
| 20 rows, 0.5 stars | 9 | 14% | 6 of 6 |
| 10 rows, 0.3 stars | 31 | 47% | 6 of 6 |
| 30 rows, 0.3 stars | 6 | 9% | 2 of 6 |

## Monthly volume, by dealership

A dealership whose months are mostly thin cannot support a monthly trend claim
at any threshold; it needs quarters instead.

| Dealer | Rows | Months | Smallest month | Median month | Largest month | Mean rating |
|---|---:|---:|---:|---:|---:|---:|
| NSW04 | 311 | 12 | 17 | 25 | 37 | 3.84 |
| QLD06 | 321 | 12 | 21 | 27 | 34 | 3.73 |
| QLD07 | 202 | 12 | 9 | 17 | 23 | 3.52 |
| QLD08 | 354 | 12 | 24 | 29 | 38 | 3.75 |
| VIC02 | 454 | 12 | 27 | 39 | 44 | 3.83 |
| VIC06 | 304 | 12 | 17 | 26 | 33 | 3.77 |

## How thin are the months?

| Responses in the month | Dealer-months | Share |
|---|---:|---:|
| under 10 | 1 | 1% |
| 10 to 19 | 10 | 14% |
| 20 or more | 61 | 85% |

## The largest moves in the data

| Dealer | Month | Previous mean | This mean | Change | n (prev → this) |
|---|---|---:|---:|---:|---|
| QLD06 | 2026-08 | 4.10 | 3.34 | 0.75 | 21 → 32 |
| VIC02 | 2026-02 | 3.58 | 4.33 | 0.75 | 33 → 40 |
| QLD06 | 2026-09 | 3.34 | 4.09 | 0.74 | 32 → 34 |
| NSW04 | 2026-06 | 4.06 | 3.32 | 0.73 | 17 → 37 |
| NSW04 | 2026-09 | 3.17 | 3.90 | 0.72 | 23 → 29 |
| QLD06 | 2026-06 | 3.37 | 4.05 | 0.68 | 30 → 21 |
| QLD07 | 2025-11 | 3.75 | 3.11 | 0.64 | 20 → 18 |
| QLD07 | 2026-05 | 2.96 | 3.55 | 0.59 | 23 → 22 |
| QLD07 | 2026-04 | 3.53 | 2.96 | 0.57 | 17 → 23 |
| VIC02 | 2026-03 | 4.33 | 3.77 | 0.56 | 40 → 39 |
| VIC06 | 2026-03 | 3.31 | 3.85 | 0.54 | 26 → 27 |
| NSW04 | 2026-05 | 3.53 | 4.06 | 0.53 | 17 → 17 |

## What to decide

Three numbers, and they interact:

1. **A minimum month size.** Below it, a dealership's month is reported as a count
   only and never as a movement.
2. **A minimum change.** It should sit outside the noise band for the month size
   chosen above, or the report will claim trends that are not there.
3. **Whether thin dealerships are compared quarterly instead**, so they appear in
   the trend section at all rather than being silently dropped.

Once set, the numbers go in `config.yaml` under `thresholds.trend_evidence` and are
committed before any trend result is produced (gate G7).

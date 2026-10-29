# How much movement is real? Evidence for the trend threshold

**Generated:** `python scripts/trend_evidence.py` · **Dataset:** 7,159 rows, 24 dealerships (NSW01, NSW02, NSW03, NSW04, NSW05, NSW06, NSW07, QLD01, QLD02, QLD03, QLD04, QLD05, QLD06, QLD07, QLD08, VIC01, VIC02, VIC03, VIC04, VIC05, VIC06, VIC07, VIC08, VIC09)

The owner chose to set `thresholds.trend_evidence` after seeing the data rather
than before (D-044, gate G7). This is that data. Nothing here is a decision.

**Scope:** all 24 dealerships.

## The noise floor — the number that matters

Ratings across the whole dataset have a standard deviation of **1.44**.
A monthly mean built from *n* ratings therefore carries a standard error of
`sd / sqrt(n)`, and the difference between two monthly means carries about
`sqrt(2)` times that. So the smallest change that is distinguishable from noise
depends entirely on how many responses the month collected:

| Responses in the month | Standard error of its mean | Noise in a month-on-month change |
|---:|---:|---:|
| 5 | ±0.64 | ±0.91 |
| 10 | ±0.46 | ±0.64 |
| 20 | ±0.32 | ±0.46 |
| 30 | ±0.26 | ±0.37 |
| 50 | ±0.20 | ±0.29 |

Read that against the candidate rules: a 0.5 move off a 10-response month sits
inside its own noise band, so a rule of *10 rows and 0.5 stars* will call some
random variation a trend. The same 0.5 move off a 30-response month is outside it.

## What each candidate rule would keep

There are **257** consecutive month pairs in the data.

| Rule | Month pairs called a trend | Share | Dealerships with at least one |
|---|---:|---:|---:|
| 10 rows, 0.5 stars | 52 | 20% | 22 of 24 |
| 20 rows, 0.5 stars | 33 | 13% | 16 of 24 |
| 10 rows, 0.3 stars | 109 | 42% | 22 of 24 |
| 30 rows, 0.3 stars | 27 | 11% | 9 of 24 |

## Monthly volume, by dealership

A dealership whose months are mostly thin cannot support a monthly trend claim
at any threshold; it needs quarters instead.

| Dealer | Rows | Months | Smallest month | Median month | Largest month | Mean rating |
|---|---:|---:|---:|---:|---:|---:|
| NSW01 | 479 | 12 | 33 | 39 | 49 | 3.59 |
| NSW02 | 454 | 11 | 30 | 43 | 56 | 3.79 |
| NSW03 | 278 | 12 | 16 | 23 | 30 | 3.71 |
| NSW04 | 311 | 12 | 17 | 25 | 37 | 3.84 |
| NSW05 | 303 | 12 | 18 | 25 | 29 | 3.78 |
| NSW06 | 285 | 12 | 17 | 22 | 32 | 3.91 |
| NSW07 | 133 | 12 | 8 | 10 | 16 | 4.08 |
| QLD01 | 460 | 12 | 30 | 37 | 51 | 3.68 |
| QLD02 | 310 | 12 | 18 | 25 | 35 | 4.00 |
| QLD03 | 277 | 12 | 11 | 22 | 31 | 3.84 |
| QLD04 | 250 | 12 | 15 | 20 | 27 | 3.64 |
| QLD05 | 49 | 12 | 1 | 3 | 8 | 4.63 |
| QLD06 | 321 | 12 | 21 | 27 | 34 | 3.73 |
| QLD07 | 202 | 12 | 9 | 17 | 23 | 3.52 |
| QLD08 | 354 | 12 | 24 | 29 | 38 | 3.75 |
| VIC01 | 484 | 12 | 31 | 40 | 53 | 3.64 |
| VIC02 | 454 | 12 | 27 | 39 | 44 | 3.83 |
| VIC03 | 346 | 12 | 19 | 26 | 45 | 3.64 |
| VIC04 | 308 | 12 | 16 | 26 | 35 | 3.75 |
| VIC05 | 309 | 12 | 17 | 25 | 38 | 3.63 |
| VIC06 | 304 | 12 | 17 | 26 | 33 | 3.77 |
| VIC07 | 292 | 12 | 15 | 25 | 31 | 3.76 |
| VIC08 | 144 | 12 | 9 | 11 | 16 | 3.78 |
| VIC09 | 52 | 6 | 5 | 9 | 12 | 3.98 |

## How thin are the months?

| Responses in the month | Dealer-months | Share |
|---|---:|---:|
| under 10 | 21 | 7% |
| 10 to 19 | 53 | 19% |
| 20 or more | 207 | 74% |

## The largest moves in the data

| Dealer | Month | Previous mean | This mean | Change | n (prev → this) |
|---|---|---:|---:|---:|---|
| VIC03 | 2026-04 | 4.09 | 2.62 | 1.46 | 23 → 32 |
| VIC09 | 2025-12 | 3.20 | 4.60 | 1.40 | 5 → 10 |
| NSW07 | 2026-08 | 3.77 | 5.00 | 1.23 | 13 → 8 |
| NSW07 | 2026-03 | 4.40 | 3.40 | 1.00 | 10 → 10 |
| NSW07 | 2026-09 | 5.00 | 4.00 | 1.00 | 8 → 8 |
| VIC08 | 2025-11 | 3.36 | 4.33 | 0.97 | 11 → 9 |
| QLD05 | 2026-02 | 3.80 | 4.75 | 0.95 | 5 → 4 |
| VIC03 | 2026-05 | 2.62 | 3.57 | 0.94 | 32 → 23 |
| VIC05 | 2026-02 | 4.12 | 3.21 | 0.91 | 17 → 29 |
| NSW03 | 2026-01 | 4.09 | 3.19 | 0.90 | 22 → 16 |
| NSW06 | 2026-09 | 3.27 | 4.16 | 0.89 | 26 → 25 |
| VIC04 | 2026-01 | 3.23 | 4.12 | 0.89 | 26 → 17 |

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

# The 16 dates the pipeline changed or invented

**Generated:** `python scripts/date_edge_cases.py` · 2026-10-29 22:01

Checkpoint 3's date review. Sixteen rows - every row whose date was corrected or imputed, not a sample. `reports/data_quality.md` lists the same rows but can only show the resolved date; the source value below is what makes them reviewable.

No comment text appears here.

## IPS_feedback_log.xlsx · sheet `Log` · 10 rows

The only non-date values in a column of 277. The day is the midpoint of the nearest dated row above and below, the year comes with them, and the written label supplies the month (D-040). All ten carry `date_approx`.

| Row | Source value | Resolved | Nearest dated row above | Nearest dated row below | Label and position agree on the month? |
|---:|---|---|---|---|---|
| 9 | `early Oct` | 2025-10-06 | row 8: 04/10/2025 | row 10: 09/10/2025 | yes |
| 26 | `mid Nov` | 2025-11-03 | row 25: 03/11/2025 | row 27: 04/11/2025 | yes |
| 73 | `early Jan` | 2026-01-12 | row 72: 10/01/2026 | row 74: 15/01/2026 | yes |
| 84 | `wk1 Feb` | 2026-02-04 | row 83: 03/02/2026 | row 85: 05/02/2026 | yes |
| 137 | `wk5 Mar` | 2026-03-29 | row 136: 27/03/2026 | row 138: 01/04/2026 | yes |
| 154 | `early Apr` | 2026-04-21 | row 153: 20/04/2026 | row 155: 23/04/2026 | yes |
| 192 | `mid Jun` | 2026-06-01 | row 191: 30/05/2026 | row 193: 04/06/2026 | yes |
| 248 | `Aug?` | 2026-08-12 | row 247: 12/08/2026 | row 249: 12/08/2026 | yes |
| 258 | `Aug?` | 2026-08-27 | row 257: 25/08/2026 | row 259: 29/08/2026 | yes |
| 269 | `mid Sep` | 2026-09-12 | row 268: 11/09/2026 | row 270: 13/09/2026 | yes |

## Shepparton feedback FINAL - site closed.xlsx · sheet `Log` · 6 rows

Dated after the site closed (30 Mar 2026), in a month the site was still open a year earlier - read as a year typo and moved to 2025 (D-032 #3). All six carry `date_corrected`.

| Row | Source value | Resolved | Shift |
|---:|---|---|---|
| 2 | `06/10/2026` | 2025-10-06 | year 2026 → 2025, day and month unchanged |
| 4 | `13/10/2026` | 2025-10-13 | year 2026 → 2025, day and month unchanged |
| 11 | `24/10/2026` | 2025-10-24 | year 2026 → 2025, day and month unchanged |
| 14 | `19/11/2026` | 2025-11-19 | year 2026 → 2025, day and month unchanged |
| 16 | `26/11/2026` | 2025-11-26 | year 2026 → 2025, day and month unchanged |
| 18 | `01/12/2026` | 2025-12-01 | year 2026 → 2025, day and month unchanged |

## What to look at

- The six corrected rows are a single consistent pattern: a 2026 date in a month the closed site could not have traded in, moved back one year with the day and month untouched. If the pattern is right, all six are right.
- The ten imputed rows are only as good as the neighbours they sit between, and the neighbours are tight: each of the ten is bracketed by dated rows within a few days. The two `Aug?` rows look like the weakest of the set, because there the source doubted the month rather than the day - but they are the best supported of all ten. Row 248 sits between two rows both dated 12 Aug, so nothing is left to guess.
- Where the written label and the resolved day disagree, the neighbours won: `mid Nov` resolved to the 3rd and `early Apr` to the 21st, because that is where the surrounding dated rows put them. The label still fixes the month, and the last column confirms label and position agree on the month for all ten (D-040's cross-check, re-run here rather than quoted).
- Every analysis in this project is monthly, so the day never reaches a published figure, and `date_approx` is set on all ten so they can be excluded from any day-level claim.

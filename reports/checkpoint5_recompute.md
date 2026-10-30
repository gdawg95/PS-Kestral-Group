# Checkpoint 5 — the headline numbers, recomputed

**PLAN.md Checkpoint 5**, first of three parts: *"recompute 2–3 headline numbers yourself"*.
Run by the owner (gdawg95) on 30 Oct 2026, before the 15:00 code freeze.

**Command:** `uv run python scripts/checkpoint5_recompute.py` · **exit code 0**

The script reads **only** `export/feedback_clean.csv` — the de-identified file published for
reviewers (D-064, D-067) — and imports nothing from `src/`. The analysis itself runs on
`data/clean/feedback_classified.parquet`, so this is a different file reached by a different
route. The expected values are typed in as literals copied by hand out of
`reports/analysis.md` and `reports/business_report.md`, so the check fails if the analysis
moves and the script is not updated.

## Output

```

Checkpoint 5 - recomputed from export\feedback_clean.csv
                                           recomputed   published

Rows in the published dataset                    7150        7150   OK
Negative rate, ALL rows (the headline)           22.5        22.5   OK
Negative rate, COMMENTED rows only               28.1        28.1   OK
Commented rows                                   5353        5353   OK
Service share of all feedback (%)                68.6        68.6   OK
Service negative rate (%)                        27.2        27.2   OK
NSW Service negative rate, 1st half (%)          21.7        21.7   OK
NSW Service negative rate, 2nd half (%)          32.1        32.1   OK
QLD negative rate, 1st half (%)                  21.0        21.0   OK
QLD negative rate, 2nd half (%)                  23.3        23.3   OK
Group mean rating, 1st half                     3.842       3.842   OK
Group mean rating, 2nd half                     3.671       3.671   OK
NSW01 Parramatta mean rating, 1st half           3.97        3.97   OK
NSW01 Parramatta mean rating, 2nd half           3.22        3.22   OK

All 14 match the published reports.

What this does and does not show:
  It shows the numbers in the reports are the numbers in the published dataset.
  It does NOT show the published dataset is a correct read of the 52 source
  spreadsheets - that is Wave 2's row reconciliation (README section 5) - and it
  is not independent, because the session that wrote the analysis wrote this too.
  D-017's independent verifier remains outstanding.
```

## What this closes, and what it does not

**Closes:** the first part of Checkpoint 5. Fourteen published figures — including all three
that the business report's recommendation rests on (Service's 68.6% share, NSW Service's
21.7% → 32.1%, and QLD's unchanged 21.0% → 23.3%) — are the numbers that are actually in the
published dataset.

**Does not close, and these are deliberately listed rather than left implied:**

1. **It does not show the published dataset is a correct read of the 52 source
   spreadsheets.** That is Wave 2's row-count reconciliation and duplicate proof
   (`README.md` section 5, `reports/reconciliation.md`), which was signed off separately at
   Checkpoint 2.
2. **It is not independent.** The Claude session that wrote `src/analyse.py` also wrote
   `scripts/checkpoint5_recompute.py`, so a shared misunderstanding could in principle appear
   in both. Its only defence is that it is 60 lines long and reads a different file. D-017's
   **independent verifier — a fresh agent, clean clone, `make all`, every number checked
   against the code — has not run**, and remains the largest outstanding item in the project.
3. **The other two parts of Checkpoint 5 are still open:** gate G9 (the owner approves each
   of the eight charts before it enters a report) and the rewriting of
   `reports/business_report.md` section 4 in the owner's own voice. That file is marked DRAFT
   in two places for exactly this reason.

## Why no spreadsheet

The owner's Excel licence had lapsed (recorded in `AI_LOG.md` AI-011, where the blind
labelling sheet went to Google Sheets for the same reason). Two spreadsheet-free routes were
checked as working before this one was used: the same `COUNTIF` / `COUNTIFS` formulas in
Google Sheets against `export/feedback_clean.xlsx`, and DuckDB 2.0.0 querying the CSV
directly. The state split reproduces in one SQL statement:

```sql
SELECT substr(dealer_code, 1, 3)                                      AS state,
       CASE WHEN feedback_month >= '2026-04' THEN 'H2' ELSE 'H1' END  AS half,
       count(*)                                                       AS n,
       round(100.0 * avg(CASE WHEN rating_1to5 <= 2 THEN 1 ELSE 0 END), 1) AS neg_pct
FROM 'export/feedback_clean.csv'
GROUP BY 1, 2 ORDER BY 1, 2;
```

```
NSW  H1  1089  18.1      NSW  H2  1154  26.4     <- +8.3 pts, the finding
QLD  H1  1088  21.0      QLD  H2  1126  23.3     <- +2.2 pts, not significant (p = 0.80)
VIC  H1  1280  20.5      VIC  H2  1413  25.1
```

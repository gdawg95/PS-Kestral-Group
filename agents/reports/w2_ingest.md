# Report: w2_ingest (pilot stage)
**Brief:** agents/briefs/w2_ingest.md
**Branch:** `w1-wrapup`
**Date:** 29 Oct 2026

Steps 1, 2 and 5 of the brief are done and the G1 pilot has run. Steps 3 and 4 —
the per-dealer joins across all 51 files and the whole-corpus leak check — are
waiting on the owner checking the pilot's reconciliation rows, which is what gate
G1 asks for.

## What I did

- Revised `mappings/columns.yaml` after the owner's review: the four changes they
  asked for and their answers to all eight questions in `mappings/QUESTIONS.md`.
  Recorded as D-036 – D-045.
- Wrote `src/ingest.py`. Everything is driven by the mapping; there are no
  per-file branches in the code, so a new quirk is a mapping change.
- Wrote `tests/test_ingest.py` — 51 test functions, 112 cases, synthetic frames
  only. One test per rule the owner decided, including the two the brief names
  explicitly: the Geelong reversal applies to the 2025 sheet only, and no column
  outside the allowlist reaches the output.
- Wrote `scripts/trend_evidence.py` → `reports/trend_evidence.md`, because the
  owner chose to set `thresholds.trend_evidence` after seeing the volumes (D-044).
- Ran the pilot on the five awkward dealers → `reports/reconciliation.md`.
- Corrected two things in the mapping that turned out to be wrong (below).

## Rows in / out — the pilot

Six dealer codes, because North QLD is two dealerships in one file.

| Stage | Rows | Note |
|---|---:|---|
| Read from the 17 worksheets in scope | 1,884 | |
| Dropped, with a reason each | −3 | 1 blank, 2 summary/note |
| Toowoomba pivot source rows | −6 | counts, not feedback |
| Rows those counts expand into | +71 | D-032 #1 |
| **Written to the dataset** | **1,946** | arithmetic closes |

| Dealer | Rows | Expected from the mapping | Agrees |
|---|---:|---:|---|
| VIC02 Ringwood | 454 | 100 + 113 + 115 + 127 = 455 source, −2 junk = 453 | see note |
| VIC06 Geelong | 304 | 304 | yes |
| NSW04 Liverpool | 311 | 82 + 73 + 71 + 85 = 311 | yes |
| QLD06 Toowoomba | 321 | 250 + 71 expanded = 321 | yes |
| QLD07 Rockhampton | 202 | 202 | yes |
| QLD08 Townsville | 354 | 354 | yes |

**The Ringwood note.** The mapping's `expected_rows` come from the Wave 1
profiles, which had already excluded blank rows but not note rows. Ringwood Q1's
profiled 113 is 34 + 79; ingestion reads 35 + 79, drops the blank row the
profiler had already netted out and the "*** NEW TEMPLATE FROM FEB" note, and
writes 33 + 79 = 112. So 100 + 112 + 115 + 127 = 454. The two numbers describe
the same rows; they differ because the profiler and the ingest count blank rows
at different points. This is the same mismatch that produced the row-budget
correction in D-039, and it is why the reconciliation reports rows read, rows
dropped and rows out separately for every worksheet rather than one total.

## Checks I ran

| Check | Command | Result |
|---|---|---|
| Mapping agrees with the profiles | `python scripts/check_mapping.py` | 52/52 files, every sheet, header row, row count and column |
| The new `department_map` check actually fires | broke `S: Sales` → `S: Salesx` on purpose | caught it, then restored |
| Test suite | `python -m pytest -q` | see the run log below |
| Schema of the pilot output | `schema.validate_frame` inside the run | no problems; nothing outside the allowlist |
| Geelong reversal | pilot output | 2025 raw mean 2.40 → 3.60; 2026 unchanged at 3.82. D-030 predicted exactly those numbers |
| 10-point conversion | pilot output | the full table, 1→1, 2→1, 3→2, 4→2, 5→3, 6→3, 7→4, 8→4, 9→5, 10→5 |
| Ringwood's mid-sheet split | pilot output | 33 rows out-of-5 dated 3–31 Jan; 79 rows out-of-10 dated 2 Feb – 31 Mar. The template changed on a month boundary, which is independent support for the owner's confirmation |
| North QLD split | pilot output | 202 / 354 exactly as asserted |
| Southport's four junk rows | run the row filter against the real sheet | rows 23, 167, 196 as `test_row`, row 192 as `summary_or_note` — what the owner decided, no more, no less |
| Liverpool Q3 | pilot output | 85 rows, all inside Jul–Sep 2026, range assertion passed |
| Redaction | pilot output | `[NAME]` 134, `[STAFF]` 124, `[REGO]` 115, `[PHONE]` 44, `[EMAIL]` 18 |

## Two corrections to the mapping the owner approved

Both were found while checking the answers, not by the owner's review.

1. **Both Wollongong CSVs are Windows-1252, not UTF-8** (D-043). The mapping said
   UTF-8. Reading them as UTF-8 raises `UnicodeDecodeError` on a curly
   apostrophe inside the comment column, so Wollongong's 285 rows would have
   been lost — or, worse, forced through and silently corrupted in the text the
   NLP reads.
2. **The row budget subtracted the blank and "Total" rows twice** (D-039). They
   were never inside the 7,162 profiled rows. The published identity now closes:
   7,162 − 51 − 7 + 71 − 16 = 7,159, and a test asserts it.

## Assumptions

- **The name roster is built from the worksheets in scope, not always all 52.**
  For the full run that is every file. For the pilot it is the 17 pilot
  worksheets, so a staff name that appears only in, say, Bendigo's staff column
  would not have been redacted out of a Ringwood comment in this pilot run. Staff
  names are site-specific, so the practical loss is near zero, but the full run's
  token counts will be slightly higher than the pilot's for this reason.
- **Trailing empty rows are trimmed before counting.** openpyxl's read-only mode
  reports a sheet's used range, which can run past the data. Those rows are not
  source rows and are not counted as drops.
- **`classify_junk` only looks at the first three cells** for note and test
  keywords, never the comment. A customer who writes "total cost came in under
  the quote" keeps their feedback; there is a test for exactly that.
- **Bendigo's letter codes are expanded into `department_raw`** (D-036). This is
  the only place ingestion rewrites a source value, it is the owner's explicit
  instruction, and a test asserts no other layout does it.

## Unresolved

- **Steps 3 and 4 have not run.** The per-dealer joins with the four D-002 proofs
  (non-overlapping file date ranges, no unexpected month gaps, rows in = rows out
  + dropped, exact-match duplicate check) and the whole-corpus leak check are
  written into the brief but not yet implemented. They need the full run, which
  needs the owner's sign-off on this pilot. **D-019 is still open** until the
  duplicate check runs.
- **`reports/trend_evidence.md` covers 6 of 24 dealerships.** Its headline — the
  rating standard deviation is 1.42, so a month-on-month change off two
  10-response months carries ±0.64 of noise — is unlikely to move much with the
  other 18, but the threshold should be set on the full table.
- **The full dataset does not exist yet.** `data/interim/consolidated.parquet`
  currently holds the pilot's 1,946 rows, not the expected 7,159. Anything
  downstream that reads it now would read a sixth of the data.
- **`config.yaml` still holds two `TBD` thresholds** (`nlp_pass_mark`,
  `trend_evidence`). `dealer_match_min_confidence` can be retired (D-034).
- **`make ingest` is still untested** — there is no `make` on the laptop. The
  pilot was run as `python -m src.ingest --dealers ...`; `scripts/run.ps1` is the
  tested path.

## Done-when criteria

- [x] Owner approved `mappings/columns.yaml` (Checkpoint 2) — 29 Oct 2026, after
      the four changes and eight answers were applied
- [ ] Pilot reconciliation checked by the owner ← **this is the next thing**
- [ ] All 24 dealers present; rows in = rows out + dropped for every file
      *(6 of 24 so far, and the identity closes for those)*
- [ ] Duplicate check run and result recorded (closes D-019)
- [ ] Leak check counts in the reconciliation report *(token counts are there;
      the leak counter — known names still present — is not)*
- [x] Tests pass on the laptop
- [ ] Report written to `agents/reports/w2_ingest.md` ← this file, but it covers
      the pilot only and must be rewritten after the full run

## Report back

Rows in 1,884 → rows out 1,946 across six dealer codes, arithmetic closing, with
every drop reasoned and the three riskiest conversions in the pack (Geelong's
reversal, Ringwood's mid-sheet 10-point switch, Liverpool's month-first quarter)
each verified against the number the owner's decision predicted. Two mapping
errors found and fixed. Waiting on the owner's check of the pilot rows before the
remaining 18 dealerships are ingested.

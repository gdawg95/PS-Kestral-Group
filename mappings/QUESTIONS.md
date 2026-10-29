# Open questions on the draft mapping — ALL ANSWERED

**Status:** the owner answered Q1–Q8 on 29 October 2026 and asked for four
further changes to the mapping. Every answer is recorded as a decision in
`DECISIONS.md` (D-036 – D-044) and implemented in `mappings/columns.yaml`.
Nothing on this page is still open.

Kept as the record of what was asked, what was answered, and what changed.

| # | Question | Owner's answer | Decision |
|---|---|---|---|
| 1 | Bendigo's `SV` / `S` / `P` | Service / Sales / Parts — **and spell the words out** | D-036 |
| 2 | Southport's row with a rating but no date | It was a test; remove it with the other test rows | D-037 |
| 3 | Toowoomba's missing Q4 Sales rows | Take at face value; report Service and Parts only | D-038 |
| 4 | Dandenong's booking-system note | Keep as contextual evidence; no numeric data in the row | D-044 |
| 5 | Ringwood's second header at row 37 | Confirmed; the 1–10 → 1–5 conversion happens either way | D-044 |
| 6 | Shepparton's six 2026 dates | Nothing to change | D-044 |
| 7 | Blank and "Total" rows | Useless — tag as "summary or notes" and drop | D-039 |
| 8 | The row budget, and the "asdf" row | Count "asdf" as "summary or notes" too, so it drops once | D-037, D-039 |

## The four further changes the owner asked for

| Change | What was done | Decision |
|---|---|---|
| "The staff column can be dropped as well" | The staff-name columns were already dropped from the dataset. The key is renamed `redact_staff` to make that plain, and the file now states that they are read in memory only, to strip staff names out of comments. | D-041 |
| "Note where all the formatting changes are" | New register: `reports/formatting_changes.md` — 13 kinds of inconsistency, each located by dealership, written to lift into the client report. | — |
| "I am OK with the imputation of estimated dates" for Ipswich | The rule is now exact and self-checking: the day is the midpoint of the nearest dated rows either side, the label supplies the month, and the run fails if those two disagree. Checked by hand for all 10 rows. | D-040 |
| "Split North QLD into Rockhampton and Townsville, using their own site codes" | Already the plan; now explicit, with both codes, both names and both row counts (202 / 354) asserted in the mapping. | D-042 |

## What changed in the mapping as a result

- `bendigo` gained `department_map` (SV → Service, S → Sales, P → Parts).
- `southport` gained a `junk_rows` block naming all four non-feedback rows by
  spreadsheet row, so the owner can check each one.
- `ips` date rule rewritten with the 10 values, the method and the cross-check.
- `northqld` gained a `split` block with asserted per-dealer row counts.
- `staff_columns` renamed `redact_staff` in all 7 layouts that have one.
- **`wollongong` encoding corrected from `utf-8` to `cp1252`** — not a question,
  a bug found while checking the answers. See below.
- `row_budget` rewritten with counted numbers; `rows_out_expected: 7159`.

## Two things found while implementing the answers

**1. Both Wollongong CSVs are Windows-1252, not UTF-8.** The draft said UTF-8.
Reading them as UTF-8 raises `UnicodeDecodeError` on a curly apostrophe inside
the comment column. Forcing it past that would corrupt the apostrophes in the
very text the NLP reads. Fixed in the mapping; recorded as D-043.

**2. The blank and "Total" rows were already outside the row count.** The draft
budget had them as a pending subtraction. They are not inside the 7,162 profiled
rows — the profiler had already excluded them — so subtracting them again would
have made the reconciliation fail to close by 26 rows. The exact counts are 14
blank rows and 12 "Total" rows, and they are now reported separately from the
16 rows that really are dropped. D-039.

---

## Still not questions — things decided without the owner

- **`Dealer` and `Site` columns are dropped, not used.** Hunter Motors' `Dealer`
  reads the same value on all 303 rows and Ipswich's `Site` on all 277. North
  QLD's `Site` *is* used, because that file genuinely holds two dealerships.
- **Liverpool Q3's dates are month-first, confirmed rather than assumed.**
  Month-first parses all 85 rows into Jul–Sep 2026; day-first parses only 29.
  The mapping asserts the date range, so the run fails if this ever changes.
- **All four Chatswood CSVs are semicolon-delimited**, not just the Q4 file.
- **Bendigo's CSV has a byte-order mark**, so it is read as `utf-8-sig`.
- **`dropped:` lists are checked, not decorative.** `scripts/check_mapping.py`
  asserts that every column in every sheet appears in `columns`, `dropped`,
  `redact_staff`, `site_column` or the pivot keys, so a new column in a re-sent
  file stops the run instead of being quietly ignored.
- **Four comment values are quoted in the mapping** — "TEST TEST", "testing new
  form", "test - ignore" and "asdf" — the Southport junk rows. They contain no
  personal data and the owner needs to see them to agree the rows are junk. It
  is the only place in the repository where a comment value appears, and the
  mapping says so at the point of use.

# Open questions on the draft mapping

Read alongside `mappings/columns.yaml`. Eight items. Each has a proposed default, so
you can approve with one word and only argue with the ones you disagree with.

Q1–Q3 change rows in the dataset. Q4–Q6 are confirmations of things the mapping already
assumes. Q7–Q8 are about how the reconciliation counts things.

---

## Q1. Bendigo codes its departments `SV` / `S` / `P` — do these mean Service / Sales / Parts?

**Proposal:** SV = Service, S = Sales, P = Parts.

Bendigo is the only file that uses letter codes rather than words. The 144 rows split
SV 97 / S 32 / P 15, which matches the Service-heavy shape of every other site.

I tested it against the comments rather than guessing from the letters:

| Code | Rows with a comment | "service" words | "sales" words | "parts" words |
|---|---:|---:|---:|---:|
| SV | 73 | 17 | 0 | 8 |
| S | 19 | 2 | 1 | 0 |
| P | 11 | 1 | 0 | 5 |

SV is clearly Service and P is clearly Parts. **S is the weak one** — 19 comments give
almost no signal either way, and it only becomes Sales by elimination. If S were
actually a second spelling of Service, Bendigo's Sales feedback would vanish and its
Service volume would be understated by 32 rows.

**Worth two minutes of your time:** open `bendigo feedback.csv`, filter `Dept = S`, and
read five comments. If they read like car buying, we are done.

## Q2. Southport has one row with a rating but no date. Drop it?

Source row 165: Sales, rating 3, no date, and it is not one of the three test rows
D-032 #5 already covers. D-031 only decided what to do about rows with no *rating*.

**Proposal:** drop it, counted under its own reason `no_date` in the reconciliation.
Every analysis is by month, so a row with no date cannot join a trend, and inventing a
date for one row adds more risk than the row is worth.

**Alternative** if you would rather keep it: date it as the midpoint of the rows either
side of it in the sheet and flag `date_approx`, the same treatment IPS gets (D-032 #4).

## Q3. Toowoomba logged no Sales feedback at all in Q4 2025. Is that real?

The Q4 2025 summary file has six rows — Parts and Service for each of October, November
and December — totalling 71. There is no Sales row anywhere in it.

**Proposal:** take it at face value and report Toowoomba Q4 2025 as Service and Parts
only. The expanded rows carry `from_summary = true`, no comment, and are dated the 15th
of their month.

**Why I am asking:** if the summary was built by someone who only pivoted two
departments, Toowoomba's Q4 Sales feedback exists somewhere we have not been given, and
Toowoomba's quarter-on-quarter numbers will look like a composition change rather than a
data gap. Either way it needs a footnote; the question is which footnote.

## Q4. Dandenong's May 2026 sheet carries a note about a new booking system. Keep it for Wave 5?

The sheet has an extra row above the header: *"NOTE: new online booking system went live
5 May. Expect some teething issues — log everything!"*

**Proposal:** drop it from the data (it is a note, not a row of feedback) but record it
as a known event for the trend section. If Dandenong's scores dip from May, this is the
most likely cause and the business report should say so rather than leave the reader to
guess.

No data changes either way — I just do not want it to disappear with the note row.

## Q5. Ringwood Q1 2026 — is the template change at row 37 right?

One sheet, two templates: rows 1–36 use the 5-point "Score (1-5)" template (34 rows of
data, January only), and from row 37 it switches to the 10-point "Score (out of 10)"
template (79 rows, February and March). The 10-point scores convert per D-020.

**Proposal:** split there, as the profiler found it.

**Worth a glance** because everything downstream for 79 of Ringwood's rows depends on
reading them as out-of-10 rather than out-of-5. Open the file and check that row 37 is
where the second header sits.

## Q6. Shepparton's six 2026 dates become 2025. Confirm?

Six rows are dated October–December 2026, after the site closed on 31 March 2026.
D-032 #3 already treats these as year typos and moves them to 2025, flagged
`date_corrected`. With that applied, Shepparton's data runs 6 Oct 2025 to 31 Mar 2026,
which fits the closure exactly.

**Proposal:** no change — just confirming, because it is six rows of a 51-row site and
the alternative (dropping them) would cost 12% of a dealership.

## Q7. How should blank and "Total" rows be counted?

Frankston has twelve monthly "Total …" rows and some blank separators; Ringwood Q1 has a
blank row and the "*** NEW TEMPLATE FROM FEB" note. These sit *inside* the row counts the
profiles report, so they have to be dropped and counted, not silently skipped.

**Proposal:** drop them with reasons `blank` and `summary_or_note`, and let the pilot
establish the exact counts per file rather than me asserting a number now. My ad-hoc
count came to roughly 14 blank and 13 note/total rows across the affected files, but the
boundaries depend on exactly where each layout starts, which the ingest code settles.

## Q8. The row budget — agree with the arithmetic?

`row_budget` at the bottom of `columns.yaml` sets out what ingestion must prove:

```
7162   source rows across the 51 ingested files
 -51   excluded sheets (Penrith Jun 26: 43, Southport Google reviews: 8)
  -7   Toowoomba summary source rows (they are counts, not feedback)
 +71   the rows those counts expand into
----
7175   candidate rows, before dropping anything
```

then drops with a reason each: Tamworth no-rating (10), Shepparton closure note (1),
Ringwood template note (1), Southport "asdf" (1), Southport TEST and 01/01/1900 (2),
blank/total rows (Q7), Southport no-date (Q2).

**One thing to agree explicitly:** Southport's "asdf" row is both a no-rating row (D-031)
and a test row (D-032 #5). **Proposal:** count it once, under `test_row`, so the
arithmetic closes. Otherwise the report double-counts one row and the totals will not add
up — which is exactly the kind of thing a reviewer checks.

---

## Not questions — things I decided and you should know about

- **`Dealer` and `Site` columns are dropped, not used.** Hunter Motors' `Dealer` reads
  `HUNTER` on all 303 rows and IPS's `Site` reads `KMG-IPS` on all 277, so neither adds
  anything over the file-level dealer code (D-034). North QLD's `Site` *is* used, because
  there the file genuinely holds two dealerships.
- **Liverpool Q3's dates are month-first, confirmed rather than assumed.** Month-first
  parses all 85 rows into Jul–Sep 2026; day-first parses only 29 and scatters them across
  the year. The mapping asserts the date range so the run fails if this ever changes.
- **All four Chatswood CSVs are semicolon-delimited**, not just the Q4 file the profiler
  brief flagged.
- **Bendigo's CSV has a byte-order mark**, so it is read as `utf-8-sig`. Without that the
  first column name comes through as `ï»¿Date` and the mapping silently misses it.
- **`dropped:` lists are checked, not decorative.** `scripts/check_mapping.py` asserts
  that every column in every sheet appears either in `columns` or in `dropped`, so a new
  column in a re-sent file stops the run instead of being quietly ignored.

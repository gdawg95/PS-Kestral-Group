# Report: w2_ingest
**Brief:** agents/briefs/w2_ingest.md
**Branch:** `w1-wrapup`
**Date:** 29 Oct 2026

All five steps are done. 7,159 rows from 51 files across 24 dealerships, the row
budget closing exactly, three of the four D-002 proofs passing and the fourth
producing a finding for the owner. **D-019 is answered but not closed** — the
duplicate check ran and found something specific; what to do about it is the
owner's call.

## What I did

- Revised `mappings/columns.yaml` after the owner's review — their four changes and
  their answers to all eight questions (D-036 – D-045) — and they approved it at
  Checkpoint 2.
- Wrote `src/ingest.py`, driven entirely by the mapping. No per-file branches in the
  code: a new quirk is a mapping change.
- Wrote `tests/test_ingest.py` — 197 cases on synthetic frames, one per rule the
  owner decided.
- Ran the pilot on five awkward dealers, the owner checked it (D-046), then ran the
  full ingestion.
- Added steps 3 and 4: the four join proofs and the leak check, both written into
  `reports/reconciliation.md`.
- Wrote `mappings/departments.yaml` + `scripts/check_departments.py` and
  `agents/briefs/w3_validate.md`, so Wave 3 has a mapping to approve and a brief to
  sign off rather than starting from PLAN.md's four-agent sketch.
- Wrote `scripts/trend_evidence.py` → `reports/trend_evidence.md`, because the owner
  chose to set the trend threshold after seeing the volumes (D-044).

## Rows in / out

| Stage | Rows | Note |
|---|---:|---|
| Read from the 80 worksheets in scope | 7,137 | 7,162 profiled − 51 excluded sheets + 26 blank/Total rows the profiler had netted out |
| Dropped, with a reason each | −43 | below |
| Toowoomba pivot source rows | −6 | counts, not feedback |
| Rows those counts expand into | +71 | D-032 #1 |
| **Written to the dataset** | **7,159** | **= `row_budget.rows_out_expected`, exactly** |

| Drop reason | Rows | Where |
|---|---:|---|
| `summary_or_note` | 16 | Frankston's 12 monthly totals, Shepparton's closure note, Ringwood's template note, Southport's "asdf", Toowoomba's "Grand Total" |
| `blank` | 14 | Frankston 12, Ringwood Q1 1, Shepparton 1 |
| `no_rating` | 10 | Tamworth — real comments, blank rating (D-031) |
| `test_row` | 3 | Southport (D-037) |

All 24 dealerships are present. Shepparton's data ends 30 Mar 2026, matching its
closure. Penrith's June 2026 is absent, as D-029 says it must be.

## The four join proofs (D-002)

| Proof | Result |
|---|---|
| (a) no two files of one dealership cover the same dates | **PASS** |
| (b) no unexpected month gaps | **PASS** — the only gap is Penrith June 2026, explained by D-029 |
| (c) rows read = rows out + dropped, worksheet by worksheet | **PASS** for all 80 |
| (d) exact-match duplicate check | **9 groups — a finding, see below** |

### (d) The Springwood duplicates — D-019's answer

9 pairs of rows share dealership, date, department, rating **and** comment text. All
18 are in `Springwood feedback.xlsx`, and **every single pair sits on consecutive
spreadsheet rows**. One pair repeats a 463-character comment.

Adjacency in all nine is what makes this conclusive. Two customers giving the same
score for the same department on the same day would land anywhere in a 310-row
sheet; they would not land next to each other nine times out of nine. And nobody
writes the same 463 characters twice.

A further **85 rows across 16 dealerships** match on everything but have no comment
at all. Those are not duplicates in any meaningful sense — two customers rating
Service 5 on the same busy Saturday produce them honestly — and they are reported,
not touched. Only 60% of those groups are on consecutive rows, against Springwood's
9 out of 9, which is the measurable difference between coincidence and double entry.

**And 63 more rows are identical by construction, not by error.** They came out of
the Toowoomba pivot: a cell saying nine people gave Service a 5 in October becomes
nine rows with the same date, the same score and no comment (D-032 #1). The first
version of this check lumped them in with the coincidences, which put that figure at
148 and made Toowoomba look like the worst offender in the pack when it is an
artefact of the expansion we chose. They are now counted on their own line.

**Nothing was de-duplicated.** Dropping 9 rows moves Springwood's published mean, so
it goes to the owner as Q1 of `agents/briefs/w3_validate.md`. D-019 is answered —
the check has run and the answer is specific — but it stays open until the owner
decides.

## Leak check (D-033)

| Pattern | Comments still containing it |
|---|---:|
| Phone number | 0 |
| Email address | 0 |
| Street address | 0 |
| Registration plate | 0 |
| A name from a staff column | 0 |

Of 5,362 redacted comments. Redaction applied `[STAFF]` 740 times, `[NAME]` 558,
`[REGO]` 479, `[PHONE]` 156, `[EMAIL]` 58.

The raw first-name counter fired on 100 comments, which would be a misleading number
to publish. Sifting it with the same capitalisation test D-026 uses to promote names:
**98 of the 100 are ordinary English words that happen to also be a first name
somewhere in the pack, and 2 are probably real misses** — 0.04% of comments. Both are
in `IPS_feedback_log.xlsx`, rows 35 and 40, named in the reconciliation so the owner
can look them up. That is the residual risk D-026 predicted, quantified.

`[STAFF]` at 740 against the PII pilot's 728 is the expected direction: the pilot
report predicted the full run would be slightly higher because the complete staff
roster is only available when every file is in scope.

## Checks I ran

| Check | Command | Result |
|---|---|---|
| Mapping vs profiles | `python scripts/check_mapping.py` | 52/52 files, every sheet, header row, row count and column |
| Department mapping vs data | `python scripts/check_departments.py` | 16 values, 16 entries, counts match; Service 4,909 · Sales 1,544 · Parts 706 |
| Lint | `python -m ruff check .` | all checks passed |
| Tests | `python -m pytest -q` | 197 passed, 2 skipped |
| Schema of the output | `validate_frame` inside the run | no problems; nothing outside the allowlist |
| Row budget | the run's own identity | 7,159 = the mapping's `rows_out_expected` |
| Geelong reversal | pilot, then the owner's read of the source | 2025 raw mean 2.40 → 3.60 exactly as D-030 states; 2026 untouched. **The owner confirmed from the spreadsheet that rows scored 1 carry praise** (D-046) — the reversal is evidence-backed, not inferred |
| 10-point conversion | pilot output | the whole D-020 table, value for value |
| Ringwood's mid-sheet split | pilot output | 33 rows out-of-5 dated 3–31 Jan, 79 out-of-10 dated 2 Feb – 31 Mar: the template changed on a month boundary |
| North QLD split | full run | 202 Rockhampton / 354 Townsville, as asserted |
| Data guardrail | `git add -f data/interim/consolidated.parquet` | refused, exit 1 — tested against the real dataset, not a dummy file |

## Four bugs found, and how

Three of the four were found by checking something nobody had asked about. All four
are in `AI_LOG.md` summary rows 12–18.

1. **A real complaint was being deleted as a spreadsheet subtotal.** Essendon Parts
   row 11 — "counter service is glacial. waited 50 mins.", scored 2. My
   `summary_or_note` regex had lost the word-boundary anchor the Wave 1 profiler
   had, so `count` matched the start of "**count**er", and because Essendon puts its
   comment in the second column the comment was inside the scanned range. A negative
   row, silently gone — the worst kind of loss for the negative-feedback question.
   **Found because the row budget came out at 7,158 instead of 7,159.** One row. The
   budget existing is the only reason this was caught; the pilot would never have
   shown it, because Essendon was not in the pilot.
2. **307 comments were stored as `""` rather than null.** An empty string is truthy
   to every `notna()` downstream: it inflated the comment total in the leak check
   and invented five duplicate groups whose "identical comment text" was two blanks.
3. **Both Wollongong CSVs are Windows-1252, not UTF-8** (D-043) — found while
   counting blank rows, by decoding every CSV byte by byte.
4. **The row budget double-subtracted the blank and "Total" rows** (D-039).

And one caught by the test suite rather than by me: tightening the regex to fix (1)
stopped it matching "Grand Total", because `total` anchored at the start of a string
does not match a string beginning "Grand". The existing test failed immediately.

## Where this differs from PLAN.md section 8

PLAN.md's Wave 2 names three agent types. Only one ran, so a reviewer looking for the
other two reports will not find them. The reason, for the record:

| PLAN.md's Wave 2 agent | What happened |
|---|---|
| Mapping — draft `columns.yaml` | Ran as **step 1 of this agent**, not separately. The mapping went to the owner on its own at Checkpoint 2 before any code was written, which is what the separation was for. |
| **Site joiners ×3 (VIC / NSW / QLD)** | **Never ran as separate agents.** There was nothing for them to do: a per-state joiner only makes sense if each state's files are stitched into a running sheet first, and ingestion reads every file straight into one frame keyed by `dealer_code`. The four proofs those joiners existed to produce — non-overlapping date ranges, no unexpected month gaps, rows in = rows out, exact-match duplicates — are implemented here as steps 3 and 4 and published in `reports/reconciliation.md`, per dealer rather than per state. |
| Ingest — build the consolidated dataset | This agent. |

So no evidence is missing, but it is in one report instead of four, and grouped by
dealership rather than by state. PLAN.md section 8 has not been edited: it is the owner's
document, and a plan that records what was intended is more useful to a reviewer than one
quietly rewritten to match what happened.

The same is true of Wave 3, which PLAN.md still describes as four agents. Two of them are
gone — dealership matching has nothing left to match (D-034) and theme discovery belongs
with the rest of the NLP in Wave 4. `agents/briefs/w3_validate.md` sets out what is
actually left and why, for the owner to approve under G2.

## Assumptions

- **`classify_junk` never scans the comment column.** A customer may open with
  "Total cost came in over the quote" or "Counter service is glacial"; both are now
  regression tests, along with five other words that merely start with a keyword.
- **Comments are stripped of surrounding whitespace** so that "no comment" is always
  null. Redaction already rewrites the text, so this is within scope.
- **Trailing empty rows are trimmed before counting**, because openpyxl reports a
  sheet's used range, which can run past the data.
- **Bendigo's letter codes are expanded into `department_raw`** (D-036) — the only
  place ingestion rewrites a source value, on the owner's instruction, with a test
  asserting no other layout does it.
- **The name roster is built from the files in scope.** For this run that is all of
  them, so the figures above are the full-corpus ones.

## Unresolved

- **D-019 is answered, not closed.** The owner must decide the 9 Springwood pairs.
  It is Q1 of the Wave 3 brief.
- **`mappings/departments.yaml` is a draft.** Every per-department number in both
  reports depends on it, so it needs Checkpoint 3 approval before Wave 3 fills the
  `department` column. Three things in it want a look: "Workshop" → Service (311
  rows, and its mean is 0.35 above plain "Service"), whether to carry a
  new-versus-used cut of Sales (326 rows at 11 of 24 sites), and the case variants.
- **Two comments may still contain a name** — `IPS_feedback_log.xlsx` rows 35 and
  40. Worth two minutes before anything is published.
- **`config.yaml` still holds two `TBD` thresholds.** `trend_evidence` now has its
  evidence (`reports/trend_evidence.md`, all 24 dealerships: rating SD 1.44, so a
  month-on-month change off two 10-response months carries ±0.64 of noise — the
  "10 rows, 0.5 stars" option would call noise a trend). `nlp_pass_mark` is still
  open and is needed before Wave 4's hand-labelling, not before Wave 3.
  `dealer_match_min_confidence` should be retired, not set (D-034).
- **`make` is still unavailable on the laptop**, so `make all` — the command the
  Wave 5 verifier runs — has only been exercised as `scripts/run.ps1`. Its `lint`
  target was broken until today and is now fixed; the rest is still untested as
  `make`.
- **`README.md` is still two lines**, and it is deliverable #3 (D-007).

## Done-when criteria

- [x] Owner approved `mappings/columns.yaml` (Checkpoint 2)
- [x] Pilot reconciliation checked by the owner (D-046)
- [x] All 24 dealers present; rows in = rows out + dropped for every file
- [x] Duplicate check run and result recorded — **D-019 stays open pending the
      owner's decision on the 9 Springwood pairs**
- [x] Leak check counts in the reconciliation report
- [x] Tests pass on the laptop (197 passed, 2 skipped)
- [x] Report written to `agents/reports/w2_ingest.md`

## Report back

7,137 rows read → 7,159 written across 24 dealerships, hitting the approved row
budget exactly, with every drop reasoned and three of four join proofs passing. The
fourth found 9 double-entered pairs in Springwood, all on consecutive rows, which is
now the owner's decision. Redaction leaves no phone, email, address, plate or staff
name in 5,362 comments and two probable name misses, both located. Four bugs found
and fixed, one of them a real negative comment that was disappearing silently and
was caught only because the row budget was one short.

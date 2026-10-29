# DECISIONS — Kestrel Motor Group: Data & AI Challenge

Each decision records what was decided, the options considered, and why. Status is **Decided**, **Provisional** (to confirm after data is seen), or **Deferred**.

Format: `D-NNN · Title · Status · Date`

---

## Scope and data

### D-001 · Unit of analysis: one row = one piece of feedback · Provisional · 29 Oct 2026
- **Decision:** Every row in every source spreadsheet is treated as one feedback record, with a new `feedback_id` assigned at ingestion.
- **Why:** In the 10 of 52 files scanned so far, each row is a distinct response (customer/date/department). Keeps counts simple and traceable.
- **Revisit if:** profiling finds rows covering several departments or multiple comments per row.

### D-002 · Join each site's files into one running sheet before consolidation · Decided · 29 Oct 2026
- **Decision:** Each dealership should have one workbook; sites sent files on different schedules. Files are joined per site first, then consolidated.
- **Verification (to turn the assumption into evidence):** the joiner agent must prove for each site that (a) file date ranges don't overlap, (b) there are no unexpected gaps, (c) rows in = rows out, and (d) an exact-match duplicate check on dealership + date + department + score + comment finds nothing (or flags what it finds).
- **Options considered:** assume no overlap (rejected — the brief says some sites keep a running workbook, so repeats are plausible); full fuzzy dedup (rejected — overkill for the timeframe).

### D-003 · Keep only four content columns; drop everything else · Decided · 29 Oct 2026 (revised)
- **Decision:** From each source file, keep only:
  1. **Date** of service/feedback
  2. **Department** (text)
  3. **Rating / satisfaction** (numeric after Wave 3 scale mapping)
  4. **Comment** (free text, redacted per D-026)

  Every other column is dropped at first ingestion — customer names, IDs, DMS numbers, phones, emails, addresses, rego, and vehicle make/model. No hashing.
- **Added by the pipeline (not from source columns):** `feedback_id` (new), `dealer_code` (from file name/sheet, matched to `dealerships.csv`), and lineage fields `source_file` + `source_row` so any record can be traced back to its spreadsheet.
- **Implementation:** an **allowlist**, not a blocklist — any source column not mapped to one of the four in `mappings/columns.yaml` is dropped, so an unexpected PII column is excluded by default.
- **Why:** these four columns answer all three business questions; no question needs customer-level or vehicle-level analysis; brand comes from `dealerships.csv`.
- **Exception:** a row's customer-name and rego values may be read *transiently* during ingestion to redact those exact strings from that row's comment (D-026), then discarded. They are never written to any interim or clean file.
- **Revision note:** earlier version used a drop-list of identifier columns; changed to an allowlist after the owner reviewed all 52 files.

### D-004 · Definition of negative feedback · Provisional · 29 Oct 2026
- **Decision:** A record is negative if its **score is 1–2 on a 1–5 scale** (3 = neutral) **OR** its comment's sentiment is negative. The score is the minimum signal, because many customers leave no comment.
- **To confirm after profiling:** equivalent thresholds for sites using other scales (1–10, 0–10, stars, words), and how to handle score/sentiment disagreement in reporting.

### D-005 · Include all dealerships, including the closed site · Decided · 29 Oct 2026
- **Decision:** Include all 24 dealerships. One site closed at the end of March 2026; it has no feedback after closure (~52 rows).
- **Mitigation:** trend results are shown with and without the closed site, plus a footnote, so a composition change can't masquerade as improvement.

### D-006 · Coverage reported as a limitation (for now) · Provisional · 29 Oct 2026
- **Decision:** Uneven feedback volumes per site are reported as a limitation. A feedback-per-transaction metric is computed from `monthly_revenue.csv` once data is consolidated; normalisation decision follows from that.

### D-026 · Free-text redaction tokens · Decided · 29 Oct 2026
- **Decision:** PII inside comments is replaced with typed tokens so the analysis keeps the signal that something was mentioned:
  | Found in comment | Token |
  |---|---|
  | Vehicle registration number | `[REGO]` |
  | Staff member's name | `[STAFF]` |
  | Customer's own / other person's name | `[NAME]` |
  | Phone number | `[PHONE]` |
  | Email address | `[EMAIL]` |
  | Street address | `[ADDRESS]` |
- **Method:** (1) exact-match redaction of that row's own name/rego values (where the source has those columns); (2) regex for phones, emails, addresses and Australian rego formats; (3) spaCy NER for remaining person names.
- **[STAFF] vs [NAME]:** an NER person name is tagged `[STAFF]` only when it appears in a staff context (e.g. "Dave in service", "my salesperson Priya"); otherwise `[NAME]`. Owner expects `[STAFF]` to be rare, so imprecision here is low-impact.
- **Known risk:** rego regex can false-positive on model and part codes (e.g. RAV4, CX5, V8). The test suite must include these as must-*not*-redact cases.
- **Method update after the PII pilot (29 Oct 2026, accepted by the owner after reviewing the second pilot):** the first laptop pilot missed "Raj" and a lower-case "dave", and redacted the ordinary words "Spooky" and "Keys". Three steps added:
  1. **Staff roster:** the 16 first names in the data's staff columns ("Taken by", "Logged by", "Card given by", "Staff") are redacted as `[STAFF]` in any letter case.
  2. **Sentence-start guard:** a one-word spaCy PERSON at the start of a sentence is redacted only if it is a first name seen in a name or staff column.
  3. **Corpus pass:** names spaCy tags mid-sentence in ≥ 2 comments, and that are capitalised in ≥ 60% of their uses, are redacted in any case ("Dave" yes; "Will", "Lovely" no). Token chosen by context.
  - Name lists are built in memory at each run and never written out (D-003 exception).
  - **Correction to the assumption above:** `[STAFF]` is not rare. 728 of 5,412 comments (13%) mention a staff-roster name.
  - **Residual risk:** a name used only once, in lower case, and not in any staff column can still get through. Reported in the data-quality report; the owner's read of pilot samples is the backstop.

### D-027 · Chermside Q1 2026: use FINAL v2 only · Decided · 29 Oct 2026
- **Decision:** `Chermside Q1 2026 FINAL v2.xlsx` (118 rows) is the source for Chermside Q1. `Chermside Q1 2026 FINAL.xlsx` (112 rows) is excluded from ingestion.
- **Evidence:** the profiler's exact-row check found every row of FINAL inside v2; v2 adds 6 rows and extends the date range to 31 Mar. Owner checked the v2 profile against the spreadsheet (agents/reports/w1_profilers_pilot_review.md).
- **Also found:** the two "extra" files in the owner's folder (54 vs the brief's 52) were Excel lock files (`~$...`), not data. The profiler skips `~$` files.

### D-020 · All ratings normalised to 1–5 · Decided · 29 Oct 2026
- **Decision (owner):** every rating is converted to a 1–5 scale. 3-point word scales map Bad = 1, OK/average/medium = 3, Good = 5. Owner approved all the mappings below, including the 10-point rule and the Geelong 2025 reversal (D-030).
- **Mappings** (applied by `scripts/check_ratings.py`; full table in `reports/rating_check.md`):
  | Source scale | Where | Rows | Rule |
  |---|---|---:|---|
  | 1–5 numeric | most sites | 6,144 | unchanged |
  | 1–10 | Ringwood (from Feb 2026 template) | 321 | `round(1 + (x−1)·4/9)` → 1,1,2,2,3,3,4,4,5,5 (1–2→1, 3–4→2, 5–6→3, 7–8→4, 9–10→5) |
  | 5-point words | Ballarat | 292 | Very dissatisfied 1 … Very satisfied 5 |
  | Stars ★ | Bendigo | 144 | number of filled stars |
  | 3-point words | Tamworth | 143 | Bad 1 · OK 3 · Good 5 (owner rule) |
  | Reversed 1–5 | Geelong 2025 sheet | 68 | `6 − x` (sheet note: "1 = Excellent, 5 = Poor") |
  | Pivot counts | Toowoomba Q4 2025 | 71 | already 1–5 |
- **Sanity check result:** every value maps; no out-of-range, fractional or non-numeric ratings. Rows without a rating are dropped (D-031).
- **Caveats for reporting:** Tamworth's stretched 3-point scale can only produce 1, 3 or 5, so its mean (4.08) isn't strictly comparable with true 5-point sites. Report % positive alongside the mean, and run a sensitivity check (Good = 4). Noosa (feedback cards handed out by staff) averages 4.63, which is likely selection bias.

### D-028 · Penrith "Sales - New" and "Sales - Used" are one Sales department · Decided · 29 Oct 2026
- **Decision (owner):** both map to Sales in the Wave 3 department mapping.

### D-029 · Penrith "Jun 26" sheet is a copy of "Jul 26" · Decided · 29 Oct 2026
- **Finding:** all 43 rows of the "Jun 26" sheet are identical to "Jul 26", and its dates run 1–31 July 2026. Penrith's real June 2026 feedback is missing from the pack.
- **Decision (owner, accepted default):** exclude the "Jun 26" sheet (43 rows); report June 2026 as a coverage gap for Penrith (no imputation).

### D-030 · Geelong 2025 sheet uses a reversed scale · Decided · 29 Oct 2026
- **Finding:** the 2025 sheet's title says "Rating: 1 = Excellent, 5 = Poor"; the 2026 sheet says "1 = Poor ... 5 = Excellent (new head office scale)". Comments agree: in 2025, low scores carry the positive comments.
- **Decision (owner):** convert all 68 ratings on the 2025 sheet with `6 − x` (mean 2.40 → 3.60). Without this, Geelong would show a false jump of +1.4 between 2025 and 2026. The ingestion test suite must assert that the reversal is applied to this sheet only.

### D-031 · Drop rows that have no rating · Decided · 29 Oct 2026
- **Decision (owner):** a row without a usable rating is dropped, even if it has a comment.
- **Rows affected:** 13 in total. 10 genuine responses from Tamworth with a blank HOW WAS IT (7% of that file), plus 3 rows that are not feedback at all: a note in Shepparton ("Site closed 31/3/26 ..."), a note in Ringwood Q1 ("*** NEW TEMPLATE FROM FEB") and a test row in Southport ("asdf").
- **Why:** every analysis needs a score; 10 rows is too few to matter, and keeping score-less rows complicates trend and negative-rate calculations.
- **Recorded in the data-quality report:** count of dropped rows per file and reason.

### D-032 · Profiling findings: owner accepted all proposed defaults · Decided · 29 Oct 2026
Source: `agents/reports/w1_profilers.md` (15 findings). Wave 2 ingestion applies each of these.

| # | File(s) | Rule |
|---|---|---|
| 1 | Toowoomba Q4 2025 summary | Expand the pivot counts into 71 rows dated mid-month, no comment, flag `from_summary=true`; use in score trends, exclude from NLP |
| 2 | liverpool_q3_2026.csv | Parse dates month-first (US format); assert every date falls in Jul–Sep 2026 |
| 3 | Shepparton | 6 dates in Oct–Dec 2026 (after closure) treated as year typos → 2025, flag `date_corrected=true`; drop the note row |
| 4 | IPS_feedback_log | 10 vague dates ("early Oct", "wk1 Feb") assigned to the 1st/8th/15th/22nd/29th of the month, year from neighbouring rows, flag `date_approx=true` |
| 5 | Southport | Drop 3 test rows ("asdf", "TEST", 01/01/1900); exclude the "Google reviews (copied)" sheet |
| 6 | North QLD (Rocky + TSV) | Split into two dealers using the Site column (Rockhampton/Rocky/ROK, Townsville/TSV/Tsv) |
| 7 | Ringwood | Keep both templates; 10-point ratings mapped per D-020 |
| 8 | Bendigo, Tamworth, Ballarat | Stars, Good/OK/Bad and satisfaction words mapped per D-020 |
| 9 | Essendon | Department taken from the sheet name (Sales / Service / Parts) |
| 10 | Frankston | Drop the 12 monthly "Total ..." rows and blank separators; read both layouts |
| 11 | Dandenong | Header at row 4 of each monthly sheet; ignore the empty `Sheet3` |
| 12 | All | Department variants mapped in Wave 3 to Service / Sales / Parts; New Cars and Used Cars → Sales (and D-028) |
| 13 | Several | Extra columns ("Action", "Action taken", "Followed up?", "Source") dropped by the allowlist (D-003) |
| 14 | Geelong 2025 sheet | Reversed scale, `6 − x` (D-030) |
| 15 | Penrith | Exclude the "Jun 26" copy; June 2026 reported as a gap (D-029) |

### D-033 · PII sign-off (gate G4) without extra owner test cases · Decided · 29 Oct 2026
- **Decision (owner):** skip the brief's "owner adds 3 test cases" criterion because of time; the PII module is accepted as is.
- **Compensating controls:** owner read 40 redacted comments across two pilots and found no visible personal data in the second; automated leak check found 0 staff names and no real names left in the two pilot files; 41 synthetic fixture cases plus 9 allowlist and corpus-pass unit tests, including must-not-redact cases.
- **Residual risk (accepted):** a name used once, in lower case and absent from any staff column, can get through. Wave 2 adds a dataset-wide leak count to the data-quality report.

### D-034 · File → dealer code assignment, including the three files named after something else · Decided · 29 Oct 2026
- **Decision (owner):** every file is assigned its dealer code in `mappings/columns.yaml` at file level, by hand. The three files whose names do not contain their suburb are resolved as:
  | File | Dealer code | Dealership |
  |---|---|---|
  | `Hunter Motors feedback 25-26.xlsx` | NSW05 | Kestrel Newcastle |
  | `IPS_feedback_log.xlsx` | QLD03 | Kestrel Ipswich |
  | `North QLD feedback (Rocky + TSV).xlsx` | **QLD07 and QLD08** | Kestrel Rockhampton *and* Kestrel Townsville — one file, split by its `Site` column |
- **Evidence (not inference from the file names):**
  - Matching all 24 suburbs against all 52 file names leaves exactly four codes unmatched (NSW05, QLD03, QLD07, QLD08) and exactly three files unmatched — the three above. Newcastle is in the Hunter region; IPS is Ipswich; Rocky and TSV are Rockhampton and Townsville.
  - `Hunter Motors`: the `Dealer` column reads `HUNTER` on all 303 rows — one site, no split needed.
  - `IPS_feedback_log`: the `Site` column reads `KMG-IPS` on all 277 rows — one site.
  - `North QLD`: the `Site` column holds exactly six spellings across all four sheets — `Rockhampton`/`Rocky`/`ROK` (202 rows) and `Townsville`/`TSV`/`Tsv` (354 rows), totalling 556. No other values, so the split is exact.
- **Corrections to the owner's approval, recorded because the codes matter:** the owner wrote "QLD 02 Ipswich" — Ipswich is **QLD03**; QLD02 is Springwood, which has its own file (`Springwood feedback.xlsx`). The owner also wrote "QLD 07 is the combination of Rockhampton & Townsville" — QLD07 is Rockhampton **only** and QLD08 is Townsville; it is the *file* that combines the two. The table above is what the mapping implements.
- **Consequence for Wave 3:** with the file → code map approved by hand, no fuzzy matching of dealership names is needed, because no file contains a free-text dealership column that reaches the output (`Dealer` and `Site` are both dropped). `thresholds.dealer_match_min_confidence` in `config.yaml` can be retired rather than set. Wave 3's fuzzy matching is removed from scope unless a later file turns out to need it.

### D-035 · Department and rating normalisation stay in Wave 3; ratings convert at ingestion · Decided · 29 Oct 2026
- **Question asked:** should Wave 2's ingest agent also do Wave 3's department and rating normalisation, to save a handoff before the Friday freeze?
- **Decision (owner):** no — keep normalisation in Wave 3, with one exception that is forced by a decision already made.
- **What this means concretely:**
  - **Departments:** ingestion writes `department_raw` exactly as the source spelled it ("Svc", "SERVICE", "Workshop", "New Cars", "P&A", "SV", …). Wave 3 adds the `department` column by mapping those to Service / Sales / Parts. Nothing in Wave 2 depends on knowing which is which.
  - **Ratings:** ingestion must still convert to 1–5, because D-031 drops rows with no usable rating and that cannot be decided without reading and converting the rating. The conversion rules are already the owner's (D-020, D-030), so ingestion is applying an approved table, not making a judgement. Both `rating_raw` and `rating_1to5` are written, so the conversion stays auditable.
  - **Validation:** the pandera data-quality suite stays in Wave 3, written by a different agent. Under D-017 the agent that builds something does not grade it, and ingest grading its own output would weaken the evidence reviewers look for.
- **Why this split:** the schema (`src/schema.py`) carries `department` as an optional column, so Wave 3 fills it in without any change to the Wave 2 contract (gate G3 untouched).

### D-036 · Bendigo's letter codes are spelled out at ingestion · Decided · 29 Oct 2026
- **Question asked:** does Bendigo's `SV` / `S` / `P` mean Service / Sales / Parts? `S` was the weak one — 19 comments gave almost no signal and it was Sales only by elimination.
- **Decision (owner):** yes, and "it would be better to spell the whole word out so there is no confusion".
- **What this means:** `layouts.bendigo.department_map` expands SV → Service, S → Sales, P → Parts, and `department_raw` holds the word for Bendigo's 144 rows.
- **Tension with D-035, recorded deliberately:** this is the one place where ingestion rewrites a source value instead of passing it through, so `department_raw` is not literally raw for this one file. The owner asked for it, the map is three lines in the mapping file, and the source letter stays recoverable from `source_file` + `source_row`. Nothing else is rewritten.
- **Checked:** `scripts/check_mapping.py` now asserts that every department value the source actually uses has a map entry, that no map key is absent from the source, and that every expansion lands on Service / Sales / Parts. Tested by breaking it on purpose.

### D-037 · Southport's four non-feedback rows · Decided · 29 Oct 2026
- **Question asked:** one row had a valid rating (3, Sales) but no date, and was not covered by D-032 #5. Drop it, or date it as a midpoint?
- **Decision (owner):** "yes, the row was a test, so that can be removed along with the other testing rows", and count the `asdf` row as "summary or notes" as well.
- **Evidence that settles it:** the row's comment reads "testing new form". It is a test row, not lost feedback. Spreadsheet row 167 (the owner referred to it as 166; the row numbers in the draft and in the owner's reply were both off by one, which is why the mapping now records every junk row by its spreadsheet row number and its cell values).
- **The four rows, verified cell by cell:**
  | Spreadsheet row | Date cell | Dept | Rating | Comment | Reason |
  |---|---|---|---|---|---|
  | 23 | `01/01/1900` | Parts | 1 | `TEST TEST` | `test_row` |
  | 167 | *empty* | Sales | 3 | `testing new form` | `test_row` |
  | 196 | `TEST` | Service | 5 | `test - ignore` | `test_row` |
  | 192 | `asdf` | *empty* | *empty* | `asdf` | `summary_or_note` |
- **No double counting:** all three test rows carry a rating, so none of them is also a D-031 no-rating row. The `asdf` row is the no-rating one, and it is counted once, under `summary_or_note`, as the owner asked.
- **Privacy note:** these four comment values are the only comment-column values quoted anywhere in the repository. They contain no personal data, and the owner needs to see them to agree the rows are junk. The exception is stated in `columns.yaml` at the point of use.

### D-038 · Toowoomba Q4 2025 is Service and Parts only, at face value · Decided · 29 Oct 2026
- **Question asked:** the Q4 2025 summary has no Sales rows at all. Real, or an incomplete pivot?
- **Decision (owner):** "since there are no sales numbers, I will take face value of the Service & parts only."
- **What this means:** Toowoomba's Q4 2025 is reported as Service and Parts only, with a footnote. The 71 expanded rows carry `from_summary = true`, no comment, and the 15th of their month as the date.
- **What the footnote must say:** Toowoomba's Q4 2025 Sales feedback was not supplied. Its quarter-on-quarter comparison therefore shows a composition change, not necessarily a change in Sales performance.

### D-039 · Non-feedback rows are tagged "summary or notes" and dropped; the row budget is corrected · Decided · 29 Oct 2026
- **Question asked:** how should blank and "Total" rows be counted? The draft left the number to the pilot.
- **Decision (owner):** "the total rows are useless to me, tag them as 'summary or notes' and drop them."
- **Counted, not estimated (29 Oct 2026):**
  | Kind | Rows | Where |
  |---|---:|---|
  | Blank separator rows | 14 | Frankston 12 (7 + 5), Ringwood Q1 1, Shepparton 1 |
  | `Total <month>` rows | 12 | Frankston, one per month |
  | Notes typed into a data row | 3 | Shepparton closure note, Ringwood template note, Toowoomba "Grand Total" |
  - 0 blank rows in any of the 15 CSVs.
- **Correction to the draft budget — the important part:** the 14 blank and 12 `Total` rows are **not inside** the 7,162 profiled source rows. The Wave 1 profiler had already excluded them when it reported `data_rows`. The draft had them queued as a further subtraction, which would have made the reconciliation fail to close by 26 rows. They are now reported separately, as rows accounted for but never counted.
- **Revised arithmetic, which ingestion must land on exactly:** 7,162 source rows − 51 excluded sheets − 7 Toowoomba summary rows + 71 expanded rows = 7,175 candidates; − 16 dropped rows (10 no-rating, 3 summary-or-note, 3 test) = **7,159 rows out**.
- **The 13 rows of D-031 are unchanged** — they are the 10 Tamworth no-rating rows plus the Shepparton, Ringwood and Southport junk rows. The same 13 rows, now split into the reasons the owner asked for.

### D-040 · Ipswich's 10 vague dates are imputed from the rows around them · Decided · 29 Oct 2026
- **Decision (owner):** "in the IPS sheet, I am OK with the imputation of estimated dates using context clues from neighbouring rows."
- **The 10 values:** `early Oct`, `mid Nov`, `early Jan`, `wk1 Feb`, `wk5 Mar`, `early Apr`, `mid Jun`, `Aug?`, `Aug?`, `mid Sep`. They are the only non-date values in a column of 277.
- **Rule:** the log is kept in date order, so the day is the midpoint of the nearest dated row above and the nearest below, and the year comes with them. The written label supplies the month.
- **Cross-check, and why it matters:** label and position disagree for two rows — `mid Jun` sits between 30 May and 4 June, and `early Apr` between 20 and 23 April. Checked by hand for all 10: both signals land in the **same month** every time. Since every analysis is monthly, no published figure depends on which signal is trusted. The run fails if a future imputation falls outside the month its label names.
- **Flagged:** all 10 rows carry `date_approx = true`, so they can be excluded from any day-level claim.

### D-041 · Staff columns are dropped from the dataset and read in memory only · Decided · 29 Oct 2026
- **Owner's instruction:** "the 'staff' col can be dropped as well, it will not provide much useful info for the analysis."
- **Decision:** agreed and already true — the staff-name columns (`Staff`, `Taken by`, `Logged by`, `Card given by`, in 7 of the 31 layouts) never reach any interim or clean file, exactly like every other unmapped column under D-003. The mapping key is renamed from `staff_columns` to `redact_staff` so this reads correctly on the page, and the file now says so at the top.
- **The one thing that cannot be removed with them, and why:** those columns are what builds the `[STAFF]` roster that strips staff names out of the comment text (D-026). The PII pilot measured the effect — **728 of 5,412 comments, 13%, mention a staff-roster name**. Stop reading the columns and roughly 700 comments keep a named employee in them, and that text is what goes to the NLP and the client report. So the columns are read in memory and discarded, and no staff data is analysed, reported or written.
- **If the owner wants them gone entirely:** say so and the roster step is removed; the consequence is the ~700 comments above, and it would need recording as a change to D-026.

### D-042 · North QLD is split into QLD07 Rockhampton and QLD08 Townsville · Decided · 29 Oct 2026
- **Owner's instruction:** "the current North QLD feedback sheet needs to be split into Rockhampton and Townsville sheets individually — using their own site codes."
- **Decision:** implemented, and now explicit in the mapping rather than implied: `layouts.northqld.split` names both codes, both dealership names and both expected row counts, and `assert_split_counts` fails the run if either drifts.
- **Numbers:** 202 rows Rockhampton (QLD07) + 354 Townsville (QLD08) = 556, from the six `Site` spellings verified on 29 Oct 2026.
- **Consequence:** from the dataset onward the two are separate dealerships everywhere — reconciliation, charts and both reports — and the combined file name appears as a dealership nowhere. 24 dealerships must be present in the output, two of them from this one file.

### D-043 · Both Wollongong files are Windows-1252, not UTF-8 · Decided · 29 Oct 2026
- **Found:** 29 Oct 2026, while checking the owner's answers. Byte `0x92` — a curly apostrophe — appears inside the comment column of each file (offset 431 in `Wollongong_Apr26-Sep26.csv`, 402 in `Wollongong_Oct25-Mar26.csv`). The draft mapping declared `utf-8` for both.
- **Decision:** read both as `cp1252`.
- **Why it matters:** as UTF-8 the read raises `UnicodeDecodeError` and the dealership's 285 rows are lost. Forcing it with `errors="replace"` would be worse — it would corrupt apostrophes inside the comments that feed the sentiment and theme analysis, silently.
- **Encodings now declared per file:** UTF-8 for 12 CSVs, `utf-8-sig` for Bendigo (byte-order mark), `cp1252` for the two Wollongong files.

### D-044 · Owner's confirmations on the Wave 2 mapping review · Decided · 29 Oct 2026
- **Ringwood's second header is at row 37** — confirmed by the owner. The owner also noted that the split does not change what is needed, since the 1–10 → 1–5 conversion happens either way. It does change it for the 79 rows after row 37: read as out-of-5 they would all look like top scores, which is why the mapping keeps two layouts and the pilot checks both halves.
- **Shepparton's six 2026 dates** — "nothing to change". D-032 #3 stands: treated as year typos, moved to 2025, flagged `date_corrected`.
- **Dandenong's booking-system note** — "just keep the note as contextual evidence of performance. There is no relevant numerical data in that row anyway." Recorded in `reports/formatting_changes.md` and to be cited in the trend section if Dandenong dips from May 2026.
- **Checkpoint 2 (gate G3) passed** — the owner approved the revised `mappings/columns.yaml` on 29 Oct 2026 and authorised the pilot on the five awkward dealers. Nothing reaches `main` without the owner's review (G5).
- **`thresholds.trend_evidence` stays TBD by the owner's choice** — the owner asked to set it after seeing the actual month-by-month volumes and spreads, so the evidence comes first and the number follows. Gate G7 still blocks trend results until it is set and committed.

### D-045 · A register of formatting inconsistencies is a deliverable in its own right · Decided · 29 Oct 2026
- **Owner's instruction:** "note where all the formatting changes are across all worksheets — I will add them to the client report."
- **Decision:** `reports/formatting_changes.md` — 13 kinds of inconsistency across 52 files and 84 worksheets, each located by dealership, with counts and the treatment applied, written to be lifted into the client report. No comment, name, phone, email or plate value is quoted in it.
- **Why it is worth its own document:** the inconsistency is itself a finding for Kestrel. 19 spellings of 3 departments, 8 ways of writing a date and 7 rating scales across 24 dealerships is the absence of a group standard, not 24 separate quirks. Three of the inconsistencies — Geelong's reversed scale, Ringwood's mid-sheet change to a 10-point scale and Liverpool's one month-first quarter — would have moved a published dealership score with nothing appearing broken.

## Outputs

### D-007 · Two reports · Decided · 29 Oct 2026
- **Decision:** (1) a non-technical business report for the Head of CX; (2) a technical report (`README.md`) for reviewers. The business report links to the technical one.

### D-008 · Non-negotiable outputs · Decided · 29 Oct 2026
- One cleaned dataset; at least one trend; basic NLP of comments; at least one business recommendation; the technical report. Everything else is on the cut list (PLAN.md §10).

### D-009 · Deadline · Decided · 29 Oct 2026
- Code freeze Friday 30 Oct 2026, 3:00pm; proofread and edit until COB.

## Technology

### D-010 · Zero-budget, open-source stack · Decided · 29 Oct 2026
- **Decision:** No paid APIs. All NLP uses open-source models run locally or in the Claude workspace. Claude is used as the coding/orchestration assistant under the owner's existing subscription.
- **Why:** project is self-funded; open-source also keeps comment text inside environments the owner controls.

### D-011 · NLP approach: fast deterministic core + optional local LLM · Decided · 29 Oct 2026
- **Core (covers the non-negotiables):** pretrained sentiment model + embedding-based theme assignment to a human-approved theme list, run on all comments.
- **Add-on:** a 3B open-source LLM via Ollama, run only on negative/mixed comments plus the hand-labelled sample.
- **Cut-off rule:** time a 20-comment pilot. If the projected run is under ~2 hours, run it in full (overnight Thursday). Otherwise run it on the labelled sample only and report it as a method comparison.
- **Options considered:** paid LLM API (rejected — no budget); LLM on all comments (rejected — too slow on CPU); no LLM (kept as fallback).

### D-012 · Run Ollama in Docker on the owner's laptop; no Google Colab · Decided · 29 Oct 2026
- **Hardware:** Windows, Intel i7, 60 GB RAM, no GPU. Docker Desktop via WSL2.
- **Decision:** Ollama in Docker, CPU-only, model pinned by exact tag in `docker-compose.yml`; `.wslconfig` gives WSL2 a fixed memory/CPU share.
- **Why:** Colab previously hit usage limits and caused more problems than it solved. Docker gives reviewers the same model via `docker compose up`.

### D-013 · Processing split: workspace + laptop · Decided · 29 Oct 2026
- **Decision:** Profiling, joining, cleaning, analysis and charts run in the Claude cloud workspace (a sandboxed Linux environment). The Ollama LLM step runs on the laptop.
- **Data handling:** raw files are shared with the workspace. Justification: the brief states all data is fictional; identifier columns are dropped at first ingestion; only redacted text is passed to any model.
- **Agents do not run directly on the laptop** — the cloud workspace is already isolated from personal files.
- **Open risk:** the workspace network may block Hugging Face model downloads; the Wave 1 NLP environment check decides whether sentiment/embedding models also move to the laptop.
- **Wave 1 environment check result (29 Oct 2026):**
  - Workspace: Hugging Face blocked (HTTP 403); PyPI and the PyTorch index also unreachable, so new Python packages cannot be installed and `uv.lock` cannot be generated there. GitHub reachable. Pre-installed: pandas, openpyxl, pydantic, scipy, scikit-learn, matplotlib, seaborn, pytest. Missing: spaCy, pandera, duckdb, pyarrow, rapidfuzz, statsmodels, pre-commit.
  - Laptop: Ollama in Docker works. Image `ollama/ollama@sha256:20d1bbfb…12d0b`, model `qwen2.5:3b` (ID `357c53fb659c`), 12.83 tokens/s on a one-sentence test. WSL2 limited to 8 CPUs / 24 GB.
  - **Consequence:** sentiment and embedding models move to the laptop. The laptop becomes the reference environment for `uv lock`, `uv sync` and `make all`.
- **Revision (29 Oct 2026, owner approved):** "Agents do not run directly on the laptop" is replaced by the working arrangement below.
  - **Options considered:** (A) split by installed libraries; (B) owner runs everything and pastes output; (C) Claude runs commands on the laptop via the desktop-app bridge, scoped to one folder; (D) carry wheels and models into the workspace by hand; (E) swap to pre-installed libraries. C was chosen, then tested: the bridge shell is a Linux sandbox on the laptop that sees only `C:\PS-Kestral-Group` (2 CPUs, 3 GB, Python 3.10 with pandas/openpyxl) and has no PyPI, Hugging Face, GitHub, Docker or Ollama access. C therefore became a B/C hybrid.
  - **Arrangement:**
    - Claude writes code in the cloud workspace clone and pushes to the agent's branch.
    - The owner runs anything needing installs, models or Docker in Windows PowerShell inside `C:\PS-Kestral-Group`, saving output to `logs\` (gitignored). Claude reads those logs through the bridge.
    - Claude does not edit tracked files in the laptop folder, so `git pull` there never conflicts. Lock files generated on the laptop (`uv.lock`) are committed and pushed by the owner.
    - Profiling and other pandas/openpyxl-only work runs in the cloud workspace.
  - **Scope limits:** bridge access is limited to `C:\PS-Kestral-Group`. Claude runs no Docker commands; the owner runs `docker compose` for this project only.
- **Revision 2 (29 Oct 2026, afternoon):** the "owner runs, Claude reads logs" arrangement above was a workaround for a sandboxed bridge shell with no Python 3.12 and no project environment. The Claude Code session running in the desktop app does not have that limitation: it works directly in `C:\PS-Kestral-Group`, runs `uv` (0.13.6) and the project virtual environment, and so can execute the pipeline and the tests itself.
  - **Arrangement from here:** Claude writes code and runs it in the laptop repository on the agent's own branch, including `pytest`, `ruff`, `pre-commit` and the pipeline stages. The owner still runs anything involving Docker or Ollama, and still reviews and merges every branch (G5).
  - **Why it changed:** the log round-trip cost roughly a full cycle per command with a Friday 3pm freeze, and the reason for it no longer applied once the session had a working environment.
  - **What did not change:** the gates. Nothing reaches `main` without the owner's review, the owner still approves each brief and each threshold, and raw data still never enters git (now enforced by a pre-commit hook as well as `.gitignore`).
  - **Unchanged constraint:** Hugging Face and PyPI remain unreachable from the cloud workspace, so the laptop stays the reference environment for `uv lock`, `uv sync` and the NLP models.

### D-014 · Tech stack · Decided · 29 Oct 2026
- See PLAN.md §5. Key reasons: `uv` for exact reproducibility; Parquet + DuckDB for typed, inspectable stages; pandera for declarative validation; cached model outputs committed so results reproduce without re-running models.

### D-015 · Repository visibility · Decided · 29 Oct 2026
- **Decision:** private repo (`gdawg95/PS-Kestral-Group`) until reviewers approve; then public. Owner is the only human contributor.
- **Before going public:** `gitleaks` + PII scan of full git history. Raw data is gitignored from the first commit because history cannot be cleaned easily later.

## Process and controls

### D-016 · Human-in-the-loop gates · Decided · 29 Oct 2026
- **Hard gates (always block):** G1 pilot before scaling · G2 approve agent plan before it acts · G3 no schema/mapping change without approval · G4 confirm redaction before data reaches any model · G5 review before every merge · G7 owner sets and commits every threshold before results · G9 owner approves every chart before it enters a report.
- **Why:** reviewers assess how AI was controlled and verified; each gate leaves evidence (brief, report, verdict, commit).

### D-017 · Agent operating rules · Decided · 29 Oct 2026
- One branch/worktree per agent; orchestrator merges after owner review.
- Only ingestion agents touch `data/raw/`.
- Producer ≠ checker: the agent that builds something never grades it; an independent verifier runs a clean reproduction before freeze.
- The hand-labelled evaluation sample is labelled by the owner, blind to model output. Any few-shot prompt examples must not come from that sample.

### D-018 · Separate conversations per phase, shared state in files · Decided · 29 Oct 2026
- Each phase runs in its own conversation. `PLAN.md`, `DECISIONS.md` and `AI_LOG.md` live in the repo and in the Claude project so every conversation starts from the same state. Benchmark research runs in its own conversation.

## Deferred

| ID | Decision | Revisit |
|---|---|---|
| D-019 | Duplicate check result (confirms or overturns D-002 assumption) | After Wave 2 |
| D-021 | Evidence threshold for calling a trend real | After basic EDA |
| D-022 | NLP pass mark (e.g. sentiment agreement ≥ X%, theme F1 ≥ Y) and fallback | Before hand-labelling |
| D-023 | Final theme list (fixed + discovered mix) | After theme discovery |
| D-024 | LLM in or out | After the 20-comment pilot |
| D-025 | Value benchmarks and assumptions (low/mid/high) | Wave 5 |

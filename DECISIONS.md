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
| 4 | IPS_feedback_log | 10 vague dates ("early Oct", "wk1 Feb") assigned to the 1st/8th/15th/22nd/29th of the month, year from neighbouring rows, flag `date_approx=true` — **superseded by D-040**, which takes the day from the midpoint of the nearest dated rows above and below instead of a fixed day. D-040 is what the code does; `reports/date_edge_cases.md` shows the neighbours for all 10 |
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

### D-046 · Gate G1 passed: the owner checked the pilot and confirmed the Geelong reversal from the data · Decided · 29 Oct 2026
- **What the owner checked**, from `reports/reconciliation.md` and the spreadsheets themselves:
  1. **Geelong 2025 — "rating of 1 are praises so the reversal is right."** This is the important one. Until now D-030 rested on a sheet title ("1 = Excellent, 5 = Poor"), which is one person's note, plus the AI's reading of which comments carried which scores. The owner has now read rows scored 1 in the source workbook and confirmed they are praise. **The reversal is evidence-backed, not inferred.** Geelong's 2025 mean moves 2.40 → 3.60 and the 2026 sheet is untouched at 3.82; without the reversal Geelong would show a false +1.4 jump between years.
  2. **The three dropped rows are correct** — "non informative to the analysis". They are Ringwood Q1's blank row and its "*** NEW TEMPLATE FROM FEB" note, and Toowoomba's "Grand Total" row.
  3. **Rockhampton's low mean (3.52, the lowest of the six pilot dealers) is plausible** — "it seems to be a weakest site thus far from the small sample size. I think more information will be revealed by the full ingestion." So the 202 / 354 split is accepted as correct and the low score is treated as a finding to confirm on the full dataset, not as a symptom of a split error.
- **Decision:** gate G1 is passed. The remaining 18 dealerships are ingested on the same code and the same mapping.
- **Carried forward to Wave 5:** Rockhampton (QLD07) is a candidate for the weakest-performing site. It must be re-checked against all 24 dealerships before it appears in either report, and against the volume floor in `thresholds.trend_evidence`, since 202 rows across 12 months is a median of 17 a month.
- **What this does not cover:** the owner checked the pilot's six dealer codes. The 18 dealerships ingested afterwards were not individually reviewed; the evidence for those is the reconciliation's arithmetic, the four D-002 join proofs and the test suite, not a human read of each file.

### D-047 · Springwood duplicates: drop the second row of each pair · Decided · 29 Oct 2026
- **Closes D-019.** Wave 2's exact-match duplicate check found 9 groups, all in
  `Springwood feedback.xlsx` (QLD02), each a pair sharing dealership, date, department,
  rating and comment text, and **every pair on consecutive spreadsheet rows** (source
  rows 18/19, 16/17, 30/31, 61/62, 95/96, 137/138, 139/140, 163/164, 186/187). One pair
  repeats a 463-character comment.
- **Decision:** drop the second row of each pair — 9 rows. Flag them as their own rule in
  the data-quality waterfall with a count of 9, and state Springwood's mean both ways in
  the report so the choice is auditable.
- **Effect, measured before deciding:** 310 → 301 rows; mean 4.0032 → 4.0100; negative
  rate (≤2) 17.10% → 16.94%; Springwood stays 3rd of 24 by mean either way. The brief had
  warned this "moves a dealership's published score"; it does not, so the decision was
  taken on correctness grounds rather than on its effect on the number.
- **Why it still matters:** the effect lands in Wave 4, not Wave 5. Two of the nine pairs
  are negative (ratings 2 and 2), one of them the 463-character complaint, so keeping both
  copies would double-weight that customer in theme frequencies and sentiment — the exact
  quantity the business question asks about.
- **Not treated as duplicates:** the 85 comment-less rows across 16 dealerships that match
  on everything else (only 60% adjacent — consistent with two customers rating Service 5
  on the same busy day), and the 63 rows identical by construction from the Toowoomba pivot
  (D-032 #1). Both are reported, not removed.

### D-048 · "Workshop" is Service; the six service spellings are one department · Decided · 29 Oct 2026
- **The concern:** "Workshop" covers 311 rows at 10 dealerships with a mean of 3.86 against
  plain "Service" at 3.51 — a 0.35 gap worth checking before it was folded away.
- **Decision:** map `Workshop` to Service, with the other five spellings (`Service`,
  `SERVICE`, `Service Dept`, `service`, `Svc`). One decision covers 4,909 rows.
- **Evidence, not assumption:**
  1. All 10 sites that write "Workshop" use **all six** spellings, in near-equal sixths
     (18.4% / 17.6% / 16.7% / 16.3% / 15.6% / 15.4%). This is row-level spelling variation
     inside the same sheets, not 10 sites that name the department differently. No site
     uses "Workshop" and "Service" as though they were different things.
  2. The 0.35 gap is mostly a between-dealer artifact: the 3,300-row "Service" bucket is
     dominated by the 14 sites that only ever write "Service" (n=3,006, mean 3.503).
     Comparing within the 10 sites that use both, the gap falls to +0.231.
  3. Across all six spellings inside those 10 sites, **one-way ANOVA gives F=1.55,
     p=0.170** — not significant. Workshop is the highest of six statistically
     indistinguishable groups. Testing it alone against the pooled other five returns
     p=0.008, but that is the artifact of choosing the winner before testing it.
  4. Per site the ordering is inconsistent: Workshop is above that site's other-service
     mean at 7 of 10, below at 3. NSW05's Workshop is its lowest spelling; NSW06's is its
     highest; VIC09's is 2 rows with a mean of 1.0.
  5. Content agrees: 37.4% of Workshop comments use service vocabulary (bookings, loan
     cars, technicians, invoices) against 34.1% of Service comments, and 1.7% use sales
     vocabulary against Sales' 12.5%.

### D-049 · One Sales department; the new/used subtype is carried but not published · Decided · 29 Oct 2026
- **Decision:** every headline number uses a single Sales department. `departments.yaml`
  keeps `subtype: new` / `subtype: used` for traceability. No new-versus-used cut appears
  in either report unless it is asked for, and if it is, it carries the caveat below.
  Consistent with D-028, which already folded Penrith's two Sales spellings into one.
- **Scale:** 326 of 1,544 Sales rows (21%) carry the distinction, at 11 of 24 sites.
- **Why not publish it:**
  1. The gap is not significant — new 4.457 (n=162) vs used 4.311 (n=164), **Welch
     p=0.221**.
  2. The direction does not hold per site: new higher at 6 sites, used at 3, tied at 2.
     Four of the 11 sites contribute fewer than five rows. Penrith (NSW02) is 35% of all
     subtype data and has used marginally *ahead* (4.27 vs 4.22), opposite to the pooled gap.
  3. **The self-selection is measurable.** The 11 sites that record the subtype have a
     higher Sales mean than the 13 that do not: 4.354 (n=628) vs 4.192 (n=916), **Welch
     p=0.006**. A group-wide new-versus-used claim from those rows would be reporting that
     selection effect, not a difference between new and used.

### D-050 · Checkpoint 3: `mappings/departments.yaml` approved · Decided · 29 Oct 2026
- The owner reviewed the 16 department spellings and approved the mapping to
  Service / Sales / Parts, including the two substantive calls recorded as D-048 and D-049.
- `mappings/departments.yaml` moves from `draft` to `approved (Checkpoint 3)`. Gate G3
  applies from here: any further change to it needs the owner's approval.
- Totals the fill must reproduce: **Service 4,909 · Sales 1,544 · Parts 706 = 7,159**,
  asserted by `uv run python scripts/check_departments.py`.
- **Still open at the end of this review:** the `w3_validate` brief itself has not been
  approved (gate G2). The four questions it asked are answered; the brief is not yet signed.

### D-051 · The "<customer name> – <note>" comment opening is redacted structurally · Decided · 29 Oct 2026
- **Owner's instruction:** the owner confirmed that rows 35 and 40 of `IPS_feedback_log.xlsx`
  do contain real names and asked for them redacted before Wave 4.
- **What was actually wrong.** Both rows use a convention several logs share — the comment
  opens with the customer's own name, then a dash, then the note:
  *"Carmen Gomes - Reckons [STAFF] made it all easy to understand."* **55 of the 5,386 raw
  comments are written that way.** spaCy caught 52 of them, but only because the customer's
  first name also appeared in some file's name column; where it did not, the sentence-start
  guard in `_redact_people` (a deliberate false-positive brake — spaCy tags "Spooky",
  "Keys", "Lovely" as PERSON at the start of a sentence) let the name through.
- **A third leak was found this way:** `Yianni Pappas`, which the Wave 2 report had not
  identified. The owner knew about two; there were three.
- **Decision:** redact the opening by its shape rather than by the roster. `pii.NAME_PREFIX`
  matches two or three capitalised tokens at the start of a comment followed by a dash, and
  replaces them with `[NAME]`, before the staff roster and spaCy see the text — so the
  person giving the feedback is `[NAME]` (a customer) even when they share a first name with
  a staff member.
- **Why two tokens and not one.** A single leading capitalised word is ordinary prose. The
  rule was sized against the corpus before being written: the two-token shape matches 55
  comments and every one is a real name; the one-token shape matches only
  `"Sarcastic - ..."` (4 comments), which is not a name. Precision on this data is 55/55.
- **No names are stored anywhere.** The alternative — a list of confirmed names in a
  committed YAML file — would have put real names into git history, which is exactly what
  D-003, D-026 and the pre-public scan (D-015) exist to prevent. A structural rule needs no
  such list.
- **Gate G3 exception, authorised by the owner.** `src/pii.py` belongs to Wave 1 and the
  `w3_validate` brief says propose, do not edit. The owner instructed this change directly,
  so it was made, tested and re-run rather than proposed.
- **Effect, verified:** `python -m src.ingest` re-run in full. **7,159 rows, 24 dealerships,
  5,362 comments — identical to before**; only comment text changed. 8 new tests in
  `tests/test_pii.py` (69 passed, 2 skipped). The reconciliation's leak check now reports
  **0 probably-real missed names, down from 2**, and no comment in the dataset still opens
  with a name.

### D-052 · `thresholds.trend_evidence` is set; `dealer_match_min_confidence` is retired · Decided · 29 Oct 2026
- **Closes D-021,** on the evidence in `reports/trend_evidence.md` rather than ahead of it
  (D-044, gate G7). Committed before any trend result exists.
- **The rule:**
  | Setting | Value |
  |---|---|
  | `min_month_responses` | 20 — below this a dealership's month is reported as a count, never as a movement |
  | `min_change_1to5` | 0.5 — the smallest month-on-month change reported as a trend |
  | `thin_dealer_basis` | `quarterly` — NSW07, QLD05, QLD07, VIC08 and VIC09 have a median month under 20 and are compared by quarter instead, so they appear in the trend section rather than being silently dropped |
- **Why these numbers.** Ratings have SD 1.44 across 7,159 rows, so a change between two
  20-response months carries ±0.46 of noise; 0.5 sits just outside it. The rejected
  candidate — 10 rows and 0.5 stars — would have called a move inside its own ±0.64 noise
  band a trend. 74% of dealer-months have 20 or more responses, so the floor keeps most of
  the data. The rule calls 33 of 257 consecutive month pairs a trend, at 16 of 24 sites:
  enough to report, not so many that everything looks like a trend.
- **`dealer_match_min_confidence` is removed from `config.yaml`, not given a value.** It was
  the confidence floor for PLAN.md's Wave 3 "dealership matching" agent, which was to
  fuzzy-match free-text dealership names to official codes. That agent has nothing to do:
  D-034 approved the file → dealer code map by hand, and no free-text dealership column
  survives ingestion (D-003), so there are no strings to score. Leaving it as `TBD` would
  have read as an unresolved threshold for the rest of the project.
- **Still `TBD`:** `nlp_pass_mark` only (D-022, Wave 4 — set later the same day, see D-055).

### D-053 · Checkpoint 3: the 16 corrected and imputed dates are approved · Decided · 29 Oct 2026
- **Owner's words:** "the 16 date rows - i approve the changes."
- **What was approved:** all sixteen rows whose date the pipeline changed or invented, read
  with their source values beside them in `reports/date_edge_cases.md` — not a sample of
  twenty arbitrary rows, but every row of this kind in the dataset.
  - **6 rows, Shepparton (VIC09), `date_corrected`.** Dates in Oct–Dec 2026, after the site
    closed on 30 Mar 2026, with the day and month plausible for a year earlier. Read as year
    typos and moved to 2025 (D-032 #3). One consistent pattern across all six.
  - **10 rows, Ipswich (QLD03), `date_approx`.** The only non-date values in a column of
    277: `early Oct`, `mid Nov`, `early Jan`, `wk1 Feb`, `wk5 Mar`, `early Apr`, `mid Jun`,
    `Aug?`, `Aug?`, `mid Sep`. The day comes from the midpoint of the nearest dated rows
    above and below, the year with them, the month from the written label (D-040).
- **What the review added that the earlier report could not show.** The source value does not
  survive ingestion, so `reports/data_quality.md` could only print the resolved date, which
  is an assertion rather than evidence. `scripts/date_edge_cases.py` reads the two raw
  workbooks read-only and puts the source text and the bracketing dated rows beside each
  row. Every one of the ten is bracketed within a few days.
- **It also corrected the AI's own framing.** The two `Aug?` rows had been flagged to the
  owner as the weakest of the set, on the reasoning that a question mark is doubt about the
  month rather than the day. They are the best supported: row 248 sits between two rows both
  dated 12 Aug, leaving nothing to guess. The rows where label and day genuinely disagree are
  `mid Nov` (resolved to the 3rd) and `early Apr` (the 21st) — D-040's own cross-check, and
  label and position agree on the *month* for all ten, which is the only thing a monthly
  analysis uses.
- **Flags stay on.** All 16 rows keep `date_corrected` / `date_approx`, so any day-level
  claim can exclude them. No published figure in this project is day-level.
- **Checkpoint 3 after this:** `departments.yaml` approved (D-050), the Springwood duplicates
  decided (D-047), the dates approved here. What remains is the data-quality waterfall and
  the five example rows per rule, which need the full validate run over all 7,159 rows —
  gate G1 still holds it.

### D-054 · The corpus name pass may not promote ordinary words, and no pass may rewrite a redaction token · Decided · 29 Oct 2026
- **Owner's instruction:** fix it now, before Wave 4.
- **The defect, found while reviewing the diff before committing Wave 3.** The redaction
  table in `reports/reconciliation.md` reported 58 `[EMAIL]` redactions; the dataset
  contained zero `[EMAIL]` tokens. Both numbers were right, which is what made it worth
  chasing.
- **Two causes, and the second is the dangerous one.**
  1. `promote_names` judges a candidate only on how often spaCy tagged it and how often it
     is capitalised. A vehicle model and a sentence-initial "Email" pass both tests as
     surely as "Dave" does. It promoted seven tokens that are not people: `Email` (85
     comments), `Corsa` (73), `Terra` (57), `Ridge` (41), `Madam` (8), `Easter` (2) and
     `Crsa` (2) - **268 comments, 5% of the corpus**, with an ordinary word replaced by
     `[NAME]`.
  2. A promoted name is replaced by whole word, case-insensitively, and the brackets of
     `[EMAIL]` are not word characters - so `EMAIL` is a whole word *inside the token*.
     Promoting "Email" therefore rewrote every one of the 58 redacted addresses into
     `[[NAME]]`. One pass silently destroyed another pass's output.
- **Not a privacy failure.** Both faults over-redact. No email address, name or other
  identifier escaped; the information lost is ordinary English and the names of cars.
- **Why it mattered anyway:** Wave 4 runs theme discovery over this text. "Email" sits in
  the booking-and-contact complaints and `Corsa`, `Terra` and `Ridge` are what customers
  call the cars they are complaining about, so the themes would have been built from text
  with its most distinctive nouns blanked out - and would have looked perfectly healthy.
- **Decision:**
  - `pii.NOT_PROMOTABLE` extends `NOT_NAMES` with the seven, plus `Vista`, `Altura` and
    `Kodiak` for the same reason, and `promote_names` skips any candidate in it.
  - **The list deliberately does not touch the spaCy pass.** A customer could be named
    Ridge, and spaCy redacts a token when the sentence makes it a person ("Ridge said he
    would call"). Only the blanket, case-insensitive pass is blocked. Under-redaction is
    the failure that matters, so the fix is scoped to the pass that cannot read context.
  - Every case-insensitive whole-word pattern now carries `(?<![\w\[])` / `(?![\w\]])`, so
    no pass can match inside an existing token. This is the general guard; the list above
    is the specific one, and the guard is what would have contained the damage if the list
    had been wrong.
- **Gate G3 exception, authorised by the owner**, as D-051 was: `src/pii.py` is a Wave 1
  module and this re-runs redaction over all 5,362 comments.
- **The fix took three parts, each found by checking the result of the one before:**
  1. `pii.NOT_PROMOTABLE` — the corpus pass skips any candidate in it. Blocking "email"
     alone restored all 58 `[EMAIL]` tokens and the word in all 85 comments.
  2. **A token guard on every case-insensitive whole-word pattern** —
     `(?<![\w\[])` / `(?![\w\]])`, so no pass can match inside an existing `[TOKEN]`. This
     is the general defence, and it is what would have contained the damage if the list in
     part 1 had been wrong.
  3. **A per-token non-name check in the spaCy pass.** Listing the models was not enough:
     spaCy tags **"Altura Corsa"** — brand plus model — as a single PERSON in 31 comments,
     and the existing check only compared the whole surface string against `NOT_NAMES`. An
     entity whose every token is a known non-name is now skipped. Fragments of one
     character are ignored, so `Altura Corsa's` passes too; an initial still leaves a
     surname, so "J. Smith" is unaffected.
- **Verified, after four re-ingestions:**

  | | Before | After |
  |---|---:|---:|
  | `[EMAIL]` tokens in the dataset | 0 of 58 applied | **58 of 58** |
  | `[[NAME]]` (a token inside a token) | 58 | **0** |
  | `[NAME]` tokens | 559 | 162 |
  | Comments containing "email" | 0 of 85 | **85 of 85** |
  | Comments containing "corsa" / "terra" | 0 of 73 / 0 of 57 | **73 of 73 / 57 of 57** |
  | Comments containing "ridge" | 0 of 41 | **40 of 41** |
  | Residual probable missed names | 0 | **0** |

  **The one remaining "ridge" is not redaction.** `Tamworth.xlsx` row 135 — "THANK YOU FOR
  EXPLAINING MY SERVICE SO CLEARLY. I UNDERSTAND NOW WHY THE WORK WAS NEEDED ON MY RIDGE."
  — has no rating and is one of the 10 rows dropped under D-031. The word is intact in the
  source and absent from the dataset because the row is.
- **Nothing else moved.** 7,159 rows, 24 dealerships, 5,362 comments before and after;
  7,150 rows and Service 4,903 / Sales 1,541 / Parts 706 after validation; `[STAFF]` 739,
  `[PHONE]` 156 and `[REGO]` 477 unchanged; residual leak still 0. Only comment text
  changed, which is the whole point.
- **Tests:** 20 new cases in `tests/test_pii.py` (69 → 89), including one per blocked word,
  one asserting a real name is still promoted, one per token asserting it cannot be
  rewritten by a name matching its own text, the "Altura Corsa" entity, the possessive, and
  a real two-word name redacted beside a model.

## Outputs

### D-055 · `thresholds.nlp_pass_mark` is set: Cohen's κ ≥ 0.60 on a 150-comment stratified sample · Decided · 29 Oct 2026
- **Owner's words:** "Set κ ≥ 0.60".
- **Closes D-022,** on the evidence in `reports/nlp_pass_mark_evidence.md` rather than ahead
  of it (gate G7). Committed before any evaluation result exists, and before the
  hand-labelling that would produce one.
- **The rule:**
  | Setting | Value |
  |---|---|
  | `metric` | `cohens_kappa` — chance-corrected agreement, not raw agreement |
  | `sentiment_min_kappa` | 0.60, on three-class sentiment (negative / neutral / positive) |
  | `sample_size` | 150 comments |
  | `sample_stratified` | `true` — roughly 50 / 50 / 50 by score class, weighted back to the true distribution for any headline figure |
  | `theme_bar` | `TBD` — the share of theme assignments judged defensible, set once the theme list is fixed (D-023) |
  | `fallback` | `score_only` — if κ < 0.60, D-004's rating signal is primary and sentiment is reported as a method comparison with its κ stated |
- **This supersedes the default proposed in `agents/briefs/w3_validate.md` Q4** — "sentiment
  agreement ≥ 80% on a 100-comment hand-labelled sample, with the fallback being rule-based
  sentiment only". That default was written before the baseline evidence existed, and the
  evidence the same agent then produced argues against it on both counts.
  - **The metric.** The commented rows are 59.3% positive, so a model that answers
    "positive" to every comment scores 59.3% raw agreement. An 80% bar therefore sits only
    21 points above a model that does not read the text, and can be cleared while getting
    the negative class — the entire business question — badly wrong. Chance agreement on
    these marginals is 0.447, so 80% raw agreement corresponds to κ ≈ 0.64: a κ floor of
    0.60 is very nearly the same bar for a model that genuinely works, and it is what fails
    the always-positive model, which scores κ = 0.
  - **The sample size.** At 100 comments the 95% confidence half-width on an agreement
    estimate near 80% is ±7.8pp, so a 100-comment sample cannot distinguish 80% from 72%
    — the ruler is wider than the margin being judged. 150 narrows it to ±6.4pp. Drawn at
    random, 100 comments also yield only about 13 neutral and 28 negative examples, so both
    minority classes would be measured off a handful of rows. Stratifying is what makes the
    negative class measurable.
- **Why there is no theme bar yet.** D-022 mentions a theme F1. A credible per-theme F1
  across roughly 8 themes is not available from 150 comments — some themes would have
  three examples. The bar that a sample this size can defend is the share of assigned
  themes judged defensible on the same comments, and that cannot be set before the theme
  list exists (D-023). A real theme F1 needs its own sample, sized after theme discovery,
  and is a candidate for the cut list.
- **What this does not change:** the owner still labels the sample blind to model output,
  and the agent that produces the classification is not the one that grades it (D-017).

### D-056 · The `unassigned` similarity floor is set from the observed distribution, not chosen in advance · Decided · 29 Oct 2026
- **Owner's answer to `agents/briefs/w4_classifier.md` Q1:** set it after assignment.
- **The decision.** The classifier assigns every comment to its nearest approved theme by
  cosine similarity and records that similarity. The floor below which a comment becomes
  `unassigned` is set by the owner *after* seeing the similarity distribution with example
  comments at each decile, and committed to `config.yaml` before any Wave 5 number uses it.
- **Why not a number now.** Cosine values depend on the embedding model and on how the theme
  descriptions in `mappings/themes.yaml` are worded — and neither is fixed until the owner
  approves the theme list. A floor chosen blind could put anywhere between none and 40% of
  comments into `unassigned`, and which it was would not be knowable until it ran.
- **Why this does not breach gate G7.** G7 stops a bar being moved *after seeing how the
  model scored* — it protects the verdict. The similarity distribution is a property of the
  comment text and the theme wording, not a result: no negative rate, driver count or
  recommendation exists or changes while it is inspected. This is the same move D-052 made
  for `trend_evidence`, which derived 0.5 stars from the measured SD of 1.44 in
  `reports/trend_evidence.md` and was still committed before any trend result existed.
- **Closed 30 Oct 2026 — see D-066.** The owner's 150 blind labels were used to test the
  mechanism and it does not separate the comments they rejected from the ones they kept, so
  the floor is retired rather than set.
- **Audit hardening.** The distribution is reviewed with comment text visible but with no
  dealership or theme-count breakdown, so the floor cannot be influenced by which site it
  would flatter.

### D-057 · Rows without a comment carry null sentiment, never "neutral" · Decided · 29 Oct 2026
- **Owner's answer to `agents/briefs/w4_classifier.md` Q2:** null.
- **The evidence.** 1,797 of the 7,150 clean rows have no comment. Their ratings are not
  neutral — they are overwhelmingly positive:

  | Rating | No comment | Has comment |
  |---|---:|---:|
  | 1 | 3.7% | 16.9% |
  | 2 | 2.2% | 11.2% |
  | 3 | 5.7% | 12.6% |
  | 4 | 27.0% | 19.9% |
  | 5 | 61.4% | 39.3% |

  Of the 1,797: **105 negative (1–2), 103 neutral (3), 1,589 positive (4–5)**. Labelling
  them all "neutral" would mislabel **1,694 of 1,797 — 94.3%** — almost entirely by
  recoding satisfied customers as indifferent ones, and would inject 1,589 invented
  neutrals into every sentiment total and every theme denominator.
- **Nothing is lost by null.** D-004 already makes the rating the minimum signal precisely
  because many customers leave no comment. The 105 negative-by-rating rows still count as
  negative feedback; they simply carry no *sentiment* label, because there is no text to
  have a sentiment about.
- 71 of the 1,797 are the Toowoomba summary rows that have no comment by design (D-032 #1).

### D-058 · Every negative rate states its denominator · Decided · 29 Oct 2026
- **Follows from D-057's evidence rather than from a question of its own.** Recorded
  separately because it is a Wave 5 reporting rule, and Wave 5's brief will cite it.
- **The finding.** Commentless rows average **4.40** on the 1–5 scale against **3.54** for
  commented rows — a gap of 0.86. Happy customers tick 5 and leave; unhappy ones write.
  The commented subset is therefore **not representative** of the feedback population.
- **The consequence.** Negative rate across commented rows is **28.1%**; across all 7,150
  rows by rating it is roughly **22.5%** (1,609 rows). A report that says "28% of feedback
  is negative" without qualification overstates it by 5.6 points, by silently excluding the
  group that is overwhelmingly satisfied.
- **The rule.** Every negative-rate figure in either report names its denominator. Theme
  and sentiment rates are necessarily over the 5,353 commented rows; dealership and
  department rates under D-004 are over all 7,150. The two are never compared without
  saying so.

### D-059 · The theme list is capped at 8 · Decided · 29 Oct 2026
- **Owner's words:** "yes, pls cap to 8 themes, I think that will capture most of the data &
  dealership sites into a manageable & reportable amount."
- **Measured against the project's own bar** — `trend_evidence.min_month_responses: 20`
  (D-052), reused here so two parts of the project do not use different ideas of "enough":

  | Themes | Average dealer × theme cell | Dealerships clearing 20 |
  |---:|---:|---:|
  | 8 | 27.9 | **19 of 24** |
  | 10 | 22.3 | 17 of 24 |
  | 12 | 18.6 | 8 of 24 |

  There is a cliff between 10 and 12. These figures are also **optimistic**: they assume
  themes split evenly, and real theme distributions are skewed, so the smaller themes' cells
  will be thinner than the table suggests.
- **The five dealerships that do not clear the bar at 8 themes are exactly D-052's five
  thin sites** — VIC09 (36 commented rows), QLD05 (37), NSW07 (94), VIC08 (103), QLD07
  (156). Two independent measures, month volume and comment volume, single out the same five
  sites, which is corroboration rather than coincidence.
- **Constrains D-023, does not close it.** The theme *names* remain the owner's to set after
  discovery; this fixes the size of the list, not its content. Cut-list item 8 already made
  themes beyond roughly 8 cuttable.

### D-060 · Wave 5's drivers cut is rescoped from three-way to two-way · Decided · 29 Oct 2026
- **This departs from PLAN.md section 8**, which promises "negative rate by theme ×
  department × dealership". Recorded now, from Wave 4's cell arithmetic, rather than
  discovered mid-analysis on the Friday.
- **Why the three-way cut is not available.** 8 themes × 72 department-dealership cells is
  576 cells for 5,353 comments: **9.3 comments per cell** before any skew. 15 of those 72
  department × dealership cells already hold fewer than 20 comments before themes enter at
  all.
  - **Parts** has 508 commented rows in total; across 8 themes and 24 dealerships that is
    about 2.6 per cell. Parts can carry a theme breakdown nationally, never per dealership.
  - **VIC09** (36 commented rows) and **QLD05** (37) cannot support a theme split at all —
    4 to 5 comments per theme.
- **The rescope.** Theme × department nationally; theme × dealership for the 19 sites whose
  average cell clears 20; the five thin sites at department level with a footnote —
  consistent with D-052 already putting those same five on a quarterly basis for trends.
- **What is not cut:** the business question. Drivers of negative feedback by theme, and by
  department, are both still answered. What is dropped is the per-dealership-per-theme cell
  that the data cannot populate.

### D-061 · KMeans, not HDBSCAN, for theme discovery · Decided · 30 Oct 2026
- **Raised by the owner,** who asked whether KMeans or GMM would be an easier fit. The
  orchestrator predicted neither would help and was wrong; the test is below.
- **The problem.** HDBSCAN cannot cluster this corpus. A `min_cluster_size` sweep over all
  5,353 redacted comments:

  | min_size | clusters | outliers | largest cluster |
  |---:|---:|---:|---:|
  | 10 | 84 | 27.3% | 533 |
  | 15 | 42 | 20.0% | 836 |
  | 20–30 | 7 | 0.0% | **4,649** |
  | 40 | 5 | 1.7% | 4,632 |
  | 89 | 2 | 1.0% | 4,862 |

  Either 84 micro-clusters or a single cluster holding 87% of the data. BERTopic's own topic
  reduction (over-cluster at 15, merge to 10) did not fix it either: the merged result still
  had one cluster of 3,191 comments, 60% of the corpus.
- **Why it fails.** HDBSCAN looks for separated density peaks. Comments averaging 101
  characters about a service visit do not have them — what varies most in the embedding space
  is which car the customer drives and how happy they are, not which CX driver they are
  describing. Two of the k=8 clusters were pure artefacts: one of short generic praise, and
  one grouped on vehicle model names (D-054's `altura`, `corsa`, `vista`, `terra`).
- **The decision.** KMeans at k=12 over the same UMAP-reduced MiniLM embeddings, seed 42.
  A forced partition cuts along the dominant variance directions, and those *do* include
  experience: staff manner, communication, waiting, pricing, parts and booking all came back
  as coherent groups, and booking separated cleanly at k=12 where it had not at k=8. GMM at
  k=8 gave the same shape but muddier groups — one mixed "reasonable quote", "LONG QUEUE AT
  THE COUNTER" and "Waited ages. No parts." — so KMeans was kept for being simpler and
  cleaner. HDBSCAN stays reachable via `--kmeans-k 0`, so the failure is reproducible.
- **The cost, stated plainly.** KMeans cannot refuse a comment, so it reports 0% outliers *by
  construction*. That is a property of the algorithm and not evidence of fit. HDBSCAN's
  20–27% outlier rate was it declining to force poorly-fitting comments anywhere, which was
  information; KMeans discards it. The `unassigned` similarity floor (D-056) therefore does
  more work, not less.
- **A finding worth keeping:** c-TF-IDF top terms were misleading on this corpus three times
  in one night — a coherent "chasing for a status update" cluster labelled "ready, ask, hold,
  car", and a parts-availability cluster labelled "car, explained, paperwork, finance".
  Themes must be named from example comments, never from top terms. The discovery report
  carries five examples per cluster for that reason.

### D-062 · Theme assignment matches short probes, max-pooled, not one long description · Decided · 30 Oct 2026
- **The first attempt and its measured failure.** Assignment embedded one 50–80 word
  description per theme. The similarity scale came out compressed — median 0.328, p90 0.475 —
  and two of ten decile spot-checks were misassigned, **one of them at the median**, so no
  floor could have caught it.
- **Two causes, both in the wording rather than the model:**
  1. A 60-word description embeds to the centroid of everything it mentions, which sits far
     from any single 101-character comment.
  2. The descriptions borrowed each other's consequences. Parts availability mentioned the
     customer "left without their vehicle", which attracted *"I was dreading losing the whole
     day without a car"* — a Waiting comment.
- **The decision.** Each theme carries 6–7 short probe phrases in the register of the data,
  each staying inside its own theme's subject, and a comment's score for a theme is the
  **maximum** over that theme's probes rather than one score against one description.
- **Result:** median similarity 0.328 → **0.424**, p90 0.475 → **0.582**, max 0.712 →
  **0.924**. Nine of ten decile spot-checks correct, with the single remaining error at p0 —
  the bottom of the distribution, where the floor removes it. Errors concentrating at low
  similarity is the signature of a score that means something. Theme volumes also rebalanced
  sensibly: Workmanship 200 → 454 and Explanation 234 → 398, so the two hand-added themes
  carry real weight instead of scraps.
- **What did not change:** the owner's eight theme names and their descriptions. `description`
  remains the human-readable text the reports quote; `probes` is a separate field that does
  the embedding. D-023 is unaffected.

### D-063 · The sentiment model fails on sarcasm and Australian idiom; the LLM is the mitigation · Decided · 30 Oct 2026
- **Owner's words:** "Route to the LLM." The owner raised sarcasm and colloquialism as a
  hypothesis before any evidence existed for it, and the evidence then confirmed it.
- **The defect, measured.** Of the eight pilot comments where the deterministic sentiment and
  the customer's rating were *opposite*, **all eight were sarcasm or Australian idiom**, and
  the model was confident while wrong:
  - *"Lovely to see the tradition continues: arrive at 7:30, wait till lunch..."* → positive, 0.83
  - *"Oh brilliant, another day of silence. I love guessing whether my car is finished"* → positive, 0.49
  - *"whacked it on the card and it barely registered. bargain."* → negative, 0.85
  - *"Well, would you look at that, a dealer who doesn't take me for a mug."* → negative, 0.70
- **Exposure, not error rate:** 812 of 5,353 comments (15.2%) carry Australian slang markers.
  Most classify correctly — *"Bloody good bunch of blokes"* is read as praise.
- **What is NOT the defect.** The 40 of 66 rating-3 comments the model labelled negative are
  *not* errors. Read directly, they are plain complaints carrying a 3/5 rating — *"Waited and
  waited. Staff rude."*, *"dirty toilets, no parking, car not ready. typical."* The model is
  right there and the **rating** is the weak signal, which is exactly why D-055 set the pass
  mark against the owner's blind labels and not against the rating. On the full corpus the
  model is also *conservative*, not optimistic: it calls 660 fewer positives than the ratings
  do and 523 more neutrals, and its single largest error cell is 781 positive→neutral.
- **The decision.** A local LLM (`qwen2.5:3b`, prompt `sentiment_v1`) gives a third opinion on
  comments where the sentiment model and the rating disagree. It **annotates only** — it does
  not overwrite `sentiment_label`, so Wave 5's headline numbers stay reproducible by a
  reviewer who never starts Ollama. The LLM's value is the *measurement* of how wrong the
  deterministic labels are on ironic text: a limitation the technical report can state with a
  number rather than a hedge.
- **Scope is D-024 and still open.** The pilot projects 1.89–2.49 hours for all 1,887
  disagreements against D-011's 2-hour cut-off. `reports/llm_review.md` recommends 857
  comments (the 350 polarity flips plus the 507 where the rating is neutral) at 0.86 hours.
- **Fallback if the LLM is cut** (PLAN.md §9 requires one in advance): report the sarcasm
  weakness as a measured limitation in both reports, citing the eight cases and the 15.2%
  slang exposure. The defect is documented either way; only the mitigation is optional.

### D-065 · The sentiment model misses the pass mark; D-055's committed fallback applies · Decided · 30 Oct 2026
- **The bar was not moved.** D-055 set κ ≥ 0.60 and named the fallback before any labels
  existed. The measured κ is **0.403**. PLAN.md §9's stop rule says apply the planned
  fallback, so that is what happens: **the customer's star rating is the primary signal for
  negative feedback, and model sentiment is reported as a method comparison with its κ
  stated.** D-004 already made the rating the minimum signal, so no downstream definition
  changes.
- **The measurement** (150 blind labels, owner, 30 Oct; `reports/evaluation.md`):

  | | Value |
  |---|---:|
  | Cohen's κ, model vs owner | **0.403** (floor 0.60) |
  | Raw agreement on the sample | 64.0% |
  | Agreement weighted back to the corpus | 65.5% |
  | **κ of the star rating alone, same labels** | **0.460** |
  | κ of the LLM, 45 overlapping rows | 0.727 |

- **The rating beats the model.** At κ 0.460 against 0.403, the customer's own star rating
  predicts the owner's judgement better than the sentiment model does. That is the clearest
  possible justification for the fallback, and it was not knowable before the labels existed.
- **Why the model failed, from the confusion matrix.** Two faults, both already identified in
  D-063 before the labels were drawn, which is the part worth noting:
  1. **It over-uses `neutral`.** The owner used neutral **3 times in 150**; the model assigns
     it to 22.4% of the whole corpus. 34 of the sample's comments were called neutral by the
     model while the owner called them negative (22) or positive (12).
  2. **It reads sarcasm and praise-then-complaint as positive.** 15 of the owner's 98
     negatives were called positive — *"Wow, what a well oiled machine"* on a 1-star, and
     *"Fantastic customer service from [STAFF], nothing was too much trouble. Part was on
     back-order though"* on a 3-star.
- **The LLM's κ 0.727 does not promote it.** It is measured on 45 rows, and those 45 are
  exactly the disagreement cases the LLM was pointed at, so the subset is the one where it was
  designed to help. A biased 45-row sample cannot justify making a 3B model the primary signal
  for every headline number, and D-055's fallback is what was committed. It is reported as
  evidence that the irony problem is tractable, not as a new primary.
- **Consequence for Wave 5, and it is a real narrowing.** The drivers analysis leads with the
  rating, not sentiment. Theme-level claims carry their own caveat: the owner placed comments
  in the same theme as the model only **44.1%** of the time, so a theme's negative *rate* is
  reportable with that stated and a theme's *ranking* against another is not safe on this
  evidence.
- **For D-056:** the owner answered "none of these" on 7 of 150 comments (4.7%), which is the
  direct evidence for where the `unassigned` floor belongs.
- **D-017 exception, recorded not hidden.** The agent that wrote `src/classify.py` wrote
  `src/evaluate.py` too; there was no time before the 15:00 freeze to stand up an independent
  one. Every input is a committed file and the arithmetic is sklearn's, so the numbers are
  reproducible with `make evaluate` — but they are not independent, and Checkpoint 5's
  verifier should re-run them.

### D-066 · The `unassigned` similarity floor is retired, not set · Recommended, owner to confirm · 30 Oct 2026
- **Closes D-056**, and not the way D-056 expected. D-056 committed to setting the floor from
  the observed distribution. The owner's 150 blind labels were then used to test the mechanism
  itself, and it does not work. Recorded as a recommendation rather than a decision because
  gate G7 applies to retiring a threshold as much as to setting one, exactly as D-052 did when
  it retired `dealer_match_min_confidence`.
- **The test.** The owner answered "none of these" on 7 of 150 comments — the ground truth for
  what a floor is supposed to catch.

  | Group | n | Similarity range | Median |
  |---|---:|---|---:|
  | Placed in a theme by the owner | 143 | 0.180 – 0.740 | 0.438 |
  | **Rejected — "none of these"** | **7** | **0.220 – 0.396** | 0.301 |

  The two groups overlap almost completely. Every floor is therefore either cosmetic or
  destructive:

  | Floor | Catches | Marks unassigned |
  |---:|---:|---|
  | 0.259 — the 4.7th percentile, reproducing the owner's own none-rate | **2 of 7** | 248 (4.6%) |
  | 0.300 | 3 of 7 | 585 (10.9%) |
  | 0.350 | 5 of 7 | 1,237 (23.1%) |
  | 0.400 | 7 of 7 | **2,185 (40.8%)** |

- **Similarity also barely predicts correctness,** which is the deeper reason a floor cannot
  work here: model-owner theme agreement is 38.3% below 0.40, 44.8% at 0.40–0.50, 42.3% at
  0.50–0.60, and 66.7% above 0.60 on only 12 comments. A cut point needs a quantity that
  separates right from wrong, and this one does not.
- **Why the obvious number was rejected.** A floor at the 4.7th percentile reproduces the
  owner's none-rate exactly and would have read as principled in the report. It catches two of
  their seven rejections. Matching the *rate* is not matching the *judgement*, and publishing
  the first while implying the second would have been the more flattering choice.
- **The decision.** No floor. `theme` is reported for every commented row, with the 44.1%
  model-owner agreement from D-065 stated wherever a theme figure appears. Theme negative
  *rates* are reportable with that caveat; theme *rankings* are not (D-065).
- **What would fix it, for the record and not for this week:** a theme model trained or
  validated against more than 150 labels, or assignment by an instruction-tuned model rather
  than embedding similarity — the LLM reached κ 0.727 on sentiment over its subset, so the
  approach is not hopeless, just unevidenced at this sample size.

### D-007 · Two reports · Decided · 29 Oct 2026
- **Decision:** (1) a non-technical business report for the Head of CX; (2) a technical report (`README.md`) for reviewers. The business report links to the technical one.

### D-008 · Non-negotiable outputs · Decided · 29 Oct 2026
- One cleaned dataset; at least one trend; basic NLP of comments; at least one business recommendation; the technical report. Everything else is on the cut list (PLAN.md §10).

### D-009 · Deadline · Decided · 29 Oct 2026
- Code freeze Friday 30 Oct 2026, 3:00pm; proofread and edit until COB.

### D-064 · The clean dataset is exported de-identified to `export/` and committed · Decided · 30 Oct 2026

- **Decision:** `src/export.py` (`make export`) writes the Wave 3 clean dataset to
  `export/feedback_clean.{csv,xlsx,json}` with a manifest, and those files are committed.
  `scripts/check_no_data.py` and `.gitignore` gain an `export/` allowance for exactly this.
- **Why:** D-008 makes the cleaned dataset a non-negotiable output and D-015 keeps data out
  of git history. Both are right, and they conflict here: deliverable #1 is parquet, which a
  reviewer cannot open without Python, so "the dataset is in the repo" was true for the
  pipeline and false for the people the deliverable is for. Three formats, all de-identified,
  settles it without touching the raw or interim paths, which stay blocked.
- **What makes the exception narrow:** the export refuses to write until it has proved on
  that run's data that no email, phone number, street address, registration plate or
  person-shaped name survived redaction, that no column outside the schema allowlist is
  present, and that no cell would be read as a formula by Excel. The manifest records the
  result and the full 64-surface spaCy candidate list, so the claim is checkable rather than
  asserted. The guard still blocks every other data path, and a file dropped into `export/`
  by hand carries none of that proof.
- **Two reviewed exceptions:** `Plin English` (a typo for "Plain English") and `Speedy Next`
  ("Speedy" is an adjective in 7 comments) are name-shaped and are not names. They are listed
  in `NOT_PEOPLE_SURFACES` with the comment that produced each one, rather than fixed by
  widening the rule until the run went green — which would have retired the only check
  standing between a surviving customer name and a file handed to reviewers. Redacting either
  would damage the data, so the dataset is right and the check was over-broad.
- **Risk accepted:** git history cannot be cleaned later, which is the whole basis of D-015.
  The repository is private, so the export is visible to the owner and invited reviewers only.
  If it is ever made public, this data goes public with it and no later commit can undo that.
  Re-check before any visibility change; `make gitleaks` stays the pre-public step.
- **Not exported:** `data/clean/feedback_classified.parquet`. Its sentiment and theme columns
  are model output that has not yet been measured against the owner's labelled sample
  (D-055's κ ≥ 0.60), so exporting them now would hand reviewers numbers no gate has cleared.

### D-067 · The published dataset withholds the source lineage and the exact date · Decided · 30 Oct 2026

- **Context:** the owner established on 30 Oct that the repository **will be made public for
  submission**. D-064 had committed the export on the stated basis that the repository was
  private, and said in terms to re-check before any visibility change. This is that re-check.
  The challenge pack is fictional; it is treated as real customer feedback throughout.
- **Decision:** the public export carries 12 columns, not 15. `source_file`, `source_sheet`
  and `source_row` are withheld, and `feedback_date` is replaced by `feedback_month`. The
  full-lineage copy is written to `data/clean/export_internal/` on `--internal`, which
  `.gitignore` and the commit guard both keep out of the repository.
- **Why, measured on this dataset rather than argued from guidance:**
  - `source_file + source_sheet + source_row` identifies **7,079 of 7,150 rows uniquely
    (99.0%)**. It is a primary key back to the original spreadsheets, which hold the names,
    phone numbers and plates that redaction removed. Any holder of the challenge pack — other
    participants and the assessors — could join on it and undo the de-identification wholesale.
    It is useless to a reader without the pack and a complete re-identification key to one
    with it, so publishing it could only ever have helped the wrong reader.
  - `dealer_code + feedback_date + department` leaves **4,149 rows (58.0%)** alone in their
    group. With the month instead: **100 rows (1.4%)**, a 40-fold reduction. Adding
    `rating_1to5` takes the exact-date figure to 84.6% and the month figure to 11.8%.
  - The month costs nothing that was in use: every analysis in this project is monthly, and
    D-040 already records that the day never reaches a published figure.
- **What is kept:** `feedback_id` remains unique, so every row is still citable and the
  labelling sample in `reports/labels_done.csv` still joins. `department_raw`, `rating_raw`
  and `rating_scale` stay, because the point of them is to let a reviewer check the mapping
  and the scale conversion rather than believe them. `date_corrected` and `date_approx` stay:
  the month is sound for all 16 flagged rows, and it was only ever the day that was inferred.
- **What this costs:** a reviewer cannot re-derive a row's source cell from the published
  file, and cannot reproduce a daily or weekly cut. The first is unavoidable — it is the
  re-identification path itself — and in any case a public reviewer does not hold the raw
  files to check lineage against. The second is not used anywhere in the project.
- **Enforced, not just documented:** `src/export.py` blocks the export if a lineage column or
  an exact date reaches the public frame, with a test per column. The audit from D-064 — no
  surviving email, phone, address, plate or person-shaped name — still runs first.
- **The committed history is the open problem.** `bec914d` carried all 15 columns and exact
  dates, and three commits now sit on top of it, all already pushed. A later commit cannot
  remove a blob from history, so publishing this repository as it stands would publish the
  99% re-identification key regardless of what the current files say. It has to be rewritten
  before the repository is ever public, and that is the owner's call because it force-pushes
  over commits that already exist on the remote. `PUBLIC_RELEASE.md` holds the checklist and
  the two options. **Until that is done, this repository must stay private.**
- **Also checked before release, and clean:** every blob in all 54 commits across every branch
  and tag was scanned for real email addresses, phone numbers, street addresses, plates and
  person-shaped names. The only hits are the regex patterns in `src/pii.py` itself and the
  synthetic fixtures in `tests/`. No staff roster or name list exists on disk at any commit.
  96 verbatim comments are quoted in four committed reports, none of them beside a dealer
  code, date or `feedback_id`, so they carry no linkage.

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
| D-019 | Duplicate check result (confirms or overturns D-002 assumption) | **Closed 29 Oct 2026 — see D-047.** D-002 holds; the only true duplicates were 9 double-entered pairs at Springwood |
| D-021 | Evidence threshold for calling a trend real | **Closed 29 Oct 2026 — see D-052.** 20 responses a month, 0.5 stars, thin sites quarterly |
| D-022 | NLP pass mark and fallback | **Closed 29 Oct 2026 — see D-055.** Cohen's κ ≥ 0.60 on a 150-comment stratified sample, with D-004's rating signal as the fallback. The theme bar stays open until the theme list is fixed (D-023) |
| D-023 | Final theme list (fixed + discovered mix) | **Closed 30 Oct 2026.** Size capped at 8 by D-059; the owner approved the eight names, six discovered by KMeans (D-061) and two added under the "fixed + discovered mix" because clustering could not isolate them. The list is `mappings/themes.yaml` |
| D-024 | LLM in or out, and at what scope | **Closed 30 Oct 2026 — in, at scope B.** The owner chose 857 of the 1,887 disagreements on the pilot's timing evidence, because all 1,887 projected at 1.89–2.49 h against D-011's 2 h cut-off. Run in 49.8 min with 0 parse failures; `reports/llm_review.md`, `agents/reports/w4_llm.md`. It annotates only — no headline number depends on it |
| D-025 | Value benchmarks and assumptions (low/mid/high) | Wave 5 |

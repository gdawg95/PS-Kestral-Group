# Register of formatting inconsistencies across the 52 feedback files

**Prepared:** 29 October 2026 · **Source:** `reports/profiles/` (built from the
spreadsheets themselves) and `mappings/columns.yaml` · **Verified by:**
`uv run python scripts/check_mapping.py`

**What this is.** Every way the 52 files disagree with each other about format,
where it happens, and what the pipeline does about it. It is written to be
lifted into the client report: each section names the dealership, so Kestrel can
see which sites to standardise first.

**The pack in one line:** 52 files · 84 worksheets · 37 Excel workbooks and 15
CSVs · 66 distinct column headings · 24 dealerships · October 2025 to September
2026.

No customer comment, name, phone number, email address or registration plate is
quoted anywhere in this register.

---

## Summary: 13 kinds of inconsistency

| # | What varies | How many variants | Sites affected |
|---|---|---:|---|
| 1 | Where the table starts on the sheet | 7 header positions | 18 of 24 |
| 2 | How the date is written | 8 representations | all 24 |
| 3 | What the rating means | 7 scales | all 24 |
| 4 | How a department is spelled | 19 spellings, plus 317 cells with stray spaces | all 24 |
| 5 | What a column is called | 66 headings for ~12 ideas | all 24 |
| 6 | File format, delimiter, text encoding | 4 combinations | all 24 |
| 7 | The layout changing part-way down one sheet | 2 files | Frankston, Ringwood |
| 8 | Rows that are not feedback | 33 rows, 4 kinds | 5 sites |
| 9 | Which personal data columns exist at all | 0 to 4 per file | all 24 |
| 10 | Dates that are wrong or vague | 17 rows, 3 kinds | Shepparton, Ipswich, Liverpool |
| 11 | One file holding two dealerships | 1 file | Rockhampton + Townsville |
| 12 | Duplicate and superseded files | 2 cases, 155 rows | Chermside, Penrith |
| 13 | Counts supplied instead of feedback rows | 1 file | Toowoomba |

---

## 1. Where the table starts on the sheet

A reader opens each file and finds the column headings in a different place.

| Header on row | Worksheets | Where |
|---:|---:|---|
| 1 | 63 | most sites |
| 2 | 2 | **Ballarat** (two-row header, group labels above the names), Southport's Google-reviews sheet |
| 3 | 2 | **Hunter Motors / Newcastle**, **Toowoomba** Q4 summary |
| 4 | 13 | **Dandenong** (11 monthly sheets), **Geelong** (both year sheets) |
| 5 | 1 | **Dandenong** "May 26" — one extra note row pushes everything down |
| 37 | 1 | **Ringwood** Q1 2026 — a second header mid-sheet |
| 160 | 1 | **Frankston** — a second header mid-sheet |

**Ballarat** also carries 3 merged cell ranges in the header area. The data
itself is not merged, so the merge is cosmetic — but it is why the headings sit
on row 2 rather than row 1.

*Treatment:* the header row is recorded per worksheet in `columns.yaml` and
cross-checked against the profiles, so a wrong guess fails the run rather than
silently reading data as headings.

## 2. How the date is written

Eight different representations of the same thing.

| Representation | Files | Example site |
|---|---:|---|
| Real Excel date cell | 26 | Dandenong, Parramatta, Penrith |
| Text, `dd/mm/yyyy` | 17 | Essendon, Ringwood, Ipswich |
| Text, `dd/mm/yy` | 1 | Geelong |
| Text, `dd-Mon-yy` | 2 | Wollongong |
| Text, `dd Mon yy` | 1 | Bendigo |
| Timestamp with a time of day | 4 | Box Hill (survey export) |
| Excel serial number stored as a plain number | 1 | North QLD |
| Text, **`mm/dd/yyyy`** — month first | 1 | **Liverpool Q3 2026 only** |

Two files appear twice in that table: Southport's two worksheets disagree with
each other, and Liverpool Q3's column parses partly either way — which is what
makes it dangerous.

**Liverpool Q3 2026 is the dangerous one.** The same dealership's other three
quarterly files are day-first; this one file is month-first. Read day-first, 56
of its 85 rows become unparseable and the other 29 scatter across the year.
Confirmed by parsing it both ways: month-first puts all 85 rows inside July to
September 2026. The mapping asserts that date range, so if the file is ever
re-sent in the other format the run stops.

*Treatment:* one date format per worksheet, named in the mapping. Box Hill's
time of day is discarded — the analysis is monthly.

## 3. What the rating means

Seven scales. A "4" does not mean the same thing at every site.

| Scale | Sites | Values as supplied |
|---|---|---|
| 1–5, 5 = best | 17 sites use nothing else | `1` … `5` |
| **1–10** | **Ringwood**, from February 2026 | `1` … `10` |
| **1–5 reversed, 1 = best** | **Geelong**, 2025 sheet only | `1` … `5` |
| Five satisfaction words | Ballarat | Very dissatisfied … Very satisfied |
| Three words | Tamworth | Bad · OK · Good |
| Star characters | Bendigo | ★☆☆☆☆ … ★★★★★ |
| Counts of each score | Toowoomba Q4 2025 | a pivot table, not ratings |

Two scales need flagging in the client report:

- **Geelong's 2025 sheet is reversed** — the sheet title says 1 = Excellent.
  Read naively, Geelong's best year looks like its worst. The 2026 sheet uses
  the normal direction, so the reversal must be applied to one sheet and not
  the other.
- **Tamworth's three-point scale is stretched to five** (Bad→1, OK→3, Good→5).
  Tamworth cannot produce a 2 or a 4, so its distribution is not comparable to
  a five-point site's. It should carry a footnote wherever it is ranked.

*Treatment:* every rating is converted to a common 1–5 scale using the approved
conversion table, and both the original value and the converted one are kept in
the dataset so any conversion can be checked.

## 4. How a department is spelled

**19 spellings for 3 departments**, pooled across the whole pack.

| Means | Spellings found |
|---|---|
| Service | `Service`, `SERVICE`, `service`, `Service Dept`, `Workshop`, `Svc`, `SV` |
| Sales | `Sales`, `sales`, `New Cars`, `Used Cars`, `Sales - New`, `Sales - Used`, `S` |
| Parts | `Parts`, `parts counter`, `Parts & Accessories`, `P&A`, `P` |

Three specific cases:

- **Frankston alone uses 14 of the 19 spellings** — within one file, "service",
  "Service", "SERVICE", "Service Dept", "Workshop" and "Svc" all appear.
- **Penrith splits Sales into "Sales - New" and "Sales - Used"**, the only site
  that distinguishes them. Both become Sales; the split is not available
  anywhere else, so it cannot be reported group-wide.
- **Bendigo uses single letters** — `SV`, `S`, `P`. The owner confirmed these
  mean Service, Sales and Parts, and asked for the words to be spelled out, so
  the dataset holds the words.
- **Essendon has no department column at all** — the department is the
  worksheet name (Sales / Service / Parts).
- **317 department cells carry a stray leading or trailing space**, across 13 of
  the 52 files — North QLD 79, Springwood 42, Frankston 39, Newcastle 35,
  Ipswich 27, Ringwood 56 across its four files, Wollongong 22, Tamworth 13,
  Shepparton 4. Invisible on screen, but `"service "` and `"service"` are two
  different values to any spreadsheet pivot or database group-by, so any count
  Kestrel has produced from these files by hand may have split a department in
  two. Ingestion trims them.

*Treatment:* the department is kept exactly as the site wrote it, and a separate
step maps the spellings onto Service / Sales / Parts. Keeping both means the
mapping can be audited and corrected without re-reading the spreadsheets.

*Note on the count.* 19 spellings occur in the source files. The consolidated
dataset holds **16**, because Bendigo's three letter codes were expanded to words
at the owner's instruction and the 317 stray spaces were trimmed. The 16 → 3
mapping is in `mappings/departments.yaml` with the row count and mean rating for
each, and the split is Service 4,909 · Sales 1,544 · Parts 706.

## 5. What a column is called

66 distinct column headings across the pack, for about a dozen underlying ideas.

| Idea | Headings used |
|---|---|
| The date | `Date`, `DATE`, `Date Received`, `When`, `submitted_at`, `Month` |
| The department | `Department`, `Dept`, `DEPT`, `Area`, `department` |
| The rating | `Rating`, `Rating (1-5)`, `Score`, `Score (1-5)`, `Score (out of 10)`, `CSAT`, `csat`, `Stars`, `How satisfied?`, `HOW WAS IT` |
| The comment | `Comments`, `COMMENTS`, `Comment`, `Customer comments`, `Customer feedback`, `Customer said`, `Feedback`, `Notes`, `What did they say?`, `verbatim` |

**Tamworth** writes every heading in capitals. **Box Hill** uses lower-case
snake_case throughout, because it is a survey-tool export rather than a
hand-kept sheet.

Two files carry fully empty columns to the right of the data: **Frankston** 3,
**Ringwood** Q1 2026 2.

*Treatment:* every one of the 66 headings is mapped explicitly. The mapping also
records the columns it deliberately ignores, and the run stops if a re-sent file
contains a heading that is in neither list — so a new column is never silently
dropped.

## 6. File format, delimiter and text encoding

| Property | Variants |
|---|---|
| Format | 37 Excel workbooks (`.xlsx`), 15 CSVs |
| Delimiter | comma in 11 CSVs; **semicolon in all 4 Chatswood CSVs** |
| Encoding | UTF-8 in 12 CSVs; **UTF-8 with a byte-order mark** in Bendigo; **Windows-1252 in both Wollongong files** |

Three of these would have broken the run silently or loudly:

- **Chatswood's semicolons.** Read as comma-separated, each row arrives as a
  single column and the file looks empty of ratings. All four quarters are
  affected, not just one.
- **Bendigo's byte-order mark.** Read as plain UTF-8, the first heading comes
  through as `ï»¿Date` instead of `Date`, so the date column is missed.
- **Wollongong is Windows-1252, not UTF-8** (found 29 October 2026). Reading it
  as UTF-8 raises an error; forcing it through would corrupt the curly
  apostrophes inside customer comments — and those comments are the input to the
  text analysis.

*Treatment:* delimiter and encoding are declared per file in the mapping.

## 7. The layout changing part-way down one sheet

Two files change template mid-worksheet, with a second set of headings in the
middle of the data.

| File | Changes at | Before | After |
|---|---|---|---|
| **Ringwood** Q1 2026 | row 37 | 34 rows, `Score (1-5)`, January | 79 rows, `Score (out of 10)`, February–March |
| **Frankston** CX tracker | row 160 | 145 rows, 4 columns, Oct 2025 – Mar 2026 | 163 rows, 7 columns incl. customer name and rego, Apr – Sep 2026 |

**Ringwood's is the costly one:** the 79 rows after row 37 are out of 10. Read as
out of 5, they would all look like top scores and Ringwood's 2026 would be
wrong. Confirmed by the owner on 29 October 2026.

*Treatment:* each file is mapped as two tables with their own header rows,
scales and column sets, and the row counts of both halves are checked.

## 8. Rows that are not feedback

33 rows across 5 sites are present in the worksheets but are not customer
feedback.

| Kind | Rows | Where |
|---|---:|---|
| Blank separator rows inside the data | 14 | Frankston 12, Ringwood Q1 1, Shepparton 1 |
| Monthly `Total <month>` rows with an average and a response count | 12 | Frankston |
| Notes typed into a data row | 3 | Shepparton closure note, Ringwood template note, Toowoomba "Grand Total" |
| Test rows | 4 | Southport |

**Southport's four** are worth naming because they are the only rows in the pack
that look like feedback and are not: three are tests (one dated 01/01/1900, one
with the date typed as "TEST", one with no date at all but a rating of 3), and
one is a row of keyboard mash. The owner confirmed all four on 29 October 2026.

No CSV contains a blank row.

*Treatment:* all 33 are dropped, each tagged with its reason, and the
reconciliation report accounts for every one. Totals and notes are tagged
"summary or notes" at the owner's instruction.

## 9. Which personal data columns exist at all

The files disagree about what they collect, which is itself a finding for
Kestrel: there is no group-wide rule about what goes in a feedback log.

| Column kind | Appears in |
|---|---:|
| Customer name | 13 of 52 files |
| Phone number or email address | 21 of 52 files |
| Vehicle model or registration plate | 24 of 52 files |
| Customer, DMS, booking or response identifier | 21 of 52 files |

**Frankston collects nothing personal before April 2026 and customer name plus
registration plate after it** — the mid-sheet template change at row 160 added
them.

*Treatment:* none of these columns reaches the dataset. Only the date,
department, rating and comment survive the first read. Name and plate values are
used in memory, for the single purpose of removing those exact strings from that
row's own comment, then discarded.

## 10. Dates that are wrong or vague

| Issue | Rows | Site |
|---|---:|---|
| Dated after the site closed — year typed as 2026 instead of 2025 | 6 | **Shepparton** (closed 31 March 2026) |
| Written as words: "early Oct", "mid Nov", "wk1 Feb", "Aug?" | 10 | **Ipswich** |
| Month and day the wrong way round for one quarter | 85 | **Liverpool** Q3 2026 (section 2) |

**Shepparton:** six rows land in October–December 2026, months after the site
shut. Treated as year typos and moved back a year, which makes Shepparton's data
run 6 October 2025 to 31 March 2026 — exactly matching the closure date. Six
rows of a 52-row site, so the alternative, dropping them, would have cost 12% of
the dealership.

**Ipswich:** the log is kept in date order, so each vague entry is dated to the
midpoint of the nearest dated rows above and below it, and the written label
supplies the month. Checked by hand for all 10 rows: the two signals agree on
the month every time, so no monthly figure depends on which one is trusted.
These rows are flagged in the dataset as approximate.

## 11. One file holding two dealerships

**`North QLD feedback (Rocky + TSV).xlsx`** holds Rockhampton and Townsville
together, across four quarterly sheets, identified by a `Site` column that uses
**six spellings for two sites**: `Rockhampton`, `Rocky`, `ROK`, `Townsville`,
`TSV`, `Tsv`.

Verified 29 October 2026: those six and no others, splitting 202 rows
Rockhampton / 354 Townsville = 556.

*Treatment:* the file is split into the two dealerships, each under its own
code, and both row counts are asserted. From the dataset onwards they are two
separate dealerships everywhere — reconciliation, charts and report — and the
combined file name never appears as a dealership.

Two other files carry a site column that is **not** a second dealership:
Hunter Motors' reads the same value on all 303 rows, and Ipswich's on all 277.
Both are dropped rather than used.

## 12. Duplicate and superseded files

| Case | Rows | Resolution |
|---|---:|---|
| **Chermside Q1 2026** exists as `FINAL` (112 rows) and `FINAL v2` (118 rows) | 112 | Every row of `FINAL` was found inside `v2`, which adds 6 rows and extends to 31 March. `FINAL` is excluded. |
| **Penrith's "Jun 26" sheet is a copy of "Jul 26"** | 43 | The sheet is excluded. **Penrith has no real June 2026 data in the pack** — a gap to report, not to fill. |

The folder also contained two Excel lock files (`~$…`), which are not data. That
is why the folder shows 54 files for a 52-file pack.

## 13. Counts supplied instead of feedback rows

**`Toowoomba Q4 2025 summary.xlsx`** is a pivot table, not a feedback log: 6
rows of month × department, each holding counts of how many 1s, 2s, 3s, 4s and
5s were received, plus a "Grand Total" row. It represents 71 pieces of feedback.

Two consequences for the client report:

- Those 71 rows have **no comment text**, so Toowoomba's Q4 2025 contributes
  nothing to the text analysis, and are dated the 15th of their month because
  the real dates no longer exist.
- The summary contains **no Sales rows at all** — only Parts and Service. The
  owner took this at face value on 29 October 2026, so Toowoomba's Q4 2025 is
  reported as Service and Parts only, with a footnote. If the pivot was built by
  someone who only included two departments, Toowoomba's Q4 Sales feedback was
  never supplied.

---

## One event worth keeping, not a formatting issue

**Dandenong's "May 26" sheet carries a note above the header:** a new online
booking system went live on 5 May, with a warning to expect teething issues. The
note holds no numbers, so nothing is lost by dropping it from the data, but it is
the most likely explanation if Dandenong's scores dip from May. The owner asked
for it to be kept as contextual evidence, so it must be cited in the trend
section rather than left for the reader to guess at.

---

## What this means for Kestrel

Three points the register supports, for the recommendations section:

1. **No two of the 24 dealerships record feedback the same way.** 19 spellings
   of 3 departments, 8 ways of writing a date and 7 rating scales are not
   site-level quirks — they are the absence of a group standard.
2. **Three of the inconsistencies would have produced wrong answers silently
   rather than failing:** Geelong's reversed scale, Ringwood's mid-sheet change
   to a 10-point scale, and Liverpool's one month-first quarter. Each would have
   moved a dealership's published score without anything looking broken. A
   single feedback template removes all three risks at once.
3. **Personal data is collected inconsistently and without need.** Customer
   names, phone numbers, emails, plates and DMS identifiers appear in roughly
   half the files, with no pattern, and none of it was required to answer any of
   the three business questions.

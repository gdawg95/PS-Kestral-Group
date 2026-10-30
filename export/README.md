# The clean dataset — reviewer export

The finished, de-identified Kestrel customer-feedback dataset: **7,150 rows**, one row per
piece of feedback, 24 dealerships, 1 Oct 2025 – 30 Sep 2026.

Three formats, one dataset. Same rows, same columns, same values in each — verified value
for value against the parquet the pipeline actually produces, not assumed.

| File | Open it with | Use it for |
|---|---|---|
| `feedback_clean.csv` | Excel, Numbers, R, pandas, anything | the default. UTF-8 with BOM so Excel on Windows reads the punctuation correctly |
| `feedback_clean.xlsx` | Excel, LibreOffice | reading and filtering by hand without import settings |
| `feedback_clean.json` | any language, `jq` | nested or programmatic use. `null`, not `"nan"`, for missing values |
| `MANIFEST.md` | — | sha256 of each file and the de-identification evidence for this run |

`feedback_clean.csv` and `MANIFEST.md` are the two to read first.

## Where this came from

52 dealership spreadsheets in 7 different layouts, with 16 spellings of three department
names and 7 different rating scales.

| Stage | Rows | What happened |
|---|---:|---|
| Raw feedback rows | — | 52 files; 51 contribute, `Chermside Q1 2026 FINAL.xlsx` superseded by `FINAL v2` (D-027) |
| Consolidated | 7,159 | one schema, ratings all converted to 1–5, dates parsed, PII redacted (Wave 2) |
| **Exported** | **7,150** | 9 rejected by the validation rules (Wave 3) |

`7,159 = 7,150 + 9`. The nine and the rule that caught each are in
[`../reports/data_quality.md`](../reports/data_quality.md).

Full method, every rule, and every judgement call: [`../README.md`](../README.md) (technical
report), [`../DECISIONS.md`](../DECISIONS.md) (D-001 – D-064), [`../AI_LOG.md`](../AI_LOG.md)
(AI usage and the owner's verdict on each wave).

## Columns

| # | Column | Type | What it is |
|---:|---|---|---|
| 1 | `feedback_id` | text | `F000001`…, assigned by the pipeline. Unique, stable |
| 2 | `dealer_code` | text | `VIC01`…`QLD08`. 24 sites. Codes, not names, mapped by hand (D-034) |
| 3 | `feedback_date` | date `YYYY-MM-DD` | within 1 Oct 2025 – 30 Sep 2026 |
| 4 | `department_raw` | text | exactly what the spreadsheet said. 16 distinct spellings, kept so the mapping is auditable |
| 5 | `department` | text | `Service` (4,903) / `Sales` (1,541) / `Parts` (706). Never empty. Mapping: [`../mappings/departments.yaml`](../mappings/departments.yaml) (D-048, D-049, D-050) |
| 6 | `rating_raw` | text | exactly what the spreadsheet said — `4`, `8/10`, `Very satisfied`, `★★★★` |
| 7 | `rating_scale` | text | which scale `rating_raw` was on, so the conversion can be checked: `1-5` (6,121), `1-10` (321), `words-5` (292), `stars-5` (144), `words-3` (133), `pivot-1-5` (71), `1-5-reversed` (68) |
| 8 | `rating_1to5` | integer 1–5 | the comparable rating. Mean 3.75. Converted from `rating_raw` (D-020, D-030) |
| 9 | `comment` | text or empty | the free-text comment, **redacted** — see below. Empty for 1,797 rows that had no comment; 5,353 have one |
| 10 | `source_file` | text | the spreadsheet this row came from |
| 11 | `source_sheet` | text or empty | the worksheet within it |
| 12 | `source_row` | integer | the row number in that sheet. Columns 10–12 are the lineage: every row traces back to a cell you can go and look at |
| 13 | `from_summary` | true/false | 71 rows expanded from a pivot table of counts, so they carry a rating but never a comment (D-032 #1) |
| 14 | `date_corrected` | true/false | 6 rows whose year was a typo — dated after the site closed, moved back one year (D-032 #3) |
| 15 | `date_approx` | true/false | 10 rows whose source gave a vague date (`mid Nov`, `Aug?`) resolved to a day (D-040). Exclude these from any day-level claim; every analysis here is monthly, so the day never reaches a published figure |

All 16 flagged dates, with their source values and the neighbouring dated rows that justify
each one: [`../reports/date_edge_cases.md`](../reports/date_edge_cases.md).

## What was done to the comments

Personal information was replaced with typed tokens, so a comment stays readable and
analysable while the person in it is not identifiable:

| Token | Comments containing it | Was |
|---|---:|---|
| `[NAME]` | 160 | a customer's name |
| `[STAFF]` | 734 | a staff member's name |
| `[REGO]` | 476 | a vehicle registration plate |
| `[PHONE]` | 156 | a phone number |
| `[EMAIL]` | 58 | an email address |
| `[ADDRESS]` | 0 | a street address — the pattern runs, the source comments had none |

Name, phone and registration **columns** in the source spreadsheets were dropped entirely at
ingestion, not redacted: only date, department, rating and comment survive (D-003). Those
columns were read once, to redact those exact strings from the same row's comment, then
discarded.

`export/` is the one data path the repository's commit guard allows, and only because
`src/export.py` refuses to write a file until it has proved, on that run's data, that no
email address, phone number, street address, registration plate or person-shaped name
survived. `MANIFEST.md` carries the result and the full list of the 64 surfaces spaCy
reported as possible people, so you can disagree with the reading rather than take it on
trust. The reasoning is D-064.

## Things worth knowing before you count rows

- **Three comments contain a line break.** The CSV quotes them correctly, so 7,150 rows is
  not 7,150 lines in a text editor. Any real CSV reader handles it.
- **`comment` is empty for 1,797 rows.** That is real: those customers gave a rating and no
  comment. It is not missing data.
- **`department_raw` is deliberately messy.** It is the evidence for column 5, not a defect.
- **Dealerships are codes.** Site names appear in the reports where they are the subject;
  the dataset carries codes so a row cannot be tied to a site by accident.
- **Ratings were on 7 different scales.** Compare on `rating_1to5`; `rating_raw` and
  `rating_scale` are there so you can check the conversion rather than believe it.

## Not in this export

- **Raw and intermediate data.** They stay out of git permanently (D-015).
- **Sentiment and theme columns.** They exist in the pipeline
  (`data/clean/feedback_classified.parquet`) but are model output that has not yet been
  measured against the owner's hand-labelled sample, so this export does not carry numbers
  no gate has cleared. D-064 and D-055.

## Regenerating it

```
make export                      # or: uv run python -m src.export
```

Reproduces these files byte for byte from `data/clean/feedback.parquet`, re-running the full
audit first. It exits non-zero and writes nothing if the audit fails. To rebuild the dataset
itself from the raw spreadsheets: `make ingest validate` (Windows:
`scripts/run.ps1 -Target validate`).

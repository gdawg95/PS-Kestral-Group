# The clean dataset — public export

The finished, de-identified Kestrel customer-feedback dataset: **7,150 rows**, one row per
piece of feedback, 24 dealerships, Oct 2025 – Sep 2026.

Three formats, one dataset. Same rows, same columns, same values in each — verified value
for value against the parquet the pipeline produces, not spot-checked.

| File | Open it with | Use it for |
|---|---|---|
| `feedback_clean.csv` | Excel, Numbers, R, pandas, anything | the default. UTF-8 with BOM so Excel on Windows reads the punctuation correctly |
| `feedback_clean.xlsx` | Excel, LibreOffice | reading and filtering by hand without import settings |
| `feedback_clean.json` | any language, `jq` | nested or programmatic use. `null`, not `"nan"`, for missing values |
| `MANIFEST.md` | — | sha256 of each file and the de-identification evidence for this run |

`feedback_clean.csv` and `MANIFEST.md` are the two to read first.

## This is a public dataset, and two columns are missing because of it

This repository is published, so the dataset in it is treated as real customer feedback
even though the challenge pack is fictional. Redacting names out of the comments is not
sufficient on its own for a published file, and two things were changed before release
(D-067):

**The source lineage is withheld.** The internal dataset carries `source_file`,
`source_sheet` and `source_row` — the spreadsheet cell each row came from. Those three
fields identify **7,079 of the 7,150 rows uniquely (99.0%)**, which makes them a primary
key straight back to the original, *un*redacted spreadsheets. Anyone holding the challenge
pack could join on them and read back the customer name, phone number and registration
plate that redaction removed. They are of no use to a reader who does not have the pack and
a complete re-identification key to every reader who does, so publishing them would only
ever have helped the wrong person. `feedback_id` still gives every row a stable handle, so
rows remain citable and discussable.

**The date is the month, not the day.** `dealer_code` + exact date + `department` left
**4,149 rows (58.0%)** alone in their group, so a reader who knew that someone visited one
site on one day could usually find their comment. The same three fields with the month
leave **100 rows (1.4%)**. Every analysis in this project is monthly and D-040 already
recorded that the day never reaches a published figure, so this costs nothing that was
being used.

Both numbers are measured on this dataset, not quoted from guidance.

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
report), [`../DECISIONS.md`](../DECISIONS.md) (D-001 – D-067), [`../AI_LOG.md`](../AI_LOG.md)
(AI usage and the owner's verdict on each wave).

## Columns

| # | Column | Type | What it is |
|---:|---|---|---|
| 1 | `feedback_id` | text | `F000001`…, assigned by the pipeline. Unique and stable; the row handle |
| 2 | `dealer_code` | text | `VIC01`…`QLD08`. 24 sites. Codes, not names, mapped by hand (D-034) |
| 3 | `feedback_month` | text `YYYY-MM` | `2025-10` … `2026-09`. Coarsened from the exact date — see above |
| 4 | `department_raw` | text | exactly what the spreadsheet said. 16 distinct spellings, kept so the mapping is auditable |
| 5 | `department` | text | `Service` (4,903) / `Sales` (1,541) / `Parts` (706). Never empty. Mapping: [`../mappings/departments.yaml`](../mappings/departments.yaml) (D-048, D-049, D-050) |
| 6 | `rating_raw` | text | exactly what the spreadsheet said — `4`, `8/10`, `Very satisfied`, `★★★★` |
| 7 | `rating_scale` | text | which scale `rating_raw` was on, so the conversion can be checked: `1-5` (6,121), `1-10` (321), `words-5` (292), `stars-5` (144), `words-3` (133), `pivot-1-5` (71), `1-5-reversed` (68) |
| 8 | `rating_1to5` | integer 1–5 | the comparable rating. Mean 3.75. Converted from `rating_raw` (D-020, D-030) |
| 9 | `comment` | text or empty | the free-text comment, **redacted** — see below. Empty for 1,797 rows that had no comment; 5,353 have one |
| 10 | `from_summary` | true/false | 71 rows expanded from a pivot table of counts, so they carry a rating but never a comment (D-032 #1) |
| 11 | `date_corrected` | true/false | 6 rows whose year was a typo — dated after the site closed, moved back one year (D-032 #3) |
| 12 | `date_approx` | true/false | 10 rows whose source gave a vague date (`mid Nov`, `Aug?`) resolved to a day (D-040). The month is sound for all ten; it is the day that was inferred, and the day is no longer published |

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
discarded. No staff roster or name list is stored anywhere in this repository — the roster is
built in memory during ingestion and only counts are ever written out.

`export/` is the one data path the repository's commit guard allows, and only because
`src/export.py` refuses to write a file until it has proved, on that run's data, that no
email address, phone number, street address, registration plate or person-shaped name
survived, that no lineage column or exact date is present, and that no cell would be read as
a formula by Excel. `MANIFEST.md` carries the result and the full list of the 64 surfaces
spaCy reported as possible people, so you can disagree with the reading rather than take it
on trust. The reasoning is D-064 and D-067.

## Things worth knowing before you count rows

- **Three comments contain a line break.** The CSV quotes them correctly, so 7,150 rows is
  not 7,150 lines in a text editor. Any real CSV reader handles it.
- **`comment` is empty for 1,797 rows.** That is real: those customers gave a rating and no
  comment. It is not missing data.
- **`department_raw` is deliberately messy.** It is the evidence for column 5, not a defect.
- **Dealerships are codes.** Site names appear in the reports where the site is the subject;
  the dataset carries codes so a row cannot be tied to a site by accident.
- **Ratings were on 7 different scales.** Compare on `rating_1to5`; `rating_raw` and
  `rating_scale` are there so you can check the conversion rather than believe it.
- **Monthly is the finest grain available**, by design. A daily or weekly cut cannot be
  reproduced from this file, and no published figure in the project uses one.

## Not in this export

- **Raw and intermediate data.** They stay out of git permanently (D-015).
- **The source lineage and the exact date.** Withheld for publication (D-067, above). The
  owner holds a full-lineage copy outside the repository for their own audit.
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

`uv run python -m src.export --internal` additionally writes the full-lineage copy to
`data/clean/export_internal/`, which `.gitignore` and the commit guard both keep out of the
repository. That copy is for the owner's own audit and is not for publication.

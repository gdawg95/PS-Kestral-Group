# Export manifest

**Generated:** `python -m src.export` · 2026-10-30 13:08
**Source:** `data/clean/feedback.parquet` (sha256 `8832792c7583278f…`)
**Rows:** 7,150 · **Columns:** 12

Three formats, one dataset. Same rows, same columns, same values in each.

**This is the public export.** It carries the month rather than the exact date, and it does not carry `source_file`, `source_sheet` or `source_row`. Those three identify 99.0% of rows uniquely and are a join key straight back to the identified source spreadsheets, so they are withheld from a published dataset (D-067). `feedback_id` still gives every row a stable handle.

| File | Bytes | sha256 |
|---|---:|---|
| `feedback_clean.csv` | 1,054,759 | `1c9499c57cf78e5736b3e855724da004c08982f0961d2fe3d2a30286c0ea2e50` |
| `feedback_clean.xlsx` | 642,271 | `01432544687a5d40acf657968e0b18a65850c79327a399c0950a64c41b33e227` |
| `feedback_clean.json` | 2,975,542 | `e268ec442c5a5d3032ac5d8f0bbce7f00de9b488c6adfe04d06815b6605ed72f` |

## De-identification evidence

`src/export.py` refuses to write a file until these pass on the data in front of it, so this section is a record of the run that produced the files above, not a claim carried over from an earlier one.

| Check | Result |
|---|---|
| Email addresses surviving redaction | none |
| Phone numbers surviving redaction | none |
| Street addresses surviving redaction | none |
| Registration plates surviving redaction | none |
| Cells Excel would read as a formula | none |
| Columns outside the allowlist | none |
| Person-shaped spaCy candidates (two or more capitalised words) | none beyond the 2 reviewed exceptions below |
| Source-lineage columns (a key back to identified rows) | withheld |
| Date granularity | month; 1.4% of rows alone on dealer + month + department, against 58.0% on the exact date |

Redaction tokens present in the exported comments:

| Token | Comments containing it |
|---|---:|
| `[NAME]` | 160 |
| `[STAFF]` | 734 |
| `[REGO]` | 476 |
| `[PHONE]` | 156 |
| `[EMAIL]` | 58 |
| `[ADDRESS]` | 0 |

`[ADDRESS]` is zero because the source comments contained no street addresses to redact, not because the pattern was skipped - it runs, and `reports/formatting_changes.md` records what each pattern applied.

### The reviewed exceptions

Two surfaces are shaped like a name and are not one. Both would be damaged by redaction, so the dataset is right and the check was over-broad; each is named in `NOT_PEOPLE_SURFACES` in `src/export.py` rather than handled by widening the rule, so any *other* person-shaped surface still stops the export.

| Surface | The comment | Reading |
|---|---|---|
| `Plin English` | "Plin English, all the way through. Top marks." | a typo for "Plain English" |
| `Speedy Next` | "Speedy Next (rego `[REGO]`)" | `Speedy` is an adjective in 7 comments; the plate beside it is already redacted |

### Every person candidate spaCy reported

64 distinct surfaces. None is a person: they are sentence-initial verbs (`Rang`, `Said`, `Felt`), objects (`Gearbox`, `hose`, `tow bar`), slang (`Ripper`, `Mate`, `arvo`) and typos. `Bill` appears nine times and is the invoice in all nine. Listed in full so a reviewer can disagree with that reading rather than take it on trust.

```
  18x 'Rang'
  18x 'Said'
  16x 'Felt'
  9x 'Bill'
  8x 'hose'
  7x 'bush'
  3x 'Rego'
  3x 'Ta'
  3x 'bin'
  2x 'Drop'
  2x 'Gearbox'
  2x 'Problem'
  2x 'Quck'
  2x 'Rang 3'
  2x 'Ripper'
  2x 'S4'
  2x 'Spooky'
  2x 'Voicemail'
  2x 'cmon'
  2x 'levy'
  1x 'Beaut'
  1x 'Beige'
  1x 'Blink'
  1x 'Bolt'
  1x 'Boo'
  1x 'Carpark'
  1x 'Chuffed'
  1x 'Cmon'
  1x 'Dunny'
  1x 'GREAT COMMS'
  1x 'Grat'
  1x 'Handy'
  1x 'Hubby'
  1x 'Keys'
  1x 'Kidding'
  1x 'LOVELY TOUCH'
  1x 'Lesson'
  1x 'Lovley'
  1x 'Mate'
  1x 'Plin English'
  1x 'Queue'
  1x 'Rang 3x'
  1x 'Repir 2/10'
  1x 'SWEET'
  1x 'Smiley'
  1x 'Speedy Next'
  1x 'Sweet'
  1x 'Tick'
  1x 'Tow bar'
  1x 'Trluy'
  1x 'Veyra S4'
  1x 'arvo'
  1x 'carpark'
  1x 'eco'
  1x 'extras'
  1x 'extras tacked'
  1x 'h7'
  1x 'jack'
  1x 'max'
  1x 'nope'
  1x 'tow bar'
  1x 'tyre'
  1x 'van'
  1x 'whine'
```

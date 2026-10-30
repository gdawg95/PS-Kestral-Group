# Export manifest

**Generated:** `python -m src.export` · 2026-10-30 12:08
**Source:** `data/clean/feedback.parquet` (sha256 `8832792c7583278f…`)
**Rows:** 7,150 · **Columns:** 15

Three formats, one dataset. Same rows, same columns, same values in each.

| File | Bytes | sha256 |
|---|---:|---|
| `feedback_clean.csv` | 1,353,755 | `7c8545944dfb5cc5c704eefdb64663ec42dc900cd228ea4c6c0a3e670bf075f8` |
| `feedback_clean.xlsx` | 773,907 | `fb81df3b4acd56c8cd879965dedab79fa8529df49da178639218b42d596c31d3` |
| `feedback_clean.json` | 3,727,607 | `10e3cf4d601d261cd9af900d4f723c79dc8a869aa18a5aa6be61d65630fbaa0d` |

## De-identification evidence

`src/export.py` refuses to write a file until these pass on the data in front of it, so this section is a record of the run that produced the files above, not a claim carried over from an earlier one.

| Check | Result |
|---|---|
| Email addresses surviving redaction | none |
| Phone numbers surviving redaction | none |
| Street addresses surviving redaction | none |
| Registration plates surviving redaction | none |
| Cells Excel would read as a formula | none |
| Columns outside the schema allowlist | none |
| Person-shaped spaCy candidates (two or more capitalised words) | none beyond the 2 reviewed exceptions below |

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

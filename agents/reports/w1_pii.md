# Report: w1_pii
**Brief:** agents/briefs/w1_pii.md (approved 29 Oct 2026) · **Branch:** `w1-pii` · **Runs on:** owner's laptop (spaCy); pattern tests also in the cloud workspace

## What I did
- `src/pii.py`:
  - `deidentify()` applies the **allowlist** (D-003): only date, department, rating and comment survive, plus `source_file` / `source_row` for lineage. Name and rego columns are read only to redact that row's own values, then dropped.
  - `redact()` replaces PII in comments with typed tokens (D-026), in this order: the row's own name/rego values → email → phone → street address → rego plates → staff roster → corpus-promoted names → spaCy person names.
  - `person_candidates()` / `promote_names()`: corpus pass that learns names used in the comments themselves.
- `tests/test_pii.py` + `tests/fixtures/pii_cases.yaml`: 41 synthetic cases (must-redact, must-not-redact, spaCy) plus allowlist, lineage and corpus-pass unit tests.
- `scripts/pii_pilot.py`: runs the redactor on Liverpool Q1 2026 and Bendigo and prints counts, a leak check and 20 redacted comments. Writes nothing to disk.

## Pilot results (gate G4)
| | Pilot 1 | Pilot 2 (after fixes) |
|---|---|---|
| Tokens | NAME 19, REGO 16, PHONE 4, EMAIL 1 | STAFF 23, NAME 11, REGO 16, PHONE 4, EMAIL 1 |
| Staff names left (any case) | not measured | **0** |
| Known first names left | not measured | 2, both ordinary words ("Will", "Lovely") |
| Owner's read of 20 samples | found misses and false positives | **all legible, no visible PII** |

Pilot 1 problems and fixes:
| Problem | Example | Fix |
|---|---|---|
| Missed names | "Raj", lower-case "dave" | Staff roster from the data's staff columns (16 names), any case; corpus pass promotes names spaCy tags mid-sentence in ≥ 2 comments if capitalised in ≥ 60% of uses (11 promoted from 5,499 comments) |
| Ordinary words redacted | "Spooky good timing", "Keys weren't ready" | Sentence-start spaCy names kept only if a known first name or followed by a staff cue |
| Staff tagged [NAME] | "thanks Ben" | Roster → [STAFF]; "thanks"/"cheers" added as staff cues |
| Model code tagged as a person | "HiLux SR5 4WD" | Entities containing digits are never names |
| Tests could not import `src` on the laptop | `uv run pytest` | `pythonpath = ["."]` in pyproject |

## Assumptions
- First names in staff columns are staff; first names in customer-name columns are customers.
- A word capitalised in most of its uses and tagged as a person in ≥ 2 comments is a name.

## Unresolved / residual risk
- A name used once, in lower case and absent from any staff column, can still get through (D-033, accepted).
- 3-letter + 3-digit trim codes (e.g. "GTS 300") match the plate shape and are redacted as [REGO]. None seen in the pilot.
- Phone numbers written with dots ("0412.345.678") are not matched.
- Owner cases: waived by the owner (D-033).

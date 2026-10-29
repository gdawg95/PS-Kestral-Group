# Brief: w1_pii
**Status:** approved by owner (gdawg95), 29 Oct 2026

Goal:            Build `src/pii.py`: the allowlist column filter and the free-text redactor, with tests that prove both work.
Inputs:          DECISIONS.md D-003, D-026; synthetic test strings written by the agent and the owner (no real feedback rows)
Outputs:         src/pii.py, tests/test_pii.py, tests/fixtures/pii_cases.yaml, agents/reports/w1_pii.md
Allowed to touch: src/pii.py, tests/, agents/reports/w1_pii.md
Not allowed:     data/, mappings/, pyproject.toml, any other src/ file
Decisions that apply: D-003 (allowlist), D-026 (tokens and method), D-013 (runs on laptop; Claude reads logs)
Steps:
  1. `keep_columns(df, mapping)`: return only columns mapped to date / department / rating / comment, plus
     pipeline fields. Anything unmapped is dropped (allowlist).
  2. `redact(text, row_values=None)` applied in this order, each step replacing matches with its token:
     a. exact-match values from the row's own name / rego columns, case-insensitive, whole-word -> [NAME] / [REGO]
     b. email -> [EMAIL]
     c. Australian phones (04xx xxx xxx, +61 4.., (0X) xxxx xxxx, 1300/1800) -> [PHONE]
     d. street addresses (number + street name + type: St, Rd, Ave, ...) -> [ADDRESS]
     e. Australian rego formats (e.g. ABC123, 1ABC234, ABC-12D, with optional space/dash) -> [REGO]
     f. spaCy `en_core_web_sm` PERSON entities -> [STAFF] when preceded/followed by a staff cue
        ("in service", "salesperson", "my advisor", "from parts", ...), else [NAME]
  3. Return the redacted text plus a count of each token type (for the DQ report; never the original strings).
  4. Tests, driven by tests/fixtures/pii_cases.yaml (input, expected):
     - must-redact: each token type, including plates inside sentences and plates with spaces/dashes
     - must-NOT-redact: model and part codes (RAV4, CX5, CX-5, V8, i30, HiLux SR5, 4WD, 2.0L, Q3 2026),
       prices ($1,200), dates (12/03/2026), job numbers if seen, "Service" as a department word
     - [STAFF] vs [NAME]: "Dave in service was great" -> [STAFF]; "I'm Sarah" -> [NAME]
     - allowlist: an unexpected column (e.g. "Customer Email 2") is dropped
  5. Owner adds their own tricky cases to the fixture file before the full run.
Pilot:           Owner runs `uv run pytest tests/test_pii.py *> logs\pii.log`; Claude reads the log.
                 Then the redactor runs over the comments of 2 files (Liverpool Q1 2026, which has name/rego
                 columns, and Bendigo) and writes ONLY a token-count summary plus 20 redacted comments to
                 logs\pii_pilot.log for the owner to eyeball. Nothing from the pilot is committed.
Done when:
  - [ ] All fixture cases pass, including every must-NOT-redact case
  - [ ] Owner has added at least 3 of their own cases
  - [ ] Owner has read the 20 pilot comments and found no leaked name, phone, email, address or plate
  - [ ] Report written to agents/reports/w1_pii.md
Report back:     what you did · assumptions · unresolved (known false positives/negatives) · token counts from the pilot

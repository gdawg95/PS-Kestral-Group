# Brief: w2_ingest
**Status:** steps 1, 2 and 5 complete; the G1 pilot has run; steps 3 and 4 wait on the
owner checking the pilot's reconciliation rows.

**Progress (29 Oct 2026, late afternoon):**
- **Checkpoint 2 passed.** The owner answered all eight questions in
  `mappings/QUESTIONS.md`, asked for four changes, and approved the revised
  `mappings/columns.yaml` (D-036 – D-045).
- `src/ingest.py` and `tests/test_ingest.py` are written: 112 test cases, synthetic
  frames only, one test per rule the owner decided.
- **Pilot run on the five awkward dealers** (six dealer codes, because North QLD is two
  dealerships): 1,884 rows read → 1,946 written, arithmetic closing, every drop reasoned.
  See `reports/reconciliation.md` and `agents/reports/w2_ingest.md`.
- Two mapping errors found and fixed in the process: the Wollongong encoding (D-043) and
  the row budget double-subtracting blank and "Total" rows (D-039).
- **Next:** the owner checks the pilot rows, then steps 3 and 4 run over all 51 files.
  `data/interim/consolidated.parquet` currently holds the pilot's 1,946 rows, not 7,159.

The questions below the steps are answered: Q1 → D-034, Q2 → D-035.

Goal:            Turn the 52 raw files into one consolidated, de-identified dataset with one row per piece of
                 feedback, and prove nothing was lost, duplicated or mis-assigned.
Inputs:          data/raw/feedback/ (52 files), data/raw/reference/dealerships.csv, reports/profiles/,
                 DECISIONS.md (D-001 – D-005, D-020, D-026 – D-033)
Outputs:         mappings/columns.yaml (per-file mapping, owner-approved before ingestion runs: Checkpoint 2)
                 src/ingest.py, tests/test_ingest.py
                 data/interim/consolidated.parquet (+ .csv copy so the cloud workspace can read it; both gitignored)
                 reports/reconciliation.md (rows in → rows out per file and per dealer, with every drop and fix counted)
                 agents/reports/w2_ingest.md
Allowed to touch: mappings/, src/ingest.py, tests/test_ingest.py, reports/reconciliation.md, Makefile (ingest target),
                 agents/reports/w2_ingest.md
Not allowed:     src/pii.py (except a bug fix, reported), DECISIONS.md, writing any raw value other than the four kept
                 columns to disk
Decisions that apply: D-001, D-002, D-003, D-005, D-020, D-026, D-027 – D-033
Runs in:         code written in the cloud workspace; ingestion runs on the owner's laptop (`make ingest`, needs spaCy),
                 output read back through the bridge (D-013)

Steps:
  1. Draft mappings/columns.yaml from the profiles. One entry per file (and per sheet / layout where they differ):
     dealer_code · header row · column → role (date / department / rating / comment / redact_name / redact_rego) ·
     date format · rating scale · sheet rules · special rules from D-032.
     **Stop here for owner approval (Checkpoint 2).**
  2. src/ingest.py reads each file per the mapping and applies, in order:
     a. row filters: blank rows, "Total ..." rows, notes / test rows, the Southport Google reviews sheet,
        Penrith "Jun 26" (D-029), Chermside Q1 FINAL (D-027);
     b. dates: per-file format; Liverpool Q3 month-first; Shepparton year fix; IPS approximate dates (flags kept);
     c. ratings: per-scale mapping to 1–5 incl. the Geelong 2025 reversal (D-020, D-030); drop rows without a rating
        (D-031); keep the raw value's scale name as `rating_scale`;
     d. department: raw text kept as `department_raw` (normalised in Wave 3);
     e. PII: `src.pii.deidentify` with the staff roster, known names and corpus pass (D-026);
     f. Toowoomba Q4 2025 pivot expanded to 71 rows (D-032 #1);
     g. North QLD split into QLD07 Rockhampton / QLD08 Townsville by the Site column;
     h. new `feedback_id`, plus `source_file`, `source_sheet`, `source_row` and flags
        (`from_summary`, `date_corrected`, `date_approx`).
  3. Join per dealer (D-002) and prove for each dealer:
     (a) file date ranges don't overlap, (b) no unexpected month gaps (Penrith June and Shepparton after March are
     expected), (c) rows in = rows out + rows dropped (by reason), (d) exact-match duplicate check on
     dealer + date + department + rating + comment.
  4. Leak check over the whole consolidated comment column: count of staff names, known first names, phone, email
     and plate patterns still present (counts only) → reconciliation report (D-033).
  5. tests/test_ingest.py: one test per D-032 rule using small synthetic frames, including "Geelong reversal applied
     to the 2025 sheet only" (D-030) and "no column outside the allowlist reaches the output".
Pilot (G1):      run on 5 awkward dealers first: Geelong (reversal), Liverpool (US dates in Q3), North QLD (split),
                 Ringwood (layout change, 10-point), Toowoomba (pivot). Owner checks their reconciliation rows.
Done when:
  - [ ] Owner approved mappings/columns.yaml (Checkpoint 2)
  - [ ] Pilot reconciliation checked by the owner
  - [ ] All 24 dealers present; rows in = rows out + dropped for every file
  - [ ] Duplicate check run and result recorded (closes D-019)
  - [ ] Leak check counts in the reconciliation report
  - [ ] Tests pass on the laptop
  - [ ] Report written to agents/reports/w2_ingest.md
Report back:     what you did · assumptions · unresolved · rows in / out / dropped per dealer

Questions for the owner — both answered 29 Oct 2026:
  Q1. **"Hunter Motors feedback 25-26.xlsx" → NSW05 Kestrel Newcastle?** ANSWERED: yes, plus IPS → QLD03 Ipswich and
      North QLD → QLD07 Rockhampton *and* QLD08 Townsville (split by its Site column). Recorded as **D-034** with the
      evidence. D-034 also retires `dealer_match_min_confidence`, since no free-text dealership column survives
      ingestion and there is nothing left to fuzzy-match.
  Q2. Merge Wave 3 (department + rating normalisation) into this agent? ANSWERED: **no** — recorded as **D-035**.
      Departments stay raw in Wave 2 (`department_raw`) and are normalised in Wave 3. Ratings still convert to 1–5 at
      ingestion, because D-031 drops rows with no usable rating and that cannot be decided without converting; both
      `rating_raw` and `rating_1to5` are written so the conversion stays auditable. The pandera suite stays in Wave 3
      with a different agent (D-017, producer ≠ checker).

Also changed since this brief was drafted:
  - The canonical schema now exists as `src/schema.py` (15 columns, `validate_frame` proves the allowlist held).
    Ingest writes exactly those columns in that order.
  - D-013 revision 2: Claude runs the pipeline and the tests directly in `C:\PS-Kestral-Group`, so step 2 onward no
    longer needs the owner to run commands and paste logs. The owner still runs Docker/Ollama and still merges.
  - `data/interim/consolidated.parquet` no longer needs a `.csv` twin: the workspace round-trip that required it is
    gone, and pyarrow 26 is installed locally.

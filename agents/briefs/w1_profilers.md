# Brief: w1_profilers
**Status:** approved by owner (gdawg95), 29 Oct 2026

Goal:            Produce one profile JSON per feedback file describing its structure, so the Wave 2 mapping can be drafted from evidence.
Inputs:          the 54 files in the challenge pack `feedback/` folder (cloud workspace copy, read-only); reference/dealerships.csv
Outputs:         reports/profiles/<file-stem>.json (one per file), reports/profiles/_index.csv (one row per file),
                 agents/reports/w1_profilers.md
Allowed to touch: reports/profiles/, scripts/profile_file.py, agents/reports/w1_profilers.md
Not allowed:     data/raw (read only), src/, mappings/, any copy of cell values outside the agent's memory
Decisions that apply: D-001, D-002, D-003 (allowlist; profiles hold no PII), D-013 (runs in the cloud workspace)
Runs in:         cloud workspace (pandas + openpyxl + python-calamine are installed there)
Each profile records:
  - file name, type, encoding, delimiter (CSV), sha256
  - every sheet, with hidden/visible state and dimensions
  - detected header row (and why), merged cells, blank or totals/notes rows
  - per column: name, inferred type, null %, number of distinct values,
    proposed role (date / department / rating / comment / identifier / vehicle / other)
  - date columns: detected format(s), min and max date, number of unparseable values
  - rating columns: distinct values with counts (this reveals the scale: 1-5, 1-10, stars, words)
  - department columns: distinct values with counts
  - row count (data rows only)
  - oddities: duplicate-looking files, more than one site in a file, mixed formats, summary-only sheets
Privacy rule:     comment, name, phone, email, rego and vehicle columns are described by type, null % and
                 length statistics only. No raw cell values from those columns appear in any profile.
                 Department and rating values may be listed (they are categories, not PII).
Split:           4 groups (VIC, NSW, QLD, Parramatta's 12 monthly files) once the pilot passes.
Pilot (G1):      profile 3 files first, then stop for owner review:
                 - Chermside Q1 2026 FINAL.xlsx + Chermside Q1 2026 FINAL v2.xlsx (likely duplicate)
                 - North QLD feedback Rocky  TSV.xlsx (likely two sites in one file)
                 - chatswood_2025_q4.csv (semicolon-delimited)
Done when:
  - [ ] 54 profile JSONs + _index.csv; every file in the folder accounted for
  - [ ] Owner has compared the 3 pilot profiles with the spreadsheets and approved
  - [ ] Owner has spot-checked 3 more profiles of their choice
  - [ ] grep of reports/profiles/ for phone/email/rego patterns returns nothing
  - [ ] Oddities list in the report, each with a proposed decision for the owner
  - [ ] The 2 files beyond the brief's stated 52 are identified
Report back:     what you did · assumptions · unresolved · files in / profiles out

# Brief: w1_scaffold
**Approved by:** owner (gdawg95), 29 Oct 2026, in the Wave 1 planning conversation.

Goal:            Create the repository skeleton and the guardrails that stop raw data or PII from ever being committed.
Inputs:          PLAN.md §5–7, DECISIONS.md (D-003, D-013, D-014, D-015, D-026)
Outputs:         Folder tree (PLAN §7), pyproject.toml + uv.lock, Makefile (stub targets), config.yaml,
                 .pre-commit-config.yaml, scripts/check_no_data.py, scripts/check_nlp_env.py,
                 docker-compose.yml, agents/briefs/_template.md, agents/reports/_template.md
Allowed to touch: repo root config files, scripts/, agents/, empty folders with .gitkeep, DECISIONS.md (sync only)
Not allowed:     data/raw contents, src/ logic (PII belongs to w1_pii), mappings/columns.yaml
Decisions that apply: D-003, D-013, D-014, D-015, D-017, D-026
Steps:
  1. Branch `w1-scaffold` from main.
  2. Create folder tree with .gitkeep placeholders.
  3. Write pyproject.toml (Python 3.12) with a core group (workspace) and an `nlp` group (laptop); run `uv lock`.
  4. Makefile with stub targets: ingest, validate, classify, analyse, figures, test, all, nlp-check.
  5. config.yaml with paths, seeds, model tags (placeholders where undecided).
  6. Guardrails: .gitignore (data dirs, spreadsheets) + pre-commit hook blocking any spreadsheet/data file
     outside mappings/ and reports/ even if force-added; ruff; nbstripout; gitleaks.
  7. docker-compose.yml for Ollama (image digest pinned once the owner supplies it).
  8. scripts/check_nlp_env.py: laptop check that sentiment + embedding models download and run.
Pilot:           n/a (single, non-bulk agent)
Done when:
  - [ ] `git add data/raw/test.xlsx` is refused by .gitignore
  - [ ] `git add -f data/raw/test.xlsx` then commit is refused by the pre-commit hook
  - [ ] `uv sync` succeeds; `make test` runs
  - [ ] Report written to agents/reports/w1_scaffold.md
Report back:     what you did · assumptions · unresolved · files created

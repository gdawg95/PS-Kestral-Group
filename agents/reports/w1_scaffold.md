# Report: w1_scaffold
**Brief:** agents/briefs/w1_scaffold.md
**Branches:** `w1-scaffold` (29 Oct, morning), `w1-wrapup` (29 Oct, afternoon — the items below marked *late*)
**Date:** 29 Oct 2026

Filed late. The scaffold agent delivered its files in the morning but never wrote a
report, so the control loop's step 5 was missing for this agent while the PII and
profiler agents had theirs. This report covers both the original run and the gaps
closed afterwards on `w1-wrapup`.

## What I did

Morning (`w1-scaffold`):

- Folder tree per PLAN.md section 7, with `.gitkeep` placeholders.
- `pyproject.toml` (Python 3.12) with a core group, a `dev` group and an `nlp` group
  that installs only on the laptop (D-013). `uv.lock` generated on the laptop by the
  owner and committed.
- `config.yaml`: paths, seed, model tags, thresholds with `TBD` where the owner has
  not set them yet (gate G7).
- `.gitignore`: all data directories and every spreadsheet extension, from the first
  commit, because git history cannot be cleaned later (D-015).
- `.gitattributes` for line-ending normalisation.
- `docker-compose.yml` for Ollama, image pinned by digest and the model ID recorded
  (D-012), with a fixed project name so the existing model volume is reused.
- NLP environment check, run by hand rather than as a script: Hugging Face and PyPI
  are blocked in the cloud workspace, so the sentiment and embedding models move to
  the laptop. Written up in D-013 rather than as `scripts/check_nlp_env.py` output.

Afternoon, *late* (`w1-wrapup`):

- `scripts/check_no_data.py` + `.pre-commit-config.yaml` — the guardrail the brief
  promised. Every hook is `language: system` running through `uv run --no-sync`,
  because the laptop cannot reach the pre-commit hook repositories (D-013).
- `Makefile` with the stage targets, and `scripts/run.ps1` mirroring them in
  PowerShell because the laptop has no `make`.
- `src/schema.py` — the canonical schema. PLAN.md section 5 promised a pydantic
  schema but no Wave 1 brief owned it, and Wave 2 was about to write a Parquet file
  with no declared contract.
- `scripts/check_mapping.py` — cross-checks `mappings/columns.yaml` against the Wave 1
  profiles. Not in the brief; added because Checkpoint 2 asks the owner to approve a
  31-layout mapping by hand and this turns "looks right" into "agrees with the profiles".
- `agents/briefs/_template.md`, `agents/reports/_template.md`.

## Checks I ran

| Check | Command | Result |
|---|---|---|
| raw data cannot be staged | `git add data/raw/test.xlsx` | refused by `.gitignore` |
| raw data cannot be force-added | `git add -f data/raw/test.xlsx` then the hook | refused, exit 1, names the path and the reason |
| hooks are valid and pass | `pre-commit run --all-files` | data guardrail Passed · ruff lint Passed · nbstripout skipped (no notebooks) |
| test suite | `python -m pytest -q` | 66 passed, 2 skipped |
| schema | round-trip a record, then add a stray column | `validate_frame` returns `["columns outside the allowlist reached the output: ['oops']"]` |
| mapping vs profiles | `python scripts/check_mapping.py` | 52/52 files, every sheet, header row, row count and column agree |

## Assumptions

- **No `ruff format` gate.** `pyproject.toml` configures `ruff.lint` only. Turning
  formatting on would rewrite `src/pii.py`, which belongs to the w1_pii agent, hours
  before code freeze. Linting is enforced; formatting is not.
- **gitleaks is not a hook.** It needs a binary the laptop cannot download. It stays a
  manual pre-public step (D-015) and has a `make gitleaks` target that fails loudly
  if the binary is missing.
- **`scripts/check_nlp_env.py` was not written.** The check it was meant to automate
  was done by hand and its result is recorded in D-013. Writing the script now would
  produce evidence for a decision already made. The `nlp-check` target points at it,
  so it can be added later without changing the interface.

## Unresolved

- `make` is unavailable on the owner's laptop, so `make all` — the reproducibility
  claim in PLAN.md section 6 and the command the Wave 5 independent verifier runs —
  has only been exercised as `scripts/run.ps1`. The Makefile itself is untested.
- The pipeline stage modules the Makefile calls (`src.ingest`, `src.validate`,
  `src.classify`, `src.analyse`, `src.figures`) do not exist yet, so every target
  except `test`, `lint` and `hooks` fails today. That is expected at the end of Wave 1.
- `config.yaml` still holds three `TBD` thresholds (`dealer_match_min_confidence`,
  `nlp_pass_mark`, `trend_evidence`). Gate G7 requires each to be set and committed
  before the matching results exist. `dealer_match_min_confidence` may be retired —
  see D-034.

## Done-when criteria

- [x] `git add data/raw/test.xlsx` is refused by `.gitignore`
- [x] `git add -f data/raw/test.xlsx` then commit is refused by the pre-commit hook
- [x] `uv sync` succeeds; the test suite runs (66 passed, 2 skipped)
- [x] Report written to `agents/reports/w1_scaffold.md`

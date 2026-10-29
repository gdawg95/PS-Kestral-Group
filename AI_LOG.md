# AI_LOG — Kestrel Motor Group: Data & AI Challenge

A record of every material use of AI in this project: what was asked, what it produced, how it was checked, and the verdict. Entries are added by the orchestrator after each agent run or conversation; the **Verified by** and **Verdict** fields are completed by the owner.

## Tools in use

| Tool | Role |
|---|---|
| Claude (Opus 5.5, claude.ai project) | Planning, orchestration, coding assistant, agent runs in the cloud workspace |
| Open-source sentiment model (Hugging Face) | Comment sentiment |
| sentence-transformers / BERTopic | Theme discovery and assignment |
| Ollama + 3B open-source LLM (optional) | Richer theme reasoning on negative/mixed comments |

## Summary of AI errors caught

Fill this in as you go. It becomes the "where AI got it wrong" section of the technical report.

| # | Entry | What the AI got wrong | How it was caught | Fix |
|---|---|---|---|---|
| 1 | AI-002 | Recommended running agents on the laptop (option C) before testing what the bridge could do; the bridge shell turned out to have no network, Docker or package access | AI tested it after the owner agreed | Arrangement revised: owner runs, Claude reads logs (D-013 revision) |
| 2 | AI-002 | Said Scaffold had started when it had not, and said the 52 feedback files were not available when they were already in the project | AI noticed on the next turns | Corrected in conversation |
| 3 | AI-003 | Staff first names ("Taken by", "Logged by", "Card given by", Southport "Reviewer") listed in profiles, against the privacy rule | AI's own review of the full run, before the owner saw it | Withhold person-like columns; name scans added |
| 4 | AI-003 | **Tamworth:** a text-date data row (row 10) mistaken for a second header. Profile reported 142 rows instead of 143, a false "format change", wrong empty % for HOW WAS IT, and one comment's text written as a column name | **Owner's spot-check** against the spreadsheet | Header detection rejects dates, numbers and sentences; regression tests; only Tamworth changed on re-run |
| 5 | AI-003 | First full run missed Geelong 2025's **reversed scale** (note above the header) and Penrith's **"Jun 26" sheet copied from "Jul 26"** | Rating sanity check the **owner asked for**; AI investigated two suspicious numbers | Profiler reads scale notes and compares sheets within a file; D-029, D-030 |
| 6 | AI-004 | Redactor missed "Raj" and lower-case "dave", and redacted the ordinary words "Spooky" and "Keys" | **Owner's laptop pilot run**; AI traced each sample back to its cause | Staff roster, sentence-start guard, corpus name pass; tests for each case |
| 7 | AI-004 | Tests could not import the code on the laptop (`No module named 'src'`): AI had only run them with a different command | Owner's laptop run | `pythonpath` set in pyproject |
| 8 | AI-004 | spaCy redacted the model code "HiLux SR5 4WD" as a person, and the new guard skipped "Dave in service" | Owner's laptop run of the spaCy tests | Digits never in names; staff cue overrides the guard |
| 9 | AI-005 | Wave 1 was reported complete while four items from the w1_scaffold brief had never been delivered: Makefile, pre-commit guardrail, the scaffold's own report, and the pydantic schema PLAN.md promised. Checkpoint 1's force-add test had therefore never been run | AI re-checked each brief's done-when list against the repository at the owner's request | Delivered on `w1-wrapup`; both Checkpoint 1 criteria now demonstrated |
| 10 | AI-005 | The `w2-ingest` branch carried an older AI_LOG in which the owner's four verdicts were back to `<owner to complete>` placeholders. Merging it would have erased the sign-offs | AI diffed the branch against `main` before recommending a merge | Only the brief was taken across; the branch is to be discarded rather than merged |
| 11 | AI-005 | The AI's own first draft of `columns.yaml` had two errors: Ringwood Q1 2026's second layout was given header row 1 instead of 37 (which would have misread 79 rows as out-of-5 instead of out-of-10), and North QLD's `Site` column was unaccounted for | `scripts/check_mapping.py`, written to cross-check the draft against the profiles before the owner read it | Both fixed; the checker now passes on all 52 files |
| 12 | AI-006 | The draft row budget queued the blank and "Total" rows as a further subtraction. They were never inside the 7,162 profiled rows — the Wave 1 profiler had already excluded them — so the reconciliation would have failed to close by 26 rows | AI counted the blank and summary rows directly from the workbooks while implementing the owner's Q7 answer, and compared them with the profiler's own row rule | Budget rewritten; 14 blank and 12 "Total" rows now reported as accounted-for-but-not-counted. D-039, and a test asserts the identity |
| 13 | AI-006 | `mappings/columns.yaml` declared `utf-8` for both Wollongong CSVs. They are Windows-1252. Reading them as UTF-8 raises `UnicodeDecodeError`, losing the dealership's 285 rows; forcing it would silently corrupt apostrophes inside the comments that feed the NLP | AI decoded every CSV in the pack byte by byte while counting blank rows — not a check anyone had asked for | Encoding corrected to `cp1252`. D-043 |
| 14 | AI-006 | `make lint` and therefore `make all` could not succeed: both ran `ruff format --check`, which fails on 8 files. `agents/reports/w1_scaffold.md` had already recorded that formatting is deliberately not gated, so the Makefile contradicted the project's own decision — and `make all` is the command the Wave 5 independent verifier runs | AI ran `ruff format --check` against the repository while checking the ingest targets | Both `Makefile` and `scripts/run.ps1` now run `ruff check` only, with the reason in a comment |
| 15 | AI-006 | The generic row filter would not have caught two of Southport's four junk rows: one has an empty date cell and a plausible rating of 3, the other a date of 01/01/1900, so neither looks like junk from its leading cells | AI ran the filter against the real sheet rather than assuming the keyword rule was enough | The mapping now names all four by spreadsheet row *and* comment value, and the run fails if a named row's comment ever changes — so a re-sent file cannot cause real feedback to be dropped silently |

---

## Entry template

```
### AI-NNN · <wave/phase> · <agent or conversation> · <date>
- **Tool / model:**
- **Task / key prompt:** <brief link or one-paragraph summary>
- **Output:** <files / commit>
- **Checks performed:** <what you looked at, sample sizes, reconciliations>
- **Issues found:**
- **Verdict:** Accepted / Corrected / Rejected — <why>
- **Verified by:** <owner, date>
```

---

## Entries

### AI-001 · Planning · Planning conversation (Claude) · 28–29 Oct 2026
- **Tool / model:** Claude Opus 5.5 (claude.ai, project "PS Take Home – Kestral Motor Group Analysis").
- **Task / key prompts:**
  - "Read the brief, then help me create a plan for how to address the problems listed."
  - "Visualise the plan as a flow chart and suggest alternative ways to organise it, given under 36 hours."
  - "Detail the setup and PII guardrails step."
  - "How much will I need to do manually vs defer to AI?" · "Suggest a tech stack per phase; everything must be reproducible." · "Ask me at least 7 questions so the plan is defensible." · "Where can agents be used, and how should a master agent orchestrate?" · "Add more human-in-the-loop approval."
- **Output:** phased plan, flow chart, PII policy, tech stack, decision questions, agent map and waves, HITL control loop and gates; written up as `PLAN.md`, `DECISIONS.md`, and this file.
- **What the owner decided (not the AI):** unit of analysis; definition of negative; per-site joining; dropping customer identifiers; including the closed site; two reports; non-negotiables; zero budget / open source; no Colab; Docker for the LLM; extra HITL gates G7 and G9; separate conversations per phase.
- **Where the AI's suggestions were changed by the owner:**
  - AI initially proposed hashing customer identifiers → owner chose to drop them (identity is inconsistent and not needed).
  - AI initially assumed a paid LLM API → owner set zero budget; plan switched to open-source models.
  - AI suggested Google Colab for inference → owner rejected based on past usage-limit problems; switched to Docker on laptop.
  - AI's first plan was a waterfall over 36 hours → reorganised into waves with checkpoints after the deadline moved to Friday 3pm.
- **Where the owner pushed back and the AI held its position:** owner initially considered skipping duplicate checks; AI recommended a cheap verification step instead of an assumption (adopted as D-002).
- **Checks performed:** owner reviewed each plan section and question in conversation.
  
Verdict: Project plan established. Plan is to be updated as further information/issues arise. 
Verified by: S Gyaw

### AI-002 · Wave 1 · Scaffold and NLP environment check · 28–29 Oct 2026
- **Tool / model:** Claude Opus 5.5 (cloud workspace + desktop-app bridge to the owner's laptop).
- **Task / key prompt:** "Time to start Wave 1. Explain what needs to be done, the tools and architecture." Then: scaffold the repo (brief `agents/briefs/w1_scaffold.md`) and check whether the NLP models can run in the workspace.
- **Output:** branch `w1-scaffold`: folder tree, `pyproject.toml`, `uv.lock` (generated on the laptop), `config.yaml`, pinned `docker-compose.yml`, `.gitignore` / `.gitattributes`; D-013 revision.
- **Checks performed:**
  - Workspace: Hugging Face (403), PyPI and the PyTorch index unreachable; GitHub reachable.
  - Laptop (owner): WSL2 limited to 8 CPUs / 24 GB (`docker info`); Ollama `qwen2.5:3b` at 12.83 tokens/s; image digest and model ID pinned.
  - Laptop bridge (AI): Linux sandbox, 2 CPUs / 3 GB, sees only `C:\PS-Kestral-Group`, no network or Docker.
  - `uv sync --group nlp` on the laptop: 123 packages installed, log read by the AI.
- **Issues found:** see summary rows 1–2. The owner chose option C on the AI's recommendation; testing showed it could not work as described, so it became "owner runs, Claude reads logs".
  
Verdict: Established required architecture and hardware to prepare fro overll project.
Verified by: S Gyaw, 29/10/2026

### AI-003 · Wave 1 · w1_profilers (structure profiles of all 52 feedback files) · 29 Oct 2026
- **Tool / model:** Claude Opus 5.5, cloud workspace (pandas + openpyxl). Brief `agents/briefs/w1_profilers.md`, approved by the owner.
- **Task / key prompt:** profile each file's sheets, headers, columns, null rates, date formats and rating/department values, with no PII in the output; pilot on 4 awkward files first (gate G1).
- **Output:** branch `w1-profilers`: `scripts/profile_file.py`, `scripts/check_ratings.py`, `reports/profiles/` (52 profiles, index, overlaps, review sheet), `reports/rating_check.md`, `tests/test_profile_file.py`, `agents/reports/w1_profilers.md`.
- **Checks performed:**
  - **Pilot (owner):** 4 profiles compared with the spreadsheets, 43/43 lines confirmed (`agents/reports/w1_profilers_pilot_review.md`). Chermside Q1 FINAL found to be fully contained in FINAL v2 → D-027.
  - **Spot-checks (owner):** Bendigo, Frankston, Tamworth, all confirmed after the fix below (`agents/reports/w1_profilers_spotcheck.md`).
  - **Tamworth issue (owner):** the owner's first spot-check found the profile said 142 data rows when the spreadsheet has 143, that HOW WAS IT showed no empty values when some are empty, and that the "format change" in the review didn't exist. Cause: the AI's new "second header" check mistook data row 10 for a header because its text date "27/10/2025" matched the "/10" rating pattern. The bug also wrote one comment's text (no personal details) into the profile as a column name; that text remains in this branch's history and is kept out of `main` by squash-merging. Fixed and re-run; only Tamworth changed (now 143 rows, HOW WAS IT 7.0% empty, recognised as a rating). Six regression tests added.
  - **Privacy (AI):** withheld-column check (0 leaks); email/phone pattern scan (0); 2,674 raw name tokens cross-checked against the profiles (only generic words such as "Service").
  - **Rating sanity check (owner request):** every rating column in every sheet mapped to 1–5; no values failed to map. Two suspicious results investigated → Geelong 2025 reversed scale (D-030), Penrith Jun = Jul copy (D-029).
- **Issues found:** see summary rows 3–5.
- **Owner decisions arising:** D-020 (all ratings to 1–5, incl. 10-point rule), D-027, D-028, D-029, D-030, D-031 (drop 13 rows without a rating), D-032 (15 findings, defaults accepted).

Verdict: Corrections from Tamworth profile wrong until fixed; re-checked.
Verified by: S Gyaw, 29/10/2026

### AI-004 · Wave 1 · w1_pii (allowlist + comment redaction) · 29 Oct 2026
- **Tool / model:** Claude Opus 5.5 wrote the code; spaCy `en_core_web_sm` 3.8.0 does the name detection (on the owner's laptop).
- **Task / key prompt:** build `src/pii.py` per brief `agents/briefs/w1_pii.md`: keep only date, department, rating and comment; redact names, staff, plates, phones, emails and addresses in comments (D-003, D-026).
- **Output:** branch `w1-pii`: `src/pii.py`, `tests/test_pii.py`, `tests/fixtures/pii_cases.yaml`, `scripts/pii_pilot.py`, `agents/reports/w1_pii.md`.
- **Checks performed:**
  - Pattern tests in the workspace; full suite including spaCy tests on the laptop (logs read by the AI).
  - **Two pilots (owner):** 20 redacted comments each from Liverpool Q1 2026 and Bendigo. Pilot 1 showed misses and false positives; after fixes the owner read pilot 2: "all legible and understandable", no visible personal data.
  - Leak check (AI): 0 staff names left in either case; 2 known first names left, both ordinary words.
- **Issues found:** see summary rows 6–8. Also: the owner's assumption that `[STAFF]` would be rare was wrong; 13% of comments mention a staff name.
- **Owner decisions arising:** D-026 method update accepted; D-033 (owner test cases waived, residual risk accepted).
  
Verdict: Corrected the issuse that pilot 1 found misses; accepted after pilot 2.
Verified by: S Gyaw, 29/10/2026

### AI-005 · Wave 1 wrap-up and Wave 2 mapping · Claude Code (desktop app, laptop repo) · 29 Oct 2026
- **Tool / model:** Claude Opus 5, running in the laptop repository `C:\PS-Kestral-Group` with the project virtual environment (see D-013 revision 2). Branch `w1-wrapup`.
- **Task / key prompts:** "Read & explain what needs to be done for Wave 2 ... are there any dependencies on wave 1?" then "let's first fix the opened/unresolved stuff from Wave 1 ... Create the mapping of columns so that I can check before you do your thing. for those that you struggle with, pls list some suggestions or questions".
- **Output:**
  - Wave 1 gaps closed: `Makefile` + `scripts/run.ps1`, `.pre-commit-config.yaml` + `scripts/check_no_data.py`, `src/schema.py`, `agents/reports/w1_scaffold.md`, brief and report templates.
  - Wave 2 step 1: `mappings/columns.yaml` (31 layouts, all 52 files), `mappings/QUESTIONS.md` (8 open questions), `scripts/check_mapping.py`.
  - Decisions recorded: D-034 (file → dealer code), D-035 (Wave 2/3 scope split), D-013 revision 2.
- **Checks performed:**
  - Checkpoint 1, both criteria: `git add data/raw/test.xlsx` refused by `.gitignore`; `git add -f` then the hook refused with exit 1. Test file removed afterwards.
  - `pre-commit run --all-files`: data guardrail Passed, ruff lint Passed.
  - `pytest -q`: 66 passed, 2 skipped (unchanged by this work).
  - `scripts/check_mapping.py`: 52/52 files, every sheet, header row, row count and column reconcile against the Wave 1 profiles.
  - Three mapping assumptions converted from inference to evidence by reading the data: Liverpool Q3 is month-first (85/85 parse into Jul–Sep 2026; day-first parses 29/85), Hunter Motors' `Dealer` is `HUNTER` on all 303 rows and IPS's `Site` is `KMG-IPS` on all 277, and North QLD's `Site` holds exactly six spellings splitting 202/354.
- **Issues found:** see summary rows 9–11.
- **Where the owner's instruction was corrected:** the owner approved the dealer codes as "QLD 02 Ipswich" and "QLD 07 is the combination of Rockhampton & Townsville". Ipswich is QLD03 (QLD02 is Springwood, which has its own file) and QLD07 is Rockhampton with QLD08 Townsville. D-034 records both the approval and the correction; the mapping implements the corrected codes.
- **Owner decisions arising:** D-034, D-035, D-013 revision 2. Eight further questions are open in `mappings/QUESTIONS.md`, three of which (Q1 Bendigo codes, Q2 Southport no-date row, Q3 Toowoomba missing Sales) change rows in the dataset.
- **Not done / not verified:** the Makefile itself is untested because the laptop has no `make`; the pipeline stage modules it calls do not exist yet. No data has been ingested — Checkpoint 2 blocks it.
- **Verdict:** <owner to complete>
- **Verified by:** <owner, date>

### AI-006 · Wave 2 · Checkpoint 2, ingestion and the G1 pilot · Claude Code (desktop app, laptop repo) · 29 Oct 2026
- **Tool / model:** Claude Opus 5, in `C:\PS-Kestral-Group` with the project virtual environment (D-013 revision 2). Branch `w1-wrapup`.
- **Task / key prompts:** the owner's answers to all eight questions in `mappings/QUESTIONS.md`, plus four changes to the mapping: "the 'staff' col can be dropped as well", "note where all the formatting changes are across all worksheets — I will add them to the client report", "I am OK with the imputation of estimated dates using context clues from neighbouring rows", "the current North QLD feedback sheet needs to be split into Rockhampton and Townsville sheets individually". Then, mid-task: "are there any other parts that require my input? I will need to leave you running for approx. 1 hr" — answered by asking for the two decisions that were genuinely the owner's (Checkpoint 2 sign-off, and the trend threshold) before they left.
- **Output:**
  - `mappings/columns.yaml` revised and approved at Checkpoint 2; `mappings/QUESTIONS.md` closed out.
  - `src/ingest.py` — mapping-driven, no per-file branches in the code.
  - `tests/test_ingest.py` — 112 cases on synthetic frames, one per owner decision.
  - `reports/formatting_changes.md` — the register the owner asked for: 13 kinds of inconsistency across 52 files and 84 worksheets, each located by dealership.
  - `scripts/trend_evidence.py` → `reports/trend_evidence.md`, because the owner chose to set the trend threshold after seeing the data.
  - `reports/reconciliation.md` — the G1 pilot, and `agents/reports/w2_ingest.md`.
  - Decisions recorded: D-036 – D-045.
- **Checks performed:**
  - `ruff check .`: all checks passed. `pytest -q`: 178 passed, 2 skipped (112 of them new).
  - `scripts/check_mapping.py`: 52/52 files reconcile. The new `department_map` check was tested by breaking `S: Sales` on purpose and confirming it was caught.
  - Pilot: 1,884 rows read → 1,946 written across six dealer codes; the arithmetic closes; `validate_frame` reports no problems and nothing outside the allowlist.
  - The three riskiest conversions were each checked against the number the owner's own decision predicted, not against the code's output: Geelong's 2025 sheet goes from a raw mean of 2.40 to 3.60, exactly as D-030 states, with 2026 untouched; the 1–10 → 1–5 table matches D-020 value for value; Ringwood's split at row 37 lands on a month boundary (33 rows out-of-5 in January, 79 out-of-10 from 2 February), which is independent support for the owner's confirmation rather than a restatement of it.
  - North QLD split: 202 / 354, exactly as asserted. Liverpool Q3: 85 rows, all inside Jul–Sep 2026, range assertion passed.
  - Southport's row filter run against the real sheet: rows 23, 167 and 196 dropped as test rows, row 192 as a note — what the owner decided, no more.
- **Issues found:** see summary rows 12–15. Three of the four were found by checking something nobody had asked about.
- **Where the owner's instruction needed qualifying:** the owner asked for the staff column to be dropped "as it will not provide much useful info for the analysis". That was already true — it never reaches the dataset — but the same columns build the roster that strips staff names out of comment text, and the PII pilot measured that at 728 of 5,412 comments. Dropping the columns outright would leave roughly 700 comments naming an employee, in the text that goes to the NLP and the client report. Recorded as D-041: the columns are read in memory and discarded, nothing about staff is analysed or written, and the owner has a one-word override if they want the roster gone too.
- **Also qualified:** the owner referred to Southport's no-date row as row 166; it is row 167. Both the draft's number and the owner's were off by one, which is why the mapping now records every junk row by spreadsheet row *and* cell values. The row is a test row either way — its comment reads "testing new form" — so the decision stands.
- **Owner decisions arising:** D-036 – D-045. Checkpoint 2 passed; the trend threshold stays TBD at the owner's choice, with `reports/trend_evidence.md` written to support it.
- **Not done / not verified:** steps 3 and 4 of the brief (per-dealer joins with the four D-002 proofs, and the whole-corpus leak check) have not run, so **D-019 is still open**. `data/interim/consolidated.parquet` holds the pilot's 1,946 rows, not the expected 7,159 — anything reading it now reads a sixth of the data. `reports/trend_evidence.md` covers 6 of 24 dealerships. The Makefile is still untested because the laptop has no `make`. `nlp_pass_mark` is still TBD.
- **Verdict:** <owner to complete>
- **Verified by:** <owner, date>

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
  
Verdict: Plan established. Start Wave 1 so that further information can be discovered for other decisions.
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
- **Verdict:** <owner to complete>
- **Verified by:** <owner, date>

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
- **Verdict:** <owner to complete, e.g. "Corrected: Tamworth profile wrong until fixed; re-checked">
- **Verified by:** <owner, date>

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
- **Verdict:** <owner to complete, e.g. "Corrected: pilot 1 found misses; accepted after pilot 2">
- **Verified by:** <owner, date>

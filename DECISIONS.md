# DECISIONS — Kestrel Motor Group: Data & AI Challenge

Each decision records what was decided, the options considered, and why. Status is **Decided**, **Provisional** (to confirm after data is seen), or **Deferred**.

Format: `D-NNN · Title · Status · Date`

---

## Scope and data

### D-001 · Unit of analysis: one row = one piece of feedback · Provisional · 29 Oct 2026
- **Decision:** Every row in every source spreadsheet is treated as one feedback record, with a new `feedback_id` assigned at ingestion.
- **Why:** In the 10 of 52 files scanned so far, each row is a distinct response (customer/date/department). Keeps counts simple and traceable.
- **Revisit if:** profiling finds rows covering several departments or multiple comments per row.

### D-002 · Join each site's files into one running sheet before consolidation · Decided · 29 Oct 2026
- **Decision:** Each dealership should have one workbook; sites sent files on different schedules. Files are joined per site first, then consolidated.
- **Verification (to turn the assumption into evidence):** the joiner agent must prove for each site that (a) file date ranges don't overlap, (b) there are no unexpected gaps, (c) rows in = rows out, and (d) an exact-match duplicate check on dealership + date + department + score + comment finds nothing (or flags what it finds).
- **Options considered:** assume no overlap (rejected — the brief says some sites keep a running workbook, so repeats are plausible); full fuzzy dedup (rejected — overkill for the timeframe).

### D-003 · Keep only four content columns; drop everything else · Decided · 29 Oct 2026 (revised)
- **Decision:** From each source file, keep only:
  1. **Date** of service/feedback
  2. **Department** (text)
  3. **Rating / satisfaction** (numeric after Wave 3 scale mapping)
  4. **Comment** (free text, redacted per D-026)

  Every other column is dropped at first ingestion — customer names, IDs, DMS numbers, phones, emails, addresses, rego, and vehicle make/model. No hashing.
- **Added by the pipeline (not from source columns):** `feedback_id` (new), `dealer_code` (from file name/sheet, matched to `dealerships.csv`), and lineage fields `source_file` + `source_row` so any record can be traced back to its spreadsheet.
- **Implementation:** an **allowlist**, not a blocklist — any source column not mapped to one of the four in `mappings/columns.yaml` is dropped, so an unexpected PII column is excluded by default.
- **Why:** these four columns answer all three business questions; no question needs customer-level or vehicle-level analysis; brand comes from `dealerships.csv`.
- **Exception:** a row's customer-name and rego values may be read *transiently* during ingestion to redact those exact strings from that row's comment (D-026), then discarded. They are never written to any interim or clean file.
- **Revision note:** earlier version used a drop-list of identifier columns; changed to an allowlist after the owner reviewed all 52 files.

### D-004 · Definition of negative feedback · Provisional · 29 Oct 2026
- **Decision:** A record is negative if its **score is 1–2 on a 1–5 scale** (3 = neutral) **OR** its comment's sentiment is negative. The score is the minimum signal, because many customers leave no comment.
- **To confirm after profiling:** equivalent thresholds for sites using other scales (1–10, 0–10, stars, words), and how to handle score/sentiment disagreement in reporting.

### D-005 · Include all dealerships, including the closed site · Decided · 29 Oct 2026
- **Decision:** Include all 24 dealerships. One site closed at the end of March 2026; it has no feedback after closure (~52 rows).
- **Mitigation:** trend results are shown with and without the closed site, plus a footnote, so a composition change can't masquerade as improvement.

### D-006 · Coverage reported as a limitation (for now) · Provisional · 29 Oct 2026
- **Decision:** Uneven feedback volumes per site are reported as a limitation. A feedback-per-transaction metric is computed from `monthly_revenue.csv` once data is consolidated; normalisation decision follows from that.

### D-026 · Free-text redaction tokens · Decided · 29 Oct 2026
- **Decision:** PII inside comments is replaced with typed tokens so the analysis keeps the signal that something was mentioned:
  | Found in comment | Token |
  |---|---|
  | Vehicle registration number | `[REGO]` |
  | Staff member's name | `[STAFF]` |
  | Customer's own / other person's name | `[NAME]` |
  | Phone number | `[PHONE]` |
  | Email address | `[EMAIL]` |
  | Street address | `[ADDRESS]` |
- **Method:** (1) exact-match redaction of that row's own name/rego values (where the source has those columns); (2) regex for phones, emails, addresses and Australian rego formats; (3) spaCy NER for remaining person names.
- **[STAFF] vs [NAME]:** an NER person name is tagged `[STAFF]` only when it appears in a staff context (e.g. "Dave in service", "my salesperson Priya"); otherwise `[NAME]`. Owner expects `[STAFF]` to be rare, so imprecision here is low-impact.
- **Known risk:** rego regex can false-positive on model and part codes (e.g. RAV4, CX5, V8). The test suite must include these as must-*not*-redact cases.

## Outputs

### D-007 · Two reports · Decided · 29 Oct 2026
- **Decision:** (1) a non-technical business report for the Head of CX; (2) a technical report (`README.md`) for reviewers. The business report links to the technical one.

### D-008 · Non-negotiable outputs · Decided · 29 Oct 2026
- One cleaned dataset; at least one trend; basic NLP of comments; at least one business recommendation; the technical report. Everything else is on the cut list (PLAN.md §10).

### D-009 · Deadline · Decided · 29 Oct 2026
- Code freeze Friday 30 Oct 2026, 3:00pm; proofread and edit until COB.

## Technology

### D-010 · Zero-budget, open-source stack · Decided · 29 Oct 2026
- **Decision:** No paid APIs. All NLP uses open-source models run locally or in the Claude workspace. Claude is used as the coding/orchestration assistant under the owner's existing subscription.
- **Why:** project is self-funded; open-source also keeps comment text inside environments the owner controls.

### D-011 · NLP approach: fast deterministic core + optional local LLM · Decided · 29 Oct 2026
- **Core (covers the non-negotiables):** pretrained sentiment model + embedding-based theme assignment to a human-approved theme list, run on all comments.
- **Add-on:** a 3B open-source LLM via Ollama, run only on negative/mixed comments plus the hand-labelled sample.
- **Cut-off rule:** time a 20-comment pilot. If the projected run is under ~2 hours, run it in full (overnight Thursday). Otherwise run it on the labelled sample only and report it as a method comparison.
- **Options considered:** paid LLM API (rejected — no budget); LLM on all comments (rejected — too slow on CPU); no LLM (kept as fallback).

### D-012 · Run Ollama in Docker on the owner's laptop; no Google Colab · Decided · 29 Oct 2026
- **Hardware:** Windows, Intel i7, 60 GB RAM, no GPU. Docker Desktop via WSL2.
- **Decision:** Ollama in Docker, CPU-only, model pinned by exact tag in `docker-compose.yml`; `.wslconfig` gives WSL2 a fixed memory/CPU share.
- **Why:** Colab previously hit usage limits and caused more problems than it solved. Docker gives reviewers the same model via `docker compose up`.

### D-013 · Processing split: workspace + laptop · Decided · 29 Oct 2026
- **Decision:** Profiling, joining, cleaning, analysis and charts run in the Claude cloud workspace (a sandboxed Linux environment). The Ollama LLM step runs on the laptop.
- **Data handling:** raw files are shared with the workspace. Justification: the brief states all data is fictional; identifier columns are dropped at first ingestion; only redacted text is passed to any model.
- **Agents do not run directly on the laptop** — the cloud workspace is already isolated from personal files.
- **Open risk:** the workspace network may block Hugging Face model downloads; the Wave 1 NLP environment check decides whether sentiment/embedding models also move to the laptop.
- **Wave 1 environment check result (29 Oct 2026):**
  - Workspace: Hugging Face blocked (HTTP 403); PyPI and the PyTorch index also unreachable, so new Python packages cannot be installed and `uv.lock` cannot be generated there. GitHub reachable. Pre-installed: pandas, openpyxl, pydantic, scipy, scikit-learn, matplotlib, seaborn, pytest. Missing: spaCy, pandera, duckdb, pyarrow, rapidfuzz, statsmodels, pre-commit.
  - Laptop: Ollama in Docker works. Image `ollama/ollama@sha256:20d1bbfb…12d0b`, model `qwen2.5:3b` (ID `357c53fb659c`), 12.83 tokens/s on a one-sentence test. WSL2 limited to 8 CPUs / 24 GB.
  - **Consequence:** sentiment and embedding models move to the laptop. The laptop becomes the reference environment for `uv lock`, `uv sync` and `make all`. Proposed split for Wave 1 (awaiting owner confirmation): profiling runs in the workspace with the pre-installed libraries; anything needing spaCy, pandera or models runs on the laptop.

### D-014 · Tech stack · Decided · 29 Oct 2026
- See PLAN.md §5. Key reasons: `uv` for exact reproducibility; Parquet + DuckDB for typed, inspectable stages; pandera for declarative validation; cached model outputs committed so results reproduce without re-running models.

### D-015 · Repository visibility · Decided · 29 Oct 2026
- **Decision:** private repo (`gdawg95/PS-Kestral-Group`) until reviewers approve; then public. Owner is the only human contributor.
- **Before going public:** `gitleaks` + PII scan of full git history. Raw data is gitignored from the first commit because history cannot be cleaned easily later.

## Process and controls

### D-016 · Human-in-the-loop gates · Decided · 29 Oct 2026
- **Hard gates (always block):** G1 pilot before scaling · G2 approve agent plan before it acts · G3 no schema/mapping change without approval · G4 confirm redaction before data reaches any model · G5 review before every merge · G7 owner sets and commits every threshold before results · G9 owner approves every chart before it enters a report.
- **Why:** reviewers assess how AI was controlled and verified; each gate leaves evidence (brief, report, verdict, commit).

### D-017 · Agent operating rules · Decided · 29 Oct 2026
- One branch/worktree per agent; orchestrator merges after owner review.
- Only ingestion agents touch `data/raw/`.
- Producer ≠ checker: the agent that builds something never grades it; an independent verifier runs a clean reproduction before freeze.
- The hand-labelled evaluation sample is labelled by the owner, blind to model output. Any few-shot prompt examples must not come from that sample.

### D-018 · Separate conversations per phase, shared state in files · Decided · 29 Oct 2026
- Each phase runs in its own conversation. `PLAN.md`, `DECISIONS.md` and `AI_LOG.md` live in the repo and in the Claude project so every conversation starts from the same state. Benchmark research runs in its own conversation.

## Deferred

| ID | Decision | Revisit |
|---|---|---|
| D-019 | Duplicate check result (confirms or overturns D-002 assumption) | After Wave 2 |
| D-020 | Score-scale mappings for non-1–5 sites | After profiling |
| D-021 | Evidence threshold for calling a trend real | After basic EDA |
| D-022 | NLP pass mark (e.g. sentiment agreement ≥ X%, theme F1 ≥ Y) and fallback | Before hand-labelling |
| D-023 | Final theme list (fixed + discovered mix) | After theme discovery |
| D-024 | LLM in or out | After the 20-comment pilot |
| D-025 | Value benchmarks and assumptions (low/mid/high) | Wave 5 |

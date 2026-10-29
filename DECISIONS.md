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
- **Method update after the PII pilot (29 Oct 2026, accepted by the owner after reviewing the second pilot):** the first laptop pilot missed "Raj" and a lower-case "dave", and redacted the ordinary words "Spooky" and "Keys". Three steps added:
  1. **Staff roster:** the 16 first names in the data's staff columns ("Taken by", "Logged by", "Card given by", "Staff") are redacted as `[STAFF]` in any letter case.
  2. **Sentence-start guard:** a one-word spaCy PERSON at the start of a sentence is redacted only if it is a first name seen in a name or staff column.
  3. **Corpus pass:** names spaCy tags mid-sentence in ≥ 2 comments, and that are capitalised in ≥ 60% of their uses, are redacted in any case ("Dave" yes; "Will", "Lovely" no). Token chosen by context.
  - Name lists are built in memory at each run and never written out (D-003 exception).
  - **Correction to the assumption above:** `[STAFF]` is not rare. 728 of 5,412 comments (13%) mention a staff-roster name.
  - **Residual risk:** a name used only once, in lower case, and not in any staff column can still get through. Reported in the data-quality report; the owner's read of pilot samples is the backstop.

### D-027 · Chermside Q1 2026: use FINAL v2 only · Decided · 29 Oct 2026
- **Decision:** `Chermside Q1 2026 FINAL v2.xlsx` (118 rows) is the source for Chermside Q1. `Chermside Q1 2026 FINAL.xlsx` (112 rows) is excluded from ingestion.
- **Evidence:** the profiler's exact-row check found every row of FINAL inside v2; v2 adds 6 rows and extends the date range to 31 Mar. Owner checked the v2 profile against the spreadsheet (agents/reports/w1_profilers_pilot_review.md).
- **Also found:** the two "extra" files in the owner's folder (54 vs the brief's 52) were Excel lock files (`~$...`), not data. The profiler skips `~$` files.

### D-020 · All ratings normalised to 1–5 · Decided · 29 Oct 2026
- **Decision (owner):** every rating is converted to a 1–5 scale. 3-point word scales map Bad = 1, OK/average/medium = 3, Good = 5. Owner approved all the mappings below, including the 10-point rule and the Geelong 2025 reversal (D-030).
- **Mappings** (applied by `scripts/check_ratings.py`; full table in `reports/rating_check.md`):
  | Source scale | Where | Rows | Rule |
  |---|---|---:|---|
  | 1–5 numeric | most sites | 6,144 | unchanged |
  | 1–10 | Ringwood (from Feb 2026 template) | 321 | `round(1 + (x−1)·4/9)` → 1,1,2,2,3,3,4,4,5,5 (1–2→1, 3–4→2, 5–6→3, 7–8→4, 9–10→5) |
  | 5-point words | Ballarat | 292 | Very dissatisfied 1 … Very satisfied 5 |
  | Stars ★ | Bendigo | 144 | number of filled stars |
  | 3-point words | Tamworth | 143 | Bad 1 · OK 3 · Good 5 (owner rule) |
  | Reversed 1–5 | Geelong 2025 sheet | 68 | `6 − x` (sheet note: "1 = Excellent, 5 = Poor") |
  | Pivot counts | Toowoomba Q4 2025 | 71 | already 1–5 |
- **Sanity check result:** every value maps; no out-of-range, fractional or non-numeric ratings. Rows without a rating are dropped (D-031).
- **Caveats for reporting:** Tamworth's stretched 3-point scale can only produce 1, 3 or 5, so its mean (4.08) isn't strictly comparable with true 5-point sites. Report % positive alongside the mean, and run a sensitivity check (Good = 4). Noosa (feedback cards handed out by staff) averages 4.63, which is likely selection bias.

### D-028 · Penrith "Sales - New" and "Sales - Used" are one Sales department · Decided · 29 Oct 2026
- **Decision (owner):** both map to Sales in the Wave 3 department mapping.

### D-029 · Penrith "Jun 26" sheet is a copy of "Jul 26" · Decided · 29 Oct 2026
- **Finding:** all 43 rows of the "Jun 26" sheet are identical to "Jul 26", and its dates run 1–31 July 2026. Penrith's real June 2026 feedback is missing from the pack.
- **Decision (owner, accepted default):** exclude the "Jun 26" sheet (43 rows); report June 2026 as a coverage gap for Penrith (no imputation).

### D-030 · Geelong 2025 sheet uses a reversed scale · Decided · 29 Oct 2026
- **Finding:** the 2025 sheet's title says "Rating: 1 = Excellent, 5 = Poor"; the 2026 sheet says "1 = Poor ... 5 = Excellent (new head office scale)". Comments agree: in 2025, low scores carry the positive comments.
- **Decision (owner):** convert all 68 ratings on the 2025 sheet with `6 − x` (mean 2.40 → 3.60). Without this, Geelong would show a false jump of +1.4 between 2025 and 2026. The ingestion test suite must assert that the reversal is applied to this sheet only.

### D-031 · Drop rows that have no rating · Decided · 29 Oct 2026
- **Decision (owner):** a row without a usable rating is dropped, even if it has a comment.
- **Rows affected:** 13 in total. 10 genuine responses from Tamworth with a blank HOW WAS IT (7% of that file), plus 3 rows that are not feedback at all: a note in Shepparton ("Site closed 31/3/26 ..."), a note in Ringwood Q1 ("*** NEW TEMPLATE FROM FEB") and a test row in Southport ("asdf").
- **Why:** every analysis needs a score; 10 rows is too few to matter, and keeping score-less rows complicates trend and negative-rate calculations.
- **Recorded in the data-quality report:** count of dropped rows per file and reason.

### D-032 · Profiling findings: owner accepted all proposed defaults · Decided · 29 Oct 2026
Source: `agents/reports/w1_profilers.md` (15 findings). Wave 2 ingestion applies each of these.

| # | File(s) | Rule |
|---|---|---|
| 1 | Toowoomba Q4 2025 summary | Expand the pivot counts into 71 rows dated mid-month, no comment, flag `from_summary=true`; use in score trends, exclude from NLP |
| 2 | liverpool_q3_2026.csv | Parse dates month-first (US format); assert every date falls in Jul–Sep 2026 |
| 3 | Shepparton | 6 dates in Oct–Dec 2026 (after closure) treated as year typos → 2025, flag `date_corrected=true`; drop the note row |
| 4 | IPS_feedback_log | 10 vague dates ("early Oct", "wk1 Feb") assigned to the 1st/8th/15th/22nd/29th of the month, year from neighbouring rows, flag `date_approx=true` |
| 5 | Southport | Drop 3 test rows ("asdf", "TEST", 01/01/1900); exclude the "Google reviews (copied)" sheet |
| 6 | North QLD (Rocky + TSV) | Split into two dealers using the Site column (Rockhampton/Rocky/ROK, Townsville/TSV/Tsv) |
| 7 | Ringwood | Keep both templates; 10-point ratings mapped per D-020 |
| 8 | Bendigo, Tamworth, Ballarat | Stars, Good/OK/Bad and satisfaction words mapped per D-020 |
| 9 | Essendon | Department taken from the sheet name (Sales / Service / Parts) |
| 10 | Frankston | Drop the 12 monthly "Total ..." rows and blank separators; read both layouts |
| 11 | Dandenong | Header at row 4 of each monthly sheet; ignore the empty `Sheet3` |
| 12 | All | Department variants mapped in Wave 3 to Service / Sales / Parts; New Cars and Used Cars → Sales (and D-028) |
| 13 | Several | Extra columns ("Action", "Action taken", "Followed up?", "Source") dropped by the allowlist (D-003) |
| 14 | Geelong 2025 sheet | Reversed scale, `6 − x` (D-030) |
| 15 | Penrith | Exclude the "Jun 26" copy; June 2026 reported as a gap (D-029) |

### D-033 · PII sign-off (gate G4) without extra owner test cases · Decided · 29 Oct 2026
- **Decision (owner):** skip the brief's "owner adds 3 test cases" criterion because of time; the PII module is accepted as is.
- **Compensating controls:** owner read 40 redacted comments across two pilots and found no visible personal data in the second; automated leak check found 0 staff names and no real names left in the two pilot files; 41 synthetic fixture cases plus 9 allowlist and corpus-pass unit tests, including must-not-redact cases.
- **Residual risk (accepted):** a name used once, in lower case and absent from any staff column, can get through. Wave 2 adds a dataset-wide leak count to the data-quality report.

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
  - **Consequence:** sentiment and embedding models move to the laptop. The laptop becomes the reference environment for `uv lock`, `uv sync` and `make all`.
- **Revision (29 Oct 2026, owner approved):** "Agents do not run directly on the laptop" is replaced by the working arrangement below.
  - **Options considered:** (A) split by installed libraries; (B) owner runs everything and pastes output; (C) Claude runs commands on the laptop via the desktop-app bridge, scoped to one folder; (D) carry wheels and models into the workspace by hand; (E) swap to pre-installed libraries. C was chosen, then tested: the bridge shell is a Linux sandbox on the laptop that sees only `C:\PS-Kestral-Group` (2 CPUs, 3 GB, Python 3.10 with pandas/openpyxl) and has no PyPI, Hugging Face, GitHub, Docker or Ollama access. C therefore became a B/C hybrid.
  - **Arrangement:**
    - Claude writes code in the cloud workspace clone and pushes to the agent's branch.
    - The owner runs anything needing installs, models or Docker in Windows PowerShell inside `C:\PS-Kestral-Group`, saving output to `logs\` (gitignored). Claude reads those logs through the bridge.
    - Claude does not edit tracked files in the laptop folder, so `git pull` there never conflicts. Lock files generated on the laptop (`uv.lock`) are committed and pushed by the owner.
    - Profiling and other pandas/openpyxl-only work runs in the cloud workspace.
  - **Scope limits:** bridge access is limited to `C:\PS-Kestral-Group`. Claude runs no Docker commands; the owner runs `docker compose` for this project only.

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
| D-021 | Evidence threshold for calling a trend real | After basic EDA |
| D-022 | NLP pass mark (e.g. sentiment agreement ≥ X%, theme F1 ≥ Y) and fallback | Before hand-labelling |
| D-023 | Final theme list (fixed + discovered mix) | After theme discovery |
| D-024 | LLM in or out | After the 20-comment pilot |
| D-025 | Value benchmarks and assumptions (low/mid/high) | Wave 5 |

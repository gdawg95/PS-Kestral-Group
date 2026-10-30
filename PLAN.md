# PLAN — Kestrel Motor Group: Data & AI Challenge

**Owner:** gdawg95 (sole human contributor)
**Repo:** https://github.com/gdawg95/PS-Kestral-Group (private until reviewers approve)
**Code freeze:** Friday 30 Oct 2026, 3:00pm (then proofread and edit until COB)
**Last updated:** Friday 30 Oct 2026, 13:40 · **Waves 1–4 complete. Wave 5 is the whole of
what remains, and it has no code.** Waves 1–3 are reviewed and merged to `main` (gate G5);
Wave 4 is on `w1-wrapup`, pushed but not reviewed or merged.

**The two outstanding §2 non-negotiables are both Wave 5's: a trend, and a recommendation.**
Wave 4's result is that the sentiment model **missed its pass mark** (κ 0.403 against the 0.60
committed in D-055) and the pre-committed fallback applies — **the customer's star rating is
the primary signal**, because it scored κ 0.460 on the same labels and beat the model (D-065).
The brief for the remaining work is `agents/briefs/w5_analysis.md`.

This is the single source of truth for the project. Every new conversation and every agent brief starts from this file and `DECISIONS.md`.

---

## 1. Goal

Turn 52 inconsistent dealership feedback spreadsheets (Oct 2025 – Sep 2026) into one trusted, de-identified dataset, analyse the free text with open-source NLP, and answer three business questions for the Head of Customer Experience:

1. What are the main drivers of negative feedback, and how do they vary across dealerships and departments?
2. Has anything changed over the year?
3. Where should Kestrel focus first, and roughly what is it worth?

## 2. Non-negotiable outputs

If time runs short, these are protected. Everything else can be cut.

- [x] One final cleaned, de-identified dataset — `data/clean/feedback.parquet`, 7,150 rows (Wave 3), exported for reviewers as CSV, Excel and JSON in `export/` (D-064)
- [ ] At least one trend identified (with evidence that it is real) — the evidence threshold is set and committed (D-052); the trend itself is Wave 5
- [x] Basic NLP analysis of customer comments (sentiment + themes) — **done.** Sentiment on all 5,353 commented rows and all eight approved themes assigned; `data/clean/feedback_classified.parquet`. Not yet *evaluated* against the owner's labels, which is the rest of Wave 4
- [ ] At least one recommendation for the business — Wave 5
- [x] Technical report for the reviewers — `README.md`, drafted; its Wave 4 and 5 sections are outstanding

## 3. Deliverables

| # | Deliverable | Audience | Location |
|---|---|---|---|
| 1 | Clean dataset | Analysis pipeline | `data/clean/feedback.parquet` (gitignored) |
| 1b | The same dataset, for reading | Reviewers | `export/feedback_clean.{csv,xlsx,json}` + `export/MANIFEST.md`, committed. 12 columns, minimised for public release (D-064, D-067) |
| 2 | Business report | Head of CX (non-technical) | `reports/business_report.md` |
| 3 | Technical report | Reviewers | `README.md` |
| 4 | Decisions log | Reviewers | `DECISIONS.md` |
| 5 | AI usage log | Reviewers | `AI_LOG.md` |
| 6 | Agent briefs and reports | Reviewers | `agents/briefs/`, `agents/reports/` |

The business report links to the technical report so every claim can be traced to code.

## 4. Phases

1. **Ingestion and consolidation** — profile, map, join each site into one running sheet, consolidate.
2. **Wrangling and cleaning** — PII removal, validation rules, standardisation, NLP (sentiment + themes).
3. **Analysis** — drivers, trends, coverage, value estimate.
4. **Reporting** — business report and technical report.
5. **Documentation** — decisions, AI usage, verification evidence (runs continuously across all phases).

## 5. Tech stack

| Area | Tool | Reason |
|---|---|---|
| Language | Python 3.12 | Best data/NLP ecosystem; readable for reviewers |
| Environment | `uv` + `pyproject.toml` + `uv.lock` | Exact, fast, reproducible installs |
| Pipeline runner | `Makefile` | `make all` runs every stage in order |
| Config | `config.yaml` | Paths, seeds, thresholds, model tags in one place |
| Code hygiene | `pre-commit`, `ruff`, `nbstripout` | Consistent code; notebooks never leak data |
| Tests | `pytest` | PII redaction, parsers, validation rules |
| Reading files | `pandas`, `openpyxl`, `python-calamine` | .xlsx/.csv, multi-sheet workbooks |
| Schema | `pydantic` | Canonical schema defined in code |
| Mapping | `mappings/columns.yaml` | Human-approved source → canonical column map |
| Storage | Parquet + DuckDB | Typed, fast, SQL without a server |
| Validation | `pandera` | Declarative rules with pass/fail reports |
| Fuzzy matching | `rapidfuzz` | Dealership names → codes; near-duplicate text |
| Free-text PII | Regex + spaCy or Presidio | Local name/contact redaction |
| Sentiment | Pretrained Hugging Face model (e.g. `cardiffnlp/twitter-roberta-base-sentiment-latest`) | Free, fast, deterministic |
| Themes (discovery) | `sentence-transformers` + BERTopic | Local clustering to seed the theme list |
| Themes (assignment) | Embedding similarity to approved themes | Fast, deterministic, covers all comments |
| LLM (optional add-on) | Ollama in Docker, 3B model pinned by tag (e.g. Qwen 2.5 3B / Llama 3.2 3B) | Zero cost, runs on CPU, reproducible via `docker compose` |
| Evaluation | `scikit-learn.metrics` | Precision/recall/F1, Cohen's kappa |
| Statistics | `scipy`, `statsmodels` | Trend and before/after tests |
| Charts | `matplotlib` + `seaborn` | Static PNGs for reports |
| Version control | Git + GitHub (private) | Evidence trail; one branch per agent |
| Pre-public check | `gitleaks` + PII scan | Nothing identifying in history |

**Hardware:** Windows, i7 CPU, 60 GB RAM, no GPU. Docker Desktop via WSL2. Set `.wslconfig` to give WSL2 a fixed share (e.g. 16–24 GB memory, most CPU cores). Google Colab is **not** used.

## 6. Reproducibility

- `uv sync` → exact environment.
- Place the challenge pack in `data/raw/` (not committed).
- `make all` → ingest → validate → classify (cached) → analyse → figures.
- `make test` → PII and rule tests.
- `docker compose up` → pinned Ollama model for the optional LLM step.
- Model outputs cached as JSONL keyed by hash(prompt + text + model) and **committed** (de-identified), so reviewers get identical results without re-running models. `make classify FRESH=1` re-runs.
- `reports/run_manifest.json` records input file hashes, package versions, model tags, prompt versions, seeds, and row counts per stage.
- Fixed random seeds everywhere (sampling, clustering, bootstrap).

## 7. Repository structure

```
PS-Kestral-Group/
├── data/
│   ├── raw/          # challenge pack, read-only, gitignored
│   ├── interim/      # per-stage Parquet, gitignored
│   ├── clean/        # final de-identified dataset, gitignored
├── export/           # the same dataset as CSV/Excel/JSON for reviewers, committed
│                  #   (12 columns; no lineage, month not day - D-067)
│   └── llm_cache/    # de-identified model outputs, committed
├── mappings/columns.yaml
├── prompts/          # versioned prompt files
├── src/              # one script per pipeline stage + pii.py
├── tests/
├── notebooks/        # exploration only, outputs stripped
├── agents/
│   ├── briefs/       # approved brief for every agent run
│   └── reports/      # every agent's end-of-run report
├── reports/
│   ├── figures/
│   ├── business_report.md
│   └── run_manifest.json
├── config.yaml
├── docker-compose.yml
├── Makefile
├── pyproject.toml / uv.lock
├── PLAN.md
├── DECISIONS.md
├── AI_LOG.md
└── README.md         # technical report
```

## 8. Schedule (waves)

Times are targets. Each wave ends at a human checkpoint; nothing downstream starts until it is signed off.

### Wave 1 — Thursday morning: setup and profiling · **COMPLETE**
| Agent | Task | Output |
|---|---|---|
| Scaffold | Repo structure, `pyproject.toml`, Makefile, `.gitignore`, pre-commit, nbstripout, templates | Committed skeleton |
| PII | `src/pii.py` + tests (drop identifier columns, redact free text) | Module + passing tests |
| NLP environment check | Can sentiment/embedding models download and run in the workspace? Ollama container up on laptop? | One-line verdict per model |
| Profilers ×3–4 | Inventory sheets, header rows, columns, date ranges, row counts, oddities per file | One profile JSON per file |
| Research *(separate conversation)* | Industry benchmarks: automotive service retention, customer lifetime value, cost of a lost customer | Cited summary for Wave 5 |

**Checkpoint 1 (you):** test commit proves raw data cannot be staged · compare 3 profiles against their source spreadsheets by eye · PII tests cover your tricky cases.

### Wave 2 — Thursday midday: mapping and joining · **COMPLETE**
| Agent | Task | Output |
|---|---|---|
| Mapping | Draft `columns.yaml` from the profiles | Draft mapping |
| Site joiners ×3 (VIC / NSW / QLD) | Join each site's files into one running sheet; prove date ranges don't overlap, no gaps, rows in = rows out; exact-match duplicate check | One sheet per site + reconciliation report |
| Ingest | Build the consolidated dataset from the approved mapping; drop all customer identifiers; assign new `feedback_id` | `data/interim/consolidated.parquet` |

**Checkpoint 2 (you):** approve every line of `columns.yaml` *before* joiners run · read each reconciliation table · any schema change needs your approval.

### Wave 3 — Thursday afternoon: cleaning · **COMPLETE**
What this wave was planned as, and what it turned out to be. Wave 2 settled two of the four
agents before Wave 3 started; the rescope was approved with the brief at gate G2
(`agents/briefs/w3_validate.md`).

| Agent | Planned task | What happened |
|---|---|---|
| DQ rules | pandera rules (reject / fix-and-flag / flag-and-keep) + report | **Done.** `src/validate.py`, 13 rules, `reports/data_quality.md`. 7,159 rows in → 7,150 out |
| Dealership matching | Fuzzy-match names to official codes | **Removed.** D-034 approved the file → dealer map by hand and no free-text dealership column survives ingestion, so there was nothing to match. `dealer_match_min_confidence` retired, not set |
| Dates and scales | Day-first date parsing; score-scale mapping to 1–5 | **Done at ingestion** (D-020, D-030, D-040). Wave 3 produced the edge-case list only: `reports/date_edge_cases.md` |
| Theme discovery | BERTopic on redacted comments | **Moved to Wave 4**, where the rest of the NLP lives |
| *(new)* Department fill | not in this plan — Wave 2 deliberately left `department` null (D-035) | **Done.** `mappings/departments.yaml`, 16 spellings → Service 4,903 / Sales 1,541 / Parts 706 |

**Checkpoint 3 — signed off 29 Oct 2026:** DQ waterfall read and the arithmetic closes ·
example rows reviewed, and eight of thirteen rules fired zero times so there was nothing to
show for those · dealership matches **n/a**, the agent was removed · all 16 edge-case dates
approved with their source values (D-053), not 20 arbitrary ones · themes deferred with the
agent that discovers them. Also decided here: D-047 duplicates, D-048 Workshop → Service,
D-049 one Sales department, D-050 the mapping itself.

### Wave 4 — Thursday evening/overnight: NLP
| Agent | Task | Output |
|---|---|---|
| Labelling prep | Random sample (~100–150), mixed across departments and scores; model labels hidden | Blank labelling sheet (**agent does not label**) |
| Classifier | Sentiment + embedding theme assignment for all comments; cached | Classified dataset |
| LLM (optional) | 20-comment pilot timed first; then negative/mixed comments + labelled sample, run overnight | LLM-classified subset |
| Evaluation | Compare outputs with your labels | Metrics + failure-case list |

**Checkpoint 4 (you):** commit the pass mark *before* labelling · label the sample yourself, blind · approve model tags and prompt version before full runs · confirm only redacted text is sent to any model · read ~20 failure cases.

**Where Wave 4 actually got to, as at 30 Oct 02:40.** What the plan above called four agents
became one large one plus a scoped LLM step, and the route is recorded because two methods
had to be replaced.

| Agent | Status |
|---|---|
| Labelling prep | **Not started, and now unblocked.** It needed the pass mark (set, D-055) and a theme list (approved, D-023). 150 comments stratified ~50/50/50, per D-055 |
| Classifier | **Done.** `src/classify.py`, 14 tests, `agents/reports/w4_classifier.md`. Sentiment on 5,353 rows; eight themes assigned; 7,150 rows in = 7,150 out |
| LLM (optional) | **Pilot run, scope undecided.** No longer optional in purpose: it is the mitigation for a measured defect (D-063). D-011's timing pilot projects 1.89–2.49 h for all 1,887 disagreements against a 2 h cut-off, so `reports/llm_review.md` recommends 857. **D-024 is yours** |
| Evaluation | **Blocked on your blind labels**, and it must be a separate agent (D-017) |

Two methods in the plan above did not survive contact with the data, both recorded with their
evidence: **BERTopic/HDBSCAN** could not cluster this corpus at any setting and was replaced
by KMeans (D-061), and theme **assignment by one long description per theme** misassigned a
comment at the median similarity and was replaced by max-pooled short probes (D-062).

**Outstanding before Wave 5 can start:** the `unassigned` similarity floor (D-056), the LLM
scope (D-024), approval of `agents/briefs/w4_llm.md`, and the 150 blind labels. Wave 5's value
model additionally needs `reports/benchmarks.md` reviewed and D-025 set.

### Wave 5 — Friday morning: analysis and reports
| Agent | Task |
|---|---|
| Drivers | Negative rate by theme × department × dealership, normalised by volume |
| Trend | Monthly change, shown with and without the closed site |
| Coverage | Feedback per transaction from `monthly_revenue.csv` |
| Value model | Low/mid/high estimate using cited benchmarks |
| Charts | Consistent figures for both reports |
| Business report drafter | Draft only — you rewrite the recommendations |
| Technical report drafter | Methods, DQ, AI verification, decisions, limitations |
| Independent verifier | Fresh agent: clean clone, `make all`, check every report number against code |

**Checkpoint 5 (you):** approve each chart before it enters a report · recompute 2–3 headline numbers yourself · read the verifier report · rewrite recommendations in your own voice.

**Friday 3:00pm — code freeze.** Tag `v1.0`. Proofread and edit until COB.

## 9. Human-in-the-loop controls

### The control loop (every agent)
1. **Brief** — orchestrator drafts, you approve, saved to `agents/briefs/<wave>_<agent>.md`.
2. **Plan** — agent shows intended steps and files it will touch; waits for your OK.
3. **Pilot** — bulk agents run on 2–3 files or 20 comments first; you check before scaling.
4. **Run** — you approve tool use as it comes up; agent works on its own branch.
5. **Report** — agent writes `agents/reports/<wave>_<agent>.md`: what it did, assumptions, unresolved issues, rows in/out.
6. **Review** — you check against the brief's done-when criteria, record a verdict in `AI_LOG.md` (accepted / corrected / rejected + why).
7. **Merge** — only after step 6. Nothing reaches `main` without you.

### Hard gates (always block)
| # | Gate |
|---|---|
| G1 | Pilot before scaling any bulk agent |
| G2 | Approve each agent's plan before it acts |
| G3 | No change to the canonical schema or `columns.yaml` without approval |
| G4 | Confirm data is redacted before it goes to any model or leaves the workspace |
| G5 | Review before every merge to `main` |
| G7 | You set every threshold (match confidence, negative definition, NLP pass mark) and commit it before results come in |
| G9 | Approve every chart before it enters a report |

### Stop rules
- Row counts don't reconcile → no merge.
- Agent goes outside its brief (touches other files, changes the schema) → reject and re-brief; don't patch.
- NLP misses the pass mark → apply the planned fallback; don't move the bar.
- Checkpoint slips by more than ~2 hours → cut from the list in section 10.

### Agent rules
- One branch (or worktree) per agent; the orchestrator merges.
- Only ingestion agents touch `data/raw/`. Everything downstream reads redacted data.
- The agent that produces something never grades it.

## 10. Cut list (in order)

1. Streamlit dashboard
2. Quarto rendering
3. Docker for the whole pipeline (keep only for Ollama)
4. CI workflow
5. LLM step (fall back to sentiment + embedding themes only)
6. Baseline model comparison
7. Statistical tests beyond one trend check
8. Themes beyond the top ~8

## 11. Orchestrator role

The master agent coordinates; it does not do the work.

- Keeps this file current (task status, dependencies, checkpoint state).
- Writes each agent brief using the template below.
- Owns the contracts between agents: canonical schema, folder conventions, file names.
- Adds an `AI_LOG.md` entry after each agent run, leaving "Verified by" for the owner.
- Flags slipping checkpoints and proposes cuts from section 10.

### Agent brief template
```
# Brief: <wave>_<agent>
Goal:            <one sentence>
Inputs:          <exact paths>
Outputs:         <exact paths and formats>
Allowed to touch: <paths>     Not allowed: <paths>
Decisions that apply: <DECISIONS.md IDs>
Steps:           <numbered>
Pilot:           <what runs first, on what subset>
Done when:       <checklist, incl. row-count reconciliation>
Report back:     what you did · assumptions · unresolved · rows in/out
```

### Handoff template for each new conversation
```
Project: Kestrel CX challenge. Read PLAN.md and DECISIONS.md first.
Phase/wave: <n>
Goal for this conversation: <...>
Inputs: <paths>
Decisions that apply: <IDs>
Done when: <...>
Write outputs to: <paths>
End by giving me an AI_LOG.md entry for this conversation.
```

## 12. Deferred decisions (to revisit)

| Decision | When |
|---|---|
| Duplicate check result | After Wave 2 |
| Score-scale mappings for non-1–5 sites | After profiling |
| Trend evidence threshold | After basic EDA |
| NLP pass mark | Before hand-labelling (Wave 4) |
| Final theme list | After theme discovery (Wave 3) |
| LLM in or out (pilot timing vs cut-off) | Wave 4 pilot |
| Value benchmarks and assumptions | Wave 5 |

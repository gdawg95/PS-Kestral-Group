# Kestrel Motor Group — customer feedback: technical report

**PS Recruitment Data & AI Challenge 2026** · Author: gdawg95 · Python 3.12

**Status: draft at code freeze, Friday 30 October 2026. Waves 1–5 are complete.** Section 13 lists
what is outstanding. Every number in this document is produced by code in this repository
and can be regenerated with the commands in section 2; where a number is not yet produced,
it says so rather than estimating.

This is deliverable #3 of six (D-007). The others are the clean dataset, the business
report for the Head of Customer Experience, [DECISIONS.md](DECISIONS.md),
[AI_LOG.md](AI_LOG.md), and the agent briefs and reports under [agents/](agents).

---

## 1. The task

Kestrel Motor Group collects customer feedback at 24 dealerships in Victoria, New South
Wales and Queensland. Each site keeps its own spreadsheet, in its own format, with its own
idea of what a rating means. Twelve months of that — October 2025 to September 2026 — had
to become one trustworthy dataset, and then answer three questions:

1. What drives negative feedback, and how does it vary by dealership and department?
2. Has anything changed over the year?
3. Where should Kestrel focus first, and roughly what is it worth?

The constraints that shaped every decision below: zero budget, open-source only, one
laptop with no GPU, and a Friday 3pm code freeze.

## 2. Reproducing this

```bash
uv sync --group nlp          # includes NLP models (torch, transformers, sentence-transformers)
# place the challenge pack in data/raw/ (not committed)
make all                     # ingest → validate → classify → analyse → figures
make test                    # 328 tests
```

`make all` runs the full pipeline end to end. Individual stages: `make ingest`,
`make validate`, `make export`, `make classify`, `make analyse`, `make figures`.
Windows users without `make` can use `scripts/run.ps1`.

> **Note:** use `uv sync --group nlp`, not plain `uv sync` — the NLP dependency group is
> non-default (D-013), and `make classify` will fail without it.

Seeds are fixed in [config.yaml](config.yaml) (`seed: 42`), model tags are pinned, and
model outputs are cached as de-identified JSONL, so a reviewer gets identical results
without re-running any model.

## 3. The source data

| | |
|---|---|
| Feedback files | 52 — 37 `.xlsx` and 15 `.csv`. (`data/raw/feedback/` holds 54 entries; two are Excel lock files, not data) |
| Files in scope | 51 — `Chermside Q1 2026 FINAL.xlsx` is excluded in favour of `FINAL v2` (D-027) |
| Worksheets in scope | 80 |
| Dealerships | 24, one of them closed mid-year (Shepparton, data ends 30 Mar 2026) |
| Period | Oct 2025 – Sep 2026 |
| Reference files | `dealerships.csv` (24 sites), `monthly_revenue.csv` (288 rows = 24 × 12 months) |

Every file was profiled before any mapping was written: 53 profile JSONs in
[reports/profiles/](reports/profiles), each recording sheets, header rows, columns, date
ranges, row counts and oddities. The profiles — not the file names, and not an assumption
about what a dealership spreadsheet looks like — are what
[mappings/columns.yaml](mappings/columns.yaml) was built from.

Inconsistentcies found in data: 
* three different reporting cycles (ie. monthly, quarterly, biannually)
* seven different rating scales (1 - 5 scale, 1 - 10 scale, text-based 1 - 3 scale, stars, etc.)  
* 16 spellings of three department names
* two files with Windows-1252 encoding
* one reversed rating scale (1 = most satisfied, 5 = least satisfied), documented only in a note above a header
* financial quarter supplied as a pivot table of counts rather than rows
* one sheet copied from another and presented as a different month
* two dealerships inside a single file
* dates in day-first and month-first formats in different files
* dates written as words
* test rows left in a production log

All of it is catalogued in [reports/formatting_changes.md](reports/formatting_changes.md), which became
a deliverable in its own right (D-045).

## 4. Pipeline

| Stage | Code | Output | Wave |
|---|---|---|---|
| Profile | [scripts/profile_file.py](scripts/profile_file.py) | `reports/profiles/*.json` | 1 |
| De-identify | [src/pii.py](src/pii.py) | (used inside ingest) | 1 |
| Ingest | [src/ingest.py](src/ingest.py) | `data/interim/consolidated.parquet` | 2 |
| Validate | [src/validate.py](src/validate.py) | `data/clean/feedback.parquet` | 3 |
| Export | [src/export.py](src/export.py) | `export/feedback_clean.{csv,xlsx,json}` | 3 |
| Classify | [src/classify.py](src/classify.py) | `data/clean/feedback_classified.parquet` | 4 |
| Analyse | [src/analyse.py](src/analyse.py) | `reports/analysis.md` | 5 |
| Figures | [src/figures.py](src/figures.py) | `reports/figures/*.png` | 5 |

`src/ingest.py` has no per-file branches. Every quirk in section 3 is expressed in
`mappings/columns.yaml`, which was approved line by line before any joining ran. The
schema lives in [src/schema.py](src/schema.py) as a pydantic model and is the contract
between waves.

### The final 15 columns

`feedback_id`, `dealer_code`, `feedback_date`, `department_raw`, `department`,
`rating_raw`, `rating_scale`, `rating_1to5`, `comment`, `source_file`, `source_sheet`,
`source_row`, `from_summary`, `date_corrected`, `date_approx`.

Four content columns survive from the source files — *date*, *department*, *rating*, *comment*.
Everything else is added by the pipeline: a new id, the dealership code, lineage back
to the originating spreadsheet row, and flags recording what ingestion had to fix. Both
raw and normalised forms of the rating and department are kept, so every conversion can be
audited against its source value.

## 5. Row reconciliation

Full evidence in [reports/reconciliation.md](reports/reconciliation.md).

| Stage | Rows |
|---|---:|
| Read from the 80 worksheets in scope | 7,137 |
| Dropped, each with a reason | −43 |
| Toowoomba pivot source rows (counts, not feedback) | −6 |
| Rows those counts expand into | +71 |
| **Written to the dataset** | **7,159** |

Drops: 16 summaries and notes, 14 blank rows, 10 rows with a comment but no rating
(D-031), 3 test rows (D-037). The total matches `row_budget.rows_out_expected` in the
approved mapping exactly — the budget was agreed before the ingestion ran, so the
arithmetic closing is a prediction met, not a figure reported after the fact.

Four join proofs run on every ingestion:

| Proof | Result |
|---|---|
| No two files of one dealership cover the same dates | PASS |
| No unexpected month gaps | PASS — the only gap is Penrith June 2026, explained by D-029 |
| Rows read = rows out + dropped, worksheet by worksheet | PASS for all 80 |
| Exact-match duplicate check | 9 double-entered pairs found, all at one site (section 7) |

## 6. De-identification

No customer identifier reaches the dataset. The pipeline uses an allowlist: only columns
named in the schema survive ingestion, so an unexpected column cannot leak. Free-text
comments are redacted to six tokens — `[NAME]`, `[STAFF]`, `[REGO]`, `[PHONE]`, `[EMAIL]`,
`[ADDRESS]` — using four passes: exact values from the row's own identifier cells,
regex patterns, a staff roster built in memory, and spaCy NER with a corpus-wide promotion
rule. Name lists are built in memory and never written to disk (D-041).

Across 5,362 comments, **0 probable real name misses** remain after testing each raw-name
match with the capitalisation rule the redactor itself uses. 268 comments (5%) had
over-redactions from a bug where "Email" was promoted as a person name — fixed in D-054,
with 20 new tests. All faults over-redacted; none leaked.

The published export carries **12 columns**, not 15. The three lineage columns
(`source_file`, `source_sheet`, `source_row`) identify 99.0% of rows uniquely and are
withheld; `feedback_date` becomes `feedback_month`, reducing unique-row exposure from 58.0%
to 1.4% (D-067). [src/export.py](src/export.py) blocks the export if either reaches the
public frame, with a test per column. `export/MANIFEST.md` records sha256 per file and all
64 surfaces spaCy reported as possible people.

Raw data is gitignored with a pre-commit hook that fails on any path under `data/raw/`,
`data/interim/` or `data/clean/`. The full history was scanned for PII and credentials
before publication — see [PUBLIC_RELEASE.md](PUBLIC_RELEASE.md).

## 7. Data quality

[src/validate.py](src/validate.py) applies 13 rules as a pandera schema over the 15
columns, each classified as PLAN.md requires — **reject** (the row leaves the dataset),
**fix-and-flag** (the value is repaired, the row stays), **flag-and-keep** (the row is
usable but carries a caveat). Every rule carries a count, including the rules that fire
zero times: a rule that never fires is evidence the condition was checked.

Each rule computes its own mask, which is a correction. The first version read counts out
of pandera's failure report, but pandera names a failure by the kind of check that failed
(`isin`, `str_matches`) and not by the name given to it, so every reject rule reported zero
— correctly, as it happened, but by accident. A test now asserts that each reject rule can
actually catch a row, so a zero in the report is a measured zero.

**Pilot result** (gate G1, four dealerships — the closed site, the site with imputed dates,
the site with the pivot-expanded rows, and the site with the duplicates):

| | Rows |
|---|---:|
| Read | 960 |
| Rejected | −9 |
| Written | **951** |

The nine are double entries at Springwood: pairs sharing dealership, date, department,
rating and comment text, **every pair on consecutive spreadsheet rows**. The first row of each pair was kept (D-047). 
The effect is small and was measured before the decision: Springwood's mean moves 4.0032 → 4.0100 and its negative rate
17.10% → 16.94%, and it ranks third of 24 either way.

Sixteen rows had their date changed or imputed, and all sixteen are listed with their
source value and the dated rows on either side in
[reports/date_edge_cases.md](reports/date_edge_cases.md). Six year typos at the closed
site and ten dates written as words (at Ipswich), imputed from neighbouring rows (D-040).

`department` is filled from [mappings/departments.yaml](mappings/departments.yaml), which
maps all 16 spellings to Service, Sales and Parts — 4,909 / 1,544 / 706 over the
consolidated 7,159 rows, and 4,903 / 1,541 / 706 over the 7,150 that survive validation,
with no nulls. Two calls in that mapping were tested rather than assumed:

- **"Workshop" = Service.** It looked like it might not be: 311 rows with a mean of 3.86
  against plain "Service" at 3.51. But the 10 sites using "Workshop" use all six service
  spellings in near-equal sixths, the gap shrinks to +0.231 when compared within those
  sites, and across all six spellings one-way ANOVA gives **F=1.55, p=0.170**. Workshop is
  the highest of six indistinguishable groups. Its comments also use service vocabulary at
  the same rate as Service comments (37.4% vs 34.1%) and sales vocabulary at 1.7% against
  Sales' 12.5% (D-048).
- **One Sales department, no new-versus-used cut.** 326 rows at 11 sites carry the
  distinction; new 4.457 vs used 4.311 is not significant (p=0.221). The direction reverses
  between sites, and the 11 sites that record it have a significantly higher Sales mean than
  the 13 that do not (4.354 vs 4.192, p=0.006). A published cut would report that selection
  effect (D-049).

## 8. NLP environment

`make nlp-check` ([scripts/check_nlp_env.py](scripts/check_nlp_env.py)) verifies that the
Wave 4 models load and run on this machine, and projects the runtime:

| Model | Result |
|---|---|
| `cardiffnlp/twitter-roberta-base-sentiment-latest` | loads on CPU, 131 ms/comment → 5,362 comments in ~12 min |
| `sentence-transformers/all-MiniLM-L6-v2` | loads on CPU, 384-dim vectors, 11 ms/comment → ~1 min |
| `bertopic` 0.17.4 | imports |
| `en_core_web_sm` | loads (already used in Wave 2) |

The Hugging Face models are not reachable from the cloud workspace where profiling ran
(HTTP 403), which is why the laptop is the reference environment for `uv lock`, `uv sync`
and every model (D-013).

## 9. NLP methodology

Sentiment analysis used `cardiffnlp/twitter-roberta-base-sentiment-latest` on the 5,353
commented rows. A pass mark of Cohen's κ ≥ 0.60 was committed before the owner labelled
150 comments blind (D-055). **The model scored κ = 0.403** — the customer's star rating
alone scored 0.460 — so the pre-committed fallback was applied: the rating is the primary
signal everywhere, and sentiment appears only as a labelled method comparison (D-065).

Theme discovery used KMeans (k=12) over UMAP-reduced MiniLM embeddings after
BERTopic/HDBSCAN failed to cluster this corpus (D-061). Eight themes were established from
the clusters ([mappings/themes.yaml](mappings/themes.yaml)). Theme assignment used cosine
similarity to short probe phrases per theme. NLP agreement with manual blind labels was
**44.1%**, and no confidence floor improved it (D-066), so theme negative rates are
reportable with the 44.1% stated; theme rankings are not.

An optional local LLM step (Ollama `qwen2.5:3b`, 857 comments) annotates disagreement
cases and never overwrites the sentiment label, so all results reproduce without it.

Full methodology, evaluation matrices and the pass-mark analysis are in
[ANALYSIS.md](ANALYSIS.md).

## 10. Data analysis

**Across all sites the mean rating fell from 3.842 (Oct 2025 – Mar 2026) to 3.671 (Apr – Sep 2026),
and the negative rate rose from 19.9% to 24.9%** (Welch p = 4.9e-07). The decline is
concentrated in Service (24.0% → 30.2% negative, p = 1.8e-06).

The group figure averages over three states that did different things:

| State | Rating change | Negative rate | p |
|---|---:|---:|---:|
| **NSW** (7 sites) | **−0.330** | 18.1% → **26.4%** | **7.9e-08** |
| VIC (9 sites) | −0.166 | 20.5% → 25.1% | 0.0028 |
| **QLD** (8 sites) | −0.015 | 21.0% → 23.3% | 0.80 |

Three sites survived Holm-corrected per-site testing: Parramatta (−0.75), Dandenong (−0.72)
and Liverpool (−0.58) — all declines, no site improved significantly.

**No link between feedback and revenue was detected.** The contemporaneous correlation
(r = −0.19 demeaned, p = 0.002) is not significant at any lag. NSW's feedback deteriorated
while its service volume grew. The **value model was cut**: no published benchmark maps a
1–5 rating to dollars, and the null revenue result removes the mechanism it would rest on
(D-070).

Coverage is **2.57%** of transactions (7,150 of 278,697), and response is not independent of
satisfaction — commented rows average 3.54 stars versus 4.40 for commentless — so no rate
generalises beyond responders.

Nine figures answer the three business questions. 
Full tables, statistical tests, per-site results and figure descriptions
are in [ANALYSIS.md](ANALYSIS.md).

## 11. How the work was controlled

The project ran as an orchestrator plus single-purpose agents, each with an approved brief
in [agents/briefs/](agents/briefs) and a report in [agents/reports/](agents/reports). Seven
hard gates always block: 
* pilot before scaling
* approve each plan
* no schema or mapping change without approval
* confirm redaction before anything reaches a model
* review before every merge
* human sets every threshold
* approve every chart.
* The agent that produces something never grades itself

Three things in this repository exist because of that structure:

- **`mappings/columns.yaml` was approved line by line before any joining ran.** Eight
  questions went to human first; answers are D-036 to D-045.
- **Pilots caught what tests could not.** The ingestion ran on five awkward dealerships and
  the owner checked the result against the spreadsheets before the other 19 ran (D-046).
  They confirmed from the source workbook that Geelong's 2025 scale really is reversed —
  until then that rested on a note above a header. Without the reversal Geelong would show a
  false +1.4 jump between years.
- **Thresholds were committed before results** — see [ANALYSIS.md](ANALYSIS.md).

### Where the AI got it wrong

[AI_LOG.md](AI_LOG.md) records every agent run and 46 specific errors with how each was
caught. It is an honest log, not a highlight reel, and the pattern in it matters more than
any single entry: **the errors that mattered most were caught by arithmetic that had to
close and by the owner checking source files, not by the AI reviewing its own work.**

Eleven worth naming:

| What went wrong | How it was caught |
|---|---|
| A real customer complaint — "counter service is glacial. waited 50 mins.", scored 2 — was being deleted as a spreadsheet subtotal, because a regex lost its word boundary and `count` matched the start of "counter" | The row budget came out at 7,158 against the approved 7,159. One row. The pilot could not have caught it; that dealership was not in the pilot |
| A profiler mistook a text-date data row for a second header, reporting 142 rows instead of 143 and a false format change | The owner's spot-check against the spreadsheet |
| 307 comments were written as `""` instead of null, which is truthy to every `notna()` downstream and invented five duplicate groups | Investigating why the duplicate check reported groups at sites other than Springwood |
| The leak check's raw name counter reported 100 comments, which would have overstated the residual PII risk by a factor of 50 | Re-testing each match with the capitalisation rule the redactor itself uses |
| A proposed `unassigned` similarity floor at the 4.7th percentile, which reproduced the owner's own "none of these" rate exactly and would have read as principled | The AI tested it against the owner's blind labels before publishing it: it catches **2 of their 7** rejections (D-066) |
| The 0.5-star trend threshold was applied to a change already rounded to two decimals, so a 0.496-star move cleared a 0.5-star rule. The count came out at 34 flags across 17 sites, and the first draft of the write-up then explained the gap against the committed 33/16 with the wrong cause | Reconciling the new count against `reports/trend_evidence.md` instead of accepting it, then recomputing both ways independently. The threshold now tests the unrounded value and the counts match the committed file exactly (section 10) |
| **The national trend was published before it was split by state.** The group's −0.171-star fall is real, but it is an average over NSW (−0.330, p = 7.9e-08), VIC (−0.166) and QLD (−0.015, p = 0.80 — no change). The first draft of both reports recommended acting on a group figure that does not describe two of the three states | The owner asked for the trend grouped by state. The analysis gained section 7.3 and the recommendation was restructured around it |
| Every chart was rendered at roughly four times its intended aspect ratio, with the plot squashed into a strip, because `savefig(bbox_inches="tight")` grows the canvas to fit any text it finds and the figure footers were single unwrapped lines | Reading the rendered PNGs rather than trusting that the code that wrote them was correct | Footers wrap to the figure's own width before they are drawn |
| **A published finding was out by a factor of two.** `analysis.md` reported "305 more negative service responses in H2 than H1's rate would have produced"; the arithmetic gives **156**. The code multiplied the H2-minus-H1 rate difference by all 4,903 Service rows — a denominator containing the first half — instead of by H2's 2,508. The derived 12,445 service jobs inherited it | **The independent verifier** (V-1). Neither the producer's own tests nor the owner's 14-number Checkpoint 5 recompute covered this figure. It is the argument for D-017 in one line | Both denominators corrected to H2's own; the sentence now reads 156, and 6,341 for the figure it then declines to publish |
| **A second threshold decided from a rounded display value.** The Holm-adjusted p was formatted to two significant figures and the string parsed back to decide significance, so a true 0.04951 displayed as "0.05" would have been read as not significant | The independent verifier (V-2), checking the brief's instruction that no other threshold was compared against a rounded number — the same class of defect as the trend threshold above, in a second place | The 0.05 decision is made on the float; the formatted string is display only. No verdict changed on this data |
| **`uv sync` + `make all` does not run end to end**, which is the command PLAN.md gives reviewers. `nlp` is a non-default dependency group, so `make classify` fails at `ModuleNotFoundError: sentence_transformers` — theme embeddings, unlike sentiment, are not cached | The independent verifier (V-3) running the documented commands on a clean environment | Section 2 now says `uv sync --group nlp` and explains why. `reports/theme_discovery.md` is recorded as not reproducing, which changes no published number |

The first is the one to read if only one. A single negative comment disappearing silently is
the worst possible failure for a project about negative feedback, and nothing but a row
count that refused to balance would have surfaced it. The last is the same shape one layer
up: a threshold committed in advance can still be loosened by accident, by a decision about
how to display a number.

## 12. Limitations

- **Coverage is uneven and not random.** Feedback volume per site ranges from 49 rows to
  484. Sites that collect little feedback cannot support a monthly trend claim at any
  threshold, which is why five of them are compared quarterly. Whether feedback volume
  tracks transaction volume is a Wave 5 question against `monthly_revenue.csv`.
- **Self-selected respondents.** Nothing in the data says who was asked, so no result here
  describes customers in general, only customers who responded.
- **Ratings are not natively comparable.** Seven scales were mapped to 1–5 (D-020). The
  mapping is documented and tested, but a 10-point scale collapsed to five points loses
  resolution, and one site's "Good" is not measurably another's 4.
- **One closed site.** Shepparton's 52 rows stop on 30 Mar 2026. Every trend figure must be
  shown with and without it, or the group's year-on-year movement includes a site that
  stopped reporting.
- **Imputed values are flagged, not hidden.** 16 dates were corrected or imputed and 71
  rows were expanded from a pivot of counts and carry no comment. All are flagged so any
  analysis can exclude them; the pivot rows are usable for scores and must be excluded from
  NLP.
- **Sentiment missed its pass mark and is not used for any headline.** Cohen's κ 0.403
  against the 0.60 committed in D-055, and the customer's star rating beat it at 0.460 on
  the same labels. The fallback named in advance was applied: the rating is the primary
  signal across all sites, and sentiment appears only as a labelled method comparison (section 9).
- **Theme assignment agrees with a human 44.1% of the time**, with no confidence floor
  because no floor separated the comments the owner rejected from the ones they kept (D-066).
  Theme negative rates are reportable with that figure attached; theme rankings are not, and
  no conclusion in either report depends on one.
- **Sarcasm is a measured weakness** 812 of 5,353 comments (15.2%)
  carry Australian slang markers, and all eight of the pilot's polarity-inverted cases were
  irony or idiom (D-063). The local LLM's 45.5% sarcasm rate over its 857-comment scope is
  unvalidated model output and is quoted nowhere as a measurement.
- **Coverage is 2.57% of transactions, and response is not independent of satisfaction.**
  Commented rows average 3.54 stars against 4.40 for commentless ones, so no rate in this
  project generalises beyond the customers who responded (D-006, D-058).
- **No dollar value.** D-025 is unset and `reports/benchmarks.md` is unreviewed, so the third
  business question — roughly what is it worth — is answered with a stated gap rather than an
  unverified scenario ([ANALYSIS.md](ANALYSIS.md)).
- **Twelve months cannot separate a seasonal cycle from a decline.** The year's fall is
  reported as a fall; no seasonality model was fitted and none is claimed.
- **One author.** Every judgement here is one person's, assisted by AI and recorded, but not
  independently reviewed. A second reader would likely find something.

## 13. What is outstanding

Everything in PLAN.md section 2 is now delivered. What remains is checking, not building.

| # | Item | Status at freeze |
|---|---|---|
| 1 | **Independent verifier** — fresh agent, separate worktree, full reproduction from the raw pack, every reported number checked | **Done, 30 Oct 2026** — [agents/reports/w5_verify.md](agents/reports/w5_verify.md). 73 of 75 published figures matched exactly; three parquets and all charts regenerated to identical hashes from the 52 source spreadsheets. It found six issues, **including one wrong published number no self-check had caught** (V-1). All six are now fixed or recorded. It re-derived `evaluation.md`'s headline numbers too, closing the part of that file's D-017 exception that recomputation can close |
| 2 | **Gate G9 — the owner approves each of the nine charts** | **Done, 30 Oct 2026.** All nine are embedded in `reports/business_report.md`, and three of them here. No chart entered a report before the approval |
| 3 | **Checkpoint 5, part 1 — the owner recomputes headline numbers** | **Done, 30 Oct 2026.** 14 published figures recomputed from the reviewer export by a route that imports nothing from `src/`; all 14 match. Evidence: [reports/checkpoint5_recompute.md](reports/checkpoint5_recompute.md) |
| 4 | **Checkpoint 5, part 2 — the owner rewrites the business report's recommendations in their own voice** | **Done, 30 Oct 2026.** Section 4 is the owner's wording; the report's status line is no longer DRAFT |
| 5 | **Industry benchmarks for the value model.** `reports/benchmarks.md` is **now committed** — it was cited by three deliverables while untracked (verifier finding V-5) — but it is still unreviewed and D-025 is unset, so the value model stays cut and the gap is stated in both reports | Owner's call; cut-list item 1 for Wave 5 |
| 6 | `tests/test_llm_review.py` — named in the Wave 4 LLM brief's outputs | **Does not exist.** The freeze arrived first |
| 7 | `thresholds.nlp_pass_mark.theme_bar` | Still `TBD`. A credible per-theme F1 needs its own sample, sized after discovery; D-055 records why 150 comments cannot carry one |
| 8 | **`gitleaks` scan of full history** | `gitleaks` has not been run (D-013: no network to install it). A manual credential sweep found nothing. The history rewrite (PUBLIC_RELEASE.md item 1) is complete — the 15-column export blobs are gone from every commit |

`make all` runs end to end: ingest → validate → classify → analyse → figures.

## 14. Repository

```
data/raw/          challenge pack, read-only, gitignored
data/interim/      consolidated.parquet (7,159 rows), gitignored
data/clean/        validated dataset, gitignored
export/            the same dataset as CSV/Excel/JSON + manifest, committed (D-064)
mappings/          columns.yaml (approved), departments.yaml (approved)
src/               pii.py, schema.py, ingest.py, validate.py, classify.py,
                   llm_review.py, evaluate.py, export.py, analyse.py, figures.py
scripts/           profilers, cross-checks, environment and review aids
tests/             328 tests, 2 skipped
reports/           analysis.md and business_report.md, evaluation, LLM review, theme
                   discovery and assignment, reconciliation, data quality, date edge
                   cases, formatting register, threshold evidence, figures/,
                   run_manifest.json, per-file profiles
agents/            briefs and reports, one per agent run
PLAN.md            schedule, gates, cut list
DECISIONS.md       D-001 to D-067, every decision with its reason
AI_LOG.md          every AI run and every error caught
```

### Environment

Python 3.12.16 · pandas 3.1.0 · pandera 0.35.0 · numpy 2.5.4 · pyarrow 26.0.0 ·
duckdb 2.0.0 · spacy 3.8.18 · transformers 5.21.0 · sentence-transformers 6.2.0 ·
bertopic 0.17.4 · scikit-learn 1.9.1 · scipy 1.18.1 · statsmodels 0.15.0 ·
rapidfuzz 3.14.6 · openpyxl 3.1.5 · pytest 9.2.0

Exact versions in [uv.lock](uv.lock). Hardware: Windows 11, i7 CPU, 60 GB RAM, no GPU;
WSL2 limited to 8 CPUs / 24 GB for the Ollama container.

# Kestrel Motor Group — customer feedback: technical report

**PS Recruitment Data & AI Challenge 2026** · Author: gdawg95 · Python 3.12

**Status: draft. Waves 1–3 are complete, Waves 4–5 have not started.** Section 12 lists exactly what is outstanding. Every number in this document is
produced by code in this repository and can be regenerated with the commands in section 2;
where a number is not yet produced, it says so rather than estimating.

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
uv sync                      # exact environment from uv.lock
# place the challenge pack in data/raw/ (not committed - see section 8)
make ingest                  # raw files -> data/interim/consolidated.parquet
make validate                # data-quality rules -> data/clean/feedback.parquet
make export                  # the clean dataset -> export/ as CSV, Excel and JSON
make test                    # 302 tests
make nlp-check               # can the Wave 4 models load and run here?
```

`make all` runs `ingest → validate → classify → analyse → figures` in order. The last
three stages are Waves 4 and 5 and do not exist yet; `make all` therefore fails at
`classify` today. Windows users without `make` can use `scripts/run.ps1`, which mirrors
the same targets.

Determinism: seeds are fixed in [config.yaml](config.yaml) (`seed: 42`), model tags are
pinned by name and the Ollama image by digest, and model outputs will be cached as
de-identified JSONL keyed by `hash(prompt + text + model)` and committed, so a reviewer
gets identical results without re-running any model.

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

What "inconsistent" meant in practice: seven different rating scales, 16 spellings of
three department names, two files with Windows-1252 encoding, a reversed rating scale
documented only in a note above a header, a quarter supplied as a pivot table of counts
rather than rows, one sheet copied from another and presented as a different month, two
dealerships inside a single file, dates in day-first and month-first formats in different
files, ten dates written as words, and test rows left in a production log. All of it is
catalogued in [reports/formatting_changes.md](reports/formatting_changes.md), which became
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
| Analyse, figures | not written | drivers, trend, value | 5 |

`src/ingest.py` has no per-file branches. Every quirk in section 3 is expressed in
`mappings/columns.yaml`, which the owner approved line by line before any joining ran
(Checkpoint 2, gate G3); a new quirk is a mapping change, not a code change. The canonical
schema lives in [src/schema.py](src/schema.py) as a pydantic model and is the contract
between waves.

### The 15 columns

`feedback_id`, `dealer_code`, `feedback_date`, `department_raw`, `department`,
`rating_raw`, `rating_scale`, `rating_1to5`, `comment`, `source_file`, `source_sheet`,
`source_row`, `from_summary`, `date_corrected`, `date_approx`.

Four content columns survive from the source files — date, department, rating, comment
(D-003). Everything else is added by the pipeline: a new id, the dealer code, lineage back
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

Four join proofs run on every ingestion (D-002):

| Proof | Result |
|---|---|
| No two files of one dealership cover the same dates | PASS |
| No unexpected month gaps | PASS — the only gap is Penrith June 2026, explained by D-029 |
| Rows read = rows out + dropped, worksheet by worksheet | PASS for all 80 |
| Exact-match duplicate check | 9 double-entered pairs found, all at one site (section 7) |

## 6. De-identification

No customer identifier reaches the dataset. Identifier columns are dropped at first
ingestion by an allowlist rather than a blocklist, so a column nobody anticipated cannot
leak: anything not named in the schema is discarded, and the run fails if an unexpected
column reaches the output. Free text is redacted to six tokens — `[NAME]`, `[STAFF]`,
`[REGO]`, `[PHONE]`, `[EMAIL]`, `[ADDRESS]` (D-026).

Across 5,362 comments, counting redactions applied during ingestion against the tokens
left in the final text:

| Token | Applied | Present in the final text |
|---|---:|---:|
| `[STAFF]` | 739 | 739 |
| `[REGO]` | 479 | 477 |
| `[NAME]` | 163 | 162 |
| `[PHONE]` | 156 | 156 |
| `[EMAIL]` | 58 | 58 |
| `[ADDRESS]` | 0 | 0 |

The `[ADDRESS]` zero is not a gap: the pattern was evaluated over every comment and the
source contains no street addresses. The small differences for `[REGO]` and `[NAME]` are
tokens nested inside a wider redaction.

**This table used to read `[EMAIL]` 58 applied, 0 present, and finding out why was the most
useful hour of the project.** Three faults compounded. The corpus pass that promotes a name
for case-insensitive redaction judges a candidate only on how often spaCy tagged it and how
often it is capitalised — true of the word "Email" and of a vehicle model as surely as of
"Dave" — so it promoted seven tokens that are not people. Because the brackets of `[EMAIL]`
are not word characters, `EMAIL` is a whole word *inside the token*, so promoting "Email"
rewrote all 58 redacted addresses into `[[NAME]]`: one pass silently destroying another's
output. And listing the models was not enough on its own, because spaCy tags "Altura Corsa"
as a single PERSON and the non-name check only compared the whole surface string.

All three are fixed (D-054), with 20 new tests. Nothing had leaked — every fault
over-redacted — but 268 comments, 5% of the corpus, had an ordinary word replaced by
`[NAME]`, and Wave 4 runs theme discovery over this text: "email" sits in the
booking-and-contact complaints and `Corsa`, `Terra` and `Ridge` are what customers call the
cars they are complaining about. The themes would have been built from text with its most
distinctive nouns blanked out, and would have looked perfectly healthy.

**Residual risk, measured rather than asserted.** A raw count of first names against the
redacted text matches 99 comments, which reads as a 1.8% leak. All 99 are ordinary English
words that are also somebody's name. Re-testing each with the same capitalisation rule used
to promote names leaves **0 probable real misses**. Getting there also took a fix: 55
comments open with the customer's own name followed by a dash, and where that first name
appeared in no other file's name column, a deliberate false-positive guard let it through.
Three names survived that way, one of which no one had spotted. `pii.NAME_PREFIX` now
catches the shape, with precision 55/55 on this corpus (D-051). Nothing was fixed by listing
the names, which would have put real names in git history.

Redaction combines four passes: exact values from the row's own name and registration
cells, regex patterns for contacts and plates, a staff roster built in memory from each
file's own "logged by" style columns, and spaCy NER with a corpus-wide pass that promotes a
name for case-insensitive redaction only if it appears capitalised in most of its
occurrences. Name lists are built in memory and never written to disk (D-041).

**Residual risk, measured rather than asserted.** A raw count of first names against the
redacted text matches 99 comments, which reads as a 1.8% leak. 99 of those are ordinary
English words that are also somebody's name. Re-testing each with the same capitalisation
rule used to promote names leaves **0 probable real misses**. Getting to zero took a late
fix: 55 comments open with the customer's own name followed by a dash, and where that first
name appeared in no other file's name column, a deliberate false-positive guard let it
through. Three names survived that way. `pii.NAME_PREFIX` now catches the pattern
structurally — two or three capitalised tokens at the start of a comment followed by a dash
— with precision of 55/55 on this corpus (D-051). Nothing was fixed by listing the names,
which would have put real names in git history.

Raw data cannot be committed: `.gitignore` plus a pre-commit hook that fails on any path
under `data/raw/`, `data/interim/` or `data/clean/`. The test for this is a force-add
attempt that must fail (Checkpoint 1).

One directory of feedback data **is** committed, and saying so here is the point: `export/`
holds the clean dataset as CSV, Excel and JSON, because deliverable #1 is parquet and a
reviewer cannot open parquet without Python (D-064). The exception is narrow rather than a
hole in the rule. [src/export.py](src/export.py) is the only thing that writes there, and
it refuses to write until it has proved, on that run's data, that no email address, phone
number, street address, registration plate or person-shaped name survived redaction, that
no column outside the schema allowlist is present, and that no cell would be read as a
formula by Excel. `export/MANIFEST.md` records the result, a sha256 per file, and all 64
surfaces spaCy reported as possible people, so the claim can be checked instead of taken on
trust. Two of those 64 are name-shaped and are not names - `Plin English`, a typo for
"Plain English", and `Speedy Next`, where "Speedy" is an adjective in seven comments - and
both are listed in `NOT_PEOPLE_SURFACES` with the comment that produced them rather than
handled by widening the rule until the check went green.

The risk that comes with it is stated plainly in D-064: git history cannot be cleaned later,
which is the whole basis of D-015. The repository is private, so the export is visible to
the owner and invited reviewers only; if it is ever made public, this data goes with it.

## 7. Data quality (Wave 3, in progress)

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
rating and comment text, **every pair on consecutive spreadsheet rows**. Adjacency in nine
cases out of nine is what distinguishes double entry from coincidence — of the groups that
match on everything but have no comment, only 60% are adjacent, and those are left alone.
The owner decided to keep the first row of each pair (D-047). The effect is small and was
measured before the decision: Springwood's mean moves 4.0032 → 4.0100 and its negative rate
17.10% → 16.94%, and it ranks third of 24 either way. The reason to drop them is Wave 4,
not Wave 5: one of the pairs is a 463-character complaint, and keeping both copies would
double-weight it in every theme count.

Sixteen rows had their date changed or invented, and all sixteen are listed with their
source value and the dated rows on either side in
[reports/date_edge_cases.md](reports/date_edge_cases.md) — six year typos at the closed
site, ten dates written as words at Ipswich, imputed from neighbouring rows (D-040).

`department` is filled from [mappings/departments.yaml](mappings/departments.yaml), which
maps all 16 spellings to Service, Sales and Parts — 4,909 / 1,544 / 706 over the
consolidated 7,159 rows, and 4,903 / 1,541 / 706 over the 7,150 that survive validation,
with no nulls. Two calls in
that mapping were tested rather than assumed:

- **"Workshop" is Service.** It looked like it might not be: 311 rows with a mean of 3.86
  against plain "Service" at 3.51. But the 10 sites using "Workshop" use all six service
  spellings in near-equal sixths, the gap shrinks to +0.231 when compared within those
  sites, and across all six spellings one-way ANOVA gives **F=1.55, p=0.170**. Workshop is
  the highest of six indistinguishable groups. Its comments also use service vocabulary at
  the same rate as Service comments (37.4% vs 34.1%) and sales vocabulary at 1.7% against
  Sales' 12.5% (D-048).
- **One Sales department, no new-versus-used cut.** 326 rows at 11 sites carry the
  distinction; new 4.457 vs used 4.311 is not significant (p=0.221), the direction reverses
  between sites, and the 11 sites that record it have a significantly higher Sales mean than
  the 13 that do not (4.354 vs 4.192, p=0.006). A published cut would report that selection
  effect (D-049).

## 8. Thresholds, set before the results

Gate G7: the owner sets every threshold and commits it before any result that depends on it
exists. Current state of [config.yaml](config.yaml):

| Threshold | Value | Basis |
|---|---|---|
| `negative_score_max_1to5` | 2 | D-004, provisional |
| `trend_evidence.min_month_responses` | 20 | ratings have SD 1.44, so a change between two 20-response months carries ±0.46 of noise |
| `trend_evidence.min_change_1to5` | 0.5 | sits just outside that band; the rejected "10 rows, 0.5 stars" rule would have called noise a trend |
| `trend_evidence.thin_dealer_basis` | quarterly | five sites have a median month under 20 and are compared by quarter rather than dropped |
| `llm_max_projected_hours` | 2 | the cut-off for keeping the optional LLM step |
| `nlp_pass_mark` | **TBD** | set in Wave 4 before hand-labelling (D-022) |

The trend rule calls 33 of 257 consecutive month pairs a trend, at 16 of 24 sites. Working
in [reports/trend_evidence.md](reports/trend_evidence.md); it was produced before the
threshold was chosen, so the choice is visible rather than retrofitted (D-052).

`dealer_match_min_confidence` was removed rather than set. It was the confidence floor for
a fuzzy dealership-name matcher that turned out to have nothing to match: the file → dealer
code map is approved by hand (D-034) and no free-text dealership column survives ingestion.

## 9. NLP environment

`make nlp-check` ([scripts/check_nlp_env.py](scripts/check_nlp_env.py)) verifies that the
Wave 4 models load and run on this machine, and projects the runtime:

| Model | Result |
|---|---|
| `cardiffnlp/twitter-roberta-base-sentiment-latest` | loads on CPU, 131 ms/comment → 5,362 comments in ~12 min |
| `sentence-transformers/all-MiniLM-L6-v2` | loads on CPU, 384-dim vectors, 11 ms/comment → ~1 min |
| `bertopic` 0.17.4 | imports |
| `en_core_web_sm` | loads (already used in Wave 2) |

So the deterministic NLP core is a ten-minute job, not an overnight one. Only the optional
local LLM step needs an overnight run, at 12.83 tokens/s on CPU (D-012), and it is item 5
on the cut list.

The Hugging Face models are not reachable from the cloud workspace where profiling ran
(HTTP 403), which is why the laptop is the reference environment for `uv lock`, `uv sync`
and every model (D-013).

## 10. How the work was controlled

The project ran as an orchestrator plus single-purpose agents, each with an approved brief
in [agents/briefs/](agents/briefs) and a report in [agents/reports/](agents/reports). Seven
hard gates always block: pilot before scaling, approve each plan, no schema or mapping
change without approval, confirm redaction before anything reaches a model, review before
every merge, the owner sets every threshold, and approve every chart. The agent that
produces something never grades it.

Three things in this repository exist because of that structure rather than in spite of it:

- **`mappings/columns.yaml` was approved line by line before any joining ran.** Eight
  questions went to the owner first; their answers are D-036 to D-045.
- **Pilots caught what tests could not.** The ingestion ran on five awkward dealerships and
  the owner checked the result against the spreadsheets before the other 19 ran (D-046).
  They confirmed from the source workbook that Geelong's 2025 scale really is reversed —
  until then that rested on a note above a header. Without the reversal Geelong would show a
  false +1.4 jump between years.
- **Thresholds were committed before results.** Section 8.

### Where the AI got it wrong

[AI_LOG.md](AI_LOG.md) records every agent run and 20 specific errors with how each was
caught. It is an honest log, not a highlight reel, and the pattern in it matters more than
any single entry: **the errors that mattered most were caught by arithmetic that had to
close and by the owner checking source files, not by the AI reviewing its own work.**

Four worth naming:

| What went wrong | How it was caught |
|---|---|
| A real customer complaint — "counter service is glacial. waited 50 mins.", scored 2 — was being deleted as a spreadsheet subtotal, because a regex lost its word boundary and `count` matched the start of "counter" | The row budget came out at 7,158 against the approved 7,159. One row. The pilot could not have caught it; that dealership was not in the pilot |
| A profiler mistook a text-date data row for a second header, reporting 142 rows instead of 143 and a false format change | The owner's spot-check against the spreadsheet |
| 307 comments were written as `""` instead of null, which is truthy to every `notna()` downstream and invented five duplicate groups | Investigating why the duplicate check reported groups at sites other than Springwood |
| The leak check's raw name counter reported 100 comments, which would have overstated the residual PII risk by a factor of 50 | Re-testing each match with the capitalisation rule the redactor itself uses |

The first is the one to read if only one. A single negative comment disappearing silently is
the worst possible failure for a project about negative feedback, and nothing but a row
count that refused to balance would have surfaced it.

## 11. Limitations

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
- **Sentiment and themes are not yet evaluated.** Until the hand-labelled sample exists,
  nothing in this repository establishes how accurate the NLP is.
- **One author.** Every judgement here is one person's, assisted by AI and recorded, but not
  independently reviewed. A second reader would likely find something.

## 12. What is outstanding

| # | Item | Blocked by |
|---|---|---|
| 1 | `nlp_pass_mark` and the blind hand-labelled sample | the owner (gate G7), Wave 4 |
| 2 | Sentiment, theme discovery and theme assignment | Wave 4 |
| 3 | **Industry benchmarks for the value model** — automotive service retention, customer lifetime value, cost of a lost customer, with citations. PLAN.md section 8 listed this as a Wave 1 research task in its own conversation; it was never done, and D-025 is blocked on it | nobody has started it; Wave 5 needs it |
| 4 | Drivers, trend, coverage and value analysis | Wave 5 |
| 5 | Charts, and the business report | Wave 5 |
| 6 | `reports/run_manifest.json` — input hashes, versions, model tags, row counts per stage | Wave 5 |
| 7 | Independent verifier: clean clone, `make all`, every reported number checked against code | Wave 5 |
| 8 | `gitleaks` scan of full history before the repository goes public | before publication |

`make all` cannot succeed until items 2, 4 and 5 exist, which matters because that is the
command the independent verifier runs.

## 13. Repository

```
data/raw/          challenge pack, read-only, gitignored
data/interim/      consolidated.parquet (7,159 rows), gitignored
data/clean/        validated dataset, gitignored
export/            the same dataset as CSV/Excel/JSON + manifest, committed (D-064)
mappings/          columns.yaml (approved), departments.yaml (approved)
src/               pii.py, schema.py, ingest.py, validate.py
scripts/           profilers, cross-checks, environment and review aids
tests/             302 tests, 2 skipped
reports/           reconciliation, data quality, date edge cases, formatting register,
                   trend and NLP threshold evidence, per-file profiles
agents/            briefs and reports, one per agent run
PLAN.md            schedule, gates, cut list
DECISIONS.md       D-001 to D-064, every decision with its reason
AI_LOG.md          every AI run and every error caught
```

### Environment

Python 3.12.16 · pandas 3.1.0 · pandera 0.35.0 · numpy 2.5.4 · pyarrow 26.0.0 ·
duckdb 2.0.0 · spacy 3.8.18 · transformers 5.21.0 · sentence-transformers 6.2.0 ·
bertopic 0.17.4 · scikit-learn 1.9.1 · scipy 1.18.1 · statsmodels 0.15.0 ·
rapidfuzz 3.14.6 · openpyxl 3.1.5 · pytest 9.2.0

Exact versions in [uv.lock](uv.lock). Hardware: Windows 11, i7 CPU, 60 GB RAM, no GPU;
WSL2 limited to 8 CPUs / 24 GB for the Ollama container.

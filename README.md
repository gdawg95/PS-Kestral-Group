# Kestrel Motor Group — customer feedback: technical report

**PS Recruitment Data & AI Challenge 2026** · Author: gdawg95 · Python 3.12

**Status: draft at code freeze, Friday 30 October 2026. Waves 1–5 are complete.** Section 14 lists
what is outstanding, and the largest item is that nobody independent has reproduced these
numbers yet. Every number in this document is
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

> **`uv sync` on its own is not enough, and that is a defect this project found late.**
> `nlp` (torch, transformers, sentence-transformers) is a non-default dependency group under
> D-013, so a plain `uv sync` leaves `make classify` failing at
> `ModuleNotFoundError: sentence_transformers`. Sentiment is fully served from the committed
> cache, but **theme embeddings are not cached and are recomputed on every run**, so the
> model is needed. Found by the independent verifier (V-3) running these very commands on a
> clean environment, which is what that check exists for.

```bash
uv sync --group nlp          # exact environment from uv.lock, INCLUDING the NLP models
# place the challenge pack in data/raw/ (not committed - see section 8)
make ingest                  # raw files -> data/interim/consolidated.parquet
make validate                # data-quality rules -> data/clean/feedback.parquet
make export                  # the clean dataset -> export/ as CSV, Excel and JSON
make scan-history            # PII scan of every blob in every commit (pre-public)
make test                    # 328 tests
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

That risk arrived the next morning. The owner established that the repository **will be
made public for submission**, which is the condition D-064 said to re-check on, so the
published dataset was minimised and the history audited: see
[PUBLIC_RELEASE.md](PUBLIC_RELEASE.md) and D-067.

The published export carries 12 columns, not 15. `source_file` + `source_sheet` +
`source_row` identify 99.0% of rows uniquely and are a join key back to the *un*redacted
spreadsheets, so anyone holding the challenge pack could have undone the de-identification
wholesale; they are withheld. `feedback_date` becomes `feedback_month`, which takes the
share of rows sitting alone on dealer + date + department from 58.0% to 1.4% and costs
nothing, because every analysis here is monthly anyway (D-040). `src/export.py` blocks the
export if either reaches the public frame, with a test per column.

`make scan-history` reads every blob in every commit on every branch and tag — not HEAD,
because publishing publishes all of it — and reports real email addresses, phone numbers,
street addresses, plates and person-shaped names. It is clean. The only hits were the
redaction patterns in `src/pii.py` itself, the synthetic test fixtures, two ruff `noqa`
codes shaped like number plates, and two adjudicated false positives: `Corsa Rubbish`,
where a customer ran a car model into a complaint without a full stop, and `Box Hill's`, a
suburb.

**The history blocker in PUBLIC_RELEASE.md item 1 is resolved.** The original export in
`bec914d` carried all 15 columns; `git-filter-repo` stripped those blobs from every commit
and the 12-column export was re-committed on top. See `PUBLIC_RELEASE.md` for details.

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
| `nlp_pass_mark.sentiment_min_kappa` | 0.60 | Cohen's κ on a 150-comment stratified sample, committed before the owner labelled anything. Raw agreement was rejected: the commented rows are 59.3% positive, so an always-positive model scores 59.3% (D-055) |
| `nlp_pass_mark.fallback` | `score_only` | named in advance — if κ < 0.60 the rating is primary and sentiment is a method comparison. **It was invoked**: measured κ 0.403 (D-065) |

The trend rule calls 33 of 257 consecutive month pairs a trend, at 16 of 24 sites. Working
in [reports/trend_evidence.md](reports/trend_evidence.md); it was produced before the
threshold was chosen, so the choice is visible rather than retrofitted (D-052). Wave 5's
`src/analyse.py` reproduces 33 flags at the same 16 sites over 256 pairs — one fewer, because
it requires the two months to be adjacent and the evidence script did not (section 11).

**One threshold was retired rather than set, for the second time in this project.** D-056
planned an `unassigned` similarity floor for theme assignment; tested against the owner's
blind labels it caught 2 of their 7 rejections at the 4.7th percentile, and catching all
seven required marking 40.8% of the corpus unassigned. D-066 retires it and makes the 44.1%
theme agreement a stated limitation instead (section 10).

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

## 10. Wave 4 — the NLP, and the pass mark it missed

This is the part of the project with the clearest result, and the result is a failure. It is
written up at length because **how a failed model was handled is better evidence of control
than a model that happened to work.**

### What was built

| Stage | Method | Output |
|---|---|---|
| Sentiment | `cardiffnlp/twitter-roberta-base-sentiment-latest`, three classes, cached by `sha256(text + model tag)` | 5,353 commented rows labelled; the 1,797 commentless rows carry **null**, never "neutral" (D-057) |
| Theme discovery | **KMeans k=12** over UMAP-reduced MiniLM embeddings, seed 42 | [reports/theme_discovery.md](reports/theme_discovery.md), five example comments per cluster |
| Theme list | The owner named and approved eight themes from the clusters; capped at 8 by D-059 | [mappings/themes.yaml](mappings/themes.yaml) |
| Theme assignment | Cosine similarity to **6–7 short probe phrases per theme, max-pooled** (D-062) | Every commented row assigned, with its similarity recorded |
| LLM adjudication | `qwen2.5:3b` in Docker, prompt `sentiment_v1`, temperature 0, seed 42 | 857 comments, 49.8 minutes, **0 parse failures** ([reports/llm_review.md](reports/llm_review.md)) |
| Evaluation | scikit-learn, against 150 comments the owner labelled **blind** | [reports/evaluation.md](reports/evaluation.md) |

### Two methods did not survive contact with the data

Both are recorded with the evidence that replaced them, because a method chosen in a plan and
a method that works on the data are different things.

- **BERTopic/HDBSCAN cannot cluster this corpus (D-061).** A `min_cluster_size` sweep over all
  5,353 comments returned either 84 micro-clusters with 27% outliers, or — at every setting
  from 20 upwards — a single cluster holding 87% of the data. BERTopic's own topic reduction
  did not fix it: the merged result still had one cluster of 3,191 comments. Short service
  comments averaging 101 characters have no separated density peaks; what varies most in the
  embedding space is which car the customer drives and how happy they are. **KMeans replaced
  it**, on the owner's suggestion, after the orchestrator predicted it would not help and was
  wrong. The cost is stated rather than glossed: KMeans cannot refuse a comment, so its 0%
  outlier rate is a property of the algorithm, not a quality result. HDBSCAN stays reachable
  via `--kmeans-k 0`, so the failure is reproducible.
- **One long description per theme embeds badly (D-062).** Assignment first ran against a
  50–80 word description per theme. The similarity scale came out compressed (median 0.328)
  and two of ten decile spot-checks were misassigned — **one at the median**, where no
  confidence floor could have caught it. The cause was in the wording, not the model: a
  60-word description embeds to the centroid of everything it mentions, and the descriptions
  borrowed each other's consequences. Short probes fixed it: median 0.328 → **0.424**, p90
  0.475 → **0.582**, nine of ten deciles correct with the single remaining error at p0.

### The pass mark, and what happened to it

`thresholds.nlp_pass_mark` was committed to [config.yaml](config.yaml) **before the owner
labelled anything** (gate G7, D-055): Cohen's κ ≥ 0.60 on a 150-comment stratified sample,
with a named fallback — `score_only` — if it missed. κ rather than raw agreement because the
commented rows are 59.3% positive, so a model that answers "positive" every time scores 59.3%
raw agreement and κ = 0.

The owner then labelled 150 comments blind to the model's output **and blind to the star
rating**, which D-017 does not require but which would otherwise have let the labels inherit
the signal they were measuring. 263 comments were excluded from the draw because they had
already been quoted in conversation, several with the model's label attached.

| Signal, same 150 labels | Cohen's κ |
|---|---:|
| **The sentiment model** | **0.403** — floor 0.60, **FAIL** |
| **The customer's star rating alone** | **0.460** |
| The local LLM, 45 overlapping rows | 0.727 |

**The customer's star rating beat the model.** D-055's pre-committed fallback was applied and
the bar was not moved (D-065): the rating is the primary signal in every Wave 5 figure, and
model sentiment appears only beside a rating-based number with its κ stated. PLAN.md §9's stop
rule — *"NLP misses the pass mark → apply the planned fallback; don't move the bar"* — is the
rule this followed.

**Why it failed, from the confusion matrix. Both causes had been identified before the labels
existed, which is the part worth noting:**

1. **It over-uses `neutral`.** The owner used neutral **3 times in 150**; the model assigns it
   to 22.4% of the corpus. 34 of the sample's comments were called neutral by the model while
   the owner called them negative (22) or positive (12).
2. **It reads sarcasm and praise-then-complaint as positive** — *"Wow, what a well oiled
   machine"* on a 1-star. 812 of 5,353 comments (15.2%) carry Australian slang markers, and
   all eight of the pilot's polarity-inverted cases were irony or idiom (D-063).

**The LLM's κ of 0.727 does not promote it.** It is measured on 45 rows, and those 45 are
exactly the disagreement cases the LLM was pointed at. It annotates and never overwrites
`sentiment_label`, so every Wave 5 number reproduces for a reviewer who never starts Ollama.

![Agreement between the models and the owner's blind labels](reports/figures/method_model_vs_owner.png)

*Panel A: the three signals against the pass mark committed before the labelling. Panel B:
where sentiment goes wrong — 34 of 150 called neutral, 15 real negatives called positive.
Panel C: the full theme confusion matrix behind the 44.1%. Panel D: what the LLM was and was
not used for.*

### The theme result, and the floor that was retired

Model and owner agreed on a comment's theme **44.1%** of the time. D-056 had planned to set an
`unassigned` similarity floor from the observed distribution; tested against the owner's
labels, **no floor works** (D-066):

| Floor | Catches the owner's 7 rejections | Marks unassigned |
|---:|---:|---|
| 0.259 — reproduces the owner's own 4.7% none-rate | **2 of 7** | 248 (4.6%) |
| 0.400 — catches all 7 | **7 of 7** | **2,185 (40.8%)** |

Similarity barely predicts correctness either: 38.3% theme agreement below 0.40, 44.8% at
0.40–0.50, 42.3% at 0.50–0.60. A floor at the 4.7th percentile would have reproduced the
owner's own none-rate exactly — a figure that reads as validation — while catching two of
their seven rejections, so **the threshold was retired rather than set**, the way
`dealer_match_min_confidence` was. The consequence is a reporting rule, enforced in
[src/analyse.py](src/analyse.py) rather than in prose: **theme negative rates are reportable
with the 44.1% attached; theme rankings are not.**

## 11. Wave 5 — the analysis

[src/analyse.py](src/analyse.py) → [reports/analysis.md](reports/analysis.md), and
[src/figures.py](src/figures.py) → `reports/figures/`. The working paper carries every table;
[reports/business_report.md](reports/business_report.md) quotes it and adds nothing of its
own.

### The four rules the analysis runs under

Each comes from a Wave 4 result, and each is enforced in code rather than left to the prose.

| | Rule | From |
|---|---|---|
| 1 | The star rating is primary; sentiment appears only as a labelled method comparison | D-055, D-065 |
| 2 | Theme tables are **alphabetical** — a rate is reportable, an ordering is not | D-065, D-066 |
| 3 | No theme × department × dealership cut: 576 cells for 5,353 comments is 9.3 per cell | D-060 |
| 4 | Every rate names its denominator | D-058 |

Rule 4 is the one a reader of the raw figures is most likely to get wrong. **28.1% of
commented rows are negative by rating; 22.5% of all 7,150 are.** Commentless rows average
**4.40** stars against **3.54** for commented ones, so the commented subset is not
representative — "28% of feedback is negative" overstates it by 5.6 points by silently
excluding the group that is overwhelmingly satisfied.

Rule 3's replacement cut is theme × department nationally, theme × dealership for the **19
sites whose average theme cell clears 20 comments**, and the five thin sites at department
level. Those five — NSW07, QLD05, QLD07, VIC08, VIC09 — are exactly the five D-052 put on a
quarterly basis for trends, reached from comment volume rather than month volume.

### The trend, and why it is believable

**The group's mean rating fell from 3.842 (Oct 2025 – Mar 2026) to 3.671 (Apr – Sep 2026),
and the negative rate rose 19.9% → 24.9%.**

The trend rule was committed before any trend result existed (D-052): 20 responses in a month,
0.5 stars, thin sites quarterly. Applied here it finds **33 of 256 consecutive dealer-month
pairs at 16 of 24 sites** — and those 33 split **16 down, 17 up**, so at the grain it was
calibrated for, *the rule finds no direction at all*. The group claim is therefore made at the
grain that has the data, and judged by the same rule's own arithmetic rather than by borrowing
its number:

> `min_change_1to5: 0.5` came from `sd × √(1/n₁ + 1/n₂)` at n = 20 a month, which is ±0.46.
> The same formula at n = 3,457 against 3,693 gives **±0.034**. The observed fall of 0.171 is
> five times that band. Welch p = 4.9e-07, Mann–Whitney p = 1.6e-05, and χ² on the
> negative/not-negative counts p = 4e-07.

Three alternative explanations were tested and none holds: the department mix is stable
(Service 69.3% → 67.9%), monthly volume is within 7%, and **removing the closed site moves the
fall from −0.171 to −0.169** (D-005). The decline is concentrated in **Service: 24.0% → 30.2%
negative, p = 1.8e-06**, against Sales +4.5 points and Parts unchanged.

**And the group figure is an average over three states that did different things** (section
7.3 of the analysis). Splitting it was the single highest-value thing done to this result:

| | Rating change | Negative rate | Welch p |
|---|---:|---:|---:|
| **NSW** (7 sites) | **−0.330** | 18.1% → **26.4%** | **7.9e-08** |
| VIC (9 sites) | −0.166 | 20.5% → 25.1% | 0.0028 |
| **QLD** (8 sites) | **−0.015** | 21.0% → 23.3% | **0.80 — no change** |

Reporting only the national figure would have told Queensland's eight sites to fix a problem
they do not have and understated New South Wales' by more than half. Inside NSW the move is
**+10.3 points in Service** (p = 3.1e-07) and +8.5 in Sales, while NSW Parts improved.

**Per-site testing, with the multiple-comparison problem handled rather than ignored.**
Testing 23 sites at p < 0.05 produces roughly one false positive by construction, so a Holm
step-down correction is applied across the whole family of tests. **Three sites survive it —
Parramatta (−0.75), Dandenong (−0.72) and Liverpool (−0.58) — and every one is a fall. No
site improved significantly.** That asymmetry is itself evidence; 23 noisy tests would not
produce three one-sided results. Uncorrected, five sites clear p < 0.05, and the corrected
table is what the report publishes. This is the full extent of per-site testing in the
project: cut-list item 7 makes tests beyond the one trend check cuttable, and the one kept is
the one the recommendation needs — *which* sites, not *whether* something changed.

![The year's movement split by state](reports/figures/q2_trend_by_state.png)

*The group figure is an average over three states that did different things.*

**Reconciliation against the committed evidence file.**
[reports/trend_evidence.md](reports/trend_evidence.md) predicted 33 of **257** pairs at 16 of
24 sites. The flag count and the site count match exactly; the pair count differs by one
because `scripts/trend_evidence.py` paired each month with the previous *present* month, so
Penrith's May 2026 was paired with its July across the June gap D-029 excluded.
`src/analyse.py` requires the two months to be adjacent. 257 − 1 = 256, and nothing else
differs.

### Coverage

7,150 responses against **278,697 transactions — 2.57%** (200,249 service jobs at 2.45%,
16,011 vehicles sold at 9.62%, 62,437 parts transactions at 1.13%). Reported as a limitation
(D-006), and it also bounds every rate in both reports: these are rates *among responders*,
and D-058 measured response as **not** independent of satisfaction. The analysis therefore
does **not** extrapolate the negative rate onto the 97.4% of transactions that produced no
feedback — section 9 of the analysis shows the arithmetic for that extrapolation and then
explicitly declines to publish it.

### Does satisfaction reach the revenue? A reported null result

`monthly_revenue.csv` (288 dealer-months) is the only behavioural data in the project, and
section 9 of the analysis tests it against the feedback. **No link is detectable.**

- The raw cross-site correlation between negative rate and service volume is **+0.22** — the
  wrong sign, and it is site size, not service. Two-way demeaning by dealer and by month
  flips it to **−0.19 (p = 0.0018)**, worth about 8 service jobs in a month of 709.
- **It is contemporaneous, not leading.** The association is strongest at lag 0 and is not
  significant at ±1, ±2 or ±3 months. A month's negative rate predicts nothing about the
  next month's volume, which is equally consistent with a struggling branch producing both
  fewer completed jobs and more complaints.
- **The natural experiment is flat.** NSW's negative rate rose 8.3 points while QLD's did not
  move; NSW service volume still **grew 4.9%** against QLD's 6.6%, a per-site difference of
  1.5 points at **p = 0.41**. Of the three sites whose rating fell by more than chance, one
  lost volume, one was flat and one outgrew the group.

The null is reported with its own limits rather than as a conclusion: twelve months is
shorter than a service interval, only **33%** of the variance in a site's monthly negative
rate is signal rather than sampling noise (which attenuates every correlation shown), and the
challenge pack is fictional, so the relationship may never have been in the data. What the
panel *does* establish is that it could have detected **|r| ≥ 0.166** at 80% power, so a
large short-term effect is ruled out.

![Feedback against revenue: the across-sites correlation, and the lag profile](reports/figures/q3_feedback_vs_revenue.png)

*Left: the correlation a reader reaches for first, which is site size. Right: only the same
month is significant, so feedback predicts nothing about next month's volume.*

**A free data-quality check falls out of it:** the revenue file records exactly zero activity
for VIC09 in all six months from April 2026. The feedback and revenue files were produced
separately, so that is independent corroboration of D-005's closure date rather than an
assumption carried between them.

### The value model was cut

PLAN.md's third business question asks roughly what it is worth. [reports/benchmarks.md](reports/benchmarks.md)
exists but **has not been reviewed, D-025 is unset, and the benchmarks themselves state that
no published source maps a 1–5 rating to dollars.** It is item 1 on the cut list for this wave
(PLAN.md §10), and both reports state the gap rather than publishing a scenario dressed as a
measurement.

**The revenue test above is the second and stronger reason.** Retention benchmarks work by
assuming dissatisfied customers leave and that their leaving costs money. Kestrel's own
revenue cannot detect that mechanism operating, so a dollar figure derived from those
benchmarks would rest on an assumption the client's own data declines to corroborate. The
null result strengthens the decision to cut the value model rather than weakening it.

### Figures and gate G9

`src/figures.py` writes nine PNGs, named for the business question each answers. Gate G9
makes every chart the owner's to approve before it enters a report; **that approval was
given on 30 October 2026**, and all nine are now embedded in
[reports/business_report.md](reports/business_report.md), three of them above. Until then
both reports carried a figure index instead, which is the evidence the gate was observed
rather than asserted.

| Figure | Answers |
|---|---|
| `q1_drivers_by_department.png` | which department carries the volume, which the rate |
| `q1_sites_vs_national.png` | every site as a deviation from the national rate, grouped by state, with Wilson intervals |
| `q1_themes_by_department.png` | theme mix within each department, beside the negative share of each |
| `q2_trend_by_state.png` | the year's movement split VIC / NSW / QLD, quarterly with intervals |
| `q2_sites_that_changed.png` | which sites moved, Holm-corrected across 23 tests |
| `q3_where_to_focus.png` | negative rate against its own change, bubble-sized by annual service jobs |
| `q3_feedback_vs_revenue.png` | the across-sites correlation and why it is site size, then the lag profile that shows no predictive link |
| `q3_coverage.png` | feedback per transaction, nationally and per site |
| `method_model_vs_owner.png` | both confusion matrices, the three kappas against the committed floor, and what the LLM was used for |

**Two of the nine exist to prevent a conclusion rather than support one.** `q3_feedback_vs_revenue.png` shows the naive across-sites correlation first, because it is positive and it is site size, and a reader who has not seen that cannot judge the rest; its footer says in terms that it is a guard, not a finding. `q3_where_to_focus.png` ranks sites on feedback, so its footer records that section 9 found no link between a site's negative rate and its revenue, and that nothing in the chart establishes a site in the top-right quadrant is losing money.

Three rules are enforced in the plotting code rather than in the captions. **The theme chart
is alphabetical and prints the 44.1% agreement on its own face**, so a sorted bar chart cannot
smuggle in the ranking D-065 forbids and the caveat cannot be separated from the picture in a
slide. **Every figure states its denominator in its own footer**, for the same reason. And
**no chart is drawn from a number this module computed** — every business figure is imported
from `src/analyse.py`, so a chart and a table cannot disagree; the method figure recomputes
the three kappas from the committed labels and `assert`s them against `reports/evaluation.md`
before it will render.

A twenty-four-line monthly chart was deliberately not drawn. A state-month holds about 190
responses, so a monthly site line is mostly noise, and twenty-four of them would invite a
reader to see patterns the data cannot support.

### Run provenance

[reports/run_manifest.json](reports/run_manifest.json) (PLAN.md §6) records the sha256 of
every input, the row count at each pipeline stage, the thresholds in force, the model and
prompt tags, the seed, the git commit and the package versions, so a reviewer can tell which
inputs produced which report.

## 12. How the work was controlled

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
| The 0.5-star trend threshold was applied to a change already rounded to two decimals, so a 0.496-star move cleared a 0.5-star rule. The count came out at 34 flags across 17 sites, and the first draft of the write-up then explained the gap against the committed 33/16 with the wrong cause | Reconciling the new count against `reports/trend_evidence.md` instead of accepting it, then recomputing both ways independently. The threshold now tests the unrounded value and the counts match the committed file exactly (section 11) |
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

## 13. Limitations

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
  signal everywhere, and sentiment appears only as a labelled method comparison (section 10).
- **Theme assignment agrees with a human 44.1% of the time**, with no confidence floor
  because no floor separated the comments the owner rejected from the ones they kept (D-066).
  Theme negative rates are reportable with that figure attached; theme rankings are not, and
  no conclusion in either report depends on one.
- **Sarcasm is a measured weakness, not a suspected one.** 812 of 5,353 comments (15.2%)
  carry Australian slang markers, and all eight of the pilot's polarity-inverted cases were
  irony or idiom (D-063). The local LLM's 45.5% sarcasm rate over its 857-comment scope is
  unvalidated model output and is quoted nowhere as a measurement.
- **Coverage is 2.57% of transactions, and response is not independent of satisfaction.**
  Commented rows average 3.54 stars against 4.40 for commentless ones, so no rate in this
  project generalises beyond the customers who responded (D-006, D-058).
- **No dollar value.** D-025 is unset and `reports/benchmarks.md` is unreviewed, so the third
  business question — roughly what is it worth — is answered with a stated gap rather than an
  unverified scenario (section 11).
- **Twelve months cannot separate a seasonal cycle from a decline.** The year's fall is
  reported as a fall; no seasonality model was fitted and none is claimed.
- **One author.** Every judgement here is one person's, assisted by AI and recorded, but not
  independently reviewed. A second reader would likely find something.

## 14. What is outstanding

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

## 15. Repository

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

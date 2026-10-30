# Report: w5_verify — the independent verification (D-017, PLAN.md Checkpoint 5)

**Agent:** independent verifier · **Branch:** `w5-verify` · **Date:** 30 Oct 2026, after the
15:00 code freeze · **Verified commit:** `2577910` (branch `w1-wrapup`; the analysis itself is
unchanged since `e7d26e8`).

**What this agent is.** The fresh agent PLAN.md section 8 names for Wave 5 and D-017 requires
("the agent that produces something never grades it"). It wrote none of `src/analyse.py`,
`src/figures.py`, `tests/test_analyse.py`, `reports/analysis.md` or
`reports/business_report.md`, and it has not modified them. Every number below was recomputed
from the data by scripts written for this check, which import nothing from `src/`. **Where a
number is wrong, it is recorded here and left in place**, as the brief requires.

---

## Verdict, in one line

**Yes, with one correction first:** every load-bearing number in both reports is correct and
reproduces exactly, but `reports/analysis.md` section 9 publishes **305** where the arithmetic
gives **156**, and that sentence must be fixed or cut before submission. Nothing in the
business report, the recommendation or any chart depends on it.

---

## 1. Clean reproduction

The raw challenge pack **was** present in `data/raw/` (52 source files plus the two reference
CSVs), so this is a true end-to-end reproduction from source, not a check against the
committed parquet. It was run in a **separate git worktree** at the verified commit, so the
working checkout was never touched.

### Deviation from the brief's commands, stated

`make` **is not installed on this machine**, so `make all` and `make test` could not be run as
written. I used the repository's own documented substitute — the Makefile header says
`scripts/run.ps1` mirrors these targets — and when that script failed to bind its parameters
under this session's non-interactive shell, I ran the five stages the `all` target names, in
the Makefile's order, directly: `src.ingest → src.validate → src.classify → src.analyse →
src.figures`, then `uv run pytest -q`. That is byte-for-byte what both runners invoke. I could
not establish whether the `run.ps1` binding failure is a defect in the script or an artefact of
this shell, so it is listed under "could not verify" rather than as a finding.

### Result

| Step | Result |
|---|---|
| `uv sync` | **Succeeded**, but **is not sufficient** — see the finding below |
| `src.ingest` | 7,159 rows → `data/interim/consolidated.parquet` · schema OK |
| `src.validate` | **7,159 in → 7,150 out (9 rejected)** · schema OK |
| `src.classify` | 7,150 in = 7,150 out · 5,353 with sentiment, 1,797 null (D-057) · sentiment **0 computed, 5,353 from cache** |
| `src.analyse` | read 7,150 rows, 5,353 commented |
| `src.figures` | 8 PNGs, and it printed its own G9 warning |
| `pytest -q` | **328 passed, 2 skipped** |

**Row counts reconcile exactly as published: 7,159 → 7,150 → 7,150, 5,353 commented.**

### Do the regenerated artefacts match the committed ones?

| Artefact | Result |
|---|---|
| `data/interim/consolidated.parquet` | **sha256 identical** to the working checkout's |
| `data/clean/feedback.parquet` | **sha256 identical** |
| `data/clean/feedback_classified.parquet` | **sha256 identical** |
| `reports/analysis.md` | **identical** (line endings only) |
| `reports/theme_assignment.md` | **identical** (line endings only) |
| **All 8 `reports/figures/*.png`** | **sha256 identical, every one** |
| `reports/data_quality.md`, `reports/reconciliation.md` | identical but for the run timestamp |
| `reports/run_manifest.json` | identical but for timestamp and `git_commit` (as its own note explains) |
| `reports/theme_discovery.md` | **DIFFERS** — see finding V-3 |

Three parquets and eight PNGs reproducing bit-for-bit from the 52 source spreadsheets is a
stronger reproducibility result than the project claims for itself.

---

## 2. Every headline number, recomputed

Recomputed independently from `data/clean/feedback_classified.parquet`, and the rating-based
figures **a second time** from `export/feedback_clean.csv` — a different file reached by a
different route. `src/analyse.py` was not imported.

### The headline and its denominators (D-058)

| # | Published | Where | My value | Verdict |
|---|---|---|---|---|
| 1 | 7,150 rows / 5,353 commented / 1,797 null | both | 7,150 / 5,353 / 1,797 | **matches** |
| 2 | **22.5%** negative, all 7,150 rows (1,609) | both | 1,609 / 7,150 = 22.5035% | **matches** |
| 3 | **28.1%** negative, 5,353 commented (1,504) | both | 1,504 / 5,353 = 28.0964% | **matches** |
| 4 | the two are **5.6 points** apart | both | 5.5929 pts | **matches** |
| 5 | commented mean **3.54** vs commentless **4.40** | both | 3.5360 / 4.4035 | **matches** |
| 6 | 29.8% by D-004 (rating *or* sentiment), 2,131 | analysis §1 | 2,131 / 7,150 = 29.80% | **matches** |

**Every rate in both reports names its denominator.** `analysis.md` carries an explicit
`**Denominator:**` caption on all six data sections plus a stated denominator on each trend
table; `business_report.md` states "over all 7,150 responses" at the headline and "all 7,150
responses" or "commented responses" at each table. I found no unqualified rate in either file.

### Departments and dealerships

| # | Published | My value | Verdict |
|---|---|---|---|
| 7 | Service 4,903 rows, 1,333 neg, **27.2%**, mean 3.57 | 4,903 / 1,333 / 27.187% / 3.567 | **matches** |
| 8 | Parts 706 / 113 / 16.0% / 3.95 | 706 / 113 / 16.01% / 3.953 | **matches** |
| 9 | Sales 1,541 / 163 / 10.6% / 4.26 | 1,541 / 163 / 10.58% / 4.257 | **matches** |
| 10 | Service is **68.6%** of all rows | 68.573% | **matches** |
| 11 | "two and a half times" Service vs Sales | 27.187 / 10.578 = 2.57× | **matches** |
| 12 | all 24 dealer rows, rates, Wilson CIs, means | all 24 rows reproduced, CI by my own Wilson | **matches** |
| 13 | site volumes run **49 to 484** | QLD05 49, VIC01 484 | **matches** |
| 14 | "twelve sites above the national 22.5% and twelve below" | 12 above, 12 below | **matches** |
| 15 | NSW01 27.8% (CI 23.9–31.9); QLD05 2.0% = 1 of 49 | 27.77% (23.94–31.94); 1/49 = 2.04% | **matches** |
| 16 | five thin sites QLD07 202 / VIC08 144 / NSW07 133 / VIC09 52 / QLD05 49 | identical; and these are exactly the five with median month < 20 | **matches** |
| 17 | the five pooled = **580** rows, by department | 580; Parts 60/9, Sales 98/5, Service 422/97 | **matches** |

### Themes (all over the 5,353 commented rows)

| # | Published | My value | Verdict |
|---|---|---|---|
| 18 | all 8 theme rows: n, % of commented, neg count, rate, CI, mean, sentiment-neg | every cell reproduced | **matches** |
| 19 | Staff manner 1,395 comments, **8.6%** negative | 1,395 / 8.60% | **matches** |
| 20 | theme × department, all 24 cells | all 24 reproduced | **matches** |
| 21 | "2 of the 24 cells hold fewer than 20" | exactly 2 (Booking×Parts 7, Workmanship×Parts 19) | **matches** |
| 22 | Parts has 508 commented rows | 508 | **matches** |
| 23 | **19 of 24** sites carry a theme split; the 5 that don't are NSW07, QLD05, QLD07, VIC08, VIC09 | 19; same five, by `commented/8 ≥ 20` | **matches** |
| 24 | "the median cell holds 28 comments" | median of the 19×8 grid = 28 | **matches** |

### The trend (section 7.2)

| # | Published | My value | Verdict |
|---|---|---|---|
| 25 | H1 n=3,457 · H2 n=3,693 | 3,457 / 3,693 | **matches** |
| 26 | mean **3.842 → 3.671**, change **−0.171** | 3.8423 → 3.6713, −0.1711 | **matches** |
| 27 | negative **19.9% → 24.9%**, **+5.0 pts** | 19.902 → 24.939, +5.037 | **matches** |
| 28 | Welch **t = 5.037, p = 4.9e-07** | t = 5.0368, p = 4.851e-07 | **matches** |
| 29 | Mann–Whitney **p = 1.6e-05** | 1.582e-05 | **matches** |
| 30 | χ² **p = 4e-07** | 4.003e-07 | **matches** |
| 31 | SD **1.44**, noise band **±0.034**, fall is **5.0×** it | SD 1.4409, band 0.03410, ratio 5.017 | **matches** |
| 32 | excl VIC09: **−0.169**, Welch **p = 7.3e-07** | −0.1690, p = 7.339e-07 | **matches** |
| 33 | VIC09: all 52 rows in H1 | 52 rows, all H1 (last date 2026-03-30) | **matches** |
| 34 | the 12-month series, both columns | all 12 months, both columns | **matches** |
| 35 | dept mix 69.3/21.1/9.6 → 67.9/21.9/10.2 | identical | **matches** |
| 36 | commenting propensity 72.5% → 77.1% | 72.5 / 77.1 | **matches** |
| 37 | Service −0.204 / +6.21 pts / p = 1.8e-06 | −0.204 / +6.21 / 1.789e-06 | **matches** |
| 38 | Sales −0.167 / +4.51 / p = 0.0043 · Parts −0.031 / −0.01 / p = 0.75 | −0.167/+4.51/0.004261 · −0.031/−0.01/0.7538 | **matches** |

### The state split — the load-bearing claim (section 7.3)

| # | Published | My value | Verdict |
|---|---|---|---|
| 39 | **NSW −0.330**, 3.946 → 3.616, 18.1 → 26.4 (+8.3), **p = 7.9e-08**, 7 sites, 2,243 rows | −0.3297, 3.9458 → 3.6161, 18.09 → 26.43 (+8.34), p = 7.931e-08, 7 sites, 2,243 | **matches** |
| 40 | **VIC −0.166**, 20.5 → 25.1 (+4.6), p = 0.0028, 9 sites, 2,693 rows; excl VIC09 **−0.159** | −0.1657, 20.47 → 25.05 (+4.58), p = 0.002753, 9, 2,693; excl −0.1586 | **matches** |
| 41 | **QLD −0.015**, 21.0 → 23.3 (+2.2), **p = 0.80**, 8 sites, 2,214 rows | −0.0154, 21.05 → 23.27 (+2.22), p = 0.7981, 8, 2,214 | **matches** |
| 42 | **NSW Service 21.7% → 32.1%, +10.3 pts, p = 3.1e-07**, −0.402 stars, 1,473 rows | 21.75 → 32.09, +10.35, p = 3.126e-07, −0.4020, 1,473 | **matches** |
| 43 | NSW Sales 7.8 → 16.4 (+8.5), −0.348, p = 0.00068, 555 rows | 7.84 → 16.38 (+8.54), −0.3477, 0.000684, 555 | **matches** |
| 44 | NSW Parts 19.2 → 14.7 (**−4.5**, improved), +0.163, p = 0.39, 215 rows | 19.19 → 14.66 (−4.54), +0.1631, 0.3937, 215 | **matches** |

The state split also reproduced a third time from `export/feedback_clean.csv`: NSW 1,089/1,154,
QLD 1,088/1,126, VIC 1,280/1,413, with identical rates.

### The per-site Holm correction — the place the brief flagged

I re-derived the family, re-ran all 23 Welch tests, and **implemented Holm's step-down by hand**
rather than trusting `statsmodels`.

| # | Published | My value | Verdict |
|---|---|---|---|
| 45 | **23 sites tested**, VIC09 not tested | 23 tested; VIC09 excluded (0 rows in H2) | **matches** |
| 46 | **NSW01 Parramatta −0.753**, adjusted **1.4e-06** | −0.753157, raw 6.578e-08, Holm 1.44721e-06 | **matches** |
| 47 | **VIC01 Dandenong −0.719**, adjusted **1.3e-06** | −0.719165, raw 5.649e-08, Holm 1.29928e-06 | **matches** |
| 48 | **NSW04 Liverpool −0.584**, adjusted **0.0057** | −0.58416, raw 2.704e-04, Holm 0.0056775 | **matches** |
| 49 | VIC08 Bendigo −0.616, adjusted **0.15** (near miss) | −0.616099, Holm 0.146371 | **matches** |
| 50 | **3 of 23 significant, every one a fall, none improved** | NSW01, VIC01, NSW04 — all falls | **matches** |
| 51 | all 24 rows of the site table (H1/H2 means, changes, adjusted p) | every row reproduced | **matches** |

- **My hand-rolled Holm equals `statsmodels`' to floating-point precision** on all 23 values.
- **The implementation is correct.** The adjusted values are assigned back by boolean mask in
  input order, which `multipletests` preserves; the three survivors are unchanged under a
  Bonferroni cross-check, so the result does not depend on the choice of correction.
- **The family is the right one.** The 23 tests are exactly the per-site screen — one test per
  site that clears the floor — which is the exploratory family that needs correcting. One
  scope note, below as V-4: the state and department tests are *not* in this family and are
  reported uncorrected.
- Uncorrected, 5 sites clear p < 0.05 (NSW01, NSW04, VIC01, VIC06, VIC08), matching the
  chart's own footer. VIC06 Geelong (+0.334, raw p = 0.042) is the one the correction removes,
  which is why "all three fell, none improved" survives.
- The test floor reuses D-052's *monthly* n ≥ 20 against a *half-year* count. That is
  conservative and stated in the report; it excludes only VIC09.

### The committed trend rule, D-052 (section 7.1)

| # | Published | My value | Verdict |
|---|---|---|---|
| 52 | **33 of 256** pairs, **16 of 24** sites | 33 flags, 256 adjacent pairs, 16 sites | **matches** |
| 53 | **16 down, 17 up** | 16 / 17 | **matches** |
| 54 | `trend_evidence.md`'s **33 of 257** differs only by Penrith's missing June | **confirmed, exactly** — see below | **matches** |
| 55 | largest move VIC03 2026-04, 4.09 → 2.62, **−1.46** on 23 → 32; recovers +0.94 | −1.461957; only move above 1.0 star | **matches** |
| 56 | D-052's "74% of dealer-months have 20 or more" | 207 of 281 = 73.7% | **matches** |
| 57 | all 33 flagged rows, with n and means | every row reproduced | **matches** |

**The rounding bug the producer reports fixing: confirmed fixed, and confirmed real.** I
re-ran both tests on the same data:

- threshold against the **unrounded** change → **33 flags at 16 sites** (what is published);
- threshold against the **2dp-rounded** change → **34 flags at 17 sites**;
- the single pair the rounded test wrongly admits is **VIC04, 2025-12, change −0.496503** on
  22 → 26 responses — exactly the pair the producer names.

**The 257 → 256 reconciliation: confirmed independently.** There is exactly **one**
non-adjacent dealer-month pair in the data — **NSW02 Penrith, 2026-07 paired across the
missing June 2026** (the sheet D-029 excluded). Pairing each month with the previous *present*
month gives 257; requiring adjacency gives 256. I also re-ran the old method on the
pre-validation `consolidated.parquet` (7,159 rows): **257 pairs, 33 flags, 16 sites** — so the
committed evidence file and the published analysis agree on flags and sites, and differ only
in that one pair, exactly as claimed.

### Coverage (section 8)

| # | Published | My value | Verdict |
|---|---|---|---|
| 58 | Service 200,249 jobs, 4,903 fb, **2.45%** | 2.4485% | **matches** |
| 59 | Sales 16,011 sold, 1,541 fb, **9.62%** | 9.6246% | **matches** |
| 60 | Parts 62,437 tx, 706 fb, **1.13%** | 1.1307% | **matches** |
| 61 | **All three 278,697 tx, 7,150 fb, 2.57%**; the other **97.4%** | 278,697; 2.5655%; 97.43% | **matches** |
| 62 | Service is **71.9%** of the transactions | 200,249 / 278,697 = 71.85% | **matches** |
| 63 | one response per **~41** service jobs | 40.84 | **matches** |
| 64 | the whole 24-row per-dealer coverage table | every cell reproduced | **matches** |
| 65 | VIC03 has the **highest** service coverage, 2.94%; QLD05 lowest 0.66% | confirmed both | **matches** |
| 66 | QLD08 1.99% (8/403), QLD06 2.37% (9/379), QLD07 3.37% (7/208) | identical; and these are the only three under 4% | **matches** |

### The measured-quality numbers (D-065), recomputed from the owner's labels

| # | Published | My value | Verdict |
|---|---|---|---|
| 67 | Cohen's κ, sentiment = **0.403** (floor 0.60) | 0.403183 | **matches** |
| 68 | κ of the star rating = **0.460** | 0.460000 | **matches** |
| 69 | raw agreement **64.0%** | 64.000% | **matches** |
| 70 | theme agreement **44.1%** on the 143 placed | 44.0559% on 143 | **matches** |
| 71 | owner said "none of these" on **7 of 150 (4.7%)** | 7 / 150 = 4.67% | **matches** |
| 72 | the 3×3 confusion matrix (61/22/15 · 1/2/0 · 4/12/33) | identical | **matches** |
| 73 | "21 comments the owner filed elsewhere were pulled into Staff manner" | off-diagonal Staff column = 21 | **matches** |

### The one number that does not check out

| # | Published | My value | Verdict |
|---|---|---|---|
| 74 | "the national Service move is **305** more negative service responses in H2 than H1's rate would have produced" (`analysis.md` §9) | **156** | **DIFFERS — see V-1** |
| 75 | "305 responses at a 2.45% response rate would extrapolate to roughly **12,445** service jobs" (declined calculation) | **~6,370** on the same logic | **DIFFERS — see V-1** |

---

## 3. Findings

### V-1 · `analysis.md` §9 publishes 305 where the arithmetic gives 156 — **must fix**

`src/analyse.py:958`:

```python
extra   = int(round(hs["neg_delta"] / 100 * len(svc)))   # 0.062149 * 4903 = 305
implied = int(round(hs["neg_delta"] / 100 * tx))         # 0.062149 * 200249 = 12,445
```

`extra` is published as *"**305** more negative service responses in H2 than H1's rate would
have produced"*. That sentence names a specific counterfactual, and the counterfactual has a
specific answer:

| | |
|---|---:|
| Service H1: n = 2,395, 575 negative | rate 24.0084% |
| Service H2: n = 2,508, **758** negative | rate 30.2233% |
| Expected in H2 at H1's rate | 0.240084 × 2,508 = **602.13** |
| **Excess** | 758 − 602.13 = **155.87 → 156** |

The code multiplies the H2-minus-H1 rate difference by `len(svc)` — **all 4,903 Service rows,
both halves** — instead of by H2's 2,508. It applies a second-half-versus-first-half delta to
a denominator that includes the first half, so the published figure is **1.96× the true one**.

`implied` inherits the same error and compounds it: it scales the delta by the **full year's**
200,249 service jobs rather than by H2's. On its own (declined) terms the figure is
155.87 / 0.024485 ≈ **6,370 service jobs**, not 12,445.

**Reach — and the reason this is a correction, not a crisis:**

| Document | Carries 305 / 12,445? |
|---|---|
| `reports/analysis.md` §9 | **yes, both** |
| `agents/reports/w5_analysis.md` | yes, both |
| `reports/business_report.md` | **no** |
| `README.md` | **no** |
| any chart | **no** |
| the recommendation chain (steps 1–7 of §9) | **no** — it is argued from 68.6%, 27.2%, +6.2 pts, NSW −0.330, +10.3 pts, the three Holm sites and 2.45%, every one of which I verified |

So no published recommendation, business-report claim or figure moves. But the 305 **is**
stated as a finding in §9 ("In plain counts, the national Service move is…"), so it is a wrong
number in a deliverable. The owner's own Checkpoint 5 recompute
(`reports/checkpoint5_recompute.md`) checked 14 figures and this was not among them.

**I have not fixed it.** The fix is one denominator (`len(svc)` → H2's row count, and `tx` →
H2's job count), plus re-rendering §9; or the two sentences can be cut, which costs the reports
nothing.

### V-2 · A second threshold *is* compared against a rounded value — latent, no effect here

The brief asked me to confirm no other threshold is tested against a rounded number. **One is.**
`src/analyse.py:813–818` formats the Holm-adjusted p to two significant figures for display and
then parses that string back to decide significance:

```python
t.loc[mask, "p (Holm-adjusted)"] = [f"{p:.2g}" for p in multipletests(...)[1]]
...
"**yes**" if float(adj) < 0.05 else "no"
```

This is the same class of defect as the one fixed in `month_pairs` — a threshold loosened (here,
tightened) by a decision about how to display a number. Demonstrated on boundary values:

| true adjusted p | `:.2g` | decision made | correct | |
|---|---|---|---|---|
| 0.04949 | `0.049` | significant | significant | ok |
| **0.04951** | `0.05` | **not significant** | significant | **wrong** |
| **0.049999** | `0.05` | **not significant** | significant | **wrong** |
| 0.05001 | `0.05` | not significant | not significant | ok |

Any adjusted p in **[0.0495, 0.05)** is wrongly called non-significant. Rounding can never move
a p *below* 0.05, so **false positives are impossible** and the published "3 of 23" cannot be
inflated by it.

**No effect on this dataset.** The five non-trivial adjusted p-values are 1.45e-06, 1.30e-06,
0.0057, 0.146 and 0.807 — none within three orders of magnitude of the band. The same
`Significant` column drives `q2_sites_that_changed.png` and `q3_where_to_focus.png`, so those
charts are equally unaffected. Recorded because the project's own lesson from the `month_pairs`
bug — *"a threshold committed in advance under gate G7 can still be loosened by accident, by a
decision about how to display a number"* — applies here and the guard test added for
`month_pairs` does not cover this site.

`theme_capable_sites` (`commented / 8 ≥ 20`) and the `n ≥ 20` floors all compare unrounded or
integer values. These two are the only `float()`-on-a-formatted-string sites in `analyse.py`
and `figures.py`; the three `round()` comparisons in `figures.py` are the measurement asserts,
where comparing at published precision is correct by design.

### V-3 · `uv sync` + `make all` does not run end to end from a clean environment

`uv sync` installs the default groups only. `nlp` (torch, transformers, **sentence-transformers**)
is a non-default group, deliberately, under D-013. The result is that the two commands PLAN.md
section 6 gives a reviewer fail at stage three:

```
ModuleNotFoundError: No module named 'sentence_transformers'
  File "src/classify.py", line 151, in embed
```

Sentiment is fully served from the committed cache (`0 computed, 5353 from cache`), but
**theme embeddings are not cached** and are recomputed on every run, so `classify` needs the
model. `uv sync --group nlp` fixes it and I continued from there. PLAN.md section 6's promise —
"Model outputs cached as JSONL … so reviewers get identical results without re-running models" —
holds for sentiment and not for themes.

Consequence: **`reports/theme_discovery.md` does not reproduce.** The KMeans discovery step
produced materially different clusters on this machine (cluster 0: 1,027 comments against the
committed 751; the eight clusters are differently composed), despite `seed: 42`, because the
embeddings are regenerated by a model resolved at run time. **This changes no published
number**: theme *discovery* only seeded the owner's theme list, which D-023 closed by hand, and
theme *assignment* runs against the approved probes in `mappings/themes.yaml` — which is why
`theme_assignment.md` and `feedback_classified.parquet` both reproduced byte-identically. It is
a reproducibility gap in a working paper, not in a result.

### V-4 · The state and department p-values are uncorrected, and not labelled as such

The Holm family is correctly scoped to the 23 per-site tests. But `analysis.md` §7.3 also
reports Welch p for 3 states and 3 NSW departments, and §7.2 for 3 national departments —
9 further tests, all uncorrected, presented beside a table that makes a point of correcting.
The two load-bearing ones survive any correction comfortably (NSW p = 7.9e-08, NSW Service
p = 3.1e-07; Bonferroni × 9 leaves both below 3e-06). The marginal ones would not change
character either (VIC 0.0028 → 0.025; NSW Sales 0.00068 → 0.0062). **No conclusion changes.**
Recorded because a reviewer who notices the care taken over 23 tests will ask about the other 9,
and one sentence in §7.3 would answer them.

### V-5 · `reports/benchmarks.md` is cited by three deliverables and is not committed

`reports/analysis.md` §10, `reports/business_report.md` §5 and `README.md` all cite
`reports/benchmarks.md` as the reason no dollar figure is published. The file exists on disk
but `git ls-files` does not know it — it is untracked, as are `agents/briefs/w1_research.md` and
`agents/reports/w1_research.md`. **A reviewer cloning this repository gets three dead citations**
backing the single largest declared omission. Not a number, but it is reader-facing, and
Wave 5's own account depends on that file being readable.

### V-6 · Two rendering defects in charts that have not yet passed G9

Reading the PNGs rather than the code, as the producer recommends:

1. `method_model_vs_owner.png`, panel D — the first stacked segment's label is **clipped**: it
   renders as "e customer's rating 218 (25%)" because the text overflows the bar's left edge.
2. `method_model_vs_owner.png` — the figure footer **overprints** panel C's red caption; the
   line ending "…could separate those 7 from the rest (D-066)" is partly illegible.
3. `q1_themes_by_department.png` — the "all commented rows / 28.1" reference-line label
   collides with the x-axis "30" tick.

Cosmetic, and exactly what gate G9 exists to catch. Flagged because G9 is still open, so these
are fixable before the charts enter a report.

---

## 4. The rule checks

| # | Rule | Verdict |
|---|---|---|
| R1 | **No theme table or chart ranks themes by rate** (D-065, D-066) | **PASS.** Both 8-row theme tables and the theme × dealership column headers are alphabetical. `analyse.py:329` sorts by name with the reason in a comment; `figures.py:340` and `:922` use `sorted()`. `q1_themes_by_department.png` is titled "alphabetical, NOT a ranking". No ordering claim found in either report. |
| R2 | **The 44.1% appears wherever a theme figure does** | **PASS.** 8 mentions in `analysis.md`, 4 in `business_report.md`; it is the red subtitle of `q1_themes_by_department.png` and the panel-C title of `method_model_vs_owner.png`. Both reports state the prohibition explicitly, not just the number. |
| R3 | **Model sentiment is never a headline** (D-065) | **PASS.** In `business_report.md` "sentiment" appears exactly twice, both as the labelled method comparison ("the sentiment model, which failed its accuracy test"; §6's κ 0.403 vs 0.460). In `analysis.md` it appears only as a right-hand comparison column beside a rating column, and once as a labelled D-004 row. The §9 recommendation chain uses rating, department and transaction counts only — I traced all seven steps. |
| R4 | **No three-way theme × department × dealership cut** (D-060) | **PASS.** No such table exists in either report. Theme × department is national; theme × dealership is 19 sites without a department axis; the five thin sites appear at department level only. The one text match was the prose row stating the rule. `q1_themes_by_department.png`'s footer states the absence. |
| R5 | **`config.yaml` unchanged since before Wave 5** (G7) | **PASS.** `git log --follow -- config.yaml` returns three commits: `db2c9b3` (Wave 1), `b63f6ec` (Wave 3), `b0947ab` (Wave 4, D-055's pass mark). **No Wave 5 commit touches it** — not `cb3d14e`, `89f320d`, `c4f9a2f`, `e7d26e8`, `43f94b9` or `2577910`. `theme_bar: TBD` is still TBD, and the manifest's recorded thresholds match the file. |
| R6 | **`method_model_vs_owner.png`'s asserts fire and are not trivially true** | **PASS, demonstrated.** The three asserts recompute κ and the theme rate from `reports/labels_done.csv` joined to the classified parquet, then compare at published precision. I re-derived all three independently (0.403183, 0.460000, 44.0559%) and then **perturbed each literal by one step in the last published digit (0.404 / 0.461 / 44.2) and re-rendered: all three raised `AssertionError`.** They are live. One caveat: the literals live in `src/analyse.py` as constants, so the assert checks the recomputation against a *transcription* of `reports/evaluation.md`, not against the file. I verified the transcription by hand — evaluation.md states 0.403, 0.460, 44.1% and a 61/22/15 · 1/2/0 · 4/12/33 matrix, all of which my recompute reproduces exactly. |

### The claims of omission

| # | Claim | Verdict |
|---|---|---|
| O1 | **No dollar figure anywhere** (D-025 unset) | **CONFIRMED.** Regex for `$n`, `AUD` and "dollars" over `analysis.md`, `business_report.md` and `README.md` returns nothing. The only `$` in `reports/` are two verbatim customer comments quoted in `theme_discovery.md` ("$180", "$210") — customer text, not an estimate. Both reports state the omission and name the three assumptions that would unblock it. |
| O2 | **No extrapolation of the negative rate onto non-responders** | **CONFIRMED as a matter of what is claimed.** `analysis.md` §8 calls the 41× "a statement about how little is seen, not a multiplier"; §9 shows the extrapolation and refuses it on D-058's evidence; `business_report.md` says it "deliberately does not scale them onto the 97.4% of transactions that produced no feedback". No rate anywhere is multiplied onto a transaction count as a finding. |
| O3 | **12,445 appears only as an explicitly declined calculation** | **CONFIRMED as to placement** — its only two appearances are inside the "What is deliberately not published here" paragraph and the producer's own report, both immediately followed by the refusal. **But the number itself is wrong** (V-1): on its own declined logic it is ~6,370. The declining is intact; the arithmetic being declined is not. |

---

## 5. What I could not verify

1. **`make all` and `make test` as literal commands.** `make` is not installed here. I ran the
   five stages the `all` target names, in order, plus `pytest -q`. A reviewer on macOS/Linux
   runs a path I did not exercise.
2. **`scripts/run.ps1`** failed to bind its parameters in this session's non-interactive shell
   (`Cannot convert … to SwitchParameter` on `-Fresh`, with and without `-Target`). An
   equivalent probe script with the same parameter shape bound correctly, so the fault is
   either in `run.ps1` or in how this shell passes arguments. **I could not tell which**, and I
   did not want to report a working script as broken.
3. **That the clean dataset is a correct read of the 52 source spreadsheets.** My reproduction
   shows `src/ingest.py` is deterministic and that its output hashes match, not that its
   *mapping* is right. That is Wave 2's reconciliation, signed off at Checkpoint 2, and I did
   not re-open it.
4. **The LLM step.** `reports/llm_review.md`'s 857 comments, 45.5% sarcasm rate and κ 0.727
   come from a local Ollama container I cannot run here. I confirmed what matters instead:
   panel D's counts sum correctly (218 + 439 + 200 = 857; 390/857 = 45.5%), and the LLM
   annotates only — `sentiment_label` is untouched by it, so **no number I verified depends on
   the LLM**.
5. **Whether the half-year boundary is the right one.** It is fixed, stated, and coincides with
   the closure date, and the producer names it as the choice a sceptic should push on. I
   confirmed it was not searched for (it is a module constant, `H1`/`H2`), but whether a
   different split would tell a different story is a judgement, not a check. The month series
   in §7.2 lets a reader make it themselves.
6. **`reports/benchmarks.md`'s content.** It is uncommitted (V-5) and D-025 is unset, so it
   backs nothing published.
7. **Gate G9 and the owner's rewriting of §4.** Both still open, by the reports' own admission.
   Not mine to close.

---

## 6. Would I sign off on these reports being submitted?

**Yes — once the 305 in `analysis.md` §9 is corrected or cut. Everything else I checked is
true, and the analysis reproduces bit-for-bit from the raw spreadsheets.**

Longer, because a one-line answer understates both sides. Seventy-three of the seventy-five
published figures I recomputed match exactly, including every number the recommendation rests
on and every number in `business_report.md`. Three parquets and all eight charts regenerate to
identical hashes from the 52 source files. The Holm correction is correctly implemented over
the correct family, and I verified it against my own step-down rather than against the library
the code uses. The rules the project set itself — the rating as primary, no theme ranking, no
three-way cut, every rate with its denominator, the pass mark not moved, `config.yaml` frozen —
are kept in the code, in the prose and in the figures, and the figure asserts that enforce the
measured numbers genuinely fire. The two wrong numbers sit in the working paper, not in the
business report, and neither touches a recommendation.

That said, the 305 is a published finding in a deliverable and it is out by a factor of two, so
it should not go out as it stands. V-2 should be fixed or noted because it is the project's own
documented failure mode surviving in a second place. V-5 is a five-minute `git add` that
prevents three dead citations under the one question the reports decline to answer.

**On independence.** This check was run by an agent that wrote none of what it graded, from a
separate worktree, with its own recomputation scripts that import nothing from `src/`, against
the raw pack rather than the committed outputs. The first substantive error anyone found in
Wave 5's published numbers was found here, which is the argument for D-017 rather than a
criticism of the work — the producer's self-check and the owner's 14-number recompute both
passed over it, exactly as a producer-grades-itself arrangement predicts. `reports/evaluation.md`
remains self-graded; I re-derived its headline numbers (κ 0.403, κ 0.460, 44.1%, the confusion
matrix) from the committed labels and they are correct, which closes the part of its D-017
exception that can be closed by recomputation.

---

**Files written by this agent:** `agents/reports/w5_verify.md` only. Nothing else in the
repository was modified, and no finding above was patched.

**Rows in / out:** read-only. 7,150 rows read; 0 written.

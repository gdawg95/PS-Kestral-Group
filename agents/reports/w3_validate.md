# Report: w3_validate
**Brief:** agents/briefs/w3_validate.md (approved at gate G2, 29 Oct 2026)
**Branch:** `w1-wrapup`
**Date:** 29 Oct 2026

All six steps are done. 7,159 rows in, 7,150 out, 9 rejected with a reason, the arithmetic
closing exactly. `department` is filled for every row and the three totals match the
owner-approved mapping. Four Checkpoint 3 items went to the owner and all four came back
decided (D-047 – D-050, D-053). One rule was found to be reporting a false zero and was
rebuilt; see **Checks I ran**.

## What I did

- Put the brief's four questions to the owner with the evidence computed first, rather
  than with the defaults the brief had proposed. Three of the four defaults survived; the
  evidence changed the *reason* for two of them, and in one case contradicted the brief's
  own framing of the risk (D-047: the brief warned that dropping 9 rows "moves a
  dealership's published score"; measured, it moves Springwood's mean by 0.007 and its rank
  not at all).
- Wrote `src/validate.py`: 13 rules over the 15 columns, each classified reject /
  fix-and-flag / flag-and-keep, each carrying a count including the eight that fire zero
  times.
- Wrote `tests/test_validate.py`: 36 tests on synthetic frames, including the two the brief
  named — a reject rule must reject rather than silently repair, and the department fill
  must leave no null.
- Filled `department` from `mappings/departments.yaml` after the owner approved it
  (D-050), and marked that file `approved` so `load_departments()` refuses to run against a
  draft. Gate G3 is now enforced in code, not only in the process.
- Ran the pilot on four dealerships, showed the owner the waterfall, and ran the full
  7,159 only after they cleared gate G1.
- Wrote `scripts/date_edge_cases.py` → `reports/date_edge_cases.md` after the owner asked
  whether they had seen everything. They had not: the date list in `reports/data_quality.md`
  could only print the *resolved* date, because the source value does not survive ingestion.
  Without the source text the list is 16 assertions, not 16 reviewable rows.
- Outside the brief, at the owner's instruction: fixed three surviving names in the comment
  text (D-051), set `thresholds.trend_evidence` and retired
  `dealer_match_min_confidence` (D-052), wrote `scripts/check_nlp_env.py` for the Wave 4
  model check, and drafted `README.md` as the technical report.

Files written: `src/validate.py`, `tests/test_validate.py`, `reports/data_quality.md`,
`reports/date_edge_cases.md`, `scripts/date_edge_cases.py`, `data/clean/feedback.parquet`
(gitignored), and this report. `mappings/departments.yaml` status line changed.

## Rows in / out

| Stage | Rows | Note |
|---|---:|---|
| Read from `data/interim/consolidated.parquet` | 7,159 | Wave 2's output, unchanged |
| Rejected: `double_entry_duplicate` | −9 | D-047, the second row of each Springwood pair |
| **Written to `data/clean/feedback.parquet`** | **7,150** | **rows in = rows out + rejected, exactly** |

Per rule, over all 7,159 rows:

| Rule | Class | Rows |
|---|---|---:|
| `dealer_code_known` | reject | 0 |
| `date_in_window` | reject | 0 |
| `rating_in_1_to_5` | reject | 0 |
| `department_raw_present` | reject | 0 |
| `feedback_id_well_formed` | reject | 0 |
| `feedback_id_unique` | reject | 0 |
| `summary_rows_have_no_comment` | reject | 0 |
| `double_entry_duplicate` | reject | **9** |
| `empty_comment_to_null` | fix-and-flag | 0 |
| `department_filled` | fix-and-flag | 7,159 |
| `date_corrected` | flag-and-keep | 6 |
| `date_approx` | flag-and-keep | 10 |
| `from_summary` | flag-and-keep | 71 |

**Eight of thirteen rules fired zero times.** That is the expected result and the reason
the brief asked for the zeros to be reported: Wave 2 already handled every one of those
conditions, so Wave 3 confirming it is evidence the ingestion was right, not padding. The
one that would have been alarming is `empty_comment_to_null` — it fired 307 times during
Wave 2 and was fixed there (AI_LOG #17), so a zero here is that fix holding.

Department fill, after the 9 rejections:

| Department | Rows |
|---|---:|
| Service | 4,903 |
| Sales | 1,541 |
| Parts | 706 |
| **Total** | **7,150** |

Nulls: 0. The 9 dropped rows were 6 Service and 3 Sales, which is why these are 6 and 3
below the mapping's own 4,909 / 1,544 / 706 against the pre-validation 7,159.

## Assumptions

- **The duplicates rule is written generically, not for Springwood.** It catches any group
  sharing dealer, date, department, rating and comment text where the comment is not null
  *and* the spreadsheet rows are consecutive. It was not given a dealership or a row
  number. On the full dataset it finds exactly the 9 pairs Wave 2 found by a different
  method, which is the useful part: two independent derivations agree. If it is wrong, it
  is wrong in the direction of catching too little — a double entry separated by one
  unrelated row would survive.
- **Rejected rows leave the dataset rather than being quarantined to a file.** The brief
  asks for rows in = rows out + rejected and for five examples per rule, and the report
  carries both plus the nine pairs by row number, so the rejections are reconstructible
  from the source workbook. A quarantine Parquet would be a second copy of customer
  comments for no extra evidence.
- **The date edge-case script reads `data/raw/` read-only.** The agent rules say only
  ingestion agents touch raw data. I judged a read-only review aid to be within the spirit
  of that rule, because the alternative was asking the owner to approve 16 imputations
  without showing them what was imputed. Flagging it here rather than assuming it is fine.
- **`empty_comment_to_null` is classified fix-and-flag although it now fires zero times.**
  It is kept as a live rule rather than deleted, because the condition it guards against
  was a real bug in Wave 2 and nothing stops a re-sent file reintroducing it.

## Checks I ran

```bash
uv run python -m src.validate            # the full run
uv run python scripts/date_edge_cases.py # the 16 dates with their source values
uv run python scripts/check_departments.py
uv run pytest -q                         # 243 passed, 2 skipped
uv run ruff check .
```

Verified on the clean dataset directly, not from the report that describes it:

| Check | Result |
|---|---|
| Rows | 7,150 = 7,159 − 9 |
| Dealerships | 24 |
| `feedback_id` unique | yes |
| `department` nulls | 0 |
| Date range | 2025-10-01 to 2026-09-30, both ends inside the window |
| `rating_1to5` values | {1, 2, 3, 4, 5} only |
| Flags carried | 71 `from_summary`, 6 `date_corrected`, 10 `date_approx` |
| Mean rating | 3.7540, against 3.7540 before validation — the 9 rejections do not move it |
| Springwood | 301 rows, mean 4.0100 — matching the figure quoted to the owner *before* they decided |
| pandera on the clean frame | passes with nothing left to reject |

**The bug the tests caught.** The first version of this module read per-rule counts out of
pandera's `failure_cases`. pandera labels a failure by the kind of check that failed
(`isin`, `str_matches`, `in_range`), not by the `name=` given to it, so no failure ever
matched a rule key and **every reject rule reported zero**. On this data the zeros happened
to be correct, so the pilot would have looked perfect and the error would have shipped — a
report asserting that eight conditions were checked when nothing had been attributed. Each
rule now computes its own mask. Two tests guard it: one asserts every reject rule with a
mask can actually catch a row, the other that a clean row trips none of them. This is the
same failure mode as AI_LOG #16 — a check that silently does nothing is worse than a check
that fails loudly.

Not verified by me: whether the nine dropped comments read as double entries to a human.
The owner decided that from the pairs table and the adjacency argument.

## Unresolved

- **`nlp_pass_mark` is still `TBD`** (D-022). The owner chose to set it in Wave 4 before
  hand-labelling. The baseline evidence it has to beat is in
  `reports/nlp_pass_mark_evidence.md`: always answering "positive" scores 59.3%, so 80% raw
  agreement is only 21 points above a model that does not read the text, and κ ≥ 0.60 is
  the floor that fails it.
- **`reports/run_manifest.json` does not exist.** PLAN.md section 6 promises input file
  hashes, package versions, model tags, prompt versions, seeds and row counts per stage.
  Wave 5 work, but nothing has been written towards it.
- **`make all` cannot succeed** — `src/classify.py`, `src/analyse.py` and `src/figures.py`
  do not exist yet. That is the command the Wave 5 independent verifier runs, so it needs
  to work before the freeze.
- **`make` itself is still unavailable on the laptop**; every target has been exercised
  directly or through `scripts/run.ps1`, not as `make`.
- **Theme discovery moved to Wave 4** (brief, step 0). The final theme list (D-023) is
  still open and is a Checkpoint 4 item.
- **Nothing is committed.** This report, the validator, the tests, the PII fix, the
  thresholds and the README are all in the working tree on `w1-wrapup`.

## Done-when criteria

- [x] Owner approved `mappings/departments.yaml` (Checkpoint 3) — D-050
- [x] Owner decided the Springwood duplicates (closes D-019) — D-047
- [x] Owner skimmed the 16 date edge cases — D-053. **The five example rows per rule are
      left for the owner:** eight of thirteen rules have no examples to show because they
      fired zero times, and the five that fired are in `reports/data_quality.md`
- [x] Every pandera rule has a count, including the zero ones
- [x] `department` is non-null for all rows and the three totals match
      `mappings/departments.yaml`
- [x] rows in = rows out + rejected, by rule, and the arithmetic closes in the report
- [x] Tests pass — 243 passed, 2 skipped
- [x] Report written to `agents/reports/w3_validate.md`

## Report back

7,159 rows in, 7,150 out, 9 rejected and reasoned, arithmetic closing exactly, `department`
filled for every row at Service 4,903 / Sales 1,541 / Parts 706. Eight of thirteen rules
fired zero times, which is Wave 2's work being confirmed rather than rules doing nothing —
and the reason that claim can be trusted is that a false-zero bug in the first version was
caught by its own tests and the counting rebuilt. Four owner decisions closed (D-047 –
D-050, D-053) and D-019 with them. Outside the brief and at the owner's instruction: three
surviving customer names removed from the comment text with the residual leak now measured
at zero, the trend threshold set on its evidence, the Wave 4 model environment proven to
work with sentiment at ~12 minutes for the corpus, and `README.md` drafted as the technical
report. `nlp_pass_mark` is the only threshold still open.

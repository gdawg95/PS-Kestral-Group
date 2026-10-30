# Report: w4_classifier
**Brief:** agents/briefs/w4_classifier.md (approved by the owner, 30 Oct 2026, after
answering Q1–Q3; recorded as D-056 – D-060)
**Branch:** `w1-wrapup`
**Date:** 30 Oct 2026 (overnight, 00:20 – 02:20)

## What I did

Sentiment over every commented row, theme discovery, and assignment of all 5,353 comments to
the eight themes the owner approved. The discovery stage took four attempts before it
produced anything nameable, and the assignment stage took two; both failures are documented
below and in D-061 and D-062, because the route matters as much as the destination here.

1. **`src/classify.py`** — three interruptible stages (`sentiment`, `discover`, `assign`),
   cached JSONL keyed by `hash(text + model tag)`, with `--pilot`, `--fresh`, `--kmeans-k`,
   `--nr-topics` and `--min-topic-size`.
2. **Pilot (G1)** on 198 stratified comments. It caught the defect it was for: cluster labels
   came back as stopwords and the redaction token `rego`, the top term of the largest
   cluster. Fixed by excluding stopwords, the six D-026 token words and the vehicle model
   names from the label vocabulary — while putting the negations *back*, since sklearn's stop
   list strips 13 of them and negation is content in a complaints corpus.
3. **Full sentiment run** — 5,143 computed in 9.3 minutes, 5,341 unique entries cached.
4. **Discovery, four attempts.** HDBSCAN at `min_cluster_size` 89 gave 2 clusters; a sweep
   showed no setting gives ~8 (84 micro-clusters at one end, one cluster of 87% at the
   other); BERTopic's own topic reduction still left one cluster of 3,191. KMeans at k=12,
   which the **owner** suggested, worked. D-061.
5. **`mappings/themes.yaml`** — the owner's eight themes with provenance for each: six
   discovered, two added under D-023's "fixed + discovered mix" because they did not separate
   at k=8 or k=12.
6. **Assignment, two attempts.** One long description per theme gave a compressed similarity
   scale and a misassignment at the median; short max-pooled probes fixed it. D-062.
7. **`tests/test_classify.py`** — 14 tests. Full suite 277 passed, 2 skipped.
8. Reports: `reports/theme_discovery.md`, `reports/theme_assignment.md`,
   `reports/theme_proposal.md` (superseded, kept for its sweep evidence).

## Rows in / out

| Stage | Rows | Note |
|---|---:|---|
| `data/clean/feedback.parquet` in | 7,150 | Wave 3 output |
| With a comment | 5,353 | the only rows any model sees |
| Without a comment | 1,797 | includes the 71 Toowoomba summary rows (D-032 #1) |
| Sentiment labelled | 5,353 | every commented row |
| Theme assigned | 5,353 | every commented row |
| `feedback_classified.parquet` out | **7,150** | asserted in code; the run aborts rather than writing if it differs |

**rows in = rows out = 7,150.** No row is dropped at this stage and none is added. The 1,797
commentless rows rejoin with null sentiment *and* null theme (D-057), which the test suite
asserts against the artifact rather than taking on trust.

## Assumptions

- **Theme descriptions and probes are my wording, not the owner's.** The owner approved eight
  names; I wrote the text that gets embedded. A different wording gives different assignments
  — the first version demonstrably did. `themes.yaml` says this at the top.
- **Null theme for commentless rows** extends D-057, which decided null *sentiment*. No text
  means no theme to have; it was not put to the owner separately.
- **k=12 then merge to 8 names.** Discovery offered 12 candidates and the owner's list is 8
  (D-059). Four candidate clusters were not used: two artefacts (generic praise, vehicle
  model names) and two that duplicated others.
- **`--pilot` writes to the same cache as a full run.** Deliberate: pilot work promotes into
  the full run instead of being thrown away. It also means a pilot's labels persist, so
  `--fresh` exists for when that is not wanted.

## Checks I ran

- `uv run pytest -q` → **277 passed, 2 skipped**. `uv run ruff check .` → clean.
- **The cache claim is proven, not asserted.** `make classify` run twice reported
  `0 computed, 198 from cache, 0.0s`. The test makes `transformers` unimportable, so a test
  that reaches for the model fails rather than quietly passing, and a paired test requires
  `--fresh` to raise, proving the guard is real.
- **Max-pooling is proven against mean-pooling.** The test's vectors are chosen so the two
  disagree — theme A mean 0.5 / max 1.0, theme B mean 0.7 / max 0.7 — so mean-pooling picks
  B and the test demands A.
- **Cache privacy, on the real artifact:** every one of 5,341 lines carries exactly
  `{key, model, label, score}`. Hashes and labels, never comment text (D-026, gate G4).
- **Assignment quality, by spot-check at all ten deciles**, twice — before and after the
  probe fix. Before: 7 of 10 correct, two wrong including one at the median. After: 9 of 10,
  with the single error at p0. Both tables are in D-062.
- Row and column integrity read back from the parquet directly: 7,150 rows,
  `feedback_id` unique, every commented row carrying both new columns, every theme name
  matching `themes.yaml`.

Re-runnable by the owner:

```
uv run pytest tests/test_classify.py -q
uv run python -m src.classify --kmeans-k 12
```

## Unresolved

- **The `unassigned` similarity floor is not set (D-056).** Every comment currently carries
  its nearest theme, including ones about the coffee machine, because KMeans produced no
  outliers *by construction*. `reports/theme_assignment.md` has the distribution and an
  example at each decile. **This is the owner's next decision and nothing in Wave 5 should
  use theme counts before it is made.**
- **Nothing here is evaluated.** Every figure in this report compares the model to the
  customer's star rating, which is not ground truth — that is the whole reason D-055 set the
  pass mark against the owner's blind labels. Under D-017 this agent does not grade itself.
- **The sentiment model fails on sarcasm and Australian idiom** (D-063). Measured, not
  suspected: all eight opposite-signal cases in the pilot were one or the other, several at
  high confidence. The LLM mitigation is scoped but not run; D-024 is the owner's call and
  `reports/llm_review.md` holds the pilot timing.
- **Two of the eight themes have thin volumes** — Workmanship 454 and Explanation 398, so
  roughly 19 and 17 per dealership. Both sit under the 20-response bar D-052 set, which is
  what D-060 already anticipated when it rescoped Wave 5's drivers cut.
- **`reports/run_manifest.json` still does not exist** (PLAN.md §6). Not this brief's output,
  but it is the thing that would record model tags, package versions and row counts per stage
  for a reviewer.
- **c-TF-IDF labels proved unreliable three times** on this corpus. Themes must be named from
  example comments; a reviewer reading only the top terms would misread three of the eight
  clusters.

## Done-when criteria

- [x] Owner approved the theme list, and `mappings/themes.yaml` matches what they approved
- [x] Sentiment label on all 5,353 commented rows
- [x] The 1,797 rows without a comment are explicitly null, never scored as "neutral"
- [x] rows in = rows out: 7,150 in, 7,150 out, nothing gained or lost in the join
- [~] Every comment either carries a theme or is counted as `unassigned`, and the unassigned
      share is stated — **every comment carries a theme and the unassigned share is currently
      zero, because the floor is not set yet (D-056).** The criterion cannot be fully met
      until the owner sets it.
- [x] `make classify` run twice re-runs no model (cache proven, not asserted)
- [x] Committed cache files checked for identifying text
- [x] Tests pass
- [x] Report written to `agents/reports/w4_classifier.md`
- [ ] *(owner)* Read the similarity distribution and set the `unassigned` floor
- [ ] *(owner)* Confirm only redacted text reached the models — Checkpoint 4

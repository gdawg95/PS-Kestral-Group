# Brief: w4_classifier
**Status:** draft, awaiting owner approval (gate G2)
<!-- When approved, replace with: **Approved by:** owner (gdawg95), <date>, <where> -->

**Drafted 29 Oct 2026, Thursday evening.** This is the first of Wave 4's four agents and
the only one whose inputs all exist now. The other three are deliberately not drafted yet,
because each is waiting on something that does not exist:

| PLAN.md's Wave 4 agent | Why not drafted yet |
|---|---|
| Labelling prep | Needs `thresholds.nlp_pass_mark` and the sample design committed first (gate G7, D-022). The sample size *is* part of that decision. |
| LLM (optional) | Needs the 20-comment pilot timing before anyone can say whether it runs in full, on the sample only, or not at all (D-011 cut-off, cut-list item 5). |
| Evaluation | Needs the pass mark and the owner's blind labels. D-017 also forbids this agent from grading its own output, so it must be a separate agent. |

This agent produces the model output. **It does not evaluate it** — gate D-017, producer
is never the checker.

Goal:            Every one of the 5,353 commented rows carries a sentiment label and a
                 theme from an owner-approved list, cached so a reviewer reproduces the
                 result without re-running the models.
Inputs:          data/clean/feedback.parquet (7,150 rows; 5,353 with a comment)
                 config.yaml — models.sentiment, models.embeddings, seed (42)
                 reports/nlp_pass_mark_evidence.md (class distribution and the baseline)
                 DECISIONS.md — D-004, D-010, D-011, D-013, D-017, D-026
Outputs:         src/classify.py (the `make classify` target already points here)
                 reports/theme_discovery.md (candidate clusters, for approval)
                 mappings/themes.yaml (the owner-approved theme list)
                 data/llm_cache/sentiment.jsonl, data/llm_cache/themes.jsonl (committed)
                 data/clean/feedback_classified.parquet (gitignored)
                 tests/test_classify.py
                 agents/reports/w4_classifier.md
Allowed to touch: src/classify.py, tests/test_classify.py, mappings/themes.yaml,
                 reports/theme_discovery.md, data/llm_cache/, Makefile (classify target),
                 agents/reports/w4_classifier.md
Not allowed:     src/ingest.py, src/pii.py, src/schema.py, src/validate.py (gate G3 —
                 propose, do not edit), mappings/columns.yaml, mappings/departments.yaml,
                 data/interim/, data/clean/feedback.parquet (read-only input),
                 DECISIONS.md, AI_LOG.md, and every `thresholds:` key in config.yaml
                 (gate G7 — the owner sets thresholds, not the agent)
Decisions that apply: D-004, D-010, D-011, D-013 (laptop is the reference environment),
                 D-017 (producer is not the checker), D-026 (only redacted text reaches
                 any model)
Runs in:         the laptop repository directly (D-013 revision 2). Both models are
                 already in the Hugging Face cache and `make nlp-check` passes, so this
                 runs offline — no download stands between the owner and a full run.

Steps:
  1. **Sentiment over all 5,353 comments** with `config.yaml`'s model, batched, three
     classes (negative / neutral / positive) plus the confidence score. Cache to
     `data/llm_cache/sentiment.jsonl`, keyed by `hash(text + model tag)` per PLAN.md
     section 6. Measured cost: 131 ms/comment, so roughly 12 minutes.
  2. **Theme discovery.** Embed the comments with `all-MiniLM-L6-v2` and cluster with
     BERTopic at seed 42. Write `reports/theme_discovery.md`: every candidate cluster
     with its size, top terms and **5 example comments**, so the owner is naming clusters
     from evidence rather than from a word list. Then **stop**. Do not proceed to
     assignment, and do not name the themes on the owner's behalf.
  3. **On approval, write `mappings/themes.yaml`** — the owner's final names, each with
     the description that will be embedded for assignment and the examples it came from.
     This file is the contract; Wave 5's drivers analysis groups by it.
  4. **Theme assignment.** Embed each approved theme description, assign every comment to
     its nearest theme by cosine similarity, and record the similarity alongside it.
     Cache to `data/llm_cache/themes.jsonl`. Report the similarity distribution so the
     owner can set the floor below which a comment is `unassigned` (see Q1).
  5. **Write `data/clean/feedback_classified.parquet`** — `feedback.parquet` plus
     `sentiment_label`, `sentiment_score`, `theme`, `theme_similarity`. No column is
     dropped and no row is added or removed.
  6. **tests/test_classify.py**: the cache key is stable across runs; a cache hit skips
     the model entirely (so `make classify` twice is not two model runs); the row count
     survives the join; the committed cache files carry no name, phone, email or plate.

Pilot (G1):      Steps 1–2 on a **200-comment stratified slice** (roughly equal negative /
                 neutral / positive by score), not the usual 20 — 20 comments cannot be
                 clustered into anything meaningful, so a 20-comment theme pilot would
                 prove nothing. What the owner looks at before the full run: the
                 three-class sentiment split against the known score distribution
                 (59.3% positive / 12.7% neutral / 28.1% negative), and whether the
                 candidate clusters look like real service themes rather than noise.

Done when:
  - [ ] Owner approved the theme list, and `mappings/themes.yaml` matches what they approved
  - [ ] Sentiment label on all 5,353 commented rows
  - [ ] The 1,797 rows without a comment are explicitly null, never scored as "neutral"
  - [ ] rows in = rows out: 7,150 in, 7,150 out, nothing gained or lost in the join
  - [ ] Every comment either carries a theme or is counted as `unassigned`, and the
        unassigned share is stated in the report
  - [ ] `make classify` run twice re-runs no model (cache proven, not asserted)
  - [ ] Committed cache files checked for identifying text
  - [ ] Tests pass
  - [ ] Report written to agents/reports/w4_classifier.md

Report back:     what you did · assumptions · unresolved · rows in / out / unassigned

Questions for the owner (answer when approving):
  Q1. **The similarity floor for `unassigned` — set it after seeing the distribution, or
      now?** A cosine floor decides when a comment is too far from every theme to be
      filed under one. Picking it blind invites either a meaningless `unassigned` bucket
      or a silent misfiling. **Proposed default:** the agent runs assignment, shows the
      similarity distribution with example comments at each decile, and the owner sets
      the floor *then* — still before any Wave 5 number uses it, so gate G7 holds.

  Q2. **Rows with no comment — null, or neutral?** 1,797 rows, including the 71 Toowoomba
      summary rows that have no comment by design (D-032 #1). **Proposed default:** null.
      Scoring them neutral would put 1,797 invented neutrals into every theme and
      sentiment total, and D-004 already says the rating is the minimum signal for rows
      like these.

  Q3. **How many themes?** Cut-list item 8 makes "themes beyond the top ~8" cuttable.
      **Proposed default:** aim for 8, accept up to 10 if discovery shows clusters that
      genuinely do not merge. More than that and the drivers table in Wave 5 fragments
      into cells too small to support a recommendation.

# Brief: w4_llm
**Status:** draft, awaiting owner approval (gate G2). The 20-comment timing pilot below is
the one step D-011 requires *before* this decision, so it runs first and on its own.
<!-- When approved, replace with: **Approved by:** owner (gdawg95), <date>, <where> -->

**Drafted 30 Oct 2026, ~02:00.** This is the last of Wave 4's four agents. Its scope changed
before it was written, and the change is the reason it exists at all.

PLAN.md §8 scoped the LLM as an optional extra over "negative/mixed comments plus the
labelled sample" — roughly 2,200 comments — and cut-list item 5 says drop it if time runs
short. It is now something narrower and more useful: **the documented mitigation for a
measured defect**.

The defect, from the classifier's full run: of the 1,887 comments where the deterministic
sentiment model and the customer's own star rating disagree, every one of the eight sampled
in the pilot was **sarcasm or Australian idiom** — *"Oh brilliant, another day of silence. I
love guessing whether my car is finished"* scored positive at 0.49; *"whacked it on the card
and it barely registered. bargain."* scored negative at 0.85. A three-class RoBERTa
classifier has no mechanism for irony. An instruction-tuned model does.

Goal:            Every comment where the sentiment model and the rating disagree gets a
                 third opinion from a local LLM, cached, so the technical report can say how
                 much of that disagreement is irony rather than model error — and so Wave 5
                 is not built on 1,887 silently wrong labels.
Inputs:          data/clean/feedback_classified.parquet (7,150 rows; 5,353 with sentiment)
                 prompts/sentiment_v1.md (v1, owner-approved 30 Oct 2026, Checkpoint 4)
                 config.yaml — models.llm (qwen2.5:3b, ID 357c53fb659c), host, seed,
                 thresholds.llm_max_projected_hours (2)
                 DECISIONS.md — D-004, D-011, D-012, D-013, D-017, D-024, D-026
Outputs:         src/llm_review.py
                 data/llm_cache/llm_sentiment.jsonl (committed, de-identified)
                 reports/llm_review.md (timing, projection, agreement, failure cases)
                 agents/reports/w4_llm.md
Allowed to touch: src/llm_review.py, tests/test_llm_review.py, data/llm_cache/,
                 reports/llm_review.md, Makefile (an `llm` target), agents/reports/w4_llm.md
Not allowed:     src/classify.py, src/ingest.py, src/pii.py, src/schema.py, src/validate.py
                 (gate G3 — propose, do not edit), mappings/, data/interim/,
                 data/clean/ (read-only), DECISIONS.md, AI_LOG.md, prompts/sentiment_v1.md
                 (approved; a change needs a v2 file and fresh approval), and every
                 `thresholds:` key in config.yaml (gate G7)
Decisions that apply: D-004 (negative = 1–2 or negative sentiment), D-011 (the 2-hour
                 cut-off), D-012 (Ollama in Docker, pinned by digest), D-013 (the owner runs
                 Docker; this agent only makes HTTP calls to an already-running container),
                 D-017 (producer is not the checker — this agent does not grade itself, and
                 few-shot examples must not come from the owner's evaluation sample),
                 D-026 (only redacted text reaches any model)
Runs in:         the laptop repository, against Ollama on http://localhost:11434. The owner
                 started the container and confirmed `qwen2.5:3b` ID `357c53fb659c`.

Steps:
  1. **Build the disagreement set** from `feedback_classified.parquet`: every commented row
     where the rating's class (1–2 negative, 3 neutral, 4–5 positive) differs from
     `sentiment_label`. Expected 1,887 of 5,353 — 350 polarity flips plus 1,537 adjacent.
     Record the split, because the flips and the adjacent cases are different claims.
  2. **Pilot (G1/D-011): 20 comments, timed.** Measure tokens/second and seconds/comment as
     observed, not as estimated, and project the full 1,887. Stop there and report.
  3. **On approval, run the full set**, cached to `llm_sentiment.jsonl` keyed by
     `hash(prompt version + text + model tag)`, flushing per batch so a run that dies at
     minute fifty keeps what it has.
  4. **Compare three signals** in `reports/llm_review.md`: the rating, the deterministic
     sentiment, and the LLM. Report how often the LLM sides with each, and the `sarcasm`
     rate it reports — that figure is the whole justification for this agent.
  5. **List ~20 failure cases** for Checkpoint 4: comments where the LLM disagrees with both
     other signals, or returns unparseable output.
  6. **tests/test_llm_review.py**: the disagreement set is built correctly from a synthetic
     frame; the cache key includes the prompt version, so a v2 prompt cannot reuse v1's
     answers; malformed model output is recorded as a failure rather than silently dropped.

Pilot (G1):      20 comments, stratified across the six disagreement cells so the timing is
                 not measured on one easy corner. This is also D-011's cut-off measurement:
                 if the projection exceeds `llm_max_projected_hours` (2), the full run does
                 **not** go ahead at this scope. Fall back in this order: the 350 polarity
                 flips only (~18 min at the estimated rate), then the hand-labelled sample
                 only, then no LLM at all with the sarcasm weakness reported as a measured
                 limitation. **Do not move the cut-off** (PLAN.md §9 stop rule).

Done when:
  - [ ] Pilot timing measured and projected against the 2-hour cut-off, and the owner has
        seen it before any full run (D-024 closes here)
  - [ ] Owner has confirmed only redacted text is sent (gate G4) — `comment` is the
        post-D-026 column and the only field in the request
  - [ ] Every comment in the chosen scope has an LLM verdict or a recorded parse failure;
        no comment is silently skipped
  - [ ] Cache keyed by prompt version, flushed per batch, and holding no comment text
  - [ ] Agreement table covers all three signals, with the sarcasm rate stated
  - [ ] ~20 failure cases listed for the owner
  - [ ] Tests pass
  - [ ] Report written to agents/reports/w4_llm.md

Report back:     what you did · assumptions · unresolved · comments in / adjudicated /
                 parse failures

Questions for the owner (answer when approving):
  Q1. **Scope: all 1,887 disagreements, or the 350 polarity flips only?**
      **Proposed default: all 1,887** — the owner chose this on 30 Oct, on the grounds that
      a flips-only rule covers 19% of disagreements and misses the model's weakest class
      entirely (neutral: only 25.1% diagonal agreement). Subject to step 2's timing.

  Q2. **Does the LLM's verdict change the published sentiment, or only annotate it?**
      **Proposed default: annotate only.** The LLM writes a separate column; `sentiment_label`
      stays as the deterministic model produced it, and Wave 5's headline numbers remain
      reproducible by a reviewer who never starts Ollama. The LLM's value here is the
      *measurement* of how wrong the deterministic labels are on ironic text — a limitation
      the technical report can state with a number instead of a hedge. Overriding the labels
      would make every headline figure depend on a 3B model running on a laptop.

  Q3. **If the LLM and the owner's hand labels disagree on the labelled sample, which is
      reported as correct?**
      **Proposed default: the owner's labels, always.** D-055 sets the pass mark against
      them and D-017 makes them the blind reference. The LLM is a third opinion, never the
      arbiter.

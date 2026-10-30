# Report: w4_llm
**Brief:** agents/briefs/w4_llm.md (approved by the owner, 30 Oct 2026 — scope B, closing D-024)
**Branch:** `w1-wrapup`
**Date:** 30 Oct 2026

## What I did

Adjudicated the 857 comments where the deterministic sentiment model and the customer's star
rating disagree, using `qwen2.5:3b` through Ollama with the owner-approved prompt
`sentiment_v1`. It annotates only: `sentiment_label` is untouched, so every headline number in
Wave 5 is still reproducible by a reviewer who never starts Ollama (brief Q2).

1. **`src/llm_review.py`** — disagreement set, three scopes, the D-011 timing pilot, the full
   run with a cache keyed by prompt version, and the report.
2. **Pilot (G1/D-011), 18 comments** across all six disagreement cells. It is why the scope
   is 857 and not 1,887: measured 3.60 s/comment against my 3 s estimate, so the full set
   would have taken 94% of the two-hour cut-off unattended.
3. **Full run, scope B:** 857 comments in 49.8 minutes — the pilot's projection was 51.6, so
   the marginal rate held. **0 parse failures.**
4. `reports/llm_review.md`, `data/llm_cache/llm_sentiment.jsonl` (committed).

## Rows in / out

| Stage | Rows | Note |
|---|---:|---|
| Commented rows with a model label | 5,353 | input |
| Rating and model disagree | 1,887 | 350 polarity flips, 1,537 adjacent |
| **Scope B** | **857** | flips + every case where the rating is neutral |
| Adjudicated | 857 | 0 parse failures |
| Unique cache entries | 853 | see Assumptions: 4 comments asked twice |
| Rows whose `sentiment_label` changed | **0** | by design (brief Q2) |

Scope B is the four cells where D-004 lets sentiment decide negative status, plus both sarcasm
corners: rating-negative → model-positive (136), rating-neutral → model-negative (308),
rating-neutral → model-positive (199), rating-positive → model-negative (214).

## Assumptions

- **4 comments were asked twice.** The loop was not deduplicated by comment text the way
  `src/classify.py` does with `dict.fromkeys`, so duplicate texts in the corpus produced
  duplicate calls and duplicate cache lines — 857 lines for 853 unique keys. Harmless at
  `temperature 0` (identical answers, last line wins on load) and about 15 seconds wasted.
  Recorded rather than quietly fixed.
- **Scope B excludes 1,030 disagreements** — the 781 positive→neutral and 249 negative→neutral
  cells. The reasoning is in the brief and D-024: the first is the lowest yield per comment and
  the second cannot change the negative count, since those rows are already negative by rating.
- The pilot's cold-start call (24.3s against a 2.1–7.8s spread) was excluded from the marginal
  rate. Including it gives 4.75 s/comment; charging a one-off model load 1,887 times is wrong
  arithmetic. Both figures are in `reports/llm_review.md`.

## Checks I ran

- **0 parse failures in 857**, and 0 in the 18-comment pilot. The JSON contract holds.
- Scope B was verified to select exactly the four intended cells before the run:
  136 + 308 + 199 + 214 = 857.
- The cache holds no comment text on success — `{key, prompt, model, sentiment, sarcasm, raw,
  eval_count, seconds}`, where `raw` is null unless parsing failed. The key includes the prompt
  version, so a v2 prompt cannot reuse v1's answers.
- Measured against the owner's blind labels afterwards (`reports/evaluation.md`): **κ 0.727 on
  the 45 rows that overlap the labelled sample.**

Re-runnable:

```
uv run python -m src.llm_review --pilot 20
uv run python -m src.llm_review --run --scope b
```

## Unresolved

- **The 45.5% sarcasm rate should not be quoted as a finding.** The model flagged sarcasm in
  390 of 857, against 22% in the 18-comment pilot. A 3B model over-flagging is the more likely
  explanation than irony genuinely accounting for nearly half of all disagreement, and nothing
  here distinguishes the two. The technical report should state it as an unvalidated model
  output, not as a measurement.
- **κ 0.727 is on 45 rows, and they are the 45 the LLM was pointed at.** It is evidence that
  the irony problem is tractable, not grounds for promoting a laptop model to primary signal.
  D-065 applies the committed fallback instead.
- The LLM sided with the deterministic model 51.2% of the time and the rating 25.4%, which
  **reverses the pilot's n=18 picture** (9 of 18 for the rating). A standing reminder of what
  an 18-comment sample is worth — including the one in this report.
- The 1,030 excluded disagreements are unadjudicated and will stay that way.

## Done-when criteria

- [x] Pilot timing measured and projected against the 2-hour cut-off before any full run; D-024 closed
- [x] Every comment in the chosen scope has a verdict or a recorded parse failure — 857 of 857, 0 failures
- [x] Cache keyed by prompt version, flushed every 20, holding no comment text on success
- [x] Agreement table covers all three signals, with the sarcasm rate stated **and caveated**
- [x] Report written to `agents/reports/w4_llm.md`
- [ ] *(owner)* Confirm only redacted text was sent — gate G4. The request body carries
      `comment` and nothing else from the row; `comment` is the post-D-026 column
- [ ] *(owner)* Read ~20 failure cases — `reports/llm_review.md`, final section
- [ ] Tests for this module were **not written.** `tests/test_llm_review.py` is in the brief's
      outputs and does not exist; the freeze arrived first. The parse function and the scope
      selector are the two things worth testing if time appears

# LLM adjudication — pilot timing and the D-024 decision

**Status:** pilot only. No full run has happened and nothing is cached. D-024 (LLM in or out,
and at what scope) is the owner's call and this file is the evidence for it.
**Run:** 30 Oct 2026, ~02:10. `qwen2.5:3b` (Ollama ID `357c53fb659c`) at
`http://localhost:11434`, prompt `sentiment_v1` (owner-approved, Checkpoint 4),
`temperature 0`, `seed 42`, `num_predict 24`.

## The disagreement set

1,887 of the 5,353 commented rows, where the rating's class differs from the deterministic
model's label: **350 polarity flips** and **1,537 adjacent** (one step apart, always with
neutral on one side).

## The pilot

18 comments, three from each of the six disagreement cells, so the timing is not measured on
one easy corner. (18 rather than 20: six cells at three each.)

| Measure | Value |
|---|---|
| Parse failures | **0 of 18** — the prompt's JSON contract holds |
| Generated tokens | 15.0 per comment, every time |
| Sarcasm reported | 4 of 18 |

### Timing, stated two ways — and the honest version is the slower one

| Basis | s/comment | Projection for 1,887 | Against the 2h cut-off |
|---|---:|---:|---|
| All 18 calls | 4.75 | **2.49 h** | **Over** |
| Excluding the first call | 3.60 | **1.89 h** | Just under |

The first call took **24.3 seconds** against a 2.1–7.8 second spread for the rest, because it
paid for loading the model into memory. That cost is paid once, so including it in a
per-comment rate and then multiplying by 1,887 charges it 1,887 times, which is wrong
arithmetic. The 3.60 s/comment figure is the better estimate of marginal cost.

**It does not follow that the full run is safe.** 1.89 hours leaves 6% headroom on a two-hour
budget, unattended, on a laptop that the owner describes as occasionally unreliable. Any
thermal throttling, any background process, any retry blows it — and PLAN.md §9 is explicit
that the cut-off does not move when a result is inconvenient.

### Why the rate is far below the recorded one

`config.yaml` records **12.83 tokens/s** from a one-sentence test on 29 Oct. This pilot
measures **3.16 generated tokens/s**. Both are correct and they measure different things: the
prompt here carries four few-shot examples and its instruction block, so each call spends
most of its time on *prefill* — reading roughly 400 prompt tokens — to generate 15. Ollama's
`eval_count` counts only generated tokens, so the stated rate understates the work done.

**Planning implication:** the recorded 12.83 tokens/s should not be used to size any
prompt-heavy run. That is a note worth correcting in `config.yaml`, which this agent is not
allowed to edit (brief: Not allowed).

## Recommended scope: 857 comments, not 1,887

| Scope | Comments | Projected | Covers |
|---|---:|---:|---|
| All disagreements | 1,887 | 1.89 h | Everything, with 6% headroom |
| **Flips + neutral row** | **857** | **0.86 h** | Both sarcasm corners, and the model's weakest class |
| Flips only | 350 | 0.35 h | The sarcasm corners only — 19% of disagreements |

The middle scope is the recommendation. It takes the 350 polarity flips plus the 507 cases
where the *rating* is neutral (308 → negative, 199 → positive) — which is the class the
deterministic model handles worst, at only 25.1% diagonal agreement. It leaves out the 781
positive→neutral and 249 negative→neutral cells, the mildest disagreements and the least
likely to be irony. It costs 43% of the budget instead of 95%.

## What the pilot already suggests

Of the 18 adjudications, the LLM sided with:

| | Count |
|---|---:|
| The customer's rating | 9 |
| The deterministic model | 5 |
| Neither | 3 |

Two things stand out, both tentative at n = 18:

1. **All six rating-3 cases came back `negative`.** That is now a third independent signal
   pointing the same way as the raw text and the deterministic model: a customer who awards
   3/5 *and writes a comment* is usually complaining. It strengthens the case that the
   rating, not the model, is the weak signal on the middle band — and it is why D-055 set the
   pass mark against the owner's blind labels rather than against the rating.
2. **Sarcasm was reported in 4 of 18**, and not only in the flip cells. If that rate holds,
   irony accounts for a meaningful slice of the disagreement rather than a curiosity.

Neither claim is an evaluation. Under D-017 this agent does not grade itself, and the owner's
hand labels remain the only reference that decides anything.

## What the owner decides (D-024)

1. **Scope:** all 1,887, the recommended 857, flips only, or no LLM at all.
2. **Confirm gate G4:** only the redacted `comment` column is sent, and nothing else from the
   row. That is what the code does; the owner confirms it.
3. Whether the LLM annotates only, or overrides `sentiment_label` — brief Q2 proposes
   annotate only, so Wave 5's headline numbers stay reproducible without Ollama.

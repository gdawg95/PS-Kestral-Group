# Prompt: sentiment_v1

**Version:** v1 · **Created:** 30 Oct 2026
**Approved by:** owner (gdawg95), 30 Oct 2026, in conversation — prompt v1 and the
`qwen2.5:3b` model tag both approved for the full run (Checkpoint 4: "approve model tags and
prompt version before full runs").
**Model:** `qwen2.5:3b` (Ollama ID `357c53fb659c`), pinned in `config.yaml`
**Parameters:** `temperature 0`, `seed 42`, `num_predict 24` — deterministic, and short output
because the 2-hour cut-off (D-011) is a token budget before it is anything else.

## What this is for

Not a second opinion on every comment. This prompt runs **only on the comments where the
deterministic sentiment model and the customer's own rating flatly contradict each other** —
a negative rating labelled positive, or a positive rating labelled negative. Measured on the
198-comment pilot, every one of those contradictions was sarcasm or Australian idiom, which a
three-class RoBERTa classifier has no mechanism for and an instruction-tuned model does.
About 4% of comments, roughly 215 corpus-wide.

## D-017 compliance: the few-shot examples are hand-written

D-017 requires that few-shot examples **must not come from the owner's hand-labelled
evaluation sample**. That sample is drawn from the commented rows with seed 42, and this
project's pilot slices are drawn the same way, so *any* real comment carries a contamination
risk. The four examples below are therefore **written by hand, not taken from the corpus** —
there is no overlap to argue about. They are in the register of the data (Australian, informal,
sarcastic) without being of it.

## Redaction tokens

The text arrives de-identified (D-026). `[NAME]`, `[STAFF]`, `[REGO]`, `[PHONE]`, `[EMAIL]`
and `[ADDRESS]` are redaction placeholders, not words the customer wrote. The prompt says so,
so the model does not try to read meaning into them.

## Template

```text
You classify customer feedback for Australian car dealerships.

Read the comment and decide its overall sentiment: negative, neutral, or positive.

Rules:
- Judge what the customer actually feels, not the words in isolation.
- Australian English, informal and often sarcastic. Sarcasm means the literal words
  are positive but the feeling is negative. Praise-shaped complaints are negative.
- Idiom is not sarcasm: "bloody good", "top blokes", "easy as", "bargain", "good as
  gold", "no worries" are genuine praise. "Not bad" is mild praise.
- A comment that praises one thing and complains about another is negative if the
  complaint is the point, positive if the praise is.
- neutral means no clear feeling either way: a bare fact, a question, a request.
- [NAME], [STAFF], [REGO], [PHONE], [EMAIL] and [ADDRESS] are redaction placeholders.
  Ignore them.

Answer with JSON only, no explanation:
{"sentiment": "negative|neutral|positive", "sarcasm": true|false}

Examples:

Comment: Oh fantastic, another week without the car. Love it.
{"sentiment": "negative", "sarcasm": true}

Comment: Bloody good bunch of blokes, sorted it while I waited.
{"sentiment": "positive", "sarcasm": false}

Comment: Staff were lovely. Still waiting on the part three weeks later though.
{"sentiment": "negative", "sarcasm": false}

Comment: Dropped the ute off Tuesday at the [ADDRESS] branch.
{"sentiment": "neutral", "sarcasm": false}

Comment: {comment}
```

## Why `sarcasm` is in the output

It costs about four tokens and it answers a question the technical report has to answer
anyway: how much of the disagreement between rating and model is irony, rather than the
model simply being wrong. Without it the mitigation is untestable.

## What this prompt is NOT allowed to do

- It does not relabel comments where the model and the rating agree. Those keep the
  deterministic label, so the headline numbers stay reproducible without an LLM.
- It does not see, and must never see, unredacted text (gate G4).
- Its output does not decide the pass mark. The owner's blind labels do (D-055), and the
  evaluation agent — not this one — measures against them (D-017).

# LLM adjudication — full run

**Scope B**: 857 comments, run 30 Oct 2026. `qwen2.5:3b` (Ollama ID `357c53fb659c`), prompt `sentiment_v1`, `temperature 0`, `seed 42`, `num_predict 24`.
**Wall clock:** 49.8 minutes (3.49 s/comment) against D-011's 2-hour cut-off.

Scope B is every polarity flip plus every case where the customer's rating is neutral. Under D-004 the sentiment label only decides whether a row counts as negative when the rating is not 1–2, so these are the cells that can move a reported number, plus both sarcasm corners. D-024.

## Which signal the LLM sided with

| | Count | Share |
|---|---:|---:|
| The customer's rating | 218 | 25.4% |
| The deterministic model | 439 | 51.2% |
| Neither | 200 | 23.3% |

**Sarcasm reported in 390 of 857 (45.5%).** That figure is the justification for this agent: it is the share of the disagreement that irony explains, rather than the deterministic model simply being wrong.

**Parse failures: 0 of 857.** Recorded, never dropped.

## By disagreement cell

| Rating | Model | LLM negative | LLM neutral | LLM positive | n |
|---|---|---:|---:|---:|---:|
| negative | positive | 136 | 0 | 0 | 136 |
| neutral | negative | 308 | 0 | 0 | 308 |
| neutral | positive | 197 | 1 | 1 | 199 |
| positive | negative | 130 | 3 | 81 | 214 |

## What this does NOT do

It does not change `sentiment_label` (brief Q2). Every headline number in Wave 5 still comes from the deterministic model, so a reviewer who never starts Ollama reproduces them exactly. And it is not an evaluation: under D-017 this agent does not grade itself, and if the LLM and the owner's blind labels disagree, the owner's labels are correct (brief Q3).

## Failure cases for Checkpoint 4

Comments where the LLM disagreed with **both** other signals, or returned unparseable output. The owner reads about 20 of these.

**rating 3 (neutral) · model positive · llm negative**

> Great speed on the timing belt job, they got it done in the one day like they said. Getting that day was the problem, because the first two dates I asked for were both full. Call me on [PHONE].

**rating 3 (neutral) · model positive · llm negative**

> helpful, cheerful staff. wait on the phone was well over 15 minutes.

**rating 3 (neutral) · model positive · llm negative**

> Gee, the explanation of the work was top notch, really easy to follow. The bill was a different story, they charged me for a premium oil when I'd asked for the standard one.

**rating 3 (neutral) · model positive · llm negative**

> Ahh yes, a 'quick' service. Four hours, I sat there for. Wonderful way to spend a Thursday, tank you.

**rating 3 (neutral) · model positive · llm negative**

> Good people, very nice to deal with. Slow, slow, slow.

**rating 3 (neutral) · model positive · llm negative**

> Oh brilliant, they actually finished the service when they said they would. Shame they couldn't find my booking when I rocked up.

**rating 3 (neutral) · model positive · llm negative**

> Service done and dusted in 90 minutes. Lovely. The booking, on the other hand, was somehow not in the diary when I arrived.

**rating 3 (neutral) · model positive · llm negative**

> Great welcome, helpful staff. Problem not fixed.

**rating 3 (neutral) · model positive · llm negative**

> Good on the team for making it all easy to understand. Not so good on the quote, which was blown out by about 30 percent.

**rating 3 (neutral) · model positive · llm negative**

> Wonderful, warm people. Took half the day, mind you.

**rating 3 (neutral) · model positive · llm negative**

> I was greeted warmly and treated with courtesy by all staff. Regrettably, the required part was unavailable and the waiting time was considerably longer than quoted.

**rating 3 (neutral) · model positive · llm negative**

> Thanks to [STAFF], very pleasant. Waited.

**rating 3 (neutral) · model positive · llm negative**

> Lovely welcome. Rubbish booking experience.

**rating 3 (neutral) · model positive · llm negative**

> New to the area and the front desk folks were so welcoming, gave me tips on where to get a decent coffee too. Wish the same care went into the wipers, because they're still chattering across the glass.

**rating 3 (neutral) · model positive · llm negative**

> Great, a new rattle in the glovebox lid. Brilliant work as always.

**rating 3 (neutral) · model positive · llm negative**

> The work was done well before I expected, which was lovely at my age as I don't like hanging about. But I rang twice to ask a question and nobody got back to me, I felt a bit forgotten.

**rating 3 (neutral) · model positive · llm negative**

> really nice staff, and i mean that. shocking how long i was left on hold though.

**rating 3 (neutral) · model positive · llm negative**

> The handover at pickup was spot on, [STAFF] went through each item on the invoice and what it meant for the van. Wish I could say the same for getting a time slot, I needed it back on the road for work and the diary was a mess.

**rating 3 (neutral) · model positive · llm negative**

> Excellent friendly service from [STAFF]. Not impressed with the long wait on the day, though.

**rating 3 (neutral) · model positive · llm negative**

> nice helpful staff, wait was too long tho

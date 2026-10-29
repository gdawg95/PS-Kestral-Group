# Theme assignment — the similarity distribution

**5353 comments** assigned to 8 approved themes (`mappings/themes.yaml` v1). Cosine similarity to the embedded theme description.

## What the owner decides here (D-056)

The floor below which a comment is `unassigned`. KMeans produced no outliers by
construction, so every comment — including the ones about the coffee machine — is
currently filed under its nearest theme. This floor is the only thing that pulls
them back out, which makes it a more consequential choice than it looks.

## Distribution

| decile | similarity |
|---|---:|
| min | 0.113 |
| p10 | 0.295 |
| p20 | 0.34 |
| p30 | 0.371 |
| p40 | 0.398 |
| p50 | 0.424 |
| p60 | 0.451 |
| p70 | 0.485 |
| p80 | 0.522 |
| p90 | 0.582 |
| max | 0.924 |

## Per theme

| theme | comments | mean similarity |
|---|---:|---:|
| Staff manner | 1395 | 0.474 |
| Waiting and turnaround | 881 | 0.414 |
| Communication and updates | 802 | 0.424 |
| Pricing and billing | 686 | 0.457 |
| Workmanship and rework | 454 | 0.375 |
| Explanation and transparency | 398 | 0.376 |
| Booking | 369 | 0.434 |
| Parts availability | 368 | 0.415 |

## Example comments at each decile

Read these to decide where the floor belongs: the point where a comment stops being
about its assigned theme.

**p0 — similarity 0.113, assigned to *Communication and updates***

> Straight answers on how the dual battery setup and the drawbar load rating work on the Altura Vista. Needed that sorted before I put it on the books.

**p10 — similarity 0.295, assigned to *Parts availability***

> Fuel cap lock key missing.

**p20 — similarity 0.340, assigned to *Waiting and turnaround***

> Great explainer. Half day gone tho

**p30 — similarity 0.371, assigned to *Waiting and turnaround***

> Been loyal to this place for over a decade and the quick turnaround is a big part of why I keep coming back.

**p40 — similarity 0.398, assigned to *Workmanship and rework***

> My first service as a new owner was a bit of a letdown. The wheel nuts weren't tightened properly and I heard a clunk on the way home. When I called to tell them, I was promised a call back and haven't heard a thing since.

**p50 — similarity 0.424, assigned to *Waiting and turnaround***

> My EV was back in the carpark ready to go well before pickup time. Love that.

**p60 — similarity 0.451, assigned to *Workmanship and rework***

> Oh fantastic, the engine light is back. That fix lasted all of a weekend.

**p70 — similarity 0.485, assigned to *Parts availability***

> Wow, so the parts department can order anything in the world as long as it arrives sometime next month. Lovely.

**p80 — similarity 0.522, assigned to *Staff manner***

> genuinely pleasant bunch. didn't feel rushed or like a nuisance.

**p90 — similarity 0.582, assigned to *Staff manner***

> Terrific bunch of staff, all very welcoming to a newcomer like me. Thanks for making us feel at home.

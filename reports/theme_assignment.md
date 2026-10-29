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
| min | 0.017 |
| p10 | 0.187 |
| p20 | 0.235 |
| p30 | 0.269 |
| p40 | 0.299 |
| p50 | 0.328 |
| p60 | 0.355 |
| p70 | 0.387 |
| p80 | 0.425 |
| p90 | 0.475 |
| max | 0.712 |

## Per theme

| theme | comments | mean similarity |
|---|---:|---:|
| Communication and updates | 1216 | 0.340 |
| Staff manner | 1189 | 0.344 |
| Pricing and billing | 706 | 0.347 |
| Parts availability | 688 | 0.320 |
| Booking | 678 | 0.342 |
| Waiting and turnaround | 442 | 0.300 |
| Explanation and transparency | 234 | 0.279 |
| Workmanship and rework | 200 | 0.262 |

## Example comments at each decile

Read these to decide where the floor belongs: the point where a comment stops being
about its assigned theme.

**p0 — similarity 0.017, assigned to *Booking***

> Spent a good whle going over the Arc controls with me, then had me try them myself. Stuck in my head better that way. (rego [REGO])

**p10 — similarity 0.187, assigned to *Communication and updates***

> Zero updates Saff attitude shocking

**p20 — similarity 0.235, assigned to *Pricing and billing***

> The value is there Compared to the market, the price on this E3 is hard to beat (rego [REGO])

**p30 — similarity 0.269, assigned to *Staff manner***

> Helpful people with big smiles. Thank you very much.

**p40 — similarity 0.299, assigned to *Pricing and billing***

> Rego service done in 2 hrs, ok. Then got hit with a $60 charge i wasnt told about

**p50 — similarity 0.328, assigned to *Parts availability***

> I was dreading losing the whole day without a car, but it was ready by early afternoon, as promised. Made my week a lot easier.

**p60 — similarity 0.355, assigned to *Communication and updates***

> I wish all businesses updated customers like this Text at drop-off, text at diagnosis, call when finished

**p70 — similarity 0.387, assigned to *Staff manner***

> Yeah, good. [STAFF] told him straight what the part does and what it doesn't. No dramas.

**p80 — similarity 0.425, assigned to *Waiting and turnaround***

> I've done my own servicing for decades and I know roguhly how long a timing belt job takes. This took double that, with the car sitting idle for most of the day.

**p90 — similarity 0.475, assigned to *Pricing and billing***

> Friendly service, no complaints there. The invoice, though, had fees I wasn't told about. First car I've owned so I wasn't sure if that was normal, but it felt off.

# Proposed theme list — for the owner to approve, rename or reject

**Status: SUPERSEDED — kept as evidence, not as a proposal.**

Written 30 Oct 2026 at about 00:50, when HDBSCAN had failed twice and the theme list looked
as though it would have to be asserted by hand. Switching the clusterer to KMeans changed
that: six of the eight themes were then discovered from the data after all. The approved list
lives in `mappings/themes.yaml`, and D-023 was closed on 30 Oct 2026.

What is still worth reading here is the next section — the `min_cluster_size` sweep and the
record of how and why HDBSCAN failed. The technical report's methods section draws on it, and
it is the evidence that the two hand-added themes were added because clustering could not
isolate them rather than because nobody tried.

## Why this is a proposal rather than discovery output

D-023 always allowed a "fixed + discovered mix". The discovered half did not work, and the
evidence is worth keeping because the technical report has to explain the choice.

A `min_cluster_size` sweep over all 5,353 comments found no setting that yields roughly eight
themes:

| min_size | clusters | outliers | largest cluster |
|---:|---:|---:|---:|
| 10 | 84 | 27.3% | 533 |
| 15 | 42 | 20.0% | 836 |
| 20–30 | 7 | 0.0% | **4,649** |
| 40 | 5 | 1.7% | 4,632 |
| 89 | 2 | 1.0% | 4,862 |

Either 84 micro-clusters, or one cluster holding 87% of the corpus. BERTopic's own topic
reduction (over-cluster at 15, merge to 10) did not fix it either: the merged result still
had one cluster of 3,191 comments, 60% of the corpus.

**What the clusters grouped on, when they grouped on anything:**

1. **Vehicle systems, not experience.** A 218-comment cluster on "brake, tyre, pads" put
   *"charged for a brake fluid flush i never approved"* beside *"Great explaining from
   [STAFF]"*. Same repair, opposite experiences.
2. **Overall positivity.** A 437-comment cluster on "good, service, friendly" and a
   191-comment cluster on "smooth, easy, explained" are both just *satisfied customers*.
3. **Everything else**, in one 3,191-comment cluster whose examples span the full range from
   *"Very welcome feeling Staff are helpful"* to *"LONG QUEUE AT THE COUNTER... NOT GOOD
   ENOUGH"*.

This is a reasonable outcome for 101-character comments about a service visit: what the
customer talks about is the car, and how they feel about it is a separate axis. Theme
*assignment* (brief step 4) never needed discovery — it needs a list with descriptions, which
is what follows.

## The proposed eight

Every theme below was observed in comments surfaced during tonight's pilot and full runs. The
quotes are real, redacted comment text.

### 1. Waiting and delays
Time lost at the dealership or waiting for the car, where the wait itself is the complaint.
> "Waited ages. No parts."
> "LONG QUEUE AT THE COUNTER, THEN A LONG WAIT FOR THE CAR..."
> "Why does it take three weeks to get a booking and then all day to do a brake pad swap?"

### 2. Communication and updates
Not being told what is happening; having to chase for status.
> "Hold music for 20 minutes just to ask if my car was done. Then they said they'd call back. They didn't."
> "Had to ring three times just to find out if my car was ready. Nobody rang me once."
> "Staff were top blokes, no complaints. Not one update though unless I picked up the phone myself."

### 3. Pricing and billing
Charges that were unapproved, unexpected, or did not match the quote.
> "friendly staff. charged for a brake fluid flush i never approved."
> "in and out so fast i barely got through my coffee. then the invoice came with a pile of extras i never said yes to."
> "trade pricing for our work utes is competitive and the invoice matched the quote."

### 4. Workmanship and rework
The job was not done right, or the original fault remains.
> "Replaced the coolant hose, now there's a drip from the clamp. Pretty sloppy."
> "Rear brakes were done but the car plls hard to one side."
> "Good communication. Poor workmanship. Oil leak is still there."

### 5. Parts availability
Work blocked or stretched out because a part was not on hand.
> "PENSIONER HERE. PART DIDN'T ARRIVE, CAR STUCK THERE, TAXI FARES ADDING UP."
> "the part wasn't on hand, and i was told it would be ordered from a warehouse in another state. it took nearly two weeks."
> "not once have they had what i needed on hand. always 'we'll odrer it in'."

### 6. Booking and scheduling
Getting in at all: availability, lost bookings, being bumped.
> "Booked online, got bumped, and still not fixed."
> "Great bunch of people. Booikng was a pain."

### 7. Staff manner and respect
How the customer was treated, independent of the work.
> "The man at parts laugh at me and say I should ask my father. This is very disrespectful."
> "Waited and waited. Staff rude."
> "Bloody good bunch of blokes. Always have a bit of a chat and a laugh before getting down to business."

### 8. Explanation and transparency
Whether the work and the invoice were explained in terms the customer understood.
> "Finally someone who tells you what's wrong in words a normal person gets."
> "Reckon I could now explain a brake fluid flush to someone else. Great explaining from [STAFF]."
> "Nobody showed me the charge port..."

## One candidate deliberately left out

**Facilities** — dirty toilets, no parking — appeared (*"dirty toilets, no parking, car not
ready. typical."*) but almost always alongside a larger complaint, and D-059 caps the list at
8. Raise it to a ninth theme only if it earns the slot ahead of one above.

## What a theme is here, and what it is not

A theme is a **subject**, not a complaint category. Each one above has positive and negative
examples deliberately, because Wave 5 reports the negative *rate within* each theme — which
only works if the theme itself is sentiment-neutral. A "bad service" theme would double-count
what the sentiment column already says.

## What happens after approval

1. The approved names and descriptions go into `mappings/themes.yaml`.
2. Assignment embeds each description and attaches every comment to its nearest theme,
   recording the cosine similarity.
3. The similarity distribution comes back to the owner, who sets the `unassigned` floor
   (D-056) before any Wave 5 number uses it.

**Coverage is unknown until step 2 runs.** If a theme attracts almost nothing, it is the wrong
theme and should be replaced — that check is part of approving the list, not a formality after
it.

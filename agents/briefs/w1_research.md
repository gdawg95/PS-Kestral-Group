# Brief: w1_research
**Status:** written retrospectively, 29 Oct 2026 (Thursday evening). PLAN.md §8 listed this agent in Wave 1, but no brief was ever drafted. This is the brief the run should have had, written alongside the run so the work can be checked against it. Awaiting owner approval (gate G2).
<!-- When approved, replace with: **Approved by:** owner (gdawg95), <date>, <where> -->

Goal:            A cited benchmark summary exists that gives Wave 5's value model low/mid/high
                 ranges for service retention, customer lifetime value and the cost of a lost
                 customer, and says plainly whether a 1–5 rating can be linked to dollars.
Inputs:          PLAN.md §1 (business question 3), §8 (Wave 1 Research row, Wave 5 Value model)
                 DECISIONS.md: D-004, D-006, D-018, D-020, D-025
                 monthly_revenue.csv and dealerships.csv (aggregates only, to express
                 per-unit benchmarks in Kestrel's own dollars)
                 Public web sources only
Outputs:         reports/benchmarks.md
                 agents/reports/w1_research.md
                 Proposed DECISIONS.md D-025 entry and AI_LOG entry, as text in the final
                 chat message (not written to those files)
Allowed to touch: reports/benchmarks.md, agents/briefs/w1_research.md,
                 agents/reports/w1_research.md
Not allowed:     DECISIONS.md, AI_LOG.md, PLAN.md, README.md, src/, tests/, mappings/, data/
                 (other agents are working in the same checkout). No commits, no branch
                 switches.
Decisions that apply: D-004 (negative = 1–2), D-006 (coverage), D-018 (separate
                 conversation), D-025 (low/mid/high, owner sets values: gate G7)
Runs in:         cloud workspace (web research). Files written to the laptop checkout
                 through the bridge (D-013).

Steps:
  1. Read PLAN.md and DECISIONS.md.
  2. Research four items: (1) dealer service retention and the effect of a poor
     experience, (2) CLV with service and repurchase streams separated, (3) the cost of
     a lost customer, meaning revenue forgone plus replacement acquisition cost,
     (4) evidence linking a satisfaction score to retention.
  3. Prefer, in order: Australian industry bodies and published surveys → peer-reviewed
     work → foreign industry surveys → vendor material (flagged as such).
  4. For every figure, record the source, year, market and a weight
     (High / Medium / Low / Do not use).
  5. Give low/mid/high for items 1–3. Where a value is arithmetic rather than sourced,
     say so in the table.
  6. List the assumptions needed to apply the figures to 24 Australian dealerships and
     mark the shaky ones.
  7. Write a "what Wave 5 can and cannot claim" section.
  8. Re-check that every number in benchmarks.md appears in its cited source, and that
     the derived arithmetic is correct.

Pilot (G1):      n/a. Single, non-bulk agent.

Done when:
  - [ ] reports/benchmarks.md holds low/mid/high ranges for items 1–3
  - [ ] Every number carries a citation, year, market and weight
  - [ ] Item 4 states plainly whether a rating can be linked to dollars
  - [ ] The assumptions needed to apply the figures to the dataset are listed, with the
        shaky ones flagged
  - [ ] Figures that cannot be sourced are reported as "not found", not estimated
  - [ ] Owner spot-checks the 5 load-bearing figures against their sources
  - [ ] Report written to agents/reports/w1_research.md

Report back:     what you did · sources · assumptions · what could not be found

Questions for the owner (answer when approving):
  Q1. Segment: treat Kestrel's brands as "volume" for the Deloitte benchmarks?
      Default: yes.
  Q2. Mid values that are arithmetic midpoints (retention gap 50 pts, service visits
      1.7/yr): keep them as labelled midpoints, or drop the mid case?
      Default: keep, labelled.
  Q3. US dollar figures: context only, or converted for use?
      Default: context only.

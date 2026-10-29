# Brief: w3_validate
**Status:** draft, awaiting owner approval (gate G2)
<!-- When approved, replace with: **Approved by:** owner (gdawg95), <date>, <where> -->

**Drafted 29 Oct 2026, after Wave 2 finished.** Two of PLAN.md section 8's four Wave 3
agents have been removed from scope and one has shrunk, because Wave 2 settled their work:

| PLAN.md's Wave 3 agent | Status now |
|---|---|
| DQ rules (pandera) | **In scope**, and the main job. Steps 1–3 below. |
| Dealership matching | **Removed.** D-034: the file → dealer code map is approved by hand and no free-text dealership column survives ingestion, so there is nothing to fuzzy-match. `thresholds.dealer_match_min_confidence` is retired, not set. |
| Dates and scales | **Mostly done.** Ingestion already converts every rating to 1–5 (D-020, D-030) and parses every date format, with `date_corrected` / `date_approx` flags. What remains is the edge-case list for Checkpoint 3 — step 4. |
| Theme discovery (BERTopic) | **Moved to Wave 4**, where the rest of the NLP lives and the laptop's models are available (D-013). |

What is new in scope and was not in PLAN.md: filling the `department` column from
`mappings/departments.yaml` (step 2), because Wave 2 deliberately left it null (D-035),
and deciding the Springwood duplicates (step 5, closing D-019).

Goal:            A validated clean dataset with `department` filled and every data-quality
                 rule applied, counted and reported — so Waves 4 and 5 can stop asking
                 whether the data is trustworthy and start using it.
Inputs:          data/interim/consolidated.parquet (7,159 rows, Wave 2)
                 mappings/departments.yaml (owner-approved: Checkpoint 3)
                 reports/reconciliation.md (the Wave 2 evidence, including the duplicates)
                 DECISIONS.md — D-003, D-019, D-020, D-026, D-030 – D-046
Outputs:         src/validate.py, tests/test_validate.py
                 data/clean/feedback.parquet (gitignored)
                 reports/data_quality.md (the waterfall, 5 example rows per rule)
                 agents/reports/w3_validate.md
Allowed to touch: src/validate.py, tests/test_validate.py, mappings/departments.yaml,
                 reports/data_quality.md, Makefile (validate target),
                 agents/reports/w3_validate.md
Not allowed:     src/ingest.py, src/pii.py, src/schema.py (gate G3 — propose, do not edit),
                 mappings/columns.yaml, DECISIONS.md, data/interim/
Decisions that apply: D-003, D-017 (producer ≠ checker — this agent is NOT the one that
                 wrote src/ingest.py), D-019, D-020, D-026, D-031, D-035, D-036 – D-046
Runs in:         the laptop repository, directly (D-013 revision 2)

Steps:
  1. **pandera schema over the 15 columns**, with each rule classified the way PLAN.md
     asks — reject / fix-and-flag / flag-and-keep — and a count for every rule, including
     the rules that fire zero times. A rule that never fires is evidence, not dead code.
     At minimum: dealer_code in dealerships.csv; feedback_date inside Oct 2025 – Sep 2026;
     rating_1to5 an integer 1–5; department_raw non-empty; comment either null or
     non-empty (never `""` — Wave 2 had that bug and fixed it); feedback_id unique and
     well-formed; from_summary rows carry no comment; nothing outside the allowlist.
  2. **Fill `department`** from `mappings/departments.yaml`. Every one of the 16
     department_raw values maps to exactly one of Service / Sales / Parts, which
     `scripts/check_departments.py` already asserts. Report the three totals and fail if
     any row comes out null.
  3. **The data-quality waterfall** → `reports/data_quality.md`: rows in, each rule's
     effect with a count, rows out, and 5 example rows per rule for Checkpoint 3. Example
     rows must be lineage plus the kept columns — never a name, phone, email or plate.
  4. **The date edge-case list** for Checkpoint 3: the 6 `date_corrected` rows
     (Shepparton, D-032 #3) and the 10 `date_approx` rows (Ipswich, D-040), with the
     source value, the resolved date and the reason, so the owner can look at 16 rows
     rather than 20 arbitrary ones.
  5. **The Springwood duplicates** (closes D-019). Wave 2 found 9 pairs of *adjacent*
     rows in `Springwood feedback.xlsx` sharing dealership, date, department, rating and
     comment text — one of them a 463-character comment. Adjacency in every single pair
     is what makes this double entry rather than coincidence. Put the 9 pairs to the
     owner with their row numbers and let them decide; implement what they choose and
     report the effect on Springwood's mean either way. **Do not de-duplicate before
     asking** — removing 9 rows moves a dealership's published score.
  6. **tests/test_validate.py**: one test per rule, on synthetic frames. Include a test
     that a row violating a reject rule is actually rejected rather than silently fixed,
     and a test that the department fill is total (no null survives).

Pilot (G1):      Run steps 1–3 on the three dealerships whose data is most likely to trip
                 a rule — VIC09 Shepparton (closed site, corrected years), QLD03 Ipswich
                 (approximate dates), QLD06 Toowoomba (71 summary-expanded rows with no
                 comment) — and show the owner the waterfall for those before running it
                 over all 7,159 rows.

Done when:
  - [ ] Owner approved `mappings/departments.yaml` (Checkpoint 3)
  - [ ] Owner decided the Springwood duplicates (closes D-019)
  - [ ] Owner skimmed 5 example rows per rule and the 16 date edge cases
  - [ ] Every pandera rule has a count, including the zero ones
  - [ ] `department` is non-null for all 7,159 rows and the three totals match
        `mappings/departments.yaml`
  - [ ] rows in = rows out + rejected, by rule, and the arithmetic closes in the report
  - [ ] Tests pass
  - [ ] Report written to agents/reports/w3_validate.md

Report back:     what you did · assumptions · unresolved · rows in / out / rejected per rule

Questions for the owner (answer when approving):
  Q1. **The Springwood duplicates — remove one of each pair, or keep both?**
      9 pairs, 18 rows, 0.25% of the dataset and 5.8% of Springwood's 310 rows. Every
      pair sits on consecutive spreadsheet rows and one pair repeats a 463-character
      comment, so these are almost certainly one piece of feedback saved twice.
      **Proposed default:** drop the second row of each pair, flag it in the data-quality
      report, and state Springwood's mean both ways so the effect is visible. The
      alternative — keeping both — inflates Springwood's volume by 9 and double-weights
      9 opinions, including a 463-character complaint.
      *This is the last thing standing between D-019 and closed.*

  Q2. **"Workshop" → Service: confirm?**
      311 rows across 10 dealerships, mean 3.86 against plain "Service" at 3.51 — a 0.35
      gap that is worth one look before it is folded away. In a dealership "workshop"
      normally means the service bays, and no site uses "Workshop" and "Service Dept" as
      though they were different things. **Proposed default:** map to Service.

  Q3. **Should the report carry a new-versus-used cut of Sales?**
      326 rows (21% of all Sales) carry the distinction, at 11 of 24 sites. New averages
      4.58 / 4.22, used 4.34 / 4.27. **Proposed default:** keep one Sales department for
      every headline number, carry the subtype in `departments.yaml`, and produce the cut
      only if asked — because the 11 sites that record it are self-selected, so no
      group-wide claim is available either way.

  Q4. **`nlp_pass_mark` (gate G7) — needed before Wave 4's hand-labelling, not before
      this wave.** Flagged here so it is not discovered late: the owner must set the
      sentiment-agreement and theme-quality bar, and label the evaluation sample blind to
      model output. **Proposed default:** sentiment agreement ≥ 80% on a 100-comment
      hand-labelled sample, with the fallback being rule-based sentiment only and the
      limitation stated in both reports.

# Report: w1_research
**Brief:** agents/briefs/w1_research.md (written retrospectively; see its status line)
**Branch:** none. Files left uncommitted in the working tree on the owner's instruction.
**Date:** 29 Oct 2026

## What I did
I researched public benchmarks for the Wave 5 value model and wrote them up in `reports/benchmarks.md`. Every figure carries a source, year, market and weight, with low/mid/high ranges for retention, CLV and lost-customer cost, an assumptions table and a can/cannot-claim section.

1. Read PLAN.md and DECISIONS.md from the Claude project.
2. Ran about 15 web searches and fetched 17 pages: J.D. Power releases (US 2009, AU 2012/2013/2016, UK 2016, US 2025), Cox Automotive 2025, Deloitte Australia Dealership Benchmarks 2025 and 2026, the AAAA 2018 consumer survey, AADA Dealernomics 2026 (via CarExpert), NADA 2024 (via TVB), Bain/Reichheld, and Mittal & Kamakura (2001).
3. Computed Kestrel's own revenue ratios from `monthly_revenue.csv` (aggregates only): A$415.53 per service job, A$46,463 sales revenue per vehicle, 12.5 service jobs per vehicle sold.
4. Re-checked the derived arithmetic in §5 of benchmarks.md and corrected one rounding slip (A$3,828 → A$3,830).

Files written: `reports/benchmarks.md`, `agents/briefs/w1_research.md`, `agents/reports/w1_research.md`.

### Revision v2 (30 Oct 2026, owner request)
The owner judged the pre-2023 sources too old (everything except Deloitte 2026). I widened the scope to automotive retail generally and cross-industry CX research, and rebuilt every range from 2023–2026 sources:
- **Added:**
  - J.D. Power 2026 U.S. CSI: 86–88% definite return at 950+, and the KPI effect, 979 vs 632.
  - J.D. Power 2025 U.S. CSI: only 50% return after a repair that wasn't fixed.
  - Qualtrics XM Institute 2025: auto dealers lose 23% of customers outright and 38% cut spending after a very poor experience. Australian bad-experience rate 11%.
  - Mittal et al. 2023 meta-analysis: satisfaction–retention r = 0.60, behaviour r = 0.21 vs intent r = 0.65.
  - Cox 2025: 80% of new buyers intend to return for service, and two-thirds keep cars 5+ years.
  - Cox 2025 Car Buyer Journey.
  - Compare the Market 2025.
- **Moved to Appendix A (cross-check only):** AAAA 2018, J.D. Power AU 2013, J.D. Power UK 2019 (UK 2016 dropped in favour of 2019), Mittal & Kamakura 2001.
- **Removed:** J.D. Power US 2009, AU 2012, UK 2016 and the 2016 AADA presentation (A$1.9bn).
- **Ranges changed:**
  - Service retention: 29 / 55* / 80% (was 37 / 60 / 79).
  - Poor-experience effect: now a loss rate of 23 / 50 / 61% (was an intent gap of 25 / 50* / 75 pts).
  - Repurchase: 43 / 60.5* / 78% (was 23 / 44 / 78), still from the older UK 2019 source because nothing newer exists.

  \* = arithmetic midpoint.
- **New do-not-use:** Finder's "Australians own cars 11 years 3 months (BITRE)". BITRE publishes fleet age, not ownership length.
- **Still no 2023+ source** for: Australian dealer share by car age, and repurchase probability by satisfaction band (any market).

## Rows in / out
n/a. No feedback data was read or moved. `monthly_revenue.csv` was summed in full (288 rows = 24 dealers × 12 months).

## Sources
14 sources, listed as [S1]–[S14] at the end of benchmarks.md. By weight:
- **High:** Deloitte Australia 2025/2026 benchmarks, AADA Dealernomics 2026, Mittal & Kamakura (2001, JMR, peer-reviewed).
- **Medium:** J.D. Power (AU 2012/2013, UK 2016, US 2009), Cox Automotive 2025 study, AAAA 2018, NADA 2024.
- **Low:** J.D. Power 2016 AADA presentation (press report only), Cox's "US$12,000 lifetime service spend" claim, and AAAA values read off a chart.
- **Do not use:** "acquisition costs 5–25× retention". The primary source could not be found, and the cited Bain page does not contain it.

## Assumptions
- Mid values for the retention gap (50 pts) and service visits (1.7/yr) are **arithmetic midpoints**, labelled as such in the tables. They are not sourced.
- Kestrel is treated as a "volume" dealer group for Deloitte figures. Brands are fictional with no segment (benchmarks.md A6).
- A low of 1 service visit a year and a low retention of 3 years are assumptions (A3, A4), not sourced figures.
- The full list is benchmarks.md §6 (A1–A10). A1, A2, A3, A5 and A10 are flagged as shaky.

## Checks I ran
- Every figure in benchmarks.md was taken from a fetched page, not from memory. Where the fetched text was ambiguous, the figure was dropped or downgraded:
  - Cox's "74% / 44% likely to repurchase" chart labels were ambiguous, so the figures were dropped.
  - Cox's visits-per-year chart was unlabelled, so it is weighted Low.
  - The AAAA dealer-share-by-age values were read from a chart, so they are weighted Medium with that caveat.
- **Citation discrepancy:** the citedrive page dates Mittal & Kamakura to 2003. The DOI (jmkr.38.1) and the reference list in Aksoy et al. both give *JMR* 38(1), February 2001. 2001 is used.
- Arithmetic in §5 was checked in Python.
- **Not independently verified.** Under D-017 the producer should not grade its own work. The owner (or a separate agent) should open the sources for the five load-bearing figures:
  (v2 numbering)
  1. R4: Qualtrics auto dealers, 23% stop / 38% decrease [S5, PDF chart "Cut Spending After Bad Experiences by Industry"]
  2. R7: J.D. Power 2025, 50% returned after a repair that wasn't fixed [S7]
  3. S-1: Mittal et al. 2023, r = 0.60 / 0.21 / 0.65 [S16, Table 3 and §4.2.4]
  4. C4: Deloitte service GP 63–65% [S3]
  5. C7: Deloitte new-vehicle GP A$4,250–4,750 [S3]

## Unresolved / not found
- Australian service visits per customer per year.
- Australian average repair-order value. Kestrel's own A$415.53 per job is used instead.
- Australian ownership length, and the rate of repurchase from the same dealer.
- A credible acquisition cost for a *service* customer. Only advertising per vehicle sold was found.
- Any published mapping from a 1–5 rating (or any rating) to a dollar value. **None exists.** This is reported as a finding in benchmarks.md §4.
- Recent (post-2016) Australian J.D. Power service-loyalty figures. Not found in accessible sources. J.D. Power does not appear to publish an Australian CSI any more.
- Qualtrics' 2026 bad-experiences report (fieldwork 2025) is behind a download form, so the 2025 study (fieldwork Q3 2024) is used.
- HBR (Gallo 2014) could not be fetched (blocked), so the 5–25× claim is unverified.

## Done-when criteria
- [x] reports/benchmarks.md holds low/mid/high ranges for items 1–3
- [x] Every number carries a citation, year, market and weight
- [x] Item 4 states plainly whether a rating can be linked to dollars (it cannot directly)
- [x] Assumptions listed, shaky ones flagged
- [x] Unsourceable figures reported as "not found"
- [ ] Owner spot-checks the 5 load-bearing figures *(owner)*
- [x] Report written to agents/reports/w1_research.md

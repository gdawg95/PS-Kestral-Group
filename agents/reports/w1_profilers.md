# Report: w1_profilers
**Brief:** agents/briefs/w1_profilers.md (approved 29 Oct 2026) · **Branch:** `w1-profilers` · **Ran in:** cloud workspace

## What I did
- Wrote `scripts/profile_file.py` and ran it on all 52 feedback files (about 5 seconds).
  The planned 4-way split was unnecessary at that speed, so it ran as one job.
- Pilot (G1) on 4 awkward files, checked by the owner: 43/43 lines confirmed
  (`agents/reports/w1_profilers_pilot_review.md`). Chermside Q1 FINAL v2 adopted (D-027).
- Outputs: 52 profile JSONs, `_index.csv` (one row per file), `_overlaps.json` (files sharing rows),
  `_review.md` (readable checklist for spot-checks).

## Files in / profiles out
- 52 data files in, 52 profiles out. The owner's folder shows 54 because of two Excel lock files
  (`~$Parramatta_Feedback_2026-01.xlsx`, `~$Tamworth.xlsx`), which the profiler skips.
- 7,161 data rows excluding Chermside Q1 FINAL (7,273 including it).

## Privacy checks
- Comment, identifier, name, contact and vehicle columns: values withheld in every profile (0 exceptions).
- Pattern scan of all profiles for emails, mobiles and +61 numbers: no matches.
- Cross-check of 2,674 capitalised tokens from raw name/contact/staff columns against the profiles:
  only generic words matched (Service, Escalated, Hunter, ...). No person names.
- **Fixed during the run:** staff-name columns ("Taken by", "Logged by", "Card given by", Ringwood's
  unnamed staff column, Southport "Reviewer") were initially listed. The rule now withholds any column
  whose header suggests a person or whose values are mostly first names.

## Script fixes made after the pilot
1. **Second header rows.** Ringwood Q1 (row 37) and Frankston (row 160) change layout mid-sheet. Sheets
   are now split at repeated headers and each layout is profiled separately.
2. **Two-row headers.** Ballarat has merged group labels above the real header (row 2).
3. **Formats.** Added `2 Oct 25` dates (Bendigo) and comment headers such as "What did they say?".

## Findings that need an owner decision
Each has a proposed default. Decisions go into DECISIONS.md before Wave 2.

| # | File(s) | Finding | Proposed default |
|---|---|---|---|
| 1 | Toowoomba Q4 2025 summary | **No row-level data**: only a pivot of counts per month × department × rating (71 responses, no comments, no days) | Expand the counts into 71 rows dated mid-month, `comment` empty, flagged `from_summary=true`; include in score trends, excluded from NLP |
| 2 | liverpool_q3_2026.csv | **US date format (mm/dd/yyyy)**: 56 values only parse as month-first; read day-first, 6 land outside the quarter | Parse this file month-first; check every date falls in Jul–Sep 2026 |
| 3 | Shepparton (site closed 31 Mar 2026) | 6 dates in Oct–Dec **2026**, after closure; one note row ("Site closed 31/3/26 ...") | Treat as year typos (→ 2025), flag `date_corrected=true`; drop the note row |
| 4 | IPS_feedback_log | 10 vague dates ("early Oct", "wk1 Feb", "mid Nov") | Assign to the 1st/8th/15th/22nd/29th of the month (year from neighbouring rows), flag `date_approx=true` |
| 5 | Southport | Test rows ("asdf", "TEST", a 01/01/1900 date); a second sheet of 8 copied Google reviews with relative dates and no department | Drop the 3 test rows; exclude the Google reviews sheet (different source, no date or department) |
| 6 | North QLD (Rocky + TSV) | Two sites in one file, each spelled 3 ways (Rockhampton/Rocky/ROK, Townsville/TSV/Tsv) | Split by site into two dealer codes using the Site column |
| 7 | Ringwood Q1 2026, Q2, Q3 | Scale changes from 1–5 to **out of 10** from February 2026 (new template) | Keep both; map to a common scale in Wave 3 (D-020) |
| 8 | Bendigo, Tamworth, Ballarat | Non-numeric scales: stars (★★★★☆), Good/OK/Bad, Very satisfied ... Very dissatisfied | Map in Wave 3 (D-020): stars → 1–5; 5-point words → 1–5; Good/OK/Bad → 3-point (kept separate or mapped to 5/3/1) |
| 9 | Essendon | Department is the **sheet name** (Sales / Service / Parts), not a column | Use the sheet name as department |
| 10 | Frankston | 12 monthly "Total ..." rows and blank separators inside the data | Drop rows whose date cell starts with "Total" |
| 11 | Dandenong | 12 monthly sheets with 3 title rows each, plus an empty `Sheet3` | Header at row 4 of each sheet; ignore `Sheet3` |
| 12 | Many sites | Department written ~20 ways (Svc, SV, Workshop, P&A, parts counter, New Cars, Used Cars, Sales - New ...) | Map in Wave 3 to Service / Sales / Parts; New/Used Cars → Sales |
| 13 | Several | Extra free-text columns ("Action", "Action taken", "Followed up?") | Drop (allowlist, D-003) |

## Assumptions
- The data period is 1 Oct 2025 – 30 Sep 2026; dates outside it are suspect.
- Day-first dates everywhere except liverpool_q3 (all other `dd/mm` files fit their quarter).
- A header row is the first row (in the top 20) with mostly short text cells followed by data.

## Unresolved
- Whether Good/OK/Bad (Tamworth) should be stretched to 1–5 or analysed as 3-point (D-020).
- Penrith "Sales - New / Sales - Used": one Sales department, or keep the split?

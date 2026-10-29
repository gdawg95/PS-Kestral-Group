# Owner spot-check of 3 profiles (Checkpoint 1)

Checked by owner (gdawg95), 29 Oct 2026, against the spreadsheets. `[y]` = confirmed.
Tamworth was checked twice: the first check found the false layout split (fixed in fb3b9b3); this is the re-check.

## bendigo feedback.csv

- [y] CSV separated by `,`
- [y] 144 data rows in total
- [y] Sheet **csv**: header in row 1, **144 data rows**
    - [y] `Date` → date; 0.0% empty; dates 2025-10-02 to 2026-09-30
    - [y] `Dept` → department; 0.0% empty; values: SV (97), S (32), P (15)
    - [y] `Stars` → rating; 0.0% empty; values: ★★★★★ (60), ★★★★☆ (41), ★☆☆☆☆ (20), ★★★☆☆ (14), ★★☆☆☆ (9)
    - [y] `What did they say?` → comment; 28.5% empty

## Frankston_CX_tracker.xlsx

- [y] 308 data rows in total
- [y] Sheet **Tracker [layout 1, from row 1]**: header in row 1, **145 data rows**
    - [y] `Date` → date; 0.0% empty; dates 2025-10-01 to 2026-03-30
    - [y] `Area` → department; 0.0% empty; values: service (24), Service Dept (18), Workshop (15), Sales (15), SERVICE (15), Svc (14), Service (13), sales (9), New Cars (5), Used Cars (4), P&A (4), Parts (4), Parts & Accessories (4), parts counter (1)
    - [y] `Rating` → rating; 0.0% empty; values: 5 (67), 4 (24), 3 (19), 1 (18), 2 (17)
    - [y] `Comments` → comment; 25.5% empty
- [y] Sheet **Tracker [layout 2, from row 160]**: header in row 160, **163 data rows**
    - [y] `Date` → date; 0.0% empty; dates 2026-04-01 to 2026-09-29
    - [y] `Area` → department; 0.0% empty; values: Workshop (26), Service (19), Svc (18), Service Dept (17), SERVICE (17), service (15), Sales (11), Used Cars (10), parts counter (8), sales (8), New Cars (5), P&A (4), Parts (3), Parts & Accessories (2)
    - [y] `CSAT` → rating; 0.0% empty; values: 5 (72), 4 (41), 1 (21), 2 (16), 3 (13)
    - [y] `Customer comments` → comment; 23.3% empty
    - [y] `Source` → other; 0.0% empty
    - [y] `Customer` → name; 0.0% empty
    - [y] `Rego` → vehicle; 16.6% empty
- Oddities: [Tracker [layout 1, from row 1]] 5 blank row(s) inside the data; [Tracker [layout 1, from row 1]] 6 summary/notes-like row(s) (e.g. Total, Average, Note); [Tracker [layout 1, from row 1]] 3 empty column(s); [Tracker [layout 2, from row 160]] second header row: column layout changes from here; [Tracker [layout 2, from row 160]] 5 blank row(s) inside the data; [Tracker [layout 2, from row 160]] 6 summary/notes-like row(s) (e.g. Total, Average, Note)

## Tamworth.xlsx

- [y] 143 data rows in total
- [y] Sheet **Sheet1**: header in row 1, **143 data rows**
    - [y] `DATE` → date; 0.0% empty; dates 2025-10-02 to 2026-09-30
    - [y] `DEPT` → department; 0.0% empty; values: Svc (20), Workshop (18), SERVICE (18), Service Dept (18), Service (17), service (13), New Cars (10), Used Cars (9), Sales (9), sales (6), Parts & Accessories (2), P&A (2), parts counter (1)
    - [y] `HOW WAS IT` → rating; 7.0% empty; values: Good (93), Bad (21), OK (19)
    - [y] `COMMENTS` → comment; 28.7% empty


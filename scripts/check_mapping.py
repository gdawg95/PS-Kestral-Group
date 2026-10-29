"""Cross-check mappings/columns.yaml against the Wave 1 profiles.

Checks, for the owner's Checkpoint 2 review:
  1. every file in data/raw/feedback is in the mapping (and vice versa)
  2. every sheet in each profile is in the mapping (and vice versa)
  3. every source column is accounted for: columns + dropped + staff_columns
  4. header_row and expected_rows agree with the profile
  5. the role set is exactly what src/pii.py accepts
  6. dealer codes exist in dealerships.csv
"""

import csv
import glob
import json
import os

import yaml

ROLES = {"date", "department", "rating", "comment", "redact_name", "redact_rego"}
RAW = "data/raw/feedback"

m = yaml.safe_load(open("mappings/columns.yaml", encoding="utf-8"))
layouts, files = m["layouts"], m["files"]

profiles = {}
for fp in glob.glob("reports/profiles/*.json"):
    if "_overlaps" in fp:
        continue
    p = json.load(open(fp, encoding="utf-8"))
    profiles[p["file"]] = p

on_disk = {f for f in os.listdir(RAW) if not f.startswith("~$")}
with open("data/raw/reference/dealerships.csv", encoding="utf-8") as fh:
    codes = {r["dealer_code"] for r in csv.DictReader(fh)}

problems = []


def note(msg):
    problems.append(msg)


# 1. file coverage
if on_disk - set(files):
    note(f"files on disk but not in the mapping: {sorted(on_disk - set(files))}")
if set(files) - on_disk:
    note(f"files in the mapping but not on disk: {sorted(set(files) - on_disk)}")
if set(files) - set(profiles):
    note(f"files in the mapping with no profile: {sorted(set(files) - set(profiles))}")

# 5/6. roles and dealer codes
for name, lay in layouts.items():
    bad = set((lay.get("columns") or {}).values()) - ROLES
    if bad:
        note(f"layout {name}: roles not accepted by src/pii.py: {sorted(bad)}")
    roles = list((lay.get("columns") or {}).values())
    for r in ("date", "rating", "comment", "department"):
        if roles.count(r) > 1:
            note(f"layout {name}: role {r} mapped more than once")

total_expected = 0
for fname, spec in files.items():
    code = spec.get("dealer_code")
    if code not in codes and code != "split_by_site":
        note(f"{fname}: dealer_code {code!r} is not in dealerships.csv")
    if spec.get("skip"):
        continue
    prof = profiles.get(fname)
    if prof is None:
        continue

    total_expected += spec.get("expected_rows") or 0
    prof_sheets = {s.get("name"): s for s in prof["sheets"]}
    map_sheets = spec.get("sheets") or {}

    # 2. sheet coverage
    if set(prof_sheets) != set(map_sheets):
        note(
            f"{fname}: sheet mismatch\n"
            f"      profile: {sorted(map(str, prof_sheets))}\n"
            f"      mapping: {sorted(map(str, map_sheets))}"
        )
        continue

    # 4. row count
    if spec.get("expected_rows") != prof.get("data_rows_total"):
        note(
            f"{fname}: expected_rows {spec.get('expected_rows')} "
            f"!= profile {prof.get('data_rows_total')}"
        )

    for sheet_name, ref in map_sheets.items():
        sh = prof_sheets[sheet_name]
        if isinstance(ref, dict):  # skipped sheet
            continue
        lay = layouts.get(ref)
        if lay is None:
            note(f"{fname} [{sheet_name}]: unknown layout {ref!r}")
            continue
        if lay.get("header_row") != sh.get("header_row"):
            note(
                f"{fname} [{sheet_name}]: header_row {lay.get('header_row')} "
                f"!= profile {sh.get('header_row')} (layout {ref})"
            )

        # 3. column accounting
        src_cols = [str(c["name"]) for c in sh.get("columns", [])]
        accounted = (
            set(map(str, (lay.get("columns") or {})))
            | set(map(str, lay.get("dropped") or []))
            | set(map(str, lay.get("staff_columns") or []))
            | set(map(str, ((lay.get("expand_pivot") or {}).get("count_columns") or [])))
        )
        if lay.get("site_column"):
            accounted |= {str(lay["site_column"])}
        pivot = lay.get("expand_pivot") or {}
        if pivot:
            accounted |= {str(pivot.get("month_column")), str(pivot.get("department_column"))}
        unnamed_ok = lay.get("unnamed_columns") == "drop"
        missing = [
            c for c in src_cols
            if c not in accounted and not (unnamed_ok and (c.startswith("Unnamed") or c == "nan"))
        ]
        extra = [c for c in accounted if c not in src_cols]
        if missing:
            note(
                f"{fname} [{sheet_name}] layout {ref}: "
                f"source columns not accounted for: {missing}"
            )
        if extra:
            note(
                f"{fname} [{sheet_name}] layout {ref}: "
                f"mapped columns not in the source: {sorted(extra)}"
            )

print(f"files on disk: {len(on_disk)} | in mapping: {len(files)} | layouts: {len(layouts)}")
print(f"sum of expected_rows (non-skipped files): {total_expected}")
print()
if problems:
    print(f"{len(problems)} PROBLEM(S):")
    for p in problems:
        print("  -", p)
else:
    print("OK: mapping and profiles agree on every file, sheet, header row, row count and column.")

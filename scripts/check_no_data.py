"""Pre-commit guardrail: refuse to commit raw or interim data files.

Checkpoint 1 requires that `git add -f data/raw/test.xlsx` followed by a commit is
refused even though .gitignore already covers the plain `git add` path (DECISIONS.md
D-015: git history cannot be cleaned easily later, so nothing data-shaped ever enters it).

Allowed exceptions:
  mappings/      human-approved column map (D-003), no data values
  reports/       profiles and reconciliation tables, written under the privacy rule
  tests/         small synthetic fixtures, never real feedback rows
  data/llm_cache/  de-identified model outputs, committed on purpose (PLAN.md section 6)

Usage: check_no_data.py [staged file ...]   (pre-commit passes the file list)
Exit 1 and name every offending path, so one commit attempt reports every problem.
"""

import sys
from pathlib import PurePosixPath

DATA_SUFFIXES = {
    ".xlsx", ".xlsm", ".xltx", ".xls", ".csv", ".tsv",
    ".parquet", ".feather", ".pkl", ".pickle", ".db", ".sqlite", ".duckdb",
}

ALLOWED_PREFIXES = ("mappings/", "reports/", "tests/", "data/llm_cache/")


def offending(paths: list[str]) -> list[tuple[str, str]]:
    problems = []
    for raw in paths:
        p = PurePosixPath(raw.replace("\\", "/"))
        path = str(p)
        if path.startswith(ALLOWED_PREFIXES):
            continue
        if path.startswith("data/"):
            problems.append(
                (path, "anything under data/ except data/llm_cache/ is raw or interim data")
            )
        elif p.suffix.lower() in DATA_SUFFIXES:
            allowed = ", ".join(ALLOWED_PREFIXES)
            problems.append((path, f"{p.suffix} is a data file; allowed only under {allowed}"))
    return problems


def main(argv: list[str]) -> int:
    problems = offending(argv[1:])
    if not problems:
        return 0
    print("Refusing to commit: data files must never enter git history (D-015).")
    for path, why in problems:
        print(f"  {path}\n      {why}")
    print("\nIf this file really belongs in the repo, move it under mappings/ or reports/")
    print("and make sure it holds no customer data.")
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))

"""Wave 3: apply the data-quality rules, fill `department`, write the clean dataset.

Brief: `agents/briefs/w3_validate.md` (approved at gate G2, 29 Oct 2026).

What this module is for: after it runs, Waves 4 and 5 stop asking whether the data is
trustworthy. Every rule is declared once, classified the way PLAN.md section 8 asks, and
counted - including the rules that fire zero times, because a rule that never fires is
evidence the condition was checked, not dead code.

    reject         the row cannot be used and leaves the dataset, with its reason counted
    fix-and-flag   the value is repaired, the row stays, the repair is counted
    flag-and-keep  the row is fine but carries a caveat downstream (the ingestion flags)

The structural rules are a pandera schema over the 15 columns of `src/schema.py`. Three
rules cannot be expressed as a column check and are applied in code: the department fill
(`mappings/departments.yaml`, D-050), the double-entry duplicates (D-047), and the empty
comment repair.

Inputs are read, never written: `data/interim/consolidated.parquet` belongs to Wave 2.

Usage:
    python -m src.validate                               # all 7,159 rows
    python -m src.validate --dealers VIC09 QLD03 QLD06   # the pilot (gate G1)
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import sys
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd
import pandera.pandas as pa
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src import schema  # noqa: E402

IN_PARQUET = ROOT / "data" / "interim" / "consolidated.parquet"
DEPARTMENTS = ROOT / "mappings" / "departments.yaml"
DEALERSHIPS = ROOT / "data" / "raw" / "reference" / "dealerships.csv"
OUT_PARQUET = ROOT / "data" / "clean" / "feedback.parquet"
DQ_REPORT = ROOT / "reports" / "data_quality.md"

REJECT, FIX, KEEP = "reject", "fix-and-flag", "flag-and-keep"

# Lineage plus the kept columns - never comment text. The redaction is proven (D-051) but
# `reports/` is the part of the repo a reviewer reads, so no comment is reproduced there at
# all; a character count stands in for the text.
EXAMPLE_COLUMNS = [
    "feedback_id", "dealer_code", "feedback_date", "department_raw", "department",
    "rating_raw", "rating_scale", "rating_1to5", "comment_chars",
    "source_file", "source_sheet", "source_row",
]


@dataclass
class Rule:
    """One data-quality rule, its class, the rows it caught and what it did.

    `test` returns a boolean mask of the rows that FAIL the rule, so a rule's count is
    computed from the data every run and can never be a zero that only means "nobody
    looked". The pandera schema below carries the same conditions as the structural
    contract; the masks are what the waterfall counts, because pandera reports the kind of
    check that failed (`isin`, `str_matches`) rather than the name given to it, which is
    not enough to attribute a failure to a rule.
    """

    key: str
    kind: str
    what: str
    decisions: str
    test: Callable[[pd.DataFrame], pd.Series] | None = None
    count: int = 0
    examples: list[int] = field(default_factory=list)   # dataset index, not spreadsheet row

    @property
    def fired(self) -> bool:
        return self.count > 0

    def apply(self, df: pd.DataFrame) -> list[int]:
        """Count the rows this rule catches and remember the first five."""
        if self.test is None:
            return []
        mask = self.test(df).fillna(False).astype(bool)
        idx = [int(i) for i in df.index[mask]]
        self.count = len(idx)
        self.examples = idx[:5]
        return idx


# --------------------------------------------------------------- the rule declarations


def declare_rules(dealer_codes_: set[str] | None = None) -> dict[str, Rule]:
    """Every rule this module applies, in the order the waterfall reports them."""
    codes = dealer_codes_ if dealer_codes_ is not None else dealer_codes()
    date_min, date_max = pd.Timestamp(schema.DATE_MIN), pd.Timestamp(schema.DATE_MAX)

    rules = [
        # --- reject: the row leaves the dataset ---------------------------------------
        Rule("dealer_code_known", REJECT,
             "dealer_code is one of the 24 codes in dealerships.csv", "D-034, D-042",
             lambda df: ~df["dealer_code"].isin(codes)),
        Rule("date_in_window", REJECT,
             "feedback_date falls inside Oct 2025 - Sep 2026", "D-032 #3, D-040",
             lambda df: df["feedback_date"].isna()
             | (df["feedback_date"] < date_min) | (df["feedback_date"] > date_max)),
        Rule("rating_in_1_to_5", REJECT,
             "rating_1to5 is a whole number from 1 to 5", "D-020, D-030, D-031",
             lambda df: ~pd.to_numeric(df["rating_1to5"], errors="coerce").isin([1, 2, 3, 4, 5])),
        Rule("department_raw_present", REJECT,
             "department_raw is non-empty", "D-035",
             lambda df: df["department_raw"].isna()
             | (df["department_raw"].astype("string").str.len() == 0)),
        Rule("feedback_id_well_formed", REJECT,
             "feedback_id matches F000000", "D-003",
             lambda df: ~df["feedback_id"].astype("string").str.fullmatch(r"F\d{6}").fillna(False)),
        Rule("feedback_id_unique", REJECT,
             "feedback_id appears once across the dataset", "D-003",
             lambda df: df["feedback_id"].duplicated(keep="first")),
        Rule("summary_rows_have_no_comment", REJECT,
             "a row expanded from a pivot carries no comment", "D-032 #1, D-038",
             lambda df: df["from_summary"].fillna(False).astype(bool) & df["comment"].notna()),
        # Index-based, not a row predicate: it needs the whole group. Applied in validate().
        Rule("double_entry_duplicate", REJECT,
             "the same comment, dealer, date, department and rating on consecutive "
             "spreadsheet rows - one piece of feedback saved twice", "D-047"),
        # --- fix-and-flag: the value is repaired, the row stays ------------------------
        Rule("empty_comment_to_null", FIX,
             'a comment of "" becomes null, so "no comment" is one thing and not two',
             "D-003"),
        Rule("department_filled", FIX,
             "department filled from departments.yaml; a null survivor is a failure",
             "D-048, D-049, D-050"),
        # --- flag-and-keep: the row is usable, with a caveat --------------------------
        Rule("date_corrected", KEEP,
             "the source year was a typo and was corrected at ingestion", "D-032 #3",
             lambda df: df["date_corrected"].fillna(False).astype(bool)),
        Rule("date_approx", KEEP,
             "the source date was vague and was resolved to a day", "D-040",
             lambda df: df["date_approx"].fillna(False).astype(bool)),
        Rule("from_summary", KEEP,
             "the row came from a pivot of counts: usable for scores, not for NLP",
             "D-032 #1, D-038",
             lambda df: df["from_summary"].fillna(False).astype(bool)),
    ]
    return {r.key: r for r in rules}


# ------------------------------------------------------------------- pandera structure


def build_schema(dealer_codes_: set[str]) -> pa.DataFrameSchema:
    """The structural contract. Check names match the rule keys in declare_rules()."""
    return pa.DataFrameSchema(
        columns={
            "feedback_id": pa.Column(
                str,
                checks=pa.Check.str_matches(r"^F\d{6}$", name="feedback_id_well_formed"),
                unique=True,
                nullable=False,
            ),
            "dealer_code": pa.Column(
                str,
                checks=pa.Check.isin(sorted(dealer_codes_), name="dealer_code_known"),
                nullable=False,
            ),
            "feedback_date": pa.Column(
                "datetime64[ns]",
                checks=pa.Check.in_range(
                    pd.Timestamp(schema.DATE_MIN), pd.Timestamp(schema.DATE_MAX),
                    name="date_in_window",
                ),
                nullable=False,
            ),
            "department_raw": pa.Column(
                str,
                checks=pa.Check.str_length(min_value=1, name="department_raw_present"),
                nullable=False,
            ),
            "department": pa.Column(
                str,
                checks=pa.Check.isin(["Service", "Sales", "Parts"], name="department_filled"),
                nullable=False,
            ),
            "rating_raw": pa.Column(str, nullable=False),
            "rating_scale": pa.Column(
                str, checks=pa.Check.isin(list(schema.RatingScale.__args__)), nullable=False
            ),
            # The widths come from schema.DTYPES so this file and the Wave 2 contract
            # cannot drift apart: int8 ratings, int32 source rows.
            "rating_1to5": pa.Column(
                schema.DTYPES["rating_1to5"],
                checks=pa.Check.isin([1, 2, 3, 4, 5], name="rating_in_1_to_5"),
                nullable=False,
            ),
            "comment": pa.Column(
                str,
                checks=pa.Check(
                    lambda s: s.str.len() > 0, name="empty_comment_to_null",
                    error='comment is "" rather than null',
                ),
                nullable=True,
            ),
            "source_file": pa.Column(str, nullable=False),
            "source_sheet": pa.Column(str, nullable=True),
            "source_row": pa.Column(schema.DTYPES["source_row"], nullable=False),
            "from_summary": pa.Column(bool, nullable=False),
            "date_corrected": pa.Column(bool, nullable=False),
            "date_approx": pa.Column(bool, nullable=False),
        },
        checks=[
            pa.Check(
                lambda df: ~(df["from_summary"] & df["comment"].notna()),
                name="summary_rows_have_no_comment",
                error="a summary-expanded row carries a comment (D-032 #1 says none)",
            ),
        ],
        strict=True,     # nothing outside the allowlist (D-003)
        ordered=True,
        coerce=False,
        name="feedback_clean",
    )


def failures_by_check(df: pd.DataFrame, pa_schema: pa.DataFrameSchema) -> dict[str, list[int]]:
    """Run the schema and return {check name: [failing dataset index, ...]}."""
    try:
        pa_schema.validate(df, lazy=True)
        return {}
    except pa.errors.SchemaErrors as err:
        out: dict[str, list[int]] = {}
        for check, grp in err.failure_cases.groupby("check"):
            name = str(check).split("(")[0].strip()
            idx = [int(i) for i in grp["index"].dropna().unique()]
            out.setdefault(name, []).extend(idx)
        return out


# ------------------------------------------------------------------------- the rules


def load_departments() -> dict[str, str]:
    """department_raw -> Service / Sales / Parts, from the owner-approved mapping (D-050)."""
    doc = yaml.safe_load(DEPARTMENTS.read_text(encoding="utf-8"))
    if not str(doc.get("status", "")).startswith("approved"):
        raise ValueError(
            f"mappings/departments.yaml is {doc.get('status')!r}, not approved - "
            "gate G3 blocks the department fill until the owner signs it off"
        )
    return {raw: spec["to"] for raw, spec in doc["mapping"].items()}


def dealer_codes() -> set[str]:
    with DEALERSHIPS.open(encoding="utf-8") as fh:
        return {r["dealer_code"] for r in csv.DictReader(fh)}


def fix_empty_comments(df: pd.DataFrame, rule: Rule) -> pd.DataFrame:
    """A comment of "" is neither a comment nor an absence; make it an absence."""
    empty = df["comment"].notna() & (df["comment"].astype("string").str.len() == 0)
    rule.count = int(empty.sum())
    rule.examples = [int(i) for i in df.index[empty][:5]]
    if rule.count:
        df = df.copy()
        df.loc[empty, "comment"] = pd.NA
    return df


def fill_department(df: pd.DataFrame, mapping: dict[str, str], rule: Rule) -> pd.DataFrame:
    """Fill `department` from the approved mapping. A null survivor is a failure (step 2)."""
    df = df.copy()
    df["department"] = df["department_raw"].map(mapping).astype("string")
    missing = df["department"].isna()
    if missing.any():
        unmapped = sorted(df.loc[missing, "department_raw"].unique())
        raise ValueError(
            f"{int(missing.sum())} rows have no department after the fill; "
            f"department_raw values not in departments.yaml: {unmapped}"
        )
    rule.count = len(df)
    rule.examples = [int(i) for i in df.index[:5]]
    return df


def double_entry_duplicates(df: pd.DataFrame) -> list[int]:
    """Indices to drop: the second and later rows of a double-entered group (D-047).

    A group qualifies only if it shares dealer, date, department, rating **and** comment
    text, the comment is not null, and the rows sit on consecutive spreadsheet rows. The
    adjacency requirement is what separates double entry from two customers who honestly
    gave the same score on the same day: of the comment-less groups only 60% are adjacent,
    against 9 of 9 for the groups this rule catches.
    """
    keys = ["dealer_code", "feedback_date", "department_raw", "rating_1to5", "comment"]
    commented = df[df["comment"].notna()]
    drop: list[int] = []
    for _key, grp in commented.groupby(keys, dropna=False, sort=False):
        if len(grp) < 2:
            continue
        grp = grp.sort_values("source_row")
        rows = grp["source_row"].tolist()
        if all(b - a == 1 for a, b in zip(rows, rows[1:], strict=False)):
            drop.extend(int(i) for i in grp.index[1:])
    return sorted(drop)


def duplicate_pairs_table(df: pd.DataFrame, dropped: list[int]) -> pd.DataFrame:
    """The pairs behind the rule, for the report and for Checkpoint 3."""
    rows = []
    for i in dropped:
        kept = df[
            (df["dealer_code"] == df.at[i, "dealer_code"])
            & (df["feedback_date"] == df.at[i, "feedback_date"])
            & (df["department_raw"] == df.at[i, "department_raw"])
            & (df["rating_1to5"] == df.at[i, "rating_1to5"])
            & (df["comment"] == df.at[i, "comment"])
            & (df["source_row"] == df.at[i, "source_row"] - 1)
        ]
        rows.append(
            {
                "dealer_code": df.at[i, "dealer_code"],
                "source_file": df.at[i, "source_file"],
                "kept_row": int(kept["source_row"].iloc[0]) if len(kept) else None,
                "dropped_row": int(df.at[i, "source_row"]),
                "feedback_date": df.at[i, "feedback_date"].date(),
                "department_raw": df.at[i, "department_raw"],
                "rating_1to5": int(df.at[i, "rating_1to5"]),
                "comment_chars": len(df.at[i, "comment"]),
            }
        )
    if not rows:
        return pd.DataFrame()
    return pd.DataFrame(rows).sort_values(["dealer_code", "dropped_row"])


def date_edge_cases(df: pd.DataFrame) -> pd.DataFrame:
    """The 16 rows Checkpoint 3 asks to see: corrected years and resolved vague dates."""
    flagged = df[df["date_corrected"] | df["date_approx"]]
    out = flagged[[
        "feedback_id", "dealer_code", "source_file", "source_sheet", "source_row",
        "feedback_date", "date_corrected", "date_approx",
    ]].copy()
    out["why"] = [
        "source year was after the site closed; read as a year typo (D-032 #3)"
        if corrected else
        'source date was vague ("early Oct", "wk1 Feb"); resolved from the rows '
        "around it (D-040)"
        for corrected in out["date_corrected"]
    ]
    return out.sort_values(["dealer_code", "source_row"])


# --------------------------------------------------------------------------- the run


def validate(dealers: set[str] | None = None) -> tuple[pd.DataFrame, dict[str, Rule], dict]:
    """Apply every rule. Returns (clean frame, rules with counts, extras for the report)."""
    df = pd.read_parquet(IN_PARQUET)
    if dealers:
        df = df[df["dealer_code"].isin(dealers)].copy()
    df = df.reset_index(drop=True)

    rows_in = len(df)
    codes = dealer_codes()
    rules = declare_rules(codes)
    depts = load_departments()

    # 1. fix-and-flag, before anything is judged on a value that is about to change
    df = fix_empty_comments(df, rules["empty_comment_to_null"])

    # 2. the department fill (step 2 of the brief)
    df = fill_department(df, depts, rules["department_filled"])

    # 3. every row-level rule, counted from its own mask
    reject_idx: set[int] = set()
    for rule in rules.values():
        idx = rule.apply(df)
        if rule.kind == REJECT:
            reject_idx.update(idx)

    # 4. the duplicates rule, which needs the whole group rather than a row (D-047)
    dup_idx = double_entry_duplicates(df)
    rules["double_entry_duplicate"].count = len(dup_idx)
    rules["double_entry_duplicate"].examples = dup_idx[:5]
    pairs = duplicate_pairs_table(df, dup_idx)
    reject_idx.update(dup_idx)

    # 5. the structural contract: dtypes, column allowlist and order, over the 15 columns.
    #    Anything here is a Wave 2 contract breach, not a row to drop (gate G3).
    structure = failures_by_check(df, build_schema(codes))

    edges = date_edge_cases(df)
    clean = df.drop(index=sorted(reject_idx)).reset_index(drop=True)

    # 6. the clean frame must pass the same schema with nothing left to reject
    residual = failures_by_check(clean, build_schema(codes))
    extras = {
        "rows_in": rows_in,
        "rejected": len(reject_idx),
        "rows_out": len(clean),
        "pairs": pairs,
        "edges": edges,
        "residual": residual,
        "structure": structure,
        "dept_totals": clean["department"].value_counts().to_dict(),
        "dealers": dealers,
    }
    return clean, rules, extras


# ------------------------------------------------------------------------ the report


def _example_table(df: pd.DataFrame, idx: list[int]) -> list[str]:
    present = [i for i in idx if i in df.index]
    if not present:
        return ["_Rule did not fire, so there is nothing to show._", ""]
    sample = df.loc[present].copy()
    sample["comment_chars"] = sample["comment"].fillna("").astype(str).str.len()
    sample["feedback_date"] = pd.to_datetime(sample["feedback_date"]).dt.date
    cols = [c for c in EXAMPLE_COLUMNS if c in sample.columns]
    lines = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    for _, r in sample[cols].iterrows():
        lines.append("| " + " | ".join("" if pd.isna(v) else str(v) for v in r) + " |")
    lines.append("")
    return lines


def write_report(df: pd.DataFrame, clean: pd.DataFrame, rules: dict[str, Rule],
                 extras: dict) -> None:
    scope = (
        "pilot - " + ", ".join(sorted(extras["dealers"])) if extras["dealers"] else "all dealers"
    )
    rejected = sum(r.count for r in rules.values() if r.kind == REJECT)
    closes = extras["rows_in"] - rejected == extras["rows_out"]

    lines = [
        "# Data quality: every rule, its class and its count",
        "",
        f"**Run:** {dt.datetime.now():%Y-%m-%d %H:%M} · **Scope:** {scope} · "
        "`python -m src.validate`",
        "",
        "Generated by `src/validate.py` from `data/interim/consolidated.parquet`.",
        "Rules are classified as PLAN.md section 8 asks - reject, fix-and-flag, "
        "flag-and-keep - and every rule carries a count, **including the rules that fire "
        "zero times**: a rule that never fires is evidence the condition was checked.",
        "",
        "No comment text appears anywhere in this report. Example rows are lineage plus the "
        "kept columns, with a character count standing in for the text.",
        "",
        "## The waterfall",
        "",
        "| | Rows |",
        "|---|---:|",
        f"| Read from the consolidated dataset | {extras['rows_in']} |",
        f"| Rejected by a rule | -{rejected} |",
        f"| **Written to the clean dataset** | **{extras['rows_out']}** |",
        f"| **Arithmetic closes** | **{'YES' if closes else 'NO'}** |",
        "",
        "## Every rule",
        "",
        "| Rule | Class | Rows | What it checks | Decisions |",
        "|---|---|---:|---|---|",
    ]
    for r in rules.values():
        lines.append(f"| `{r.key}` | {r.kind} | {r.count} | {r.what} | {r.decisions} |")

    zero = [r.key for r in rules.values() if not r.fired]
    lines += [
        "",
        f"**{len(zero)} of {len(rules)} rules fired zero times**"
        + (f": `{'`, `'.join(zero)}`." if zero else ".")
        + " Each was still evaluated over every row.",
        "",
        "## Example rows, five per rule",
        "",
    ]
    for r in rules.values():
        lines += [f"### `{r.key}` - {r.kind}, {r.count} rows", "", r.what + ".", ""]
        lines += _example_table(df, r.examples)

    lines += [
        "## The double-entered pairs (D-047)",
        "",
        "Every one on consecutive spreadsheet rows. The first row of each pair is kept and "
        "the second dropped, as the owner decided at Checkpoint 3.",
        "",
    ]
    pairs = extras["pairs"]
    if len(pairs):
        lines += [
            "| Dealer | File | Kept row | Dropped row | Date | Department | Rating | Chars |",
            "|---|---|---:|---:|---|---|---:|---:|",
        ]
        for _, r in pairs.iterrows():
            lines.append(
                f"| {r.dealer_code} | {r.source_file} | {r.kept_row} | {r.dropped_row} | "
                f"{r.feedback_date} | {r.department_raw} | {r.rating_1to5} | {r.comment_chars} |"
            )
    else:
        lines.append("_No double-entered pairs in this scope._")

    lines += [
        "",
        "## Date edge cases for Checkpoint 3",
        "",
        "Every row whose date the pipeline had to change or invent - sixteen rows across the "
        "whole dataset, rather than twenty arbitrary ones.",
        "",
    ]
    edges = extras["edges"]
    if len(edges):
        lines += [
            "| Dealer | File | Sheet | Row | Resolved date | Flag | Why |",
            "|---|---|---|---:|---|---|---|",
        ]
        for _, r in edges.iterrows():
            flag = "date_corrected" if r.date_corrected else "date_approx"
            lines.append(
                f"| {r.dealer_code} | {r.source_file} | {r.source_sheet or ''} | "
                f"{r.source_row} | {pd.to_datetime(r.feedback_date).date()} | `{flag}` | "
                f"{r.why} |"
            )
    else:
        lines.append("_No corrected or approximate dates in this scope._")

    totals = extras["dept_totals"]
    lines += [
        "",
        "## Department fill (D-050)",
        "",
        "| Department | Rows |",
        "|---|---:|",
    ]
    for dept in ("Service", "Sales", "Parts"):
        lines.append(f"| {dept} | {totals.get(dept, 0)} |")
    lines += [
        f"| **Total** | **{sum(totals.values())}** |",
        "",
        f"Nulls after the fill: **{int(clean['department'].isna().sum())}** "
        "(any other number is a failure, not a gap).",
        "",
        "## Schema check on the clean dataset",
        "",
    ]
    if extras["structure"]:
        lines += [
            "The structural pass over the incoming dataset reported:",
            "",
        ]
        lines += [f"- `{k}`: {len(v)} rows" for k, v in extras["structure"].items()]
        lines.append("")
    if extras["residual"]:
        lines.append("**Problems remain:**")
        lines += [f"- `{k}`: {len(v)} rows" for k, v in extras["residual"].items()]
    else:
        lines.append(
            "No failures: the clean dataset passes the same pandera schema that produced the "
            "rejections above, with nothing left to reject."
        )
    lines.append("")

    DQ_REPORT.parent.mkdir(parents=True, exist_ok=True)
    DQ_REPORT.write_text("\n".join(lines), encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dealers", nargs="*", help="dealer codes to validate (default: all)")
    ap.add_argument("--out", default=str(OUT_PARQUET))
    args = ap.parse_args(argv)

    dealers = set(args.dealers) if args.dealers else None
    source = pd.read_parquet(IN_PARQUET)
    if dealers:
        source = source[source["dealer_code"].isin(dealers)]
    source = source.reset_index(drop=True)

    clean, rules, extras = validate(dealers)

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    clean.to_parquet(out, index=False)
    write_report(source, clean, rules, extras)

    print(f"{extras['rows_in']} rows in -> {extras['rows_out']} rows out "
          f"({extras['rejected']} rejected) -> {out}")
    print(f"data-quality report -> {DQ_REPORT.relative_to(ROOT)}")
    for r in rules.values():
        if r.fired:
            print(f"  {r.kind:<13} {r.key:<28} {r.count}")
    problems = schema.validate_frame(clean, dealer_codes())
    if problems or extras["residual"]:
        print("\nPROBLEMS:")
        for p in problems:
            print("  -", p)
        for k, v in extras["residual"].items():
            print(f"  - pandera {k}: {len(v)} rows")
        return 1
    print("schema: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

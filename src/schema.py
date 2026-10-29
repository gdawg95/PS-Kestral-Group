"""Canonical schema for the consolidated dataset (PLAN.md section 5).

One row = one piece of feedback (D-001). Only the four content columns survive from the
source files (D-003); everything else here is added by the pipeline — the new id, the
dealer code, lineage back to the spreadsheet, and the flags that record what ingestion
had to fix.

This module is the contract between Wave 2 (ingest) and everything downstream. Changing
it needs the owner's approval (gate G3).

`validate_frame` is a cheap structural gate run at the end of ingestion: right columns,
right types, values in range, and — the point of the allowlist — nothing extra. The
declarative data-quality rules (reject / fix-and-flag / flag-and-keep) are Wave 3's
pandera suite, not this file.
"""

from __future__ import annotations

import datetime as dt
import re
from typing import Literal

import pandas as pd
from pydantic import BaseModel, ConfigDict, Field, field_validator

DEALER_CODE = re.compile(r"^(VIC|NSW|QLD)\d{2}$")

Department = Literal["Service", "Sales", "Parts"]

RatingScale = Literal[
    "1-5",            # most sites
    "1-10",           # Ringwood, from the Feb 2026 template
    "words-5",        # Ballarat: Very dissatisfied .. Very satisfied
    "words-3",        # Tamworth: Bad / OK / Good
    "stars-5",        # Bendigo
    "1-5-reversed",   # Geelong 2025 sheet (D-030)
    "pivot-1-5",      # Toowoomba Q4 2025 summary (D-032 #1)
]

# The study window: Oct 2025 - Sep 2026 inclusive.
DATE_MIN = dt.date(2025, 10, 1)
DATE_MAX = dt.date(2026, 9, 30)


class FeedbackRecord(BaseModel):
    """One consolidated feedback row."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    feedback_id: str = Field(pattern=r"^F\d{6}$")
    dealer_code: str
    feedback_date: dt.date

    department_raw: str = Field(min_length=1)
    department: Department | None = None  # filled in Wave 3

    rating_raw: str = Field(min_length=1)
    rating_scale: RatingScale
    rating_1to5: int = Field(ge=1, le=5)

    comment: str | None = None  # redacted (D-026); None where the source had none

    source_file: str = Field(min_length=1)
    source_sheet: str | None = None
    source_row: int = Field(ge=0)

    from_summary: bool = False     # expanded from a pivot, no comment (D-032 #1)
    date_corrected: bool = False   # year typo fixed (D-032 #3)
    date_approx: bool = False      # vague source date resolved to a day (D-032 #4)

    @field_validator("dealer_code")
    @classmethod
    def _known_code_shape(cls, v: str) -> str:
        if not DEALER_CODE.match(v):
            raise ValueError(f"dealer_code {v!r} is not of the form VIC01 / NSW01 / QLD01")
        return v

    @field_validator("feedback_date")
    @classmethod
    def _in_window(cls, v: dt.date) -> dt.date:
        if not DATE_MIN <= v <= DATE_MAX:
            raise ValueError(f"feedback_date {v} is outside Oct 2025 - Sep 2026")
        return v


# Column order of data/interim/consolidated.parquet.
COLUMNS: tuple[str, ...] = tuple(FeedbackRecord.model_fields)

DTYPES: dict[str, str] = {
    "feedback_id": "string",
    "dealer_code": "string",
    "feedback_date": "datetime64[ns]",
    "department_raw": "string",
    "department": "string",
    "rating_raw": "string",
    "rating_scale": "string",
    "rating_1to5": "int8",
    "comment": "string",
    "source_file": "string",
    "source_sheet": "string",
    "source_row": "int32",
    "from_summary": "bool",
    "date_corrected": "bool",
    "date_approx": "bool",
}


def validate_frame(df: pd.DataFrame, dealer_codes: set[str] | None = None) -> list[str]:
    """Return a list of problems; empty means the frame matches the schema.

    dealer_codes: the official codes from data/raw/reference/dealerships.csv. Passing them
    turns the shape check into a membership check.
    """
    problems: list[str] = []

    extra = [c for c in df.columns if c not in COLUMNS]
    missing = [c for c in COLUMNS if c not in df.columns]
    if extra:
        problems.append(f"columns outside the allowlist reached the output: {extra}")
    if missing:
        problems.append(f"missing columns: {missing}")
    if extra or missing:
        return problems  # the rest of the checks would be noise

    if list(df.columns) != list(COLUMNS):
        problems.append(f"column order is {list(df.columns)}, expected {list(COLUMNS)}")

    if df["feedback_id"].duplicated().any():
        problems.append(f"{int(df['feedback_id'].duplicated().sum())} duplicate feedback_id values")
    if not df["feedback_id"].astype("string").str.fullmatch(r"F\d{6}").all():
        problems.append("feedback_id values not of the form F000001")

    bad_codes = set(df["dealer_code"].dropna().unique()) - (dealer_codes or set())
    if dealer_codes is not None and bad_codes:
        problems.append(f"dealer codes not in dealerships.csv: {sorted(bad_codes)}")

    dates = pd.to_datetime(df["feedback_date"], errors="coerce")
    if dates.isna().any():
        problems.append(f"{int(dates.isna().sum())} rows have no usable feedback_date")
    out_of_window = ((dates.dt.date < DATE_MIN) | (dates.dt.date > DATE_MAX)).sum()
    if out_of_window:
        problems.append(f"{int(out_of_window)} rows fall outside Oct 2025 - Sep 2026")

    r = pd.to_numeric(df["rating_1to5"], errors="coerce")
    if r.isna().any():
        problems.append(
            f"{int(r.isna().sum())} rows have a non-numeric rating_1to5 (D-031 drops these)"
        )
    if ((r < 1) | (r > 5)).any():
        problems.append(f"{int(((r < 1) | (r > 5)).sum())} rows have rating_1to5 outside 1-5")
    if (r.dropna() % 1 != 0).any():
        problems.append("rating_1to5 holds fractional values")

    scales = set(df["rating_scale"].dropna().unique()) - set(RatingScale.__args__)
    if scales:
        problems.append(f"unknown rating_scale values: {sorted(scales)}")

    if df["department_raw"].isna().any():
        problems.append(f"{int(df['department_raw'].isna().sum())} rows have no department_raw")

    depts = set(df["department"].dropna().unique()) - set(Department.__args__)
    if depts:
        problems.append(f"department holds values outside Service/Sales/Parts: {sorted(depts)}")

    if df["from_summary"].any():
        summary_with_comment = int((df["from_summary"] & df["comment"].notna()).sum())
        if summary_with_comment:
            problems.append(
                f"{summary_with_comment} summary-expanded rows carry a comment "
                "(D-032 #1 says none)"
            )

    return problems

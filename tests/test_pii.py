"""Tests for src/pii.py, driven by tests/fixtures/pii_cases.yaml (DECISIONS.md D-003, D-026)."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pandas as pd
import pytest
import yaml

from src.pii import TOKENS, deidentify, redact

CASES = yaml.safe_load((Path(__file__).parent / "fixtures" / "pii_cases.yaml").read_text())
HAS_SPACY_MODEL = importlib.util.find_spec("en_core_web_sm") is not None
needs_spacy = pytest.mark.skipif(not HAS_SPACY_MODEL, reason="spaCy model not installed here")


def _ids(cases):
    return [c["id"] for c in cases]


@pytest.mark.parametrize("case", CASES["must_redact"], ids=_ids(CASES["must_redact"]))
def test_patterns_redact(case):
    out, counts = redact(case["input"], case.get("row_values"), use_ner=False)
    assert out == case["expected"]
    assert sum(counts.values()) >= 1


@pytest.mark.parametrize("case", CASES["must_not_redact"], ids=_ids(CASES["must_not_redact"]))
def test_patterns_leave_alone(case):
    out, counts = redact(case["input"], use_ner=False)
    assert out == case["input"], f"false positive: {out}"
    assert not counts


@needs_spacy
@pytest.mark.parametrize("case", CASES["must_not_redact"], ids=_ids(CASES["must_not_redact"]))
def test_ner_leave_alone(case):
    out, _ = redact(case["input"], use_ner=True)
    assert out == case["input"], f"spaCy false positive: {out}"


@needs_spacy
@pytest.mark.parametrize("case", CASES["ner_cases"], ids=_ids(CASES["ner_cases"]))
def test_ner_people(case):
    out, _ = redact(case["input"], use_ner=True)
    assert out == case["expected"]


@pytest.mark.parametrize("case", CASES.get("owner_cases") or [{"id": "none"}],
                         ids=_ids(CASES.get("owner_cases") or [{"id": "none"}]))
def test_owner_cases(case):
    if case["id"] == "none":
        pytest.skip("owner has not added cases yet")
    if case.get("ner") and not HAS_SPACY_MODEL:
        pytest.skip("needs spaCy")
    out, _ = redact(case["input"], case.get("row_values"), use_ner=HAS_SPACY_MODEL)
    assert out == case["expected"]


def test_owner_has_added_cases():
    """Done-when criterion in agents/briefs/w1_pii.md."""
    assert len(CASES.get("owner_cases") or []) >= 3, "owner to add at least 3 cases"


def test_none_and_blank():
    assert redact(None)[0] is None
    assert redact(float("nan"))[0] is None
    assert redact("", use_ner=False)[0] == ""


def test_tokens_are_not_re_redacted():
    text = "call [PHONE] or rego [REGO]"
    assert redact(text, use_ner=False)[0] == text


# ---------------------------------------------------------------- allowlist


@pytest.fixture
def frame():
    return pd.DataFrame({
        "Date": ["2026-01-02", "2026-01-03"],
        "Dept": ["Service", "Sales"],
        "Score": [5, 2],
        "Comments": ["Bronwyn here, all good", "Car ABC123 was late, call 0412 345 678"],
        "Customer Name": ["Bronwyn Taylor", "Sam Lee"],
        "Rego": ["XYZ999", "ABC123"],
        "Customer Email 2": ["b@t.com", "s@l.com"],  # unexpected column: must be dropped
        "Model": ["Voltra E3", "Arc"],
    })


MAPPING = {
    "Date": "date", "Dept": "department", "Score": "rating", "Comments": "comment",
    "Customer Name": "redact_name", "Rego": "redact_rego",
}


def test_allowlist_drops_everything_else(frame):
    out, _ = deidentify(frame, MAPPING, "test.csv", use_ner=False)
    assert list(out.columns) == ["source_file", "source_row", "date", "department", "rating", "comment"]
    flat = out.astype(str).to_string()
    for leaked in ("Bronwyn", "Taylor", "Sam Lee", "XYZ999", "ABC123", "b@t.com", "Voltra", "0412"):
        assert leaked not in flat


def test_deidentify_redacts_and_counts(frame):
    out, totals = deidentify(frame, MAPPING, "test.csv", use_ner=False)
    assert out.loc[0, "comment"] == "[NAME] here, all good"
    assert out.loc[1, "comment"] == "Car [REGO] was late, call [PHONE]"
    assert totals["[NAME]"] == 1 and totals["[REGO]"] == 1 and totals["[PHONE]"] == 1
    assert set(totals) <= set(TOKENS)


def test_lineage(frame):
    out, _ = deidentify(frame, MAPPING, "test.csv", use_ner=False)
    assert (out["source_file"] == "test.csv").all()
    assert out["source_row"].tolist() == [0, 1]


def test_mapping_errors(frame):
    with pytest.raises(ValueError):
        deidentify(frame, {"Date": "birthday"}, "x")
    with pytest.raises(KeyError):
        deidentify(frame, {"Nope": "date"}, "x")
    with pytest.raises(ValueError):
        deidentify(frame, {"Date": "date", "Dept": "date"}, "x")

"""Tests for src/pii.py, driven by tests/fixtures/pii_cases.yaml (DECISIONS.md D-003, D-026)."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pandas as pd
import pytest
import yaml

from src.pii import TOKENS, deidentify, promote_names, redact

CASES = yaml.safe_load((Path(__file__).parent / "fixtures" / "pii_cases.yaml").read_text())
HAS_SPACY_MODEL = importlib.util.find_spec("en_core_web_sm") is not None
needs_spacy = pytest.mark.skipif(not HAS_SPACY_MODEL, reason="spaCy model not installed here")


def _ids(cases):
    return [c["id"] for c in cases]


@pytest.mark.parametrize("case", CASES["must_redact"], ids=_ids(CASES["must_redact"]))
def test_patterns_redact(case):
    out, counts = redact(case["input"], case.get("row_values"), use_ner=False,
                         staff_names=case.get("staff_names"))
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
    out, _ = redact(case["input"], use_ner=True, staff_names=case.get("staff_names"),
                    known_names=case.get("known_names"))
    assert out == case["expected"]


@pytest.mark.parametrize("case", CASES.get("owner_cases") or [{"id": "none"}],
                         ids=_ids(CASES.get("owner_cases") or [{"id": "none"}]))
def test_owner_cases(case):
    if case["id"] == "none":
        pytest.skip("owner has not added cases yet")
    if case.get("ner") and not HAS_SPACY_MODEL:
        pytest.skip("needs spaCy")
    out, _ = redact(case["input"], case.get("row_values"), use_ner=HAS_SPACY_MODEL,
                    staff_names=case.get("staff_names"), known_names=case.get("known_names"))
    assert out == case["expected"]


@pytest.mark.skip(reason="owner waived extra cases on 29 Oct 2026 (D-033); "
                         "compensating control: owner read 40 redacted pilot comments")
def test_owner_has_added_cases():
    """Done-when criterion in agents/briefs/w1_pii.md, waived by the owner (D-033)."""
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
    expected_cols = ["source_file", "source_row", "date", "department", "rating", "comment"]
    assert list(out.columns) == expected_cols
    flat = out.astype(str).to_string()
    leaks = ("Bronwyn", "Taylor", "Sam Lee", "XYZ999", "ABC123", "b@t.com", "Voltra", "0412")
    for leaked in leaks:
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


# ---------------------------------------------------------------- corpus pass (no spaCy needed)


def test_promote_names_picks_mostly_capitalised():
    texts = ["Dave was great", "thanks Dave", "dave fixed it", "Dave again", "you will love it",
             "Will do", "it will be ready", "will call", "Lovely staff", "lovely people", "lovely"]
    cands = {"Dave": 3, "Will": 2, "Lovely": 2}
    assert promote_names(texts, cands) == {"Dave"}


def test_promote_names_needs_min_count():
    assert promote_names(["Zed was great"], {"Zed": 1}) == set()


def test_extra_names_any_case_with_context():
    out, _ = redact("as a retiree, dave was a delight. Thanks Dave!", use_ner=False,
                    extra_names={"Dave"})
    assert out == "as a retiree, [NAME] was a delight. Thanks [STAFF]!"


# ------------------------------------------------- the "<name> - <note>" opening (D-051)


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        # Two capitalised tokens then a dash: the convention in several logs.
        ("Carmen Gomes - Reckons it was easy to understand.",
         "[NAME] - Reckons it was easy to understand."),
        # Three tokens (double-barrelled or middle name) still qualify.
        ("Mary Anne Fitzgerald - Said the quote was clear.",
         "[NAME] - Said the quote was clear."),
        # An en dash and an em dash are the same convention.
        ("Yianni Pappas – Tradie, needed the ute back.",
         "[NAME] – Tradie, needed the ute back."),
    ],
)
def test_name_prefix_redacted(text, expected):
    out, counts = redact(text, use_ner=False)
    assert out == expected
    assert counts["[NAME]"] == 1


@pytest.mark.parametrize(
    "text",
    [
        # One leading word is ordinary prose, not a name. This is the case that keeps the
        # rule honest: "Sarcastic - ..." appears four times in the data.
        "Sarcastic - 'great to see the filter I ordered is still on its holiday'",
        "Great service - thanks heaps.",
        # A department name is not a person, even in the two-token shape.
        "Service Dept - fine as always.",
        # No dash separator, so no attribution prefix.
        "Carmen Gomes was lovely to deal with.",
        # The dash has to follow the name, not sit mid-sentence.
        "Booked in Monday - Carmen Gomes called back.",
    ],
)
def test_name_prefix_leaves_prose_alone(text):
    out, counts = redact(text, use_ner=False)
    assert out == text
    assert counts["[NAME]"] == 0


def test_name_prefix_beats_the_staff_roster_for_the_customers_own_name():
    """The person opening the comment is the customer, so [NAME], even if a staff member
    shares the first name."""
    out, _ = redact("Aroha Williams - Said the service was quick.",
                    staff_names={"Aroha"}, use_ner=False)
    assert out == "[NAME] - Said the service was quick."

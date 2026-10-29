"""De-identification for Kestrel feedback (DECISIONS.md D-003, D-026).

Two jobs:
1. Allowlist: keep only the date, department, rating and comment columns. Every other source
   column is dropped. Name/rego columns are read only to redact those exact strings from the
   same row's comment, then discarded.
2. Redact free text, replacing PII with typed tokens:
   [NAME] [STAFF] [REGO] [PHONE] [EMAIL] [ADDRESS]

Order matters: exact row values first, then patterns (email, phone, address, rego), then spaCy
person names last, so the model never sees text that patterns have already cleaned.
"""

from __future__ import annotations

import re
from collections import Counter
from collections.abc import Iterable, Mapping
from functools import lru_cache

import pandas as pd

TOKENS = ("[NAME]", "[STAFF]", "[REGO]", "[PHONE]", "[EMAIL]", "[ADDRESS]")
KEEP_ROLES = ("date", "department", "rating", "comment")
TRANSIENT_ROLES = ("redact_name", "redact_rego")  # read for redaction, never kept

# ---------------------------------------------------------------- patterns

EMAIL = re.compile(r"\b[\w.+-]+@[\w-]+(?:\.[\w-]+)+\b")

_SEP = r"[\s-]?"
PHONE = re.compile(
    r"(?<![\w/])(?:"
    r"(?:\+?61|0061)" + _SEP + r"\(?0?\)?" + _SEP + r"[2-478](?:" + _SEP + r"\d){8}"  # +61 ...
    r"|\(0[2378]\)" + _SEP + r"\d{4}" + _SEP + r"\d{4}"  # (02) 9123 4567
    r"|0[2-478](?:" + _SEP + r"\d){8}"  # 0412 345 678 / 02 9123 4567
    r"|1[38]00" + _SEP + r"\d{3}" + _SEP + r"\d{3}"                                    # 1300 / 1800
    r"|13" + _SEP + r"\d{2}" + _SEP + r"\d{2}"                                         # 13 xx xx
    r")(?![\w/])"
)

_STREET_TYPES = (
    r"St|Street|Rd|Road|Ave|Avenue|Dr|Drive|Ct|Court|Pl|Place|Cres|Crescent|Hwy|Highway|"
    r"Pde|Parade|Tce|Terrace|Bvd|Blvd|Boulevard|Ln|Lane|Way|Cl|Close|Gr|Grove|Cct|Circuit"
)
ADDRESS = re.compile(
    r"\b(?:(?:Unit|Apt|Flat|Shop)\s*\d+[A-Za-z]?\s*[/,]?\s*)?"
    r"\d{1,5}[A-Za-z]?(?:\s*/\s*\d{1,5}[A-Za-z]?)?\s+"
    r"(?:[A-Z][a-z]+\s+){1,3}(?:" + _STREET_TYPES + r")\b\.?"
)

# Australian plate shapes (letters/digits, optional single space or dash).
_REGO_SHAPES = [
    r"[A-Z]{3}" + _SEP + r"\d{2,3}[A-Z]{0,2}",   # ABC123, ABC-12D, ABC 12DE (NSW/most states)
    r"\d[A-Z]{2,3}" + _SEP + r"\d[A-Z]{2}",      # 1AB2CD (VIC)
    r"\d[A-Z]{3}" + _SEP + r"\d{3}",             # 1ABC234 (VIC/WA)
    r"\d{3}" + _SEP + r"[A-Z]{3}",               # 123ABC (QLD)
    r"[A-Z]{2}" + _SEP + r"\d{2}" + _SEP + r"[A-Z]{2}",  # AB12CD (NSW)
]
# not followed by another digit group, so "ABN 12 345 678 901" is left alone
REGO_SHAPE = re.compile(r"(?<![\w$./-])(?:" + "|".join(_REGO_SHAPES) + r")(?![\w./-])(?!\s\d)")
# After an explicit cue word, accept any 2-7 character plate-like token (e.g. "rego XYZ9").
REGO_CUED = re.compile(
    r"(?i:\b(?:rego|registration|reg\.?|plate|number\s*plate)\b\s*(?:no\.?|number|#)?\s*[:#-]?\s*)"
    # one 2-7 char token containing a digit, optionally followed by an upper-case/digit chunk
    # (so "rego XYZ 789" is caught but "rego XYZ9 was" stops before "was")
    r"([A-Za-z0-9]{1,4}[\s-]\d[A-Za-z0-9]{0,3}|(?=[A-Za-z]*\d)[A-Za-z0-9]{2,7})(?!\w)"
)
# Codes that look like plates but are models, trims, parts or periods. Extend as data shows more.
NOT_REGO = {
    "RAV4", "CX5", "CX-5", "CX9", "SR5", "V8", "V6", "4WD", "AWD", "2WD", "GT86", "MX5", "ZR",
    "Q1", "Q2", "Q3", "Q4", "FY25", "FY26", "COVID19", "MP3", "USB", "CD", "DVD",
}

STAFF_BEFORE = re.compile(
    r"(?i)\b(?:sales\s*(?:person|man|woman|guy|girl|rep|consultant|exec(?:utive)?)|salesperson|"
    r"service\s*(?:advisor|adviser|manager|guy|rep)|advisor|adviser|consultant|mechanic|"
    r"technician|tech|manager|receptionist|staff(?:\s*member)?|parts\s*(?:guy|person|rep)|"
    r"thanks(?:\s+to)?|thank\s+you(?:\s+to)?|cheers|shout\s*-?\s*out\s+to|ask\s+for|dealt\s+with|"
    r"served\s+by|helped\s+by|spoke\s+(?:to|with))\b[\s,:-]*(?:\w+\s+){0,2}$"
)
STAFF_AFTER = re.compile(
    r"(?i)^[\s,]*(?:\(?(?:from|in|at|on)\s+(?:the\s+)?"
    r"(?:service|sales|parts|reception|front\s*desk|workshop|desk|counter|finance)\b)"
)
# Several logs open a comment with the customer's own name and then a dash:
# "Carmen Gomes - Reckons Aroha made it all easy to understand." 55 of the 5,386 raw
# comments use that convention. spaCy catches most of them, but only because the first
# name happens to sit in a name column too — where it does not, the sentence-start guard
# in _redact_people lets the name through (D-051). This pattern is deterministic and does
# not depend on the roster. Two or three capitalised tokens are required, which is what
# keeps "Sarcastic - 'great to see the filter...'" out of it: a single leading word is
# ordinary prose, a first name plus a surname is not.
NAME_PREFIX = re.compile(
    r"^\s*([A-Z][a-z'’-]+(?:\s+[A-Z][a-z'’-]+){1,2})\s+[-–—]\s+"
)

# Words spaCy may tag as PERSON that are not people in this data.
NOT_NAMES = {
    "service", "sales", "parts", "workshop", "kestrel", "voltra", "veyra", "arc",
    "thanks", "cheers", "regards", "great", "excellent", "mr", "mrs", "ms",
}

# ---------------------------------------------------------------- helpers


def _sub(pattern: re.Pattern, token: str, text: str, counts: Counter, group: int = 0,
         skip: set[str] | None = None) -> str:
    def repl(m: re.Match) -> str:
        target = m.group(group)
        if skip and target.upper().replace(" ", "") in skip:
            return m.group(0)
        counts[token] += 1
        if group == 0:
            return token
        start, end = m.span(group)
        return m.group(0)[: start - m.start()] + token + m.group(0)[end - m.start():]
    return pattern.sub(repl, text)


def _whole_word(value: str) -> re.Pattern:
    return re.compile(r"(?<!\w)" + re.escape(value) + r"(?!\w)", re.IGNORECASE)


def _row_value_patterns(row_values: Mapping[str, Iterable] | None) -> list[tuple[re.Pattern, str]]:
    """Exact-match patterns built from this row's own name and rego cells."""
    pats: list[tuple[re.Pattern, str]] = []
    if not row_values:
        return pats
    for value in row_values.get("redact_name", []) or []:
        if value is None or (isinstance(value, float) and pd.isna(value)):
            continue
        full = str(value).strip()
        if len(full) >= 2:
            pats.append((_whole_word(full), "[NAME]"))
        for part in re.split(r"[\s,.]+", full):
            if len(part) >= 3 and part.lower() not in NOT_NAMES:
                pats.append((_whole_word(part), "[NAME]"))
    for value in row_values.get("redact_rego", []) or []:
        if value is None or (isinstance(value, float) and pd.isna(value)):
            continue
        plate = re.sub(r"[\s-]", "", str(value)).upper()
        if len(plate) >= 2:
            # match the plate with or without a space/dash between any characters
            flexible = r"[\s-]?".join(re.escape(c) for c in plate)
            pats.append((re.compile(r"(?<!\w)" + flexible + r"(?!\w)", re.IGNORECASE), "[REGO]"))
    # longest first, so "Sarah Jones" wins over "Sarah"
    pats.sort(key=lambda p: -len(p[0].pattern))
    return pats


@lru_cache(maxsize=8)
def _roster_pattern(names: frozenset[str]) -> re.Pattern | None:
    """One case-insensitive whole-word pattern for a set of staff first names."""
    usable = sorted((n.strip() for n in names if n and len(n.strip()) >= 2), key=len, reverse=True)
    if not usable:
        return None
    return re.compile(r"(?<!\w)(?:" + "|".join(re.escape(n) for n in usable) + r")(?!\w)", re.I)


def _at_sentence_start(ent) -> bool:
    """True if the entity is the first real word of its sentence (ignoring quotes/brackets)."""
    for tok in ent.sent:
        if tok.is_punct or tok.is_space:
            continue
        return tok.i == ent.start
    return False


@lru_cache(maxsize=1)
def _nlp():
    import spacy  # imported lazily so pattern-only use does not need spaCy

    return spacy.load("en_core_web_sm", disable=["lemmatizer"])


def _redact_people(text: str, counts: Counter, known_names: frozenset[str] = frozenset()) -> str:
    doc = _nlp()(text)
    out, last = [], 0
    for ent in doc.ents:
        if ent.label_ != "PERSON":
            continue
        surface = ent.text.strip()
        if (not surface or surface.startswith("[") or surface.lower() in NOT_NAMES
                or not any(ch.isupper() for ch in surface)):
            continue
        # Names don't contain digits ("HiLux SR5 4WD" was tagged PERSON).
        if any(ch.isdigit() for ch in surface):
            continue
        before, after = text[: ent.start_char], text[ent.end_char:]
        is_staff = STAFF_BEFORE.search(before) or STAFF_AFTER.search(after)
        # spaCy often tags a capitalised word that opens a sentence ("Spooky good timing.",
        # "Keys weren't ready"). Trust a sentence-initial PERSON only if its first word is a
        # first name seen in the data's name or staff columns, or a staff cue follows it
        # ("Dave in service was great").
        first = ent[0].text
        if _at_sentence_start(ent) and first not in known_names and not is_staff:
            continue
        token = "[STAFF]" if is_staff else "[NAME]"
        out.append(text[last: ent.start_char])
        out.append(token)
        counts[token] += 1
        last = ent.end_char
    out.append(text[last:])
    return "".join(out)


def _redact_extra_names(text: str, names: frozenset[str], counts: Counter) -> str:
    """Names promoted from the whole corpus (see promote_names), any letter case."""
    pat = _roster_pattern(names)
    if pat is None:
        return text
    out, last = [], 0
    for m in pat.finditer(text):
        before, after = text[: m.start()], text[m.end():]
        is_staff = STAFF_BEFORE.search(before) or STAFF_AFTER.search(after)
        token = "[STAFF]" if is_staff else "[NAME]"
        out += [text[last: m.start()], token]
        counts[token] += 1
        last = m.end()
    out.append(text[last:])
    return "".join(out)


# ---------------------------------------------------------------- corpus pass


def person_candidates(texts: Iterable[str]) -> Counter:
    """Count one-word spaCy PERSON entities that are NOT at the start of a sentence.

    Mid-sentence capitalisation is a much stronger signal than sentence-initial ("Keys weren't").
    Needs spaCy; run once over all comments at ingestion.
    """
    found: Counter = Counter()
    for doc in _nlp().pipe(t for t in texts if isinstance(t, str) and t.strip()):
        for ent in doc.ents:
            surface = ent.text.strip()
            if (ent.label_ == "PERSON" and len(ent) == 1 and not _at_sentence_start(ent)
                    and surface[:1].isupper() and surface.lower() not in NOT_NAMES):
                found[surface] += 1
    return found


def promote_names(texts: Iterable[str], candidates: Mapping[str, int], min_count: int = 2,
                  min_cap_share: float = 0.6) -> set[str]:
    """Pick candidate names that are safe to redact in ANY letter case.

    A candidate qualifies if spaCy tagged it in >= min_count comments and, across all comments,
    >= min_cap_share of its occurrences are capitalised. "Dave" (mostly capitalised) qualifies,
    so a lower-case "dave" is then caught; "Will" or "Lovely" (mostly ordinary words) do not.
    Pure function (no spaCy), so it is unit-tested directly.
    """
    texts = [t for t in texts if isinstance(t, str)]
    promoted = set()
    for name, n in candidates.items():
        if n < min_count or len(name) < 3:
            continue
        occ = [m.group(0) for t in texts for m in _whole_word(name).finditer(t)]
        if occ and sum(o[:1].isupper() for o in occ) / len(occ) >= min_cap_share:
            promoted.add(name)
    return promoted


# ---------------------------------------------------------------- public API


def redact(text, row_values: Mapping[str, Iterable] | None = None, use_ner: bool = True,
           staff_names: Iterable[str] | None = None, known_names: Iterable[str] | None = None,
           extra_names: Iterable[str] | None = None,
           ) -> tuple[str | None, Counter]:
    """Return (redacted_text, token_counts). Never returns or logs the original strings.

    staff_names: first names from the data's staff columns ("Taken by", "Logged by", "Staff", ...);
        redacted as [STAFF] in any letter case.
    known_names: first names seen in any name or staff column (case-sensitive); used only to
        confirm spaCy's one-word, sentence-initial PERSON guesses.
    extra_names: names promoted from the whole corpus by promote_names(); any letter case,
        token chosen by context.
    All three lists are built in memory at ingestion and never written out (D-003, D-026).
    """
    counts: Counter = Counter()
    if text is None or (isinstance(text, float) and pd.isna(text)):
        return None, counts
    t = str(text)

    for pat, token in _row_value_patterns(row_values):
        t = _sub(pat, token, t, counts)
    t = _sub(EMAIL, "[EMAIL]", t, counts)
    t = _sub(PHONE, "[PHONE]", t, counts)
    t = _sub(ADDRESS, "[ADDRESS]", t, counts)
    t = _sub(REGO_CUED, "[REGO]", t, counts, group=1, skip=NOT_REGO)
    t = _sub(REGO_SHAPE, "[REGO]", t, counts, skip=NOT_REGO)
    # The "<customer name> - <note>" opening, before the roster and spaCy see the text, so
    # the person giving the feedback is [NAME] rather than a [STAFF] match on their first
    # name (D-051).
    m = NAME_PREFIX.match(t)
    if m and not any(w.lower() in NOT_NAMES for w in m.group(1).split()):
        t = t[: m.start(1)] + "[NAME]" + t[m.end(1):]
        counts["[NAME]"] += 1

    roster = _roster_pattern(frozenset(staff_names or ()))
    if roster is not None:
        t = _sub(roster, "[STAFF]", t, counts)
    if extra_names:
        t = _redact_extra_names(t, frozenset(extra_names), counts)
    if use_ner:
        t = _redact_people(t, counts, frozenset(known_names or ()))
    return t, counts


def deidentify(df: pd.DataFrame, mapping: Mapping[str, str], source_file: str,
               use_ner: bool = True, staff_names: Iterable[str] | None = None,
               known_names: Iterable[str] | None = None,
               extra_names: Iterable[str] | None = None) -> tuple[pd.DataFrame, Counter]:
    """Apply the allowlist and redact comments.

    mapping: source column name -> role, where role is one of KEEP_ROLES or TRANSIENT_ROLES.
    Columns not in the mapping are dropped. Returns (clean_df, total_token_counts).
    Output columns: source_file, source_row, date, department, rating, comment.
    """
    bad = {r for r in mapping.values() if r not in KEEP_ROLES + TRANSIENT_ROLES}
    if bad:
        raise ValueError(f"unknown roles in mapping: {sorted(bad)}")
    missing = [c for c in mapping if c not in df.columns]
    if missing:
        raise KeyError(f"mapped columns not in data: {missing}")
    for role in KEEP_ROLES:
        if list(mapping.values()).count(role) > 1:
            raise ValueError(f"more than one column mapped to '{role}'")

    by_role: dict[str, list[str]] = {}
    for col, role in mapping.items():
        by_role.setdefault(role, []).append(col)

    totals: Counter = Counter()
    comments = []
    comment_col = by_role.get("comment", [None])[0]
    for _, row in df.iterrows():
        row_values = {r: [row[c] for c in by_role.get(r, [])] for r in TRANSIENT_ROLES}
        text = row[comment_col] if comment_col else None
        red, counts = redact(text, row_values, use_ner=use_ner, staff_names=staff_names,
                             known_names=known_names, extra_names=extra_names)
        comments.append(red)
        totals.update(counts)

    out = pd.DataFrame({
        "source_file": source_file,
        "source_row": df.index.to_numpy(),
        "date": df[by_role["date"][0]].to_numpy() if "date" in by_role else None,
        "department": df[by_role["department"][0]].to_numpy() if "department" in by_role else None,
        "rating": df[by_role["rating"][0]].to_numpy() if "rating" in by_role else None,
        "comment": comments,
    })
    return out, totals

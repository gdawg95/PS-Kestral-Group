# Making this repository public — checklist and open blocker

The owner established on 30 Oct 2026 that the repository **will be made public for
submission**. D-064 had committed the dataset export on the stated basis that it was
private, and said in terms to re-check before any visibility change. This file is that
re-check, the evidence behind it, and the one thing still outstanding.

The challenge pack is fictional. It is treated throughout as real customer feedback,
because that is the only way the controls get tested.

> **Status: NOT READY. Do not change the repository to public yet.**
> Everything below is done except item 1, which cannot be fixed by a later commit.

---

## 1. BLOCKER — the dataset already in history is a re-identification key

`bec914d` ("Export the clean dataset for reviewers") committed the export with all 15
columns: exact dates, and `source_file` + `source_sheet` + `source_row`.

Those three lineage columns identify **7,079 of the 7,150 rows uniquely — 99.0%**. They
are a primary key back to the original, *un*redacted spreadsheets. Anyone holding the
challenge pack — other participants, the assessors — can join on them and read back the
customer name, phone number and registration plate that redaction removed.

The current working tree no longer publishes them (D-067), but **a later commit cannot
remove a blob from git history**. Three commits now sit on top of `bec914d`, all already
pushed to `origin/w1-wrapup`. Publishing the repository as it stands publishes that commit
and everything in it.

So `bec914d` has to be rewritten before the repository is ever public. That force-pushes
over commits that already exist on the remote, which is why it is the owner's call and not
something to do quietly.

### Option A — rewrite in place, then force-push

```bash
git filter-branch --index-filter \
  'git rm --cached --ignore-unmatch export/feedback_clean.csv export/feedback_clean.json export/feedback_clean.xlsx' \
  --prune-empty bec914d^..HEAD
```

Then force-push `w1-wrapup`, and re-commit the public export on top.

The four commit SHAs change. Anything referring to them by SHA goes stale, and any other
clone of this branch has to reset to the rewritten history rather than merge.

**Residual risk:** GitHub keeps unreachable objects reachable by their SHA for a period
after a force-push. The old blob would have to be guessed or already known to be fetched,
so the risk is low — but it is not zero, and "low" is a different claim from "gone".

### Option B — publish to a fresh repository (recommended)

Rewrite locally as above, then push to a **brand-new empty GitHub repository** and make
that one public, leaving this one private.

The old objects were never pushed there, so there is nothing unreachable to retain and the
residual risk in Option A disappears by construction. The full commit history, all 67
decisions and the AI log still come across intact, which matters because the process *is*
the submission.

Cost: the repository URL changes, and any link already shared points at the private one.

### What must NOT happen

Making the repository public first and fixing it afterwards. Once a public clone or a
crawler has the commit, no rewrite reaches it.

---

## 2. DONE — the published dataset is minimised

`export/feedback_clean.{csv,xlsx,json}` carries 12 columns, not 15 (D-067). Measured on
this dataset, not argued from guidance:

| Quasi-identifier set | Rows alone in their group |
|---|---:|
| `source_file` + `source_sheet` + `source_row` | 7,079 of 7,150 (99.0%) — **withheld** |
| `dealer_code` + exact date + `department` | 4,149 (58.0%) — **exact date withheld** |
| `dealer_code` + `feedback_month` + `department` | 100 (1.4%) — what is published |
| `dealer_code` + `feedback_month` | 1 (0.0%) |

The month costs nothing that was being used: every analysis in the project is monthly, and
D-040 already recorded that the day never reaches a published figure.

`src/export.py` **blocks** the export if a lineage column or an exact date reaches the
public frame, with a test per column. It is a gate, not a convention.

The owner's full-lineage copy goes to `data/clean/export_internal/` via
`--internal`, which `.gitignore` and the commit guard both keep out of the repository.
Verified: `git check-ignore` matches, and the guard exits 1 on it.

## 3. DONE — the whole history was scanned for personal information

Every blob in all 54 commits, across every branch and both archive tags — not just HEAD,
because publishing publishes all of it.

| Checked | Result |
|---|---|
| Real email addresses | none |
| Real phone numbers | none |
| Street addresses | none |
| Registration plates | none |
| Person-shaped names in comment-bearing files | none |

Every pattern hit traced to either the regexes in `src/pii.py` itself or the synthetic
fixtures in `tests/` (`b@t.com`, `ABC123`, `0412 345 678`). The two name-shaped hits are
false positives: `Corsa Rubbish` is row 3256 missing a full stop between a car model and a
complaint, and `Box Hill's` is a suburb in a formatting report.

**No staff roster or name list exists on disk at any commit.** The roster is built in
memory during ingestion from columns that are then discarded; only counts are ever written
(`src/ingest.py:823`).

Re-run it before publishing if any commit has been added since:
`uv run python -I scripts/scan_history_pii.py`

## 4. DONE — committed reports carry no linkage

96 verbatim comments are quoted across `reports/llm_review.md`,
`reports/theme_assignment.md`, `reports/theme_discovery.md` and
`reports/theme_proposal.md`. Checked: **zero** dealer codes, dates or `feedback_id`s appear
in those four files, so a quote cannot be tied to a site, a month or a row.

`reports/label_sample.csv` and `reports/labels_done.csv` carry `feedback_id` and redacted
comment text only — no dates and no lineage.

## 5. DONE — no credentials in history

No `gitleaks` on this machine (D-013: no network access to hook repositories), so every
blob in every commit was swept for the high-signal credential shapes instead: GitHub PATs,
OpenAI and Hugging Face keys, AWS access keys, Google API keys, Slack tokens and PEM
private-key headers. **Nothing found.**

This is narrower than `gitleaks`, which carries far more rules. Run the real thing if it
can be installed:

```bash
make gitleaks
```

Treat item 5 as "swept, not gitleaks-clean" until that passes.

## 6. Before flipping the switch

- [ ] **Item 1 resolved** — history rewritten, Option A or B
- [ ] `make export` re-run and committed, so the published files match the audit in `export/MANIFEST.md`
- [ ] `uv run pytest -q` green
- [ ] `make gitleaks` run, or item 5 accepted as a sweep
- [ ] Re-run the history PII scan if commits were added after this file was written
- [ ] Confirm `data/raw/`, `data/interim/` and `data/clean/` are absent from the published tree
- [ ] Decide whether the four `archive/*` tags and the `w5-research` branch should go public too — they were scanned and are clean, but they hold superseded content and old verdict placeholders

## What a public reader loses, stated honestly

They cannot trace a published row back to its source cell, and they cannot reproduce a
daily or weekly cut. The first is the re-identification path itself, and a public reader
does not hold the raw spreadsheets to check lineage against in any case. The second is not
used anywhere in the project. Everything that supports a claim in either report —
`department_raw`, `rating_raw`, `rating_scale`, the flags, the reports and all 67 decisions
— is still there.

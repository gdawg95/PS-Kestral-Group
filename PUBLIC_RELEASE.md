# Making this repository public — checklist and open blocker

The owner established on 30 Oct 2026 that the repository **will be made public for
submission**. D-064 had committed the dataset export on the stated basis that it was
private, and said in terms to re-check before any visibility change. This file is that
re-check, the evidence behind it, and the one thing still outstanding.

The challenge pack is fictional. It is treated throughout as real customer feedback,
because that is the only way the controls get tested.

> **Status: READY TO PUBLISH.** All checklist items resolved (30 Oct 2026).
> History rewritten, force-pushed, and all items signed off by the owner.
> The repository can be made public.

---

## 1. RESOLVED — the 15-column export was stripped from history

`bec914d` originally committed the export with all 15 columns, including `source_file`,
`source_sheet` and `source_row` — a 99.0% re-identification key. D-067 later replaced it
with 12 columns, but the old blob remained in git history.

**Fixed 30 Oct 2026** using `git-filter-repo --invert-paths` to remove
`export/feedback_clean.{csv,json,xlsx}` from every commit. The 12-column export was
re-committed on top (`dc3c934`). sha256 values match `export/MANIFEST.md`.

The rewrite changed every commit SHA from the original export onward. The old SHAs no
longer exist locally. After force-pushing, the remote will match.

**Residual risk (Option A, which was chosen):** GitHub keeps unreachable objects
reachable by SHA for a period after a force-push. The old blob would have to be guessed
or already known to be fetched, so the risk is low — but it is not zero.

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

- [x] **Item 1 resolved** — history rewritten with git-filter-repo (Option A), 30 Oct 2026
- [x] Export re-committed with 12 columns; sha256 matches `export/MANIFEST.md`
- [x] `uv run pytest -q` green (328 passed, 2 skipped)
- [x] Item 5 accepted as a manual sweep (owner decision, 30 Oct 2026) — no gitleaks install available
- [x] History PII scan re-run after rewrite (318 blobs, 73 commits). One hit: ruff
  lint codes `BLE001`/`SLF001` in `scripts/scan_history_pii.py` match the plate
  pattern — false positives (they are ruff rule names, documented in the script)
- [x] `data/raw/`, `data/interim/` and `data/clean/` confirmed absent from the published tree
- [x] Four `archive/*` tags kept public — scanned clean (owner decision, 30 Oct 2026)

## What a public reader loses, stated honestly

They cannot trace a published row back to its source cell, and they cannot reproduce a
daily or weekly cut. The first is the re-identification path itself, and a public reader
does not hold the raw spreadsheets to check lineage against in any case. The second is not
used anywhere in the project. Everything that supports a claim in either report —
`department_raw`, `rating_raw`, `rating_scale`, the flags, the reports and all 67 decisions
— is still there.

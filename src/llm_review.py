"""Wave 4: a local LLM adjudicates rating/sentiment disagreements.

Brief: `agents/briefs/w4_llm.md`. Prompt: `prompts/sentiment_v1.md` (v1, owner-approved,
Checkpoint 4). Model: `qwen2.5:3b` pinned by Ollama ID in `config.yaml` (D-012).

This runs only where the deterministic sentiment model and the customer's own star rating
disagree. Every one of the eight such cases sampled in the classifier pilot was sarcasm or
Australian idiom, which a three-class RoBERTa classifier cannot read and an instruction-tuned
model can (D-063). It annotates; it never overwrites `sentiment_label` (brief Q2), so Wave 5
stays reproducible for a reviewer who never starts Ollama.

Scope (D-024, owner chose B on 30 Oct 2026):
  b      857 comments - every polarity flip, plus every case where the rating is neutral.
         Under D-004 the sentiment label only changes whether a row counts as negative when
         the rating is not 1-2, so these are the cells that can move a reported number, plus
         both sarcasm corners. 0.86 h at the measured rate.
  all    1,887 - every disagreement. 1.89 h, 94% of the 2-hour cut-off.
  flips  350 - the sarcasm corners only.

D-013 keeps Docker in the owner's hands. This module only makes HTTP calls to a container the
owner already started, and fails with a clear message if nothing is listening.

Usage:
    python -m src.llm_review --pilot 20          # D-011 cut-off measurement, writes nothing
    python -m src.llm_review --run --scope b     # the owner-approved scope
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import time
from pathlib import Path

import pandas as pd
import requests
import yaml

ROOT = Path(__file__).resolve().parents[1]
CONFIG = yaml.safe_load((ROOT / "config.yaml").read_text(encoding="utf-8"))

SEED = CONFIG["seed"]
LLM = CONFIG["models"]["llm"]
HOST = LLM["host"].rstrip("/")
CACHE_FILE = ROOT / CONFIG["paths"]["llm_cache"] / "llm_sentiment.jsonl"
CLASSIFIED = ROOT / CONFIG["paths"]["clean"] / "feedback_classified.parquet"
PROMPT_FILE = ROOT / "prompts" / "sentiment_v1.md"
PROMPT_VERSION = "sentiment_v1"
REPORT = ROOT / "reports" / "llm_review.md"

MAX_HOURS = CONFIG["thresholds"]["llm_max_projected_hours"]
SCORE_CLASSES = {1: "negative", 2: "negative", 3: "neutral", 4: "positive", 5: "positive"}
LABELS = {"negative", "neutral", "positive"}
FLUSH_EVERY = 20


def load_prompt() -> str:
    """The template is the first fenced block in the approved prompt file."""
    text = PROMPT_FILE.read_text(encoding="utf-8")
    try:
        start = text.index("```text") + len("```text")
        end = text.index("```", start)
    except ValueError:  # pragma: no cover - the prompt file is committed
        sys.exit(f"No fenced template found in {PROMPT_FILE}")
    template = text[start:end].strip()
    if "{comment}" not in template:
        sys.exit("The prompt template has no {comment} placeholder")
    return template


def cache_key(comment: str) -> str:
    """Includes the prompt version, so a v2 prompt can never reuse v1's answers."""
    material = f"{PROMPT_VERSION}\x00{LLM['name']}\x00{comment}"
    return hashlib.sha256(material.encode()).hexdigest()


class LlmCache:
    """Append-only JSONL, committed. Keyed by prompt version + model + text hash.

    Flushed every FLUSH_EVERY records rather than once at the end: a fifty-minute run that
    writes nothing until it finishes loses everything if the laptop sleeps.
    """

    FIELDS = ("key", "prompt", "model", "sentiment", "sarcasm", "raw", "eval_count", "seconds")

    def __init__(self, path: Path) -> None:
        self.path = path
        self.entries: dict[str, dict] = {}
        if path.exists():
            for line in path.read_text(encoding="utf-8").splitlines():
                if line.strip():
                    record = json.loads(line)
                    self.entries[record["key"]] = record
        self._pending: list[dict] = []

    def get(self, comment: str) -> dict | None:
        return self.entries.get(cache_key(comment))

    def put(self, comment: str, payload: dict) -> None:
        record = {
            "key": cache_key(comment),
            "prompt": PROMPT_VERSION,
            "model": LLM["name"],
            "sentiment": payload.get("sentiment"),
            "sarcasm": payload.get("sarcasm"),
            "raw": payload.get("raw"),
            "eval_count": payload.get("eval_count"),
            "seconds": payload.get("seconds"),
        }
        self.entries[record["key"]] = record
        self._pending.append(record)

    def flush(self) -> int:
        if not self._pending:
            return 0
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as f:
            for record in self._pending:
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
        count = len(self._pending)
        self._pending = []
        return count


def disagreements(df: pd.DataFrame) -> pd.DataFrame:
    """Commented rows where the rating's class differs from the model's label."""
    commented = df[df["comment"].notna() & df["sentiment_label"].notna()].copy()
    commented["score_class"] = commented["rating_1to5"].map(SCORE_CLASSES)
    out = commented[commented["score_class"] != commented["sentiment_label"]].copy()
    flip = {("negative", "positive"), ("positive", "negative")}
    out["kind"] = [
        "flip" if (s, m) in flip else "adjacent"
        for s, m in zip(out["score_class"], out["sentiment_label"], strict=True)
    ]
    return out.sort_values("feedback_id").reset_index(drop=True)


def select_scope(df: pd.DataFrame, scope: str) -> pd.DataFrame:
    if scope == "all":
        return df
    if scope == "flips":
        return df[df["kind"] == "flip"]
    # Scope B: every flip, plus every case where the customer's rating is neutral. Under
    # D-004 the sentiment label only decides negative status when the rating is not 1-2.
    return df[(df["kind"] == "flip") | (df["score_class"] == "neutral")]


def parse(raw: str) -> dict:
    """A parse failure is recorded, never silently dropped (brief step 6)."""
    match = re.search(r"\{.*?\}", raw, re.DOTALL)
    if not match:
        return {"sentiment": None, "sarcasm": None, "raw": raw[:160]}
    try:
        obj = json.loads(match.group(0))
    except json.JSONDecodeError:
        return {"sentiment": None, "sarcasm": None, "raw": raw[:160]}
    label = str(obj.get("sentiment", "")).strip().lower()
    if label not in LABELS:
        return {"sentiment": None, "sarcasm": None, "raw": raw[:160]}
    return {"sentiment": label, "sarcasm": bool(obj.get("sarcasm", False)), "raw": None}


def ask(template: str, comment: str, timeout: int = 120) -> dict:
    """One call. Returns the parsed verdict plus its cost. Raises on transport failure."""
    body = {
        "model": LLM["name"],
        "prompt": template.replace("{comment}", comment),
        "stream": False,
        "options": {"temperature": 0, "seed": SEED, "num_predict": 24},
    }
    started = time.perf_counter()
    reply = requests.post(f"{HOST}/api/generate", json=body, timeout=timeout)
    elapsed = time.perf_counter() - started
    reply.raise_for_status()
    payload = reply.json()
    verdict = parse(payload.get("response", ""))
    verdict["eval_count"] = int(payload.get("eval_count", 0))
    verdict["seconds"] = round(elapsed, 2)
    return verdict


def check_host() -> None:
    try:
        tags = requests.get(f"{HOST}/api/tags", timeout=10).json()
    except requests.RequestException as exc:
        sys.exit(
            f"Cannot reach Ollama at {HOST}: {exc}\n"
            "The owner starts it (D-013): docker compose up -d"
        )
    names = [m.get("name", "") for m in tags.get("models", [])]
    if not any(n.startswith(LLM["name"]) for n in names):
        sys.exit(f"{LLM['name']} not loaded. Found: {names or 'nothing'}")


def write_report(df: pd.DataFrame, scope: str, elapsed: float) -> None:
    """Three signals compared, the sarcasm rate, and the failure cases for Checkpoint 4."""
    done = df[df["llm_sentiment"].notna()]
    failures = df[df["llm_sentiment"].isna()]
    agrees_rating = (done["llm_sentiment"] == done["score_class"]).sum()
    agrees_model = (done["llm_sentiment"] == done["sentiment_label"]).sum()
    neither = len(done) - agrees_rating - agrees_model
    sarcasm = int(done["llm_sarcasm"].fillna(False).astype(bool).sum())

    lines = [
        "# LLM adjudication — full run",
        "",
        f"**Scope {scope.upper()}**: {len(df)} comments, run 30 Oct 2026. "
        f"`{LLM['name']}` (Ollama ID `{LLM['ollama_model_id']}`), prompt `{PROMPT_VERSION}`, "
        "`temperature 0`, `seed 42`, `num_predict 24`.",
        f"**Wall clock:** {elapsed / 60:.1f} minutes "
        f"({elapsed / max(1, len(df)):.2f} s/comment) against D-011's {MAX_HOURS}-hour cut-off.",
        "",
        "Scope B is every polarity flip plus every case where the customer's rating is "
        "neutral. Under D-004 the sentiment label only decides whether a row counts as "
        "negative when the rating is not 1–2, so these are the cells that can move a "
        "reported number, plus both sarcasm corners. D-024.",
        "",
        "## Which signal the LLM sided with",
        "",
        "| | Count | Share |",
        "|---|---:|---:|",
        f"| The customer's rating | {agrees_rating} | {agrees_rating / len(done) * 100:.1f}% |",
        f"| The deterministic model | {agrees_model} | {agrees_model / len(done) * 100:.1f}% |",
        f"| Neither | {neither} | {neither / len(done) * 100:.1f}% |",
        "",
        f"**Sarcasm reported in {sarcasm} of {len(done)} ({sarcasm / len(done) * 100:.1f}%).** "
        "That figure is the justification for this agent: it is the share of the "
        "disagreement that irony explains, rather than the deterministic model simply being "
        "wrong.",
        "",
        f"**Parse failures: {len(failures)} of {len(df)}.** Recorded, never dropped.",
        "",
        "## By disagreement cell",
        "",
        "| Rating | Model | LLM negative | LLM neutral | LLM positive | n |",
        "|---|---|---:|---:|---:|---:|",
    ]
    for (score, model), group in done.groupby(["score_class", "sentiment_label"]):
        counts = group["llm_sentiment"].value_counts()
        lines.append(
            f"| {score} | {model} | {counts.get('negative', 0)} | {counts.get('neutral', 0)} "
            f"| {counts.get('positive', 0)} | {len(group)} |"
        )

    lines += [
        "",
        "## What this does NOT do",
        "",
        "It does not change `sentiment_label` (brief Q2). Every headline number in Wave 5 "
        "still comes from the deterministic model, so a reviewer who never starts Ollama "
        "reproduces them exactly. And it is not an evaluation: under D-017 this agent does "
        "not grade itself, and if the LLM and the owner's blind labels disagree, the owner's "
        "labels are correct (brief Q3).",
        "",
        "## Failure cases for Checkpoint 4",
        "",
        "Comments where the LLM disagreed with **both** other signals, or returned "
        "unparseable output. The owner reads about 20 of these.",
        "",
    ]
    odd = done[
        (done["llm_sentiment"] != done["score_class"])
        & (done["llm_sentiment"] != done["sentiment_label"])
    ]
    for _, row in pd.concat([failures, odd]).head(20).iterrows():
        verdict = row["llm_sentiment"] if pd.notna(row["llm_sentiment"]) else "UNPARSEABLE"
        lines += [
            f"**rating {row['rating_1to5']} ({row['score_class']}) · "
            f"model {row['sentiment_label']} · llm {verdict}**",
            "",
            f"> {row['comment']}",
            "",
        ]

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    ap = argparse.ArgumentParser(description="LLM adjudication of rating/sentiment conflicts")
    ap.add_argument("--pilot", type=int, default=0, metavar="N",
                    help="D-011 cut-off measurement: time N comments, write nothing")
    ap.add_argument("--run", action="store_true", help="run the scope and cache the results")
    ap.add_argument("--scope", choices=("b", "all", "flips"), default="b",
                    help="b (default, owner-approved D-024), all, or flips")
    args = ap.parse_args()

    if not CLASSIFIED.exists():
        sys.exit(f"{CLASSIFIED} not found. Run `make classify` first.")
    check_host()

    template = load_prompt()
    everything = disagreements(pd.read_parquet(CLASSIFIED))
    df = select_scope(everything, args.scope).copy()

    counts = df["kind"].value_counts().to_dict()
    print(f"scope {args.scope}: {len(df)} of {len(everything)} disagreements "
          f"({counts.get('flip', 0)} flips, {counts.get('adjacent', 0)} adjacent)")
    print(f"model {LLM['name']} at {HOST}, prompt {PROMPT_VERSION}")
    print()

    if args.pilot:
        cell = df["score_class"] + "->" + df["sentiment_label"]
        per = max(1, args.pilot // max(1, cell.nunique()))
        sample = (
            df.assign(cell=cell)
            .groupby("cell", group_keys=False)
            .apply(lambda g: g.sample(n=min(per, len(g)), random_state=SEED), include_groups=False)
            .head(args.pilot)
        )
        print(f"PILOT (G1, D-011): {len(sample)} comments, stratified across cells")
        print()
        seconds = 0.0
        for _, row in sample.iterrows():
            verdict = ask(template, row["comment"])
            seconds += verdict["seconds"]
            print(f"  {verdict['seconds']:5.1f}s  rating {row['rating_1to5']} / "
                  f"model {row['sentiment_label']:8s} -> llm {str(verdict['sentiment']):8s} "
                  f"sarcasm={verdict['sarcasm']}")
        per_comment = seconds / len(sample)
        projected = per_comment * len(df) / 3600
        print()
        print(f"measured {per_comment:.2f} s/comment -> {projected:.2f} h for {len(df)} "
              f"(cut-off {MAX_HOURS}h)")
        print("Pilot writes nothing. Owner decides D-024.")
        return 0

    if not args.run:
        print("Nothing to do. Pass --pilot N to measure, or --run to run the scope.")
        return 0

    cache = LlmCache(CACHE_FILE)
    todo = [c for c in df["comment"] if cache.get(c) is None]
    print(f"{len(df) - len(todo)} already cached, {len(todo)} to ask")
    print()

    started = time.perf_counter()
    for number, comment in enumerate(todo, start=1):
        try:
            cache.put(comment, ask(template, comment))
        except requests.RequestException as exc:
            print(f"  ! transport failure at {number}: {exc}")
            cache.flush()
            print(f"  flushed {number - 1} verdicts; rerun to resume from the cache")
            return 1
        if number % FLUSH_EVERY == 0:
            cache.flush()
            rate = (time.perf_counter() - started) / number
            remaining = rate * (len(todo) - number) / 60
            print(f"  {number}/{len(todo)}  {rate:.2f}s/comment  ~{remaining:.0f} min left")
    cache.flush()
    elapsed = time.perf_counter() - started

    verdicts = [cache.get(c) or {} for c in df["comment"]]
    df["llm_sentiment"] = [v.get("sentiment") for v in verdicts]
    df["llm_sarcasm"] = [v.get("sarcasm") for v in verdicts]
    write_report(df, args.scope, elapsed)

    print()
    print(f"done in {elapsed / 60:.1f} min -> {REPORT.relative_to(ROOT)}")
    print(f"  cached: {len(cache.entries)} verdicts in {CACHE_FILE.relative_to(ROOT)}")
    failures = int(df["llm_sentiment"].isna().sum())
    print(f"  parse failures: {failures} of {len(df)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

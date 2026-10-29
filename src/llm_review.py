"""Wave 4: a local LLM adjudicates rating/sentiment disagreements.

Brief: `agents/briefs/w4_llm.md`. Prompt: `prompts/sentiment_v1.md` (v1, owner-approved,
Checkpoint 4). Model: `qwen2.5:3b` pinned by Ollama ID in `config.yaml` (D-012).

This runs only where the deterministic sentiment model and the customer's own star rating
disagree. Every one of the eight such cases sampled in the classifier pilot was sarcasm or
Australian idiom, which a three-class RoBERTa classifier cannot read and an instruction-tuned
model can. It annotates; it never overwrites `sentiment_label` (brief Q2), so Wave 5 stays
reproducible for a reviewer who never starts Ollama.

D-013 keeps Docker in the owner's hands. This module only makes HTTP calls to a container the
owner already started, and fails with a clear message if nothing is listening.

Usage:
    python -m src.llm_review --pilot 20      # D-011 cut-off measurement, timed
    python -m src.llm_review --all           # the full disagreement set
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
CACHE = ROOT / CONFIG["paths"]["llm_cache"] / "llm_sentiment.jsonl"
CLASSIFIED = ROOT / CONFIG["paths"]["clean"] / "feedback_classified.parquet"
PROMPT_FILE = ROOT / "prompts" / "sentiment_v1.md"
PROMPT_VERSION = "sentiment_v1"
REPORT = ROOT / "reports" / "llm_review.md"

MAX_HOURS = CONFIG["thresholds"]["llm_max_projected_hours"]
SCORE_CLASSES = {1: "negative", 2: "negative", 3: "neutral", 4: "positive", 5: "positive"}
LABELS = {"negative", "neutral", "positive"}


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
    return out


def ask(template: str, comment: str, timeout: int = 120) -> tuple[dict, int, float]:
    """One call. Returns (parsed, eval_count, seconds). Raises on transport failure."""
    body = {
        "model": LLM["name"],
        "prompt": template.replace("{comment}", comment),
        "stream": False,
        "options": {"temperature": 0, "seed": SEED, "num_predict": 24},
    }
    t0 = time.perf_counter()
    reply = requests.post(f"{HOST}/api/generate", json=body, timeout=timeout)
    elapsed = time.perf_counter() - t0
    reply.raise_for_status()
    payload = reply.json()
    return parse(payload.get("response", "")), int(payload.get("eval_count", 0)), elapsed


def parse(raw: str) -> dict:
    """A parse failure is recorded, never silently dropped (brief step 6)."""
    match = re.search(r"\{.*?\}", raw, re.DOTALL)
    if not match:
        return {"sentiment": None, "sarcasm": None, "parse_error": raw[:120]}
    try:
        obj = json.loads(match.group(0))
    except json.JSONDecodeError:
        return {"sentiment": None, "sarcasm": None, "parse_error": raw[:120]}
    label = str(obj.get("sentiment", "")).strip().lower()
    if label not in LABELS:
        return {"sentiment": None, "sarcasm": None, "parse_error": raw[:120]}
    return {"sentiment": label, "sarcasm": bool(obj.get("sarcasm", False))}


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


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    ap = argparse.ArgumentParser(description="LLM adjudication of rating/sentiment conflicts")
    ap.add_argument("--pilot", type=int, default=20, metavar="N",
                    help="D-011 cut-off measurement: time N comments and project (default 20)")
    ap.add_argument("--all", action="store_true", help="run the full disagreement set")
    ap.add_argument("--flips-only", action="store_true",
                    help="fall back to polarity flips only, if the projection blows the budget")
    args = ap.parse_args()

    if not CLASSIFIED.exists():
        sys.exit(f"{CLASSIFIED} not found. Run `make classify` first.")
    check_host()

    template = load_prompt()
    df = disagreements(pd.read_parquet(CLASSIFIED))
    if args.flips_only:
        df = df[df["kind"] == "flip"]

    counts = df["kind"].value_counts().to_dict()
    print(f"disagreement set: {len(df)} comments "
          f"({counts.get('flip', 0)} flips, {counts.get('adjacent', 0)} adjacent)")
    print(f"model {LLM['name']} at {HOST}, prompt {PROMPT_VERSION}")
    print()

    if not args.all:
        # Stratify the pilot across the disagreement cells so timing is not measured on
        # one easy corner (brief Pilot section).
        cell = df["score_class"] + "->" + df["sentiment_label"]
        per = max(1, args.pilot // max(1, cell.nunique()))
        sample = (
            df.assign(cell=cell)
            .groupby("cell", group_keys=False)
            .apply(lambda g: g.sample(n=min(per, len(g)), random_state=SEED), include_groups=False)
        )
        sample = sample.head(args.pilot)
        print(f"PILOT (G1, D-011): {len(sample)} comments, stratified across cells")
        print()

        tokens = 0
        seconds = 0.0
        sarcasm = 0
        failures = 0
        for _, row in sample.iterrows():
            parsed, count, elapsed = ask(template, row["comment"])
            tokens += count
            seconds += elapsed
            sarcasm += bool(parsed.get("sarcasm"))
            failures += parsed.get("sentiment") is None
            flag = "!" if parsed.get("sentiment") is None else " "
            print(f"  {flag} {elapsed:5.1f}s {count:3d}tok  "
                  f"rating {row['rating_1to5']} / model {row['sentiment_label']:8s} -> "
                  f"llm {str(parsed.get('sentiment')):8s} "
                  f"sarcasm={parsed.get('sarcasm')}")

        n = len(sample)
        per_comment = seconds / n
        rate = tokens / seconds if seconds else 0
        projected = per_comment * len(df) / 3600
        print()
        print(f"measured: {per_comment:.2f} s/comment, {rate:.2f} tokens/s, "
              f"{tokens / n:.1f} tokens/comment")
        print(f"parse failures: {failures} of {n} | sarcasm reported: {sarcasm} of {n}")
        print()
        print(f"projection for {len(df)} comments: {projected:.2f} hours "
              f"(cut-off {MAX_HOURS}h, D-011)")
        if projected <= MAX_HOURS:
            print("  VERDICT: inside the cut-off. The full run may go ahead at this scope.")
        else:
            flips = int(counts.get("flip", 0))
            print("  VERDICT: OVER the cut-off. Do not move it (PLAN.md section 9).")
            print(f"  Fall back to --flips-only: {flips} comments, "
                  f"{per_comment * flips / 3600:.2f} hours.")
        print()
        print("Owner decides D-024 from this. Nothing cached; the pilot writes nothing.")
        return 0

    print("Full run not implemented until the owner has seen the pilot projection (D-024).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

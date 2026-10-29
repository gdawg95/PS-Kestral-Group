"""Can the Wave 4 models load and run here? One line per model, plus a timing estimate.

`make nlp-check` (or `uv run python scripts/check_nlp_env.py`). Nothing here is cached or
written into the pipeline: this script only answers the question PLAN.md's Wave 1 NLP
environment check asked, for the two models `config.yaml` names, on the machine that will
actually run them (D-013: the laptop is the reference environment).

The first run downloads the weights (roughly 500 MB for the sentiment model, 90 MB for the
embedding model) into the Hugging Face cache, so it needs the network. Every later run is
offline. Run it once before Wave 4 so a 500 MB download is not the thing standing between
you and an overnight classification run.

Exit code 0 means both models loaded and produced output. 1 means Wave 4 cannot start.
"""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
CONFIG = yaml.safe_load((ROOT / "config.yaml").read_text(encoding="utf-8"))

# Two sentences from the real shape of the data: one plainly negative, one plainly positive.
PROBES = [
    "Waited over two hours past the booked time and nobody called to explain.",
    "Service was quick and the price was exactly what they quoted.",
]
# Comments in the dataset that Wave 4 has to classify (5,362 at the time of writing).
CORPUS_SIZE = 5362


def _cache_dir() -> Path:
    return Path(os.environ.get("HF_HOME", Path.home() / ".cache" / "huggingface"))


def _size_mb(path: Path) -> float:
    if not path.exists():
        return 0.0
    return sum(f.stat().st_size for f in path.rglob("*") if f.is_file()) / 1e6


def check_sentiment(tag: str) -> tuple[bool, str]:
    try:
        from transformers import pipeline
    except Exception as exc:  # noqa: BLE001
        return False, f"transformers will not import: {exc}"
    try:
        t0 = time.perf_counter()
        clf = pipeline("sentiment-analysis", model=tag, device=-1)
        load = time.perf_counter() - t0
        t1 = time.perf_counter()
        out = clf(PROBES)
        per = (time.perf_counter() - t1) / len(PROBES)
    except Exception as exc:  # noqa: BLE001
        return False, f"{type(exc).__name__}: {exc}"
    labels = ", ".join(f"{o['label']} {o['score']:.2f}" for o in out)
    projected = per * CORPUS_SIZE / 60
    return True, (
        f"loaded in {load:.1f}s · {per * 1000:.0f} ms/comment on CPU · "
        f"{labels} · {CORPUS_SIZE} comments ~ {projected:.0f} min"
    )


def check_embeddings(tag: str) -> tuple[bool, str]:
    try:
        from sentence_transformers import SentenceTransformer
    except Exception as exc:  # noqa: BLE001
        return False, f"sentence-transformers will not import: {exc}"
    try:
        t0 = time.perf_counter()
        model = SentenceTransformer(tag, device="cpu")
        load = time.perf_counter() - t0
        t1 = time.perf_counter()
        vecs = model.encode(PROBES)
        per = (time.perf_counter() - t1) / len(PROBES)
    except Exception as exc:  # noqa: BLE001
        return False, f"{type(exc).__name__}: {exc}"
    projected = per * CORPUS_SIZE / 60
    return True, (
        f"loaded in {load:.1f}s · {vecs.shape[1]}-dim vectors · {per * 1000:.0f} ms/comment · "
        f"{CORPUS_SIZE} comments ~ {projected:.0f} min"
    )


def check_bertopic() -> tuple[bool, str]:
    try:
        import bertopic
    except Exception as exc:  # noqa: BLE001
        return False, f"will not import: {exc}"
    return True, f"bertopic {bertopic.__version__} imports (theme discovery, Wave 4)"


def check_spacy(tag: str) -> tuple[bool, str]:
    try:
        import spacy

        spacy.load(tag)
    except Exception as exc:  # noqa: BLE001
        return False, f"{type(exc).__name__}: {exc}"
    return True, f"{tag} loads (PII redaction, already used in Wave 2)"


def main() -> int:
    # A plain Windows console is cp1252 and cannot encode the characters in these lines,
    # which crashed the first run of this script after every check had already passed.
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    models = CONFIG["models"]
    cache = _cache_dir()
    print("Wave 4 model check")
    print(f"  python {sys.version.split()[0]}  ·  HF cache {cache} ({_size_mb(cache):.0f} MB)")
    print()

    results = [
        ("sentiment", models["sentiment"], *check_sentiment(models["sentiment"])),
        ("embeddings", models["embeddings"], *check_embeddings(models["embeddings"])),
        ("themes", "bertopic", *check_bertopic()),
        ("pii", models["spacy"], *check_spacy(models["spacy"])),
    ]

    width = max(len(r[0]) for r in results)
    for name, tag, ok, detail in results:
        print(f"  {'PASS' if ok else 'FAIL'}  {name:<{width}}  {tag}")
        print(f"        {detail}")
    print()
    print(f"  HF cache after this run: {_size_mb(cache):.0f} MB")

    # The LLM step is optional (D-011, cut list item 5) and is the owner's to run.
    print()
    print("  Not checked here: Ollama. `docker compose up` then "
          "`curl http://localhost:11434/api/tags` — the owner runs Docker (D-013).")

    failed = [name for name, _tag, ok, _d in results if not ok]
    if failed:
        print(f"\n  VERDICT: Wave 4 cannot start — {', '.join(failed)} unavailable.")
        return 1
    print("\n  VERDICT: Wave 4 can run on this machine.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

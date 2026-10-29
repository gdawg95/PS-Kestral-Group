# Pipeline runner (PLAN.md section 6). `make all` runs every stage in order.
# The owner's laptop has no `make`; scripts/run.ps1 mirrors these targets in PowerShell.
# Reviewers on macOS/Linux can use this file directly.

PY := uv run python
PYTEST := uv run pytest

.PHONY: all ingest validate classify analyse figures test lint hooks nlp-check gitleaks clean

all: ingest validate classify analyse figures

ingest:            ## raw files -> data/interim/consolidated.parquet (Wave 2)
	$(PY) -m src.ingest

validate:          ## pandera rules + data-quality report (Wave 3)
	$(PY) -m src.validate

classify:          ## sentiment + theme assignment, cached (Wave 4). FRESH=1 re-runs the models
	$(PY) -m src.classify $(if $(FRESH),--fresh,)

analyse:           ## drivers, trend, coverage, value model (Wave 5)
	$(PY) -m src.analyse

figures:           ## charts for both reports (Wave 5)
	$(PY) -m src.figures

test:
	$(PYTEST) -q

lint:
	uv run ruff check . && uv run ruff format --check .

hooks:             ## install the pre-commit hooks into .git/hooks
	uv run pre-commit install

nlp-check:         ## can the sentiment and embedding models load here? (laptop only)
	$(PY) scripts/check_nlp_env.py

gitleaks:          ## pre-public secret scan of full history (D-015); needs gitleaks on PATH
	gitleaks detect --source . --log-opts="--all" --redact

clean:             ## remove derived data, keep raw and the committed model cache
	rm -rf data/interim data/clean reports/figures/*.png

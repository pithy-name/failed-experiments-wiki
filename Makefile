# Failed-experiments wiki: one-command entry points.
# Run from the repository root. `make setup` once, then any target.

PYTHON ?= python3.11
PY     := .venv/bin/python
PORT   ?= 8001
HANDLE ?=

.PHONY: help setup test validate validate-gold site db datasette evals sync-gold scout facets

help:
	@echo "make setup          create .venv and install everything"
	@echo "make test           run the test suite"
	@echo "make validate       validate every entry (fetches sources to check quotes)"
	@echo "make validate-gold  validate the gold entries in evals/gold/"
	@echo "make site           build site/index.html (the static browse page)"
	@echo "make db             build wiki.db from entries/"
	@echo "make datasette      build wiki.db and serve it with Datasette on PORT (default 8001)"
	@echo "make evals          re-score saved skill outputs against the gold set -> evals/results/"
	@echo "make sync-gold HANDLE=<github handle>   publish verified gold entries into entries/"
	@echo "make scout          re-run the candidate search (cached, rate-limited)"

setup:
	$(PYTHON) -m venv .venv
	$(PY) -m pip install -r requirements-dev.txt

test:
	$(PY) -m pytest -q

validate:
	$(PY) tools/validate.py

validate-gold:
	$(PY) tools/validate.py --gold

site:
	$(PY) tools/build_site.py

db:
	$(PY) tools/build_db.py

datasette:
	$(PY) tools/build_db.py --serve --port $(PORT)

evals:
	$(PY) evals/run_evals.py

sync-gold:
	$(PY) tools/sync_gold.py --handle "$(HANDLE)"

scout:
	$(PY) tools/scout/search_candidates.py

facets:
	$(PY) tools/cli.py facets

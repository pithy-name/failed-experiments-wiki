# Failed-experiments wiki: one-command entry points.
# Run from the repository root. `make setup` once, then any target.

PYTHON ?= python3.11
PY     := .venv/bin/python
PORT   ?= 8001
HANDLE ?=

.PHONY: help setup test validate validate-gold site db datasette datasette-check mcp-smoke check-facts demo-script demo-setup demo-video set-handle evals sync-gold scout facets

help:
	@echo "make setup          create .venv and install everything"
	@echo "make test           run the test suite"
	@echo "make validate       validate every entry (fetches sources to check quotes)"
	@echo "make validate-gold  validate the gold entries in evals/gold/"
	@echo "make site           build site/index.html (the static browse page)"
	@echo "make db             build wiki.db from entries/"
	@echo "make datasette      build wiki.db and serve it with Datasette on PORT (default 8001)"
	@echo "make datasette-check  list and filter the wiki through Datasette without opening a port"
	@echo "make mcp-smoke      start the MCP server as the plugin does and call it over stdio"
	@echo "make check-facts    check that every number and model name in an entry occurs in its post"
	@echo "make demo-script    write demo/script.md from demo/scenes.yaml"
	@echo "make demo-setup     install what the demo video needs (Playwright and its headless browser)"
	@echo "make demo-video     build demo/out/demo-draft.mp4 (needs ffmpeg; the voice needs macOS say, outside the sandbox)"
	@echo "make evals          re-score saved skill outputs against the gold set -> evals/results/"
	@echo "make sync-gold HANDLE=<github handle>   publish verified gold entries into entries/"
	@echo "make set-handle HANDLE=<github handle>  replace the HANDLE-TBD placeholder in the seed entries"
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

datasette-check:
	$(PY) tools/datasette_check.py

mcp-smoke:
	$(PY) tools/mcp_smoke.py

check-facts:
	$(PY) tools/check_facts.py

demo-script:
	$(PY) demo/build_demo.py --script-only

demo-setup:
	$(PY) -m pip install -r requirements-demo.txt
	$(PY) -m playwright install chromium-headless-shell

demo-video:
	$(PY) demo/build_demo.py

evals:
	$(PY) evals/run_evals.py

sync-gold:
	$(PY) tools/sync_gold.py --handle "$(HANDLE)"

set-handle:
	$(PY) tools/set_handle.py "$(HANDLE)"

scout:
	$(PY) tools/scout/search_candidates.py

facets:
	$(PY) tools/cli.py facets

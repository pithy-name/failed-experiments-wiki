#!/bin/sh
# Start the wiki's MCP server over stdio.
# Python is taken from FEWIKI_PYTHON, else the repo's .venv, else python3 on PATH.
# The interpreter needs: fastmcp, PyYAML, jsonschema (pip install -r requirements-dev.txt).
here="$(cd "$(dirname "$0")" && pwd)"
repo="${FEWIKI_REPO:-$(cd "$here/../.." && pwd)}"
if [ -n "$FEWIKI_PYTHON" ]; then
  python="$FEWIKI_PYTHON"
elif [ -x "$repo/.venv/bin/python" ]; then
  python="$repo/.venv/bin/python"
else
  python="python3"
fi
FEWIKI_REPO="$repo" exec "$python" "$here/server.py"

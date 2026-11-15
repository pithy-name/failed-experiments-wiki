"""Show that Datasette lists and filters the real wiki, without opening a port.

  python tools/datasette_check.py        (or: make datasette-check)

Rebuilds wiki.db, then runs Datasette in its in-process request mode
(`datasette --get`) for a listing, a facet page and one filter of each kind.
Useful where a server cannot be started, and as a quick end-to-end check.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_db  # noqa: E402
import wikilib  # noqa: E402

QUERIES = [
    ("every entry", "/wiki/entries.json?_shape=array&_col=id"),
    ("badge: agent-written (array filter)", "/wiki/entries.json?_shape=array&_col=id&badges__arraycontains=agent-written"),
    ("failure_type = hypothesis_false AND method contains sae", "/wiki/entries.json?_shape=array&_col=id&failure_type=hypothesis_false&method__arraycontains=sae"),
    ("retry_welcome = 1 (boolean)", "/wiki/entries.json?_shape=array&_col=id&retry_welcome=1"),
    ("source published on or after 2026-01-01 (date range)", "/wiki/entries.json?_shape=array&_col=id&source_published__gte=2026-01-01"),
    ("result n at least 100 (number range)", "/wiki/entries.json?_shape=array&_col=id&result_n__gte=100"),
    ("contributor.type = human", "/wiki/entries.json?_shape=array&_col=id&contributor_type=human"),
    ("full-text search: steganography", "/wiki/entries.json?_shape=array&_col=id&_search=steganography"),
]


def get(datasette: str, path: str):
    completed = subprocess.run(
        [datasette, str(build_db.DEFAULT_DB), "--metadata", str(build_db.METADATA_PATH), "--get", path],
        capture_output=True, text=True, timeout=180,
    )
    if completed.returncode != 0:
        raise SystemExit(f"datasette failed for {path}:\n{completed.stderr[-600:]}")
    return json.loads(completed.stdout)


def main() -> int:
    datasette = build_db.find_datasette()
    if not datasette:
        print("datasette is not installed: pip install -r requirements-dev.txt", file=sys.stderr)
        return 1
    outcome = build_db.build(wikilib.ENTRIES_DIR, build_db.DEFAULT_DB)
    build_db.write_metadata()
    print(f"wiki.db rebuilt with {outcome['entries']} entries\n")
    for label, path in QUERIES:
        ids = [row["id"] for row in get(datasette, path)]
        print(f"{label}: {len(ids)}\n    {', '.join(ids) or '(none)'}")
    facets = get(datasette, "/wiki/entries.json")["facet_results"]
    facets = facets.get("results", facets)
    print("\nfacets shown by default:", ", ".join(sorted(facets)))
    for name in ("failure_type", "badges", "review_status", "contributor_type"):
        counts = {item["value"]: item["count"] for item in facets[name]["results"]}
        print(f"    {name}: {counts}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

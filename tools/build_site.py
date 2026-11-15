"""Build the static browse page (D4): entries/ -> site/index.html.

  python tools/build_site.py [--entries DIR] [--out FILE] [--repo-url URL]

One self-contained HTML file: inline CSS and JavaScript, entry data embedded as
JSON, no external requests. It works when opened from disk.

Every schema field is filterable. The controls are generated from
wikilib.FIELDS: facet fields get checkbox lists with counts, number and date
fields get from/to inputs, and text fields are covered by the search box. A
field added to FIELDS gets its control without any change to the JavaScript.
"""
from __future__ import annotations

import argparse
import datetime as dt
import html
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import wikilib  # noqa: E402

ASSETS = Path(__file__).resolve().parent / "site_assets"
DEFAULT_OUT = wikilib.REPO_ROOT / "site" / "index.html"

# Order matters: the filters people reach for first are at the top and open.
GROUPS = [
    {"id": "badges", "label": "Badges", "open": True},
    {"id": "result", "label": "Result and failure", "open": True},
    {"id": "experiment", "label": "Experiment", "open": True},
    {"id": "trust", "label": "Contributor and review", "open": False},
    {"id": "source", "label": "Source", "open": False},
    {"id": "dates", "label": "Dates, links and IDs", "open": False},
]
RESULT_FIELDS = {"failure_type", "confidence_true_negative", "retry_welcome", "evidence_level"}


def group_of(path: str) -> str:
    if path.startswith(("contributor.", "review.")) or path == "info_hazard":
        return "trust"
    if path.startswith("result.") or path in RESULT_FIELDS:
        return "result"
    if path.startswith("source."):
        return "source"
    if path.startswith(("dates.", "related.")) or path == "id":
        return "dates"
    return "experiment"


def control_of(kind: str) -> str:
    if kind in wikilib.FACET_KINDS:
        return "facet"
    if kind in wikilib.RANGE_KINDS:
        return "range"
    return "text"


def label_of(path: str) -> str:
    return path.replace("_", " ").replace(".", " › ")


# Within a group, these fields come first, in this order. The rest follow in schema order.
FIRST_FIELDS = [
    "failure_type", "confidence_true_negative", "retry_welcome", "result.direction", "evidence_level",
    "research_area", "method", "models.name", "benchmarks", "checks_done",
    "review.status", "contributor.type", "contributor.agent_model",
    "source.type", "source.authors", "source.published",
]


def field_catalogue() -> list[dict]:
    """Every schema field with its control, plus the derived badges as a facet."""
    catalogue = [{"path": "badges", "kind": "list", "control": "facet", "group": "badges", "label": "who wrote it · reviewed or not"}]
    for path, kind in wikilib.FIELDS:
        catalogue.append({"path": path, "kind": kind, "control": control_of(kind), "group": group_of(path), "label": label_of(path)})
    position = {field["path"]: index for index, field in enumerate(catalogue)}
    catalogue.sort(key=lambda f: FIRST_FIELDS.index(f["path"]) if f["path"] in FIRST_FIELDS else len(FIRST_FIELDS) + position[f["path"]])
    return catalogue


def github_web_url(remote: str | None) -> str | None:
    """https://github.com/owner/repo from an https or ssh GitHub remote; None for anything else."""
    match = re.match(r"^(?:https://github\.com/|git@github\.com:|ssh://git@github\.com/)([\w.-]+)/([\w.-]+?)(?:\.git)?/?$", remote or "")
    return f"https://github.com/{match.group(1)}/{match.group(2)}" if match else None


def embed_json(payload: dict) -> str:
    """JSON that is safe inside a <script> element: no character can close the tag or start markup."""
    text = json.dumps(payload, ensure_ascii=False)        # key order is kept: "All fields" lists an entry in schema order
    for raw, escaped in (("&", "\\u0026"), ("<", "\\u003c"), (">", "\\u003e"), (" ", "\\u2028"), (" ", "\\u2029")):
        text = text.replace(raw, escaped)
    return text


def build_payload(entries: list[wikilib.Entry], repo_url: str | None) -> dict:
    return {
        "built": dt.date.today().isoformat(),
        "repo_url": repo_url,
        "groups": GROUPS,
        "fields": field_catalogue(),
        "entries": [
            {
                "id": entry.id,
                "data": entry.data,
                "body": entry.body,
                "badges": wikilib.badges(entry.data),
                "file_url": f"{repo_url}/blob/main/entries/{entry.id}.md" if repo_url else f"../entries/{entry.id}.md",
            }
            for entry in entries
        ],
    }


def render(payload: dict) -> str:
    css = (ASSETS / "style.css").read_text(encoding="utf-8")
    filter_js = (ASSETS / "filter.js").read_text(encoding="utf-8")
    app_js = (ASSETS / "app.js").read_text(encoding="utf-8")
    for name, source in (("filter.js", filter_js), ("app.js", app_js)):
        if "</script" in source.lower():
            raise ValueError(f"{name} must not contain a closing script tag")
    if payload["repo_url"]:
        remote_note = f'Source: <a href="{html.escape(payload["repo_url"], quote=True)}">{html.escape(payload["repo_url"])}</a>.'
    else:
        remote_note = "No GitHub remote is configured yet, so entry links point to the local files."
    count = len(payload["entries"])
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Failed-experiments wiki</title>
<style>
{css}
</style>
</head>
<body>
<header class="site">
  <h1>Failed-experiments wiki</h1>
  <p>AI-safety experiments that did not work, from LessWrong and the Alignment Forum, so the next attempt can be less wrong than the last.</p>
  <p>Entries describe experiments. They never judge people. Entries written by an AI agent, and entries nobody has reviewed yet, are labelled.</p>
</header>
<div class="layout">
  <aside aria-label="Filters">
    <div id="filters"></div>
  </aside>
  <main>
    <div class="toolbar">
      <input id="search" type="search" placeholder="Search every field…" aria-label="Search every field">
      <span id="count" role="status">{count} entries</span>
      <button id="clear" type="button" disabled>Clear all filters</button>
    </div>
    <div id="results"></div>
    <noscript><p>This page needs JavaScript to filter entries. The entries are plain Markdown files in <code>entries/</code>.</p></noscript>
  </main>
</div>
<footer class="site">
  <p>{count} entries. Built {html.escape(payload["built"])} by <code>tools/build_site.py</code>. {remote_note}</p>
  <p>A filter that matches nothing means nobody has filed an entry, not that an idea is untested.</p>
</footer>
<script type="application/json" id="fewiki-data">{embed_json(payload)}</script>
<script>
{filter_js}
</script>
<script>
{app_js}
</script>
</body>
</html>
"""


def build(entries_dir: Path, out_path: Path, repo_url: str | None = None) -> dict:
    entries = wikilib.load_entries(entries_dir)
    payload = build_payload(entries, repo_url)
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(render(payload), encoding="utf-8")
    return {"entries": len(entries), "out": str(out_path), "repo_url": repo_url}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build the static browse page.")
    parser.add_argument("--entries", default=str(wikilib.ENTRIES_DIR))
    parser.add_argument("--out", default=str(DEFAULT_OUT))
    parser.add_argument("--repo-url", help="GitHub repository URL for entry links (default: the origin remote, if it is on GitHub)")
    args = parser.parse_args(argv)
    repo_url = github_web_url(args.repo_url) if args.repo_url else github_web_url(wikilib.remote_url(wikilib.REPO_ROOT))
    if args.repo_url and not repo_url:
        print(f"not a GitHub repository URL: {args.repo_url}", file=sys.stderr)
        return 2
    outcome = build(Path(args.entries), Path(args.out), repo_url)
    print(f"built {outcome['out']} with {outcome['entries']} entries" + ("" if repo_url else " (no GitHub remote: entry links are relative)"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

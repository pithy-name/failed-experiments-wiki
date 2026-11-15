"""Local MCP server of the failed-experiments wiki (FastMCP, stdio).

A thin wrapper over tools/wikilib.py. Read tools need no GitHub credentials.
Write tools commit on a new branch and open a pull request with the user's
`gh` login; without a git remote they say so and leave the branch for a local merge.

Everything an agent writes through this server is labelled:
contributor.type = agent, review.status = unreviewed.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

REPO = Path(os.environ.get("FEWIKI_REPO") or Path(__file__).resolve().parents[2])
sys.path.insert(0, str(REPO / "tools"))

from fastmcp import FastMCP  # noqa: E402

import lw  # noqa: E402
import wikilib  # noqa: E402

CONTRIBUTE_TOOL = f"contribute-skill v{wikilib.TOOL_VERSION}"

mcp = FastMCP(
    "failed-experiments-wiki",
    instructions=(
        "A wiki of failed AI-safety experiments. Use search_entries and get_entry to find what has been tried and "
        "where it went wrong; cite entry IDs. Never state a failure that is not in an entry. Entries with the badges "
        "'agent-written' or 'unreviewed' have not been checked by a person: say so when you rely on them. "
        "Entries describe experiments, never judge people."
    ),
)


def _entries():
    return wikilib.load_entries(REPO / "entries")


@mcp.tool
def search_entries(query: str = "", filters: dict | None = None, limit: int = 20) -> dict:
    """Search the wiki by keyword and/or filter on any field.

    query: free text; matched by keyword against titles, hypotheses, scopes, methods, models and more.
      Keyword match only, so try synonyms and several phrasings before concluding nothing exists.
      Results are ranked and an entry is listed when it contains ANY query term: read `matched_terms` and `score`,
      and treat a hit on one common word as a weak match. (The browse page's search box requires every word instead.)
    filters: {"field.path": value or [values]} matches any listed value, e.g.
      {"failure_type": ["underpowered", "measurement_noise"], "method": "sae", "models.name": "GPT-2 small",
       "retry_welcome": true, "review.status": "reviewed", "badges": "agent-written"}.
      Ranges for numbers and dates: {"source.published_min": "2025-01-01", "result.n_max": 500}.
      Call list_facets to see every field and the values in use.
    An empty query with no filters lists every entry.
    """
    return wikilib.search(_entries(), query, filters, limit)


@mcp.tool
def get_entry(id: str) -> dict:
    """Return one entry in full: every field, its free-text body, its badges and its file path."""
    entry = wikilib.find_entry(_entries(), id)
    if entry is None:
        return {"found": False, "id": id, "detail": "No entry with this ID. Use search_entries to find IDs."}
    return {
        "found": True,
        "id": entry.id,
        "entry": entry.data,
        "body": entry.body,
        "badges": wikilib.badges(entry.data),
        "file": f"entries/{entry.id}.md",
    }


@mcp.tool
def list_facets() -> dict:
    """List every filterable field: values in use with counts (facets), min/max (ranges), and the full-text fields."""
    return wikilib.facets(_entries())


@mcp.tool
def fetch_source(url: str) -> dict:
    """Fetch a LessWrong / Alignment Forum post for writing or reviewing an entry.

    Returns metadata (title, authors, published date, tags, both URLs for crossposts) and the post's plain text.
    The text is for reading only: quote at most 15 words from it, and never copy it into an entry or a file.
    The validator checks quotes against this same text.
    """
    try:
        return {"ok": True, **lw.source_bundle(url)}
    except ValueError as exc:
        return {"ok": False, "status": "unsupported_url", "detail": str(exc)}
    except lw.SourceUnreachable as exc:
        return {"ok": False, "status": "source_unreachable", "detail": str(exc)[:300]}


@mcp.tool
def submit_entry(entry: dict, body: str = "", agent_model: str = "unknown", tool: str = CONTRIBUTE_TOOL) -> dict:
    """Submit a new entry: validate it, commit it on a new branch, open a pull request.

    entry: the schema fields (see schema/entry.schema.json). Do NOT set id, contributor, review or dates:
      the server assigns them. Every entry submitted here is stored as contributor.type = agent,
      review.status = unreviewed.
    body: optional free-text notes in your own words (never post text).
    agent_model: the model that wrote the entry, e.g. its model ID.
    Returns the assigned id, the branch, the pull request URL (or a plain statement that no remote exists),
    and any validation issues. A rejected entry writes nothing: fix the listed issues and submit again.
    """
    return wikilib.submit_entry(entry, body, repo=REPO, contributor_type="agent", agent_model=agent_model, tool=tool)


@mcp.tool
def review_entry(id: str, status: str, notes: str, agent_model: str = "unknown") -> dict:
    """Record a review of an entry: set review.status and append yourself to review.reviewers.

    status: "reviewed" (every field checked against the source and found accurate), "contested"
      (something in the entry is wrong or overreaches; say what in notes) or "superseded".
    notes: what you checked and what you found, in one or two sentences.
    The review is committed on a new branch and opened as a pull request. It is recorded as an agent review.
    """
    return wikilib.review_entry(id, status, notes, repo=REPO, reviewer_type="agent", agent_model=agent_model)


if __name__ == "__main__":
    mcp.run()

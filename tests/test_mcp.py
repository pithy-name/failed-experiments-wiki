"""The MCP server, exercised in process through a real FastMCP client (no sockets, no subprocess)."""
import asyncio
import copy
import importlib.util
import json
from pathlib import Path

import pytest

import wikilib
from conftest import FAKE_URL, run_git

SERVER_PATH = Path(__file__).resolve().parent.parent / "plugin" / "mcp" / "server.py"


@pytest.fixture
def server(git_repo, monkeypatch):
    spec = importlib.util.spec_from_file_location("fewiki_mcp_server", SERVER_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    monkeypatch.setattr(module, "REPO", git_repo)
    return module


def call(server, name, arguments=None):
    from fastmcp import Client

    async def run():
        async with Client(server.mcp) as client:
            result = await client.call_tool(name, arguments or {})
            return result.data if result.data is not None else json.loads(result.content[0].text)

    return asyncio.run(run())


def list_tools(server):
    from fastmcp import Client

    async def run():
        async with Client(server.mcp) as client:
            return {tool.name: tool for tool in await client.list_tools()}

    return asyncio.run(run())


def test_server_exposes_the_prd_tools(server):
    tools = list_tools(server)
    assert {"search_entries", "get_entry", "list_facets", "submit_entry", "review_entry"} <= set(tools)
    assert "fetch_source" in tools
    assert all(tool.description for tool in tools.values())


def test_search_get_and_facets(server):
    found = call(server, "search_entries", {"query": "activation steering refusal"})
    assert found["match_count"] == 1 and found["results"][0]["id"] == "fe-2026-0001"
    assert found["results"][0]["badges"] == ["agent-written", "unreviewed", "retry-welcome"]

    assert call(server, "search_entries", {"query": "protein folding"})["match_count"] == 0
    assert call(server, "search_entries", {"filters": {"failure_type": "underpowered"}})["match_count"] == 0
    assert call(server, "search_entries", {"filters": {"method": "activation-steering"}})["match_count"] == 1

    entry = call(server, "get_entry", {"id": "fe-2026-0001"})
    assert entry["found"] and entry["entry"]["source"]["url"] == FAKE_URL and entry["body"] == "Body text."
    assert call(server, "get_entry", {"id": "fe-2026-0404"})["found"] is False

    facets = call(server, "list_facets")
    assert facets["total_entries"] == 1 and facets["facets"]["failure_type"] == {"hypothesis_false": 1}


def test_fetch_source_returns_text_from_cache_and_refuses_other_sites(server):
    bundle = call(server, "fetch_source", {"url": FAKE_URL})
    assert bundle["ok"] and "no measurable effect" in bundle["text"] and bundle["authors"] == ["Test Author"]
    assert call(server, "fetch_source", {"url": "https://example.com/x"})["status"] == "unsupported_url"


def test_submit_entry_labels_agent_work_and_opens_a_branch(server, git_repo, valid_entry):
    draft = copy.deepcopy(valid_entry)
    for owned in ("id", "contributor", "review", "dates"):
        draft.pop(owned)
    draft["title"] = "A second steering attempt on GPT-2 small also showed no effect"
    result = call(server, "submit_entry", {"entry": draft, "body": "Notes.", "agent_model": "test-model"})
    assert result["ok"] and result["id"] == "fe-2026-0002"
    assert result["status"] == "branch_only_no_remote" and result["pull_request"] is None
    stored, _ = wikilib.parse_entry_text(wikilib.read_file_at(git_repo, result["branch"], result["file"]))
    assert stored["contributor"]["type"] == "agent" and stored["contributor"]["agent_model"] == "test-model"
    assert stored["review"]["status"] == "unreviewed"


def test_submit_entry_rejects_an_invented_quote(server, git_repo, valid_entry):
    draft = copy.deepcopy(valid_entry)
    for owned in ("id", "contributor", "review", "dates"):
        draft.pop(owned)
    draft["source"]["quote"] = "this sentence was never in the post"
    result = call(server, "submit_entry", {"entry": draft})
    assert result["ok"] is False and any(issue["code"] == "quote_not_found" for issue in result["issues"])
    assert run_git(git_repo, "branch", "--list", "entry/*") == ""


def test_review_entry_records_an_agent_review(server, git_repo):
    result = call(server, "review_entry", {"id": "fe-2026-0001", "status": "contested", "notes": "Scope overreaches.", "agent_model": "test-model"})
    assert result["ok"] and result["new_status"] == "contested"
    stored, _ = wikilib.parse_entry_text(wikilib.read_file_at(git_repo, result["branch"], "entries/fe-2026-0001.md"))
    assert stored["review"]["reviewers"][0]["type"] == "agent"

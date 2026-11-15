"""Start the MCP server as a real process and talk to it over stdio.

  python tools/mcp_smoke.py        (or: make mcp-smoke)

Launches plugin/mcp/run.sh, the same launcher the Claude Code plugin uses,
connects with a FastMCP client, lists the tools and runs one search. This
checks the launcher, the interpreter it picks and the stdio transport, which
the in-process tests (tests/test_mcp.py) do not. No port is opened.
"""
from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


async def run() -> int:
    from fastmcp import Client
    from fastmcp.client.transports import StdioTransport

    transport = StdioTransport(command=str(REPO_ROOT / "plugin" / "mcp" / "run.sh"), args=[])
    async with Client(transport) as client:
        tools = sorted(tool.name for tool in await client.list_tools())
        print("tools:", ", ".join(tools))
        result = await client.call_tool("search_entries", {"query": "sparse autoencoder probes", "limit": 3})
        data = result.data if result.data is not None else json.loads(result.content[0].text)
        print(f"search_entries: {data['match_count']} matches of {data['total_entries_in_wiki']} entries")
        for item in data["results"]:
            print(f"  {item['id']}  {item['badges']}  {item['title'][:70]}")
        facets = await client.call_tool("list_facets", {})
        fdata = facets.data if facets.data is not None else json.loads(facets.content[0].text)
        print("list_facets: total_entries =", fdata["total_entries"])
    expected = {"search_entries", "get_entry", "list_facets", "submit_entry", "review_entry", "fetch_source"}
    return 0 if expected <= set(tools) else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(run()))

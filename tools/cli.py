"""Command-line twin of the MCP server. Same functions, same JSON, no MCP client needed.

  python tools/cli.py search "steering vectors" --filter failure_type=underpowered
  python tools/cli.py get fe-2026-0001
  python tools/cli.py facets
  python tools/cli.py fetch-source https://www.lesswrong.com/posts/<id>/<slug>
  python tools/cli.py submit --file draft.md --agent-model <model-id>
  python tools/cli.py review fe-2026-0001 reviewed --notes "Checked every field." --human --handle <github-handle>
  python tools/cli.py merge-local entry/fe-2026-0006      # only for repos with no remote
  python tools/cli.py next-id
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import lw  # noqa: E402
import wikilib  # noqa: E402


def _parse_filters(pairs: list[str], raw_json: str | None) -> dict:
    filters: dict = json.loads(raw_json) if raw_json else {}
    for pair in pairs or []:
        key, _, value = pair.partition("=")
        parsed: object = value
        if value.lower() in {"true", "false"}:
            parsed = value.lower() == "true"
        existing = filters.get(key)
        if existing is None:
            filters[key] = parsed
        else:
            filters[key] = (existing if isinstance(existing, list) else [existing]) + [parsed]
    return filters


def _read_draft(path: Path) -> tuple[dict, str]:
    text = path.read_text(encoding="utf-8")
    if path.suffix == ".json":
        payload = json.loads(text)
        if "entry" in payload and isinstance(payload["entry"], dict):
            return payload["entry"], payload.get("body", "")
        return payload, ""
    return wikilib.parse_entry_text(text)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Carpe Ignota wiki CLI (JSON output).")
    parser.add_argument("--repo", default=str(wikilib.REPO_ROOT), help="repository root (default: this checkout)")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("search", help="keyword search and field filters")
    p.add_argument("query", nargs="?", default="")
    p.add_argument("--filter", action="append", default=[], metavar="FIELD=VALUE", help="repeatable; same field twice = OR")
    p.add_argument("--filters", help="filters as a JSON object")
    p.add_argument("--limit", type=int, default=20)
    p.add_argument("--brief", action="store_true", help="one line per result instead of JSON, for reading at a terminal")

    p = sub.add_parser("get", help="one entry in full")
    p.add_argument("id")

    sub.add_parser("facets", help="every filterable field and its values")

    p = sub.add_parser("fetch-source", help="post metadata and plain text (cached)")
    p.add_argument("url")
    p.add_argument("--cached", action="store_true", help="use the cache only, no network")
    p.add_argument("--no-text", action="store_true", help="omit the post text")
    p.add_argument(
        "--save", action="store_true",
        help="also write the metadata and the text to the git-ignored cache (.cache/lw/meta/<id>.json, .cache/lw/text/<id>.txt) "
        "and print the paths instead of the text, for agents that read files but cannot run commands",
    )

    p = sub.add_parser("submit", help="validate a draft, commit it on a branch, open a pull request")
    p.add_argument("--file", required=True, help="draft: Markdown with front matter, or JSON")
    p.add_argument("--agent-model", default="unknown")
    p.add_argument("--tool", default=f"contribute-skill v{wikilib.TOOL_VERSION}")
    p.add_argument("--human", action="store_true", help="record the contributor as a human (default: agent)")
    p.add_argument("--handle", help="GitHub handle (default: FEWIKI_HANDLE or the gh login)")
    p.add_argument("--quotes", choices=["online", "strict", "cached", "skip"], default="online")

    p = sub.add_parser("review", help="record a review on a branch, open a pull request")
    p.add_argument("id")
    p.add_argument("status", choices=["reviewed", "contested", "superseded", "unreviewed"])
    p.add_argument("--notes", required=True)
    p.add_argument("--human", action="store_true", help="record the reviewer as a human (default: agent)")
    p.add_argument("--handle")
    p.add_argument("--agent-model", default="unknown")
    p.add_argument("--quotes", choices=["online", "strict", "cached", "skip"], default="online")

    p = sub.add_parser("merge-local", help="validate and merge a branch (stand-in for a pull-request merge when there is no remote)")
    p.add_argument("branch")

    sub.add_parser("next-id", help="the next free entry ID")

    args = parser.parse_args(argv)
    repo = Path(args.repo)
    entries_dir = repo / "entries"

    if args.command == "search":
        out = wikilib.search(wikilib.load_entries(entries_dir), args.query, _parse_filters(args.filter, args.filters), args.limit)
        if args.brief:
            print(f"{out['match_count']} of {out['total_entries_in_wiki']} entries match (keyword search; terms: {', '.join(out['query_terms']) or 'none'})")
            for item in out["results"]:
                print(f"  {item['id']}  score {item['score']:>3}  {item['failure_type']}, evidence strength {item['evidence_strength']}  [{', '.join(item['badges'])}]")
                print(f"      {item['title']}")
            return 0
    elif args.command == "get":
        entry = wikilib.find_entry(wikilib.load_entries(entries_dir), args.id)
        out = (
            {"found": True, "id": entry.id, "entry": entry.data, "body": entry.body, "badges": wikilib.badges(entry.data),
             "file": f"entries/{entry.id}.md"}
            if entry else {"found": False, "id": args.id}
        )
    elif args.command == "facets":
        out = wikilib.facets(wikilib.load_entries(entries_dir))
    elif args.command == "fetch-source":
        try:
            out = {"ok": True, **lw.source_bundle(args.url, offline=args.cached)}
            if args.save:
                text = out.pop("text")
                meta_path = lw.cache_dir() / "meta" / f"{out['post_id']}.json"
                text_path = lw.cache_dir() / "text" / f"{out['post_id']}.txt"
                for path in (meta_path, text_path):
                    path.parent.mkdir(parents=True, exist_ok=True)
                meta_path.write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
                header = (
                    f"TITLE: {out['title']}\nAUTHORS: {', '.join(out['authors'])}\nPUBLISHED: {out['published']}\n"
                    f"URL: {out['url_lesswrong']}\nTAGS: {', '.join(out['lw_tags'])}\nWORDS: {out['word_count']}\n----\n"
                )
                text_path.write_text(header + text + "\n", encoding="utf-8")
                out.update(meta_file=str(meta_path), text_file=str(text_path))
            elif args.no_text:
                out.pop("text")
        except (ValueError, lw.SourceUnreachable) as exc:
            out = {"ok": False, "detail": str(exc)[:300]}
    elif args.command == "submit":
        data, body = _read_draft(Path(args.file))
        out = wikilib.submit_entry(
            data, body, repo=repo, contributor_type="human" if args.human else "agent", handle=args.handle,
            agent_model=args.agent_model, tool=args.tool, quote_mode=args.quotes,
        )
    elif args.command == "review":
        out = wikilib.review_entry(
            args.id, args.status, args.notes, repo=repo, reviewer_type="human" if args.human else "agent",
            handle=args.handle, agent_model=args.agent_model, quote_mode=args.quotes,
        )
    elif args.command == "merge-local":
        out = wikilib.merge_local(args.branch, repo=repo)
    else:
        out = {"next_id": wikilib.next_id(repo)}

    print(json.dumps(out, indent=2, ensure_ascii=False))
    return 0 if out.get("ok", True) and out.get("found", True) else 1


if __name__ == "__main__":
    raise SystemExit(main())

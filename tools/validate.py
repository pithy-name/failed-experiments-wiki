"""The single validator of the wiki (PRD 5.6, D7).

Used locally, by the MCP server (through tools/wikilib.py) and by the GitHub Action.

It rejects an entry that:
- breaks the JSON Schema (schema/entry.schema.json);
- uses a value outside a closed list;
- lacks a source URL;
- reuses an ID, or has an ID that does not match its file name;
- has a quote longer than 15 words;
- has a quote that does not appear in the fetched source text.

If the source cannot be fetched, the quote check is a warning (or an error with
--strict-quotes).

Run:
  python tools/validate.py                      # every file in entries/
  python tools/validate.py entries/fe-2026-0001.md
  python tools/validate.py --gold               # the gold entries in evals/gold/
  python tools/validate.py --quotes cached      # no network: use cached sources only
Exit code 1 when any error is found.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import wikilib  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate wiki entries.")
    parser.add_argument("paths", nargs="*", help="entry files (default: every .md in entries/)")
    parser.add_argument("--gold", action="store_true", help="validate evals/gold/ (allows the gold_status key)")
    parser.add_argument(
        "--quotes", choices=["online", "strict", "cached", "skip"], default="online",
        help="quote check: online (default; unreachable source = warning), strict (unreachable = error), "
        "cached (no network), skip",
    )
    parser.add_argument("--strict-quotes", action="store_true", help="same as --quotes strict")
    parser.add_argument("--json", action="store_true", help="print issues as JSON")
    args = parser.parse_args(argv)

    quote_mode = "strict" if args.strict_quotes else args.quotes
    if args.paths:
        paths = [Path(p) for p in args.paths]
    elif args.gold:
        paths = sorted((wikilib.REPO_ROOT / "evals" / "gold").glob("*.md"))
    else:
        paths = sorted(wikilib.ENTRIES_DIR.glob("*.md"))

    issues = wikilib.validate_paths(paths, quote_mode=quote_mode, allow_gold_status=args.gold)
    errors = [i for i in issues if i.level == "error"]
    warnings = [i for i in issues if i.level == "warning"]

    if args.json:
        print(json.dumps({"files": len(paths), "errors": len(errors), "warnings": len(warnings),
                          "issues": [i.as_dict() for i in issues]}, indent=2))
    else:
        for issue in issues:
            print(issue)
        print(f"{len(paths)} file(s) checked, quote check: {quote_mode}. {len(errors)} error(s), {len(warnings)} warning(s).")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())

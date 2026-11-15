"""Replace the placeholder GitHub handle in the seed entries with the real one.

The seed entries were written in a session that could not read the `gh` login,
so they carry the visible placeholder HANDLE-TBD (as contributor.handle, and as
the handle of the account that ran the reviewing agent).

  python tools/set_handle.py <github-handle>        (or: make set-handle HANDLE=<github-handle>)

Rewrites only that placeholder, in entries/ and evals/gold/, keeps each file in
place, validates the result, and changes nothing else. Commit the files yourself.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import wikilib  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if len(args) != 1 or not re.fullmatch(r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,37}[A-Za-z0-9])?", args[0]):
        print("usage: python tools/set_handle.py <github-handle>", file=sys.stderr)
        return 2
    handle = args[0]
    changed = []
    for directory in (wikilib.ENTRIES_DIR, wikilib.REPO_ROOT / "evals" / "gold"):
        for path in sorted(directory.glob("fe-*.md")):
            text = path.read_text(encoding="utf-8")
            if wikilib.PLACEHOLDER_HANDLE not in text:
                continue
            with path.open("w", encoding="utf-8") as handle_file:  # rewrite in place, same file
                handle_file.write(text.replace(wikilib.PLACEHOLDER_HANDLE, handle))
            changed.append(path)
    issues = wikilib.validate_paths(sorted(wikilib.ENTRIES_DIR.glob("*.md")), quote_mode="skip")
    errors = [issue for issue in issues if issue.level == "error"]
    for issue in errors:
        print(issue)
    print(f"replaced {wikilib.PLACEHOLDER_HANDLE} with {handle} in {len(changed)} file(s); {len(errors)} validation error(s)")
    if changed:
        print('commit with: git add entries evals/gold && git commit -m "Set the maintainer\'s GitHub handle on the seed entries"')
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())

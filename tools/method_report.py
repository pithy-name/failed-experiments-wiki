"""Report write-in methods: methods entries use that the issue form's Method dropdown does not offer.

A write-in used by two or more entries is ready to join the dropdown. Run it
whenever entries are added; the list needs review when this report flags one.

Usage: python tools/method_report.py   (or `make method-report`)

Reusability: PROJECT-INTERNAL
"""
from __future__ import annotations

import argparse
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import wikilib  # noqa: E402

READY_AT = 2  # entries using a write-in before it should join the dropdown


def write_ins(entry_methods: list[list[str]], options: list[str]) -> list[tuple[str, int]]:
    """(method, number of entries using it) for methods not in the options, most used first."""
    listed = set(options)
    counts = Counter(m for methods in entry_methods for m in set(methods) if m not in listed)
    return sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))


def ready_to_add(rows: list[tuple[str, int]]) -> list[str]:
    return [method for method, count in rows if count >= READY_AT]


FORM = Path(__file__).resolve().parent.parent / ".github" / "ISSUE_TEMPLATE" / "new-entry.yml"


def form_options() -> list[str]:
    import yaml
    template = yaml.safe_load(FORM.read_text(encoding="utf-8"))
    return next(item["attributes"]["options"] for item in template["body"] if item.get("id") == "method")


def main(argv: list[str] | None = None) -> int:
    argparse.ArgumentParser(description=__doc__.splitlines()[0]).parse_args(argv)
    entries = wikilib.load_entries()
    rows = write_ins([e.data.get("method") or [] for e in entries], form_options())
    print(f"{len(entries)} entries; {len(rows)} write-in method(s) not in the form's Method list.")
    for method, count in rows:
        print(f"- {method}: {count} entr{'y' if count == 1 else 'ies'}")
    ready = ready_to_add(rows)
    if ready:
        print(f"\nReady to add to the dropdown (used by {READY_AT}+ entries): {', '.join(ready)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

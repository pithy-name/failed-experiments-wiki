"""Mechanical cross-check of an entry's specifics against its source post.

  python tools/check_facts.py                 # every entry
  python tools/check_facts.py entries/fe-2026-0006.md

The validator proves the quote is in the post. It cannot tell whether the rest
of an entry is faithful. This check narrows the gap a little: every number and
every model name an entry states must also occur somewhere in the post text.
A miss is not proof of an error (an entry may say "five" where the post says
"5", or state a count the reader derived), but each miss is worth a look. A
clean run is not proof of accuracy either: it says nothing about meaning.

Uses the cached post text only (no network). Exit code is always 0; this is a
review aid, not a gate.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import lw  # noqa: E402
import wikilib  # noqa: E402

TEXT_FIELDS = ["title", "hypothesis", "claim_scope", "limitations", "revival_conditions"]
NUMBER_RE = re.compile(r"(?<![\w.])-?\d+(?:[.,]\d+)*%?(?![\w])")
WORD_NUMBERS = {
    "0": "zero", "1": "one", "2": "two", "3": "three", "4": "four", "5": "five", "6": "six", "7": "seven",
    "8": "eight", "9": "nine", "10": "ten", "11": "eleven", "12": "twelve", "20": "twenty", "50": "fifty", "100": "hundred",
}


def squash(text: str) -> str:
    return re.sub(r"[\s\-_]+", "", lw.normalize_for_quote(text).lower())


def number_in_post(token: str, post_plain: str, post_squashed: str) -> bool:
    bare = token.rstrip("%").lstrip("-")
    variants = {bare, bare.replace(",", "")}
    if bare.endswith(".0"):
        variants.add(bare[:-2])
    for variant in variants:
        if re.search(rf"(?<![\d.]){re.escape(variant)}(?!\d)", post_plain):
            return True
    word = WORD_NUMBERS.get(bare)
    return bool(word) and word in post_plain.lower()


def check(path: Path) -> dict:
    entry = wikilib.load_entry(path)
    data = entry.data
    post_id = lw.post_id_from_url((data.get("source") or {}).get("url", ""))
    try:
        post = lw.fetch_post(post_id, offline=True)
    except (lw.SourceUnreachable, TypeError):
        return {"id": entry.id, "error": "source text is not in the cache"}
    post_plain = lw.normalize_for_quote(lw.post_text(post) + " " + (post.get("title") or ""))
    post_squashed = squash(post_plain)

    texts = [str(data.get(field) or "") for field in TEXT_FIELDS] + [entry.body]
    numbers = sorted({match.group(0) for text in texts for match in NUMBER_RE.finditer(lw.normalize_for_quote(text))})
    result = data.get("result") or {}
    for key in ("effect_size", "ci_low", "ci_high", "n"):
        if key in result:
            numbers.append(str(result[key]))
    missing_numbers = [n for n in dict.fromkeys(numbers) if not number_in_post(n, post_plain, post_squashed)]

    names = [str(model.get("name")) for model in data.get("models") or [] if model.get("name") not in (None, "unknown")]
    names += [str(b) for b in data.get("benchmarks") or []]
    missing_names = [name for name in names if squash(name) not in post_squashed]
    return {"id": entry.id, "numbers_checked": len(dict.fromkeys(numbers)), "numbers_not_in_post": missing_numbers,
            "names_checked": len(names), "names_not_in_post": missing_names}


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    paths = [Path(arg) for arg in args] or sorted(wikilib.ENTRIES_DIR.glob("fe-*.md"))
    for path in paths:
        outcome = check(path)
        if "error" in outcome:
            print(f"{outcome['id']}: {outcome['error']}")
            continue
        print(
            f"{outcome['id']}: {outcome['numbers_checked']} numbers, {len(outcome['numbers_not_in_post'])} not in post "
            f"{outcome['numbers_not_in_post'] or ''}; {outcome['names_checked']} model/benchmark names, "
            f"{len(outcome['names_not_in_post'])} not in post {outcome['names_not_in_post'] or ''}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

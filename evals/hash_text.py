"""Print the hashes that tie a grade or a judgement to the exact text it was made on.

  python evals/hash_text.py --gold fe-2026-0001 --draft draft-1.md --field claim_scope
  python evals/hash_text.py --answer q1

Used by the grader and judge prompts in evals/prompts/. The scorer
(evals/run_evals.py) recomputes the same hashes and reports a grade as STALE
when the text has changed since.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path

EVALS = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("run_evals", EVALS / "run_evals.py")
run_evals = importlib.util.module_from_spec(spec)
spec.loader.exec_module(run_evals)
wikilib = run_evals.wikilib


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gold", help="gold entry id")
    parser.add_argument("--draft", help="draft file name under evals/results/contribute/<gold id>/")
    parser.add_argument("--field", help="hypothesis, claim_scope or limitations")
    parser.add_argument("--answer", help="question id of an ask answer")
    args = parser.parse_args(argv)

    if args.answer:
        text = (EVALS / "results" / "ask" / f"{args.answer}.md").read_text(encoding="utf-8")
        print(json.dumps({"qid": args.answer, "answer_hash": run_evals.text_hash(text)}))
        return 0
    if not (args.gold and args.draft and args.field):
        parser.error("give --answer, or all of --gold, --draft and --field")
    gold = wikilib.load_entry(EVALS / "gold" / f"{args.gold}.md").data
    draft, _ = wikilib.parse_entry_text((EVALS / "results" / "contribute" / args.gold / args.draft).read_text(encoding="utf-8"))
    print(json.dumps({
        "gold_id": args.gold, "draft": args.draft, "field": args.field,
        "gold_hash": run_evals.text_hash(run_evals.first(gold, args.field) or ""),
        "skill_hash": run_evals.text_hash(run_evals.first(draft, args.field) or ""),
    }))
    return 0


if __name__ == "__main__":
    sys.exit(main())

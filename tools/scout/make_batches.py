"""Step 2b of scouting: split the sample into classification batches.

Writes scouting/classification/batches.json: a list of batches, each a list of
{post_id, title, word_count}. Batches are balanced by word count so no
classifier gets all the long posts. Deterministic.

Run:  python tools/scout/make_batches.py [--batches 6]
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sample", default=str(REPO_ROOT / "scouting" / "sample.jsonl"))
    parser.add_argument("--out", default=str(REPO_ROOT / "scouting" / "classification" / "batches.json"))
    parser.add_argument("--batches", type=int, default=6)
    args = parser.parse_args()

    with Path(args.sample).open(encoding="utf-8") as handle:
        sample = [json.loads(line) for line in handle if line.strip()]
    sample.sort(key=lambda r: (-(r.get("word_count") or 0), r["post_id"]))

    batches: list[list[dict]] = [[] for _ in range(args.batches)]
    totals = [0] * args.batches
    for record in sample:
        index = min(range(args.batches), key=lambda i: (len(batches[i]) >= -(-len(sample) // args.batches), totals[i], i))
        batches[index].append(
            {"post_id": record["post_id"], "title": record["title"], "word_count": record.get("word_count") or 0}
        )
        totals[index] += record.get("word_count") or 0

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as handle:
        json.dump(batches, handle, indent=2, ensure_ascii=False)
        handle.write("\n")
    for index, batch in enumerate(batches, start=1):
        print(f"batch {index:02d}: {len(batch)} posts, {totals[index - 1]} words")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

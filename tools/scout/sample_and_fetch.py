"""Step 2a of scouting: pick the classification sample and cache its texts.

Reads scouting/candidates.jsonl, picks up to 60 posts deterministically, writes
scouting/sample.jsonl, and fetches each sampled post into the local cache so
that classifier subagents can read plain text without touching the network.

Sampling rule (deterministic, no randomness):
- the two posts the PRD names as known examples are always included, found by
  title search if the phrase and tag routes did not surface them;
- the rest are taken round-robin across routes, best-ranked hit first, so every
  search phrase and tag is represented in the sample.

Post texts go only to .cache/ (git-ignored). They are never committed.

Run:  python tools/scout/sample_and_fetch.py
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import lw  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SAMPLE_SIZE = 60
KNOWN_ROUTE = "prd-known-example"

KNOWN_EXAMPLES = [
    "Negative Results for SAEs On Downstream Tasks",
    "My Failed AI Safety Research Projects",
]


def load_candidates(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def find_known(title_start: str, candidates: list[dict]) -> dict | None:
    wanted = title_start.lower()
    for record in candidates:
        if (record.get("title") or "").lower().startswith(wanted):
            return record
    for hit in lw.search_posts(title_start, page=0, hits_per_page=5):
        if (hit.get("title") or "").lower().startswith(wanted):
            tags = hit.get("tags") or []
            return {
                "post_id": hit["objectID"],
                "url": f"https://www.lesswrong.com/posts/{hit['objectID']}/{hit.get('slug', '')}",
                "title": hit.get("title"),
                "author": hit.get("authorDisplayName"),
                "published": (hit.get("postedAt") or "")[:10],
                "base_score": hit.get("baseScore"),
                "alignment_forum": bool(hit.get("af")),
                "tags": [tag.get("name") for tag in tags],
                "tag_slugs": [tag.get("slug") for tag in tags],
                "snippet": "",
                "routes": [],
                "route_ranks": {},
            }
    return None


def pick_sample(candidates: list[dict], forced: list[dict], size: int) -> list[dict]:
    chosen: dict[str, dict] = {}
    for record in forced:
        chosen[record["post_id"]] = record

    by_route: dict[str, list[dict]] = {}
    for record in candidates:
        for route in record["routes"]:
            by_route.setdefault(route, []).append(record)
    for route, records in by_route.items():
        records.sort(key=lambda r: (r["route_ranks"][route], r["post_id"]))

    routes = sorted(by_route)
    depth = 0
    while len(chosen) < size and any(depth < len(by_route[route]) for route in routes):
        for route in routes:
            if len(chosen) >= size:
                break
            if depth < len(by_route[route]):
                record = by_route[route][depth]
                chosen.setdefault(record["post_id"], record)
        depth += 1
    return list(chosen.values())


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidates", default=str(REPO_ROOT / "scouting" / "candidates.jsonl"))
    parser.add_argument("--out", default=str(REPO_ROOT / "scouting" / "sample.jsonl"))
    parser.add_argument("--size", type=int, default=SAMPLE_SIZE)
    parser.add_argument(
        "--exclude", help="a sample file whose posts are skipped (used for a second round over the remaining candidates)"
    )
    args = parser.parse_args()

    candidates = load_candidates(Path(args.candidates))
    excluded: set[str] = set()
    if args.exclude:
        excluded = {record["post_id"] for record in load_candidates(Path(args.exclude))}
        candidates = [record for record in candidates if record["post_id"] not in excluded]
    forced = []
    for title_start in [] if args.exclude else KNOWN_EXAMPLES:
        record = find_known(title_start, candidates)
        if record is None:
            print(f"known example not found: {title_start}", file=sys.stderr)
            continue
        record = dict(record)
        if KNOWN_ROUTE not in record["routes"]:
            record["routes"] = record["routes"] + [KNOWN_ROUTE]
        forced.append(record)

    sample = pick_sample(candidates, forced, args.size)

    text_dir = lw.cache_dir() / "text"
    text_dir.mkdir(parents=True, exist_ok=True)
    kept = []
    for record in sample:
        try:
            post = lw.fetch_post(record["post_id"])
        except lw.SourceUnreachable as exc:
            print(f"skip {record['post_id']}: {exc}", file=sys.stderr)
            continue
        text = lw.post_text(post)
        header = (
            f"TITLE: {post.get('title')}\n"
            f"AUTHORS: {', '.join(lw.post_authors(post))}\n"
            f"PUBLISHED: {(post.get('postedAt') or '')[:10]}\n"
            f"URL: {record['url']}\n"
            f"TAGS: {', '.join(tag['name'] for tag in post.get('tags') or [])}\n"
            f"WORDS: {(post.get('contents') or {}).get('wordCount')}\n"
            "----\n"
        )
        (text_dir / f"{record['post_id']}.txt").write_text(header + text + "\n", encoding="utf-8")
        record = dict(record)
        record["word_count"] = (post.get("contents") or {}).get("wordCount")
        kept.append(record)

    out_path = Path(args.out)
    with out_path.open("w", encoding="utf-8") as handle:
        for record in kept:
            handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")
    print(f"sampled {len(kept)} of {len(candidates)} candidates; texts cached in {text_dir}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

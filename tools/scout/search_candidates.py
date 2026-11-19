"""Step 1 of scouting: deterministic candidate search.

Queries LessWrong by search phrase and by tag, keeps AI-related posts, and
writes scouting/candidates.jsonl: one line per post with URL, title, authors,
date, tags, the routes that found it and a matching snippet (not the post text).

Run:  python tools/scout/search_candidates.py
Responses are cached under .cache/ and requests are paused (see tools/lw.py),
so re-running is free and reproducible.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import lw  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parent.parent.parent

# Search phrases from the PRD, used verbatim.
PHRASES = [
    "negative result",
    "null result",
    "didn't work",
    "did not improve",
    "failed to replicate",
    "we tried",
    "what went wrong",
    "lessons learned",
    "postmortem",
    "retrospective",
]

# Tags that are about failure write-ups: every AI-related post under them is a candidate.
FAILURE_TAGS = ["postmortems-and-retrospectives", "negative-results", "replication-crisis"]

# Topical AI-safety tags: only posts whose title or description matches a
# failure phrase are kept, otherwise these tags would flood the candidate list.
TOPIC_TAGS = [
    "interpretability-ml-and-ai",
    "sparse-autoencoders-saes",
    "activation-engineering",
    "ai-evaluations",
    "ai-control",
    "mats-program",
]

# A post counts as AI-related when it carries at least one of these tags.
AI_TAG_SLUGS = {
    "ai", "ai-risk", "interpretability-ml-and-ai", "sparse-autoencoders-saes", "activation-engineering",
    "ai-evaluations", "ai-control", "mats-program", "language-models-llms", "language-models",
    "machine-learning-ml", "ai-safety-camp", "alignment-research", "inner-alignment", "outer-alignment",
    "deceptive-alignment", "eliciting-latent-knowledge-elk", "ai-alignment-fieldbuilding",
    "reinforcement-learning", "gpt", "transformers", "deep-learning", "ai-capabilities",
    "mechanistic-interpretability", "steering-vectors", "sycophancy", "adversarial-training",
    "ai-governance", "ai-robustness", "scheming", "sandbagging-ai", "chain-of-thought-alignment",
    "research-agendas", "apart-research", "redwood-research", "spar", "probing",
}

LOCAL_FAILURE_RE = re.compile(
    r"negative results?|null results?|didn[’']t work|did not (?:work|improve|replicate)|doesn[’']t work|"
    r"fail(?:ed|ure|s)? to (?:replicate|reproduce|find|improve)|failed|we tried|what went wrong|"
    r"lessons learned|post-?mortem|retrospective|no (?:evidence|effect|improvement)|disappointing",
    re.IGNORECASE,
)

HITS_PER_PAGE = 5  # each hit carries the whole post body; larger pages get cut off mid-response
PAGES_PER_PHRASE = 8
TAG_POST_LIMIT = 100


def snippet_for(text: str, pattern: re.Pattern | None, width: int = 240) -> str:
    """Up to `width` characters around the first match (or from the start)."""
    text = re.sub(r"\s+", " ", text or "").strip()
    match = pattern.search(text) if pattern else None
    if not match:
        return text[:width]
    start = max(0, match.start() - width // 2)
    return ("…" if start else "") + text[start : start + width] + "…"


def is_ai_related(tag_slugs: list[str]) -> bool:
    return bool(AI_TAG_SLUGS.intersection(tag_slugs))


def add(candidates: dict, post_id: str, record: dict, route: str, rank: int) -> None:
    existing = candidates.get(post_id)
    if existing is None:
        record["routes"] = [route]
        record["route_ranks"] = {route: rank}
        candidates[post_id] = record
    elif route not in existing["routes"]:
        existing["routes"].append(route)
        existing["route_ranks"][route] = rank


def from_search_hit(hit: dict, phrase: str) -> dict:
    tags = hit.get("tags") or []
    phrase_re = re.compile(re.escape(phrase).replace("'", "[’']"), re.IGNORECASE)
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
        "snippet": snippet_for(hit.get("body") or "", phrase_re),
    }


def from_tag_post(post: dict) -> dict:
    tags = post.get("tags") or []
    description = (post.get("contents") or {}).get("plaintextDescription") or ""
    return {
        "post_id": post["_id"],
        "url": f"https://www.lesswrong.com/posts/{post['_id']}/{post.get('slug', '')}",
        "title": post.get("title"),
        "author": (post.get("user") or {}).get("displayName"),
        "published": (post.get("postedAt") or "")[:10],
        "base_score": post.get("baseScore"),
        "alignment_forum": bool(post.get("af")),
        "tags": [tag.get("name") for tag in tags],
        "tag_slugs": [tag.get("slug") for tag in tags],
        "snippet": snippet_for(description, LOCAL_FAILURE_RE),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", default=str(REPO_ROOT / "scouting" / "candidates.jsonl"))
    args = parser.parse_args()

    candidates: dict[str, dict] = {}
    route_stats: dict[str, dict] = {}
    notes: list[str] = []

    for phrase in PHRASES:
        route = f"phrase:{phrase}"
        raw = kept = 0
        for page in range(PAGES_PER_PHRASE):
            hits = lw.search_posts(phrase, page=page, hits_per_page=HITS_PER_PAGE)
            for index, hit in enumerate(hits):
                raw += 1
                record = from_search_hit(hit, phrase)
                if not is_ai_related(record["tag_slugs"]):
                    continue
                kept += 1
                add(candidates, record["post_id"], record, route, page * HITS_PER_PAGE + index)
        route_stats[route] = {"returned": raw, "ai_related": kept}
        print(f"{route}: returned {raw}, AI-related {kept}", file=sys.stderr)

    for kind, slugs in (("failure", FAILURE_TAGS), ("topic", TOPIC_TAGS)):
        for slug in slugs:
            route = f"tag:{slug}"
            tag = lw.tag_by_slug(slug)
            if not tag:
                notes.append(f"tag '{slug}' does not exist on LessWrong; skipped")
                route_stats[route] = {"returned": 0, "ai_related": 0, "note": "tag not found"}
                print(f"{route}: tag not found", file=sys.stderr)
                continue
            posts = lw.posts_by_tag(tag["_id"], limit=TAG_POST_LIMIT)
            raw = kept = 0
            for index, post in enumerate(posts):
                raw += 1
                record = from_tag_post(post)
                if not is_ai_related(record["tag_slugs"]):
                    continue
                if kind == "topic":
                    haystack = f"{record['title']} {(post.get('contents') or {}).get('plaintextDescription') or ''}"
                    if not LOCAL_FAILURE_RE.search(haystack):
                        continue
                kept += 1
                add(candidates, record["post_id"], record, route, index)
            route_stats[route] = {
                "returned": raw,
                "ai_related": kept,
                "tag_post_count": tag.get("postCount"),
                "filter": "AI-related" if kind == "failure" else "AI-related and local failure-phrase match",
            }
            print(f"{route}: returned {raw}, kept {kept}", file=sys.stderr)

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    ordered = sorted(candidates.values(), key=lambda r: (-len(r["routes"]), r["published"] or "", r["post_id"]))
    with out_path.open("w", encoding="utf-8") as handle:
        for record in ordered:
            handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")

    stats_path = out_path.with_name("search_stats.json")
    with stats_path.open("w", encoding="utf-8") as handle:
        json.dump(
            {
                "run_date": dt.date.today().isoformat(),
                "endpoint_search": lw.SEARCH_URL,
                "endpoint_graphql": lw.GRAPHQL_URL,
                "hits_per_page": HITS_PER_PAGE,
                "pages_per_phrase": PAGES_PER_PHRASE,
                "tag_post_limit": TAG_POST_LIMIT,
                "unique_candidates": len(ordered),
                "routes": route_stats,
                "notes": notes,
            },
            handle,
            indent=2,
            ensure_ascii=False,
        )
        handle.write("\n")
    print(f"wrote {len(ordered)} candidates to {out_path}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

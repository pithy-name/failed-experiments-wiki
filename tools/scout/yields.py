"""Step 3 of scouting: yields.

Merges the classifier batch files into scouting/classification*.jsonl and
writes scouting/yields.md: yes / sampled, overall and broken down by search
phrase and tag, for each classification round, followed by the funnel down to
the posts that support every required schema field.

A post found by several routes counts once under each of them.

Run:  python tools/scout/yields.py [--model-id claude-haiku-...]
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SCOUTING = REPO_ROOT / "scouting"

ROUNDS = [
    {
        "name": "Round 1",
        "sample": "sample.jsonl",
        "batches": "classification",
        "out": "classification.jsonl",
        "about": "The planned sample of 60 (PRD section 8): best-ranked hits of every route in turn, plus the two posts "
        "the PRD names as known examples.",
    },
    {
        "name": "Round 2",
        "sample": "sample_round2.jsonl",
        "batches": "classification_round2",
        "out": "classification_round2.jsonl",
        "about": "Every remaining candidate. Added because round 1 produced too few posts that support every required "
        "schema field (see DECISION-LOG.md, DEC-32).",
    },
]


def read_jsonl(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def load_round(spec: dict, model_id: str, date: str) -> dict | None:
    sample_path = SCOUTING / spec["sample"]
    batch_dir = SCOUTING / spec["batches"]
    if not sample_path.exists() or not list(batch_dir.glob("batch-*.json")):
        return None
    sample = {record["post_id"]: record for record in read_jsonl(sample_path)}
    labels: dict[str, dict] = {}
    problems: list[str] = []
    for path in sorted(batch_dir.glob("batch-*.json")):
        try:
            with path.open(encoding="utf-8") as handle:
                batch = json.load(handle)
        except ValueError as exc:
            problems.append(f"{path.name}: not valid JSON ({exc})")
            continue
        for label in batch["labels"]:
            post_id = label.get("post_id")
            if post_id not in sample:
                problems.append(f"{path.name}: {post_id} is not in the sample")
            elif post_id in labels:
                problems.append(f"{path.name}: {post_id} labelled twice")
            elif label.get("label") not in {"yes", "no"}:
                problems.append(f"{path.name}: {post_id} has label {label.get('label')!r}")
            else:
                labels[post_id] = {**label, "batch": batch.get("batch")}
    for post_id in sample:
        if post_id not in labels:
            problems.append(f"{spec['name']}: {post_id} is in the sample but has no label")
    if problems:
        print("\n".join(problems), file=sys.stderr)
        raise SystemExit(1)
    with (SCOUTING / spec["out"]).open("w", encoding="utf-8") as handle:
        for post_id, record in sample.items():
            label = labels[post_id]
            row = {
                "post_id": post_id, "url": record["url"], "title": record["title"], "author": record["author"],
                "published": record["published"], "routes": record["routes"], "label": label["label"],
                "reason": label["reason"], "detail": label.get("detail"), "batch": label["batch"],
                "classifier_model": model_id, "classified_on": date,
            }
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
    by_route: dict[str, dict] = {}
    for post_id, record in sample.items():
        for route in record["routes"]:
            bucket = by_route.setdefault(route, {"sampled": 0, "yes": 0})
            bucket["sampled"] += 1
            bucket["yes"] += labels[post_id]["label"] == "yes"
    return {**spec, "sample_records": sample, "labels": labels, "by_route": by_route,
            "yes": sum(label["label"] == "yes" for label in labels.values())}


def rate(yes: int, total: int) -> str:
    return f"{100 * yes / total:.0f}%" if total else "n/a"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model-id", default="claude-haiku-5-5", help="model the classifier subagents ran on")
    parser.add_argument("--date", default=dt.date.today().isoformat(), help="date the classification ran")
    args = parser.parse_args()

    candidates = read_jsonl(SCOUTING / "candidates.jsonl")
    with (SCOUTING / "search_stats.json").open(encoding="utf-8") as handle:
        stats = json.load(handle)
    rounds = [r for r in (load_round(spec, args.model_id, args.date) for spec in ROUNDS) if r]
    candidates_by_route: dict[str, int] = {}
    for record in candidates:
        for route in record["routes"]:
            candidates_by_route[route] = candidates_by_route.get(route, 0) + 1

    total_sampled = sum(len(r["sample_records"]) for r in rounds)
    total_yes = sum(r["yes"] for r in rounds)
    lines = [
        "# Scouting yields",
        "",
        f"Classification: {args.date}, model `{args.model_id}` (Claude Code subagents), prompt `tools/scout/classify_prompt.md`.",
        f"Candidate search: {stats['run_date']}, `{stats['endpoint_search']}` and `{stats['endpoint_graphql']}`.",
        "",
        "These are single-model labels on one candidate list, not an estimate of how many such posts exist on "
        "LessWrong / the Alignment Forum. \"Yes\" means the classifier judged the post a genuine write-up of a failed "
        "experiment; it does not mean the post supports every schema field (see the funnel below).",
        "",
        "## Headline",
        "",
        f"- Unique AI-related candidates found by the search: **{len(candidates)}**",
    ]
    for r in rounds:
        lines.append(
            f"- {r['name']}: **{r['yes']} yes of {len(r['sample_records'])} classified** ({rate(r['yes'], len(r['sample_records']))}). {r['about']}"
        )
    if len(rounds) > 1:
        lines.append(f"- Both rounds: **{total_yes} yes of {total_sampled} classified** ({rate(total_yes, total_sampled)}).")

    summary_path = SCOUTING / "field_audit" / "summary.json"
    if summary_path.exists():
        with summary_path.open(encoding="utf-8") as handle:
            audits = json.load(handle)
        passing = [a for a in audits if a["passes_machine_checks"]]
        lines += [
            "",
            "## Funnel: from \"yes\" to \"can seed the wiki\"",
            "",
            "A post can seed the wiki only if the post itself supports every required field (hypothesis, claim scope, "
            "method, models, result direction, failure type, a quotable sentence). A stronger model audited the \"yes\" "
            "posts field by field (`tools/scout/field_audit_prompt.md`), and `tools/scout/check_audit.py` re-checked "
            "each proposed quote against the post text.",
            "",
            f"- Classified: {total_sampled}",
            f"- Labelled yes: {total_yes}",
            f"- Audited field by field: {len(audits)}",
            f"- Support every required field, with a verbatim quote: **{len(passing)}**",
            "",
            "Which required field was missing, among audited posts that did not pass:",
            "",
            "| Field not supported by the post | Posts |",
            "|---|---|",
        ]
        missing: dict[str, int] = {}
        for audit in audits:
            for name in audit["unsupported_fields"]:
                missing[name] = missing.get(name, 0) + 1
        for name, count in sorted(missing.items(), key=lambda item: (-item[1], item[0])):
            lines.append(f"| `{name}` | {count} |")

    lines += [
        "",
        "## By route",
        "",
        "A post found by several routes is counted under each of them, so rows do not sum to the headline.",
        "",
        "| Route | Returned by API | Kept as candidates | " + " | ".join(f"{r['name']}: yes / classified" for r in rounds) + " | All: yield |",
        "|---|---|---|" + "---|" * (len(rounds) + 1),
    ]
    all_routes = sorted(set(stats["routes"]) | {route for r in rounds for route in r["by_route"]})
    for route in all_routes:
        route_stats = stats["routes"].get(route, {})
        note = f" ({route_stats['note']})" if route_stats.get("note") else ""
        cells, yes_sum, sampled_sum = [], 0, 0
        for r in rounds:
            bucket = r["by_route"].get(route, {"sampled": 0, "yes": 0})
            cells.append(f"{bucket['yes']} / {bucket['sampled']}")
            yes_sum += bucket["yes"]
            sampled_sum += bucket["sampled"]
        lines.append(
            f"| `{route}`{note} | {route_stats.get('returned', 'n/a')} | {candidates_by_route.get(route, 0)} | "
            + " | ".join(cells) + f" | {rate(yes_sum, sampled_sum)} |"
        )
    lines += [
        "",
        "Notes on the routes:",
        "",
        f"- Phrase routes: the site search, {stats['pages_per_phrase']} pages of {stats['hits_per_page']} hits per phrase, "
        "kept when the post carries an AI-related tag. The search is fuzzy full-text, not exact-phrase.",
        f"- Tag routes: the first {stats['tag_post_limit']} posts of the tag by relevance. Failure-flavoured tags keep every "
        "AI-related post; topical tags keep only posts whose title or description matches a failure phrase.",
        "- `prd-known-example`: the two posts named in the PRD, added by title.",
    ]
    for note in stats.get("notes", []):
        lines.append(f"- {note}")
    for r in rounds:
        lines += ["", f"## Posts labelled yes: {r['name'].lower()}", "", "| Post | Author | Published | Detail | Classifier's reason |", "|---|---|---|---|---|"]
        for post_id, record in r["sample_records"].items():
            label = r["labels"][post_id]
            if label["label"] == "yes":
                title = str(record["title"]).replace("|", "/").replace("[", "(").replace("]", ")")
                lines.append(
                    f"| [{title}]({record['url']}) | {record['author']} | {record['published']} | {label.get('detail') or ''} | "
                    f"{label['reason'].replace('|', '/')} |"
                )
    lines.append("")
    (SCOUTING / "yields.md").write_text("\n".join(lines), encoding="utf-8")

    print(f"{total_yes} yes of {total_sampled} classified; wrote scouting/yields.md")
    for r in rounds:
        for post_id, record in r["sample_records"].items():
            if r["labels"][post_id]["label"] == "yes":
                print(f"  {r['name']}  {post_id}  {record.get('word_count')}w  {r['labels'][post_id].get('detail')}  {record['title']}  [{record['author']}]")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

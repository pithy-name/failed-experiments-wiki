"""Step 4 of scouting (PRD section 8): write scouting/selection.md.

The choices themselves are in scouting/selection.json (who decided, which
posts, why). This script joins them with the classification labels and the
field-audit summary, so the table of supported fields is generated from the
audit data and cannot drift from it.

Run:  python tools/scout/selection.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SCOUTING = REPO_ROOT / "scouting"
REQUIRED = ["hypothesis", "claim_scope", "method", "models", "result_direction", "failure_type", "quote"]


def read_jsonl(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def cell(text: object) -> str:
    return str(text if text is not None else "").replace("|", "/").replace("\n", " ")


def main() -> int:
    with (SCOUTING / "selection.json").open(encoding="utf-8") as handle:
        selection = json.load(handle)
    selection["selected"].sort(key=lambda item: item["entry_id"])
    with (SCOUTING / "field_audit" / "summary.json").open(encoding="utf-8") as handle:
        audits = {audit["post_id"]: audit for audit in json.load(handle)}
    posts: dict[str, dict] = {}
    for name in ("classification.jsonl", "classification_round2.jsonl"):
        if (SCOUTING / name).exists():
            for row in read_jsonl(SCOUTING / name):
                posts[row["post_id"]] = {**row, "round": 1 if name == "classification.jsonl" else 2}

    problems = []
    for item in selection["selected"]:
        audit = audits.get(item["post_id"])
        if audit is None:
            problems.append(f"{item['post_id']}: selected but never audited")
            continue
        allowed = [item["exception"]] if item.get("exception") else []
        if sorted(audit["unsupported_fields"]) != sorted(allowed):
            problems.append(f"{item['post_id']}: audit says unsupported={audit['unsupported_fields']}, selection allows {allowed}")
        if not audit["quote_verbatim_in_post"] or not 0 < audit["quote_words"] <= 15:
            problems.append(f"{item['post_id']}: the audit quote failed the machine check")
    if problems:
        print("\n".join(problems), file=sys.stderr)
        return 1

    selected_ids = {item["post_id"] for item in selection["selected"]}
    strict = [item for item in selection["selected"] if not item.get("exception")]
    passing = [a for a in audits.values() if a["passes_machine_checks"]]
    lines = [
        "# Seed selection",
        "",
        f"Decided {selection['decided_on']} by the {selection['decided_by']}.",
        "",
        "## The rule",
        "",
        "A post can seed the wiki only if it is a genuine write-up of a failed experiment **and** the post itself supports "
        "every required schema field: hypothesis, claim scope, method, models, result direction, failure type, and a "
        "quotable sentence of 15 words or fewer.",
        "",
        "How it was applied:",
        "",
        "1. Haiku classifiers labelled every candidate yes or no (`scouting/yields.md`).",
        "2. A Sonnet auditor read each \"yes\" post in full and marked each required field supported or not, strictly: a "
        "research question is not a hypothesis, and a setup without data or scale is not a claim scope "
        "(`tools/scout/field_audit_prompt.md`, results in `scouting/field_audit/`).",
        "3. `tools/scout/check_audit.py` re-checked every proposed quote against the post text by machine.",
        "4. The orchestrator read the audit evidence for every post that passed, and the post itself for the exception.",
        "",
        f"**{len(passing)} posts passed all of this. All {len(strict)} of them are selected.** The tenth seed is the closest "
        "near-miss, taken as a stated exception (see below). No other post was admitted with a missing field.",
        "",
        "## The 10 seed posts",
        "",
        "| Entry | Post | Author (first listed) | Published | Topic | Made by | Experiment covered | Required fields supported |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for item in selection["selected"]:
        post, audit = posts[item["post_id"]], audits[item["post_id"]]
        supported = "all 7" if not item.get("exception") else f"6 of 7 (not `{item['exception']}`)"
        made_by = "gold draft (separate careful pass)" if item["role"] == "gold" else "`contribute` skill"
        lines.append(
            f"| `{item['entry_id']}` | [{cell(post['title'])}]({post['url']}) | {cell(post['author'])} | {post['published']} | "
            f"{cell(item['topic'])} | {made_by} | {cell(audit['primary_experiment'])} | {supported} |"
        )
    lines += ["", "## Why each one qualified", ""]
    for item in selection["selected"]:
        audit = audits[item["post_id"]]
        lines += [
            f"### `{item['entry_id']}`: {cell(posts[item['post_id']]['title'])}",
            "",
            item["why"],
            "",
            f"- Auditor's verdict: genuine = {audit['genuine']}; result direction `{audit['result_direction']}`; failure type `{audit['failure_type']}`.",
            f"- Models named in the post: {cell(audit['models'])}",
            f"- Quote found verbatim in the post ({audit['quote_words']} words): \"{audit['quote']}\"",
            f"- Info hazard: {cell(audit['info_hazard'])}. Auditor's note: {cell(audit['notes'])}",
            f"- Found in classification round {posts[item['post_id']]['round']} via: {', '.join(posts[item['post_id']]['routes'])}",
            "",
        ]
    extra = selection.get("additional_entries")
    if extra:
        lines += [
            "## Entries beyond the 10 seeds",
            "",
            extra["why"],
            "",
            "| Entry | Post | Experiment covered | Note |",
            "|---|---|---|---|",
        ]
        for item in extra["added"]:
            post = posts[item["post_id"]]
            lines.append(f"| `{item['entry_id']}` | [{cell(post['title'])}]({post['url']}) | {cell(item['experiment'])} | {cell(item.get('note', ''))} |")
        lines += ["", "Drafted by the skill but not added:", ""]
        for item in extra.get("drafted_but_not_added", []):
            lines.append(f"- {cell(posts[item['post_id']]['title'])}, \"{cell(item['experiment'])}\": {item['reason']}")
        lines += ["", extra["skipped_by_the_skill"], ""]
    lines += [
        "## What the selection does not have",
        "",
        "- **Topic spread is narrow.** Six of the ten are about sparse autoencoders or closely related interpretability "
        "methods. That is what passed the rule, not a choice: the posts that reported failures with enough structure were "
        "mostly interpretability posts.",
        "- **Ten different first authors**, which the PRD asks for.",
        "- **The seed entries quote these posts and describe their experiments. They do not judge the authors**, and "
        "author confirmation and opt-out are future work.",
        "",
        "## The PRD's two named examples",
        "",
    ]
    for example in selection["prd_named_examples"]:
        lines.append(f"- [{cell(posts[example['post_id']]['title'])}]({posts[example['post_id']]['url']}): {example['outcome']}.")
    near = [a for a in audits.values() if len(a["unsupported_fields"]) == 1 and a["post_id"] not in selected_ids]
    lines += [
        "",
        "## Near-misses: one required field short",
        "",
        "Genuine or partly genuine failure write-ups that were not seeded because the post does not state one required field.",
        "",
        "| Post | Missing field | Auditor's note |",
        "|---|---|---|",
    ]
    for audit in sorted(near, key=lambda a: (a["unsupported_fields"][0], a["title"] or "")):
        post = posts.get(audit["post_id"], {})
        lines.append(f"| [{cell(audit['title'])}]({post.get('url', '')}) | `{audit['unsupported_fields'][0]}` | {cell(audit['notes'])} |")
    lines.append("")
    (SCOUTING / "selection.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote scouting/selection.md: {len(selection['selected'])} selected ({len(strict)} strict), {len(near)} near-misses")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Skill evals (PRD section 9, D8). One command, one results file.

  python evals/run_evals.py        (or: make evals)

This script SCORES saved skill outputs against the gold set. It is deterministic
and needs no model, no network and no credentials, so it can be re-run any time
the gold entries change:

  evals/gold/<id>.md                      gold entries (ground truth once verified)
  evals/results/contribute/<id>/*.md      what the contribute skill drafted for that gold post
  evals/results/ask/<qid>.md              what the ask skill answered to each question
  evals/results/rubric_scores.json        0-2 grades for text fields, by a separate grader subagent
  evals/results/ask_judgements.json       "did the answer invent a failure?" verdicts, by a separate judge
  evals/ask_questions.json                the questions and what each should find

Producing the skill outputs and the grades is a model step; evals/README.md
gives the exact prompts. Grades are tied to the exact texts they graded by a
hash: if a gold text or a skill output changes, its grade is reported as STALE
and left out of the totals until regraded.

Outputs: evals/results/results.json and evals/results/RESULTS.md.
Results are labelled PROVISIONAL while any gold entry is unverified.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import re
import sys
from pathlib import Path

EVALS = Path(__file__).resolve().parent
REPO_ROOT = EVALS.parent
sys.path.insert(0, str(REPO_ROOT / "tools"))

import lw  # noqa: E402
import wikilib  # noqa: E402

EXACT_FIELDS = [
    "result.direction", "failure_type", "confidence_true_negative", "retry_welcome", "evidence_level",
    "info_hazard", "source.type", "source.url", "source.crosspost_url", "source.published",
    "result.effect_size", "result.ci_low", "result.ci_high", "result.n",
]
LIST_FIELDS = [
    "research_area", "method", "models.name", "models.developer", "models.access", "benchmarks", "checks_done",
    "source.authors", "source.lw_tags",
]
RUBRIC_FIELDS = ["hypothesis", "claim_scope", "limitations"]
NOT_SCORED = {
    "id, contributor.*, review.*, dates.*": "trust and provenance fields are assigned by the system, not the skill (PRD section 9)",
    "title, revival_conditions, source.title, source.section, related, body": "free wording with no single right answer; not in the PRD's scored list",
    "source.quote": "any verbatim fragment is acceptable, so it is checked for validity (quote_valid) instead of compared with gold",
}
RETRY_TYPES = wikilib.RETRY_FAILURE_TYPES


def text_hash(text: str) -> str:
    return hashlib.sha256(re.sub(r"\s+", " ", (text or "").strip()).encode("utf-8")).hexdigest()[:12]


def norm_item(value) -> str:
    return re.sub(r"[^a-z0-9]+", "-", str(value).lower()).strip("-")


def first(data: dict, path: str):
    values = wikilib.get_values(data, path)
    return values[0] if values else None


def load_json(path: Path, default):
    if not path.exists():
        return default
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


# --------------------------------------------------------------------------
# contribute eval
# --------------------------------------------------------------------------


def score_draft(gold: dict, draft: dict, gold_id: str, draft_name: str, rubric: dict) -> dict:
    fields: dict[str, dict] = {}
    for path in EXACT_FIELDS:
        expected, got = first(gold, path), first(draft, path)
        fields[path] = {"kind": "exact", "gold": expected, "skill": got, "score": 1.0 if expected == got else 0.0}
    for path in LIST_FIELDS:
        expected = {norm_item(v) for v in wikilib.get_values(gold, path)}
        got = {norm_item(v) for v in wikilib.get_values(draft, path)}
        union = expected | got
        fields[path] = {
            "kind": "list", "gold": sorted(expected), "skill": sorted(got),
            "score": 1.0 if expected == got else 0.0,
            "jaccard": round(len(expected & got) / len(union), 3) if union else 1.0,
        }
    for path in RUBRIC_FIELDS:
        gold_text, draft_text = first(gold, path) or "", first(draft, path) or ""
        entry = {"kind": "rubric_0_2", "gold_hash": text_hash(gold_text), "skill_hash": text_hash(draft_text)}
        if not gold_text and not draft_text:
            entry.update(score=1.0, raw=None, status="both_absent")
        else:
            grade = rubric.get((gold_id, draft_name, path))
            if grade is None:
                entry.update(score=None, raw=None, status="UNGRADED")
            elif grade.get("gold_hash") != entry["gold_hash"] or grade.get("skill_hash") != entry["skill_hash"]:
                entry.update(score=None, raw=grade.get("score"), status="STALE: text changed since it was graded; regrade")
            else:
                entry.update(score=grade["score"] / 2, raw=grade["score"], status="graded", reason=grade.get("reason"),
                             grader_model=grade.get("grader_model"))
        fields[path] = entry
    scored = [f["score"] for f in fields.values() if f["score"] is not None]
    quote = first(draft, "source.quote") or ""
    quote_valid = None
    post_id = lw.post_id_from_url(first(draft, "source.url") or "")
    if post_id:
        try:
            quote_valid = lw.word_count(quote) <= wikilib.MAX_QUOTE_WORDS and lw.quote_in_text(
                quote, lw.post_text(lw.fetch_post(post_id, offline=True))
            )
        except lw.SourceUnreachable:
            quote_valid = None
    schema_issues = [
        i.as_dict() for i in wikilib.validate_data(
            wikilib.prepare_new_entry(draft, repo=REPO_ROOT, contributor_type="agent", handle="eval", agent_model="eval", tool="eval"),
            quote_mode="skip",
        ) if i.level == "error"
    ]
    return {
        "draft": draft_name,
        "fields": fields,
        "accuracy": round(sum(scored) / len(scored), 4) if scored else None,
        "fields_scored": len(scored),
        "fields_unscored": [p for p, f in fields.items() if f["score"] is None],
        "quote_valid": quote_valid,
        "schema_valid": not schema_issues,
        "schema_issues": schema_issues,
    }


def contribute_eval(gold_dir: Path, results_dir: Path) -> dict:
    rubric_rows = load_json(results_dir / "rubric_scores.json", {"grades": []}).get("grades", [])
    rubric = {(row["gold_id"], row["draft"], row["field"]): row for row in rubric_rows}
    items = []
    for gold_path in sorted(gold_dir.glob("fe-*.md")):
        gold = wikilib.load_entry(gold_path).data
        gold_id = gold_path.stem
        status = gold.pop("gold_status", "missing")
        draft_paths = sorted((results_dir / "contribute" / gold_id).glob("*.md"))
        candidates = []
        for draft_path in draft_paths:
            try:
                draft, _ = wikilib.parse_entry_text(draft_path.read_text(encoding="utf-8"))
            except wikilib.EntryError as exc:
                candidates.append({"draft": draft_path.name, "accuracy": None, "unreadable": str(exc), "fields": {}, "fields_unscored": []})
                continue
            candidates.append(score_draft(gold, draft, gold_id, draft_path.name, rubric))
        readable = [c for c in candidates if c.get("accuracy") is not None]
        best = max(readable, key=lambda c: c["accuracy"]) if readable else None
        items.append(
            {
                "gold_id": gold_id, "gold_status": status, "source_url": first(gold, "source.url"),
                "drafts_produced": len(draft_paths), "scored_draft": best["draft"] if best else None,
                "result": best, "other_drafts": [c["draft"] for c in candidates if c is not best],
            }
        )
    per_field: dict[str, dict] = {}
    for path in EXACT_FIELDS + LIST_FIELDS + RUBRIC_FIELDS:
        scores = [item["result"]["fields"][path]["score"] for item in items if item["result"]]
        usable = [s for s in scores if s is not None]
        per_field[path] = {
            "accuracy": round(sum(usable) / len(usable), 4) if usable else None,
            "n": len(usable), "unscored": len(scores) - len(usable),
        }
    field_accuracies = [f["accuracy"] for f in per_field.values() if f["accuracy"] is not None]
    return {
        "items": items,
        "per_field": per_field,
        "overall_accuracy": round(sum(field_accuracies) / len(field_accuracies), 4) if field_accuracies else None,
        "overall_definition": "mean of per-field accuracies; exact and list fields score 0 or 1 per item, rubric fields score grade/2",
        "gold_items": len(items),
        "items_with_output": sum(1 for item in items if item["result"]),
        "not_scored": NOT_SCORED,
        "run": load_json(results_dir / "contribute" / "run.json", {}),
    }


# --------------------------------------------------------------------------
# ask eval
# --------------------------------------------------------------------------

SECTIONS = ["Already tried", "Where it went wrong", "What to avoid", "Worth retrying", "Not found"]
ID_RE = re.compile(r"fe-\d{4}-\d{4}")


def split_sections(answer: str) -> dict[str, str]:
    sections: dict[str, str] = {}
    current = None
    for line in answer.split("\n"):
        heading = re.match(r"^#{1,4}\s*(?:\d+\.\s*)?\**(.+?)\**:?\s*$", line)
        name = next((s for s in SECTIONS if heading and heading.group(1).strip().lower() == s.lower()), None)
        if name:
            current = name
            sections[current] = ""
        elif current:
            sections[current] += line + "\n"
    return sections


def ask_eval(results_dir: Path, gold_dir: Path, entries_dir: Path, questions_path: Path | None = None) -> dict:
    questions = load_json(questions_path or EVALS / "ask_questions.json", {"questions": []})["questions"]
    judgements = {row["qid"]: row for row in load_json(results_dir / "ask_judgements.json", {"judgements": []}).get("judgements", [])}
    known_ids = {path.stem for path in entries_dir.glob("fe-*.md")}
    items = []
    for question in questions:
        qid = question["qid"]
        answer_path = results_dir / "ask" / f"{qid}.md"
        item = {"qid": qid, "question": question["question"], "expected_entry_id": question.get("expected_entry_id")}
        if not answer_path.exists():
            item.update(passed=False, status="NO ANSWER FILE")
            items.append(item)
            continue
        answer = answer_path.read_text(encoding="utf-8")
        sections = split_sections(answer)
        cited_everywhere = set(ID_RE.findall(answer))
        tried_ids = set(ID_RE.findall(sections.get("Already tried", "")))
        checks = {
            "has_all_five_sections": all(name in sections for name in SECTIONS),
            "cites_only_existing_entries": cited_everywhere <= known_ids,
        }
        judgement = judgements.get(qid)
        if judgement is None:
            checks["judge_no_invented_failures"] = None
            judge_status = "UNJUDGED"
        elif judgement.get("answer_hash") != text_hash(answer):
            checks["judge_no_invented_failures"] = None
            judge_status = "STALE: answer changed since it was judged; rejudge"
        else:
            checks["judge_no_invented_failures"] = not judgement["invents_failures"]
            judge_status = "judged"
        expected_id = question.get("expected_entry_id")
        if expected_id:
            gold_path = gold_dir / f"{expected_id}.md"
            expected_type = wikilib.load_entry(gold_path).data.get("failure_type") if gold_path.exists() else None
            wrong_lines = [line for line in sections.get("Where it went wrong", "").split("\n") if expected_id in line]
            wrong_block = " ".join(wrong_lines) if wrong_lines else sections.get("Where it went wrong", "")
            checks["cites_expected_entry_under_already_tried"] = expected_id in tried_ids
            checks["failure_type_matches_gold"] = bool(expected_type) and expected_type in wrong_block
            item["expected_failure_type_from_gold"] = expected_type
        else:
            not_found = sections.get("Not found", "").strip()
            checks["already_tried_cites_nothing"] = not tried_ids
            checks["not_found_section_says_so"] = bool(not_found) and bool(re.search(r"\bno (?:entries|entry)\b|nothing|not found|does not (?:have|hold|contain)|none", not_found, re.I))
        item.update(
            checks=checks, judge_status=judge_status,
            judge_reason=(judgement or {}).get("reason"),
            entries_cited=sorted(cited_everywhere),
            passed=all(value is True for value in checks.values()),
            status="scored" if all(value is not None for value in checks.values()) else "INCOMPLETE: needs judge",
        )
        items.append(item)
    with_match = [i for i in items if i.get("expected_entry_id")]
    without = [i for i in items if not i.get("expected_entry_id")]
    return {
        "items": items,
        "passed": sum(1 for i in items if i["passed"]), "total": len(items),
        "match_questions": {"passed": sum(1 for i in with_match if i["passed"]), "total": len(with_match)},
        "no_match_questions": {"passed": sum(1 for i in without if i["passed"]), "total": len(without)},
        "pass_rule": "match question: cites the expected entry under 'Already tried', names the gold failure_type under "
        "'Where it went wrong', cites only existing entries, and a separate judge finds no invented failure. "
        "No-match question: 'Already tried' cites nothing, 'Not found' says so, and the judge finds no invented failure.",
        "run": load_json(results_dir / "ask" / "run.json", {}),
    }


# --------------------------------------------------------------------------
# Report
# --------------------------------------------------------------------------


def pct(value) -> str:
    return "n/a" if value is None else f"{100 * value:.0f}%"


def render(results: dict) -> str:
    c, a = results["contribute"], results["ask"]
    lines = ["# Eval results", ""]
    if results["provisional"]:
        lines += [
            "> **PROVISIONAL.** " + results["provisional_reason"],
            "> These numbers compare one model's drafts with another model pass, not with human ground truth.",
            "> Do not cite them as accuracy until the gold entries are verified and this file is regenerated.",
            "",
        ]
    lines += [
        f"Generated {results['generated']} by `python evals/run_evals.py` (deterministic re-scoring of saved outputs).",
        "",
        "This is a spot-check on 5 posts with one model vendor. It is not a benchmark.",
        "",
        "## `contribute` skill: field accuracy against the gold set",
        "",
        f"- Gold entries: {c['gold_items']} ({', '.join(sorted({i['gold_status'] for i in c['items']})) or 'none'})",
        f"- Gold posts with a skill draft: {c['items_with_output']}",
        f"- **Overall field accuracy: {pct(c['overall_accuracy'])}** ({c['overall_definition']})",
        f"- Skill run: {json.dumps(c['run'], ensure_ascii=False) if c['run'] else 'no run record'}",
        "",
        "| Field | Kind | Accuracy | Items scored | Unscored |",
        "|---|---|---|---|---|",
    ]
    kinds = {**{p: "exact" for p in EXACT_FIELDS}, **{p: "list (set match)" for p in LIST_FIELDS}, **{p: "rubric 0-2" for p in RUBRIC_FIELDS}}
    for path, stats in c["per_field"].items():
        lines.append(f"| `{path}` | {kinds[path]} | {pct(stats['accuracy'])} | {stats['n']} | {stats['unscored']} |")
    lines += ["", "Per gold entry:", "", "| Gold entry | Gold status | Drafts | Accuracy | Quote valid | Schema valid | Unscored fields |", "|---|---|---|---|---|---|---|"]
    for item in c["items"]:
        r = item["result"]
        if not r:
            lines.append(f"| `{item['gold_id']}` | {item['gold_status']} | {item['drafts_produced']} | no output | | | |")
            continue
        lines.append(
            f"| `{item['gold_id']}` | {item['gold_status']} | {item['drafts_produced']} | {pct(r['accuracy'])} | "
            f"{r['quote_valid']} | {r['schema_valid']} | {', '.join(r['fields_unscored']) or '-'} |"
        )
    lines += ["", "Mismatches (gold vs skill), exact and list fields:", ""]
    any_mismatch = False
    for item in c["items"]:
        if not item["result"]:
            continue
        for path, f in item["result"]["fields"].items():
            if f["kind"] in {"exact", "list"} and f["score"] == 0.0:
                any_mismatch = True
                lines.append(f"- `{item['gold_id']}` `{path}`: gold `{f['gold']}` / skill `{f['skill']}`")
    if not any_mismatch:
        lines.append("- none")
    lines += ["", "Not scored:", ""] + [f"- `{k}`: {v}" for k, v in c["not_scored"].items()]
    lines += [
        "",
        "## `ask` skill",
        "",
        f"- **Passed: {a['passed']} of {a['total']}** (match questions {a['match_questions']['passed']}/{a['match_questions']['total']}, "
        f"no-match questions {a['no_match_questions']['passed']}/{a['no_match_questions']['total']})",
        f"- Pass rule: {a['pass_rule']}",
        f"- Skill run: {json.dumps(a['run'], ensure_ascii=False) if a['run'] else 'no run record'}",
        "",
        "| Question | Expects | Passed | Status | Failed checks |",
        "|---|---|---|---|---|",
    ]
    for item in a["items"]:
        failed = [k for k, v in (item.get("checks") or {}).items() if v is not True]
        lines.append(
            f"| `{item['qid']}` | {item.get('expected_entry_id') or 'nothing (no-match)'} | {'yes' if item['passed'] else 'NO'} | "
            f"{item.get('status')} | {', '.join(failed) or '-'} |"
        )
    lines += [
        "",
        "## Limits",
        "",
        "- 5 gold items and 7 questions: a spot-check, not a benchmark.",
        "- One model vendor wrote the drafts, the answers, the grades and (until verified) the gold entries.",
        "- Rubric grades and invented-failure judgements come from a grader subagent and are to be spot-checked by the maintainer.",
        "- Keyword-level checks on `ask` answers can pass an answer that is right for the wrong reason; the judge verdict is the backstop.",
        "",
    ]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Score saved skill outputs against the gold set.")
    parser.add_argument("--gold", default=str(EVALS / "gold"))
    parser.add_argument("--results", default=str(EVALS / "results"))
    parser.add_argument("--entries", default=str(REPO_ROOT / "entries"))
    parser.add_argument("--questions", default=str(EVALS / "ask_questions.json"))
    args = parser.parse_args(argv)
    gold_dir, results_dir, entries_dir = Path(args.gold), Path(args.results), Path(args.entries)
    results_dir.mkdir(parents=True, exist_ok=True)

    contribute = contribute_eval(gold_dir, results_dir)
    ask = ask_eval(results_dir, gold_dir, entries_dir, Path(args.questions))
    pending = sorted(item["gold_id"] for item in contribute["items"] if item["gold_status"] != "verified")
    results = {
        "generated": dt.datetime.now().astimezone().isoformat(timespec="seconds"),
        "provisional": bool(pending) or not contribute["items"],
        "provisional_reason": (
            f"{len(pending)} of {len(contribute['items'])} gold entries are model drafts awaiting the maintainer's verification "
            f"({', '.join(pending)})." if pending else ("No gold entries found." if not contribute["items"] else "")
        ),
        "contribute": contribute,
        "ask": ask,
    }
    with (results_dir / "results.json").open("w", encoding="utf-8") as handle:
        json.dump(results, handle, indent=2, ensure_ascii=False)
        handle.write("\n")
    (results_dir / "RESULTS.md").write_text(render(results), encoding="utf-8")
    label = "PROVISIONAL " if results["provisional"] else ""
    print(f"{label}contribute: overall field accuracy {pct(contribute['overall_accuracy'])} on {contribute['items_with_output']}/{contribute['gold_items']} gold posts")
    print(f"{label}ask: {ask['passed']}/{ask['total']} passed")
    print(f"wrote {results_dir / 'results.json'} and {results_dir / 'RESULTS.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

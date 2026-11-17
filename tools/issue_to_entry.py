"""Human contribution path (D2): turn a submitted GitHub issue form into an entry file.

Run by .github/workflows/issue-to-pr.yml. It reads the issue body from the
ISSUE_BODY environment variable (never from the command line, so issue text is
never interpreted by a shell), builds the entry, validates it and writes
entries/<id>.md. The workflow then commits that file and opens a pull request.

  ISSUE_BODY=... ISSUE_AUTHOR=octocat ISSUE_NUMBER=12 python tools/issue_to_entry.py --report report.md

Exit code 1 when the form cannot be turned into a valid entry; the report says why.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import lw  # noqa: E402
import wikilib  # noqa: E402

TEMPLATE_PATH = Path(__file__).resolve().parent.parent / ".github" / "ISSUE_TEMPLATE" / "new-entry.yml"


def load_template() -> dict:
    import yaml
    return yaml.safe_load(TEMPLATE_PATH.read_text(encoding="utf-8"))


def form_answers(draft: dict, body: str) -> dict[str, str]:
    """Each form field's answer, as text, keyed by the converter's field key."""
    result, source = draft.get("result", {}), draft["source"]

    def number(value) -> str:
        return "" if value is None else str(value)

    # The Method dropdown only offers its listed options; anything else goes under Other methods.
    listed = set(next(i for i in load_template()["body"] if i.get("id") == "method")["attributes"]["options"])
    chosen = [m for m in draft["method"] if m in listed]
    other = [m for m in draft["method"] if m not in listed]

    return {
        "title": draft["title"],
        "research_area": ", ".join(draft["research_area"]),
        "hypothesis": draft["hypothesis"],
        "claim_scope": draft["claim_scope"],
        "method": ", ".join(chosen),
        "method_other": ", ".join(other),
        "models": "\n".join(" | ".join(str(model.get(key, "unknown")) for key in ("name", "developer", "version", "size", "access"))
                            for model in draft["models"]),
        "benchmarks": "\n".join(draft.get("benchmarks", [])),
        "result_direction": result.get("direction", ""),
        "effect_size": number(result.get("effect_size")),
        "ci_low": number(result.get("ci_low")),
        "ci_high": number(result.get("ci_high")),
        "n": number(result.get("n")),
        "failure_type": draft["failure_type"],
        "evidence_strength": draft["evidence_strength"],
        "checks_done": ", ".join(draft.get("checks_done", [])),
        "limitations": draft.get("limitations", ""),
        "revival_conditions": draft.get("revival_conditions", ""),
        "retry_welcome": "yes" if draft.get("retry_welcome") else "no",
        "evidence_level": draft["evidence_level"],
        "source_url": source["url"],
        "crosspost_url": source.get("crosspost_url", ""),
        "source_title": source["title"],
        "source_authors": ", ".join(source["authors"]),
        "source_published": str(source["published"]),
        "source_section": source.get("section", ""),
        "source_quote": source["quote"],
        "lw_tags": ", ".join(source.get("lw_tags", [])),
        "experiment_date": str((draft.get("dates") or {}).get("experiment", "")),
        "related": ", ".join(f"{item['id']}:{item['relation']}" for item in draft.get("related", [])),
        # the form's own option text, which the converter maps back to the schema value
        "info_hazard": {v: k for k, v in INFO_HAZARD_FROM_FORM.items()}.get(draft.get("info_hazard", "none"), draft.get("info_hazard", "none")),
        "ai_draft_model": "",
        "notes": body,
    }


def form_body(answers: dict[str, str], ticked: bool = True) -> str:
    """The text GitHub sends for a submitted form, with the labels taken from the form itself."""
    parts = []
    for item in load_template()["body"]:
        label = (item.get("attributes") or {}).get("label")
        if item.get("type") == "markdown" or not label:
            continue
        key = LABELS.get(label)
        if key is None:
            raise SystemExit(f"the issue form has a field the converter does not know: '{label}'")
        if key == "confirm":
            options = item["attributes"]["options"]
            answer = "\n".join(f"- [{'x' if ticked else ' '}] {option['label']}" for option in options)
        else:
            answer = answers[key]
        parts.append(f"### {label}\n\n{answer if str(answer).strip() else '_No response_'}\n")
    return "\n".join(parts)

NO_RESPONSE = {"_no response_", "none", ""}

# GitHub reserves "None" as a dropdown option, so the form says "no hazard" for the schema's "none".
INFO_HAZARD_FROM_FORM = {"no hazard": "none"}

# Form label -> key used below. Labels must match .github/ISSUE_TEMPLATE/new-entry.yml.
LABELS = {
    "Entry title": "title",
    "Research area": "research_area",
    "Hypothesis": "hypothesis",
    "Claim scope": "claim_scope",
    "Method": "method",
    "Other methods": "method_other",
    "Models": "models",
    "Benchmarks": "benchmarks",
    "Result direction": "result_direction",
    "Effect size": "effect_size",
    "Confidence interval low": "ci_low",
    "Confidence interval high": "ci_high",
    "Sample size": "n",
    "Likely reason": "failure_type",
    "Strength of evidence": "evidence_strength",
    "Checks done": "checks_done",
    "Limitations": "limitations",
    "Revival conditions": "revival_conditions",
    "Retry welcome": "retry_welcome",
    "Evidence level": "evidence_level",
    "Source URL": "source_url",
    "Crosspost URL": "crosspost_url",
    "Source title": "source_title",
    "Source authors": "source_authors",
    "Source published date": "source_published",
    "Source section": "source_section",
    "Source quote": "source_quote",
    "LessWrong tags": "lw_tags",
    "Experiment date": "experiment_date",
    "Related entries": "related",
    "Info hazard": "info_hazard",
    "AI first-pass model": "ai_draft_model",
    "Notes": "notes",
    "Before you submit": "confirm",
}


class FormError(Exception):
    pass


def parse_issue_body(body: str) -> dict[str, str]:
    """GitHub renders an issue form as '### Label' headings, each followed by the answer."""
    fields: dict[str, str] = {}
    current: str | None = None
    lines: list[str] = []
    for line in (body or "").replace("\r\n", "\n").split("\n"):
        heading = re.match(r"^###\s+(.*\S)\s*$", line)
        if heading and heading.group(1) in LABELS:
            if current:
                fields[current] = "\n".join(lines).strip()
            current, lines = LABELS[heading.group(1)], []
        elif current:
            lines.append(line)
    if current:
        fields[current] = "\n".join(lines).strip()
    return {key: ("" if value.strip().lower() in NO_RESPONSE else value) for key, value in fields.items()}


def _split(value: str) -> list[str]:
    return [part.strip() for part in re.split(r"[,\n]", value or "") if part.strip()]


def _methods(chosen: str, other: str) -> list[str]:
    """Dropdown choices first, then any typed-in methods; normalized, without repeats."""
    out: list[str] = []
    for part in _split(chosen) + _split(other):
        tag = wikilib.normalize_tag(part)
        if tag and tag not in out:
            out.append(tag)
    return out


def _number(value: str, label: str, integer: bool = False):
    if not value:
        return None
    try:
        return int(value) if integer else float(value)
    except ValueError as exc:
        raise FormError(f"'{label}' must be a {'whole ' if integer else ''}number, got '{value}'") from exc


def _models(value: str) -> list[dict]:
    models = []
    for line in [line.strip() for line in (value or "").split("\n") if line.strip()]:
        parts = [part.strip() for part in line.split("|")]
        if len(parts) != 5:
            raise FormError(f"Models: each line needs 5 parts separated by '|' (name | developer | version | size | access), got: '{line}'")
        models.append(dict(zip(["name", "developer", "version", "size", "access"], [part or "unknown" for part in parts])))
    return models


def _related(value: str) -> list[dict]:
    related = []
    for item in _split(value):
        entry_id, _, relation = item.partition(":")
        related.append({"id": entry_id.strip(), "relation": relation.strip()})
    return related


def entry_from_fields(fields: dict[str, str]) -> tuple[dict, str]:
    """Schema-shaped entry (without the fields the system owns) and the free-text body."""
    def get(key: str) -> str:
        return fields.get(key, "")

    url = get("source_url")
    result = {"direction": get("result_direction")}
    for key, label, integer in (("effect_size", "Effect size", False), ("ci_low", "Confidence interval low", False),
                                ("ci_high", "Confidence interval high", False), ("n", "Sample size", True)):
        number = _number(get(key), label, integer)
        if number is not None:
            result[key] = number

    source = {
        "type": lw.source_type_from_url(url) or "lesswrong",
        "url": url,
        "title": get("source_title"),
        "authors": _split(get("source_authors")),
        "published": get("source_published"),
        "quote": get("source_quote"),
    }
    for key, target in (("crosspost_url", "crosspost_url"), ("source_section", "section")):
        if get(key):
            source[target] = get(key)
    if get("lw_tags"):
        source["lw_tags"] = _split(get("lw_tags"))
    if source.get("crosspost_url", "").startswith("https://www.alignmentforum.org/"):
        source["type"] = "alignment_forum"

    data: dict = {
        "title": get("title"),
        "research_area": _split(get("research_area")),
        "hypothesis": get("hypothesis"),
        "claim_scope": get("claim_scope"),
        "method": _methods(get("method"), get("method_other")),
        "models": _models(get("models")),
        "result": result,
        "failure_type": get("failure_type"),
        "evidence_strength": get("evidence_strength"),
        "retry_welcome": get("retry_welcome").strip().lower() == "yes",
        "evidence_level": get("evidence_level"),
        "source": source,
        "info_hazard": INFO_HAZARD_FROM_FORM.get(get("info_hazard"), get("info_hazard")) or "none",
    }
    for key in ("limitations", "revival_conditions"):
        if get(key):
            data[key] = get(key)
    for key in ("benchmarks", "checks_done"):
        if get(key):
            data[key] = _split(get(key))
    if get("related"):
        data["related"] = _related(get("related"))
    if get("experiment_date"):
        data["dates"] = {"experiment": get("experiment_date")}
    return data, get("notes")


def confirmations_ticked(fields: dict[str, str]) -> bool:
    boxes = re.findall(r"^- \[( |x|X)\]", fields.get("confirm", ""), flags=re.MULTILINE)
    return bool(boxes) and all(box.lower() == "x" for box in boxes)


def convert(body: str, author: str, repo: Path, quote_mode: str = "online") -> dict:
    fields = parse_issue_body(body)
    if not fields:
        return {"ok": False, "problems": ["The issue body does not look like the new-entry form."]}
    if not confirmations_ticked(fields):
        return {"ok": False, "problems": ["Both boxes under 'Before you submit' must be ticked."]}
    try:
        draft, notes = entry_from_fields(fields)
    except FormError as exc:
        return {"ok": False, "problems": [str(exc)]}
    data = wikilib.prepare_new_entry(draft, repo=repo, contributor_type="human", handle=author)
    model = fields.get("ai_draft_model", "").strip()
    if model:
        data["contributor"]["note"] = f"First pass drafted by {model}; edited and submitted by a person."
    issues = wikilib.validate_data(data, file_name=f"{data['id']}.md", quote_mode=quote_mode)
    if wikilib.has_errors(issues):
        return {"ok": False, "problems": [f"[{i.code}] {i.message}" for i in issues if i.level == "error"]}
    return {
        "ok": True,
        "id": data["id"],
        "title": data["title"],
        "text": wikilib.dump_entry(data, notes),
        "warnings": [f"[{i.code}] {i.message}" for i in issues if i.level == "warning"],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--body-file", help="read the issue body from a file instead of ISSUE_BODY")
    parser.add_argument("--report", help="write a Markdown report (for the issue comment / pull-request body) here")
    parser.add_argument("--quotes", choices=["online", "strict", "cached", "skip"], default="online")
    parser.add_argument("--repo", default=str(wikilib.REPO_ROOT))
    args = parser.parse_args(argv)

    body = Path(args.body_file).read_text(encoding="utf-8") if args.body_file else os.environ.get("ISSUE_BODY", "")
    author = os.environ.get("ISSUE_AUTHOR", "").strip() or wikilib.PLACEHOLDER_HANDLE
    number = os.environ.get("ISSUE_NUMBER", "").strip()
    repo = Path(args.repo)

    outcome = convert(body, author, repo, args.quotes)
    if outcome["ok"]:
        path = repo / "entries" / f"{outcome['id']}.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(outcome["text"], encoding="utf-8")
        report = [
            f"Entry `{outcome['id']}` created from issue #{number} by @{author} (human contributor).",
            "",
            "- Validation: passed (schema, closed lists, source URL, quote length).",
            "- Quote check: " + ("NOT run, the source could not be fetched" if any("source_unreachable" in w or "quote_unchecked" in w for w in outcome["warnings"]) else "the quote was found in the source post."),
            "- Review status: `unreviewed` until someone reviews it.",
        ]
        output = os.environ.get("GITHUB_OUTPUT")
        if output:
            with open(output, "a", encoding="utf-8") as handle:
                handle.write(f"entry_id={outcome['id']}\nentry_file=entries/{outcome['id']}.md\n")
    else:
        report = ["The form could not be turned into a valid entry:", ""] + [f"- {p}" for p in outcome["problems"]] + [
            "", "Please fix these in the issue text, then close and reopen the issue to run the conversion again.",
        ]
    if args.report:
        Path(args.report).write_text("\n".join(report) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in outcome.items() if k != "text"}, indent=2, ensure_ascii=False))
    return 0 if outcome["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

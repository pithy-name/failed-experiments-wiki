"""Turn an AI-drafted entry into a pre-filled "New entry" issue-form link.

A person opens the link, checks and edits every field, picks the dropdown values
listed alongside it, and submits. The form records which model wrote the first
pass (the "AI first-pass model" field), so the entry is a person's but its
provenance stays visible.

GitHub pre-fills text fields from URL parameters named by the field's `id`. Its
docs do not say dropdowns can be pre-filled, so dropdown and checkbox answers are
printed for the person to pick instead of put in the link.

Usage:
  python tools/form_link.py --file draft.md --model claude-sonnet-5-5 [--repo owner/name]

Reusability: PROJECT-INTERNAL
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from urllib.parse import quote, urlencode

sys.path.insert(0, str(Path(__file__).resolve().parent))
import issue_to_entry  # noqa: E402
import wikilib  # noqa: E402

# Above this length GitHub may answer "414 URI Too Long"; 8,000 is a conservative cap.
MAX_URL = 8000
TEXT_TYPES = ("input", "textarea")


def _answers(draft: dict, body: str, model: str) -> dict[str, str]:
    answers = issue_to_entry.form_answers(draft, body)
    answers["ai_draft_model"] = model
    return answers


def submitted_body(draft: dict, body: str, model: str) -> str:
    """The issue text GitHub would send if the person submitted the link unchanged."""
    return issue_to_entry.form_body(_answers(draft, body, model))


def build(draft: dict, body: str, model: str, repo: str) -> tuple[str, list[tuple[str, str]], list[str]]:
    """(link, choices to pick by hand as (label, value), warnings)."""
    answers = _answers(draft, body, model)
    text_params: dict[str, str] = {}
    choices: list[tuple[str, str]] = []
    for item in issue_to_entry.load_template()["body"]:
        attrs = item.get("attributes") or {}
        label = attrs.get("label")
        if item.get("type") == "markdown" or not label:
            continue
        key = issue_to_entry.LABELS[label]
        if key == "confirm":
            choices.append((label, "tick both boxes after checking every field"))
        elif item["type"] in TEXT_TYPES:
            if str(answers[key]).strip():
                text_params[item["id"]] = str(answers[key])
        elif str(answers[key]).strip():
            choices.append((label, str(answers[key])))

    def url_for(params: dict[str, str]) -> str:
        head = {"template": issue_to_entry.TEMPLATE_PATH.name, "title": f"[entry] {draft['title']}"}
        return f"https://github.com/{repo}/issues/new?" + urlencode({**head, **params}, quote_via=quote)

    warnings: list[str] = []
    labels_by_id = {item["id"]: item["attributes"]["label"] for item in issue_to_entry.load_template()["body"] if item.get("id")}
    while len(url_for(text_params)) > MAX_URL and text_params:
        longest = max((k for k in text_params if k != "ai_draft_model"), key=lambda k: len(text_params[k]))
        choices.append((labels_by_id[longest], text_params.pop(longest)))
        warnings.append(f"'{labels_by_id[longest]}' was too long for the link; paste it into the form by hand.")
    return url_for(text_params), choices, warnings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Pre-filled issue-form link from an AI-drafted entry.")
    parser.add_argument("--file", required=True, help="draft entry: Markdown with YAML front matter")
    parser.add_argument("--model", required=True, help="the model that drafted it, recorded in the form")
    parser.add_argument("--repo", default="pithy-name/failed-experiments-wiki", help="GitHub owner/name")
    args = parser.parse_args(argv)
    data, body = wikilib.parse_entry_text(Path(args.file).read_text(encoding="utf-8"))
    draft = {k: v for k, v in data.items() if k not in ("id", "contributor", "review", "dates")}
    url, choices, warnings = build(draft, body, args.model, args.repo)
    print(url)
    print("\nPick these in the form:")
    for label, value in choices:
        print(f"- {label}: {value}")
    for warning in warnings:
        print(f"Warning: {warning}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

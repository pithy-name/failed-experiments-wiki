"""The form-link tool: an AI draft becomes a pre-filled issue-form link a person edits and submits."""
import copy
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import yaml

import form_link
import issue_to_entry
import wikilib

REPO_ROOT = Path(__file__).resolve().parent.parent
TEMPLATE = yaml.safe_load((REPO_ROOT / ".github" / "ISSUE_TEMPLATE" / "new-entry.yml").read_text(encoding="utf-8"))
TYPES = {item["id"]: item["type"] for item in TEMPLATE["body"] if item.get("id")}


def _draft():
    entry = next(e for e in wikilib.load_entries(REPO_ROOT / "entries") if e.id == "fe-2026-0006")
    return {k: v for k, v in copy.deepcopy(entry.data).items() if k not in ("id", "contributor", "review", "dates")}, entry.body


def test_link_prefills_text_fields_by_id_and_lists_the_dropdowns():
    draft, body = _draft()
    url, choices, warnings = form_link.build(draft, body, model="claude-sonnet-5-5", repo="owner/wiki")
    parsed = urlparse(url)
    assert parsed.netloc == "github.com" and parsed.path == "/owner/wiki/issues/new"
    query = {k: v[0] for k, v in parse_qs(parsed.query).items()}
    assert query["template"] == "new-entry.yml"
    assert query["title"] == f"[entry] {draft['title']}"
    assert query["ai_draft_model"] == "claude-sonnet-5-5"
    assert query["hypothesis"] == draft["hypothesis"]
    assert query["source_quote"] == draft["source"]["quote"]
    # only text fields go in the link; dropdowns and checkboxes are listed for the person to pick
    assert all(TYPES[k] in ("input", "textarea") for k in query if k not in ("template", "title"))
    chosen = dict(choices)
    assert chosen["Failure type"] == draft["failure_type"]
    # every listed choice is an option the form actually offers
    options = {item["attributes"]["label"]: item["attributes"]["options"] for item in TEMPLATE["body"] if item["type"] == "dropdown"}
    for label, value in choices:
        if label in options:
            assert all(v.strip() in options[label] for v in value.split(",")), (label, value)
    assert "Before you submit" in " ".join(label for label, _ in choices) or any("tick" in v.lower() for _, v in choices)
    assert not warnings


def test_a_submitted_link_round_trips_to_the_same_entry():
    draft, body = _draft()
    fields = issue_to_entry.parse_issue_body(form_link.submitted_body(draft, body, model="claude-sonnet-5-5"))
    converted, notes = issue_to_entry.entry_from_fields(fields)
    assert wikilib.normalize_data(converted) == wikilib.normalize_data(draft)
    assert notes.strip() == body.strip()


def test_a_link_that_is_too_long_warns_and_moves_the_longest_fields_to_the_list():
    draft, body = _draft()
    draft["hypothesis"] = "word " * 3000
    url, choices, warnings = form_link.build(draft, body, model="m", repo="owner/wiki")
    assert len(url) <= form_link.MAX_URL
    assert warnings
    assert "Hypothesis" in dict(choices)


def test_ai_first_pass_model_is_recorded_as_a_contributor_note(tmp_path):
    draft, body = _draft()
    issue = form_link.submitted_body(draft, body, model="claude-sonnet-5-5")
    outcome = issue_to_entry.convert(issue, "octocat", REPO_ROOT, quote_mode="skip")
    assert outcome["ok"], outcome
    data, _ = wikilib.parse_entry_text(outcome["text"])
    assert data["contributor"]["type"] == "human"
    assert "claude-sonnet-5-5" in data["contributor"]["note"]


def test_no_ai_model_means_no_note(tmp_path):
    draft, body = _draft()
    issue = form_link.submitted_body(draft, body, model="")
    outcome = issue_to_entry.convert(issue, "octocat", REPO_ROOT, quote_mode="skip")
    assert outcome["ok"], outcome
    data, _ = wikilib.parse_entry_text(outcome["text"])
    assert "note" not in data["contributor"]

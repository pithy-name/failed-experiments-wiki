"""D2: the issue form becomes a schema-valid entry marked contributor.type: human."""
from pathlib import Path

import yaml

import issue_to_entry
import wikilib
from conftest import FAKE_QUOTE, FAKE_URL

REPO_ROOT = Path(__file__).resolve().parent.parent

# What GitHub sends as the issue body for a submitted form: '### Label', blank line, answer.
ISSUE_BODY = f"""### Entry title

Activation steering on GPT-2 small did not change refusal rates

### Research area

steering, interpretability

### Hypothesis

Adding a refusal direction to the residual stream raises refusal rates.

### Claim scope

One steering vector, one layer, GPT-2 small, 200 prompts; nothing beyond that was tested.

### Method

activation-steering

### Other methods

Probing

### Models

GPT-2 small | OpenAI | unknown | 124M | open-weight
GPT-2 medium | OpenAI |  | 355M | open-weight

### Benchmarks

_No response_

### Result direction

null

### Effect size

_No response_

### Confidence interval low

_No response_

### Confidence interval high

_No response_

### Sample size

200

### Likely reason

hypothesis_false

### Strength of evidence

low

### Checks done

seed-sweep

### Limitations

Only one layer was tried.

### Revival conditions

_No response_

### Retry welcome

yes

### Evidence level

author_report

### Source URL

{FAKE_URL}

### Crosspost URL

_No response_

### Source title

A test post

### Source authors

Test Author, Second Author

### Source published date

2025-03-01

### Source section

_No response_

### Source quote

{FAKE_QUOTE}

### LessWrong tags

_No response_

### Experiment date

_No response_

### Related entries

_No response_

### Info hazard

none

### Notes

We stopped after one layer.

### A heading the author typed inside notes

still part of the notes

### Before you submit

- [X] The entry describes the experiment and does not judge the people who ran it.
- [X] The quote is copied exactly from the post and everything else is in my own words.
"""


def test_form_labels_match_the_issue_template():
    template = yaml.safe_load((REPO_ROOT / ".github" / "ISSUE_TEMPLATE" / "new-entry.yml").read_text(encoding="utf-8"))
    labels = {item["attributes"]["label"] for item in template["body"] if item["type"] != "markdown"}
    assert labels == set(issue_to_entry.LABELS)
    assert "new-entry" in template["labels"]


def test_template_dropdowns_match_the_schema_closed_lists():
    template = yaml.safe_load((REPO_ROOT / ".github" / "ISSUE_TEMPLATE" / "new-entry.yml").read_text(encoding="utf-8"))
    options = {item["id"]: item["attributes"]["options"] for item in template["body"] if item["type"] == "dropdown"}
    props = wikilib.load_schema()["properties"]
    assert options["research_area"] == props["research_area"]["items"]["enum"]
    assert options["result_direction"] == props["result"]["properties"]["direction"]["enum"]
    assert options["failure_type"] == props["failure_type"]["enum"]
    assert options["evidence_strength"] == props["evidence_strength"]["enum"]
    assert options["evidence_level"] == props["evidence_level"]["enum"]
    form_to_schema = issue_to_entry.INFO_HAZARD_FROM_FORM
    assert [form_to_schema.get(o, o) for o in options["info_hazard"]] == props["info_hazard"]["enum"]


def test_method_is_a_sorted_multiselect_covering_every_method_in_the_wiki():
    template = yaml.safe_load((REPO_ROOT / ".github" / "ISSUE_TEMPLATE" / "new-entry.yml").read_text(encoding="utf-8"))
    field = next(i for i in template["body"] if i.get("id") == "method")
    assert field["type"] == "dropdown" and field["attributes"]["multiple"] is True
    options = field["attributes"]["options"]
    assert options == sorted(set(options))
    assert all(o == wikilib.normalize_tag(o) for o in options)
    # Entries may use typed-in methods the list does not have yet; `make method-report` tracks those.
    # Requiring every entry method to be listed here would fail CI on the first write-in entry.


def test_method_combines_dropdown_choices_and_other_methods(tmp_path):
    body = ISSUE_BODY.replace("### Method\n\nactivation-steering", "### Method\n\nactivation-steering, linear-probing")
    body = body.replace("### Other methods\n\nProbing", "### Other methods\n\nCustom Probe, linear-probing")
    outcome = issue_to_entry.convert(body, "octocat", tmp_path, quote_mode="cached")
    assert outcome["ok"], outcome
    data, _ = wikilib.parse_entry_text(outcome["text"])
    assert data["method"] == ["activation-steering", "linear-probing", "custom-probe"]


def test_no_method_at_all_is_refused(tmp_path):
    body = ISSUE_BODY.replace("### Method\n\nactivation-steering", "### Method\n\n_No response_")
    body = body.replace("### Other methods\n\nProbing", "### Other methods\n\n_No response_")
    outcome = issue_to_entry.convert(body, "octocat", tmp_path, quote_mode="cached")
    assert not outcome["ok"]


def test_evidence_question_covers_null_results_and_anchors_each_level():
    template = yaml.safe_load((REPO_ROOT / ".github" / "ISSUE_TEMPLATE" / "new-entry.yml").read_text(encoding="utf-8"))
    field = next(i["attributes"] for i in template["body"] if i.get("id") == "evidence_strength")
    assert field["label"] == "Strength of evidence"
    text = field["description"].lower()
    assert "null" in text
    for level in ("low:", "medium:", "high:"):
        assert level in text


def test_form_is_framed_as_negative_results_and_defines_them():
    template = yaml.safe_load((REPO_ROOT / ".github" / "ISSUE_TEMPLATE" / "new-entry.yml").read_text(encoding="utf-8"))
    assert template["name"] == "New entry (negative result)"
    assert "negative result" in template["description"].lower()
    intro = template["body"][0]["attributes"]["value"].lower()
    for kind in ("null", "neutral", "smaller than expected", "opposite"):
        assert kind in intro, kind
    failure_type = next(i["attributes"] for i in template["body"] if i.get("id") == "failure_type")
    assert failure_type["label"] == "Likely reason"
    assert "failed" not in yaml.safe_dump(template).lower()


def test_research_areas_are_alphabetical_with_other_last():
    template = yaml.safe_load((REPO_ROOT / ".github" / "ISSUE_TEMPLATE" / "new-entry.yml").read_text(encoding="utf-8"))
    options = next(i["attributes"]["options"] for i in template["body"] if i.get("id") == "research_area")
    assert options[-1] == "other"
    assert options[:-1] == sorted(options[:-1])


def test_no_dropdown_option_uses_a_word_github_reserves():
    # GitHub rejects the whole form, silently, if a dropdown option is "None".
    template = yaml.safe_load((REPO_ROOT / ".github" / "ISSUE_TEMPLATE" / "new-entry.yml").read_text(encoding="utf-8"))
    for item in template["body"]:
        if item["type"] == "dropdown":
            assert all(str(o).strip().lower() != "none" for o in item["attributes"]["options"]), item["id"]


def test_no_hazard_option_becomes_info_hazard_none(tmp_path):
    body = ISSUE_BODY.replace("### Info hazard\n\nnone", "### Info hazard\n\nno hazard")
    assert body != ISSUE_BODY
    outcome = issue_to_entry.convert(body, "octocat", tmp_path, quote_mode="cached")
    assert outcome["ok"], outcome
    data, _ = wikilib.parse_entry_text(outcome["text"])
    assert data["info_hazard"] == "none"


def test_issue_becomes_a_valid_human_entry(tmp_path):
    outcome = issue_to_entry.convert(ISSUE_BODY, "octocat", tmp_path, quote_mode="cached")
    assert outcome["ok"], outcome
    data, body = wikilib.parse_entry_text(outcome["text"])
    assert data["id"] == outcome["id"]
    assert data["contributor"] == {"type": "human", "handle": "octocat"}
    assert data["review"] == {"status": "unreviewed"}
    assert data["research_area"] == ["steering", "interpretability"]
    assert data["method"] == ["activation-steering", "probing"]
    assert data["models"][1] == {"name": "GPT-2 medium", "developer": "OpenAI", "version": "unknown", "size": "355M", "access": "open-weight"}
    assert data["result"] == {"direction": "null", "n": 200}
    assert data["retry_welcome"] is True
    assert data["evidence_strength"] == "low" and "confidence_true_negative" not in data
    assert data["source"]["authors"] == ["Test Author", "Second Author"]
    assert data["source"]["type"] == "lesswrong"
    assert "benchmarks" not in data and "revival_conditions" not in data
    assert body.startswith("We stopped after one layer.") and "still part of the notes" in body
    assert wikilib.badges(data) == ["unreviewed", "retry-welcome"]
    assert wikilib.validate_data(data, quote_mode="cached") == []


def test_invalid_forms_are_reported_not_written(tmp_path):
    bad_quote = ISSUE_BODY.replace(FAKE_QUOTE, "a sentence that is not in the post")
    outcome = issue_to_entry.convert(bad_quote, "octocat", tmp_path, quote_mode="cached")
    assert not outcome["ok"] and any("quote_not_found" in problem for problem in outcome["problems"])

    unticked = ISSUE_BODY.replace("- [X] The quote", "- [ ] The quote")
    assert "ticked" in issue_to_entry.convert(unticked, "octocat", tmp_path, quote_mode="cached")["problems"][0]

    bad_models = ISSUE_BODY.replace("GPT-2 small | OpenAI | unknown | 124M | open-weight", "GPT-2 small, OpenAI")
    assert "Models" in issue_to_entry.convert(bad_models, "octocat", tmp_path, quote_mode="cached")["problems"][0]

    bad_number = ISSUE_BODY.replace("\n200\n", "\nabout 200\n")
    assert "Sample size" in issue_to_entry.convert(bad_number, "octocat", tmp_path, quote_mode="cached")["problems"][0]

    assert not issue_to_entry.convert("just a normal issue", "octocat", tmp_path)["ok"]


def test_main_writes_the_file_and_a_report(tmp_path, monkeypatch):
    monkeypatch.setenv("ISSUE_BODY", ISSUE_BODY)
    monkeypatch.setenv("ISSUE_AUTHOR", "octocat")
    monkeypatch.setenv("ISSUE_NUMBER", "12")
    output = tmp_path / "gh_output"
    monkeypatch.setenv("GITHUB_OUTPUT", str(output))
    report = tmp_path / "report.md"
    assert issue_to_entry.main(["--repo", str(tmp_path), "--report", str(report), "--quotes", "cached"]) == 0
    written = list((tmp_path / "entries").glob("fe-*.md"))
    assert len(written) == 1
    assert wikilib.load_entry(written[0]).data["contributor"]["handle"] == "octocat"
    assert f"entry_id={written[0].stem}" in output.read_text(encoding="utf-8")
    assert "issue #12" in report.read_text(encoding="utf-8") and "found in the source post" in report.read_text(encoding="utf-8")


def test_main_fails_cleanly_on_a_bad_form(tmp_path, monkeypatch):
    monkeypatch.setenv("ISSUE_BODY", ISSUE_BODY.replace("hypothesis_false", "bad_luck"))
    monkeypatch.setenv("ISSUE_AUTHOR", "octocat")
    report = tmp_path / "report.md"
    assert issue_to_entry.main(["--repo", str(tmp_path), "--report", str(report), "--quotes", "cached"]) == 1
    assert not (tmp_path / "entries").exists()
    assert "closed_list" in report.read_text(encoding="utf-8")

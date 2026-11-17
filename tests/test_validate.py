"""D7: the validator rejects every class of bad entry. One failing fixture per class."""
import copy

import pytest

import lw
import validate
import wikilib


def codes(issues, level="error"):
    return {issue.code for issue in issues if issue.level == level}


def check(data, **kwargs):
    kwargs.setdefault("quote_mode", "cached")
    return wikilib.validate_data(data, file_name=f"{data.get('id', 'x')}.md", **kwargs)


def test_valid_entry_passes_with_quote_found(valid_entry):
    assert check(valid_entry) == []


# ---- schema ---------------------------------------------------------------

@pytest.mark.parametrize("field", ["hypothesis", "claim_scope", "method", "models", "failure_type", "contributor", "review", "dates"])
def test_missing_required_field_is_rejected(valid_entry, field):
    del valid_entry[field]
    assert "schema" in codes(check(valid_entry))


def test_unknown_field_is_rejected(valid_entry):
    valid_entry["vibes"] = "good"
    assert "schema" in codes(check(valid_entry))


def test_bad_id_format_is_rejected(valid_entry):
    valid_entry["id"] = "entry-1"
    assert "schema" in codes(check(valid_entry))


def test_agent_contributor_needs_model_and_tool(valid_entry):
    del valid_entry["contributor"]["agent_model"]
    assert "schema" in codes(check(valid_entry))


def test_method_tags_must_be_lowercase_hyphen(valid_entry):
    valid_entry["method"] = ["Activation Steering"]
    assert "schema" in codes(check(valid_entry))


# ---- closed lists ---------------------------------------------------------

@pytest.mark.parametrize(
    "path,value",
    [
        (("failure_type",), "bad_luck"),
        (("result", "direction"), "negative"),
        (("evidence_strength",), "certain"),
        (("evidence_level",), "rumour"),
        (("review", "status"), "approved"),
        (("contributor", "type"), "bot"),
        (("source", "type"), "arxiv"),
        (("info_hazard",), "maybe"),
        (("research_area",), ["astrology"]),
    ],
)
def test_value_outside_closed_list_is_rejected(valid_entry, path, value):
    target = valid_entry
    for key in path[:-1]:
        target = target[key]
    target[path[-1]] = value
    assert "closed_list" in codes(check(valid_entry))


# ---- source URL -----------------------------------------------------------

def test_missing_source_url_is_rejected(valid_entry):
    del valid_entry["source"]["url"]
    assert "source_url" in codes(check(valid_entry))


def test_missing_source_block_is_rejected(valid_entry):
    del valid_entry["source"]
    assert "source_url" in codes(check(valid_entry))


def test_source_url_must_be_a_lesswrong_or_af_post(valid_entry):
    valid_entry["source"]["url"] = "https://example.com/blog/failed"
    assert codes(check(valid_entry))  # rejected by the URL pattern


# ---- quote ----------------------------------------------------------------

def test_quote_not_in_source_is_rejected(valid_entry):
    valid_entry["source"]["quote"] = "the steering vector doubled refusal rates"
    assert "quote_not_found" in codes(check(valid_entry))


def test_quote_over_15_words_is_rejected(valid_entry):
    valid_entry["source"]["quote"] = " ".join(["word"] * 16)
    assert "quote_length" in codes(check(valid_entry))


def test_unreachable_source_is_a_warning_by_default_and_an_error_when_strict(valid_entry):
    valid_entry["source"]["url"] = "https://www.lesswrong.com/posts/NotCached000000001/x"
    assert codes(check(valid_entry, quote_mode="online")) == set()
    assert "source_unreachable" in codes(check(valid_entry, quote_mode="online"), level="warning")
    assert "source_unreachable" in codes(check(valid_entry, quote_mode="strict"))


def test_skipped_quote_check_says_so(valid_entry):
    assert "quote_unchecked" in codes(check(valid_entry, quote_mode="skip"), level="warning")


# ---- consistency ----------------------------------------------------------

def test_reviewed_status_needs_a_reviewer(valid_entry):
    valid_entry["review"] = {"status": "reviewed"}
    assert "review_without_reviewer" in codes(check(valid_entry))
    valid_entry["review"]["reviewers"] = [{"handle": "someone", "type": "human", "date": "2026-11-15", "notes": "checked"}]
    assert check(valid_entry) == []


def test_updated_before_created_is_rejected(valid_entry):
    valid_entry["dates"]["updated"] = "2026-01-01"
    assert "dates_order" in codes(check(valid_entry))


def test_inverted_confidence_interval_is_rejected(valid_entry):
    valid_entry["result"].update({"ci_low": 0.5, "ci_high": 0.1})
    assert "ci_order" in codes(check(valid_entry))


# ---- files ----------------------------------------------------------------

def write(tmp_path, name, data, body=""):
    path = tmp_path / name
    path.write_text(wikilib.dump_entry(data, body), encoding="utf-8")
    return path


def test_duplicate_ids_are_rejected(tmp_path, valid_entry):
    (tmp_path / "a").mkdir()
    (tmp_path / "b").mkdir()
    first = write(tmp_path / "a", "fe-2026-0001.md", valid_entry)
    second = write(tmp_path / "b", "fe-2026-0001.md", valid_entry)
    assert "duplicate_id" in codes(wikilib.validate_paths([first, second], quote_mode="cached"))


def test_id_must_match_file_name(tmp_path, valid_entry):
    path = write(tmp_path, "fe-2026-0099.md", valid_entry)
    assert "id_filename" in codes(wikilib.validate_paths([path], quote_mode="cached"))


def test_file_without_front_matter_is_rejected(tmp_path):
    path = tmp_path / "fe-2026-0001.md"
    path.write_text("just some text\n", encoding="utf-8")
    assert "unreadable" in codes(wikilib.validate_paths([path], quote_mode="cached"))


def test_bare_yaml_null_direction_is_read_as_the_null_result(tmp_path, valid_entry):
    text = wikilib.dump_entry(valid_entry).replace("direction: 'null'", "direction: null")
    assert "direction: null" in text
    path = tmp_path / "fe-2026-0001.md"
    path.write_text(text, encoding="utf-8")
    assert wikilib.load_entry(path).data["result"]["direction"] == "null"
    assert not wikilib.has_errors(wikilib.validate_paths([path], quote_mode="cached"))


def test_gold_files_need_a_gold_status(tmp_path, valid_entry):
    gold = copy.deepcopy(valid_entry)
    gold["gold_status"] = "pending_maintainer_verification"
    path = write(tmp_path, "fe-2026-0001.md", gold)
    assert not wikilib.has_errors(wikilib.validate_paths([path], quote_mode="cached", allow_gold_status=True))
    assert "schema" in codes(wikilib.validate_paths([path], quote_mode="cached"))  # not allowed in entries/
    plain = write(tmp_path, "fe-2026-0001.md", valid_entry)
    assert "gold_status" in codes(wikilib.validate_paths([plain], quote_mode="cached", allow_gold_status=True))


# ---- CLI ------------------------------------------------------------------

def test_cli_exit_codes(tmp_path, valid_entry, capsys):
    good = write(tmp_path, "fe-2026-0001.md", valid_entry)
    assert validate.main([str(good), "--quotes", "cached"]) == 0
    bad_entry = copy.deepcopy(valid_entry)
    bad_entry["id"] = "fe-2026-0002"
    bad_entry["failure_type"] = "bad_luck"
    bad = write(tmp_path, "fe-2026-0002.md", bad_entry)
    assert validate.main([str(bad), "--quotes", "cached"]) == 1
    out = capsys.readouterr().out
    assert "closed_list" in out and "1 error(s)" in out

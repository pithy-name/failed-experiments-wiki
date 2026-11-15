"""D8: the eval scorer runs with one command, writes a results file, and is honest about what it has not scored."""
import copy
import importlib.util
import json
from pathlib import Path

import pytest

import sync_gold
import wikilib

REPO_ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("run_evals", REPO_ROOT / "evals" / "run_evals.py")
run_evals = importlib.util.module_from_spec(spec)
spec.loader.exec_module(run_evals)

ANSWER = """## Already tried
- **fe-2026-0001** — activation steering on GPT-2 small did not change refusal rates.
  Models: GPT-2 small · Evidence: author_report, confidence it is a true negative: low · Badges: agent-written, unreviewed

## Where it went wrong
- **fe-2026-0001** — failure type `hypothesis_false`: one layer, no effect.

## What to avoid
- Do not conclude from a single layer (from fe-2026-0001).

## Worth retrying
- **fe-2026-0001** — retry welcome: sweep layers and coefficients.

## Not found
- Nothing on steering for larger models. The wiki holds 1 entry.
"""

NO_MATCH_ANSWER = """## Already tried
Nothing in the wiki matches this plan.

## Where it went wrong
Nothing to report.

## What to avoid
Nothing to report.

## Worth retrying
None of the entries above.

## Not found
- The wiki has no entries on protein folding. It holds 1 entry.
"""


@pytest.fixture
def workspace(tmp_path, valid_entry):
    gold_dir, results, entries = tmp_path / "gold", tmp_path / "results", tmp_path / "entries"
    for directory in (gold_dir, results / "contribute" / "fe-2026-0001", results / "ask", entries):
        directory.mkdir(parents=True)
    gold = copy.deepcopy(valid_entry)
    gold["gold_status"] = "pending_maintainer_verification"
    (gold_dir / "fe-2026-0001.md").write_text(wikilib.dump_entry(gold), encoding="utf-8")
    (entries / "fe-2026-0001.md").write_text(wikilib.dump_entry(valid_entry), encoding="utf-8")

    draft = copy.deepcopy(valid_entry)
    for owned in ("id", "contributor", "review", "dates"):
        draft.pop(owned)
    draft["failure_type"] = "underpowered"             # one enum wrong
    draft["method"] = ["activation-steering", "probing"]  # one list wrong
    draft["claim_scope"] = "GPT-2 small, one vector, one layer."
    (results / "contribute" / "fe-2026-0001" / "draft-1.md").write_text(wikilib.dump_entry(draft), encoding="utf-8")

    questions = tmp_path / "questions.json"
    questions.write_text(json.dumps({"questions": [
        {"qid": "q1", "question": "Steering for refusal?", "expected_entry_id": "fe-2026-0001"},
        {"qid": "q2", "question": "Protein folding?", "expected_entry_id": None},
    ]}), encoding="utf-8")
    (results / "ask" / "q1.md").write_text(ANSWER, encoding="utf-8")
    (results / "ask" / "q2.md").write_text(NO_MATCH_ANSWER, encoding="utf-8")
    return {"gold": gold_dir, "results": results, "entries": entries, "questions": questions, "valid": valid_entry, "draft": draft}


def run(workspace):
    code = run_evals.main(["--gold", str(workspace["gold"]), "--results", str(workspace["results"]),
                           "--entries", str(workspace["entries"]), "--questions", str(workspace["questions"])])
    assert code == 0
    return json.loads((workspace["results"] / "results.json").read_text(encoding="utf-8"))


def grade(workspace, field, score):
    gold_text = workspace["valid"].get(field, "")
    draft_text = workspace["draft"].get(field, "")
    return {"gold_id": "fe-2026-0001", "draft": "draft-1.md", "field": field, "score": score, "reason": "test",
            "gold_hash": run_evals.text_hash(gold_text), "skill_hash": run_evals.text_hash(draft_text), "grader_model": "test"}


def test_results_are_provisional_while_gold_is_unverified_and_ungraded_fields_are_left_out(workspace):
    results = run(workspace)
    assert results["provisional"] is True and "fe-2026-0001" in results["provisional_reason"]
    item = results["contribute"]["items"][0]["result"]
    assert item["fields"]["failure_type"]["score"] == 0.0
    assert item["fields"]["result.direction"]["score"] == 1.0
    assert item["fields"]["method"]["score"] == 0.0 and item["fields"]["method"]["jaccard"] == 0.5
    assert item["fields"]["claim_scope"]["status"] == "UNGRADED" and item["fields"]["claim_scope"]["score"] is None
    assert "claim_scope" in item["fields_unscored"]
    assert item["quote_valid"] is True and item["schema_valid"] is True
    report = (workspace["results"] / "RESULTS.md").read_text(encoding="utf-8")
    assert "PROVISIONAL" in report and "gold `hypothesis_false` / skill `underpowered`" in report


def test_rubric_grades_count_only_while_they_match_the_graded_texts(workspace):
    grades = [grade(workspace, "hypothesis", 2), grade(workspace, "claim_scope", 1), grade(workspace, "limitations", 2)]
    (workspace["results"] / "rubric_scores.json").write_text(json.dumps({"grades": grades}), encoding="utf-8")
    fields = run(workspace)["contribute"]["items"][0]["result"]["fields"]
    assert fields["claim_scope"]["score"] == 0.5 and fields["hypothesis"]["score"] == 1.0

    # The maintainer corrects the gold text: the old grade must not be reused.
    gold_path = workspace["gold"] / "fe-2026-0001.md"
    gold = wikilib.load_entry(gold_path).data
    gold["claim_scope"] = "A corrected scope statement written by the maintainer."
    gold_path.write_text(wikilib.dump_entry(gold), encoding="utf-8")
    fields = run(workspace)["contribute"]["items"][0]["result"]["fields"]
    assert fields["claim_scope"]["score"] is None and fields["claim_scope"]["status"].startswith("STALE")
    assert fields["hypothesis"]["score"] == 1.0


def test_overall_accuracy_is_the_mean_of_per_field_accuracies(workspace):
    results = run(workspace)
    per_field = results["contribute"]["per_field"]
    usable = [f["accuracy"] for f in per_field.values() if f["accuracy"] is not None]
    assert results["contribute"]["overall_accuracy"] == pytest.approx(sum(usable) / len(usable), abs=1e-4)
    assert per_field["failure_type"]["accuracy"] == 0.0 and per_field["claim_scope"]["accuracy"] is None


def test_verified_gold_removes_the_provisional_label(workspace):
    gold_path = workspace["gold"] / "fe-2026-0001.md"
    gold_path.write_text(gold_path.read_text(encoding="utf-8").replace("pending_maintainer_verification", "verified"), encoding="utf-8")
    assert run(workspace)["provisional"] is False


def test_ask_scoring_needs_the_judge_and_checks_sections(workspace):
    ask = run(workspace)["ask"]
    assert [item["status"] for item in ask["items"]] == ["INCOMPLETE: needs judge", "INCOMPLETE: needs judge"]
    assert ask["passed"] == 0

    judgements = [
        {"qid": "q1", "invents_failures": False, "reason": "all traced", "answer_hash": run_evals.text_hash(ANSWER)},
        {"qid": "q2", "invents_failures": False, "reason": "says none", "answer_hash": run_evals.text_hash(NO_MATCH_ANSWER)},
    ]
    (workspace["results"] / "ask_judgements.json").write_text(json.dumps({"judgements": judgements}), encoding="utf-8")
    ask = run(workspace)["ask"]
    assert ask["passed"] == 2 and ask["match_questions"] == {"passed": 1, "total": 1}
    assert ask["items"][0]["checks"]["failure_type_matches_gold"] is True


def test_ask_fails_on_wrong_failure_type_invented_ids_or_a_false_hit(workspace):
    results_dir = workspace["results"]
    (results_dir / "ask" / "q1.md").write_text(ANSWER.replace("`hypothesis_false`", "`underpowered`"), encoding="utf-8")
    (results_dir / "ask" / "q2.md").write_text(NO_MATCH_ANSWER.replace("Nothing in the wiki matches this plan.", "- **fe-2026-0777** — folding failed."), encoding="utf-8")
    ask = run(workspace)["ask"]
    assert ask["items"][0]["checks"]["failure_type_matches_gold"] is False
    assert ask["items"][1]["checks"]["already_tried_cites_nothing"] is False
    assert ask["items"][1]["checks"]["cites_only_existing_entries"] is False
    assert ask["passed"] == 0


def test_pending_gold_drafts_are_published_unreviewed_with_their_note_and_without_maintainer_notes(tmp_path, valid_entry):
    gold_dir, entries = tmp_path / "gold", tmp_path / "entries"
    gold_dir.mkdir()
    gold = copy.deepcopy(valid_entry)
    gold["gold_status"] = "pending_maintainer_verification"
    gold["contributor"] = {"type": "agent", "handle": wikilib.PLACEHOLDER_HANDLE, "agent_model": "some-model", "tool": "gold-draft",
                           "note": "Model draft awaiting verification."}
    gold["review"] = {"status": "reviewed", "reviewers": [{"handle": "x", "type": "human", "date": "2026-11-14"}]}  # must not survive
    body = "Public summary.\n\n## Verification notes for the maintainer\n\n- private pointer"
    (gold_dir / "fe-2026-0001.md").write_text(wikilib.dump_entry(gold, body), encoding="utf-8")

    outcomes = sync_gold.publish_drafts(gold_dir, entries, quote_mode="cached")
    assert outcomes[0]["action"] == "published_as_unreviewed_draft"
    entry = wikilib.load_entry(entries / "fe-2026-0001.md")
    assert entry.data["review"] == {"status": "unreviewed"}
    assert entry.data["contributor"]["note"] == "Model draft awaiting verification."
    assert entry.data["contributor"]["type"] == "agent" and "agent-written" in wikilib.badges(entry.data)
    assert "gold_status" not in entry.data
    assert entry.body == "Public summary."
    assert sync_gold.publish_drafts(gold_dir, entries, quote_mode="cached")[0]["reason"] == "entry file already exists"

    without_note = copy.deepcopy(gold)
    without_note["id"] = "fe-2026-0002"
    without_note["contributor"] = {"type": "agent", "handle": "someone", "agent_model": "some-model"}
    (gold_dir / "fe-2026-0002.md").write_text(wikilib.dump_entry(without_note), encoding="utf-8")
    assert sync_gold.publish_drafts(gold_dir, entries, quote_mode="cached")[1]["action"] == "rejected"

    # A draft a model wrote must not be filed under a person, note or no note: three cold reviewers were misled by exactly that.
    filed_as_person = copy.deepcopy(gold)
    filed_as_person["id"] = "fe-2026-0003"
    filed_as_person["contributor"] = {"type": "human", "handle": "someone", "note": "Model draft awaiting verification."}
    (gold_dir / "fe-2026-0003.md").write_text(wikilib.dump_entry(filed_as_person), encoding="utf-8")
    outcome = sync_gold.publish_drafts(gold_dir, entries, quote_mode="cached")[2]
    assert outcome["action"] == "rejected" and "agent" in outcome["issues"][0]


def test_the_real_gold_drafts_and_their_entries_are_labelled_as_model_written_until_verified():
    for gold_path in sorted((REPO_ROOT / "evals" / "gold").glob("fe-*.md")):
        gold = wikilib.load_entry(gold_path).data
        entry = wikilib.load_entry(REPO_ROOT / "entries" / gold_path.name).data
        if gold.get("gold_status") == "verified":
            assert entry["contributor"]["type"] == "human" and entry["review"]["status"] == "reviewed", gold_path.name
        else:
            for data in (gold, entry):
                assert data["contributor"]["type"] == "agent" and data["contributor"].get("agent_model"), gold_path.name
                assert data["contributor"].get("note"), gold_path.name
            assert "agent-written" in wikilib.badges(entry), gold_path.name


def test_sync_gold_publishes_only_verified_entries_as_human_reviewed(workspace):
    entries, gold_dir = workspace["entries"], workspace["gold"]
    pending = copy.deepcopy(workspace["valid"])
    pending["contributor"] = {"type": "agent", "handle": wikilib.PLACEHOLDER_HANDLE, "agent_model": "some-model", "tool": "gold-draft",
                              "note": "Draft awaiting verification."}
    (entries / "fe-2026-0001.md").write_text(wikilib.dump_entry(pending), encoding="utf-8")

    outcomes = sync_gold.sync("maintainer-handle", gold_dir, entries, quote_mode="cached")
    assert outcomes[0]["action"] == "skipped"
    assert wikilib.load_entry(entries / "fe-2026-0001.md").data["review"]["status"] == "unreviewed"

    gold_path = gold_dir / "fe-2026-0001.md"
    text = gold_path.read_text(encoding="utf-8").replace("pending_maintainer_verification", "verified")
    gold_path.write_text(text.replace("failure_type: hypothesis_false", "failure_type: underpowered"), encoding="utf-8")
    outcomes = sync_gold.sync("maintainer-handle", gold_dir, entries, quote_mode="cached")
    assert outcomes[0]["action"] == "published"
    data = wikilib.load_entry(entries / "fe-2026-0001.md").data
    assert data["failure_type"] == "underpowered"            # the maintainer's correction reached the wiki
    assert data["contributor"] == {"type": "human", "handle": "maintainer-handle"}
    assert data["review"]["status"] == "reviewed" and data["review"]["reviewers"][0]["type"] == "human"
    assert "gold_status" not in data
    assert wikilib.validate_data(data, quote_mode="cached") == []
    assert sync_gold.sync("maintainer-handle", gold_dir, entries, quote_mode="cached")[0]["action"] == "unchanged"

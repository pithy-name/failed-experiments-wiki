"""Write path: submit and review go to branches, never straight to main."""
import copy

import wikilib
from conftest import run_git


def new_entry(valid_entry):
    data = copy.deepcopy(valid_entry)
    for owned in ("id", "contributor", "review", "dates"):
        data.pop(owned)
    data["title"] = "A second steering attempt on GPT-2 small also showed no effect"
    return data


def test_submit_writes_a_branch_and_leaves_main_and_the_working_tree_alone(git_repo, valid_entry):
    head_before = run_git(git_repo, "rev-parse", "main")
    result = wikilib.submit_entry(new_entry(valid_entry), "Body.", repo=git_repo, agent_model="test-model",
                                  tool="contribute-skill v0.1", quote_mode="cached")
    assert result["ok"] and result["id"] == "fe-2026-0002"
    assert result["branch"] == "entry/fe-2026-0002"
    assert result["status"] == "branch_only_no_remote" and result["pull_request"] is None
    assert result["badges"] == ["agent-written", "unreviewed", "retry-welcome"]
    assert run_git(git_repo, "rev-parse", "main") == head_before
    assert run_git(git_repo, "status", "--porcelain") == ""
    assert not (git_repo / "entries" / "fe-2026-0002.md").exists()

    text = wikilib.read_file_at(git_repo, "entry/fe-2026-0002", "entries/fe-2026-0002.md")
    data, body = wikilib.parse_entry_text(text)
    assert body == "Body."
    assert data["contributor"] == {"type": "agent", "handle": "test-handle", "agent_model": "test-model", "tool": "contribute-skill v0.1"}
    assert data["review"] == {"status": "unreviewed"}
    message = run_git(git_repo, "log", "-1", "--format=%B", "entry/fe-2026-0002")
    assert "Add entry fe-2026-0002" in message and "Source: https://www.lesswrong.com/posts/" in message
    assert "quote found in source" in message


def test_submitter_cannot_set_its_own_trust_fields(git_repo, valid_entry):
    data = new_entry(valid_entry)
    data["id"] = "fe-1999-0001"
    data["contributor"] = {"type": "human", "handle": "impostor"}
    data["review"] = {"status": "reviewed", "reviewers": [{"handle": "impostor", "type": "human", "date": "2026-01-01"}]}
    result = wikilib.submit_entry(data, repo=git_repo, agent_model="m", tool="t", quote_mode="cached")
    stored, _ = wikilib.parse_entry_text(wikilib.read_file_at(git_repo, result["branch"], result["file"]))
    assert stored["id"] == "fe-2026-0002"
    assert stored["contributor"]["type"] == "agent" and stored["contributor"]["handle"] == "test-handle"
    assert stored["review"] == {"status": "unreviewed"}
    # the result says whose name went on the entry, so the agent can tell the user without opening the file
    assert result["recorded_as"] == {"type": "agent", "handle": "test-handle", "agent_model": "m", "tool": "t"}


def test_invalid_submission_is_rejected_and_writes_nothing(git_repo, valid_entry):
    data = new_entry(valid_entry)
    data["source"]["quote"] = "a sentence that is not in the post"
    result = wikilib.submit_entry(data, repo=git_repo, agent_model="m", tool="t", quote_mode="cached")
    assert not result["ok"] and result["status"] == "rejected_by_validation"
    assert any(issue["code"] == "quote_not_found" for issue in result["issues"])
    assert run_git(git_repo, "branch", "--list", "entry/*") == ""


def test_ids_reserved_by_pending_branches_are_not_reused(git_repo, valid_entry):
    first = wikilib.submit_entry(new_entry(valid_entry), repo=git_repo, agent_model="m", tool="t", quote_mode="cached")
    second = wikilib.submit_entry(new_entry(valid_entry), repo=git_repo, agent_model="m", tool="t", quote_mode="cached")
    assert (first["id"], second["id"]) == ("fe-2026-0002", "fe-2026-0003")


def test_merge_local_publishes_the_entry_with_a_merge_commit(git_repo, valid_entry):
    result = wikilib.submit_entry(new_entry(valid_entry), repo=git_repo, agent_model="m", tool="t", quote_mode="cached")
    merged = wikilib.merge_local(result["branch"], repo=git_repo)
    assert merged["ok"] and merged["status"] == "merged_locally"
    assert (git_repo / "entries" / "fe-2026-0002.md").exists()
    assert len(run_git(git_repo, "log", "-1", "--format=%P", "main").split()) == 2  # a real merge commit
    assert "stand-in for merging a pull request" in run_git(git_repo, "log", "-1", "--format=%B", "main")


def test_review_changes_status_records_reviewer_and_shows_in_history(git_repo):
    result = wikilib.review_entry("fe-2026-0001", "reviewed", "Checked every field against the post.", repo=git_repo,
                                  reviewer_type="human", handle="reviewer-handle", quote_mode="cached")
    assert result["ok"] and (result["previous_status"], result["new_status"]) == ("unreviewed", "reviewed")
    assert "unreviewed" not in result["badges"]
    data, body = wikilib.parse_entry_text(wikilib.read_file_at(git_repo, result["branch"], "entries/fe-2026-0001.md"))
    assert body == "Body text."
    assert data["review"]["status"] == "reviewed"
    reviewer = data["review"]["reviewers"][0]
    assert reviewer["handle"] == "reviewer-handle" and reviewer["type"] == "human" and reviewer["notes"]
    assert reviewer["date"] == data["dates"]["updated"]
    message = run_git(git_repo, "log", "-1", "--format=%B", result["branch"])
    assert "Review fe-2026-0001: unreviewed -> reviewed" in message and "reviewer-handle" in message
    # main is unchanged until the review branch is merged
    main_data, _ = wikilib.parse_entry_text(wikilib.read_file_at(git_repo, "main", "entries/fe-2026-0001.md"))
    assert main_data["review"]["status"] == "unreviewed"
    assert wikilib.merge_local(result["branch"], repo=git_repo)["ok"]
    assert wikilib.load_entry(git_repo / "entries" / "fe-2026-0001.md").data["review"]["status"] == "reviewed"


def test_agent_review_records_the_model(git_repo):
    result = wikilib.review_entry("fe-2026-0001", "contested", "Quote is fine but claim_scope overreaches.", repo=git_repo,
                                  reviewer_type="agent", agent_model="test-model", quote_mode="cached")
    data, _ = wikilib.parse_entry_text(wikilib.read_file_at(git_repo, result["branch"], "entries/fe-2026-0001.md"))
    assert data["review"]["reviewers"][0]["agent_model"] == "test-model"
    assert wikilib.badges(data) == ["agent-written", "contested", "retry-welcome"]
    assert result["recorded_as"]["type"] == "agent" and result["recorded_as"]["handle"] == "test-handle"
    assert result["recorded_as"]["agent_model"] == "test-model"


def test_review_of_missing_entry_or_bad_status_is_refused(git_repo):
    assert wikilib.review_entry("fe-2026-0099", "reviewed", "x", repo=git_repo)["status"] == "not_found"
    assert wikilib.review_entry("fe-2026-0001", "approved", "x", repo=git_repo)["status"] == "invalid_status"

"""The demo script stays true to the repository, and stays within its time budget."""
import importlib.util
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("build_demo", REPO_ROOT / "demo" / "build_demo.py")
build_demo = importlib.util.module_from_spec(spec)
spec.loader.exec_module(build_demo)


def test_numbers_the_narration_states_match_the_repository():
    assert build_demo.stale_facts(build_demo.load_scenes()) == []


def test_every_scene_is_well_formed_and_points_at_real_things():
    scenes = build_demo.load_scenes()["scenes"]
    ids = [scene["id"] for scene in scenes]
    assert len(ids) == len(set(ids))
    for scene in scenes:
        assert scene["kind"] in {"card", "page", "terminal", "file", "datasette"}, scene["id"]
        assert len(scene["narration"].split()) >= 10, scene["id"]
        if scene["kind"] == "file":
            path = REPO_ROOT / scene["path"]
            assert path.exists(), scene["path"]
            line_count = len(path.read_text(encoding="utf-8").split("\n"))
            for first, last in build_demo.file_ranges(scene):
                assert 1 <= first <= last <= line_count, (scene["id"], first, last, line_count)
        if scene["kind"] == "page":
            assert scene["beats"] and all(beat["say"].strip() for beat in scene["beats"]), scene["id"]
        if scene["kind"] == "terminal":
            assert scene["commands"], scene["id"]
            assert all(1 <= position <= len(scene["commands"]) for position in scene.get("expect_fail", [])), scene["id"]
        if scene["kind"] == "datasette":
            assert scene["beats"][0].get("path", "").startswith("/"), scene["id"]
        assert scene["narration"] == " ".join(beat["say"] for beat in scene["beats"]), scene["id"]


def test_page_actions_only_use_controls_values_and_entries_that_exist():
    """An action that names a missing facet value or entry would stall the recorder half-way through."""
    entries = build_demo.wikilib.load_entries(REPO_ROOT / "entries")
    by_id = {entry.id: entry for entry in entries}
    catalogue = {field["path"]: field for field in build_demo.build_site.field_catalogue()}
    known = {"tick", "untick", "type", "clear", "open", "show_field", "scroll", "scroll_to", "scroll_top", "scroll_panel", "panel_top"}
    for scene in build_demo.load_scenes()["scenes"]:
        for beat in scene["beats"]:
            for action in beat["actions"]:
                where = (scene["id"], action)
                assert action["do"] in known, where
                if action["do"] in {"tick", "untick"}:
                    assert catalogue[action["field"]]["control"] == "facet", where
                    if action["field"] == "badges":
                        values = {badge for entry in entries for badge in build_demo.wikilib.badges(entry.data)}
                    else:
                        values = {build_demo.wikilib._facet_key(v) for entry in entries
                                  for v in build_demo.wikilib.get_values(entry.data, action["field"])}
                    assert action["value"] in values, where
                if action["do"] in {"open", "show_field", "scroll_to"}:
                    assert action["entry"] in by_id, where
                if action["do"] == "show_field":
                    # scenes.yaml matches the recorded video, so it may name a field by its old name
                    field = build_demo.wikilib.RENAMED_FIELDS.get(action["field"], action["field"])
                    data = by_id[action["entry"]].data
                    assert field in data or any(
                        isinstance(value, dict) and field in value for value in data.values()
                    ), where


def test_demo_runs_five_to_seven_minutes_at_speaking_pace():
    demo = build_demo.load_scenes()
    seconds = sum(build_demo.estimate_seconds(scene, demo["words_per_minute"]) for scene in demo["scenes"])
    assert 5 * 60 <= seconds <= 7 * 60, seconds


def test_the_short_cut_fits_a_five_minute_limit_and_still_tells_the_story():
    """The sprint asks for a video of three to five minutes; the maintainer asked for five to seven. Both are built."""
    demo = build_demo.load_scenes()
    kept = [scene for scene in demo["scenes"] if scene.get("short", True)]
    seconds = sum(build_demo.estimate_seconds(scene, demo["words_per_minute"]) for scene in kept)
    assert 3 * 60 <= seconds <= 5 * 60, seconds
    ids = {scene["id"] for scene in kept}
    # the problem, the page, the question it is for, both write paths' guard, the finding and the close all stay
    assert {"s01-title", "s03-browse", "s05-entry", "s08-answer", "s10-contribute", "s11-validate", "s16-finding", "s17-close"} <= ids


def test_a_terminal_scene_shows_the_command_before_its_output(tmp_path):
    scene = {"id": "x", "kind": "terminal", "commands": ["echo first-output", "echo second-output"]}
    pages, record = build_demo.terminal_html(scene, tmp_path)
    assert len(pages) == 3 and [item["exit_code"] for item in record] == [0, 0]
    assert "echo first-output" in pages[0] and ">first-output" not in pages[0].replace("echo first-output", "")
    assert "first-output" in pages[1].replace("echo first-output", "") and "second-output" not in pages[1]
    assert "second-output" in pages[2].replace("echo second-output", "")


def test_paths_with_the_users_name_are_kept_off_screen(tmp_path):
    home = str(Path.home())
    shown = build_demo.scrub(f"{REPO_ROOT}/entries/x.md and {tmp_path}/y and {home}/elsewhere", tmp_path)
    assert shown == "./entries/x.md and $TMP/y and ~/elsewhere"
    assert home not in shown


def test_a_clone_with_no_remote_can_be_told_which_remote_the_narration_describes(monkeypatch):
    """The verification run works in a clone with its remote removed; the narration is still about the real repository."""
    monkeypatch.setattr(build_demo.wikilib, "remote_url", lambda repo: None)
    monkeypatch.delenv("FEWIKI_DEMO_REMOTE_URL", raising=False)
    assert build_demo.repo_facts()["has_github_remote"] is False
    monkeypatch.setenv("FEWIKI_DEMO_REMOTE_URL", "git@github.com:someone/some-wiki.git")
    assert build_demo.repo_facts()["has_github_remote"] is True

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
        assert scene["kind"] in {"card", "page", "terminal", "file"}, scene["id"]
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
        assert scene["narration"] == " ".join(beat["say"] for beat in scene["beats"]), scene["id"]


def test_page_actions_only_use_controls_values_and_entries_that_exist():
    """An action that names a missing facet value or entry would stall the recorder half-way through."""
    entries = build_demo.wikilib.load_entries(REPO_ROOT / "entries")
    by_id = {entry.id: entry for entry in entries}
    catalogue = {field["path"]: field for field in build_demo.build_site.field_catalogue()}
    known = {"tick", "untick", "type", "clear", "open", "show_field", "scroll", "scroll_to", "scroll_top"}
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
                    data = by_id[action["entry"]].data
                    assert action["field"] in data or any(
                        isinstance(value, dict) and action["field"] in value for value in data.values()
                    ), where


def test_demo_runs_five_to_seven_minutes_at_speaking_pace():
    demo = build_demo.load_scenes()
    seconds = sum(build_demo.estimate_seconds(scene, demo["words_per_minute"]) for scene in demo["scenes"])
    assert 5 * 60 <= seconds <= 7 * 60, seconds


def test_paths_with_the_users_name_are_kept_off_screen(tmp_path):
    home = str(Path.home())
    shown = build_demo.scrub(f"{REPO_ROOT}/entries/x.md and {tmp_path}/y and {home}/elsewhere", tmp_path)
    assert shown == "./entries/x.md and $TMP/y and ~/elsewhere"
    assert home not in shown

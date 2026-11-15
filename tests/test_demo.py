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
            assert scene["states"], scene["id"]
        if scene["kind"] == "terminal":
            assert scene["commands"], scene["id"]


def test_page_links_only_use_fields_and_entries_that_exist():
    catalogue = {field["path"] for field in build_demo.build_site.field_catalogue()}
    entry_ids = {path.stem for path in (REPO_ROOT / "entries").glob("fe-*.md")}
    for scene in build_demo.load_scenes()["scenes"]:
        for state in scene.get("states", []):
            for pair in filter(None, state["link"].split("&")):
                key, _, value = pair.partition("=")
                if key.startswith("f."):
                    assert key[2:] in catalogue, (scene["id"], key)
                elif key.startswith(("min.", "max.")):
                    assert key[4:] in catalogue, (scene["id"], key)
                elif key == "open":
                    assert value in entry_ids, (scene["id"], value)
                else:
                    assert key == "q", (scene["id"], key)


def test_demo_runs_five_to_seven_minutes_at_speaking_pace():
    demo = build_demo.load_scenes()
    seconds = sum(build_demo.estimate_seconds(scene, demo["words_per_minute"]) for scene in demo["scenes"])
    assert 5 * 60 <= seconds <= 7 * 60, seconds


def test_paths_with_the_users_name_are_kept_off_screen(tmp_path):
    home = str(Path.home())
    shown = build_demo.scrub(f"{REPO_ROOT}/entries/x.md and {tmp_path}/y and {home}/elsewhere", tmp_path)
    assert shown == "./entries/x.md and $TMP/y and ~/elsewhere"
    assert home not in shown

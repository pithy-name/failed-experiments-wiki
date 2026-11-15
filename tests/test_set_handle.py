import copy

import set_handle
import wikilib


def test_set_handle_replaces_only_the_placeholder_and_keeps_entries_valid(tmp_path, valid_entry, monkeypatch):
    entries, gold = tmp_path / "entries", tmp_path / "evals" / "gold"
    entries.mkdir()
    gold.mkdir(parents=True)
    entry = copy.deepcopy(valid_entry)
    entry["contributor"]["handle"] = wikilib.PLACEHOLDER_HANDLE
    path = entries / "fe-2026-0001.md"
    path.write_text(wikilib.dump_entry(entry, "Body."), encoding="utf-8")
    other = copy.deepcopy(valid_entry)
    other["id"] = "fe-2026-0002"
    (entries / "fe-2026-0002.md").write_text(wikilib.dump_entry(other), encoding="utf-8")
    monkeypatch.setattr(wikilib, "ENTRIES_DIR", entries)
    monkeypatch.setattr(wikilib, "REPO_ROOT", tmp_path)
    inode_before = path.stat().st_ino

    assert set_handle.main(["octo-cat"]) == 0
    assert wikilib.load_entry(path).data["contributor"]["handle"] == "octo-cat"
    assert wikilib.load_entry(path).body == "Body."
    assert path.stat().st_ino == inode_before                      # rewritten in place, not replaced
    assert wikilib.load_entry(entries / "fe-2026-0002.md").data["contributor"]["handle"] == "test-handle"

    assert set_handle.main(["not a handle"]) == 2
    assert set_handle.main([]) == 2

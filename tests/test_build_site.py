"""Web page: one self-contained file that lists all entries and filters on every field."""
import copy
import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest

import build_site
import wikilib

REPO_ROOT = Path(__file__).resolve().parent.parent
ASSETS = REPO_ROOT / "tools" / "site_assets"
JS_TESTS = REPO_ROOT / "tests" / "js"
JSC = Path("/System/Library/Frameworks/JavaScriptCore.framework/Versions/Current/Helpers/jsc")
HOSTILE_TITLE = "Probe test </script><script>alert(1)</script> did nothing"


def js_engine():
    if JSC.exists():
        return [str(JSC)]
    node = shutil.which("node")
    return [node] if node else None


def run_js(files: list[Path]) -> str:
    engine = js_engine()
    if engine is None:
        pytest.skip("no JavaScript engine available (jsc or node)")
    if engine[0].endswith("node"):
        # node has no load-several-files mode: concatenate, and give it jsc's print().
        source = "var print = console.log;\n" + "\n".join(path.read_text(encoding="utf-8") for path in files)
        completed = subprocess.run(engine + ["-e", source], capture_output=True, text=True, timeout=120)
    else:
        completed = subprocess.run(engine + [str(path) for path in files], capture_output=True, text=True, timeout=120)
    assert completed.returncode == 0, (completed.stdout + completed.stderr)[-1500:]
    return completed.stdout


@pytest.fixture
def site(tmp_path, valid_entry):
    entries_dir = tmp_path / "entries"
    entries_dir.mkdir()
    first = copy.deepcopy(valid_entry)
    first["title"] = HOSTILE_TITLE
    second = copy.deepcopy(valid_entry)
    second.update(id="fe-2026-0002", title="SAE probes did not beat linear probes", method=["sae"], failure_type="underpowered",
                  retry_welcome=False, research_area=["interpretability"])
    second["contributor"] = {"type": "human", "handle": "someone", "note": "Draft awaiting verification."}
    second["source"] = dict(second["source"], published="2025-06-10")
    third = copy.deepcopy(valid_entry)
    third.update(id="fe-2026-0003", title="Debate pilot showed no judge improvement", method=["debate"], failure_type="underpowered")
    third["review"] = {"status": "reviewed", "reviewers": [{"handle": "rev", "type": "human", "date": "2026-11-15", "notes": "ok"}]}
    third["dates"] = {"created": "2026-11-14", "updated": "2026-11-15"}
    (entries_dir / "fe-2026-0001.md").write_text(wikilib.dump_entry(first, "Body mentions quokka. Second line."), encoding="utf-8")
    (entries_dir / "fe-2026-0002.md").write_text(wikilib.dump_entry(second), encoding="utf-8")
    (entries_dir / "fe-2026-0003.md").write_text(wikilib.dump_entry(third), encoding="utf-8")
    out = tmp_path / "site" / "index.html"
    build_site.build(entries_dir, out, None)
    return {"entries": entries_dir, "out": out, "html": out.read_text(encoding="utf-8"), "tmp": tmp_path}


def payload_of(page: str) -> tuple[dict, str]:
    match = re.search(r'<script type="application/json" id="fewiki-data">(.*?)</script>', page, re.DOTALL)
    assert match, "embedded data not found"
    return json.loads(match.group(1)), match.group(1)


def test_page_is_one_self_contained_file(site):
    page = site["html"]
    assert page.startswith("<!doctype html>")
    for forbidden in ('src="http', "src='http", "@import", '<link rel="stylesheet"', "<link ", "fetch(", "XMLHttpRequest", "<iframe"):
        assert forbidden not in page, forbidden
    assert not re.search(r"<script[^>]*\ssrc=", page)


def test_every_schema_field_has_a_control(site):
    payload, _ = payload_of(site["html"])
    catalogue = {field["path"]: field for field in payload["fields"]}
    for path, kind in wikilib.FIELDS:
        assert path in catalogue, path
        expected = "facet" if kind in wikilib.FACET_KINDS else "range" if kind in wikilib.RANGE_KINDS else "text"
        assert catalogue[path]["control"] == expected, path
        assert catalogue[path]["group"] in {group["id"] for group in payload["groups"]}
    assert catalogue["badges"]["control"] == "facet"
    # the three kinds of control the spec asks for are all present
    assert {field["control"] for field in payload["fields"]} == {"facet", "range", "text"}


def test_entries_badges_notes_and_links_are_embedded(site):
    payload, _ = payload_of(site["html"])
    by_id = {entry["id"]: entry for entry in payload["entries"]}
    assert sorted(by_id) == ["fe-2026-0001", "fe-2026-0002", "fe-2026-0003"]
    assert by_id["fe-2026-0001"]["badges"] == ["agent-written", "unreviewed", "retry-welcome"]
    assert by_id["fe-2026-0002"]["badges"] == ["unreviewed"]
    assert by_id["fe-2026-0003"]["badges"] == ["agent-written", "retry-welcome"]
    assert by_id["fe-2026-0002"]["data"]["contributor"]["note"] == "Draft awaiting verification."
    assert by_id["fe-2026-0001"]["body"].startswith("Body mentions quokka.")
    assert by_id["fe-2026-0001"]["file_url"] == "../entries/fe-2026-0001.md"
    assert "No GitHub remote is configured yet" in site["html"]


def test_entry_links_point_to_github_when_a_remote_is_known(site):
    out = site["tmp"] / "with-remote.html"
    build_site.build(site["entries"], out, "https://github.com/someone/failed-experiments-wiki")
    payload, _ = payload_of(out.read_text(encoding="utf-8"))
    assert payload["entries"][0]["file_url"] == "https://github.com/someone/failed-experiments-wiki/blob/main/entries/fe-2026-0001.md"
    assert "No GitHub remote" not in out.read_text(encoding="utf-8")


def test_github_remote_forms():
    assert build_site.github_web_url("git@github.com:someone/repo.git") == "https://github.com/someone/repo"
    assert build_site.github_web_url("https://github.com/someone/repo.git") == "https://github.com/someone/repo"
    assert build_site.github_web_url("https://github.com/someone/repo") == "https://github.com/someone/repo"
    assert build_site.github_web_url("https://example.com/someone/repo.git") is None
    assert build_site.github_web_url("javascript:alert(1)") is None
    assert build_site.github_web_url(None) is None


def test_hostile_entry_text_cannot_break_out_of_the_data_block(site):
    page = site["html"]
    payload, raw = payload_of(page)
    assert payload["entries"][0]["data"]["title"] == HOSTILE_TITLE     # round-trips intact
    assert "<" not in raw and ">" not in raw and "&" not in raw          # nothing in the block can close the tag or start markup
    assert " " not in raw
    assert "alert(1)</script>" not in page
    assert page.count("<script") == 3                                     # data, filter.js, app.js: no injected fourth


def test_dom_code_never_assigns_html_from_data():
    for name in ("app.js", "filter.js"):
        source = (ASSETS / name).read_text(encoding="utf-8")
        for forbidden in ("innerHTML", "outerHTML", "insertAdjacentHTML", "document.write", "eval("):
            assert forbidden not in source, f"{name} uses {forbidden}"


def test_filter_logic_in_a_real_javascript_engine():
    out = run_js([ASSETS / "filter.js", JS_TESTS / "filter_test.js"])
    assert re.search(r"filter tests passed: \d+", out), out


def test_page_script_runs_and_reacts_in_a_fake_dom(site):
    """Executes the real app.js: render, search, clear, facet tick. Not a browser, but not a syntax check either."""
    _, raw = payload_of(site["html"])
    data_js = site["tmp"] / "data.js"
    data_js.write_text("var __FEWIKI_DATA__ = " + json.dumps(raw) + ";\n", encoding="utf-8")
    out = run_js([data_js, JS_TESTS / "fake_dom.js", ASSETS / "filter.js", ASSETS / "app.js", JS_TESTS / "dom_test.js"])
    assert re.search(r"dom tests passed: \d+", out), out


def test_page_loads_its_filters_from_a_link(site):
    """A filtered view can be shared: filters, search text, ranges and the opened entry come from the URL fragment."""
    _, raw = payload_of(site["html"])
    data_js = site["tmp"] / "data_link.js"
    link = "#f.failure_type=underpowered&q=sae&min.source.published=2025-01-01&open=fe-2026-0002&f.not_a_field=x&junk"
    data_js.write_text(
        "var __FEWIKI_DATA__ = " + json.dumps(raw) + ";\nvar __FEWIKI_HASH__ = " + json.dumps(link) + ";\n", encoding="utf-8"
    )
    out = run_js([data_js, JS_TESTS / "fake_dom.js", ASSETS / "filter.js", ASSETS / "app.js", JS_TESTS / "link_test.js"])
    assert re.search(r"link tests passed: \d+", out), out


def test_cli_builds_the_page(site, capsys):
    out = site["tmp"] / "cli.html"
    assert build_site.main(["--entries", str(site["entries"]), "--out", str(out)]) == 0
    assert "3 entries" in capsys.readouterr().out and out.exists()
    assert build_site.main(["--entries", str(site["entries"]), "--out", str(out), "--repo-url", "https://example.com/x/y"]) == 2


def test_the_page_does_not_depend_on_the_day_it_is_built(tmp_path, monkeypatch):
    """The first run on GitHub failed because the page carried the build date, and the runner's clock is in UTC."""
    entries = wikilib.load_entries(REPO_ROOT / "entries")
    payload = build_site.build_payload(entries, None)
    assert payload["built"] == max(str((entry.data.get("dates") or {}).get("updated", "")) for entry in entries)

    class Tomorrow(build_site.dt.date):
        @classmethod
        def today(cls):
            return cls(2099, 1, 1)

    monkeypatch.setattr(build_site.dt, "date", Tomorrow)
    assert build_site.render(build_site.build_payload(entries, None)) == build_site.render(payload)


def test_the_tracked_page_is_what_the_builder_makes_now(tmp_path):
    """site/index.html is committed so it opens straight from a checkout; it must not lag behind the entries or the script."""
    fresh = tmp_path / "index.html"
    build_site.build(REPO_ROOT / "entries", fresh, build_site.github_web_url(wikilib.remote_url(REPO_ROOT)))
    tracked = REPO_ROOT / "site" / "index.html"
    assert tracked.read_text(encoding="utf-8") == fresh.read_text(encoding="utf-8"), "run `make site` and commit site/index.html"

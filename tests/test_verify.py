"""The verification run's check list stays well formed, and its fixtures are honest.

The run itself (demo/verify.py) is slow and needs a browser, so it is not part of
the suite. These tests keep its inputs sound: every check is complete, every
coverage row points at checks that exist, and the issue-form fixture really is
built from the form's own labels and survives the converter unchanged.
"""
import copy
import importlib.util
import sys
from pathlib import Path

import yaml

import issue_to_entry
import wikilib

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "demo"))
spec = importlib.util.spec_from_file_location("verify", REPO_ROOT / "demo" / "verify.py")
verify = importlib.util.module_from_spec(spec)
spec.loader.exec_module(verify)

SPEC = yaml.safe_load((REPO_ROOT / "demo" / "verify.yaml").read_text(encoding="utf-8"))


def test_every_check_is_complete_and_can_fail():
    ids = [check["id"] for check in SPEC["checks"]]
    assert len(ids) == len(set(ids))
    for check in SPEC["checks"]:
        # D1-D8 are requirement labels; "demo" and "all" mark checks that serve no single requirement
        assert check["requirement"] in {f"D{n}" for n in range(1, 9)} | {"demo", "all"}, check["id"]
        assert check["title"].strip() and len(check["proves"].split()) >= 6, check["id"]
        assert check.get("cwd", "clone") in {"clone", "repo"}, check["id"]
        assert check["commands"], check["id"]
        # a check with no expectation at all would pass whatever happened
        assert any(
            command.get("expect") or command.get("expect_no_output") or command.get("expect_exit") for command in check["commands"]
        ), check["id"]


def test_commands_that_write_never_run_in_the_real_repository():
    # build_demo is here because its --script-only run rewrote demo/script.md in the real repository once (DEC-77)
    writers = ("submit", "review ", "merge-local", "issue_to_entry", "sync_gold", "set_handle", "run_evals", "build_db", "build_site",
               "build_demo")
    for check in SPEC["checks"]:
        if check.get("cwd") != "repo":
            continue
        for command in check["commands"]:
            assert not any(word in command["run"] for word in writers), (check["id"], command["run"])


def test_coverage_rows_point_at_real_checks_and_every_check_is_covered():
    known = {check["id"] for check in SPEC["checks"]} | set(verify.CODED_CHECKS)
    covered = set()
    for row in SPEC["coverage"]:
        assert row["status"] in {"recorded", "tests only", "not checkable"}, row["function"]
        assert row["evidence"].strip(), row["function"]
        if row["status"] == "recorded":
            assert row.get("checks"), row["function"]
        for check_id in row.get("checks", []):
            assert check_id in known, (row["function"], check_id)
            covered.add(check_id)
    assert known - covered == set()


def test_the_issue_form_fixture_carries_a_real_entry_through_the_converter():
    """Offline check on the human path: form labels come from the form file, and no field is lost or changed."""
    entry = next(e for e in wikilib.load_entries(REPO_ROOT / "entries") if e.id == "fe-2026-0006")
    draft = {key: value for key, value in copy.deepcopy(entry.data).items() if key not in verify.SYSTEM_KEYS}
    body = verify.issue_body(draft, entry.body)
    fields = issue_to_entry.parse_issue_body(body)
    assert issue_to_entry.confirmations_ticked(fields)
    converted, notes = issue_to_entry.entry_from_fields(fields)
    assert wikilib.normalize_data(converted) == wikilib.normalize_data(draft)
    assert notes.strip() == entry.body.strip()
    assert not issue_to_entry.confirmations_ticked(issue_to_entry.parse_issue_body(verify.issue_body(draft, entry.body, ticked=False)))


def test_machine_paths_are_scrubbed_from_evidence(tmp_path):
    clone = tmp_path / "clone"
    clone.mkdir()
    scrub = verify.Scrubber(tmp_path, clone)
    home = str(Path.home())
    shown = scrub(f"{clone}/entries/x.md {tmp_path}/fixtures/y {REPO_ROOT}/z {home}/elsewhere")
    assert shown == "./entries/x.md $WORK/fixtures/y <repo>/z ~/elsewhere"
    assert home not in shown

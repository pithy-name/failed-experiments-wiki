"""Datasette: the database lists all entries and every field can be filtered."""
import copy
import json
import sqlite3
import subprocess
import sys
from pathlib import Path

import pytest

import build_db
import wikilib


@pytest.fixture
def built(tmp_path, valid_entry):
    entries_dir = tmp_path / "entries"
    entries_dir.mkdir()
    second = copy.deepcopy(valid_entry)
    second.update(
        id="fe-2026-0002",
        title="SAE probes did not beat linear probes out of distribution",
        research_area=["interpretability", "robustness"],
        method=["sae", "linear-probing"],
        failure_type="underpowered",
        retry_welcome=False,
        claim_scope="Gemma residual stream dictionaries on five probing datasets, zebra-striped splits.",
    )
    second["models"] = [
        {"name": "Gemma 2 9B", "developer": "Google DeepMind", "version": "unknown", "size": "9B", "access": "open-weight"},
        {"name": "GPT-4o", "developer": "OpenAI", "version": "unknown", "size": "unknown", "access": "api"},
    ]
    second["result"] = {"direction": "smaller_than_expected", "effect_size": -0.12, "n": 5}
    second["source"] = dict(second["source"], published="2025-06-10")
    second["contributor"] = {"type": "human", "handle": "someone", "note": "Draft awaiting verification."}
    second["review"] = {"status": "reviewed", "reviewers": [{"handle": "rev", "type": "human", "date": "2026-11-15", "notes": "ok"}]}
    second["dates"] = {"created": "2026-11-14", "updated": "2026-11-15"}
    second["related"] = [{"id": "fe-2026-0001", "relation": "same_hypothesis"}]
    (entries_dir / "fe-2026-0001.md").write_text(wikilib.dump_entry(valid_entry, "First body mentions quokka."), encoding="utf-8")
    (entries_dir / "fe-2026-0002.md").write_text(wikilib.dump_entry(second, ""), encoding="utf-8")
    db_path = tmp_path / "wiki.db"
    metadata_path = tmp_path / "metadata.yml"
    assert build_db.main(["--entries", str(entries_dir), "--db", str(db_path), "--metadata", str(metadata_path)]) == 0
    return {"db": db_path, "metadata": metadata_path, "entries": entries_dir}


def query(db_path, sql, params=()):
    with sqlite3.connect(db_path) as connection:
        return connection.execute(sql, params).fetchall()


def test_every_schema_field_has_a_column(built):
    columns = {row[1] for row in query(built["db"], "pragma table_info(entries)")}
    assert {build_db.column_name(path) for path, _ in wikilib.FIELDS} <= columns
    assert {"badges", "body"} <= columns


def test_rows_and_list_tables(built):
    assert query(built["db"], "select count(*) from entries") == [(2,)]
    assert query(built["db"], "select count(*) from entry_models") == [(3,)]
    assert query(built["db"], "select value from entry_method where entry_id = 'fe-2026-0002' order by value") == [("linear-probing",), ("sae",)]
    assert query(built["db"], "select handle, type from entry_reviewers") == [("rev", "human")]
    assert query(built["db"], "select entry_id, related_id, relation from entry_related") == [("fe-2026-0002", "fe-2026-0001", "same_hypothesis")]
    assert ("fe-2026-0001", "agent-written") in query(built["db"], "select entry_id, value from entry_badges")
    for table in ("entry_research_area", "entry_benchmarks", "entry_checks_done", "entry_source_authors", "entry_source_lw_tags"):
        assert query(built["db"], f"select count(*) from {table}")[0][0] >= 1


def test_types_support_range_filters(built):
    assert query(built["db"], "select id from entries where source_published >= ?", ("2025-06-01",)) == [("fe-2026-0002",)]
    assert query(built["db"], "select id from entries where result_n >= ?", (100,)) == [("fe-2026-0001",)]
    assert query(built["db"], "select id from entries where result_effect_size < 0") == [("fe-2026-0002",)]
    assert query(built["db"], "select id from entries where retry_welcome = 1") == [("fe-2026-0001",)]
    assert query(built["db"], "select id from entries where result_ci_low is null order by id") == [("fe-2026-0001",), ("fe-2026-0002",)]


def test_list_fields_are_json_arrays_in_the_main_table(built):
    row = query(built["db"], "select method, models_name, badges, review_reviewers_handle from entries where id = 'fe-2026-0002'")[0]
    assert json.loads(row[0]) == ["sae", "linear-probing"]
    assert json.loads(row[1]) == ["Gemma 2 9B", "GPT-4o"]
    assert json.loads(row[2]) == []
    assert json.loads(row[3]) == ["rev"]


def test_full_text_search_covers_fields_and_body(built):
    def search(word):
        return query(built["db"], "select id from entries where rowid in (select rowid from entries_fts where entries_fts match ?)", (word,))

    assert search("zebra") == [("fe-2026-0002",)]
    assert search("quokka") == [("fe-2026-0001",)]


def test_rebuild_is_idempotent(built):
    assert build_db.main(["--entries", str(built["entries"]), "--db", str(built["db"]), "--metadata", str(built["metadata"])]) == 0
    assert query(built["db"], "select count(*) from entries") == [(2,)]
    assert query(built["db"], "select count(*) from entry_models") == [(3,)]
    assert [p.name for p in built["db"].parent.glob("*.db")] == ["wiki.db"]


def datasette_get(built, path):
    datasette = Path(sys.executable).parent / "datasette"
    if not datasette.exists():
        pytest.skip("datasette is not installed")
    completed = subprocess.run(
        [str(datasette), str(built["db"]), "--metadata", str(built["metadata"]), "--get", path],
        capture_output=True, text=True, timeout=120,
    )
    assert completed.returncode == 0, completed.stderr[-800:]
    return json.loads(completed.stdout)


def test_datasette_lists_filters_searches_and_facets_without_a_port(built):
    """Runs Datasette itself in its in-process request mode: no socket is opened."""
    ids = lambda rows: sorted(row["id"] for row in rows)  # noqa: E731
    assert ids(datasette_get(built, "/wiki/entries.json?_shape=array")) == ["fe-2026-0001", "fe-2026-0002"]
    assert ids(datasette_get(built, "/wiki/entries.json?_shape=array&failure_type=underpowered")) == ["fe-2026-0002"]
    assert ids(datasette_get(built, "/wiki/entries.json?_shape=array&method__arraycontains=sae")) == ["fe-2026-0002"]
    assert ids(datasette_get(built, "/wiki/entries.json?_shape=array&badges__arraycontains=agent-written")) == ["fe-2026-0001"]
    assert ids(datasette_get(built, "/wiki/entries.json?_shape=array&source_published__gte=2025-06-01")) == ["fe-2026-0002"]
    assert ids(datasette_get(built, "/wiki/entries.json?_shape=array&result_n__gte=100")) == ["fe-2026-0001"]
    assert ids(datasette_get(built, "/wiki/entries.json?_shape=array&contributor_handle=someone")) == ["fe-2026-0002"]
    assert ids(datasette_get(built, "/wiki/entries.json?_shape=array&_search=quokka")) == ["fe-2026-0001"]

    page = datasette_get(built, "/wiki/entries.json?_facet=review_status&_facet_array=models_developer")
    facets = page["facet_results"]
    facets = facets.get("results", facets)
    # facets configured in metadata.yml are applied without being asked for
    assert {"failure_type", "badges", "method", "review_status", "models_developer"} <= set(facets)
    failure_counts = {item["value"]: item["count"] for item in facets["failure_type"]["results"]}
    assert failure_counts == {"hypothesis_false": 1, "underpowered": 1}
    assert {item["value"] for item in facets["method"]["results"]} == {"activation-steering", "sae", "linear-probing"}

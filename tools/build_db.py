"""Build wiki.db, a SQLite database of the wiki, for browsing with Datasette.

  python tools/build_db.py                 # entries/ -> wiki.db, datasette/metadata.yml
  python tools/build_db.py --serve         # build, then run Datasette on port 8001

Tables:
- entries: one row per entry. One column per schema field (dots become
  underscores). List fields are JSON arrays in this table, so Datasette can
  facet and filter them (?_facet_array=method, ?method__arraycontains=sae).
  `badges` holds the derived badges. Full-text search covers the text fields.
- entry_research_area, entry_method, entry_benchmarks, entry_checks_done,
  entry_source_authors, entry_source_lw_tags, entry_badges: one row per value.
- entry_models, entry_reviewers, entry_related: one row per item.

The column list comes from wikilib.FIELDS, so a new schema field gets a column.
The database is rebuilt from scratch on every run and is git-ignored.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
import tempfile
from pathlib import Path

import sqlite_utils
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
import wikilib  # noqa: E402

DEFAULT_DB = wikilib.REPO_ROOT / "wiki.db"
METADATA_PATH = wikilib.REPO_ROOT / "datasette" / "metadata.yml"

# Paths that sit inside a list of objects: always stored as JSON arrays.
NESTED_LIST_PREFIXES = ("models.", "review.reviewers.", "related.")
VALUE_TABLES = {
    "research_area": "entry_research_area",
    "method": "entry_method",
    "benchmarks": "entry_benchmarks",
    "checks_done": "entry_checks_done",
    "source.authors": "entry_source_authors",
    "source.lw_tags": "entry_source_lw_tags",
}
ITEM_TABLES = {
    "models": ("entry_models", ["name", "developer", "version", "size", "access"], {}),
    "review.reviewers": ("entry_reviewers", ["handle", "type", "date", "notes", "agent_model"], {}),
    "related": ("entry_related", ["id", "relation"], {"id": "related_id"}),
}
FTS_COLUMNS = [
    "title", "hypothesis", "claim_scope", "limitations", "revival_conditions", "source_title", "source_section",
    "source_quote", "contributor_note", "body",
]
SCALAR_FACETS = [
    "result_direction", "failure_type", "confidence_true_negative", "retry_welcome", "evidence_level", "source_type",
    "contributor_type", "review_status", "info_hazard",
]
ARRAY_FACETS = ["badges", "research_area", "method", "models_name", "benchmarks"]


def column_name(path: str) -> str:
    return path.replace(".", "_")


def is_array_column(path: str, kind: str) -> bool:
    return kind == "list" or path.startswith(NESTED_LIST_PREFIXES)


def column_types() -> dict[str, type]:
    """Explicit column types, so a column exists (as NULLs) even when no entry uses the field yet."""
    types: dict[str, type] = {}
    for path, kind in wikilib.FIELDS:
        if is_array_column(path, kind):
            types[column_name(path)] = str
        elif kind == "bool":
            types[column_name(path)] = int
        elif kind == "number":
            types[column_name(path)] = int if path == "result.n" else float
        else:
            types[column_name(path)] = str
    types["badges"] = str
    types["body"] = str
    return types


def entry_row(entry: wikilib.Entry) -> dict:
    row: dict = {}
    for path, kind in wikilib.FIELDS:
        values = wikilib.get_values(entry.data, path)
        if is_array_column(path, kind):
            row[column_name(path)] = json.dumps(values, ensure_ascii=False)
        elif not values:
            row[column_name(path)] = None
        elif kind == "bool":
            row[column_name(path)] = int(bool(values[0]))
        else:
            row[column_name(path)] = values[0]
    row["badges"] = json.dumps(wikilib.badges(entry.data), ensure_ascii=False)
    row["body"] = entry.body
    return row


def build(entries_dir: Path, db_path: Path) -> dict:
    """Write the database to a temp file, then move it into place, so a failed build leaves the old one."""
    entries = wikilib.load_entries(entries_dir)
    db_path = Path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    handle, tmp_name = tempfile.mkstemp(suffix=".db", dir=str(db_path.parent))
    os.close(handle)
    tmp_path = Path(tmp_name)
    tmp_path.unlink()
    try:
        db = sqlite_utils.Database(tmp_path)
        types = column_types()
        db["entries"].create({"id": str, **{k: v for k, v in types.items() if k != "id"}}, pk="id")
        db["entries"].insert_all([entry_row(entry) for entry in entries])
        db["entries"].enable_fts(FTS_COLUMNS, create_triggers=True)

        foreign = [("entry_id", "entries", "id")]
        value_tables = {**VALUE_TABLES, "badges": "entry_badges"}
        for path, table in value_tables.items():
            db[table].create({"entry_id": str, "value": str}, foreign_keys=foreign)
            rows = []
            for entry in entries:
                values = wikilib.badges(entry.data) if path == "badges" else wikilib.get_values(entry.data, path)
                rows.extend({"entry_id": entry.id, "value": str(value)} for value in values)
            db[table].insert_all(rows)
        for path, (table, keys, renames) in ITEM_TABLES.items():
            db[table].create({"entry_id": str, **{renames.get(key, key): str for key in keys}}, foreign_keys=foreign)
            rows = []
            for entry in entries:
                for item in wikilib.get_values(entry.data, path):
                    if isinstance(item, dict):
                        rows.append({"entry_id": entry.id, **{renames.get(key, key): item.get(key) for key in keys}})
            db[table].insert_all(rows)
        db.close()
        shutil.move(str(tmp_path), str(db_path))
    finally:
        if tmp_path.exists():
            tmp_path.unlink()
    return {"entries": len(entries), "db": str(db_path)}


def metadata(db_name: str = "wiki") -> dict:
    return {
        "title": "Failed-experiments wiki",
        "description": (
            "A wiki of failed AI-safety experiments, drawn from LessWrong and the Alignment Forum. Entries describe "
            "experiments and never judge people. Agent-written and unreviewed entries are labelled in the badges column."
        ),
        "databases": {
            db_name: {
                "description": "Built from entries/ by tools/build_db.py. Read-only; edit the entry files, not the database.",
                "tables": {
                    "entries": {
                        "description": (
                            "One row per entry. Every column can be filtered. Badges (agent-written, unreviewed, contested, "
                            "superseded, retry-welcome) are derived from the contributor and review fields."
                        ),
                        "sort": "id",
                        "facets": SCALAR_FACETS + [{"array": column} for column in ARRAY_FACETS],
                    },
                    "entry_models": {"description": "One row per model tested in an entry.", "facets": ["developer", "access", "name"]},
                    "entry_reviewers": {"description": "One row per review of an entry.", "facets": ["type", "handle"]},
                    "entry_related": {"description": "Links between entries.", "facets": ["relation"]},
                    "entry_method": {"description": "One row per method tag.", "facets": ["value"]},
                    "entry_research_area": {"description": "One row per research area.", "facets": ["value"]},
                    "entry_badges": {"description": "One row per derived badge.", "facets": ["value"]},
                },
            }
        },
    }


def write_metadata(path: Path = METADATA_PATH, db_name: str = "wiki") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = "# Generated by tools/build_db.py. Edit the metadata() function there, not this file.\n"
    text += yaml.safe_dump(metadata(db_name), sort_keys=False, allow_unicode=True, width=100)
    path.write_text(text, encoding="utf-8")


def find_datasette() -> str | None:
    beside = Path(sys.executable).parent / "datasette"
    return str(beside) if beside.exists() else shutil.which("datasette")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build the SQLite database for Datasette.")
    parser.add_argument("--entries", default=str(wikilib.ENTRIES_DIR))
    parser.add_argument("--db", default=str(DEFAULT_DB))
    parser.add_argument("--metadata", default=str(METADATA_PATH))
    parser.add_argument("--serve", action="store_true", help="after building, run Datasette")
    parser.add_argument("--port", type=int, default=8001)
    args = parser.parse_args(argv)

    outcome = build(Path(args.entries), Path(args.db))
    write_metadata(Path(args.metadata), Path(args.db).stem)
    print(f"built {outcome['db']} with {outcome['entries']} entries; metadata at {args.metadata}")
    if args.serve:
        datasette = find_datasette()
        if not datasette:
            print("datasette is not installed: pip install -r requirements-dev.txt", file=sys.stderr)
            return 1
        print(f"serving at http://localhost:{args.port}/{Path(args.db).stem}/entries  (Ctrl-C to stop)")
        os.execv(datasette, [datasette, args.db, "--metadata", args.metadata, "--port", str(args.port)])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

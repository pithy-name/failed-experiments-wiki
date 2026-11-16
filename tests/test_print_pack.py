"""The printable review pack: marks go only where a passage is found, and never change the post's words."""
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "tools"))
import make_print_pack  # noqa: E402

POST = "We expected the probe to transfer. It did not: accuracy stayed at chance on the held-out set. We only tried layer 20."
MARK = re.compile(r"\*\*⟦[^⟧/][^⟧]*⟧\*\* | \*\*⟦/⟧\*\*")     # an opening mark and its one added space, or a closing mark and its


def notes(*pairs):
    """Annotations in the shape the annotators write: {"entries": {entry id: {field: [{"snippet": ...}]}}}."""
    entries = {}
    for entry_id, field, snippet in pairs:
        entries.setdefault(entry_id, {}).setdefault(field, []).append({"snippet": snippet, "note": ""})
    return {"entries": entries}


def test_a_passage_found_in_the_post_is_marked_where_it_sits():
    marked, placed, missing = make_print_pack.annotate(POST, notes(("fe-2026-0001", "hypothesis", "We expected the probe to transfer.")))
    assert marked.startswith("**⟦HYPOTHESIS · 0001⟧** We expected the probe to transfer. **⟦/⟧**")
    assert placed == {("fe-2026-0001", "hypothesis"): 1}
    assert missing == []


def test_marking_never_changes_the_posts_own_words():
    marked, _, _ = make_print_pack.annotate(POST, notes(
        ("fe-2026-0001", "hypothesis", "We expected the probe to transfer."),
        ("fe-2026-0001", "result", "accuracy stayed at chance on the held-out set"),
        ("fe-2026-0001", "quote", "accuracy stayed at chance"),            # sits inside the passage above
        ("fe-2026-0002", "claim_scope", "We only tried layer 20."),
    ))
    assert MARK.sub("", marked) == POST


def test_a_passage_that_is_not_in_the_post_is_reported_and_not_marked():
    marked, placed, missing = make_print_pack.annotate(POST, notes(("fe-2026-0001", "result", "accuracy rose above chance")))
    assert marked == POST
    assert placed == {}
    assert missing == [("fe-2026-0001", "result", "accuracy rose above chance")]


def test_fields_and_entries_that_share_a_passage_share_one_mark():
    passage = "We only tried layer 20."
    marked, placed, _ = make_print_pack.annotate(POST, notes(
        ("fe-2026-0001", "claim_scope", passage), ("fe-2026-0001", "limitations", passage), ("fe-2026-0002", "claim_scope", passage)))
    assert marked.count("⟦/⟧") == 1
    assert "⟦SCOPE, LIMITATIONS · 0001 | SCOPE · 0002⟧" in marked
    assert sum(placed.values()) == 3


def test_hand_wrapped_text_becomes_one_line_per_paragraph_and_list_item():
    wrapped = "A paragraph wrapped\nby hand.\n\n1. A step that\n   runs on.\n   - a nested point\n     that runs on\n\n## Heading\nText under it."
    assert make_print_pack.reflow(wrapped) == (
        "A paragraph wrapped by hand.\n\n1. A step that runs on.\n   - a nested point that runs on\n\n## Heading\nText under it.")


def test_reflow_leaves_code_and_tables_as_they_are():
    kept = "Run:\n\n```\npython a.py\npython b.py\n```\n\n| a | b |\n|---|---|\n| 1 | 2 |"
    assert make_print_pack.reflow(kept) == kept


def test_no_printout_of_the_skills_and_tools_is_wrapped_by_hand():
    """Outside code blocks, every line that follows another line starts something new (a list item, a heading, a table row)."""
    fenced, previous = False, ""
    for line in make_print_pack.tools_markdown().split("\n"):
        if line.strip().startswith("```"):
            fenced = not fenced
        elif not fenced and line.strip() and previous.strip() and not previous.strip().startswith(("```", "#", "|", ">", "---")):
            assert make_print_pack._STARTS_A_BLOCK.match(line), (previous, line)
        previous = line


def test_a_tools_description_prints_as_text_with_its_arguments_listed():
    prose = make_print_pack.docstring_as_prose("Search the wiki.\n\nquery: free text; matched by keyword.\n  Try synonyms.\nAn empty query lists everything.")
    assert prose == "Search the wiki.\n\n- **query:** free text; matched by keyword. Try synonyms.\n\nAn empty query lists everything."


def test_the_schema_printout_lists_every_field_in_the_schema():
    schema = json.loads((REPO / "schema" / "entry.schema.json").read_text(encoding="utf-8"))
    printout = make_print_pack.schema_markdown()
    for name in schema["properties"]:
        assert f"| `{name}` |" in printout, name


def test_the_tracked_schema_printout_is_what_the_builder_makes_now():
    assert (REPO / "schema" / "SCHEMA.md").read_text(encoding="utf-8") == make_print_pack.schema_markdown()


def test_the_tools_printout_names_every_tool_the_server_offers():
    printout = make_print_pack.tools_markdown()
    for tool in ("search_entries", "get_entry", "list_facets", "fetch_source", "submit_entry", "review_entry"):
        assert f"### `{tool}(" in printout, tool

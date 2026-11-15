import copy

import wikilib
from wikilib import Entry


def schema_leaves(node, prefix=""):
    """Dotted paths of every leaf field in the JSON Schema (lists of objects are descended into)."""
    leaves = []
    for name, spec in node.get("properties", {}).items():
        path = f"{prefix}{name}"
        if spec.get("type") == "object":
            leaves.extend(schema_leaves(spec, path + "."))
        elif spec.get("type") == "array" and spec.get("items", {}).get("type") == "object":
            leaves.extend(schema_leaves(spec["items"], path + "."))
        else:
            leaves.append(path)
    return leaves


def test_field_catalogue_covers_every_schema_field():
    """'Every field is filterable' starts here: the catalogue drives facets, ranges and search."""
    catalogue = {path for path, _ in wikilib.FIELDS}
    assert catalogue == set(schema_leaves(wikilib.load_schema()))


def test_every_catalogue_kind_is_filterable():
    kinds = {kind for _, kind in wikilib.FIELDS}
    assert kinds <= wikilib.FACET_KINDS | wikilib.RANGE_KINDS | wikilib.TEXT_KINDS


def test_dump_and_parse_round_trip(valid_entry):
    text = wikilib.dump_entry(valid_entry, "Free text body.")
    data, body = wikilib.parse_entry_text(text)
    assert data == valid_entry
    assert body == "Free text body."
    assert text.index("id:") < text.index("title:") < text.index("source:") < text.index("info_hazard:")


def test_badges_follow_the_prd_rules(valid_entry):
    assert wikilib.badges(valid_entry) == ["agent-written", "unreviewed", "retry-welcome"]
    human = copy.deepcopy(valid_entry)
    human["contributor"] = {"type": "human", "handle": "someone"}
    human["review"] = {"status": "reviewed", "reviewers": [{"handle": "r", "type": "human", "date": "2026-11-15"}]}
    human["retry_welcome"] = False
    assert wikilib.badges(human) == []
    human["review"]["status"] = "contested"
    assert wikilib.badges(human) == ["contested"]


def make_entries(valid_entry):
    second = copy.deepcopy(valid_entry)
    second.update(
        id="fe-2026-0002",
        title="Sparse autoencoder probes did not beat linear probes on out-of-distribution data",
        research_area=["interpretability"],
        method=["sae", "probing"],
        failure_type="underpowered",
        retry_welcome=False,
        hypothesis="SAE latents give more robust probes than raw activations.",
        claim_scope="Gemma 2 residual stream SAEs on five probing datasets.",
    )
    second["models"] = [{"name": "Gemma 2 9B", "developer": "Google DeepMind", "version": "unknown", "size": "9B", "access": "open-weight"}]
    second["source"] = dict(second["source"], published="2025-06-10", quote="SAE probes underperformed", title="Another test post")
    second["limitations"] = "Only residual stream SAEs."
    second["revival_conditions"] = "Better dictionaries."
    second["benchmarks"] = ["probing-suite"]
    second["checks_done"] = ["noise-floor"]
    second["result"] = {"direction": "smaller_than_expected", "n": 5}
    second["contributor"] = {"type": "human", "handle": "someone"}
    return [Entry(valid_entry, "body one"), Entry(second, "")]


def test_search_ranks_by_keyword_and_reports_matched_terms(valid_entry):
    entries = make_entries(valid_entry)
    found = wikilib.search(entries, "I want to try steering vectors for refusal")
    assert [r["id"] for r in found["results"]] == ["fe-2026-0001"]
    assert "steering" in found["results"][0]["matched_terms"]
    assert wikilib.search(entries, "sparse autoencoders")["results"][0]["id"] == "fe-2026-0002"


def test_search_with_no_match_returns_nothing_and_says_how_many_entries_exist(valid_entry):
    found = wikilib.search(make_entries(valid_entry), "protein folding")
    assert found["match_count"] == 0 and found["total_entries_in_wiki"] == 2


def test_search_lists_an_entry_on_any_term_and_says_so(valid_entry):
    """Ranked any-term matching: one real word among nonsense still lists the entry, and the result says which word hit."""
    found = wikilib.search(make_entries(valid_entry), "zzzqqq steering xxxyyy")
    assert [r["id"] for r in found["results"]] == ["fe-2026-0001"]
    assert found["results"][0]["matched_terms"] == ["steering"]
    assert "ANY of the query terms" in found["note"] and "weak match" in found["note"]


def test_empty_query_lists_everything_passing_the_filters(valid_entry):
    entries = make_entries(valid_entry)
    assert wikilib.search(entries)["match_count"] == 2
    assert [r["id"] for r in wikilib.search(entries, filters={"failure_type": "underpowered"})["results"]] == ["fe-2026-0002"]


def test_filters_cover_lists_nested_fields_booleans_ranges_and_badges(valid_entry):
    entries = make_entries(valid_entry)

    def ids(filters):
        return [r["id"] for r in wikilib.search(entries, filters=filters)["results"]]

    assert ids({"method": ["sae", "rl"]}) == ["fe-2026-0002"]
    assert ids({"models.developer": "openai"}) == ["fe-2026-0001"]
    assert ids({"retry_welcome": True}) == ["fe-2026-0001"]
    assert ids({"contributor.type": "human"}) == ["fe-2026-0002"]
    assert ids({"source.published_min": "2025-06-01"}) == ["fe-2026-0002"]
    assert ids({"source.published_max": "2025-06-01"}) == ["fe-2026-0001"]
    assert ids({"result.n_min": 100}) == ["fe-2026-0001"]
    assert ids({"badges": "agent-written"}) == ["fe-2026-0001"]
    assert ids({"failure_type": "hypothesis_false", "method": "sae"}) == []


def test_facets_count_values_and_give_ranges(valid_entry):
    result = wikilib.facets(make_entries(valid_entry))
    assert result["total_entries"] == 2
    assert result["facets"]["failure_type"] == {"hypothesis_false": 1, "underpowered": 1}
    assert result["facets"]["method"]["sae"] == 1
    assert result["facets"]["retry_welcome"] == {"false": 1, "true": 1}
    assert result["facets"]["badges"]["agent-written"] == 1
    assert result["ranges"]["source.published"] == {"min": "2025-03-01", "max": "2025-06-10"}
    assert result["ranges"]["result.effect_size"] is None
    assert "claim_scope" in result["text_fields"]


def test_normalize_tag():
    assert wikilib.normalize_tag("Activation Steering") == "activation-steering"
    assert wikilib.normalize_tag("  SAE_probing ") == "sae-probing"

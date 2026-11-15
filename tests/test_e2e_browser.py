"""End-to-end checks in a real browser engine (Playwright's headless Chromium), on the real entries.

Unit tests run the page's script against a stand-in DOM. These drive the actual
page: every facet value of every field is ticked and the cards shown are
compared with what the entry data says they should be. Datasette's own pages
are loaded in the same browser, served in process (no port is opened).

Skipped when Playwright or its browser is not installed (`make demo-setup`).
"""
from __future__ import annotations

import asyncio
import copy
import os
import threading
from pathlib import Path
from urllib.parse import urlsplit

import pytest
import yaml

import build_db
import build_site
import wikilib

REPO_ROOT = Path(__file__).resolve().parent.parent
if (REPO_ROOT / ".cache" / "ms-playwright").exists():
    os.environ.setdefault("PLAYWRIGHT_BROWSERS_PATH", str(REPO_ROOT / ".cache" / "ms-playwright"))
sync_api = pytest.importorskip("playwright.sync_api")

ENTRIES = wikilib.load_entries(REPO_ROOT / "entries")
BY_ID = {entry.id: entry for entry in ENTRIES}
CATALOGUE = build_site.field_catalogue()


@pytest.fixture(scope="module")
def browser():
    with sync_api.sync_playwright() as playwright:
        try:
            instance = playwright.chromium.launch(headless=True)
        except Exception:  # noqa: BLE001  inside a sandbox the multi-process launch crashes
            try:
                instance = playwright.chromium.launch(headless=True, args=["--single-process", "--no-zygote", "--disable-gpu"])
            except Exception as exc:  # noqa: BLE001
                pytest.skip(f"no usable browser: {str(exc).splitlines()[0]}")
        yield instance
        instance.close()


@pytest.fixture(scope="module")
def context(browser):
    """One context for the whole module: in single-process mode a second context kills the browser."""
    context = browser.new_context(viewport={"width": 1280, "height": 800})
    yield context
    context.close()


@pytest.fixture(scope="module")
def site_url(tmp_path_factory):
    out = tmp_path_factory.mktemp("site") / "site" / "index.html"
    build_site.build(REPO_ROOT / "entries", out, None)
    return out.as_uri()


@pytest.fixture
def page(context, site_url):
    page = context.new_page()
    page.problems = []
    page.requests = []
    page.on("console", lambda message: page.problems.append(message.text) if message.type == "error" else None)
    page.on("pageerror", lambda error: page.problems.append(str(error)))
    page.on("request", lambda request: page.requests.append(request.url))
    page.on("dialog", lambda dialog: (page.problems.append("dialog: " + dialog.message), dialog.dismiss()))
    page.goto(site_url)
    page.wait_for_selector("article.card")
    page.evaluate("() => document.querySelectorAll('details.group').forEach(d => { d.open = true; })")
    yield page
    page.close()


@pytest.fixture(scope="module")
def snap(request):
    """Save a screenshot when pytest runs with --snap-dir, so a person (or the agent) can look at what the checks saw."""
    folder = request.config.getoption("--snap-dir")
    if folder:
        Path(folder).mkdir(parents=True, exist_ok=True)

    def take(page, name: str, full_page: bool = False) -> None:
        if folder:
            page.screenshot(path=str(Path(folder) / f"{name}.png"), full_page=full_page)
    return take


def shown_ids(page) -> list[str]:
    return page.evaluate("() => Array.from(document.querySelectorAll('article.card')).map(card => card.id.replace('entry-', ''))")


def css_string(value: str) -> str:
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\a ") + '"'


def checkbox(page, path: str, value: str):
    return page.locator(f"input[data-facet={css_string(path)}][data-value={css_string(value)}]")


def values_of(entry, path: str) -> set[str]:
    if path == "badges":
        return set(wikilib.badges(entry.data))
    return {wikilib._facet_key(value) for value in wikilib.get_values(entry.data, path)}


def all_strings(value) -> list[str]:
    if isinstance(value, dict):
        return [text for item in value.values() for text in all_strings(item)]
    if isinstance(value, list):
        return [text for item in value for text in all_strings(item)]
    return [] if value is None else [str(value)]


def test_page_loads_all_entries_with_no_errors_and_no_outside_requests(page, site_url, snap):
    snap(page, "page-01-default")
    snap(page, "page-02-default-full", full_page=True)
    assert page.locator("#count").inner_text() == f"{len(ENTRIES)} of {len(ENTRIES)} entries"
    assert shown_ids(page) == [entry.id for entry in ENTRIES]
    assert page.problems == []
    assert [url for url in page.requests if not url.startswith("file://")] == []
    assert page.locator("#clear").is_disabled()


def test_every_value_of_every_facet_field_filters_to_exactly_the_right_entries(page):
    """The claim 'every field is filterable', checked value by value against the entry data."""
    checked_fields, checked_values = 0, 0
    for field in CATALOGUE:
        if field["control"] != "facet":
            continue
        values = sorted({value for entry in ENTRIES for value in values_of(entry, field["path"])})
        if not values:
            assert page.locator(f"input[data-facet={css_string(field['path'])}]").count() == 0   # unused fields are hidden
            continue
        checked_fields += 1
        for value in values:
            box = checkbox(page, field["path"], value)
            assert box.count() == 1, (field["path"], value)
            box.check()
            expected = [entry.id for entry in ENTRIES if value in values_of(entry, field["path"])]
            assert shown_ids(page) == expected, (field["path"], value)
            assert page.locator("#count").inner_text() == f"{len(expected)} of {len(ENTRIES)} entries"
            box.uncheck()
            checked_values += 1
    assert shown_ids(page) == [entry.id for entry in ENTRIES]
    assert checked_fields >= 20 and checked_values >= 100, (checked_fields, checked_values)
    assert page.problems == []


def test_facet_counts_shown_match_the_data(page):
    for path in ("failure_type", "badges", "method", "models.name", "review.status"):
        for value in sorted({v for entry in ENTRIES for v in values_of(entry, path)}):
            label = checkbox(page, path, value).locator("xpath=ancestor::label[1]")
            shown = int(label.locator(".facet-count").inner_text())
            assert shown == sum(1 for entry in ENTRIES if value in values_of(entry, path)), (path, value)


def test_every_range_field_filters_inclusively_and_drops_entries_without_the_field(page):
    checked = 0
    for field in CATALOGUE:
        if field["control"] != "range":
            continue
        pairs = [(entry.id, value) for entry in ENTRIES for value in wikilib.get_values(entry.data, field["path"])]
        low = page.locator(f"input[data-range={css_string(field['path'])}][data-bound=\"min\"]")
        high = page.locator(f"input[data-range={css_string(field['path'])}][data-bound=\"max\"]")
        if not pairs:
            assert low.count() == 0
            continue
        checked += 1
        key = (lambda v: float(v)) if field["kind"] == "number" else str
        ordered = sorted({key(value) for _, value in pairs})
        middle = ordered[len(ordered) // 2]
        text = str(middle) if field["kind"] == "date" else repr(middle).rstrip("0").rstrip(".") if isinstance(middle, float) else str(middle)

        low.fill(text)
        assert shown_ids(page) == [e.id for e in ENTRIES if any(key(v) >= middle for v in wikilib.get_values(e.data, field["path"]))], field["path"]
        low.fill("")
        high.fill(text)
        assert shown_ids(page) == [e.id for e in ENTRIES if any(key(v) <= middle for v in wikilib.get_values(e.data, field["path"]))], field["path"]
        high.fill("")
        assert len(shown_ids(page)) == len(ENTRIES)
    assert checked >= 4, checked


@pytest.mark.parametrize("term", ["steganography", "GPT-2", "random directions", "zzz-no-such-word", "fe-2026-0009", "pre-registered"])
def test_search_finds_text_in_any_field_or_the_body(page, term, snap):
    page.locator("#search").fill(term)
    snap(page, "page-05-search-" + "".join(ch if ch.isalnum() else "-" for ch in term))
    words = term.lower().split()
    expected = []
    for entry in ENTRIES:
        haystack = " \n ".join(all_strings(entry.data) + [entry.body, entry.id] + wikilib.badges(entry.data)).lower()
        if all(word in haystack for word in words):
            expected.append(entry.id)
    assert shown_ids(page) == expected, term
    if not expected:
        assert "nobody has filed one" in page.locator("#results").inner_text()


def test_filters_combine_and_clear_resets_everything(page, snap):
    checkbox(page, "badges", "agent-written").check()
    checkbox(page, "failure_type", "hypothesis_false").check()
    checkbox(page, "failure_type", "unknown").check()
    page.locator("#search").fill("sae")
    snap(page, "page-04-combined-filters")
    expected = [
        e.id for e in ENTRIES
        if "agent-written" in wikilib.badges(e.data) and e.data["failure_type"] in {"hypothesis_false", "unknown"}
        and "sae" in " ".join(all_strings(e.data) + [e.body]).lower()
    ]
    assert shown_ids(page) == expected and 0 < len(expected) < len(ENTRIES)
    page.locator("#clear").click()
    assert shown_ids(page) == [entry.id for entry in ENTRIES]
    assert page.locator("#search").input_value() == ""
    assert page.locator("input[type=checkbox]:checked").count() == 0
    assert page.evaluate("() => location.hash") in {"", "#"}


def test_a_filtered_view_survives_as_a_link(page, context, site_url, snap):
    checkbox(page, "method", "sae").check()
    page.locator("#search").fill("dead")
    page.locator('input[data-range="source.published"][data-bound="min"]').fill("2024-01-01")
    page.locator('input[data-range="source.published"][data-bound="max"]').fill("2026-12-31")
    before = shown_ids(page)
    assert 0 < len(before) < len(ENTRIES), before          # a view that shows nothing would prove nothing
    link = page.evaluate("() => location.hash")
    assert "f.method=sae" in link and "q=dead" in link and "min.source.published=2024-01-01" in link
    assert "max.source.published=2026-12-31" in link
    snap(page, "page-06-range-and-link")

    other = context.new_page()
    other.goto(site_url + link)
    other.wait_for_selector("#count")
    assert shown_ids(other) == before
    assert other.locator("#search").input_value() == "dead"
    assert checkbox(other, "method", "sae").is_checked()
    other.close()


def test_every_facet_value_round_trips_through_a_link(page, context, site_url):
    """Values contain spaces, slashes, colons and the like; each must survive being written to the link and read back."""
    other = context.new_page()
    checked = 0
    for field in CATALOGUE:
        if field["control"] != "facet":
            continue
        for value in sorted({v for entry in ENTRIES for v in values_of(entry, field["path"])}):
            box = checkbox(page, field["path"], value)
            box.check()
            link, before = page.evaluate("() => location.hash"), shown_ids(page)
            box.uncheck()
            other.goto("about:blank")
            other.goto(site_url + link)
            other.wait_for_selector("#count")
            assert shown_ids(other) == before, (field["path"], value, link)
            assert checkbox(other, field["path"], value).is_checked(), (field["path"], value, link)
            assert other.locator("input[type=checkbox]:checked").count() == 1, (field["path"], value, link)
            checked += 1
    other.close()
    assert checked >= 100, checked


def test_an_opened_entry_is_part_of_the_link(page, context, site_url, snap):
    entry = ENTRIES[8]
    page.locator(f"#entry-{entry.id} details.all-fields > summary").click()
    page.wait_for_function("() => location.hash.indexOf('open=') !== -1")
    link = page.evaluate("() => location.hash")
    assert f"open={entry.id}" in link

    # a filter change redraws the cards; the opened one must stay open
    page.locator("#search").fill(entry.data["title"].split()[0])
    assert entry.id in shown_ids(page)
    assert page.locator(f"#entry-{entry.id} details.all-fields").evaluate("el => el.open")
    page.locator("#search").fill("")

    # closing it takes it out of the link again
    page.locator(f"#entry-{entry.id} details.all-fields > summary").click()
    page.wait_for_function("() => location.hash.indexOf('open=') === -1")
    page.locator(f"#entry-{entry.id} details.all-fields > summary").click()
    page.wait_for_function("() => location.hash.indexOf('open=') !== -1")
    other = context.new_page()
    other.goto(site_url + link)
    other.wait_for_selector("article.card")
    assert other.locator(f"#entry-{entry.id} details.all-fields").evaluate("el => el.open")
    assert other.locator("details.all-fields[open]").count() == 1
    snap(other, "page-07-opened-from-link")
    other.close()


def test_the_full_view_of_every_entry_shows_every_field_it_has(page):
    for entry in ENTRIES:
        card = page.locator(f"#entry-{entry.id}")
        card.locator("details.all-fields > summary").click()
        terms = card.locator("details.all-fields dt").all_inner_texts()
        for key, value in entry.data.items():
            assert key in terms, (entry.id, key)
            if isinstance(value, dict):
                for nested in value:
                    assert nested in terms, (entry.id, key, nested)
        text = card.locator("details.all-fields").inner_text()
        assert entry.data["hypothesis"][:60] in text and entry.data["claim_scope"][:60] in text
        if entry.body:
            assert entry.body[:50] in card.locator("pre.body").inner_text()
        # fields come in schema order, not alphabetical
        top = [term for term in terms if term in entry.data]
        assert top[:3] == ["id", "title", "research_area"], entry.id


def test_full_view_screens(page, snap):
    """Screens only: the full view of one agent-written and one human-drafted entry, top to bottom."""
    for entry_id in ("fe-2026-0001", "fe-2026-0007"):
        card = page.locator(f"#entry-{entry_id}")
        card.locator("details.all-fields > summary").click()
        card.scroll_into_view_if_needed()
        page.evaluate("(id) => document.getElementById(id).scrollIntoView({block: 'start'})", f"entry-{entry_id}")
        snap(page, f"page-08-all-fields-{entry_id}-top")
        page.evaluate("() => window.scrollBy(0, 640)")
        snap(page, f"page-08-all-fields-{entry_id}-next")
        page.evaluate("() => window.scrollBy(0, 640)")
        snap(page, f"page-08-all-fields-{entry_id}-last")


def test_each_card_shows_the_right_badges_quote_and_links(page):
    names = {"agent-written": "Agent-written", "unreviewed": "Unreviewed", "contested": "Contested", "superseded": "Superseded",
             "retry-welcome": "Retry welcome"}
    for entry in ENTRIES:
        card = page.locator(f"#entry-{entry.id}")
        expected = [names[badge] for badge in wikilib.badges(entry.data)]
        if entry.data["review"]["status"] == "reviewed":
            kinds = {reviewer["type"] for reviewer in entry.data["review"].get("reviewers", [])}
            expected.append("Reviewed by a person" if "human" in kinds else "Reviewed by an agent only")
        assert card.locator(".badge").all_inner_texts() == expected, entry.id
        assert card.locator("blockquote.quote").inner_text() == entry.data["source"]["quote"]
        assert card.locator("p.cite a").get_attribute("href") == entry.data["source"]["url"]
        assert card.locator("p.links a").get_attribute("href") == f"../entries/{entry.id}.md"
        note = entry.data["contributor"].get("note")
        assert card.locator(".contributor-note").count() == (1 if note else 0)
        # "Written by" must point at the note when there is one: a model draft filed under a person is not that person's writing yet
        assert ("see the note above" in card.locator(".meta").inner_text()) == bool(note), entry.id
        if note:
            assert card.locator(".contributor-note").inner_text() == note


def test_narrow_screens_get_one_column_and_no_sideways_scroll(context, site_url, snap):
    page = context.new_page()
    page.set_viewport_size({"width": 390, "height": 844})
    page.goto(site_url)
    page.wait_for_selector("article.card")
    assert page.evaluate("() => document.documentElement.scrollWidth <= window.innerWidth")
    assert page.evaluate("() => getComputedStyle(document.querySelector('aside')).position") == "static"
    panel = page.locator("aside").bounding_box()
    first = page.locator("article.card").first.bounding_box()
    assert first["y"] > panel["y"] + panel["height"] - 1          # results come below the filters, not beside them
    # on a phone the filter groups start closed, so the first result is not screens away
    assert page.locator("details.group[open]").count() == 0
    assert first["y"] < 844 * 1.5, first["y"]
    snap(page, "page-09-narrow-top")
    page.goto("about:blank")
    page.goto(site_url + "#f.method=sae")
    page.wait_for_selector("article.card")
    assert page.locator("details.group[open]").count() == 1          # a group with a filter in use stays open
    assert checkbox(page, "method", "sae").is_visible()
    page.locator("article.card").first.scroll_into_view_if_needed()
    snap(page, "page-09-narrow-first-card")
    page.close()


def test_dark_colour_scheme_is_dark_and_readable(context, site_url, snap):
    page = context.new_page()
    page.emulate_media(color_scheme="dark")
    page.goto(site_url)
    page.wait_for_selector("article.card")

    def brightness(selector, prop):
        rgb = page.evaluate(f"() => getComputedStyle(document.querySelector('{selector}')).{prop}")
        numbers = [float(part) for part in rgb[rgb.index("(") + 1: rgb.index(")")].split(",")[:3]]
        return sum(numbers) / 3

    assert brightness("body", "backgroundColor") < 60
    assert brightness("article.card", "backgroundColor") < 80
    assert brightness("h2.card-title", "color") > 180
    snap(page, "page-10-dark")
    page.locator("details.all-fields > summary").first.click()
    snap(page, "page-10-dark-all-fields")
    page.close()


def test_hostile_entry_text_is_shown_as_text_and_runs_nothing(context, tmp_path, snap):
    hostile = copy.deepcopy(ENTRIES[0].data)
    hostile["title"] = 'Probe <img src=x onerror="window.__pwned=1"> </script><script>window.__pwned=2</script> end'
    hostile["limitations"] = "<b>bold?</b> <a href=\"javascript:window.__pwned=3\">link</a>"
    hostile["source"] = dict(hostile["source"], title="<svg onload=window.__pwned=4>")
    entries_dir = tmp_path / "entries"
    entries_dir.mkdir()
    (entries_dir / f"{hostile['id']}.md").write_text(
        wikilib.dump_entry(hostile, "Body <script>window.__pwned=5</script>"), encoding="utf-8"
    )
    out = tmp_path / "site" / "index.html"
    build_site.build(entries_dir, out, None)
    page = context.new_page()
    dialogs = []
    page.on("dialog", lambda dialog: (dialogs.append(dialog.message), dialog.dismiss()))
    page.goto(out.as_uri())
    page.wait_for_selector("article.card")
    page.locator("details.all-fields > summary").click()
    assert page.evaluate("() => window.__pwned") is None and dialogs == []
    assert page.locator("h2.card-title").inner_text() == hostile["title"]
    assert page.locator("article.card img, article.card svg, article.card b, article.card script").count() == 0
    assert page.locator('article.card a[href^="javascript:"]').count() == 0
    snap(page, "page-11-hostile-text")
    page.close()


# ---- Datasette, in the same browser, served in process ---------------------


@pytest.fixture(scope="module")
def datasette_page(context, tmp_path_factory):
    datasette_app = pytest.importorskip("datasette.app")
    folder = tmp_path_factory.mktemp("datasette")
    db_path, metadata_path = folder / "wiki.db", folder / "metadata.yml"
    build_db.build(REPO_ROOT / "entries", db_path)
    build_db.write_metadata(metadata_path, "wiki")
    datasette = datasette_app.Datasette([str(db_path)], metadata=yaml.safe_load(metadata_path.read_text(encoding="utf-8")))

    loop = asyncio.new_event_loop()
    threading.Thread(target=loop.run_forever, daemon=True).start()
    asyncio.run_coroutine_threadsafe(datasette.invoke_startup(), loop).result(timeout=60)

    def serve(route, request):
        url = urlsplit(request.url)
        target = url.path + ("?" + url.query if url.query else "")
        response = asyncio.run_coroutine_threadsafe(datasette.client.get(target, follow_redirects=True), loop).result(timeout=60)
        route.fulfill(status=response.status_code, headers=dict(response.headers), body=response.content)

    page = context.new_page()
    page.set_viewport_size({"width": 1400, "height": 900})
    page.route("**/*", serve)          # Datasette writes some links with its own host name; serve them all
    yield page
    page.close()
    loop.call_soon_threadsafe(loop.stop)


def table_ids(page) -> list[str]:
    return page.locator("table.rows-and-columns tbody tr td.col-id").all_inner_texts()


def test_datasette_lists_every_entry_with_its_facets(datasette_page, snap):
    page = datasette_page
    page.goto("http://datasette.test/wiki/entries")
    snap(page, "datasette-01-entries")
    snap(page, "datasette-01-entries-full", full_page=True)
    assert f"{len(ENTRIES)} rows" in page.locator("h3.table-row-count, h3").first.inner_text()
    assert sorted(table_ids(page)) == [entry.id for entry in ENTRIES]
    facets = page.locator(".facet-results").inner_text()
    for name in ("failure_type", "badges", "method", "review_status", "contributor_type"):
        assert name in facets, name
    assert "Every column can be filtered" in page.locator("body").inner_text()


def test_datasette_facet_links_and_search_filter_in_the_browser(datasette_page, snap):
    page = datasette_page
    page.goto("http://datasette.test/wiki/entries")
    page.locator(".facet-results a", has_text="hypothesis_false").first.click()
    page.wait_for_load_state()
    expected = [e.id for e in ENTRIES if e.data["failure_type"] == "hypothesis_false"]
    assert sorted(table_ids(page)) == expected
    snap(page, "datasette-02-facet-clicked")

    page.goto("http://datasette.test/wiki/entries?method__arraycontains=sae")
    assert sorted(table_ids(page)) == [e.id for e in ENTRIES if "sae" in e.data["method"]]
    snap(page, "datasette-03-list-field-filter")

    page.goto("http://datasette.test/wiki/entries")
    page.locator('input[name="_search"]').fill("steganography")
    page.locator('input[name="_search"]').press("Enter")
    page.wait_for_load_state()
    assert sorted(table_ids(page)) == ["fe-2026-0010", "fe-2026-0011"]
    snap(page, "datasette-04-search")

    page.goto("http://datasette.test/wiki/entries?source_published__gte=2026-01-01&_sort=source_published")
    assert sorted(table_ids(page)) == [e.id for e in ENTRIES if e.data["source"]["published"] >= "2026-01-01"]


def test_datasette_shows_the_list_tables_and_a_single_entry(datasette_page, snap):
    page = datasette_page
    page.goto("http://datasette.test/wiki")
    snap(page, "datasette-05-database")
    body = page.locator("body").inner_text()
    for table in ("entries", "entry_models", "entry_method", "entry_reviewers", "entry_badges"):
        assert table in body, table
    page.goto("http://datasette.test/")
    snap(page, "datasette-06-home")
    assert "never judge people" in page.locator("body").inner_text()
    page.goto("http://datasette.test/wiki/entries/fe-2026-0001")
    assert BY_ID["fe-2026-0001"].data["title"] in page.locator("body").inner_text()
    snap(page, "datasette-07-one-entry")
    page.goto("http://datasette.test/wiki/entry_models?developer=unknown")
    assert "rows" in page.locator("h3").first.inner_text()

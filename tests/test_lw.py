import lw
from conftest import FAKE_HTML, FAKE_POST_ID, FAKE_QUOTE, FAKE_URL


def test_post_id_from_url_accepts_the_three_front_ends():
    assert lw.post_id_from_url(FAKE_URL) == FAKE_POST_ID
    assert lw.post_id_from_url(f"https://www.alignmentforum.org/posts/{FAKE_POST_ID}/x") == FAKE_POST_ID
    assert lw.post_id_from_url(f"https://www.greaterwrong.com/posts/{FAKE_POST_ID}") == FAKE_POST_ID


def test_post_id_from_url_rejects_other_sites():
    assert lw.post_id_from_url("https://example.com/posts/abc/def") is None
    assert lw.post_id_from_url("http://www.lesswrong.com/posts/abc/def") is None
    assert lw.post_id_from_url("") is None


def test_source_type_from_url():
    assert lw.source_type_from_url(FAKE_URL) == "lesswrong"
    assert lw.source_type_from_url("https://www.alignmentforum.org/posts/abc/x") == "alignment_forum"


def test_html_to_text_drops_scripts_and_keeps_block_breaks():
    text = lw.html_to_text(FAKE_HTML)
    assert "ignore()" not in text
    assert text.startswith("A test post\n")
    assert "refusal rates across seeds." in text  # &nbsp; became a plain space


def test_quote_check_is_verbatim_but_folds_typography():
    text = lw.html_to_text(FAKE_HTML)
    assert lw.quote_in_text(FAKE_QUOTE, text)
    assert lw.quote_in_text('It\'s a "null" result - nothing more.', text)  # curly quotes and em dash folded
    assert not lw.quote_in_text("the steering vector had a measurable effect", text)
    assert not lw.quote_in_text("The Steering Vector had no measurable effect", text)  # case must match
    assert not lw.quote_in_text("", text)


def test_fetch_post_reads_cache_and_reports_unreachable_when_missing():
    assert lw.fetch_post(FAKE_POST_ID)["title"] == "A test post"
    try:
        lw.fetch_post("NotCached000000001")
    except lw.SourceUnreachable:
        pass
    else:
        raise AssertionError("expected SourceUnreachable")


def test_source_bundle_gives_metadata_and_text():
    bundle = lw.source_bundle(FAKE_URL)
    assert bundle["authors"] == ["Test Author"]
    assert bundle["published"] == "2025-03-01"
    assert bundle["url_alignment_forum"] is None
    assert FAKE_QUOTE in bundle["text"]

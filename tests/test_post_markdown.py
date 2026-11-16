"""A post's HTML as Markdown for printing: the page's structure is kept, and so is every word."""
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "tools"))
import post_markdown  # noqa: E402

LABELS = {"hypothesis": "HYPOTHESIS", "result": "RESULT"}


def md(html):
    return post_markdown.convert(html)[0]


def test_headings_keep_their_levels_under_the_packs_own():
    assert md("<h1>Intro</h1><p>Text.</p><h2>Detail</h2>") == "### Intro\n\nText.\n\n#### Detail"
    assert md("<h2>Intro</h2><h3><strong>Detail</strong></h3>") == "### Intro\n\n#### Detail"


def test_lists_are_tight_and_nested_with_tabs_as_on_the_page():
    html = "<ul><li>one</li><li>two<ul><li>two-a</li><li>two-b</li></ul></li></ul><ol><li><p>first</p></li><li><p>second</p></li></ol>"
    assert md(html) == "- one\n- two\n\t- two-a\n\t- two-b\n\n1. first\n2. second"


def test_footnotes_become_markers_and_definitions():
    html = ('<p>A claim.<span class="footnote-reference" data-footnote-index="1"><sup><a href="#fn1">[1]</a></sup></span> More.</p>'
            '<ol class="footnote-section footnotes"><li class="footnote-item" data-footnote-index="1">'
            '<span class="footnote-back-link"><sup><strong><a href="#fnref1">^</a></strong></sup></span>'
            '<div class="footnote-content"><p>The note.</p></div></li></ol>')
    assert md(html) == "A claim.[^1] More.\n\n[^1]: The note."


def test_maths_is_the_pages_own_latex():
    html = ('<p>Above <span class="math-tex"><span class="mjpage"><span class="mjx-chtml"><span class="mjx-math" aria-label="&gt;10\\%">'
            '<span class="mjx-char">&gt;10%</span></span></span></span></span> of cases.</p>')
    assert md(html) == "Above $>10\\%$ of cases."


def test_a_figure_is_an_image_with_its_caption_and_a_table_is_a_table():
    assert md('<figure class="image"><img src="https://example.org/a.png"><figcaption>The curve.</figcaption></figure>') == (
        "![|450](https://example.org/a.png)  \n*The curve.*")
    assert md('<figure><img src="https://example.org/b.png"><figcaption><p></p></figcaption><figcaption><p><b>Figure 1: </b>Gap.</p></figcaption></figure>') == (
        "![|450](https://example.org/b.png)  \n*Figure 1: Gap.*")
    assert md('<figure class="table"><table><tr><td></td><th>Train</th></tr><tr><td>Probe</td><td>0.1</td></tr></table></figure>') == (
        "|  | Train |\n|---|---|\n| Probe | 0.1 |")


def test_code_is_fenced_emphasis_kept_and_link_addresses_dropped():
    assert md("<pre><code>a = 1\n\nb = 2</code></pre>") == "```\na = 1\nb = 2\n```"
    assert md('<p>See <a href="https://example.org">the <em>paper</em></a>, <strong>really</strong>.</p>') == "See the *paper*, **really**."
    assert md("<p>penalise <i>all </i>latents</p>") == "penalise *all* latents"          # a space inside the tag would break the emphasis


def test_the_markdown_holds_exactly_the_pages_words():
    html = ('<h2>Setup</h2><p>We <em>expected</em> transfer.<span class="footnote-reference" data-footnote-index="1"><sup><a>[1]</a></sup></span></p>'
            '<ol><li>step</li></ol><ol class="footnotes"><li class="footnote-item" data-footnote-index="1"><div class="footnote-content"><p>Note.</p></div></li></ol>')
    markdown, stream = post_markdown.convert(html)
    assert post_markdown.same_words(html, stream)
    assert not post_markdown.same_words(html + "<p>extra words</p>", stream)
    assert "".join(char for char, _ in stream) == "setupweexpectedtransfer1stepnote"       # the list number 1. is layout, not the post's word


def test_a_passage_is_marked_although_emphasis_and_a_footnote_marker_sit_inside_it():
    html = '<p>We <em>expected</em> the probe<span class="footnote-reference" data-footnote-index="1"><sup><a>[1]</a></sup></span> to transfer. It did not.</p>'
    markdown, stream = post_markdown.convert(html)
    notes = {"entries": {"fe-2026-0001": {"hypothesis": [{"snippet": "We expected the probe[1] to transfer."}], "result": [{"snippet": "not in the post"}]}}}
    marked, placed, missing = post_markdown.place_marks(markdown, stream, notes, LABELS, show_entry=False)
    assert marked == "**⟦HYPOTHESIS⟧** We *expected* the probe[^1] to transfer **⟦/⟧**. It did not."
    assert placed == {("fe-2026-0001", "hypothesis"): 1}
    assert missing == [("fe-2026-0001", "result", "not in the post")]


def test_a_mark_never_splits_emphasis_or_a_footnote_marker():
    html = '<p>Before <strong>bold claim</strong><span class="footnote-reference" data-footnote-index="2"><sup><a>[2]</a></sup></span> after.</p>'
    markdown, stream = post_markdown.convert(html)
    marked, _, _ = post_markdown.place_marks(markdown, stream, {"entries": {"fe-2026-0001": {"result": [{"snippet": "bold claim[2]"}]}}}, LABELS, show_entry=False)
    assert marked == "Before **⟦RESULT⟧** **bold claim**[^2] **⟦/⟧** after."

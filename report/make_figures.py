"""Make the figures and tables the report can use.

  python report/make_figures.py        (or: make report-figures)

Writes into report/figures/:
  architecture.png        one diagram of how entries get in, are checked, and are read
  browse-*.png, ask-*.png screenshots of the real page (taken here, in a headless browser)
  schema-fields.md        the table of filterable fields, generated from the schema's field catalogue

Needs Playwright (make demo-setup). Everything is generated from the repository
as it is now; nothing is drawn by hand except the architecture diagram's layout.
"""
from __future__ import annotations

import html
import os
import sys
from pathlib import Path

REPORT = Path(__file__).resolve().parent
REPO = REPORT.parent
FIGURES = REPORT / "figures"
sys.path.insert(0, str(REPO / "tools"))
sys.path.insert(0, str(REPO / "demo"))
if (REPO / ".cache" / "ms-playwright").exists():
    os.environ.setdefault("PLAYWRIGHT_BROWSERS_PATH", str(REPO / ".cache" / "ms-playwright"))

import build_demo  # noqa: E402
import build_site  # noqa: E402
import wikilib  # noqa: E402

W, H = 1500, 800
BOXES = {
    # id: (x, y, w, h, title, lines, style)
    "posts": (30, 60, 290, 110, "LessWrong / Alignment Forum", ["public write-ups of experiments", "that did not work"], "source"),
    "agent": (30, 250, 290, 110, "AI agent", ["contribute skill drafts an entry", "from a post (MCP: submit_entry)"], "actor"),
    "person": (30, 420, 290, 110, "Person", ["GitHub issue form", "(or edits a file directly)"], "actor"),
    "reviewer": (30, 610, 290, 110, "Reviewer: person or agent", ["review skill checks an entry", "against its post"], "actor"),
    "validator": (390, 320, 280, 150, "One validator on every path", ["schema and closed lists", "source link required", "quote (15 words or fewer) must be", "found in the fetched post"], "gate"),
    "pr": (770, 335, 200, 120, "Pull request", ["one branch per entry", "merge only if valid"], "gate"),
    "entries": (1075, 290, 300, 210, "entries/*.md in git", ["the source of truth", "trust fields set by the system:", "who wrote it (a person, or an", "agent and its model),", "review status, dates", "history of every change"], "store"),
    "page": (1075, 50, 190, 100, "Static web page", ["filter on every field", "badges on every card"], "reader"),
    "datasette": (1285, 50, 190, 100, "Datasette", ["table, facets, SQL,", "JSON"], "reader"),
    "mcp": (1075, 640, 190, 110, "MCP server and CLI", ["search, get, facets,", "fetch source"], "reader"),
    "ask": (1285, 640, 190, 110, "ask skill", ['"what has been tried,', "where did it go wrong,", 'what should I avoid?"'], "reader"),
}
ARROWS = [
    ("posts", "agent", "reads"), ("agent", "validator", ""), ("person", "validator", ""), ("validator", "pr", "passes"),
    ("pr", "entries", "merge"), ("reviewer", "validator", "review"), ("entries", "page", ""), ("entries", "datasette", ""),
    ("entries", "mcp", ""), ("mcp", "ask", ""),
]
STYLES = {
    "source": ("#eef3f8", "#5b7fa6"), "actor": ("#f4efe6", "#a07c3b"), "gate": ("#fdeeee", "#b4443c"),
    "store": ("#eaf5ee", "#3c7d55"), "reader": ("#f0edf8", "#6a56a8"),
}


def anchor(box, towards):
    x, y, w, h = box[:4]
    cx, cy = x + w / 2, y + h / 2
    tx, ty = towards[0] + towards[2] / 2, towards[1] + towards[3] / 2
    dx, dy = tx - cx, ty - cy
    if abs(dx) * h > abs(dy) * w:                      # leaves through the left or right side
        return (x + w if dx > 0 else x, cy + dy * (w / 2) / abs(dx) * 0.6)
    return (cx + dx * (h / 2) / abs(dy) * 0.6, y + h if dy > 0 else y)


def architecture_svg() -> str:
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-family="-apple-system, Helvetica, Arial, sans-serif">',
             '<defs><marker id="tip" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="9" markerHeight="9" orient="auto-start-reverse">'
             '<path d="M0,0 L10,5 L0,10 z" fill="#444"/></marker></defs>',
             f'<rect width="{W}" height="{H}" fill="#ffffff"/>']
    for label, x in (("WHO PUTS CONTENT IN", 30), ("WHAT EVERY CHANGE PASSES THROUGH", 390), ("WHERE IT LIVES, AND WHO READS IT", 1075)):
        parts.append(f'<text x="{x}" y="28" font-size="15" font-weight="700" fill="#666" letter-spacing="1">{label}</text>')
    labels = []
    for start, end, label in ARROWS:
        a, b = BOXES[start], BOXES[end]
        x1, y1 = anchor(a, b)
        x2, y2 = anchor(b, a)
        parts.append(f'<line x1="{x1:.0f}" y1="{y1:.0f}" x2="{x2:.0f}" y2="{y2:.0f}" stroke="#444" stroke-width="2" marker-end="url(#tip)"/>')
        if label:
            labels.append(f'<text x="{(x1 + x2) / 2:.0f}" y="{(y1 + y2) / 2 - 10:.0f}" font-size="14" fill="#444" text-anchor="middle" '
                          f'stroke="#ffffff" stroke-width="5" paint-order="stroke">{html.escape(label)}</text>')
    for x, y, w, h, title, lines, style in BOXES.values():
        fill, stroke = STYLES[style]
        parts.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="10" fill="{fill}" stroke="{stroke}" stroke-width="2"/>')
        parts.append(f'<text x="{x + 14}" y="{y + 28}" font-size="17" font-weight="700" fill="#1c1c1c">{html.escape(title)}</text>')
        for index, line in enumerate(lines):
            parts.append(f'<text x="{x + 14}" y="{y + 52 + index * 20}" font-size="14.5" fill="#333">{html.escape(line)}</text>')
    parts += labels                                         # after the boxes, so a label is never hidden behind one
    parts.append("</svg>")
    return "\n".join(parts)


def schema_table() -> str:
    entries = wikilib.load_entries(REPO / "entries")
    rows = ["| Field | Kind | Filter control | Values in use now |", "|---|---|---|---|"]
    for field in build_site.field_catalogue():
        values = sorted({wikilib._facet_key(v) for e in entries for v in (wikilib.badges(e.data) if field["path"] == "badges" else wikilib.get_values(e.data, field["path"]))})
        rows.append(f"| `{field['path']}` | {field['kind']} | {field['control']} | {len(values)} |")
    return ("# Filterable fields\n\nGenerated by `report/make_figures.py` from the field catalogue the browse page is built from. "
            "\"Values in use now\" counts distinct values across the entries at the time of generation.\n\n" + "\n".join(rows) + "\n")


def main() -> int:
    from playwright.sync_api import sync_playwright

    FIGURES.mkdir(parents=True, exist_ok=True)
    (FIGURES / "architecture.svg").write_text(architecture_svg(), encoding="utf-8")
    (FIGURES / "schema-fields.md").write_text(schema_table(), encoding="utf-8")
    site = FIGURES / "_site" / "index.html"
    build_site.build(REPO / "entries", site, None)
    with sync_playwright() as playwright:
        browser = build_demo.launch_browser(playwright)
        context = browser.new_context(viewport={"width": 1360, "height": 850}, device_scale_factor=2, color_scheme="light")
        page = context.new_page()
        page.set_content(f'<html><body style="margin:0">{architecture_svg()}</body></html>')
        page.set_viewport_size({"width": W, "height": H})
        page.screenshot(path=str(FIGURES / "architecture.png"))
        page.set_viewport_size({"width": 1360, "height": 850})

        page.goto(site.as_uri())
        page.wait_for_selector("article.card")
        page.screenshot(path=str(FIGURES / "browse-all-entries.png"))
        page.goto("about:blank")
        page.goto(site.as_uri() + "#f.failure_type=hypothesis_false&f.badges=retry-welcome")
        page.wait_for_selector("article.card")
        page.screenshot(path=str(FIGURES / "browse-filtered.png"))
        page.goto("about:blank")
        page.goto(site.as_uri() + "#open=fe-2026-0007")
        page.wait_for_selector("article.card")
        page.evaluate("() => document.getElementById('entry-fe-2026-0007').scrollIntoView({block: 'start'})")
        page.screenshot(path=str(FIGURES / "browse-full-entry.png"))
        browser.close()
    for name in sorted(path.name for path in FIGURES.iterdir() if path.is_file()):
        print("wrote report/figures/" + name)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

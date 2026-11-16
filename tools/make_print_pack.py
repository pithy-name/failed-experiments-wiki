"""Build printable review packs for the maintainer, in _print/ (git-ignored).

  python tools/make_print_pack.py        (or: make print-pack)

Writes:
  _print/posts/post-NN-<entry ids>.md   one post and its entries per file, for printing one at a time
  _print/1-human-review-pack.md   how to review an entry, the posts behind the wiki, and for each post the
                                  entries drawn from it beside the post's own text, with the passage behind
                                  each field marked in place
  _print/2-schema.md              the entry schema as tables (also written to schema/SCHEMA.md, which is tracked)
  _print/3-skills-and-tools.md    the three skills in full and the six MCP tools

The review pack contains full post texts, so it is for the maintainer's own reading and is never
committed (see .gitignore and the copyright rule in the PRD). Post texts come from the local cache
(.cache/lw/text/). The marked passages come from _print/annotations/<post id>.json, written by a model
that was asked to copy each passage exactly; every passage is checked here by exact string search and
the ones that are not found are listed, not shown.
"""
from __future__ import annotations

import ast
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import lw  # noqa: E402
import post_markdown  # noqa: E402
import wikilib  # noqa: E402

REPO = wikilib.REPO_ROOT
OUT = REPO / "_print"
TEXT_DIR = REPO / ".cache" / "lw" / "text"
FIELD_LABELS = [
    ("hypothesis", "HYPOTHESIS"), ("claim_scope", "SCOPE"), ("method", "METHOD"), ("models", "MODELS"), ("benchmarks", "BENCHMARKS"),
    ("result", "RESULT"), ("failure_type", "FAILURE TYPE"), ("confidence_true_negative", "CONFIDENCE"), ("checks_done", "CHECKS"),
    ("limitations", "LIMITATIONS"), ("revival_conditions", "REVIVAL"), ("retry_welcome", "RETRY"), ("quote", "QUOTE"),
]
LABEL = dict(FIELD_LABELS)

GUIDE = """## How to review one entry, step by step

You need a pen. Each post below comes with the entries drawn from it, and then the post's own text with the
passage behind each field marked where it sits, like this: ***⟦HYPOTHESIS⟧*** …the passage… ***⟦/HYPOTHESIS⟧***.
When a post has several entries, the mark also says which one: ***⟦HYPOTHESIS · 0010⟧*** is entry fe-2026-0010.

1. **Read the post's text first, start to finish,** without looking at the entry. Ignore the marks on this pass.
   Ask yourself: what did they try, what did they expect, what happened, and how sure are they?
2. **Read the entry's checklist.** For each field, find its mark in the post text and read the sentence around it.
3. **Tick or cross each box.** A field is right when the post says it. It is wrong when the post says something
   else, says less (the entry overreaches), or does not say it at all.
4. **Check these harder, in this order:**
   1. **Quote:** is it in the post word for word, 15 words or fewer, and does it state the negative result?
   2. **Claim scope:** does it say exactly what was tested and nothing more? An entry that reads as "X never
      works" when the post tested one setup is wrong.
   3. **Hypothesis:** does the post state this expectation, or did the entry invent one?
   4. **Result direction and numbers:** does every number appear in the post?
   5. **Failure type and confidence:** does the post give that cause, and that much certainty? `hypothesis_false`
      with `high` confidence needs strong support.
   6. **Models and benchmarks:** each one named in the post; nothing added from general knowledge.
   7. **Tone:** it describes the experiment and says nothing about the authors' skill or effort.
5. **Read the box "Flagged before you start".** A model listed there every claim it could not find in the post.
   Each one is either a real error in the entry or a passage the model missed; you decide which.
6. **Decide:**
   - every box ticked: **reviewed**;
   - any box crossed: **contested**, and write which field and what the post says instead;
   - write the corrected value in the margin if you want the entry fixed.
7. **Record it** (or hand the marked-up pages back and it will be recorded for you):
   - a reference ("gold") entry, IDs 0001 to 0005: correct `evals/gold/<id>.md`, set `gold_status: verified`,
     then `make sync-gold HANDLE=<your handle>`;
   - any other entry: `.venv/bin/python tools/cli.py review <id> reviewed --human --notes "…"` (or `contested`).

**What the marks are, and are not.** A model placed them after the entries were written, by searching the post
for the passage each field most plausibly rests on. They are a reading aid, not proof: a mark shows where to
look, and you judge whether the passage really supports the field. Passages that could not be found in the post's
own words were dropped and are counted under each post. The post is printed from its own page: headings, lists,
footnotes, maths and figures as they are there (figures load from the web when you print). When the same words occur more than once in a post, the mark
sits on the first occurrence, which may not be the one the field rests on (rare: a handful of passages in the whole pack).

**Date posted** is `source.published` in each entry and is shown at the top of each post below.
"""


_STARTS_A_BLOCK = re.compile(r"^\s*(?:[-*+] |\d+[.)] |#|\||>|```|---\s*$)")


def reflow(markdown: str) -> str:
    """Join lines that were wrapped by hand, so each paragraph or list item is one line and the printer wraps it.

    Some Markdown viewers print a single line break as a line break, which leaves hand-wrapped text ragged and long.
    Fenced code, tables, headings and quotes are left as they are.
    """
    out, fenced = [], False
    for line in markdown.split("\n"):
        stripped = line.strip()
        if stripped.startswith("```"):
            fenced = not fenced
            out.append(line)
            continue
        previous = out[-1].strip() if out else ""
        continues = (not fenced and stripped and previous and not _STARTS_A_BLOCK.match(line)
                     and not previous.startswith(("```", "#", "|", ">")) and previous != "---")
        if continues:
            out[-1] = out[-1].rstrip() + " " + stripped
        else:
            out.append(line)
    return "\n".join(out)


def front_matter_as_list(text: str) -> str:
    """A skill file's YAML header as a short list, so it prints as text and not as a rule and a run-on line."""
    if not text.startswith("---\n") or "\n---" not in text[4:]:
        return text
    header, body = text[4:].split("\n---", 1)
    items = []
    for line in header.split("\n"):
        key, colon, value = line.partition(":")
        if colon and key.strip() and not line.startswith((" ", "\t")):
            items.append(f"- **{key.strip()}:** {value.strip()}")
        elif items and line.strip():
            items[-1] += " " + line.strip()
    return "\n".join(items) + "\n" + body.lstrip("-")


def docstring_as_prose(doc: str) -> str:
    """A tool's docstring as paragraphs and a list of its arguments, not as a fixed-width block that cannot wrap."""
    logical: list[str] = []
    for line in doc.split("\n"):
        if not line.strip():
            logical.append("")
        elif line.startswith((" ", "\t")) and logical and logical[-1]:
            logical[-1] += " " + line.strip()
        else:
            logical.append(line.strip())
    out = []
    for line in logical:
        argument = re.match(r"^(\w+): (.+)$", line)
        line = line.replace("<", "\\<")
        if argument:
            out.append(f"- **{argument.group(1)}:** " + argument.group(2).replace("<", "\\<"))
        elif line:
            out += ["", line, ""]
    return re.sub(r"\n{3,}", "\n\n", "\n".join(out)).strip()


def load_json(path: Path, default):
    if not path.exists():
        return default
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def cell(value) -> str:
    """One table cell: readable, on one line."""
    if isinstance(value, bool):
        text = "yes" if value else "no"
    elif isinstance(value, list):
        if value and isinstance(value[0], dict):
            text = "; ".join(", ".join(f"{k}: {v}" for k, v in item.items()) for item in value)
        else:
            text = ", ".join(str(item) for item in value)
    elif isinstance(value, dict):
        text = ", ".join(f"{k}: {v}" for k, v in value.items())
    else:
        text = "" if value is None else str(value)
    return " ".join(text.split()).replace("|", "\\|")


def entry_rows(data: dict) -> list[tuple[str, str, str]]:
    """(field, value, annotation key) for the review table, in reading order."""
    source, result = data.get("source") or {}, data.get("result") or {}
    numbers = ", ".join(f"{key} {result[key]}" for key in ("effect_size", "ci_low", "ci_high", "n") if key in result)
    rows = [
        ("title", data.get("title"), ""),
        ("research_area", data.get("research_area"), ""),
        ("hypothesis", data.get("hypothesis"), "hypothesis"),
        ("claim_scope", data.get("claim_scope"), "claim_scope"),
        ("method", data.get("method"), "method"),
        ("models", data.get("models"), "models"),
        ("benchmarks", data.get("benchmarks"), "benchmarks"),
        ("result.direction", result.get("direction"), "result"),
        ("result numbers", numbers, "result"),
        ("failure_type", data.get("failure_type"), "failure_type"),
        ("confidence_true_negative", data.get("confidence_true_negative"), "confidence_true_negative"),
        ("checks_done", data.get("checks_done"), "checks_done"),
        ("limitations", data.get("limitations"), "limitations"),
        ("revival_conditions", data.get("revival_conditions"), "revival_conditions"),
        ("retry_welcome", data.get("retry_welcome"), "retry_welcome"),
        ("evidence_level", data.get("evidence_level"), ""),
        ("source.quote", source.get("quote"), "quote"),
        ("source.section", source.get("section"), ""),
        ("source.published (date posted)", source.get("published"), ""),
        ("source.authors", source.get("authors"), ""),
        ("info_hazard", data.get("info_hazard"), ""),
    ]
    return [(name, cell(value), key) for name, value, key in rows if value not in (None, "", [])]


def annotate(text: str, annotations: dict, show_entry: bool = True) -> tuple[str, dict, list]:
    """The post text with a mark around every passage found by exact search.

    Returns the marked text, how many passages were placed per (entry, field), and the passages not found.
    """
    spans, placed, missing = {}, {}, []
    for entry_id, fields in (annotations.get("entries") or {}).items():
        short = entry_id[-4:]
        for field, items in (fields or {}).items():
            for item in items or []:
                snippet = (item or {}).get("snippet") or ""
                start = text.find(snippet) if snippet else -1
                if start < 0:
                    missing.append((entry_id, field, snippet))
                    continue
                # several fields, or several entries, often rest on the same passage: one mark, all its labels
                spans.setdefault((start, start + len(snippet)), {}).setdefault(short, []).append(LABEL.get(field, field.upper()))
                placed[(entry_id, field)] = placed.get((entry_id, field), 0) + 1
    inserts = []
    for (start, end), by_entry in spans.items():
        label = " | ".join(", ".join(dict.fromkeys(names)) + (f" · {short}" if show_entry else "") for short, names in sorted(by_entry.items()))
        inserts.append((start, 1, f"***⟦{label}⟧*** "))
        inserts.append((end, 0, f" ***⟦/{label}⟧***"))
    for position, _, mark in sorted(inserts, key=lambda item: (-item[0], item[1])):
        text = text[:position] + mark + text[position:]
    return text, placed, missing


_MARK = re.compile(r"\*\*\*⟦[^⟧/][^⟧]*⟧\*\*\* ?| ?\*\*\*⟦/[^⟧]*⟧\*\*\*")


def post_structure(html: str) -> tuple[list, set, list, list]:
    """The post's headings, one-line list items, tables and code blocks, spelled as its plain text spells them."""
    def plain(fragment):
        return lw.html_to_text(fragment)

    def one_line(value):
        return bool(value) and "\n" not in value

    headings = [(int(level), plain(inner)) for level, inner in re.findall(r"<h([1-6])[^>]*>(.*?)</h\1>", html or "", flags=re.S)]
    items = {plain(inner) for inner in re.findall(r"<li[^>]*>(.*?)</li>", html or "", flags=re.S)}
    tables = []
    for table in re.findall(r"<table.*?</table>", html or "", flags=re.S):
        rows = [[plain(inner) for inner in re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", row, flags=re.S)] for row in re.findall(r"<tr.*?</tr>", table, flags=re.S)]
        rows = [row for row in rows if any(row)]
        if rows and all("\n" not in value for row in rows for value in row):    # a many-line cell: leave the table as text
            tables.append(rows)
    code = [[line for line in plain(inner).split("\n") if line.strip()] for inner in re.findall(r"<pre[^>]*>(.*?)</pre>", html or "", flags=re.S)]
    return ([(level, value) for level, value in headings if one_line(value)], {value for value in items if one_line(value)}, tables,
            [lines for lines in code if lines])


def shape_post(marked: str, html: str) -> str:
    """The marked plain text as Markdown with the post's own headings, lists and tables, so it prints compactly.

    Only layout changes: a line that is a heading, a list item or a table cell in the post's HTML is printed as one.
    Anything that cannot be matched exactly is left as a paragraph. The words are never changed.
    """
    headings, items, tables, code = post_structure(html)
    top = min((level for level, _ in headings), default=1)
    lines = marked.split("\n")
    if "----" in lines[:12]:                                   # the cache's own header repeats what is printed above the entries
        cut = lines.index("----")
        if not any("⟦" in line for line in lines[:cut]):
            lines = lines[cut + 1:]
    blocks = [line.strip() for line in lines if line.strip()]
    raw = [_MARK.sub("", block).strip() for block in blocks]
    out, index, next_heading = [], 0, 0
    while index < len(blocks):
        table = next((rows for rows in tables
                      if raw[index:index + sum(1 for row in rows for value in row if value)] == [value for row in rows for value in row if value]), None)
        if table:
            width, cursor, rendered = max(map(len, table)), index, []
            for number, row in enumerate(table):
                cells = []
                for value in row + [""] * (width - len(row)):                # an empty cell has no line in the plain text
                    cells.append(blocks[cursor].replace("|", "\\|") if value else "")
                    cursor += 1 if value else 0
                rendered.append("| " + " | ".join(cells) + " |")
                if number == 0:
                    rendered.append("|" + "---|" * width)
            out.append(("table", "\n".join(rendered)))
            tables.remove(table)
            index = cursor
            continue
        block = next((lines for lines in code if raw[index:index + len(lines)] == lines), None)
        if block:
            out.append(("code", "```\n" + "\n".join(blocks[index:index + len(block)]) + "\n```"))
            code.remove(block)
            index += len(block)
            continue
        ahead = next((offset for offset in range(3) if next_heading + offset < len(headings) and headings[next_heading + offset][1] == raw[index]), None)
        if ahead is not None:
            level = headings[next_heading + ahead][0]
            next_heading += ahead + 1
            out.append(("heading", "#" * min(6, 3 + level - top) + " " + blocks[index]))
        elif raw[index] in items:
            out.append(("item", "- " + blocks[index]))
        else:
            out.append(("text", blocks[index]))
        index += 1
    text = ""
    for position, (kind, block) in enumerate(out):
        joiner = "" if position == 0 else ("\n" if kind == "item" and out[position - 1][0] == "item" else "\n\n")
        text += joiner + block
    plain = "\n".join(lines).strip()
    return text if post_words(text) == post_words(plain) else plain          # layout only: if a word moved or went missing, print it unshaped


def post_words(text: str) -> list[str]:
    """The words of a printed post, without the marks and the layout characters around them."""
    return re.findall(r"\w+", re.sub(r"\*\*\*⟦[^⟧]*⟧\*\*\*", " ", text))


def model_names(models) -> str:
    """Models on one line: the name, what the entry states about it, and a note when the rest is unknown."""
    parts = []
    for model in models or []:
        known = [f"{key} {value}" for key, value in model.items() if key != "name" and value not in (None, "", "unknown")]
        unknown = any(value == "unknown" for key, value in model.items() if key != "name")
        detail = "; ".join(filter(None, [", ".join(known), "rest unknown" if unknown and known else ("all else unknown" if unknown else "")]))
        parts.append(str(model.get("name")) + (f" ({detail})" if detail else ""))
    return "; ".join(parts)


def entry_checklist(entry, placed: dict) -> list[str]:
    """One entry as tick boxes: long fields one per line, short ones together, so it prints in a fraction of a table's space."""
    long_rows, short_rows = [], []
    for name, value, key in entry_rows(entry.data):
        if name == "models":
            value = cell(model_names(entry.data.get("models")))
        unmarked = " *(no mark in the post)*" if key and not placed.get((entry.id, key)) else ""
        if len(value) > 70:
            long_rows.append(f"- ☐ **{name}:** {value}{unmarked}")
        else:
            short_rows.append(f"☐ **{name}:** {value}{unmarked}")
    return long_rows + ["", " · ".join(short_rows)]


def footnotes_with_the_post(body: str) -> str:
    """Footnotes as plain numbered text under the post. A Markdown viewer moves real footnotes to the end of the whole file,
    which in a pack of ten posts is a hundred pages from where they are cited."""
    lines, seen = [], False
    for line in body.split("\n"):
        definition = re.match(r"^\[\^(\d+)\]: (.*)$", line)
        if definition:
            if not seen:
                lines += ["#### Footnotes", ""]
                seen = True
            line = f"{definition.group(1)}. {definition.group(2)}"
        lines.append(line)
    return re.sub(r"\[\^(\d+)\]", r"<sup>[\1]</sup>", "\n".join(lines))


def post_section(number: int, post_id: str, entries: list, audit: dict | None) -> tuple[str, dict]:
    first = entries[0].data["source"]
    text_path = TEXT_DIR / f"{post_id}.txt"
    annotations = load_json(OUT / "annotations" / f"{post_id}.json", {})
    lines = [f"\n\n---\n\n# Post {number}: {first['title']}", ""]
    lines += [
        f"- **Link:** {first['url']}" + (f" (also {first['crosspost_url']})" if first.get("crosspost_url") else ""),
        f"- **Authors:** {', '.join(first['authors'])}",
        f"- **Date posted:** {first['published']}",
        f"- **Entries drawn from it:** {', '.join(entry.id for entry in entries)}",
    ]
    if audit is not None:
        unsupported = audit.get("unsupported_fields") or []
        lines.append("- **Your qualification rule (the post supports every required field):** "
                     + ("met, by the seeding audit" if not unsupported else "NOT met. The audit says the post does not state: " + ", ".join(unsupported)))
    stats = {"placed": 0, "missing": 0, "flagged": 0}
    if not text_path.exists():
        lines += ["", "> The post text is not in the local cache, so this post could not be printed. Run "
                      f"`.venv/bin/python tools/cli.py fetch-source {first['url']} --save` and rebuild."]
        return "\n".join(lines), stats
    cached = load_json(REPO / ".cache" / "lw" / "posts" / f"{post_id}.json", {})
    html = ((cached.get("contents") or {}).get("html") if isinstance(cached, dict) else "") or ""
    body = None
    if html:                                                   # the page's own HTML: headings, lists, footnotes, maths, figures
        markdown, stream = post_markdown.convert(html)
        if post_markdown.same_words(html, stream):             # every word of the page, in order, and nothing else
            body, placed, missing = post_markdown.place_marks(markdown, stream, annotations, LABEL, show_entry=len(entries) > 1)
    if body is None:                                           # no HTML in the cache, or a word would differ: the plain text
        marked, placed, missing = annotate(text_path.read_text(encoding="utf-8"), annotations, show_entry=len(entries) > 1)
        body = shape_post(marked, html)
        print(f"  post {number}: printed from the plain text (the HTML was missing or did not convert word for word)")
    stats["placed"], stats["missing"] = sum(placed.values()), len(missing)
    lines += ["", "## Entries"]

    for entry in entries:
        data = entry.data
        who = data.get("contributor") or {}
        review = data.get("review") or {}
        lines += ["", f"### Entry {entry.id}", "",
                  f"Written by: {who.get('type')}" + (f" ({who.get('agent_model')}, {who.get('tool')})" if who.get("agent_model") else "")
                  + f" · Review status: {review.get('status')}" + (f" · {who['note']}" if who.get("note") else ""), ""]
        lines += entry_checklist(entry, placed)
        if entry.body:
            lines += ["", "☐ **The entry's notes (its free text):** " + " ".join(entry.body.split())]
        flagged = (annotations.get("not_in_post") or {}).get(entry.id) or {}
        stats["flagged"] += len(flagged)
        lines += ["", "**Flagged before you start** (a model could not find these in the post; each is an error in the entry or a passage it missed):", ""]
        lines += [f"- ☐ `{field}`: {' '.join(str(reason).split())}" for field, reason in flagged.items()] or ["- Nothing flagged."]
        lines += ["", "**Decision:** ☐ reviewed ☐ contested (fields: ______________________) &nbsp; **Date:** __________"]
    if missing:
        lines += ["", f"*{len(missing)} passage(s) proposed for marking were not found by exact search and are not shown: "
                      + "; ".join(sorted({f"{entry_id[-4:]} {field}" for entry_id, field, _ in missing})) + ".*"]
    if not annotations:
        lines += ["", "*No marks: the passages for this post have not been located yet.*"]
    lines += ["", "## The post's text, marked", "", footnotes_with_the_post(body)]
    return "\n".join(lines), stats


def review_pack() -> str:
    entries = wikilib.load_entries(REPO / "entries")
    by_post: dict[str, list] = {}
    for entry in entries:
        by_post.setdefault(lw.post_id_from_url(entry.data["source"]["url"]), []).append(entry)
    audits = {row["post_id"]: row for row in load_json(REPO / "scouting" / "field_audit" / "summary.json", [])}

    out = ["# Human review pack: the failed-experiments wiki", "",
           "Printed for the maintainer's own review. It holds full post texts, so it stays out of the repository.", "",
           "**What is in here:** how to review an entry; the list of posts behind the wiki; then each post with its entries "
           "and its marked text; then the posts that were judged genuine failure write-ups and left out, with the reason.", "",
           "**Print this file.** Posts 1 to 5 carry the reference entries to verify; post 8 is the shortest, for the single human review.", "",
           reflow(GUIDE), "", "## The posts behind the wiki", ""]
    sections, totals = [], {"placed": 0, "missing": 0, "flagged": 0}
    for number, (post_id, group) in enumerate(by_post.items(), start=1):
        source = group[0].data["source"]
        unsupported = (audits.get(post_id) or {}).get("unsupported_fields")
        rule = "not audited" if post_id not in audits else ("meets your rule" if not unsupported else "**does not meet your rule**: lacks " + ", ".join(unsupported))
        out.append(f"{number}. **{cell(source['title'])}.** {cell(source['authors'])}, posted {source['published']}. "
                   f"Entries {', '.join(entry.id[-4:] for entry in group)}; {rule}. {source['url']}")
        section, stats = post_section(number, post_id, group, audits.get(post_id))
        sections.append(re.sub(r"\[\^(\d+)\]", rf"[^{number}-\1]", section))      # ten posts in one file: keep their footnotes apart
        # the same section as its own file, so one post can be printed at a time
        (OUT / "posts").mkdir(parents=True, exist_ok=True)
        (OUT / "posts" / f"post-{number:02d}-{'-'.join(entry.id[-4:] for entry in group)}.md").write_text(
            compact(section.replace("\n\n---\n\n", "", 1).lstrip()) + "\n", encoding="utf-8")
        for key in totals:
            totals[key] += stats[key]
    (OUT / "posts" / "post-00-how-to-review.md").write_text(compact("# How to review an entry\n\n" + "\n".join(out[8:])) + "\n", encoding="utf-8")    # the guide and the list, to print once
    out += ["", f"Marks placed across all posts: {totals['placed']}. Proposed passages not found and dropped: {totals['missing']}. "
                f"Claims flagged as not found in a post: {totals['flagged']}."]
    out += sections

    used = set(by_post)
    left_out = [row for row in audits.values() if row["post_id"] not in used]
    out += ["\n\n---\n\n# Posts judged genuine failure write-ups and left out", "",
            "A small model judged each of these a genuine write-up of a failed experiment. A stronger model then checked "
            "whether the post itself states every required field, and found it does not. They are not in the wiki. "
            "If the rule is relaxed (for example, by letting an entry say \"the post states no expectation\"), these are the candidates.", "",
            ]
    for row in sorted(left_out, key=lambda item: (len(item.get("unsupported_fields") or []), item["title"])):
        out.append(f"- **{cell(row['title'])}.** Does not state: {', '.join(row.get('unsupported_fields') or []) or 'see the audit notes'}. "
                   f"https://www.lesswrong.com/posts/{row['post_id']}")
    return "\n".join(out) + "\n"


def schema_rows(node: dict, prefix: str = "", required: bool = True) -> list[list[str]]:
    rows = []
    needed = set(node.get("required") or [])
    for name, spec in (node.get("properties") or {}).items():
        path = f"{prefix}{name}"
        kind = spec.get("type") or ("enum" if "enum" in spec else "")
        inner = spec.get("items") if kind == "array" else None
        if "enum" in spec:
            kind, allowed = "one of", ", ".join(f"`{value}`" for value in spec["enum"])
        elif inner and "enum" in inner:
            kind, allowed = "list, each one of", ", ".join(f"`{value}`" for value in inner["enum"])
        elif inner and inner.get("type") == "object":
            kind, allowed = "list of objects", ""
        elif inner:
            kind, allowed = f"list of {inner.get('type', 'values')}", ""
        else:
            allowed = spec.get("pattern") and f"pattern `{spec['pattern']}`" or spec.get("format") or ""
        if spec.get("maxLength"):
            allowed = (allowed + "; " if allowed else "") + f"at most {spec['maxLength']} characters"
        must = "yes" if (name in needed and required) else ("if its parent is present" if name in needed else "")
        rows.append([f"`{path}`", kind, must, allowed, " ".join(str(spec.get("description", "")).split())])
        if kind == "object" or spec.get("properties"):
            rows += schema_rows(spec, path + ".", required and name in needed)
        if inner and inner.get("type") == "object":
            rows += schema_rows(inner, path + "[].", False)
    return rows


def schema_markdown() -> str:
    schema = load_json(REPO / "schema" / "entry.schema.json", {})
    lines = ["# Entry schema", "",
             "Generated from `schema/entry.schema.json` by `tools/make_print_pack.py`. The JSON file is the one the validator uses; "
             "this is the same content laid out for reading.", "",
             "An entry is a Markdown file, `entries/fe-YYYY-NNNN.md`, with these fields in its YAML front matter and optional free text below.", "",
             "| Field | Type | Required | Allowed values | Notes |", "|---|---|---|---|---|"]
    lines += ["| " + " | ".join(value.replace("|", "\\|") for value in row) + " |" for row in schema_rows(schema)]
    lines += ["", "## Rules the validator adds on top of the schema", "",
              "- `source.quote` is 15 words or fewer and must be found, word for word, in the text of the post at `source.url`.",
              "- `id` must match the file name, and no two entries share an ID.",
              "- An entry marked `reviewed` must name at least one reviewer.",
              "- An agent-written entry must name its model.",
              "- `dates.updated` is not before `dates.created`; an interval's low end is not above its high end; an entry cannot be related to itself.",
              "", "## Badges (derived, never stored)", "",
              "| Badge | Shown when |", "|---|---|",
              "| agent-written | `contributor.type` is `agent` |",
              "| unreviewed | `review.status` is `unreviewed` |",
              "| contested | `review.status` is `contested` |",
              "| superseded | `review.status` is `superseded` |",
              "| retry-welcome | `retry_welcome` is true |",
              "", "The browse page also shows \"Reviewed by a person\" or \"Reviewed by an agent only\" on reviewed entries."]
    return "\n".join(lines) + "\n"


def tools_markdown() -> str:
    server = (REPO / "plugin" / "mcp" / "server.py").read_text(encoding="utf-8")
    lines = ["# The plugin: three skills and six tools", "",
             "**Skills** are instructions a model follows. They live in `plugin/skills/<name>/SKILL.md` and are printed in full below.", "",
             "**Tools** are functions the model calls through the plugin's MCP server (a local program, `plugin/mcp/server.py`). "
             "The same six are on the command line as `tools/cli.py`.", "",
             "| Tool | Reads or writes | What it is for |", "|---|---|---|",
             "| `search_entries` | reads | Find entries by words and by filters on any field |",
             "| `get_entry` | reads | One entry in full |",
             "| `list_facets` | reads | Every filterable field and the values in use |",
             "| `fetch_source` | reads | A post's title, authors, date and text, for writing or reviewing an entry |",
             "| `submit_entry` | writes | Validate a new entry and commit it on its own branch (a pull request when there is a remote) |",
             "| `review_entry` | writes | Record a review of an entry on its own branch |",
             "", "## The six tools, as the model sees them", ""]
    for node in ast.parse(server).body:
        if isinstance(node, ast.FunctionDef) and any(isinstance(d, ast.Attribute) and d.attr == "tool" for d in node.decorator_list):
            arguments = ", ".join(argument.arg for argument in node.args.args)
            lines += [f"### `{node.name}({arguments})`", "", docstring_as_prose(ast.get_docstring(node) or ""), ""]
    for name in ("ask", "contribute", "review"):
        text = (REPO / "plugin" / "skills" / name / "SKILL.md").read_text(encoding="utf-8")
        lines += ["\n---\n", f"# Skill file: `plugin/skills/{name}/SKILL.md`", "", reflow(front_matter_as_list(text)).strip(), ""]
    return "\n".join(lines) + "\n"


def compact(text: str) -> str:
    """Only the blank lines Markdown needs: one between paragraphs and blocks, one before a --- rule (without it the line
    above would become a heading), none after a heading or a rule, and never two in a row. Code blocks are left alone."""
    out, fenced = [], False
    for line in text.strip("\n").split("\n"):
        if line.strip().startswith("```"):
            fenced = not fenced
        if not fenced and not line.strip():
            if not out or not out[-1].strip() or out[-1].startswith("#") or out[-1].strip() == "---":
                continue                                           # a second blank, or one after a heading or a rule
            out.append("")
            continue
        if not fenced and line.startswith("#") and out and not out[-1].strip():
            out.pop()                                              # no blank before a heading
        out.append(line)
    return "\n".join(out).rstrip("\n")


def main() -> int:
    OUT.mkdir(exist_ok=True)
    outputs = {
        OUT / "1-human-review-pack.md": compact(review_pack()) + "\n",
        OUT / "2-schema.md": compact(schema_markdown()) + "\n",
        OUT / "3-skills-and-tools.md": compact(tools_markdown()) + "\n",
        REPO / "schema" / "SCHEMA.md": schema_markdown(),
    }
    for path, text in outputs.items():
        path.write_text(text, encoding="utf-8")
        print(f"wrote {path.relative_to(REPO)}  ({len(text.split()):,} words)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

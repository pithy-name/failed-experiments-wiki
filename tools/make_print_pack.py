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
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import lw  # noqa: E402
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
passage behind each field marked where it sits, like this: **⟦HYPOTHESIS · 0001⟧** …the passage… **⟦/⟧**.
The number is the last four digits of the entry ID, so a post with several entries shows which entry a mark belongs to.

1. **Read the post's text first, start to finish,** without looking at the entry. Ignore the marks on this pass.
   Ask yourself: what did they try, what did they expect, what happened, and how sure are they?
2. **Read the entry's table.** For each row, find its mark in the post text and read the sentence around it.
3. **Tick or cross each row.** A row is right when the post says it. It is wrong when the post says something
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
   - every row ticked: **reviewed**;
   - any row crossed: **contested**, and write which field and what the post says instead;
   - write the corrected value beside the row if you want the entry fixed.
7. **Record it** (or hand the marked-up pages back and it will be recorded for you):
   - a reference ("gold") entry, IDs 0001 to 0005: correct `evals/gold/<id>.md`, set `gold_status: verified`,
     then `make sync-gold HANDLE=<your handle>`;
   - any other entry: `.venv/bin/python tools/cli.py review <id> reviewed --human --notes "…"` (or `contested`).

**What the marks are, and are not.** A model placed them after the entries were written, by searching the post
for the passage each field most plausibly rests on. They are a reading aid, not proof: a mark shows where to
look, and you judge whether the passage really supports the field. Passages that could not be found by exact
search were dropped and are counted under each post.

**Date posted** is `source.published` in each entry and is shown at the top of each post below.
"""


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


def annotate(text: str, annotations: dict) -> tuple[str, dict, list]:
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
        label = " | ".join(f"{', '.join(dict.fromkeys(names))} · {short}" for short, names in sorted(by_entry.items()))
        inserts.append((start, 1, f"**⟦{label}⟧** "))
        inserts.append((end, 0, " **⟦/⟧**"))
    for position, _, mark in sorted(inserts, key=lambda item: (-item[0], item[1])):
        text = text[:position] + mark + text[position:]
    return text, placed, missing


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
    marked, placed, missing = annotate(text_path.read_text(encoding="utf-8"), annotations)
    stats["placed"], stats["missing"] = sum(placed.values()), len(missing)

    for entry in entries:
        data = entry.data
        who = data.get("contributor") or {}
        review = data.get("review") or {}
        lines += ["", f"## Entry {entry.id}", "",
                  f"Written by: {who.get('type')}" + (f" ({who.get('agent_model')}, {who.get('tool')})" if who.get("agent_model") else "")
                  + f" · Review status: {review.get('status')}" + (f" · {who['note']}" if who.get("note") else ""), "",
                  "| Field | The entry says | Marks in the post | Right? | Your correction |", "|---|---|---|---|---|"]
        for name, value, key in entry_rows(data):
            count = placed.get((entry.id, key), 0) if key else None
            marks = "" if count is None else (f"{count} × ⟦{LABEL[key]} · {entry.id[-4:]}⟧" if count else "none placed")
            lines.append(f"| `{name}` | {value} | {marks} | ☐ yes ☐ no | |")
        if entry.body:
            lines += ["", "**The entry's notes (its free text):** " + " ".join(entry.body.split())]
        flagged = (annotations.get("not_in_post") or {}).get(entry.id) or {}
        stats["flagged"] += len(flagged)
        lines += ["", "**Flagged before you start** (claims a model could not find in the post; each is an error in the entry or a passage it missed):", ""]
        lines += [f"- ☐ `{field}`: {' '.join(str(reason).split())}" for field, reason in flagged.items()] or ["- Nothing flagged."]
        lines += ["", "**Decision:** ☐ reviewed ☐ contested (fields: ______________________) &nbsp; **Date:** __________"]
    if missing:
        lines += ["", f"*{len(missing)} passage(s) proposed for marking were not found by exact search and are not shown: "
                      + "; ".join(sorted({f"{entry_id[-4:]} {field}" for entry_id, field, _ in missing})) + ".*"]
    if not annotations:
        lines += ["", "*No marks: the passages for this post have not been located yet.*"]
    lines += ["", f"## The post's text, marked ({first['title']})", "", marked.strip()]
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
           GUIDE, "", "## The posts behind the wiki", "",
           "| # | Post | Authors | Date posted | Entries | Meets your rule? | Link |", "|---|---|---|---|---|---|---|"]
    sections, totals = [], {"placed": 0, "missing": 0, "flagged": 0}
    for number, (post_id, group) in enumerate(by_post.items(), start=1):
        source = group[0].data["source"]
        unsupported = (audits.get(post_id) or {}).get("unsupported_fields")
        rule = "not audited" if post_id not in audits else ("yes" if not unsupported else "**no**: lacks " + ", ".join(unsupported))
        out.append(f"| {number} | {cell(source['title'])} | {cell(source['authors'])} | {source['published']} | "
                   f"{', '.join(entry.id[-4:] for entry in group)} | {rule} | {source['url']} |")
        section, stats = post_section(number, post_id, group, audits.get(post_id))
        sections.append(section)
        # the same section as its own file, so one post can be printed at a time
        (OUT / "posts").mkdir(parents=True, exist_ok=True)
        (OUT / "posts" / f"post-{number:02d}-{'-'.join(entry.id[-4:] for entry in group)}.md").write_text(
            section.replace("\n\n---\n\n", "", 1).lstrip() + "\n", encoding="utf-8")
        for key in totals:
            totals[key] += stats[key]
    out += ["", f"Marks placed across all posts: {totals['placed']}. Proposed passages not found and dropped: {totals['missing']}. "
                f"Claims flagged as not found in a post: {totals['flagged']}."]
    out += sections

    used = set(by_post)
    left_out = [row for row in audits.values() if row["post_id"] not in used]
    out += ["\n\n---\n\n# Posts judged genuine failure write-ups and left out", "",
            "A small model judged each of these a genuine write-up of a failed experiment. A stronger model then checked "
            "whether the post itself states every required field, and found it does not. They are not in the wiki. "
            "If the rule is relaxed (for example, by letting an entry say \"the post states no expectation\"), these are the candidates.", "",
            "| Post | The post does not state | Link |", "|---|---|---|"]
    for row in sorted(left_out, key=lambda item: (len(item.get("unsupported_fields") or []), item["title"])):
        out.append(f"| {cell(row['title'])} | {', '.join(row.get('unsupported_fields') or []) or 'see the audit notes'} | "
                   f"https://www.lesswrong.com/posts/{row['post_id']} |")
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
             "**Skills** are instructions a model follows. They live in `plugin/skills/<name>/SKILL.md` and are printed in full below.",
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
            lines += [f"### `{node.name}({arguments})`", "", "```", ast.get_docstring(node) or "", "```", ""]
    for name in ("ask", "contribute", "review"):
        text = (REPO / "plugin" / "skills" / name / "SKILL.md").read_text(encoding="utf-8")
        lines += ["\n---\n", f"# Skill file: `plugin/skills/{name}/SKILL.md`", "", text.strip(), ""]
    return "\n".join(lines) + "\n"


def main() -> int:
    OUT.mkdir(exist_ok=True)
    outputs = {
        OUT / "1-human-review-pack.md": review_pack(),
        OUT / "2-schema.md": schema_markdown(),
        OUT / "3-skills-and-tools.md": tools_markdown(),
        REPO / "schema" / "SCHEMA.md": schema_markdown(),
    }
    for path, text in outputs.items():
        path.write_text(text, encoding="utf-8")
        print(f"wrote {path.relative_to(REPO)}  ({len(text.split()):,} words)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

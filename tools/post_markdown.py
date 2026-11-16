"""A LessWrong / Alignment Forum post's HTML as Markdown for printing. Standard library only.

Used by tools/make_print_pack.py. It follows the conventions the maintainer's clippings use:

  headings     the post's own levels, shifted so its top level prints as ###
  lists        nested as on the page, one tab per level, no blank lines between items
  footnotes    [^N] where the page has the marker, and [^N]: definitions at the end
  maths        the page's own LaTeX ($...$ inline, $$...$$ on its own line), never retyped
  figures      the image at a fixed width with its caption in italics under it
  tables       Markdown tables; code blocks fenced
  links        the link text only: a printed URL helps nobody

convert() also returns the "stream": every letter and digit of the post's own words with its position in the
Markdown. Passages are located in that stream, so a mark can be placed although the Markdown around the words
(emphasis, list numbers, footnote markers) is not in the passage that was copied from the plain text.
"""
from __future__ import annotations

import re
from html.parser import HTMLParser

OPEN, CLOSE = "", ""          # wrap the post's own words while the Markdown is built; removed at the end
VOID = {"br", "img", "hr", "input", "meta", "link", "source", "wbr", "col"}
SKIP = {"style", "script", "noscript"}
BLOCK = {"p", "div", "section", "article", "h1", "h2", "h3", "h4", "h5", "h6", "ul", "ol", "li", "table", "thead", "tbody", "tfoot",
         "tr", "td", "th", "blockquote", "pre", "figure", "figcaption", "hr", "details", "summary"}
IMAGE_WIDTH = 450


class Node:
    def __init__(self, tag: str, attrs: dict | None = None):
        self.tag, self.attrs, self.children = tag, attrs or {}, []

    @property
    def classes(self) -> set:
        return set((self.attrs.get("class") or "").split())

    def walk(self):
        for child in self.children:
            if isinstance(child, Node):
                yield child
                yield from child.walk()

    def find(self, test):
        return next((node for node in self.walk() if test(node)), None)


class _Tree(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.root = Node("root")
        self.stack = [self.root]

    def handle_starttag(self, tag, attrs):
        node = Node(tag, {key: value or "" for key, value in attrs})
        self.stack[-1].children.append(node)
        if tag not in VOID:
            self.stack.append(node)

    def handle_startendtag(self, tag, attrs):
        self.stack[-1].children.append(Node(tag, {key: value or "" for key, value in attrs}))

    def handle_endtag(self, tag):
        for depth in range(len(self.stack) - 1, 0, -1):
            if self.stack[depth].tag == tag:
                del self.stack[depth:]
                return

    def handle_data(self, data):
        self.stack[-1].children.append(data)


def parse(html: str) -> Node:
    tree = _Tree()
    tree.feed(html or "")
    tree.close()
    return tree.root


def norm(text: str) -> str:
    """Letters and digits only, lower case: what a passage and the page are compared on."""
    return "".join(char.lower() for char in text if char.isalnum())


def _words(text: str) -> str:
    core = text.strip(" ")
    if not core:
        return text
    return text[:len(text) - len(text.lstrip(" "))] + OPEN + core + CLOSE + text[len(text.rstrip(" ")):]    # spaces stay outside, so emphasis hugs its words


def _bare(text: str) -> str:
    return text.replace(OPEN, "").replace(CLOSE, "")


def _tidy(text: str) -> str:
    """One paragraph: runs of spaces collapsed, a <br> kept as a Markdown line break."""
    lines = [re.sub(r" {2,}", " ", line).strip() for line in text.split("\n")]
    return "  \n".join(line for line in lines if _bare(line).strip())


def _wrap(inner: str, mark: str) -> str:
    core = inner.strip(" ")
    if not _bare(core).strip() or "\n" in core:
        return inner
    lead, tail = inner[:len(inner) - len(inner.lstrip(" "))], inner[len(inner.rstrip(" ")):]
    return f"{lead}{mark}{core}{mark}{tail}"


class _Writer:
    def __init__(self, root: Node):
        levels = [int(node.tag[1]) for node in root.walk() if re.fullmatch(r"h[1-6]", node.tag)]
        self.top = min(levels, default=1)

    # ---- inline ---------------------------------------------------------------------------
    def inline(self, node) -> str:
        if isinstance(node, str):
            return _words(re.sub(r"\s+", " ", node.replace("\xa0", " ")))
        classes = node.classes
        if node.tag in SKIP or "footnote-back-link" in classes:
            return ""
        if "footnote-reference" in classes:
            index = node.attrs.get("data-footnote-index") or norm("".join(self.inline(child) for child in node.children))
            return f"[^{OPEN}{index}{CLOSE}]"
        if "math-tex" in classes:
            labelled = node.find(lambda inner: inner.attrs.get("aria-label"))
            if labelled is not None:
                latex = labelled.attrs["aria-label"].strip()
                display = node.find(lambda inner: "mjpage__block" in inner.classes) is not None
                return f"\n$${latex}$$\n" if display else f"${latex}$"
        if node.tag == "br":
            return "\n"
        if node.tag == "img":
            return f"![|{IMAGE_WIDTH}]({node.attrs['src']})" if node.attrs.get("src") else ""
        inner = "".join(self.inline(child) for child in node.children)
        if node.tag in ("em", "i"):
            return _wrap(inner, "*")
        if node.tag in ("strong", "b"):
            return _wrap(inner, "**")
        if node.tag == "code":
            return _wrap(inner, "`")
        return inner

    # ---- blocks ---------------------------------------------------------------------------
    def _is_block(self, node) -> bool:
        return isinstance(node, Node) and (node.tag in BLOCK or any(inner.tag in BLOCK for inner in node.walk()))

    def blocks(self, node: Node) -> list[str]:
        out, run = [], []

        def flush():
            text = _tidy("".join(run))
            run.clear()
            if text:
                out.append(text)

        for child in node.children:
            if self._is_block(child):
                flush()
                out.extend(self.block(child))
            else:
                run.append(self.inline(child))
        flush()
        return out

    def block(self, node: Node) -> list[str]:
        tag = node.tag
        if tag in SKIP:
            return []
        if re.fullmatch(r"h[1-6]", tag):
            text = _tidy("".join(self.inline(child) for child in node.children)).replace("*", "").replace("  \n", " ")
            return ["#" * min(6, 3 + int(tag[1]) - self.top) + " " + text] if _bare(text).strip() else []
        if tag in ("ul", "ol"):
            if node.classes & {"footnotes", "footnote-section"}:
                return self.footnotes(node)
            listed = self.listing(node, 0)
            return [listed] if listed else []
        if tag == "blockquote":
            inner = "\n\n".join(self.blocks(node))
            return ["\n".join("> " + line if line else ">" for line in inner.split("\n"))] if inner else []
        if tag == "pre":
            lines = [line.rstrip() for line in self.raw(node).split("\n")]
            lines = [_words(line) for line in lines if line.strip()]
            return ["```\n" + "\n".join(lines) + "\n```"] if lines else []
        if tag == "table":
            return self.table(node)
        if tag == "figure":
            return self.figure(node)
        if tag == "hr":
            return ["---"]
        return self.blocks(node)

    def raw(self, node) -> str:
        if isinstance(node, str):
            return node.replace("\xa0", " ")
        if node.tag == "br":
            return "\n"
        return "" if node.tag in SKIP else "".join(self.raw(child) for child in node.children)

    def listing(self, node: Node, depth: int) -> str:
        lines, number, indent = [], 0, "\t" * depth
        for item in node.children:
            if not isinstance(item, Node) or item.tag != "li":
                continue
            parts, run = [], []

            def flush():
                text = _tidy("".join(run))
                run.clear()
                if text:
                    parts.append(("text", text))

            for child in item.children:
                if isinstance(child, Node) and child.tag in ("ul", "ol"):
                    flush()
                    parts.append(("list", self.listing(child, depth + 1)))
                elif self._is_block(child):
                    flush()
                    parts.extend(("text", text) for text in self.block(child))
                else:
                    run.append(self.inline(child))
            flush()
            if not parts:
                continue
            number += 1
            marker, first = (f"{number}. " if node.tag == "ol" else "- "), True
            for kind, text in parts:
                if kind == "list":
                    if text:
                        lines.append(text)
                elif first:
                    lines.append(indent + marker + text.replace("\n", "\n" + indent + "\t"))
                    first = False
                else:
                    lines += ["", indent + "\t" + text.replace("\n", "\n" + indent + "\t")]
            if first and lines:                                           # an item that is only a nested list
                pass
        return "\n".join(lines)

    def footnotes(self, node: Node) -> list[str]:
        definitions = []
        for position, item in enumerate((child for child in node.children if isinstance(child, Node) and child.tag == "li"), start=1):
            index = item.attrs.get("data-footnote-index") or str(position)
            body = item.find(lambda inner: "footnote-content" in inner.classes) or item
            paragraphs = self.blocks(body)
            if paragraphs:
                definitions.append(f"[^{index}]: " + "\n\n".join([paragraphs[0]] + ["    " + text.replace("\n", "\n    ") for text in paragraphs[1:]]))
        joiner = "\n\n" if any("\n\n" in text for text in definitions) else "\n"
        return [joiner.join(definitions)] if definitions else []

    def cell(self, node: Node) -> str:
        return " ".join(self.blocks(node)).replace("  \n", " ").replace("\n", " ").replace("|", "\\|")

    def table(self, node: Node) -> list[str]:
        rows = [[self.cell(cell) for cell in row.children if isinstance(cell, Node) and cell.tag in ("td", "th")]
                for row in node.walk() if row.tag == "tr"]
        rows = [row for row in rows if any(_bare(value).strip() for value in row)]
        if not rows:
            return []
        width = max(map(len, rows))
        lines = ["| " + " | ".join(row + [""] * (width - len(row))) + " |" for row in rows]
        return ["\n".join([lines[0], "|" + "---|" * width] + lines[1:])]

    def figure(self, node: Node) -> list[str]:
        out = []
        captions = [inner for inner in node.walk() if inner.tag == "figcaption"]      # a page can carry an empty one before the real one
        table = node.find(lambda inner: inner.tag == "table")
        image = node.find(lambda inner: inner.tag == "img" and inner.attrs.get("src"))
        text = " ".join(part for caption in captions for part in self.blocks(caption)).replace("  \n", " ")
        text = _wrap(text.replace("*", ""), "*") if _bare(text).strip() else ""
        if table is not None:
            out += self.table(table)
            if text:
                out.append(text)
        elif image is not None:
            out.append(f"![|{IMAGE_WIDTH}]({image.attrs['src']})" + ("  \n" + text if text else ""))
        else:
            out += [text for child in node.children if isinstance(child, Node) and child not in captions for text in (self.block(child) if self._is_block(child) else [])]
            if text:
                out.append(text)
        return out


def convert(html: str) -> tuple[str, list]:
    """(Markdown, stream). The stream is [(letter or digit, its position in the Markdown), ...] over the post's own words."""
    root = parse(html)
    tagged = "\n\n".join(_Writer(root).blocks(root))
    markdown, stream, inside = [], [], False
    for char in tagged:
        if char == OPEN:
            inside = True
        elif char == CLOSE:
            inside = False
        else:
            if inside and char.isalnum():
                stream.append((char.lower(), len(markdown)))
            markdown.append(char)
    return "".join(markdown), stream


def page_text(html: str) -> str:
    """The page's own words in order, read straight off the HTML: the reference convert() is checked against."""
    def read(node) -> str:
        if isinstance(node, str):
            return node
        if node.tag in SKIP or node.classes & {"math-tex", "footnote-back-link"}:
            return " "
        return " ".join(read(child) for child in node.children)

    return read(parse(html))


def same_words(html: str, stream: list) -> bool:
    """True when the Markdown holds every letter and digit of the page's words, in the page's order, and nothing else."""
    return norm(page_text(html)) == "".join(char for char, _ in stream)


def place_marks(markdown: str, stream: list, annotations: dict, labels: dict, show_entry: bool = True) -> tuple[str, dict, list]:
    """The Markdown with a mark around every passage found in the stream. Same return shape as make_print_pack.annotate."""
    keys = "".join(char for char, _ in stream)
    spans, placed, missing = {}, {}, []
    for entry_id, fields in (annotations.get("entries") or {}).items():
        for field, items in (fields or {}).items():
            for item in items or []:
                snippet = (item or {}).get("snippet") or ""
                needle = norm(snippet)
                at = keys.find(needle) if len(needle) >= 2 else -1
                if at < 0:
                    missing.append((entry_id, field, snippet))
                    continue
                start, end = stream[at][1], stream[at + len(needle) - 1][1] + 1
                if markdown[max(0, start - 2):start] == "[^":            # never split a footnote marker or an emphasis run
                    start -= 2
                while start > 0 and markdown[start - 1] in "*`":
                    start -= 1
                if markdown[end:end + 1] == "]" and "[^" in markdown[max(0, end - 6):end]:
                    end += 1
                while markdown[end:end + 1] and markdown[end] in "*`":
                    end += 1
                spans.setdefault((start, end), {}).setdefault(entry_id[-4:], []).append(labels.get(field, field.upper()))
                placed[(entry_id, field)] = placed.get((entry_id, field), 0) + 1
    inserts = []
    for (start, end), by_entry in spans.items():
        label = " | ".join(", ".join(dict.fromkeys(names)) + (f" · {short}" if show_entry else "") for short, names in sorted(by_entry.items()))
        inserts.append((start, 1, f"***⟦{label}⟧*** "))
        inserts.append((end, 0, f" ***⟦/{label}⟧***"))
    for position, _, mark in sorted(inserts, key=lambda item: (-item[0], item[1])):
        markdown = markdown[:position] + mark + markdown[position:]
    return markdown, placed, missing

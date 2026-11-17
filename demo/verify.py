"""Verification run: exercise every function of the proof of concept and record what happened.

  python demo/verify.py                  (or: make verify)
  python demo/verify.py --with-plugin    (or: make verify PLUGIN=1) also loads the plugin in headless Claude Code sessions

It uses the same method as the demo video (demo/build_demo.py): a headless
browser shows each step and a frame is captured, so a person can look at the
evidence instead of trusting a green tick. It differs from the demo in purpose:
the demo tells the story, this checks everything, including what the demo
leaves out.

What it does, in order:

1. Clones this repository into a throwaway folder (no remote, so nothing can be
   pushed) and builds fixtures there: drafts, deliberately broken entries, and
   an issue-form body. Every command that writes runs in the clone.
2. Runs the commands in demo/verify.yaml. Each has an expected exit code and
   text that must appear; a command passes only if both hold and the text is on
   the captured frame.
3. Drives the real browse page and Datasette (in process, then on a real port
   when the machine allows it) and compares what is shown with the entry data.
4. Checks that this repository was not changed: same commit, same branches,
   same working tree as before.
5. Writes demo/out/verify/ (frames, verification.mp4, transcript.json) and
   VERIFICATION.md, the tracked report.

Exit code 0 only if every check passed and the repository is unchanged.
"""
from __future__ import annotations

import asyncio
import copy
import datetime as dt
import html
import json
import os
import re
import shutil
import socket
import string
import subprocess
import sys
import tempfile
import threading
import time
import urllib.request
from pathlib import Path
from urllib.parse import urlsplit

import yaml

DEMO = Path(__file__).resolve().parent
REPO = DEMO.parent
sys.path.insert(0, str(DEMO))
sys.path.insert(0, str(REPO / "tools"))

import build_demo as bd  # noqa: E402
import build_db  # noqa: E402
import build_site  # noqa: E402
import issue_to_entry  # noqa: E402
import wikilib  # noqa: E402

OUT = bd.OUT / "verify"
SPEC = DEMO / "verify.yaml"
REPORT = REPO / "VERIFICATION.md"
PY = REPO / ".venv" / "bin" / "python"
ROWS_PER_FRAME = 21           # visual rows of terminal text on one frame
CHARS_PER_ROW = 118
MAX_SHOWN_LINES = 120         # per command; expected text must be within what is shown
FRAME_SECONDS = 4.0
SYSTEM_KEYS = ("id", "contributor", "review", "dates")
# Checks made in code (the form round trip and the browser steps), as opposed to the command checks in verify.yaml.
CODED_CHECKS = (
    "issue-form-round-trip",
    "page-all-entries", "page-one-filter", "page-two-filters", "page-or-within-field", "page-clear", "page-search",
    "page-no-match", "page-date-range", "page-link", "page-full-entry", "page-dark",
    "datasette-inprocess-table", "datasette-inprocess-facet", "datasette-inprocess-list-fields", "datasette-inprocess-search",
    "datasette-port-table", "datasette-port-facet", "datasette-port-list-fields", "datasette-port-search",
)


# --------------------------------------------------------------------------
# The repository must come out of a run unchanged
# --------------------------------------------------------------------------


def git(repo: Path, *args: str) -> str:
    env = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
    completed = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, env=env)
    if completed.returncode != 0:
        raise SystemExit(f"git {' '.join(args)} failed: {completed.stderr.strip()[:400]}")
    return completed.stdout


def repo_state(repo: Path) -> dict:
    return {
        "head": git(repo, "rev-parse", "HEAD").strip(),
        "refs": git(repo, "for-each-ref", "--format=%(refname) %(objectname)").strip(),
        "status": git(repo, "status", "--porcelain").strip(),
        "stash": git(repo, "stash", "list").strip(),
    }


# --------------------------------------------------------------------------
# The throwaway clone and its fixtures
# --------------------------------------------------------------------------


def make_clone(work: Path) -> Path:
    clone = work / "clone"
    subprocess.run(["git", "clone", "-q", "--no-hardlinks", str(REPO), str(clone)], check=True, capture_output=True)
    git(clone, "remote", "remove", "origin")                       # no remote: nothing in this run can push anywhere
    git(clone, "config", "user.name", "Verification run")
    git(clone, "config", "user.email", "verification-run@example.invalid")
    return clone


def write_entry(path: Path, data: dict, body: str = "") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(wikilib.dump_entry(data, body), encoding="utf-8")


def issue_body(draft: dict, body: str, ticked: bool = True) -> str:
    """The text GitHub would send for a submitted form, with the labels taken from the form itself."""
    return issue_to_entry.form_body(issue_to_entry.form_answers(draft, body), ticked=ticked)


def make_fixtures(work: Path, clone: Path) -> dict:
    """Drafts, broken entries and issue-form bodies, all derived from real entries so the quote checks are real."""
    fix = work / "fixtures"
    entries = {entry.id: entry for entry in wikilib.load_entries(clone / "entries")}
    base = entries["fe-2026-0006"]
    draft = {key: value for key, value in copy.deepcopy(base.data).items() if key not in SYSTEM_KEYS}
    write_entry(fix / "draft-good.md", draft, base.body)

    invented = copy.deepcopy(draft)
    invented["source"]["quote"] = "This sentence was never written anywhere in the post."
    write_entry(fix / "draft-invented-quote.md", invented, base.body)

    promoted = copy.deepcopy(draft)
    promoted["contributor"] = {"type": "human", "handle": "someone-else"}
    promoted["review"] = {"status": "reviewed", "reviewers": [{"handle": "someone-else", "type": "human", "date": "2026-11-01", "notes": "Looks fine."}]}
    write_entry(fix / "draft-claims-own-review.md", promoted, base.body)

    good = entries["fe-2026-0008"]

    def broken(name: str, change, file_name: str = "fe-2026-0008.md") -> None:
        data = copy.deepcopy(good.data)
        change(data)
        write_entry(fix / "bad" / name / file_name, data, good.body)

    broken("value-not-on-the-list", lambda d: d.update(failure_type="bad_luck"))
    broken("no-source-url", lambda d: d["source"].pop("url"))
    broken("quote-not-in-post", lambda d: d["source"].update(quote="This sentence was never written anywhere in the post."))
    broken("quote-too-long", lambda d: d["source"].update(
        quote="one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen seventeen"))
    broken("no-hypothesis", lambda d: d.pop("hypothesis"))
    broken("wrong-field-type", lambda d: d.update(limitations=["a list", "where text is required"]))
    broken("id-does-not-match-file", lambda d: d.update(id="fe-2026-0099"))
    broken("reviewed-without-reviewer", lambda d: d.update(review={"status": "reviewed"}))
    broken("agent-entry-not-labelled", lambda d: d["contributor"].pop("agent_model", None))
    broken("same-id-twice", lambda d: None)
    broken("same-id-twice", lambda d: None, file_name="fe-2026-0009.md")

    (fix / "issue-body.md").write_text(issue_body(draft, base.body), encoding="utf-8")
    (fix / "issue-body-boxes-not-ticked.md").write_text(issue_body(draft, base.body, ticked=False), encoding="utf-8")
    bad_form = copy.deepcopy(draft)
    bad_form["failure_type"] = "bad_luck"
    (fix / "issue-body-bad-value.md").write_text(issue_body(bad_form, base.body), encoding="utf-8")
    return {"draft": draft, "body": base.body, "fix": fix}


def form_round_trip(fixtures: dict, clone: Path) -> tuple[bool, str]:
    """Does the issue form carry every field of a draft through unchanged?"""
    text = (fixtures["fix"] / "issue-body.md").read_text(encoding="utf-8")
    fields = issue_to_entry.parse_issue_body(text)
    converted, notes = issue_to_entry.entry_from_fields(fields)
    converted = wikilib.normalize_data(converted)
    draft = wikilib.normalize_data(json.loads(json.dumps(fixtures["draft"], default=str)))
    different = sorted(key for key in set(draft) | set(converted) if json.dumps(draft.get(key), sort_keys=True, default=str)
                       != json.dumps(converted.get(key), sort_keys=True, default=str))
    if notes.strip() != fixtures["body"].strip():
        different.append("notes")
    if different:
        return False, "fields changed by the form: " + ", ".join(different)
    return True, f"all {len(draft)} top-level fields and the notes came through the form unchanged"


# --------------------------------------------------------------------------
# Running commands and judging them
# --------------------------------------------------------------------------


class Scrubber:
    """Keep machine paths, and the user's name with them, out of frames and reports."""

    def __init__(self, work: Path, clone: Path):
        pairs = []
        for path, shown in ((clone, "."), (work, "$WORK"), (REPO, "<repo>"), (Path.home(), "~")):
            for form in {str(path), str(path.resolve())}:
                pairs.append((form, shown))
        self.pairs = sorted(pairs, key=lambda pair: -len(pair[0]))

    def __call__(self, text: str) -> str:
        for old, new in self.pairs:
            text = text.replace(old, new)
        return text


def command_env(work: Path, clone: Path, fix: Path, ids: dict) -> dict:
    env = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
    env.update({
        "PATH": f"{PY.parent}:{env.get('PATH', '')}",
        "WORK": str(work), "FIX": str(fix), "REPO": str(REPO),
        "FEWIKI_CACHE": str(REPO / ".cache" / "lw"),              # post texts already fetched; the clone has none
        "FEWIKI_PYTHON": str(PY),
        "FEWIKI_HANDLE": "verification-run",
        "FEWIKI_DEMO_REMOTE_URL": wikilib.remote_url(REPO) or "",    # the clone has no remote; the narration describes the real repository
        "ISSUE_AUTHOR": "verification-run", "ISSUE_NUMBER": "1",
        "DAY": dt.date.today().strftime("%Y%m%d"),
        "PLAYWRIGHT_BROWSERS_PATH": os.environ.get("PLAYWRIGHT_BROWSERS_PATH", ""),
    })
    env.update(ids)
    return env


def run_check(check: dict, env: dict, clone: Path, scrub: Scrubber) -> dict:
    cwd = REPO if check.get("cwd") == "repo" else clone
    commands, passed = [], True
    for spec in check["commands"]:
        command = spec["run"]
        # shell=True on purpose: the commands are this repository's own check list (demo/verify.yaml), shown on the
        # frame exactly as they are run. Nothing here comes from entries, issue text or other outside input.
        completed = subprocess.run(command, shell=True, cwd=str(cwd), env=env, capture_output=True, text=True, timeout=spec.get("timeout", 900))
        output = scrub((completed.stdout + completed.stderr).rstrip("\n"))
        lines = output.split("\n") if output else []
        shown = lines[:MAX_SHOWN_LINES]
        hidden = len(lines) - len(shown)
        visible = "\n".join(shown)
        want_exit = spec.get("expect_exit", 0)
        expand = lambda text: string.Template(text).safe_substitute(env)  # noqa: E731
        problems = []
        if completed.returncode != want_exit:
            problems.append(f"exit code {completed.returncode}, expected {want_exit}")
        for text in spec.get("expect", []):
            if expand(text) not in output:
                problems.append(f"missing: {expand(text)!r}")
            elif expand(text) not in visible:
                problems.append(f"present but not on the frame: {expand(text)!r}")
        for text in spec.get("reject", []):
            if expand(text) in output:
                problems.append(f"must not appear: {expand(text)!r}")
        if spec.get("expect_no_output") and output.strip():
            problems.append("expected no output")
        passed = passed and not problems
        commands.append({
            "command": command, "exit_code": completed.returncode, "expected_exit": want_exit, "output": output, "shown": shown, "hidden": hidden,
            "expect": [expand(text) for text in spec.get("expect", [])], "problems": problems,
        })
    return {"passed": passed, "commands": commands}


# --------------------------------------------------------------------------
# Frames
# --------------------------------------------------------------------------

EXTRA_CSS = """
.bar .pass { color: #7fd491; } .bar .fail { color: #ff9b8f; } .bar .skip { color: #e8c468; }
.ok { color: #7fd491; } .bad { color: #ff9b8f; font-weight: 600; } .dim { color: #8a96a3; }
"""


def visual_rows(line: str) -> int:
    return max(1, -(-len(line) // CHARS_PER_ROW))


def terminal_pages(check: dict, outcome: dict) -> list[str]:
    """One or more pages of terminal text for a check; nothing that decides pass or fail is left off."""
    rows: list[tuple[str, int]] = []                     # (html line, visual rows)
    for item in outcome["commands"]:
        rows.append((f'<span class="prompt">$</span> <span class="cmd">{html.escape(item["command"])}</span>', visual_rows("$ " + item["command"])))
        for line in item["shown"]:
            rows.append((html.escape(line), visual_rows(line)))
        if item["hidden"] > 0:
            rows.append((f'<span class="more">… {item["hidden"]} more lines</span>', 1))
        if item["problems"]:
            for problem in item["problems"]:
                rows.append((f'<span class="bad">✗ {html.escape(problem)}</span>', visual_rows(problem) ))
        else:
            found = "; found " + ", ".join(repr(text) for text in item["expect"]) if item["expect"] else ""
            verdict = f"✓ exit code {item['exit_code']} as expected{found}"
            rows.append((f'<span class="ok">{html.escape(verdict)}</span>', visual_rows(verdict)))
        rows.append(("", 1))
    pages, current, used = [], [], 0
    for line, height in rows:
        if current and used + height > ROWS_PER_FRAME:
            pages.append(current)
            current, used = [], 0
        current.append(line)
        used += height
    if current:
        pages.append(current)
    status = "PASS" if outcome["passed"] else "FAIL"
    out = []
    for number, lines in enumerate(pages, start=1):
        bar = (f'<div class="bar"><b class="{status.lower()}">{status}</b> &nbsp; {html.escape(check["requirement"])} · '
               f'{html.escape(check["title"])} &nbsp; <span class="dim">({number}/{len(pages)})</span></div>')
        page = bd.page_html(bar + '<pre class="wrap">' + "\n".join(lines).rstrip("\n") + "</pre>")
        out.append(page.replace("</style>", EXTRA_CSS + "</style>", 1))
    return out


class Frames:
    def __init__(self, page, folder: Path):
        self.page, self.folder, self.items = page, folder, []
        self.recorder = bd.Recorder(page, folder, captions=True)

    def shot(self, name: str, caption: str, seconds: float = FRAME_SECONDS) -> str:
        if self.page.evaluate("() => !document.getElementById('demo-caption')"):
            self.recorder.prepare()
        self.recorder.caption(caption)
        self.recorder.hide_pointer()
        png = self.folder / f"{len(self.items) + 1:03d}-{name}.png"
        self.page.screenshot(path=str(png))
        self.items.append((png, seconds))
        return png.name


# --------------------------------------------------------------------------
# Browser checks: the browse page, then Datasette
# --------------------------------------------------------------------------


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


def browse_checks(page, frames: Frames, site_url: str) -> list[dict]:
    entries = wikilib.load_entries(REPO / "entries")
    ids = [entry.id for entry in entries]
    results = []
    problems: list[str] = []
    outside: list[str] = []
    page.on("console", lambda message: problems.append(message.text) if message.type == "error" else None)
    page.on("pageerror", lambda error: problems.append(str(error)))
    page.on("request", lambda request: outside.append(request.url) if not request.url.startswith(("file://", "about:", "data:")) else None)

    def shown() -> list[str]:
        return page.evaluate("() => Array.from(document.querySelectorAll('article.card')).map(card => card.id.replace('entry-', ''))")

    def box(path: str, value: str):
        return page.locator(f'input[data-facet="{path}"][data-value="{value}"]')

    def record(check_id: str, title: str, proves: str, expected: list[str], extra: str = "") -> None:
        got = shown()
        ok = got == expected and not problems
        detail = f"{len(got)} of {len(ids)} entries shown; the entry data says {len(expected)}" + (f"; {extra}" if extra else "")
        if problems:
            detail += "; page errors: " + "; ".join(problems[:3])
        name = frames.shot(check_id, f"{'PASS' if ok else 'FAIL'} · D4 · {title}: {detail}")
        results.append({"id": check_id, "requirement": "D4", "title": title, "proves": proves, "status": "PASS" if ok else "FAIL",
                        "detail": detail, "frames": [name]})

    def load(link: str = "") -> None:
        page.goto("about:blank")
        page.goto(site_url + link)
        page.wait_for_selector("#count")

    load()
    record("page-all-entries", "The page lists every entry", "The static page opens from a file with no server and shows the whole wiki.", ids,
           "no request left the machine" if not outside else f"requests to outside: {outside[:2]}")
    if outside:
        results[-1]["status"] = "FAIL"

    box("failure_type", "hypothesis_false").check()
    record("page-one-filter", "One tick filters the list", "A facet value keeps exactly the entries that have it.",
           [e.id for e in entries if e.data["failure_type"] == "hypothesis_false"])

    group = box("badges", "agent-written").locator("xpath=ancestor::details[1]")
    if not group.evaluate("el => el.open"):
        group.locator("summary").first.click()
    box("badges", "agent-written").check()
    record("page-two-filters", "Two fields combine with AND", "Filters on different fields narrow the list together.",
           [e.id for e in entries if e.data["failure_type"] == "hypothesis_false" and "agent-written" in wikilib.badges(e.data)])

    box("failure_type", "unknown").check()
    record("page-or-within-field", "Two values of one field combine with OR", "Ticking a second value of the same field widens that field.",
           [e.id for e in entries if e.data["failure_type"] in {"hypothesis_false", "unknown"} and "agent-written" in wikilib.badges(e.data)])

    page.locator("#clear").click()
    record("page-clear", "Clear all filters restores the full list", "One button undoes every filter.", ids)

    page.locator("#search").fill("steganography")
    record("page-search", "Search looks in every field and the notes", "Free-text search finds a word wherever it occurs in an entry.",
           [e.id for e in entries if "steganography" in " ".join(all_strings(e.data) + [e.body]).lower()])

    page.locator("#search").fill("zzz-no-such-word")
    message = page.locator("#results").inner_text()
    record("page-no-match", "No match says so without overclaiming", "An empty result says nobody has filed one, not that the idea is untested.", [],
           "message shown" if "nobody has filed one" in message else "MESSAGE MISSING")
    if "nobody has filed one" not in message:
        results[-1]["status"] = "FAIL"

    page.locator("#clear").click()
    group = page.locator('input[data-range="source.published"][data-bound="min"]').locator("xpath=ancestor::details[1]")
    if not group.evaluate("el => el.open"):
        group.locator("summary").first.click()
    low = page.locator('input[data-range="source.published"][data-bound="min"]')
    low.fill("2026-01-01")
    low.evaluate("el => { var panel = el.closest('aside'); var r = el.getBoundingClientRect(), p = panel.getBoundingClientRect(); panel.scrollTop += (r.top - p.top) - panel.clientHeight / 2; }")
    record("page-date-range", "Date and number fields filter by range", "A from-date keeps entries published on or after it.",
           [e.id for e in entries if str(e.data["source"]["published"]) >= "2026-01-01"])

    box("method", "sae").locator("xpath=ancestor::details[1]").evaluate("el => { el.open = true; }")
    box("method", "sae").check()
    page.locator("#entry-" + [e.id for e in entries if str(e.data["source"]["published"]) >= "2026-01-01" and "sae" in e.data["method"]][0]
                 + " details.all-fields > summary").click()
    page.wait_for_function("() => location.hash.indexOf('open=') !== -1")
    link = page.evaluate("() => location.hash")
    before = shown()
    load(link)
    opened = page.locator("details.all-fields[open]").count()
    record("page-link", "A filtered view reopens from its link", "Filters and the opened entry are in the address, so a view can be shared.", before,
           f"link {link}; entries open after reload: {opened}")
    if opened != 1 or not before:
        results[-1]["status"] = "FAIL"

    target = "fe-2026-0007"
    load("#open=" + target)
    entry = next(e for e in entries if e.id == target)
    terms = page.locator(f"#entry-{target} details.all-fields dt").all_inner_texts()
    missing = [key for key in entry.data if key not in terms]
    badges = page.locator(f"#entry-{target} .badge").all_inner_texts()
    record("page-full-entry", "The full view shows every field, and who reviewed it", "Nothing in an entry is hidden from a reader; an agent-only review is labelled as such.",
           ids, f"fields missing from the view: {missing or 'none'}; badges: {', '.join(badges)}")
    if missing or "Reviewed by an agent only" not in badges:
        results[-1]["status"] = "FAIL"

    page.emulate_media(color_scheme="dark")
    load()
    background = page.evaluate("() => getComputedStyle(document.body).backgroundColor")
    record("page-dark", "Dark colour scheme", "The page follows the reader's light or dark setting.", ids, f"background {background}")
    page.emulate_media(color_scheme="light")
    return results


def datasette_checks(page, frames: Frames, clone_db: Path, metadata: Path, work: Path) -> list[dict]:
    from datasette.app import Datasette

    entries = wikilib.load_entries(REPO / "entries")
    ids = [entry.id for entry in entries]
    results = []

    def table_ids() -> list[str]:
        return sorted(page.locator("table.rows-and-columns tbody tr td.col-id").all_inner_texts())

    def record(check_id: str, title: str, proves: str, expected: list[str], how: str) -> None:
        got = table_ids()
        ok = got == sorted(expected)
        detail = f"{len(got)} rows shown; the entry data says {len(expected)}; {how}"
        name = frames.shot(check_id, f"{'PASS' if ok else 'FAIL'} · D4 · {title}: {detail}")
        results.append({"id": check_id, "requirement": "D4", "title": title, "proves": proves, "status": "PASS" if ok else "FAIL",
                        "detail": detail, "frames": [name]})

    def run_pages(base: str, prefix: str, how: str) -> None:
        page.goto(base + "/wiki/entries")
        record(prefix + "-table", "Datasette lists every entry with facets", "The second browse UI shows the same wiki as a filterable table.", ids, how)
        page.locator(".facet-results a", has_text="hypothesis_false").first.click()
        page.wait_for_load_state()
        record(prefix + "-facet", "A Datasette facet link filters the table", "Clicking a facet value keeps the rows that have it.",
               [e.id for e in entries if e.data["failure_type"] == "hypothesis_false"], how)
        page.goto(base + "/wiki/entries?method__arraycontains=sae&badges__arraycontains=agent-written")
        record(prefix + "-list-fields", "List fields filter by membership", "Fields that hold lists (methods, badges) can be filtered by one value.",
               [e.id for e in entries if "sae" in e.data["method"] and "agent-written" in wikilib.badges(e.data)], how)
        page.goto(base + "/wiki/entries")
        page.locator('input[name="_search"]').fill("steganography")
        page.locator('input[name="_search"]').press("Enter")
        page.wait_for_load_state()
        record(prefix + "-search", "Datasette full-text search", "The search box finds entries by any word.",
               [e.id for e in entries if "steganography" in " ".join(all_strings(e.data) + [e.body]).lower()], how)

    # 1. In process: the browser's requests are answered by Datasette's own app, no port opened.
    datasette = Datasette([str(clone_db)], metadata=yaml.safe_load(metadata.read_text(encoding="utf-8")))
    loop = asyncio.new_event_loop()
    threading.Thread(target=loop.run_forever, daemon=True).start()
    asyncio.run_coroutine_threadsafe(datasette.invoke_startup(), loop).result(timeout=60)

    def serve(route, request):
        url = urlsplit(request.url)
        target = url.path + ("?" + url.query if url.query else "")
        response = asyncio.run_coroutine_threadsafe(datasette.client.get(target, follow_redirects=True), loop).result(timeout=60)
        route.fulfill(status=response.status_code, headers=dict(response.headers), body=response.content)

    page.route("**/*", serve)
    run_pages("http://datasette.test", "datasette-inprocess", "served in process, no port")
    page.unroute("**/*")
    loop.call_soon_threadsafe(loop.stop)

    # 2. On a real port, the way `make datasette` serves it, when this machine allows listening.
    with socket.socket() as probe:
        try:
            probe.bind(("127.0.0.1", 0))
            port = probe.getsockname()[1]
        except OSError as exc:
            results.append({"id": "datasette-port-table", "requirement": "D4", "title": "Datasette served on a local port", "status": "NOT RUN",
                            "proves": "The documented `make datasette` path works in a browser.", "frames": [],
                            "detail": f"this machine refused a local port ({exc}); the in-process run above covers the same pages"})
            return results
    server = subprocess.Popen([str(PY), "-m", "datasette", "serve", str(clone_db), "--metadata", str(metadata), "--host", "127.0.0.1", "--port", str(port)],
                              stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    try:
        base = f"http://127.0.0.1:{port}"
        for _ in range(60):
            try:
                urllib.request.urlopen(base + "/-/versions.json", timeout=2).read()
                break
            except OSError:
                time.sleep(0.5)
        else:
            raise SystemExit("Datasette did not start on its port")
        run_pages(base, "datasette-port", "served on a local port, as `make datasette` does")
    finally:
        server.terminate()
        try:
            server.wait(timeout=10)
        except subprocess.TimeoutExpired:
            server.kill()
    return results


# --------------------------------------------------------------------------
# Report
# --------------------------------------------------------------------------


def write_report(spec: dict, results: list[dict], unchanged: bool, leaks: list[str], commit: str, video: str | None) -> None:
    counts = {status: sum(1 for item in results if item["status"] == status) for status in ("PASS", "FAIL", "NOT RUN")}
    lines = [
        "# Verification report",
        "",
        "Generated by `python demo/verify.py` (`make verify`). Do not edit by hand; rerun instead.",
        "",
        f"- **Run:** {dt.datetime.now().astimezone().strftime('%Y-%m-%d %H:%M %Z')}, on commit `{commit[:7]}`.",
        f"- **Result:** {counts['PASS']} passed, {counts['FAIL']} failed, {counts['NOT RUN']} not run.",
        f"- **This repository after the run:** {'unchanged (same commit, branches, working tree and stash as before)' if unchanged else '**CHANGED: the run touched the real repository**'}.",
        f"- **Personal paths in the evidence:** {'none found' if not leaks else '**found in: ' + ', '.join(leaks) + '**'}.",
        "- **Evidence:** one frame per step in `demo/out/verify/frames/`" + (f", joined as `{video}`" if video else "")
        + ", plus `demo/out/verify/transcript.json` with every command's full output. That folder is git-ignored; rerun to regenerate it.",
        "",
        "## Method",
        "",
        "The same method as the demo video: a headless browser shows each step and a frame is captured. Commands that write "
        "(submit, review, merge, the issue form, gold sync, handle change, evals) run in a throwaway clone with no remote, "
        "so nothing here can push and the real repository is compared before and after. A command passes only when its exit "
        "code is the expected one and the expected text is on the captured frame. Browser steps pass only when the entries "
        "shown equal what the entry files say should be shown.",
        "",
        "## Checks",
        "",
        "| Check | Requirement | What it shows | Result | Frames |",
        "|---|---|---|---|---|",
    ]
    for item in results:
        frames = ", ".join(f"`{name}`" for name in item["frames"]) or "—"
        note = f" {item['detail']}" if item["status"] != "PASS" and item.get("detail") else ""
        lines.append(f"| `{item['id']}` | {item['requirement']} | {item['proves']}{note} | **{item['status']}** | {frames} |")
    lines += ["", "## Coverage: every function, and how it was checked", "",
              "| Function | How it was checked | Evidence |", "|---|---|---|"]
    status_of = {item["id"]: item["status"] for item in results}
    for row in spec["coverage"]:
        evidence, how = row["evidence"], row["status"]
        states = [status_of.get(check_id, "NOT RUN") for check_id in row.get("checks", [])]
        if states and all(state == "NOT RUN" for state in states):
            how = "not run in this report"
        elif "NOT RUN" in states:
            evidence += " **(some of these checks did not run in this report)**"
        if "FAIL" in states:
            how = "**FAILED**"
        lines.append(f"| {row['function']} | {how} | {evidence} |")
    failed = [item for item in results if item["status"] == "FAIL"]
    if failed:
        lines += ["", "## Failures", ""]
        for item in failed:
            lines.append(f"- `{item['id']}`: {item.get('detail', '')}")
            for command in item.get("commands", []):
                for problem in command["problems"]:
                    lines.append(f"  - `{command['command']}`: {problem}")
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Exercise every function and record the evidence on frames.")
    parser.add_argument("--with-plugin", action="store_true",
                        help="also load the plugin in headless Claude Code sessions (needs the `claude` command; uses model credits)")
    args = parser.parse_args(argv)
    enabled = {"plugin"} if args.with_plugin else set()
    spec = yaml.safe_load(SPEC.read_text(encoding="utf-8"))
    for tool in ("ffmpeg", "git"):
        if not shutil.which(tool):
            print(f"{tool} is not installed.", file=sys.stderr)
            return 1
    # Frames of an earlier run are set aside, not removed: this project never deletes (see _trash-review/ in .gitignore).
    stamp = dt.datetime.now().strftime("%Y%m%dT%H%M%S")
    for folder in ("frames", "html"):
        if (OUT / folder).exists() and any((OUT / folder).iterdir()):
            aside = REPO / "_trash-review" / f"verify-run-{stamp}"
            aside.mkdir(parents=True, exist_ok=True)
            shutil.move(str(OUT / folder), str(aside / folder))
    for folder in ("frames", "html", "site"):
        (OUT / folder).mkdir(parents=True, exist_ok=True)

    before = repo_state(REPO)
    work = Path(tempfile.mkdtemp(prefix="fewiki-verify-"))
    clone = make_clone(work)
    fixtures = make_fixtures(work, clone)
    scrub = Scrubber(work, clone)
    first = int(wikilib.next_id(clone).rsplit("-", 1)[1])
    ids = {f"NEW{n}": f"fe-{dt.date.today().year}-{first + n - 1:04d}" for n in (1, 2, 3)}
    env = command_env(work, clone, fixtures["fix"], ids)

    results: list[dict] = []
    pages: list[tuple[dict, list[str]]] = []
    for check in spec["checks"]:
        if check.get("optional") and check["optional"] not in enabled:
            results.append({"id": check["id"], "requirement": check["requirement"], "title": check["title"], "proves": check["proves"],
                            "status": "NOT RUN", "frames": [], "commands": [],
                            "detail": f"optional; run with --with-{check['optional']} (it starts headless Claude Code sessions, which use model credits)"})
            print(f"{'NOT RUN':8} {check['id']}")
            continue
        outcome = run_check(check, env, clone, scrub)
        item = {"id": check["id"], "requirement": check["requirement"], "title": check["title"], "proves": check["proves"],
                "status": "PASS" if outcome["passed"] else "FAIL", "commands": outcome["commands"], "frames": [],
                "detail": "; ".join(problem for command in outcome["commands"] for problem in command["problems"])}
        results.append(item)
        pages.append((item, terminal_pages(check, outcome)))
        print(f"{item['status']:8} {check['id']}")

    ok, detail = form_round_trip(fixtures, clone)
    results.append({"id": "issue-form-round-trip", "requirement": "D2", "title": "The issue form carries every field",
                    "proves": "A draft written into the issue form comes out as the same entry, field for field.",
                    "status": "PASS" if ok else "FAIL", "detail": detail, "frames": []})
    print(f"{results[-1]['status']:8} issue-form-round-trip  ({detail})")

    # Browser: terminal frames first, then the two browse UIs
    from playwright.sync_api import sync_playwright

    site = OUT / "site" / "index.html"
    build_site.build(REPO / "entries", site, None)
    db_path, metadata = work / "wiki.db", work / "metadata.yml"
    build_db.build(REPO / "entries", db_path)
    build_db.write_metadata(metadata, "wiki")
    with sync_playwright() as playwright:
        browser = bd.launch_browser(playwright)
        context = browser.new_context(viewport={"width": bd.WIDTH, "height": bd.HEIGHT}, device_scale_factor=bd.SCALE, color_scheme="light")
        page = context.new_page()
        frames = Frames(page, OUT / "frames")
        for item, htmls in pages:
            for number, text in enumerate(htmls, start=1):
                path = OUT / "html" / f"{item['id']}-{number}.html"
                path.write_text(text, encoding="utf-8")
                page.goto(path.as_uri())
                name = frames.shot(f"{item['id']}-{number}", item["proves"])
                item["frames"].append(name)
                if page.evaluate("() => document.documentElement.hasAttribute('data-overflow')"):
                    item["status"] = "FAIL"
                    item["detail"] = (item["detail"] + "; " if item["detail"] else "") + f"evidence does not fit frame {name}"
        try:
            results += browse_checks(page, frames, site.as_uri())
            results += datasette_checks(page, frames, db_path, metadata, work)
        finally:
            for item in results[len(spec["checks"]) + 1:]:
                print(f"{item['status']:8} {item['id']}")
            browser.close()

    after = repo_state(REPO)
    unchanged = before == after

    transcript = OUT / "transcript.json"
    transcript.write_text(json.dumps(results, indent=2, ensure_ascii=False, default=str) + "\n", encoding="utf-8")
    video = None
    if frames.items:
        final = OUT / "verification.mp4"
        bd.scene_video(frames.items, None, sum(seconds for _, seconds in frames.items), final)
        video = "demo/out/verify/verification.mp4"

    write_report(spec, results, unchanged, [], after["head"], video)
    home, user = str(Path.home()), Path.home().name
    leaks = [path.name for path in (transcript, REPORT) if home in path.read_text(encoding="utf-8") or re.search(re.escape(user), path.read_text(encoding="utf-8"), re.I)]
    if leaks:
        write_report(spec, results, unchanged, leaks, after["head"], video)

    failed = [item["id"] for item in results if item["status"] == "FAIL"]
    expected_ids = {check["id"] for check in spec["checks"]} | set(CODED_CHECKS)
    missing = sorted(expected_ids - {item["id"] for item in results})
    if missing:
        print("checks that did not run: " + ", ".join(missing), file=sys.stderr)
        failed += missing
    print(f"\n{sum(1 for item in results if item['status'] == 'PASS')} passed, {len(failed)} failed, "
          f"{sum(1 for item in results if item['status'] == 'NOT RUN')} not run; {len(frames.items)} frames")
    print(f"repository unchanged: {unchanged}; personal paths in evidence: {leaks or 'none'}")
    print(f"scratch folder (safe to remove yourself): {scrub(str(work))} under the system temp directory")
    print(f"wrote {REPORT.relative_to(REPO)}" + (f" and {video}" if video else ""))
    return 0 if not failed and unchanged and not leaks else 1


if __name__ == "__main__":
    raise SystemExit(main())

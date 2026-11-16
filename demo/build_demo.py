"""Build the demo: the narration script and a draft screen recording.

  python demo/build_demo.py --script-only     # demo/script.md only (needs nothing extra)
  python demo/build_demo.py                   # script + demo/out/demo-draft.mp4 (+ .srt)
  python demo/build_demo.py --no-voice        # no text-to-speech; timed from word counts
  python demo/build_demo.py --no-captions     # no caption bar (for recording your own voice over it)
  python demo/build_demo.py --short           # the short cut: leaves out scenes marked `short: false` -> demo-short.mp4

What the video is, plainly: a headless browser (Playwright's Chromium) is
driven through the real browse page with real clicks, typing and scrolling, and
shown real files and the real output of commands run at build time. A frame is
captured after every step and the frames are joined into a video. It is not a
capture of a person's screen:

- the pointer ring and the outline around a field are drawn by this script;
- motion is step by step (a frame per action), not continuous;
- the caption bar shows the narration; the voice, when present, is macOS
  text-to-speech, a scratch track meant to be replaced by a person's.

Needs: `pip install -r requirements-demo.txt`, `playwright install
chromium-headless-shell`, and ffmpeg. The voice needs macOS `say`, which does
not work inside the Claude Code sandbox; the rest does.

Everything is driven by demo/scenes.yaml. Outputs go to demo/out/ (git-ignored).
"""
from __future__ import annotations

import argparse
import html
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

import yaml

DEMO = Path(__file__).resolve().parent
REPO = DEMO.parent
OUT = DEMO / "out"
sys.path.insert(0, str(REPO / "tools"))
if (REPO / ".cache" / "ms-playwright").exists():
    os.environ.setdefault("PLAYWRIGHT_BROWSERS_PATH", str(REPO / ".cache" / "ms-playwright"))

import build_site  # noqa: E402
import wikilib  # noqa: E402

WIDTH, HEIGHT, SCALE = 1280, 720, 1.5        # CSS pixels and device scale: frames are 1920x1080
FPS = 30
PAD_SECONDS = 0.9                              # pause after each scene's narration
CAPTION_HEIGHT = 86
QUICK_SECONDS = 0.11                           # a frame inside typing or a scroll
POINT_SECONDS = 0.55                           # the pointer resting on a control before the click

CSS = f"""
* {{ box-sizing: border-box; }}
html, body {{ margin: 0; width: {WIDTH}px; height: {HEIGHT}px; overflow: hidden; }}
body {{ font: 20px/1.45 -apple-system, "Helvetica Neue", Arial, sans-serif; color: #e9ecef; background: #14171a; }}
.card {{ display: flex; flex-direction: column; justify-content: center; height: {HEIGHT - CAPTION_HEIGHT}px; padding: 0 110px; }}
.card h1 {{ font-size: 52px; line-height: 1.15; margin: 0 0 18px; color: #ffffff; }}
.card .subtitle {{ font-size: 30px; color: #a9c7e8; margin: 0 0 28px; }}
.card ul {{ list-style: none; margin: 10px 0 0; padding: 0; }}
.card li {{ font-size: 29px; line-height: 1.35; margin: 0 0 20px; padding-left: 34px; position: relative; }}
.card li:before {{ content: ""; position: absolute; left: 0; top: 15px; width: 14px; height: 14px; border-radius: 3px; background: #6fb1f2; }}
.card .footer {{ margin-top: 34px; font-size: 19px; color: #8a96a3; }}
.bar {{ height: 46px; line-height: 46px; padding: 0 22px; background: #23282e; color: #aeb8c2; font: 17px/46px ui-monospace, Menlo, monospace; border-bottom: 1px solid #343b43; white-space: nowrap; overflow: hidden; }}
.bar b {{ color: #ffffff; font-weight: 600; }}
pre {{ margin: 0; padding: 14px 22px; font: 16px/1.42 ui-monospace, Menlo, monospace; white-space: pre; overflow: hidden; height: {HEIGHT - 46 - CAPTION_HEIGHT}px; }}
pre.wrap {{ white-space: pre-wrap; overflow-wrap: anywhere; }}
.ln {{ color: #5d6875; }}
.prompt {{ color: #7fd491; }}
.cmd {{ color: #ffffff; font-weight: 600; }}
.exit-bad {{ color: #ff9b8f; }}
.more {{ color: #8a96a3; }}
"""

# Added to every page the recorder shows: the caption bar, the pointer ring, the field outline.
OVERLAY_CSS = f"""
#demo-caption {{ position: fixed; left: 0; right: 0; bottom: 0; height: {CAPTION_HEIGHT}px; z-index: 99999;
  display: flex; align-items: center; justify-content: center; padding: 0 70px; text-align: center;
  background: #0c0e11; color: #ffffff; border-top: 1px solid #3a424b;
  font: 500 21px/1.3 -apple-system, "Helvetica Neue", Arial, sans-serif; }}
#demo-caption.off {{ display: none; }}
body.demo-captions aside {{ max-height: calc(100vh - 24px - {CAPTION_HEIGHT}px) !important; }}
#demo-pointer {{ position: fixed; z-index: 99998; width: 34px; height: 34px; margin: -17px 0 0 -17px; border-radius: 50%;
  border: 4px solid #ff6a3d; background: rgba(255, 106, 61, 0.22); left: -100px; top: -100px; pointer-events: none; }}
.demo-outline {{ outline: 3px solid #ff6a3d; outline-offset: 3px; border-radius: 3px; background: rgba(255, 106, 61, 0.10); }}
"""

FIT_SCRIPT = """
(function () {
  var pre = document.querySelector("pre");
  if (!pre) { return; }
  var size = 16;
  while (pre.scrollHeight > pre.clientHeight && size > 9) { size -= 0.5; pre.style.fontSize = size + "px"; }
  if (pre.scrollHeight > pre.clientHeight) { document.documentElement.setAttribute("data-overflow", "1"); }
})();
"""


# --------------------------------------------------------------------------
# Scenes and facts
# --------------------------------------------------------------------------


def words(text: str) -> int:
    return len(text.split())


def sentences(text: str) -> list[str]:
    return [part.strip() for part in re.split(r"(?<=[.!?])\s+", " ".join(text.split())) if part.strip()]


def load_scenes() -> dict:
    """The demo definition, with every scene given `beats` (a sentence plus optional actions) and `narration`."""
    with (DEMO / "scenes.yaml").open(encoding="utf-8") as handle:
        spec = yaml.safe_load(handle)
    for scene in spec["scenes"]:
        if scene.get("beats"):
            for beat in scene["beats"]:
                beat.setdefault("actions", [])
            scene["narration"] = " ".join(beat["say"] for beat in scene["beats"])
        else:
            scene["narration"] = " ".join(scene["narration"].split())
            scene["beats"] = [{"say": sentence, "actions": []} for sentence in sentences(scene["narration"])]
    return spec


def repo_facts() -> dict:
    """The numbers the narration states, read from the repository."""
    def jsonl(name):
        path = REPO / "scouting" / name
        if not path.exists():
            return []
        with path.open(encoding="utf-8") as handle:
            return [json.loads(line) for line in handle if line.strip()]

    labels = jsonl("classification.jsonl") + jsonl("classification_round2.jsonl")
    with (REPO / "scouting" / "field_audit" / "summary.json").open(encoding="utf-8") as handle:
        audits = json.load(handle)
    with (REPO / "evals" / "results" / "results.json").open(encoding="utf-8") as handle:
        results = json.load(handle)
    gold = [wikilib.load_entry(path).data.get("gold_status") for path in sorted((REPO / "evals" / "gold").glob("fe-*.md"))]
    entries = wikilib.load_entries(REPO / "entries")
    return {
        "entries": len(list((REPO / "entries").glob("fe-*.md"))),
        "posts_classified": len(labels),
        "genuine_writeups": sum(1 for row in labels if row["label"] == "yes"),
        "full_field_posts": sum(1 for audit in audits if audit["passes_machine_checks"]),
        "contribute_accuracy_percent": round(100 * (results["contribute"]["overall_accuracy"] or 0)),
        "ask_passed": results["ask"]["passed"],
        "ask_total": results["ask"]["total"],
        "gold_verified": sum(1 for status in gold if status == "verified"),
        "agent_written": sum(1 for entry in entries if (entry.data.get("contributor") or {}).get("type") == "agent"),
        "reviewed": sum(1 for entry in entries if (entry.data.get("review") or {}).get("status") == "reviewed"),
        "reviewed_by_a_person": sum(1 for entry in entries if wikilib.reviewed_by(entry.data) == "a person"),
        # FEWIKI_DEMO_REMOTE_URL: set by the verification run, whose clone has its remote removed on purpose
        "has_github_remote": bool(build_site.github_web_url(os.environ.get("FEWIKI_DEMO_REMOTE_URL") or wikilib.remote_url(REPO))),
    }


def stale_facts(spec: dict) -> list[str]:
    actual = repo_facts()
    return [
        f"{key}: the narration assumes {value!r}, the repository now says {actual.get(key)!r}"
        for key, value in (spec.get("facts") or {}).items()
        if actual.get(key) != value
    ]


def estimate_seconds(scene: dict, wpm: int) -> float:
    return words(scene["narration"]) * 60 / wpm + PAD_SECONDS


def clock(seconds: float) -> str:
    return f"{int(seconds // 60)}:{int(seconds % 60):02d}"


# --------------------------------------------------------------------------
# The script document
# --------------------------------------------------------------------------


def describe_action(action: dict) -> str:
    do = action["do"]
    if do in {"tick", "untick"}:
        return f"{do} **{action['field'].replace('_', ' ')} → {action['value']}**"
    if do == "type":
        return f"type `{action['text']}` in the search box"
    if do == "clear":
        return "click **Clear all filters**"
    if do == "open":
        return f"open **All fields** on `{action['entry']}`"
    if do == "show_field":
        return f"scroll to **{action['field'].replace('_', ' ')}** and outline it"
    if do == "scroll_to":
        return f"scroll to `{action['entry']}`"
    if do == "scroll_top":
        return "scroll back to the top"
    if do == "scroll_panel":
        return "scroll the filter panel to show more fields"
    if do == "panel_top":
        return "scroll the filter panel back to the top"
    return f"scroll down {action.get('px', 300)} px"


def on_screen(scene: dict) -> str:
    kind = scene["kind"]
    if kind == "card":
        return "Title card: " + scene["title"]
    if kind == "page":
        steps = [describe_action(action) for beat in scene["beats"] for action in beat["actions"]]
        start = f", starting from the link `#{scene['start_link']}`" if scene.get("start_link") else ""
        return "The browse page in a headless browser" + start + (": " + "; ".join(steps) if steps else "") + "."
    if kind == "file":
        spans = ", then ".join(f"{first}–{last}" for first, last in file_ranges(scene))
        return f"File `{scene['path']}`, lines {spans}"
    if kind == "datasette":
        return "Datasette's own pages in the headless browser, served in process: " + "; ".join(f"`{beat['path']}`" for beat in scene["beats"] if beat.get("path"))
    return "Terminal, real output of: " + "; ".join(f"`{command}`" for command in scene["commands"])


def write_script(spec: dict, durations: dict[str, float] | None = None, voiced: bool = False) -> Path:
    wpm = spec.get("words_per_minute", 150)
    total_words = sum(words(scene["narration"]) for scene in spec["scenes"])
    lines = [
        f"# {spec['title']}: narration script",
        "",
        "Generated from `demo/scenes.yaml` by `demo/build_demo.py`. Edit the YAML, not this file, then run `make demo-script`.",
        "",
        "## How to read this",
        "",
        "- **Narration** is written for you to read aloud, in your voice. Change any of it in `demo/scenes.yaml`.",
        "- **On screen** is what the draft video shows for that scene: the real page driven by real clicks, a real file, or real command output.",
        "- **Update when** flags lines that are true today and will need changing as the project moves.",
        f"- Timings are {'measured from the generated voice track' if voiced else f'estimated at {wpm} words a minute'}, plus {PAD_SECONDS} s of pause per scene."
        " A built video's measured timings are in `demo/out/timings.json`; the text-to-speech voice runs a little faster than the estimate.",
        f"- Narration length: {total_words} words.",
        "",
        "## What the draft video is, and is not",
        "",
        "- `demo/out/demo-draft.mp4` (1920×1080), with subtitles in `demo/out/demo-draft.srt`. Build it with `make demo-video`. The short cuts are `demo/out/demo-short.mp4` (`make demo-short`) and `demo/out/demo-short-voice.mp4`, the narrated short cut embedded in the README.",
        "- A headless browser is driven through the real browse page with real clicks, typing and scrolling. A frame is captured after every step and the frames are joined into a video.",
        "- It is not a capture of a person's screen. The orange pointer ring and the outline around a field are drawn by the recorder, and motion is step by step, not continuous.",
        "- The caption bar shows the narration, and the cuts carry a voice track. `--no-captions` gives a clean picture if you want to record your own voice, or re-record live with `demo/live-demo-script.md`.",
        "- It shows no GitHub screens. It was recorded before the repository went public, so the close says \"not public yet\"; the repository is now public on GitHub. The form scene says the form has not been submitted on GitHub, which is still true.",
        "- The Claude Code session it shows is a saved transcript of a real headless session with the plugin loaded (`demo/answers/plugin-session.md`), not a live capture. The two `ask` answers on screen are saved files too; each scene's note says where its file came from.",
        "- Scenes marked *(not in the short cut)* are left out by `--short`, which builds `demo/out/demo-short.mp4` for places that ask for a video of five minutes or less.",
        "",
        "## Scenes",
        "",
    ]
    start = 0.0
    for number, scene in enumerate(spec["scenes"], start=1):
        seconds = (durations or {}).get(scene["id"]) or estimate_seconds(scene, wpm)
        lines += [
            f"### {number}. `{scene['id']}` · {clock(start)}–{clock(start + seconds)} ({seconds:.0f} s)"
            + ("" if scene.get("short", True) else " *(not in the short cut)*"),
            "",
            f"**On screen:** {on_screen(scene)}",
            "",
            "**Narration:**",
            "",
            "> " + scene["narration"],
            "",
        ]
        if scene.get("note"):
            lines += [f"**Note:** {scene['note']}", ""]
        if scene.get("update_when"):
            lines += [f"**Update when:** {scene['update_when']}", ""]
        start += seconds
    short_total = sum((durations or {}).get(scene["id"]) or estimate_seconds(scene, wpm) for scene in spec["scenes"] if scene.get("short", True))
    lines += [
        f"**Total: {clock(start)}** ({start:.0f} s). **Short cut: {clock(short_total)}** ({short_total:.0f} s). Estimates from word counts; measured on 2026-11-16 with `ffprobe`: full 6:34, short 5:03, narrated short 4:53.",
        "",
        "## Numbers the narration states",
        "",
        "The build checks these against the repository and stops if one is out of date.",
        "",
        "| Fact | Value |",
        "|---|---|",
    ]
    lines += [f"| {key} | {value} |" for key, value in (spec.get("facts") or {}).items()]
    lines += [
        "",
        "## The live-recording variant",
        "",
        "The plugin loads in Claude Code (checked headless; see `VERIFICATION.md`). The repository is on GitHub now, so these scenes are better recorded live (`demo/live-demo-script.md` has the shorter script):",
        "",
        "| Scene id | Record instead |",
        "|---|---|",
        "| `s07`–`s09` (ask) | A Claude Code session with the plugin: type the plan from `s07`, show the five-part answer; then the debate question from `s09`. |",
        "| `s10` (contribute) | Same session: \"Contribute this post: <a LessWrong URL not yet in the wiki>\". Show the pull request it opens, with the badges. |",
        "| `s11` (validate) | The failed check on that pull request, or the same terminal commands. |",
        "| `s12` (human path) | GitHub → Issues → New entry: submit the form, show the pull request the workflow opens. |",
        "| `s13` (review) | Run the human review command live (see `TODO.md`, T4), then `git log --oneline --grep Review`. |",
        "| `s14` (Datasette) | `make datasette`, then the entries table with its facets in a browser. |",
        "",
    ]
    path = DEMO / "script.md"
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


# --------------------------------------------------------------------------
# Scene pages (cards, files, terminals)
# --------------------------------------------------------------------------


def scrub(text: str, tmp: Path) -> str:
    """Keep machine-specific paths, and the user's name with them, off the screen."""
    text = text.replace(str(tmp), "$TMP").replace(str(REPO), ".")
    return text.replace(str(Path.home()), "~")


def page_html(body: str) -> str:
    return (
        f'<!doctype html><html lang="en"><head><meta charset="utf-8"><style>{CSS}</style></head>'
        f"<body>{body}<script>{FIT_SCRIPT}</script></body></html>"
    )


def card_html(scene: dict) -> str:
    parts = [f"<h1>{html.escape(scene['title'])}</h1>"]
    if scene.get("subtitle"):
        parts.append(f'<p class="subtitle">{html.escape(scene["subtitle"])}</p>')
    if scene.get("bullets"):
        parts.append("<ul>" + "".join(f"<li>{html.escape(item)}</li>" for item in scene["bullets"]) + "</ul>")
    if scene.get("footer"):
        parts.append(f'<div class="footer">{html.escape(scene["footer"])}</div>')
    return page_html(f'<div class="card">{"".join(parts)}</div>')


def file_ranges(scene: dict) -> list[tuple[int, int]]:
    """A file scene shows one excerpt, or several in turn (`ranges`)."""
    if scene.get("ranges"):
        return [(first, last) for first, last in scene["ranges"]]
    return [(scene["first_line"], scene["last_line"])]


def file_html(scene: dict, first: int, last: int) -> str:
    path = REPO / scene["path"]
    all_lines = path.read_text(encoding="utf-8").split("\n")
    last = min(last, len(all_lines))
    rows = [f'<span class="ln">{number:>3}  </span>{html.escape(all_lines[number - 1])}' for number in range(first, last + 1)]
    wrap = " wrap" if scene.get("wrap") else ""
    bar = f'<div class="bar"><b>{html.escape(scene["path"])}</b> &nbsp; lines {first}–{last} of {len(all_lines)}</div>'
    return page_html(bar + f'<pre class="file{wrap}">' + "\n".join(rows) + "</pre>")


def terminal_html(scene: dict, tmp: Path) -> tuple[list[str], list[dict]]:
    """Pages for a terminal scene, in the order a viewer sees them: the first command typed, then each command's output added."""
    env = dict(os.environ)
    env["TMP"] = str(tmp)
    env["PATH"] = f"{REPO / '.venv' / 'bin'}:{env.get('PATH', '')}"
    for name in ("GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE"):
        env.pop(name, None)
    blocks, record = [], []
    for command in scene["commands"]:
        # shell=True on purpose: the commands are this repository's own demo script (demo/scenes.yaml),
        # shown on screen exactly as they are run. Nothing here comes from entries or other outside input.
        completed = subprocess.run(command, shell=True, cwd=str(REPO), env=env, capture_output=True, text=True, timeout=300)
        output = scrub((completed.stdout + completed.stderr).rstrip("\n"), tmp)
        record.append({"command": command, "exit_code": completed.returncode, "output": output})
        shown = output.split("\n") if output else []
        limit = scene.get("max_lines", 30)
        extra = len(shown) - limit
        if extra > 0:
            shown = shown[:limit] + [f"… {extra} more lines"]
        block = f'<span class="prompt">$</span> <span class="cmd">{html.escape(command)}</span>\n'
        block += "\n".join(
            f'<span class="more">{html.escape(line)}</span>' if line.startswith("… ") and line.endswith("more lines") else html.escape(line)
            for line in shown
        )
        if completed.returncode != 0:
            block += f'\n<span class="exit-bad">(exit code {completed.returncode})</span>'
        blocks.append(block)
    bar = '<div class="bar"><b>terminal</b> &nbsp; failed-experiments-wiki</div>'
    wrap = ' class="wrap"' if scene.get("wrap") else ""
    typed = f'<span class="prompt">$</span> <span class="cmd">{html.escape(scene["commands"][0])}</span>'
    steps = [typed] + ["\n\n".join(blocks[:count]) for count in range(1, len(blocks) + 1)]
    return [page_html(bar + f"<pre{wrap}>" + step + "</pre>") for step in steps], record


# --------------------------------------------------------------------------
# The recorder: a headless browser, one frame per step
# --------------------------------------------------------------------------


class Recorder:
    """Drives the browser and collects frames as (png path, kind), kind being lead, quick, point or settle."""

    def __init__(self, page, frames_dir: Path, captions: bool):
        self.page = page
        self.frames_dir = frames_dir
        self.captions = captions
        self.count = 0

    def prepare(self) -> None:
        self.page.add_style_tag(content=OVERLAY_CSS)
        self.page.evaluate(
            """(captions) => {
                 var cap = document.createElement("div"); cap.id = "demo-caption"; if (!captions) { cap.className = "off"; }
                 var ptr = document.createElement("div"); ptr.id = "demo-pointer";
                 document.body.appendChild(cap); document.body.appendChild(ptr);
                 if (captions) { document.body.style.paddingBottom = "%dpx"; document.body.classList.add("demo-captions"); }
               }""" % CAPTION_HEIGHT,
            self.captions,
        )

    def caption(self, text: str) -> None:
        self.page.evaluate("(text) => { document.getElementById('demo-caption').textContent = text; }", text)

    def shot(self, scene_id: str, kind: str) -> tuple[Path, str]:
        self.count += 1
        png = self.frames_dir / f"{scene_id}-{self.count:03d}.png"
        self.page.screenshot(path=str(png))
        return png, kind

    def point_at(self, locator, anchor: str = "center") -> None:
        """Bring a control into view and put the pointer ring on it.

        A control in the filter panel scrolls only that panel, to its middle, so the results do not move.
        `anchor="left"` is for wide elements whose label sits at their left edge.
        """
        locator.evaluate(
            """el => {
                 var panel = el.closest('aside');
                 if (panel && getComputedStyle(panel).overflowY !== 'visible') {
                   var r = el.getBoundingClientRect(), p = panel.getBoundingClientRect();
                   panel.scrollTop += (r.top - p.top) - panel.clientHeight / 2;
                 } else {
                   el.scrollIntoView({block: 'center'});
                 }
               }"""
        )
        box = locator.bounding_box()
        if box:
            x = box["x"] + (min(box["width"] / 2, 44) if anchor == "left" else box["width"] / 2)
            self.page.evaluate(
                "([x, y]) => { var p = document.getElementById('demo-pointer'); p.style.left = x + 'px'; p.style.top = y + 'px'; }",
                [x, box["y"] + box["height"] / 2],
            )

    def hide_pointer(self) -> None:
        self.page.evaluate("() => { var p = document.getElementById('demo-pointer'); p.style.left = '-100px'; p.style.top = '-100px'; }")

    def act(self, scene_id: str, action: dict) -> list[tuple[Path, str]]:
        page, frames, do = self.page, [], action["do"]
        if do in {"tick", "untick"}:
            box = page.locator(f'input[data-facet="{action["field"]}"][data-value="{action["value"]}"]')
            group = box.locator("xpath=ancestor::details[1]")
            if not group.evaluate("el => el.open"):
                group.locator("summary").first.click()
            self.point_at(box)
            frames.append(self.shot(scene_id, "point"))
            box.check() if do == "tick" else box.uncheck()
            page.evaluate("() => window.scrollTo(0, 0)")          # show the filtered results from the top
            frames.append(self.shot(scene_id, "quick"))           # the click lands, pointer still on the box
            self.hide_pointer()
            frames.append(self.shot(scene_id, "settle"))
        elif do == "type":
            search = page.locator("#search")
            self.point_at(search)
            frames.append(self.shot(scene_id, "point"))
            search.click()
            self.hide_pointer()
            for index, letter in enumerate(action["text"], start=1):
                page.keyboard.type(letter)
                if index % 2 == 0 or index == len(action["text"]):
                    frames.append(self.shot(scene_id, "quick"))
            frames[-1] = (frames[-1][0], "settle")
        elif do == "clear":
            button = page.locator("#clear")
            self.point_at(button)
            frames.append(self.shot(scene_id, "point"))
            button.click()
            page.evaluate("() => window.scrollTo(0, 0)")
            self.hide_pointer()
            frames.append(self.shot(scene_id, "settle"))
        elif do == "open":
            summary = page.locator(f'#entry-{action["entry"]} details.all-fields > summary')
            self.point_at(summary, anchor="left")
            frames.append(self.shot(scene_id, "point"))
            summary.click()
            self.hide_pointer()
            page.evaluate("(id) => document.getElementById(id).scrollIntoView({block: 'start'})", f"entry-{action['entry']}")
            frames.append(self.shot(scene_id, "settle"))
        elif do == "show_field":
            page.evaluate("() => document.querySelectorAll('.demo-outline').forEach(el => el.classList.remove('demo-outline'))")
            found = page.evaluate(
                """([id, field]) => {
                     var terms = document.querySelectorAll('#' + id + ' details.all-fields dt');
                     for (var i = 0; i < terms.length; i++) {
                       if (terms[i].textContent === field) {
                         var value = terms[i].nextElementSibling;
                         terms[i].classList.add('demo-outline'); if (value) { value.classList.add('demo-outline'); }
                         (value || terms[i]).scrollIntoView({block: 'center'});
                         return true;
                       }
                     }
                     return false;
                   }""",
                [f"entry-{action['entry']}", action["field"]],
            )
            if not found:
                raise SystemExit(f"{scene_id}: field '{action['field']}' is not shown in {action['entry']}")
            frames.append(self.shot(scene_id, "settle"))
        elif do == "scroll_to":
            page.evaluate("(id) => document.getElementById(id).scrollIntoView({block: 'start'})", f"entry-{action['entry']}")
            frames.append(self.shot(scene_id, "settle"))
        elif do == "scroll_top":
            page.evaluate("() => window.scrollTo(0, 0)")
            frames.append(self.shot(scene_id, "settle"))
        elif do in {"scroll_panel", "panel_top"}:
            steps = 4 if do == "scroll_panel" else 1
            for step in range(steps):
                page.evaluate(
                    "([px, top]) => { var panel = document.querySelector('aside'); if (top) { panel.scrollTop = 0; } else { panel.scrollTop += px; } }",
                    [action.get("px", 600) / steps, do == "panel_top"],
                )
                frames.append(self.shot(scene_id, "quick" if step < steps - 1 else "settle"))
        elif do == "scroll":
            steps = 4
            for step in range(steps):
                page.evaluate("(px) => window.scrollBy(0, px)", action.get("px", 300) / steps)
                frames.append(self.shot(scene_id, "quick" if step < steps - 1 else "settle"))
        else:
            raise SystemExit(f"{scene_id}: unknown action {do!r}")
        return frames


def launch_browser(playwright):
    """Normal headless launch; inside a sandbox that refuses Chromium's helper processes, single-process mode."""
    try:
        return playwright.chromium.launch(headless=True)
    except Exception:  # noqa: BLE001  the failure is a crashed browser process, reported as a generic error
        return playwright.chromium.launch(headless=True, args=["--single-process", "--no-zygote", "--disable-gpu"])


POINTER_ACTIONS = {"tick", "untick", "type", "clear", "open"}     # the pointer moves first, so the old picture is shown briefly
DATASETTE_HOST = "http://datasette.demo"


class InProcessDatasette:
    """Datasette's own pages, answered from its app inside this process: no port is opened."""

    def __init__(self, folder: Path):
        import asyncio
        import threading

        import build_db
        from datasette.app import Datasette

        db_path, metadata_path = folder / "wiki.db", folder / "metadata.yml"
        build_db.build(REPO / "entries", db_path)
        build_db.write_metadata(metadata_path, "wiki")
        self.asyncio = asyncio
        self.app = Datasette([str(db_path)], metadata=yaml.safe_load(metadata_path.read_text(encoding="utf-8")))
        self.loop = asyncio.new_event_loop()
        threading.Thread(target=self.loop.run_forever, daemon=True).start()
        asyncio.run_coroutine_threadsafe(self.app.invoke_startup(), self.loop).result(timeout=60)

    def serve(self, route, request) -> None:
        from urllib.parse import urlsplit

        url = urlsplit(request.url)
        target = url.path + ("?" + url.query if url.query else "")
        response = self.asyncio.run_coroutine_threadsafe(self.app.client.get(target, follow_redirects=True), self.loop).result(timeout=60)
        route.fulfill(status=response.status_code, headers=dict(response.headers), body=response.content)

    def stop(self) -> None:
        self.loop.call_soon_threadsafe(self.loop.stop)


def record(spec: dict, urls: dict[str, list[str]], site_url: str, captions: bool) -> dict[str, list[list[tuple[Path, str]]]]:
    """Frames per scene, per beat."""
    from playwright.sync_api import sync_playwright

    frames_dir = OUT / "frames"
    result: dict[str, list[list[tuple[Path, str]]]] = {}
    with sync_playwright() as playwright:
        browser = launch_browser(playwright)
        context = browser.new_context(viewport={"width": WIDTH, "height": HEIGHT}, device_scale_factor=SCALE, color_scheme="light")
        page = context.new_page()
        recorder = Recorder(page, frames_dir, captions)
        datasette = None
        if any(scene["kind"] == "datasette" for scene in spec["scenes"]):
            datasette = InProcessDatasette(OUT / "tmp")
            page.route(DATASETTE_HOST + "/**", datasette.serve)
        for scene in spec["scenes"]:
            recorder.count = 0
            beats: list[list[tuple[Path, str]]] = []
            if scene["kind"] == "datasette":
                for beat in scene["beats"]:
                    if beat.get("path"):
                        page.goto(DATASETTE_HOST + beat["path"])
                        recorder.prepare()
                    recorder.caption(beat["say"])
                    beats.append([recorder.shot(scene["id"], "lead")])
            elif scene["kind"] == "page":
                page.goto("about:blank")
                page.goto(site_url + ("#" + scene["start_link"] if scene.get("start_link") else ""))
                page.wait_for_selector("article.card")
                recorder.prepare()
                for beat in scene["beats"]:
                    recorder.caption(beat["say"])
                    # A sentence about a field or a scroll must not sit over the previous picture: act first, then show.
                    actions = beat["actions"]
                    frames = [recorder.shot(scene["id"], "lead")] if not actions or actions[0]["do"] in POINTER_ACTIONS else []
                    for action in actions:
                        frames += recorder.act(scene["id"], action)
                    beats.append(frames)
            else:
                pages = urls[scene["id"]]
                for index, beat in enumerate(scene["beats"]):
                    # several excerpts of one file are spread evenly over the scene's sentences
                    wanted = pages[min(len(pages) - 1, index * len(pages) // len(scene["beats"]))]
                    if page.url != wanted:
                        page.goto(wanted)
                        recorder.prepare()
                        if page.evaluate("() => document.documentElement.hasAttribute('data-overflow')"):
                            print(f"warning: {scene['id']} does not fit the frame even at the smallest text size", file=sys.stderr)
                    recorder.caption(beat["say"])
                    beats.append([recorder.shot(scene["id"], "lead")])
            result[scene["id"]] = beats
        browser.close()
        if datasette:
            datasette.stop()
    return result


# --------------------------------------------------------------------------
# Timing, audio, video
# --------------------------------------------------------------------------


def run(args: list[str], **kwargs) -> subprocess.CompletedProcess:
    return subprocess.run(args, capture_output=True, text=True, **kwargs)


def media_seconds(path: Path) -> float:
    completed = run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)])
    try:
        return float(completed.stdout.strip())
    except ValueError:
        return 0.0


def speak(text: str, voice: str, wav: Path, rate: int | None = None) -> bool:
    """macOS text-to-speech into a WAV file. False if `say` is missing or produced nothing."""
    if not shutil.which("say"):
        return False
    aiff = wav.with_suffix(".aiff")
    run(["say", "-v", voice, *(["-r", str(rate)] if rate else []), "-o", str(aiff), text], timeout=300)
    if not aiff.exists() or media_seconds(aiff) < 0.5:
        return False
    run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", str(aiff), "-ar", "44100", "-ac", "1", str(wav)], check=True)
    return wav.exists()


def beat_seconds(scene: dict, scene_seconds: float) -> list[float]:
    """Share the scene's speaking time between its sentences by word count; the pause goes to the last one."""
    speaking = max(scene_seconds - PAD_SECONDS, 0.5)
    total = sum(words(beat["say"]) for beat in scene["beats"]) or 1
    shares = [speaking * words(beat["say"]) / total for beat in scene["beats"]]
    shares[-1] += scene_seconds - speaking
    return shares


def frame_seconds(frames: list[tuple[Path, str]], seconds: float) -> list[float]:
    """How long each frame of one beat is held. The first frame sets the scene, the last one is read."""
    if len(frames) == 1:
        return [seconds]
    fixed = [QUICK_SECONDS if kind == "quick" else POINT_SECONDS if kind == "point" else 0.0 for _, kind in frames]
    flexible = [index for index, (_, kind) in enumerate(frames) if kind in {"lead", "settle"}]
    budget = seconds - sum(fixed)
    if budget < 0.3 * len(flexible):                      # too much action for the sentence: squeeze the fixed frames
        scale = max(0.2, (seconds - 0.3 * len(flexible)) / (sum(fixed) or 1))
        fixed = [value * scale for value in fixed]
        budget = seconds - sum(fixed)
    out = list(fixed)
    lead_share = min(0.5, 0.15 * budget)                  # the old picture under a new sentence: keep it short
    last = flexible[-1]
    others = [index for index in flexible if index != last]
    for index in others:
        out[index] = lead_share if index == flexible[0] else max(0.4, 0.15 * budget)
    out[last] = max(0.3, budget - sum(out[index] for index in others))
    return out


def scene_video(frames: list[tuple[Path, float]], audio: Path | None, seconds: float, out: Path) -> None:
    listing = out.with_suffix(".txt")
    rows = []
    for png, held in frames:
        rows += [f"file '{png}'", f"duration {held:.3f}"]
    rows.append(f"file '{frames[-1][0]}'")              # the concat demuxer needs the last file repeated
    listing.write_text("\n".join(rows) + "\n", encoding="utf-8")
    command = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(listing)]
    command += ["-i", str(audio), "-af", "apad"] if audio else ["-f", "lavfi", "-i", "anullsrc=r=44100:cl=mono"]
    command += [
        "-t", f"{seconds:.3f}", "-r", str(FPS), "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "128k", "-ar", "44100", "-ac", "1", str(out),
    ]
    completed = run(command)
    if completed.returncode != 0:
        raise SystemExit(f"ffmpeg failed on {out.name}:\n{completed.stderr[-800:]}")


def srt_time(seconds: float) -> str:
    millis = int(round(seconds * 1000))
    return f"{millis // 3600000:02d}:{millis // 60000 % 60:02d}:{millis // 1000 % 60:02d},{millis % 1000:03d}"


def write_srt(spec: dict, durations: dict[str, float], path: Path) -> None:
    blocks, start, index = [], 0.0, 1
    for scene in spec["scenes"]:
        for beat, seconds in zip(scene["beats"], beat_seconds(scene, durations[scene["id"]])):
            blocks.append(f"{index}\n{srt_time(start)} --> {srt_time(start + seconds)}\n{beat['say']}\n")
            start += seconds
            index += 1
    path.write_text("\n".join(blocks), encoding="utf-8")


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build the demo script and the draft video.")
    parser.add_argument("--script-only", action="store_true", help="write demo/script.md and stop")
    parser.add_argument("--no-voice", action="store_true", help="no text-to-speech; scenes are timed from word counts")
    parser.add_argument("--no-captions", action="store_true", help="leave out the caption bar")
    parser.add_argument("--allow-stale", action="store_true", help="build even if a number in the narration is out of date")
    parser.add_argument("--short", action="store_true", help="leave out scenes marked `short: false` and write demo-short.mp4")
    args = parser.parse_args(argv)

    spec = load_scenes()
    stale = stale_facts(spec)
    if stale:
        print("Numbers in the narration are out of date (update demo/scenes.yaml):\n  " + "\n  ".join(stale), file=sys.stderr)
        if not args.allow_stale:
            return 1

    if not args.short:                       # the short cut must not replace measured timings with estimates
        print(f"wrote {write_script(spec).relative_to(REPO)}")
    if args.script_only:
        return 0
    if args.short:
        spec = dict(spec, scenes=[scene for scene in spec["scenes"] if scene.get("short", True)])

    for tool in ("ffmpeg", "ffprobe"):
        if not shutil.which(tool):
            print(f"{tool} is not installed.", file=sys.stderr)
            return 1
    try:
        import playwright  # noqa: F401
    except ImportError:
        print("Playwright is not installed: pip install -r requirements-demo.txt && playwright install chromium-headless-shell", file=sys.stderr)
        return 1

    run_dir = OUT
    for folder in ("html", "frames", "audio", "video", "tmp", "site"):
        (run_dir / folder).mkdir(parents=True, exist_ok=True)
    tmp = run_dir / "tmp"
    site = run_dir / "site" / "index.html"
    build_site.build(REPO / "entries", site, build_site.github_web_url(wikilib.remote_url(REPO)))

    # 1. Scene pages, and the real command output for terminal scenes
    urls: dict[str, list[str]] = {}
    transcript = {}
    for scene in spec["scenes"]:
        kind = scene["kind"]
        if kind in {"page", "datasette"}:
            continue
        if kind == "file":
            urls[scene["id"]] = []
            for number, (first, last) in enumerate(file_ranges(scene), start=1):
                page = run_dir / "html" / f"{scene['id']}-{number}.html"
                page.write_text(file_html(scene, first, last), encoding="utf-8")
                urls[scene["id"]].append(page.as_uri())
            continue
        if kind == "card":
            texts = [card_html(scene)]
        else:
            texts, transcript[scene["id"]] = terminal_html(scene, tmp)
        urls[scene["id"]] = []
        for number, text in enumerate(texts, start=1):
            page = run_dir / "html" / f"{scene['id']}-{number}.html"
            page.write_text(text, encoding="utf-8")
            urls[scene["id"]].append(page.as_uri())
    (run_dir / "terminal-transcript.json").write_text(json.dumps(transcript, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    # A scene that demonstrates a refusal lists the commands that must fail (`expect_fail`: 1-based positions).
    must_fail = {scene["id"]: set(scene.get("expect_fail", [])) for scene in spec["scenes"]}
    failed = [f"{sid}: `{item['command']}` exited {item['exit_code']}" for sid, items in transcript.items()
              for position, item in enumerate(items, start=1) if (item["exit_code"] != 0) != (position in must_fail[sid])]
    if failed:
        print("Commands that failed unexpectedly:\n  " + "\n  ".join(failed), file=sys.stderr)
        return 1
    print(f"ran {sum(len(v) for v in transcript.values())} terminal commands")

    # 2. Frames
    frames = record(spec, urls, site.as_uri(), captions=not args.no_captions)
    print(f"captured {sum(len(beat) for beats in frames.values() for beat in beats)} frames")

    # 3. Narration audio and scene durations
    durations: dict[str, float] = {}
    audio: dict[str, Path | None] = {}
    for scene in spec["scenes"]:
        wav = run_dir / "audio" / f"{scene['id']}.wav"
        if not args.no_voice and speak(scene["narration"], spec.get("voice", "Samantha"), wav, spec.get("voice_rate")):
            audio[scene["id"]] = wav
            durations[scene["id"]] = media_seconds(wav) + PAD_SECONDS
        else:
            audio[scene["id"]] = None
            durations[scene["id"]] = estimate_seconds(scene, spec.get("words_per_minute", 150))
    voiced = sum(1 for value in audio.values() if value)
    if 0 < voiced < len(spec["scenes"]):
        print(f"warning: only {voiced} of {len(spec['scenes'])} scenes got a voice", file=sys.stderr)
    print(f"narration: {'text-to-speech voice' if voiced else 'no voice (captions only), timed from word counts'}")

    # 4. Scene videos, then one file
    segments = []
    for scene in spec["scenes"]:
        timed: list[tuple[Path, float]] = []
        for beat_frames, seconds in zip(frames[scene["id"]], beat_seconds(scene, durations[scene["id"]])):
            timed += [(png, held) for (png, _), held in zip(beat_frames, frame_seconds(beat_frames, seconds))]
        segment = run_dir / "video" / f"{scene['id']}.mp4"
        scene_video(timed, audio[scene["id"]], durations[scene["id"]], segment)
        segments.append(segment)
    listing = run_dir / "video" / "all.txt"
    listing.write_text("".join(f"file '{segment}'\n" for segment in segments), encoding="utf-8")
    final = run_dir / ("demo-short.mp4" if args.short else "demo-draft.mp4")
    completed = run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(listing),
                     "-c", "copy", "-movflags", "+faststart", str(final)])
    if completed.returncode != 0:
        print(f"ffmpeg could not join the scenes:\n{completed.stderr[-800:]}", file=sys.stderr)
        return 1
    write_srt(spec, durations, final.with_suffix(".srt"))
    (run_dir / "timings.json").write_text(json.dumps(durations, indent=2) + "\n", encoding="utf-8")
    # demo/script.md keeps its estimated timings whether or not a voice was made, so that it is a pure function of
    # scenes.yaml and never differs between two machines. The measured timings are in demo/out/timings.json.
    total = media_seconds(final)
    print(f"wrote {final.relative_to(REPO)}: {clock(total)} ({total:.0f} s), {int(WIDTH * SCALE)}x{int(HEIGHT * SCALE)}, "
          f"{len(segments)} scenes, {'with' if voiced else 'no'} voice, captions {'off' if args.no_captions else 'on'}")
    print(f"wrote {final.with_suffix('.srt').relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

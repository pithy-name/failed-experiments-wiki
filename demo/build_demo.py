"""Build the demo: the narration script and a draft screen recording.

  python demo/build_demo.py --script-only     # demo/script.md only (needs nothing extra)
  python demo/build_demo.py                   # script + demo/out/demo-draft.mp4 (+ .srt)
  python demo/build_demo.py --no-voice        # silent video, timed from word counts
  python demo/build_demo.py --placeholder     # no Chrome: flat frames, to test the assembly

What the video is, plainly: a sequence of real screens assembled into a video.
Every frame is a screenshot taken by headless Chrome of (a) the real browse
page loaded from a filter link, (b) a real file from the repository, (c) the
real output of commands run at build time, or (d) a title card. It is not a
live capture of someone clicking: there is no mouse pointer and no typing.
The voice is a text-to-speech scratch track for timing, meant to be replaced.

Needs: Google Chrome (or CHROME=/path/to/binary), ffmpeg, and macOS `say` for
the voice. Chrome and `say` cannot run inside the Claude Code sandbox (Chrome
must bind a local socket), so run this from a normal terminal.

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

import build_site  # noqa: E402
import wikilib  # noqa: E402

WIDTH, HEIGHT, SCALE = 1280, 720, 1.5       # CSS pixels and device scale: frames are 1920x1080
FPS = 30
PAD_SECONDS = 0.9                             # silence after each scene's narration
CHROME_CANDIDATES = [
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
    "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser",
]

CSS = """
* { box-sizing: border-box; }
html, body { margin: 0; width: 1280px; height: 720px; overflow: hidden; }
body { font: 20px/1.45 -apple-system, "Helvetica Neue", Arial, sans-serif; color: #e9ecef; background: #14171a; }
.card { display: flex; flex-direction: column; justify-content: center; height: 720px; padding: 0 110px; }
.card h1 { font-size: 54px; line-height: 1.15; margin: 0 0 18px; color: #ffffff; }
.card .subtitle { font-size: 30px; color: #a9c7e8; margin: 0 0 28px; }
.card ul { list-style: none; margin: 10px 0 0; padding: 0; }
.card li { font-size: 30px; line-height: 1.35; margin: 0 0 22px; padding-left: 34px; position: relative; }
.card li:before { content: ""; position: absolute; left: 0; top: 16px; width: 14px; height: 14px; border-radius: 3px; background: #6fb1f2; }
.card .footer { position: absolute; left: 110px; right: 110px; bottom: 48px; font-size: 19px; color: #8a96a3; }
.bar { height: 46px; line-height: 46px; padding: 0 22px; background: #23282e; color: #aeb8c2; font: 17px/46px ui-monospace, Menlo, monospace; border-bottom: 1px solid #343b43; white-space: nowrap; overflow: hidden; }
.bar b { color: #ffffff; font-weight: 600; }
pre { margin: 0; padding: 16px 22px; font: 16px/1.42 ui-monospace, Menlo, monospace; white-space: pre; overflow: hidden; height: 674px; }
pre.wrap { white-space: pre-wrap; overflow-wrap: anywhere; }
.ln { color: #5d6875; user-select: none; }
.prompt { color: #7fd491; }
.cmd { color: #ffffff; font-weight: 600; }
.exit-bad { color: #ff9b8f; }
.more { color: #8a96a3; }
"""


# --------------------------------------------------------------------------
# Scenes and facts
# --------------------------------------------------------------------------


def load_scenes() -> dict:
    with (DEMO / "scenes.yaml").open(encoding="utf-8") as handle:
        return yaml.safe_load(handle)


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
    return {
        "entries": len(list((REPO / "entries").glob("fe-*.md"))),
        "posts_classified": len(labels),
        "genuine_writeups": sum(1 for row in labels if row["label"] == "yes"),
        "full_field_posts": sum(1 for audit in audits if audit["passes_machine_checks"]),
        "contribute_accuracy_percent": round(100 * (results["contribute"]["overall_accuracy"] or 0)),
        "ask_passed": results["ask"]["passed"],
        "ask_total": results["ask"]["total"],
        "gold_verified": sum(1 for status in gold if status == "verified"),
        "has_github_remote": bool(build_site.github_web_url(wikilib.remote_url(REPO))),
    }


def stale_facts(spec: dict) -> list[str]:
    actual = repo_facts()
    return [
        f"{key}: the narration assumes {value!r}, the repository now says {actual.get(key)!r}"
        for key, value in (spec.get("facts") or {}).items()
        if actual.get(key) != value
    ]


def words(text: str) -> int:
    return len(text.split())


def estimate_seconds(scene: dict, wpm: int) -> float:
    return words(scene["narration"]) * 60 / wpm + PAD_SECONDS


def clock(seconds: float) -> str:
    return f"{int(seconds // 60)}:{int(seconds % 60):02d}"


# --------------------------------------------------------------------------
# The script document
# --------------------------------------------------------------------------


def on_screen(scene: dict) -> str:
    kind = scene["kind"]
    if kind == "card":
        return "Title card: " + scene["title"]
    if kind == "page":
        links = [("#" + state["link"]) if state["link"] else "no filters" for state in scene["states"]]
        return "The browse page (`site/index.html`): " + ", then ".join(f"`{link}`" for link in links)
    if kind == "file":
        spans = ", then ".join(f"{first}–{last}" for first, last in file_ranges(scene))
        return f"File `{scene['path']}`, lines {spans}"
    return "Terminal, real output of: " + "; ".join(f"`{command}`" for command in scene["commands"])


def write_script(spec: dict, durations: dict[str, float] | None = None) -> Path:
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
        "- **On screen** is what the draft video shows for that scene. Every frame is a real page state, a real file or real command output.",
        "- **Update when** flags lines that are true today and will need changing as the project moves.",
        f"- Timings are {'measured from the generated voice track' if durations else f'estimated at {wpm} words a minute'}, plus {PAD_SECONDS} s of pause per scene.",
        f"- Narration length: {total_words} words.",
        "",
        "## What the draft video is, and is not",
        "",
        "- It is a sequence of real screens assembled into a video: `demo/out/demo-draft.mp4`, with subtitles in `demo/out/demo-draft.srt`.",
        "- It is not a live capture. There is no mouse pointer and nothing is typed on screen. Filter changes appear as cuts between page states.",
        "- The voice is macOS text-to-speech, there only so you can judge pacing. Record your own over it, or re-record the screens live using this script.",
        "- It shows no GitHub screens and no Claude Code session, because neither exists yet for this project: there is no remote, and the plugin has not been loaded. Scenes 7 to 10 and 12 show the local equivalent and the narration says so where it matters.",
        "",
        "## Scenes",
        "",
    ]
    start = 0.0
    for number, scene in enumerate(spec["scenes"], start=1):
        seconds = (durations or {}).get(scene["id"]) or estimate_seconds(scene, wpm)
        lines += [
            f"### {number}. `{scene['id']}` · {clock(start)}–{clock(start + seconds)} ({seconds:.0f} s)",
            "",
            f"**On screen:** {on_screen(scene)}",
            "",
            "**Narration:**",
            "",
            "> " + " ".join(scene["narration"].split()),
            "",
        ]
        if scene.get("update_when"):
            lines += [f"**Update when:** {scene['update_when']}", ""]
        start += seconds
    lines += [
        f"**Total: {clock(start)}** ({start:.0f} s).",
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
        "Once the repository is on GitHub and the plugin loads in Claude Code, these scenes are better recorded live:",
        "",
        "| Scene | Record instead |",
        "|---|---|",
        "| 7–9 (ask) | A Claude Code session with the plugin: type the plan from scene 7, show the five-part answer; then the debate question from scene 9. |",
        "| 10 (contribute) | Same session: \"Contribute this post: <a LessWrong URL not yet in the wiki>\". Show the pull request it opens, with the badges. |",
        "| 11 (validate) | The failed check on that pull request, or the same terminal commands. |",
        "| 12 (human path) | GitHub → Issues → New entry: submit the form, show the pull request the workflow opens. |",
        "| 13 (review) | Run the human review command live (see `TODO.md`), then `git log --oneline --grep Review`. |",
        "| 14 (Datasette) | `make datasette`, then the entries table with its facets in a browser. |",
        "",
    ]
    path = DEMO / "script.md"
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


# --------------------------------------------------------------------------
# Scene HTML
# --------------------------------------------------------------------------


def scrub(text: str, tmp: Path) -> str:
    """Keep machine-specific paths, and the user's name with them, off the screen."""
    text = text.replace(str(tmp), "$TMP").replace(str(REPO), ".")
    home = str(Path.home())
    return text.replace(home, "~")


# Shrinks the text of a file or terminal scene until it fits the frame, so nothing is cut off silently.
FIT_SCRIPT = """
(function () {
  var pre = document.querySelector("pre");
  if (!pre) { return; }
  var size = 16;
  while (pre.scrollHeight > pre.clientHeight && size > 9) { size -= 0.5; pre.style.fontSize = size + "px"; }
  if (pre.scrollHeight > pre.clientHeight) { document.title = "OVERFLOW"; }
})();
"""


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
    rows = []
    for number in range(first, last + 1):
        rows.append(f'<span class="ln">{number:>3}  </span>{html.escape(all_lines[number - 1])}')
    wrap = " wrap" if scene.get("wrap") else ""
    bar = f'<div class="bar"><b>{html.escape(scene["path"])}</b> &nbsp; lines {first}–{last} of {len(all_lines)}</div>'
    return page_html(bar + f'<pre class="file{wrap}">' + "\n".join(rows) + "</pre>")


def terminal_html(scene: dict, tmp: Path) -> tuple[str, list[dict]]:
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
    return page_html(bar + f"<pre{wrap}>" + "\n\n".join(blocks) + "</pre>"), record


# --------------------------------------------------------------------------
# Frames, audio, video
# --------------------------------------------------------------------------


def find_chrome() -> str | None:
    override = os.environ.get("CHROME")
    if override:
        return override
    return next((path for path in CHROME_CANDIDATES if Path(path).exists()), None)


def run(args: list[str], **kwargs) -> subprocess.CompletedProcess:
    return subprocess.run(args, capture_output=True, text=True, **kwargs)


def screenshot(chrome: str, url: str, png: Path, profile: Path) -> None:
    completed = run(
        [
            chrome, "--headless=new", "--disable-gpu", "--no-first-run", "--no-default-browser-check", "--disable-extensions",
            f"--user-data-dir={profile}", f"--window-size={WIDTH},{HEIGHT}", f"--force-device-scale-factor={SCALE}",
            "--hide-scrollbars", "--virtual-time-budget=4000", f"--screenshot={png}", url,
        ],
        timeout=180,
    )
    if not png.exists() or png.stat().st_size == 0:
        tail = "\n".join(line for line in completed.stderr.splitlines() if "crashpad" not in line)[-600:]
        raise SystemExit(
            f"Chrome did not produce {png.name}.\n{tail}\n"
            "If this ran inside the Claude Code sandbox: Chrome cannot bind its local socket there. Run it from a normal terminal."
        )


def placeholder_frame(png: Path, index: int) -> None:
    colour = ["0x1e2a38", "0x2a1e38", "0x1e3828", "0x38301e"][index % 4]
    run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "lavfi", "-i",
         f"color=c={colour}:s={int(WIDTH * SCALE)}x{int(HEIGHT * SCALE)}", "-frames:v", "1", str(png)], check=True)


def media_seconds(path: Path) -> float:
    completed = run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)])
    try:
        return float(completed.stdout.strip())
    except ValueError:
        return 0.0


def speak(text: str, voice: str, wav: Path) -> bool:
    """macOS text-to-speech into a WAV file. False if `say` is missing or produced nothing."""
    if not shutil.which("say"):
        return False
    aiff = wav.with_suffix(".aiff")
    run(["say", "-v", voice, "-o", str(aiff), " ".join(text.split())], timeout=300)
    if not aiff.exists() or media_seconds(aiff) < 0.5:
        return False
    run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", str(aiff), "-ar", "44100", "-ac", "1", str(wav)], check=True)
    return wav.exists()


def scene_video(frames: list[Path], audio: Path | None, seconds: float, out: Path, work: Path) -> None:
    """One scene: its frames shown for equal shares of `seconds`, with its narration (or silence)."""
    share = seconds / len(frames)
    listing = work / f"{out.stem}.txt"
    rows = []
    for frame in frames:
        rows += [f"file '{frame}'", f"duration {share:.3f}"]
    rows.append(f"file '{frames[-1]}'")          # the concat demuxer needs the last file repeated
    listing.write_text("\n".join(rows) + "\n", encoding="utf-8")
    command = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(listing)]
    if audio:
        command += ["-i", str(audio), "-af", "apad"]
    else:
        command += ["-f", "lavfi", "-i", "anullsrc=r=44100:cl=mono"]
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
    """Subtitles: each scene's narration split into sentences, timed by word count within the scene."""
    blocks, start, index = [], 0.0, 1
    for scene in spec["scenes"]:
        seconds = durations[scene["id"]]
        sentences = [s.strip() for s in re.split(r"(?<=[.!?:])\s+", " ".join(scene["narration"].split())) if s.strip()]
        total = sum(words(s) for s in sentences) or 1
        speaking = max(seconds - PAD_SECONDS, 0.5)
        cursor = start
        for sentence in sentences:
            length = speaking * words(sentence) / total
            blocks.append(f"{index}\n{srt_time(cursor)} --> {srt_time(cursor + length)}\n{sentence}\n")
            cursor += length
            index += 1
        start += seconds
    path.write_text("\n".join(blocks), encoding="utf-8")


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build the demo script and the draft video.")
    parser.add_argument("--script-only", action="store_true", help="write demo/script.md and stop")
    parser.add_argument("--html-only", action="store_true", help="also render the scene pages and run the commands, but take no screenshots")
    parser.add_argument("--no-voice", action="store_true", help="silent video, timed from word counts")
    parser.add_argument("--placeholder", action="store_true", help="flat colour frames instead of Chrome screenshots (tests the assembly)")
    parser.add_argument("--allow-stale", action="store_true", help="build even if a number in the narration is out of date")
    args = parser.parse_args(argv)

    spec = load_scenes()
    stale = stale_facts(spec)
    if stale:
        print("Numbers in the narration are out of date (update demo/scenes.yaml):\n  " + "\n  ".join(stale), file=sys.stderr)
        if not args.allow_stale:
            return 1

    script = write_script(spec)
    print(f"wrote {script.relative_to(REPO)}")
    if args.script_only:
        return 0

    for folder in ("html", "frames", "audio", "video", "tmp", "site"):
        (OUT / folder).mkdir(parents=True, exist_ok=True)
    tmp = OUT / "tmp"
    site = OUT / "site" / "index.html"
    build_site.build(REPO / "entries", site, build_site.github_web_url(wikilib.remote_url(REPO)))

    chrome = None
    if not (args.html_only or args.placeholder):
        chrome = find_chrome()
        if not chrome:
            print("Google Chrome was not found. Set CHROME=/path/to/browser or use --placeholder.", file=sys.stderr)
            return 1
        for tool in ("ffmpeg", "ffprobe"):
            if not shutil.which(tool):
                print(f"{tool} is not installed.", file=sys.stderr)
                return 1

    # 1. Scene pages (and the real command output for terminal scenes)
    targets: dict[str, list[str]] = {}
    transcript = {}
    for scene in spec["scenes"]:
        kind = scene["kind"]
        if kind == "page":
            targets[scene["id"]] = [site.as_uri() + ("#" + state["link"] if state["link"] else "") for state in scene["states"]]
            continue
        if kind == "file":
            targets[scene["id"]] = []
            for number, (first, last) in enumerate(file_ranges(scene), start=1):
                page = OUT / "html" / f"{scene['id']}-{number}.html"
                page.write_text(file_html(scene, first, last), encoding="utf-8")
                targets[scene["id"]].append(page.as_uri())
            continue
        if kind == "card":
            text = card_html(scene)
        else:
            text, transcript[scene["id"]] = terminal_html(scene, tmp)
        page = OUT / "html" / f"{scene['id']}.html"
        page.write_text(text, encoding="utf-8")
        targets[scene["id"]] = [page.as_uri()]
    (OUT / "terminal-transcript.json").write_text(json.dumps(transcript, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    failed = [f"{sid}: `{item['command']}` exited {item['exit_code']}" for sid, items in transcript.items() for item in items
              if item["exit_code"] != 0 and "bad_luck" not in item["output"] and "fe-2026-0008.md --quotes" not in item["command"]]
    print(f"rendered {len(targets)} scenes; terminal commands run: {sum(len(v) for v in transcript.values())}")
    if failed:
        print("Commands that failed unexpectedly:\n  " + "\n  ".join(failed), file=sys.stderr)
        return 1
    if args.html_only:
        print(f"scene pages are in {(OUT / 'html').relative_to(REPO)}/ (no screenshots taken)")
        return 0

    # 2. Frames
    frames: dict[str, list[Path]] = {}
    index = 0
    for scene in spec["scenes"]:
        frames[scene["id"]] = []
        for state_number, url in enumerate(targets[scene["id"]], start=1):
            png = OUT / "frames" / f"{scene['id']}-{state_number}.png"
            if args.placeholder:
                placeholder_frame(png, index)
            else:
                screenshot(chrome, url, png, OUT / "chrome-profile")
            frames[scene["id"]].append(png)
            index += 1
    print(f"captured {index} frames")

    # 3. Narration audio and scene durations
    durations: dict[str, float] = {}
    audio: dict[str, Path | None] = {}
    voiced = 0
    for scene in spec["scenes"]:
        wav = OUT / "audio" / f"{scene['id']}.wav"
        if not (args.no_voice or args.placeholder) and speak(scene["narration"], spec.get("voice", "Samantha"), wav):
            audio[scene["id"]] = wav
            durations[scene["id"]] = media_seconds(wav) + PAD_SECONDS
            voiced += 1
        else:
            audio[scene["id"]] = None
            durations[scene["id"]] = estimate_seconds(scene, spec.get("words_per_minute", 150))
    print(f"narration: {voiced} of {len(spec['scenes'])} scenes voiced" + ("" if voiced else " (silent video, timed from word counts)"))

    # 4. Scene videos, then one file
    segments = []
    for scene in spec["scenes"]:
        segment = OUT / "video" / f"{scene['id']}.mp4"
        scene_video(frames[scene["id"]], audio[scene["id"]], durations[scene["id"]], segment, OUT / "video")
        segments.append(segment)
    listing = OUT / "video" / "all.txt"
    listing.write_text("".join(f"file '{segment}'\n" for segment in segments), encoding="utf-8")
    final = OUT / ("demo-placeholder.mp4" if args.placeholder else "demo-draft.mp4")
    completed = run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(listing),
                     "-c", "copy", "-movflags", "+faststart", str(final)])
    if completed.returncode != 0:
        print(f"ffmpeg could not join the scenes:\n{completed.stderr[-800:]}", file=sys.stderr)
        return 1
    write_srt(spec, durations, final.with_suffix(".srt"))
    if voiced == len(spec["scenes"]):
        write_script(spec, durations)       # replace estimated timings with measured ones
    total = media_seconds(final)
    print(f"wrote {final.relative_to(REPO)}: {clock(total)} ({total:.0f} s), {int(WIDTH * SCALE)}x{int(HEIGHT * SCALE)}, {len(segments)} scenes")
    print(f"wrote {final.with_suffix('.srt').relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

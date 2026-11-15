# TODO

What is left for the maintainer, shortest task first. Moved here from `DONE.md`
on 2026-11-15, which now holds only what was built and how it was verified.

IDs are stable: `DONE.md`, the decision log and the demo script refer to tasks
by ID. A finished task stays in the table, marked DONE, so the record is kept.

| ID | Task | Time | Status |
|---|---|---|---|
| T1 | Load the commit history | 1 min | **DONE** 2026-11-14 |
| T2 | Set your GitHub handle | 1 min | open |
| T3 | Decide on the exception post | 2 min | open |
| T4 | Do the human review (D3) | 5 min | open |
| T5 | Look at both browse UIs and pick one | 5 min | open |
| T9 | Build the draft demo video and review the script | 5 min + your review | open |
| T6 | Put it on GitHub | 10–20 min | open |
| T7 | Verify the 5 gold entries | 45–60 min | open |
| T8 | Load the plugin once | 5 min | open |

Run every command from the repository root.

## T1. Load the commit history — DONE

You ran `git init -b main` in this folder at the end of the build session, and
the rest was then run for you: `git fetch --update-head-ok history.bundle
'+refs/heads/*:refs/heads/*' '+refs/tags/*:refs/tags/*'` and `git reset`.
Result: `git status` clean, 51 commits, 12 branches, tag `pre-seed`.

The procedure was first tested on a scratch copy with the same partial `.git/`
directory (DEC-54), then run for real here (DEC-55).

`history.bundle` is now only a spare copy of the history. It was moved to
`_trash-review/history.bundle` on 2026-11-15 at your request. Delete it when
you no longer want it.

## T2. Set your GitHub handle

`make set-handle HANDLE=<your handle>` then commit as it prints.

All 15 entries carry `contributor.handle: HANDLE-TBD`, because the build session
could not read your `gh` login. Your git user name is `pithy-name`; whether that
is also your GitHub handle was not assumed.

## T3. Decide on the exception post

Your rule: a post qualifies only if it supports every required field. "Some
negative steganography results" does not: it asks a question and states no
prediction. Two entries rest on it, `fe-2026-0010` and `fe-2026-0011`, and both
say plainly that the post poses a question.

- Keep them: nothing to do.
- Back them out: `git revert -m 1 c20c7d1` then `git revert -m 1 61b12aa`, then
  `make site`. That leaves 13 entries from 9 posts. The demo opens
  `fe-2026-0010` in scene 5, so `demo/scenes.yaml` would need another entry there.

## T4. Do the human review (D3)

1. `.venv/bin/python tools/cli.py get fe-2026-0008` and open its `source.url` (a short post).
2. Check each field against the post. `plugin/skills/review/SKILL.md` step 3 is the checklist.
3. Record it:
   `.venv/bin/python tools/cli.py review fe-2026-0008 reviewed --human --handle <your handle> --notes "Checked every field against the post."`
   Use `contested`, and say which field, if something is wrong.
4. With a remote this opens a pull request. Without one:
   `.venv/bin/python tools/cli.py merge-local <the branch it printed>`
5. `git log --oneline --grep Review` shows it.

## T5. Look at both browse UIs and pick one

- `make site`, then open `site/index.html`.
- `make datasette`, then open http://localhost:8001/wiki/entries.

Recommendation: the web page (see `DONE.md`, D4). Nobody has seen either one
rendered in a real browser yet, so check before recording anything. A filtered
view of the page can now be shared as a link: the filters are in the URL after `#`.

## T9. Build the draft demo video and review the script

1. Read `demo/script.md`: the narration, scene by scene, with timings and the
   lines that will need updating. Edit the wording in `demo/scenes.yaml`.
2. Build the video from a normal terminal (not from inside Claude Code's
   sandbox, where Chrome cannot start): `make demo-video`
   This takes a minute or two and writes `demo/out/demo-draft.mp4` and
   `demo/out/demo-draft.srt`.
3. Watch it. It is a draft for pacing and content: real screens, no mouse
   pointer, a text-to-speech voice. Then either record your own voice over it,
   or record the screens live with the script (`demo/live-demo-script.md`).

Not yet verified by anyone: the screenshot step and the voice step have never
run. Everything before and after them has (scene pages, real command output,
video assembly with placeholder frames).

## T6. Put it on GitHub

1. `gh repo create failed-experiments-wiki --private --source . --push`, then `git push origin --all --tags`.
2. Watch the first "Validate entries" run in the Actions tab (D7).
3. Settings → Actions → General → allow GitHub Actions to create and approve pull requests.
4. Create the label `new-entry`.
5. Issues → New issue → New entry: submit one, and watch the pull request appear (D2).
6. `make site` again, so entry links point to GitHub.

This gives no pull requests for the existing agent entries, because their
branches are already merged. For a real pull request in the demo, contribute a
new post (D1). An alternative that has not been tested: push `main` first at
commit `291c14b` (the last commit before the agent entries), then push the
`entry/*` branches and open pull requests from them, then push the full `main`.

Before the repository ever goes public: it contains your first name in a field
value (`pending_maintainer_verification`) and in the decision log.

## T7. Verify the 5 gold entries

For each `evals/gold/fe-2026-000N.md`:

1. Open its post.
2. Use the "Verification notes for the maintainer" at the bottom of the file.
   They give line numbers into the cached post text in `.cache/lw/text/`.
3. Correct any field. Set `gold_status: verified`.

Then `make validate-gold`, `make sync-gold HANDLE=<your handle>`, commit, and
`make evals`. Text fields you changed show as STALE: `evals/README.md` gives the
one prompt that regrades them.

Two rules to decide across the set, because the skill and the gold drafts
differ on both and much of the scored disagreement comes from them:

- May well-known facts that the post does not state (for example a model's
  developer) be filled in?
- Should `retry_welcome` be true for a medium-confidence negative?

After this, update `demo/scenes.yaml` (the `facts`, and scenes 3 and 15).

## T8. Load the plugin once

Try `claude --plugin-dir plugin` from the repository root. That flag was not
confirmed against the Claude Code documentation; if it is wrong, add the folder
through `/plugin`. Check that the MCP server starts and the three skills appear.

The server itself starts and answers (`make mcp-smoke`). What is untested is
Claude Code loading it.

## Leftovers to remove when you like

Nothing was deleted during the build. These are yours to remove:

- `_trash-review/history.bundle`: spare copy of the commit history (T1).
- `_trash-review/` also holds three empty or six-byte probe files from testing
  whether the folder was writable.
- `demo/out/`: demo build outputs, including a placeholder video from testing
  the assembly. Git-ignored. `make demo-video` writes its own files there.

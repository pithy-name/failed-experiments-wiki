# TODO

What is left for the maintainer. Moved here from `DONE.md`
on 2026-11-15, which now holds only what was built and how it was verified.

IDs are stable: `DONE.md`, the decision log and the demo script refer to tasks
by ID. A finished task stays in the table, marked DONE, so the record is kept.

| ID | Task | Time | Status |
|---|---|---|---|
| T1 | Load the commit history | 1 min | **DONE** 2026-11-14 |
| T2 | Set your GitHub handle | 1 min | **DONE** 2026-11-15 (set to your `gh` login; see T11) |
| T3 | Decide on the exception post | 2 min | open |
| T4 | Do the human review (D3) | 5 min | open. Printable: `_print/posts/post-08-0008.md` (`make print-pack`) |
| T5 | Look at both browse UIs and pick one | 5 min | open |
| T6 | Put it on GitHub | 10–20 min | step 1 **DONE by you** 2026-11-15 (the repository is now public). Step 2 **DONE**: the validation Action's first run failed on a test-suite bug (since fixed); every run since has passed. Step 3 **DONE by you** and step 4 **DONE** 2026-11-16 (Actions may open pull requests; the `new-entry` label exists). Open: steps 5 and 6 (no issue filed yet) |
| T7 | Verify the 5 gold entries | 45–60 min | open. Printable, with each field's passage marked in the post: `_print/posts/post-01` to `post-05` |
| T8 | Load the plugin once | 5 min | **DONE** 2026-11-15, headless (an interactive try is optional) |
| T9 | Review the demo script and the two cuts of the video | 10 min + your edits | short cut **watched by you** 2026-11-15; script edits still open |
| T10 | Choose a licence | 5 min | open |
| T11 | Confirm or undo two changes made for you overnight | 3 min | (b) the handle: **confirmed by you** 2026-11-15. (a) the reference entries' label: open |
| T12 | File the first human entry through the form | 10–15 min | open. Also T6 step 5 |
| T13 | Tidy the Method list | 10 min | open |
| T14 | Decide on three proposed form and schema changes | 5 min | open |
| T15 | Decide whether to rename the repository and plugin | 2 min | open |
| T16 | Move dependencies to `pyproject.toml` | 30 min | open |
| T17 | Record who made each decision | 1–2 hours | open |
| T18 | Remove spec references from generated output | 20 min | open |

Run every command from the repository root.

## T1. Load the commit history — DONE

You ran `git init -b main` in this folder at the end of the build session, and
the rest was then run for you: `git fetch --update-head-ok history.bundle
'+refs/heads/*:refs/heads/*' '+refs/tags/*:refs/tags/*'` and `git reset`.
Result on 2026-11-14: `git status` clean, 51 commits, 12 branches, tag `pre-seed`. (Now: tags `pre-seed` and `poc-0.0.1`; count commits with `git rev-list --count HEAD`.)

The procedure was first tested on a scratch copy with the same partial `.git/`
directory (DEC-54), then run for real here (DEC-55).

## T2. Set your GitHub handle — DONE

Done on 2026-11-15: `gh api user` returned `pithy-name`, and
`tools/set_handle.py` replaced the placeholder in the entries and the gold
files. Confirm or undo under T11 (b).

What this task said before (kept for the record): "`make set-handle
HANDLE=<your handle>` then commit as it prints. All 15 entries carry
`contributor.handle: HANDLE-TBD`, because the build session could not read
your `gh` login. Your git user name is `pithy-name`; whether that is also your
GitHub handle was not assumed."

## T3. Decide on the exception post

Your rule: a post qualifies only if it supports every required field. "Some
negative steganography results" does not: it asks a question and states no
prediction. Two entries rest on it, `fe-2026-0010` and `fe-2026-0011`, and both
say plainly that the post poses a question.

- Keep them: nothing to do.
- Back them out (untested): `git revert -m 1 6fb495c` then `git revert -m 1 e032ad5`. Later
  commits `cfa27a6` and `61409d9` edit the same two entries, so expect conflicts; if so,
  `git rm entries/fe-2026-0010.md entries/fe-2026-0011.md` and commit. Then
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

Recommendation: the web page (see `DONE.md`, D4). A filtered view of the page
can be shared as a link: the filters and the opened entry are in the URL after `#`.

Both were rendered and checked in headless Chromium on 2026-11-15, Datasette
also on a real port (`VERIFICATION.md`). Screenshots of every state are in
`demo/out/verify/screens/` (regenerate with
`.venv/bin/python -m pytest tests/test_e2e_browser.py --snap-dir demo/out/verify/screens`).
What is left is your own look, and any browser other than Chromium.

## T6. Put it on GitHub

1. `gh repo create failed-experiments-wiki --private --source . --push`, then `git push origin --all --tags`. **DONE** 2026-11-15; the repository is public.
2. Watch the first "Validate entries" run in the Actions tab (D7). **DONE** 2026-11-15.
3. Settings → Actions → General → allow GitHub Actions to create and approve pull requests. **DONE** 2026-11-16.
4. Create the label `new-entry`. **DONE** 2026-11-16, with `gh label create new-entry`.
5. Issues → New issue → New entry: submit one, and watch the pull request appear (D2). T12 is one way to do it.
6. `make site` again, so entry links point to GitHub.

This gives no pull requests for the existing agent entries, because their
branches were merged before the push. The `entry/*` and `review/*` branches are
on the remote, but no pull request exists for any of them. For a real pull
request in the demo, contribute a new post (D1).

The repository is public. Tracked files outside `report/` contain no first
name; the `report/` drafts carry your by-line.

## T7. Verify the 5 gold entries

For each `evals/gold/fe-2026-000N.md`:

While unverified, each gold file and its copy in `entries/` is labelled as
written by an agent (T11 a). Verifying is what makes it yours.

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

A third thing to settle while you are in these files (DEC-67): two names are
spelled two ways across entries, so a filter on one spelling misses the other.

| Field | Spellings | Entries |
|---|---|---|
| `models.name` | `GPT-2 small` / `GPT-2-small` | `fe-2026-0002` / `fe-2026-0004` |
| `benchmarks` | `HarmBench` / `harmbench` | `fe-2026-0003` / `fe-2026-0001` |

Recommendation: `GPT-2 small` and `HarmBench`, changed in both the gold file and
its entry. Each post spells its own way, so this is a naming rule, not a correction.

After this, update `demo/scenes.yaml` (the `facts`, and the scenes `s03-browse` and `s15-evals`).

## T8. Load the plugin once — DONE, headless

Done on 2026-11-15 once the command sandbox was lifted: `claude --plugin-dir plugin`
is the right flag. Headless sessions started with it listed the six tools and the
three skills (as `failed-experiments-wiki:ask`, `:contribute`, `:review`), ran a
live search, and ran the `ask` skill on one question. The frames are in
`VERIFICATION.md` under `plugin-…-live`; rerun with `make verify PLUGIN=1`.

`claude plugin validate plugin` passes, with warnings for a missing author,
licence (T10) and icon.

Still open if you want it: an interactive session. (A live run of the
`contribute` and `review` skills through the plugin was done on 2026-11-15, in a
scratch clone: DEC-75.)

What this task said before (kept for the record): "Try `claude --plugin-dir plugin`
from the repository root. That flag was not confirmed against the Claude Code
documentation; if it is wrong, add the folder through `/plugin`. Check that the
MCP server starts and the three skills appear. The server itself starts and
answers (`make mcp-smoke`). What is untested is Claude Code loading it."

## T9. Review the demo script and the two cuts of the video

Three cuts exist, all with captions and a voice track:

| File | Length | For |
|---|---|---|
| `demo/out/demo-draft.mp4` | 6:34 | The five-to-seven-minute demo you asked for: every scene |
| `demo/out/demo-short.mp4` | 5:03 | The sprint form, which suggests three to five minutes. It leaves out the scenes marked *(not in the short cut)* in `demo/script.md` |
| `demo/out/demo-short-voice.mp4` | 4:53 | The narrated short cut, embedded in the README |

The full cut was rebuilt on 2026-11-15 and the short cuts on 2026-11-16, after a reviewer who was told nothing about the
project read the frames and the narration (DEC-70). Its findings, and what
changed for each, are in `reviews/README.md`.
The rewrite answers them; the frames were looked at again afterwards.

1. Read `demo/script.md`: the narration, scene by scene, with timings and the
   lines that will need updating. Edit the wording in `demo/scenes.yaml`.
2. Watch a cut. It shows the real page driven by real clicks, typing and
   scrolling in a headless browser, real Datasette pages, real files and real
   command output. The orange pointer ring and field outline are drawn by the
   recorder; motion is step by step. The plugin session and the two `ask`
   answers on screen are saved output of real headless Claude Code sessions.
3. Rebuild after editing: `make demo-video` and `make demo-short` (about a
   minute each; `make demo-setup` first on a machine without the browser).
4. Then either record your own voice over a clean picture
   (`.venv/bin/python demo/build_demo.py --no-captions --no-voice`), or record
   the screens live with `demo/live-demo-script.md`.

One finding the rewrite could not settle, because it is a question for you:
the video names no place to try the wiki, since the repository was private when its
frames were recorded. It is public now (DEC-81), so the closing scene could name it.

What this task said before (kept for the record): the draft was 6:11, captions
only; "the voice step has never run, so the timings in the script are
estimates". The voice has run since. The script keeps estimated timings on
purpose, so it is the same on every machine; a build's measured timings are in
`demo/out/timings.json`.

## T10. Choose a licence

The repository has none, and the plugin validator flags it (DEC-69). Decide
before the repository is shared or made public.

| Option | For the code | For the entries | Consequence |
|---|---|---|---|
| A (recommended) | MIT | CC BY 4.0 | Anyone may reuse both with credit. The usual pair for an open research tool with a data set. |
| B | MIT | CC BY-SA 4.0 | As A, but anything built from the entries must be shared the same way. |
| C | none | none | Nobody may legally reuse it. Fine while private; a problem once judged or public. |

Entries are short summaries in your own words plus quotes of 15 words or fewer
from posts whose authors keep their rights; a licence on the entries covers
your wording, not theirs. To apply A: add `LICENSE` (MIT) and `LICENSE-entries`
(CC BY 4.0) at the root and set `"license": "MIT"` in `plugin/.claude-plugin/plugin.json`.

## T11. Confirm or undo two changes made for you overnight

Both were made because every cold reviewer flagged them, and both change
something you had specified or left open. Each is one decision.

| # | What changed | Why | Keep (recommended) | Undo |
|---|---|---|---|---|
| a | The five reference ("gold") entries and their copies in `entries/` are labelled `contributor.type: agent` (model `claude-sonnet-5-5`, tool `gold-draft`) while unverified. You had asked for `type: human`, unreviewed, with a note. | Three reviewers told nothing about the project each read "written by human" next to "model draft" as a contradiction, and the agent-written count understated model authorship (DEC-71). | Nothing to do. When you verify an entry (T7), `make sync-gold` makes it yours: `type: human`, reviewed by you, exactly as before. | `git log --oneline --grep "Label the model-drafted reference"` lists the commits; `git revert` each, and the `sync_gold` commit "Refuse to file a model draft under a person". |
| b | Every entry's `contributor.handle`, and the one reviewer handle, are `pithy-name`: your `gh` login, readable once the sandbox was lifted. | The placeholder `HANDLE-TBD` read as broken attribution to every reviewer. This is what the tools do by themselves when `gh` is readable (DEC-72). | Nothing to do. | `make set-handle` only replaces the placeholder, so to change it, search and replace `handle: pithy-name` in `entries/` and `evals/gold/` with the handle you want, then `make validate`. (Reverting is messier: in the five reference entries the handle went in with the label commit.) |

Note for (b): your handle now sits on fifteen entries that a model wrote and
no person has reviewed, as "the accountable person". That is the design, and
the entries say `type: agent` beside it, but it is your name: decide before
the repository is shared.

## T12. File the first human entry through the form

No issue has been filed, so the issue-to-pull-request workflow has never run
(D2), and no form link has been opened in a browser (DEC-89). One submission
checks both.

1. Pick a post with a negative result that is not in the wiki yet.
2. Ask the `contribute` skill to draft the entry for you to submit yourself.
   It runs `tools/form_link.py` instead of submitting, and gives you the link.
3. Or, from a draft file: `.venv/bin/python tools/form_link.py --file <draft> --model <drafting model>`.
4. Paste the fields it prints under "PASTE THESE FIRST" (too long for the link),
   open the link, and check that the other text fields are filled.
5. Pick the dropdown and checkbox answers it lists, check and edit every field,
   and submit.
6. Watch the workflow open a pull request. Read the entry, then merge.

The entry is `contributor.type: human` with your handle, and its contributor
note names the drafting model. If a field did not fill from the link, say which:
`tools/form_link.py` may need to move it to the paste list. If the workflow fails,
copy an entry file by hand, `make validate`, and open a pull request.

## T13. Tidy the Method list

The form's Method list is every tag the entries already use, so it carries
their near-duplicates. A contributor who picks one splits a filter from the
other (findings 6 and 9 in the decision log).

| Overlap | Tags |
|---|---|
| Same method, two names | `sae`, `sparse-autoencoders` |
| Model as judge | `judge-evaluation`, `llm-as-judge-filtering` |
| Linear probes | `linear-probing`, `dense-linear-probing`, `logistic-regression` |

Recommendation: merge only the first row now (`sparse-autoencoders`); the
others may be meant as distinct. A merge changes the tag in the entries, the
form and, if you allow it, the gold entries (T7), then `make validate`,
`make site` and `make evals`. `make method-report` shows write-ins that are
ready to join the list.

## T14. Decide on three proposed form and schema changes

Raised while reviewing the form on 2026-11-16. You deferred (c); (a) and (b)
were explained but not approved.

| # | Change | For | Against |
|---|---|---|---|
| a | A field for what the confidence interval measures (`metric`) | The low and high numbers mean nothing without it | One more question on a long form |
| b | A field for the interval's level, such as 95% (`ci_level`) | Makes intervals comparable | No entry records an interval yet |
| c | `failure_type` as a multi-select | A result can have more than one failure type | Every entry, the schema, the filters and the eval scoring change |

Recommendation: a and b together, as optional fields; c only once entries
show they need it.

## T15. Decide whether to rename the repository and plugin

The README names the project "Carpe Ignota" (DEC-82), but the repository and
the plugin are still `failed-experiments-wiki`. Installed tool names depend on
the plugin name.

| Option | Consequence |
|---|---|
| A (recommended for now) | Keep both. Nothing breaks. |
| B | Rename the repository only. GitHub redirects the old URL; update the default in `tools/form_link.py` and run `make site`. |
| C | Rename both. Anyone who installed the plugin sees new tool names and must reinstall. |

## T16. Move dependencies to `pyproject.toml`

Python's standard place for them (PEP 621). Replace the `requirements*.txt`
files with `dependencies` plus `dev` and `demo` extras, and update every
`pip install -r`.

## T17. Record who made each decision

Add a "Decided by" column to `DECISION-LOG.md`: maintainer, builder agent, or a
later session at the maintainer's request. Fill it from evidence (the row, session
logs, git authors); where none exists, write "not recorded".

## T18. Remove spec references from generated output

`evals/run_evals.py`, `tools/scout/yields.py` and `tools/scout/selection.py`
write "the PRD" or "PRD section N" into `evals/results/` and `scouting/`, and
`scouting/selection.json` says it too. The spec is not tracked. Reword the
strings, then regenerate the output files.


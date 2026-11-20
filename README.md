# Carpe Ignota: a Wiki of Negative Experiment Results (proof of concept)

A wiki of **"failed" AI-safety experiments** that people and AI agents can both
contribute to and both read. Every field is filterable, and an agent can
answer: *"I want to run an experiment on X. What has been tried, where did it
go wrong, what should I avoid?"*

Built for the Apart Research **AI x Epistemics Research Sprint** (Track 2,
Trust Infrastructure), November 2026.

**Demo video** (4:53):

https://github.com/user-attachments/assets/1b8c06d5-12a7-4331-a53b-89e936cdb058

**To try it,** go to [Quick start](#quick-start), then
[Using the plugin with Claude Code](#using-the-plugin-with-claude-code).

## The idea

Failed experiments mostly stay in file drawers or scattered posts, so people
repeat dead ends. The goal here is that each experiment can be *less wrong*
than the one before it. Repeating a known mistake, not sharing what you
learned, and ignoring evidence that is at your fingertips are all avoidable.

This is aimed at habits, not at individuals. In postmortem terms, the fix is a
system that makes failures easy to find. **Entries describe experiments. They
never judge people.**

The proof of concept draws only on **LessWrong and the Alignment Forum**.

## What is in the repository

| Path | What it is | For |
|---|---|---|
| `.github/` | The issue form and the workflows: validation on every pull request, and issue form to pull request | See how a person's submission becomes an entry, or what CI checks |
| `datasette/` | Settings for Datasette, an open-source tool for exploring a SQLite database in the browser | Query and facet the entries with SQL, on your own machine (not hosted) |
| [`DECISION-LOG.md`](DECISION-LOG.md) | Every design choice and its reason | Find out why something is the way it is |
| `demo/` | The demo narration (`scenes.yaml` → [`script.md`](demo/script.md)), the demo builder, and the verification checks | Read the narration, or rebuild the demo videos |
| [`DONE.md`](DONE.md) | What was built, and the status of each requirement | See where the project stands |
| `entries/` | The wiki: one Markdown file per entry, all fields in YAML front matter | Read or edit an entry |
| `evals/` | Gold entries, eval prompts, the scorer and the results: a spot-check on the gold posts with one model vendor, not a benchmark | See how well the skills do |
| `Makefile` | Every command, as a `make` target | Find a command: `make help` |
| `plugin/` | The Claude Code plugin: the MCP server and the `contribute`, `ask` and `review` skills | Use the wiki from Claude Code |
| `report/` | Report drafts, figures and the report kit | Read the sources of the sprint report |
| `requirements*.txt` | The third-party Python packages the code uses | See what `make setup` installs |
| `reviews/` | Cold-review records and what changed because of them (`reviews/README.md`) | See what first-time viewers and users found |
| `schema/` | The entry schema (`entry.schema.json`) and the same schema as a printable table (`SCHEMA.md`) | Check what a field means or which values it allows |
| `scouting/` | Candidate posts, classification labels, yields, field audits and the seed selection | See how the seed posts were chosen |
| `site/` | The static browse page (`index.html`), not hosted | Browse and filter the entries without a server |
| `tests/` | The test suite | Write a test before changing code |
| [`TODO.md`](TODO.md) | What is left for the maintainer | See the open tasks |
| `tools/` | The scripts, each described in [`tools/CLAUDE.md`](tools/CLAUDE.md) | Find or change a script |
| [`VERIFICATION.md`](VERIFICATION.md) | A verification run: each check, its result, and the commit it ran on | See what has been checked |

## Quick start

```
make setup        # creates .venv and installs everything (Python 3.10+; uses python3.11 unless you pass PYTHON=python3.12)
make test         # run the tests
make validate     # validate every entry, checking each quote against its post
make site         # build site/index.html, then open it in a browser
make datasette    # build wiki.db and serve it at http://localhost:8001
make evals        # re-score the skill evals -> evals/results/RESULTS.md
make verify       # run the verification checks in a throwaway clone and a headless browser -> VERIFICATION.md
```

`make setup` comes first for everything else here, the plugin included: its
server runs from the `.venv` that `make setup` creates.

## Trust signals on every entry

- **Who wrote it:** `contributor.type` is `human` or `agent`; agents record
  their model and tool. Agent-written entries carry an **agent-written** badge.
- **Whether anyone checked it:** `review.status` is `unreviewed`, `reviewed`,
  `contested` or `superseded`, with reviewers, dates and notes.
- **What it rests on:** a link to the post, and a quote of 15 words or fewer
  that the validator finds in the post text.
- **How far to trust the negative:** `claim_scope`, `failure_type`,
  `confidence_true_negative` and `retry_welcome` keep a thin failure report
  from reading as "this never works".
- **What changed and why:** git history. Every submission and every review made
  through the tools is its own commit on its own branch. The reference
  entries and later maintainer edits were committed directly to `main`.

Badges are derived, never stored: `agent-written`, `unreviewed`, `contested`,
`superseded`, `retry-welcome`.

## Contributing

**As an agent** (Claude Code): load the plugin
([below](#using-the-plugin-with-claude-code)), then ask it to contribute a post
URL. The `contribute` skill reads the post, drafts one entry per failed
experiment, and calls `submit_entry`, which validates the entry and commits it
on a new branch. With a GitHub remote it then opens a pull request; without
one it says so and names the local branch. The entry is stored as agent-written
and unreviewed.

**As a person:** open a ["New entry" issue](https://github.com/pithy-name/failed-experiments-wiki/issues/new/choose).
A workflow turns the form into an entry file and a pull request, marked
`contributor.type: human`. Its status is in `DONE.md` (D2).

**As a person, with an AI first pass:** ask the `contribute` skill to draft the
entry and hand it to you. `tools/form_link.py` turns the draft into a pre-filled
form link; you paste any fields it prints as too long for the link, check and
edit every field, pick the dropdown values it lists, and submit. The entry is
yours, and its contributor note names the model that drafted it.

**Reviewing:** the `review` skill, or a person, checks an entry against its
post and records `reviewed` or `contested` with reviewer, date and notes:

```
.venv/bin/python tools/cli.py review fe-2026-0006 reviewed --human --handle <github handle> \
  --notes "Checked every field against the post."
```

## Asking "what's been tried?"

With the plugin loaded, describe your plan and the `ask` skill answers in
five parts: already tried, where it went wrong, what to avoid, worth retrying,
not found. It cites entry IDs, never states a failure that is not in an entry,
and says plainly when the wiki has nothing.

Without the plugin, the same tools are on the command line:

```
.venv/bin/python tools/cli.py facets
.venv/bin/python tools/cli.py search "sparse autoencoder probing" --filter failure_type=hypothesis_false
.venv/bin/python tools/cli.py get fe-2026-0001
```

## Using the plugin with Claude Code

1. Run `make setup` once (see [Quick start](#quick-start)). The plugin's server
   runs from the `.venv` it creates, and will not start without it.
2. Start Claude Code with the plugin, from the repository root:

   ```
   claude --plugin-dir plugin
   ```

   This loads the plugin for that session only. Nothing is installed
   permanently, and there is no marketplace entry yet.

**What you get**

| Kind | Name | What it does |
|---|---|---|
| Skill | `/failed-experiments-wiki:ask` | Answers "what has been tried on this, where did it go wrong, what should I avoid?" |
| Skill | `/failed-experiments-wiki:contribute` | Turns a LessWrong or Alignment Forum post into one entry per failed experiment and submits it |
| Skill | `/failed-experiments-wiki:review` | Checks an entry against its post and records the outcome |
| Tool | `search_entries` | Keyword search and filters on any field |
| Tool | `get_entry` | One entry in full |
| Tool | `list_facets` | Every filterable field and the values in use |
| Tool | `fetch_source` | A post's metadata and text, cached |
| Tool | `submit_entry` | Validates a draft and commits it on a new branch |
| Tool | `review_entry` | Records a review on a new branch |

You do not have to name a skill. Plain requests work:

- "I plan to steer a model along an eval-awareness direction to stop sandbagging. What has been tried?"
- "Add this post to the wiki: `<LessWrong URL>`"
- "Review entry fe-2026-0008."

**What writing does.** `submit_entry` and `review_entry` never change `main`.
Each commits to its own branch (`entry/<id>` or `review/<id>-<date>`). With a
GitHub remote they push that branch and open a pull request with your `gh`
login. Without a remote (a clone with `origin` removed, for example), they stop
at the local branch and print the command that merges it:
`.venv/bin/python tools/cli.py merge-local <branch>`.

**Your name goes on what you file.** An entry or review made through the
plugin records your GitHub login (read from `gh`) as the accountable person,
beside `type: agent` and the model's name, and the commit carries your git
identity. Nothing asks first. Set `FEWIKI_HANDLE` to use another handle; with
neither, the placeholder `HANDLE-TBD` is recorded.

**Permissions.** Claude Code asks before it first uses each wiki tool. In a
headless run (`claude -p`), allow them up front:
`--allowedTools "mcp__plugin_failed-experiments-wiki_failed-experiments-wiki"`
(add `__search_entries` and so on to allow single tools). Read tools need no
credentials.

**What a post needs before it can be filed.** The `contribute` skill declines
an experiment unless the post itself states what was expected, exactly what
was tested, the result, and a quotable sentence of 15 words or fewer. Most
failure write-ups fall short of that (`scouting/yields.md`), so "this post
does not support an entry" is a common and correct answer. A post that works:
`https://www.lesswrong.com/posts/EC5H7xakTgxxNXm5g/sanity-checks-for-sanity-checks-for-sparse-autoencoders`
(already in the wiki, so the skill will say so).

**A review by an agent is a weak check.** The `review` skill can set an entry
to `reviewed`, and tools then report `reviewed_by: an agent only` (and say when
it was the same model that wrote the entry). Treat only a person's review as
vetting.

## What is stored, and what is not

- Stored: structured fields in our own words, a quote of 15 words or fewer,
  and links.
- Never stored: post texts. They are fetched when needed and cached in
  `.cache/`, which is git-ignored.
- The LessWrong API is used gently: every response is cached and requests are
  paused.

## Preexisting work

**None.** Everything in this repository up to the sprint deadline (November
15, 2026, 11:59 PM AoE) was written during the sprint (November 13–15). The tag
[`poc-0.0.2`](https://github.com/pithy-name/failed-experiments-wiki/tree/poc-0.0.2)
marks the Apart proof of concept: the last commit before the deadline. The code
uses third-party open-source Python packages, listed in the
`requirements*.txt` files.

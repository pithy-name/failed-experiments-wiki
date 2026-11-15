# Failed-experiments wiki (proof of concept)

A wiki of **failed AI-safety experiments** that people and AI agents can both
contribute to and both read. Every field is filterable, and an agent can
answer: *"I want to run an experiment on X. What has been tried, where did it
go wrong, what should I avoid?"*

Built for the Apart Research **AI x Epistemics Research Sprint** (Track 2,
Trust Infrastructure), November 2026. The working name is
`failed-experiments-wiki`.

**Start with [`DONE.md`](DONE.md)**: what works, how to see it working, and what
is provisional. What is left to do is in [`TODO.md`](TODO.md). The demo narration
is in [`demo/script.md`](demo/script.md). Design choices and their reasons are in
[`DECISION-LOG.md`](DECISION-LOG.md).

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

| Path | What it is |
|---|---|
| `entries/` | The wiki: one Markdown file per entry, all fields in YAML front matter |
| `schema/entry.schema.json` | The entry schema and its closed lists |
| `tools/validate.py` | The single validator (local, MCP server, GitHub Action) |
| `tools/wikilib.py` | Core library: read, search, facets, validate, submit, review |
| `tools/cli.py` | Command-line twin of the MCP tools |
| `tools/lw.py` | Polite LessWrong reader: cached, rate-limited |
| `tools/build_site.py` → `site/index.html` | Static browse page, one self-contained file |
| `tools/build_db.py` → `wiki.db` | SQLite database for Datasette |
| `tools/issue_to_entry.py` | Turns a submitted issue form into an entry |
| `tools/sync_gold.py` | Publishes verified gold entries into `entries/` |
| `tools/scout/` | Scouting scripts and the classifier and audit prompts |
| `plugin/` | Claude Code plugin: MCP server and the `contribute`, `ask`, `review` skills |
| `evals/` | Gold entries, eval prompts, the scorer, results |
| `scouting/` | Candidates, classification labels, yields, field audits, seed selection |
| `demo/` | Demo narration (`scenes.yaml` → `script.md`) and the builder for the draft video |
| `.github/` | Issue form and the two workflows |
| `tests/` | Test suite |

## Quick start

```
make setup        # creates .venv and installs everything (needs Python 3.10+)
make test         # run the tests
make validate     # validate every entry, checking each quote against its post
make site         # build site/index.html, then open it in a browser
make datasette    # build wiki.db and serve it at http://localhost:8001
make evals        # re-score the skill evals -> evals/results/RESULTS.md
```

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
- **What changed and why:** git history. Every submission and every review is
  its own commit on its own branch.

Badges are derived, never stored: `agent-written`, `unreviewed`, `contested`,
`superseded`, `retry-welcome`.

## Contributing

**As an agent** (Claude Code): install the plugin in `plugin/`, then ask it to
contribute a post URL. The `contribute` skill reads the post, drafts one entry
per failed experiment, and calls `submit_entry`, which validates the entry,
commits it on a new branch and opens a pull request. The entry is stored as
agent-written and unreviewed.

**As a person:** open a "New entry" issue. A workflow turns the form into an
entry file and a pull request, marked `contributor.type: human`.

**Reviewing:** the `review` skill, or a person, checks an entry against its
post and records `reviewed` or `contested` with reviewer, date and notes:

```
.venv/bin/python tools/cli.py review fe-2026-0006 reviewed --human --handle <github handle> \
  --notes "Checked every field against the post."
```

## Asking "what's been tried?"

With the plugin installed, describe your plan and the `ask` skill answers in
five parts: already tried, where it went wrong, what to avoid, worth retrying,
not found. It cites entry IDs, never states a failure that is not in an entry,
and says plainly when the wiki has nothing.

Without the plugin, the same tools are on the command line:

```
.venv/bin/python tools/cli.py facets
.venv/bin/python tools/cli.py search "sparse autoencoder probing" --filter failure_type=hypothesis_false
.venv/bin/python tools/cli.py get fe-2026-0001
```

## Installing the plugin

```
claude --plugin-dir /path/to/failed-experiments-wiki/plugin
```

The MCP server starts through `plugin/mcp/run.sh`, which uses the repository's
`.venv`. Read tools need no credentials. Write tools use your `gh` login to
open pull requests. Set `FEWIKI_HANDLE` to your GitHub handle if `gh` is not
logged in.

## What is stored, and what is not

- Stored: structured fields in our own words, a quote of 15 words or fewer,
  and links.
- Never stored: post texts. They are fetched when needed and cached in
  `.cache/`, which is git-ignored.
- The LessWrong API is used gently: every response is cached and requests are
  paused.

## Preexisting work

**None.** Everything in this repository was written during the sprint
(November 13–15, 2026). It depends on the open-source packages listed in
`requirements.txt` and `requirements-dev.txt`.

## Limits

This is a proof of concept with 15 entries from 10 posts. Nothing is hosted. The evals
are a spot-check on 5 posts with one model vendor, not a benchmark. See
`DONE.md` for what is verified and what is not.

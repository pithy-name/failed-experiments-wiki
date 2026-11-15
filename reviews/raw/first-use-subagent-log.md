# First-use log: failed-experiments-wiki plugin

Persona: AI-safety researcher, colleague said "There's a Claude Code plugin in here, try it out and tell me how it went."
Started: 2026-11-15 (30-minute budget).

## Step 0: orient
- Goal: find out what this repo is and how to install/use the plugin.
- Started 01:37 PST (local clock at first write). Time budget ends ~02:07.
- Read README.md (top level) in full. Told me: "Start with DONE.md" (line 12). Plugin install is at README.md lines 114-123 ("Installing the plugin"): `claude --plugin-dir /path/to/failed-experiments-wiki/plugin`. Also: MCP server "starts through plugin/mcp/run.sh, which uses the repository's .venv" (line 120). Quick start (line 52-61) says `make setup` "creates .venv and installs everything (needs Python 3.10+)".
- Read DONE.md (272 lines). It is a build-status report, not an install guide. It says plugin was "never loaded into Claude Code" (line 25 and P8 line 143) and that T8 in TODO.md is about loading it. It lists 3 skills (contribute, ask, review) and 6 MCP tools (line 88: "lists the six tools") but never names the six tools.
- Friction 0a: README "Installing the plugin" (lines 114-123) does not say "run make setup first", yet the plugin's MCP server depends on .venv (line 120). The Quick start section 60 lines earlier does say `make setup`. A reader jumping to "Installing the plugin" would miss it.
- Friction 0b: README line 12 says to start with DONE.md, but DONE.md is a 270-line build report, mostly about verification status and scouting yields; the first-use path (install -> try) is not in it. DONE.md also says the plugin was never loaded in Claude Code (so I am the first test).
- Friction 0c: README line 82 says "install the plugin in `plugin/`" while line 117 gives only a session-scoped `--plugin-dir` flag (not a persistent install). "install" is ambiguous (there is no marketplace/`/plugin install` instruction).

## Step 1: make setup (README.md line 55; Makefile lines 31-33)
- Cmd: `make -C <clone> setup` (I used -C because my shell starts in a different checkout, see env note below).
- Result: WORKED first try, no errors, no pip flag needed. Makefile default PYTHON is python3.11 (Makefile line 4), which exists here. It installed fastmcp 4.2.0 / mcp 2.3.0 / datasette 0.65.5 etc. into <clone>/.venv. Last lines: "Successfully installed Jinja2-3.1.6 ... fastmcp-4.2.0 ...".
- Friction 1a: README says "needs Python 3.10+" (line 55) but Makefile hardcodes `PYTHON ?= python3.11` (Makefile line 4). On a machine with only python3.10 or a bare `python3`, `make setup` fails with "python3.11: command not found" unless you know to pass `PYTHON=python3`. README does not mention the PYTHON variable. (Not hit here; inferred from reading the Makefile. Unverified on a machine without 3.11.)
- Friction 1b: requirements are unpinned (could not tell without reading); resolved to bleeding-edge versions here. Works today.
- ENVIRONMENT NOTE (not product): my shell's cwd is a different checkout of this project, which I must not touch; `claude --help` has no working-directory flag (only --add-dir). So all `claude -p` runs go through a wrapper script under firstuse/ that cds into the clone first. The clone has no git remote (`git remote -v` printed nothing), single branch `main`, clean status. `gh` is logged in on this machine (real account) so I will watch what write tools try.

## Step 2: load the plugin (README.md line 117; TODO.md T8 lines 141-148)
- Cmd (via wrapper script out-load.txt): `claude -p "Reply with just the word ready." --plugin-dir <clone>/plugin --setting-sources project --permission-prompts none --no-session-persistence --model sonnet --output-format stream-json --verbose`
- Result: WORKS. Init event: plugin `failed-experiments-wiki` version 0.1.0 loaded; MCP server `plugin:failed-experiments-wiki:failed-experiments-wiki` status `connected`; six tools: `mcp__plugin_failed-experiments-wiki_failed-experiments-wiki__{fetch_source,get_entry,list_facets,review_entry,search_entries,submit_entry}`; three skills/slash commands: `failed-experiments-wiki:ask`, `:contribute`, `:review`. Answer: "ready". So `--plugin-dir <path>/plugin` is correct (the TODO.md T8 doubt "flag was not confirmed" is resolved).
- Friction 2a: docs never name the six tools or give their full namespaced names; you need them for `--allowedTools`/permissions (README line 82-104 only name `submit_entry`; DONE.md line 88 says "six tools" without listing them). I got the names from the init event.
- Friction 2b: nowhere does the README/DONE tell the user that Claude Code will ask permission for every wiki tool call, or what permission rule to add (e.g. `mcp__plugin_failed-experiments-wiki_failed-experiments-wiki__*`). In non-interactive mode this made the first `ask` fail (next step).

## Step 3: ask skill (README.md lines 99-104)
- Prompt (natural language, as README says "describe your plan"), attempt 1, no allowedTools: "I want to run an experiment using sparse autoencoders to find an evaluation-awareness direction for steering. What has been tried, where did it go wrong, and what should I avoid?"
- Attempt 1 result (out-ask.txt): FAILED to answer. First lines: "I can't answer this from the wiki yet, because the wiki tools were blocked. I tried `list_facets` and three `search_entries` calls ... All four were denied. This session has no way to approve permission prompts, so they were refused automatically." It did recognise the plugin's tools and rules (so the skill DID trigger from natural language) and told me the permission rule to add: `mcp__plugin_failed-experiments-wiki_failed-experiments-wiki__*`.
- Attempt 2 with `--allowedTools` for list_facets, search_entries, get_entry (out-ask2.txt): WORKED. First lines: "## Already tried / The wiki has 15 entries. None of them is an SAE-based eval-awareness steering experiment. Four are close enough to matter. All four are `author_report` and **unreviewed**. ..." Cited fe-2026-0005, 0001, 0008, 0003; then headings "## Where it went wrong", "## What to avoid", "## Worth retrying" (answer was cut at 5000 chars in my view; headings seen: Already tried, Where it went wrong, What to avoid, Worth retrying; "Not found" section not seen in the part I read).
- Friction 3a: headless mode refuses every MCP call by default: an interactive user would get a prompt; documents don't say so. (Partly my environment.)
- Observation 3b: the answer says "The one entry marked reviewed (fe-2026-0007)" while another line says all four close ones are unreviewed: consistent with DONE.md line 59-61.

## Step 4: fetch_source tool, direct prompt (no doc describes it as user-facing; DONE.md line 154 DEC-22 mentions it)
- Prompt: "Use the wiki's fetch_source tool on the source URL of entry fe-2026-0008 and tell me the first 3 lines it returns and how many characters the text has." (allowed: fetch_source, get_entry)
- Result: WORKED (1 attempt). It fetched the LessWrong post (real network call to lesswrong.com). Returned first lines of the post text, `word_count: 687`, but no character count (tool does not return one; the shell for counting was denied). Fine.
- Friction 4a: no doc explains fetch_source in the README at all (it is not in README's repo table or any usage section).
- Correction to step 3: the full ask answer (out-ask2.txt) has all five headings: "## Already tried", "## Where it went wrong", "## What to avoid", "## Worth retrying", "## Not found" (checked with grep on the saved file).

## Step 5: review skill (README.md lines 91-97)
- README's documented review example is a raw CLI command (`.venv/bin/python tools/cli.py review fe-2026-0006 reviewed --human --handle <github handle> ...`, lines 94-97), not a plugin prompt; the text says "the `review` skill, or a person". I typed what a user would: "Please review wiki entry fe-2026-0008 against its source post and record your verdict." with get_entry, fetch_source, review_entry allowed.
- Result: WORKED on attempt 1 (natural language triggered the skill). Answer, first lines: "I've finished the review of fe-2026-0008 and recorded it as `reviewed`. ... The quote is verbatim and 12 words long ... The change is committed on the local branch `review/fe-2026-0008-20261115` (commit `ba14dcb`). No pull request was opened, because the repo has no git remote. ... To merge it locally, run `python tools/cli.py merge-local review/fe-2026-0008-20261115`."
- Verified on disk: `git branch -a` now lists `review/fe-2026-0008-20261115`; working tree still on `main`, status clean. Commit message: "Review fe-2026-0008: unreviewed -> reviewed / Reviewer: agent pithy-name (claude-sonnet-5-5) ... same-model agent review and weaker than a human one." Commit author: the machine's git user name + email (pithy-name <pithy.name@fastmail.com>).
- Friction 5a: the reviewer is recorded as "agent pithy-name": a real GitHub login (from `gh`) is stamped onto an agent's judgment. A reader of the wiki would read "pithy-name reviewed this" as a person standing behind it, though the notes say same-model agent review.
- Friction 5b: the review's merge instruction ("python tools/cli.py merge-local ...") assumes .venv is activated or a bare `python` has the deps; README elsewhere always writes `.venv/bin/python`.
- Friction 5c: README says the reviewer needs `FEWIKI_HANDLE` if `gh` is not logged in (line 122); not tested here (gh was logged in).

## Step 6: contribute skill (README.md lines 82-86)
- README says "ask it to contribute a post URL" but gives no example URL. I used the one post URL the repo names as an example: the PRD-named post "My Failed AI Safety Research Projects (Q1/Q2 2025)" (DONE.md line 228 says it was deliberately NOT selected as a seed because it is a roundup); I found its URL by grep in scouting/.
- Prompt: "Please contribute this post to the wiki: https://www.lesswrong.com/posts/kiCZzHDkRtupek2mc/my-failed-ai-safety-research-projects-q1-q2-2025" (allowed: get_entry, fetch_source, submit_entry, search_entries, list_facets)
- Result: WORKED on attempt 1, locally. Answer first lines: "I submitted two entries from the post. Both are agent-written and unreviewed, and the quote check passed for each. | fe-2026-0016 | LLM multiplication ... | `entry/fe-2026-0016` | fe-2026-0017 | Toy model of memorisation ... | `entry/fe-2026-0017` | No pull request was opened because the wiki repo has no git remote. Each entry is committed on its local branch."
- Verified on disk: branches `entry/fe-2026-0016` and `entry/fe-2026-0017` exist; main still checked out and clean. `git show entry/fe-2026-0016:entries/fe-2026-0016.md`: models all `unknown`, failure_type `unknown`, direction `mixed`, confidence low, `contributor.handle: pithy-name`, agent_model claude-sonnet-5-5, quote "I found no evidence for an equivalent of angular encoding for log(token value)." (12 words). Real network fetch from lesswrong.com happened (fetch_source).
- NOT TESTED: the pull-request path (no remote; I did not add one, to honour "no push"). `submit_entry` says nothing was pushed. That the README's promise "opens a pull request" (line 86) works is unverified by me.
- Friction 6a: no example URL; no statement of what kinds of posts qualify. The repo's own build notes (DONE.md line 228) say this very post was judged unsuitable (a roundup), yet the skill accepted it and produced two entries with `models: unknown` and `failure_type: unknown`. The plugin did not warn me the post was a poor fit.
- Friction 6b: the answer gives "python tools/cli.py merge-local" again without `.venv/bin/`.
- Friction 6c: no way to preview a draft before it is committed to a branch (it commits straight away); an ordinary user would want "show me the draft first". Not documented either way.

## Not done (time or scope)
- Slash form (`/failed-experiments-wiki:ask`) never typed; natural language triggered all three skills on attempt 1 (ask attempt 1 failed only for permissions).
- The remaining MCP tools `list_facets`, `search_entries`, `get_entry` were exercised only inside the ask/review/contribute runs (the ask answer says it called them; permission refusal on attempt 1 named list_facets and search_entries). I did not run a separate direct prompt for each.
- Did not run make test, mcp-smoke, site, datasette (not plugin offerings).
- I read plugin/skills/review/SKILL.md only by `grep -n handle` after the review ran, to understand the reviewer-handle behaviour; no other source reading.

---
# FINAL SECTIONS

## 1. Table

| Thing the plugin offers | Worked? | Attempts | What blocked or confused me |
|---|---|---|---|
| Plugin loads (`--plugin-dir`) | yes | 1 | README does not say run `make setup` in the install section; "install" ambiguous (session flag only). |
| MCP server (connects, 6 tools) | yes | 1 | The six tools are never listed in the docs; had to read them from the startup event. |
| `ask` skill | yes | 2 | Attempt 1 refused: every MCP call needs permission, undocumented (headless only; interactive user would get a prompt). Natural language did trigger the skill. Answer had all five sections, cited IDs. |
| `review` skill | yes (local only) | 1 | README example is a CLI command, not a plugin prompt. Reviewer recorded as my GitHub login. PR path unverifiable (no remote). |
| `contribute` skill | yes (local only) | 1 | No example URL, no guidance on which posts qualify; accepted a post the repo's own notes call unsuitable; PR step unverified. |
| `fetch_source` tool | yes | 1 | Not described in README at all. |
| `submit_entry` / `review_entry` | yes, to local branches | 1 each (via skills) | Pull-request behaviour (README line 86) not tested: no remote. |
| `list_facets`, `search_entries`, `get_entry` | yes (used inside ask/review/contribute) | n/a | Not run as direct prompts, so only indirect evidence. |

## 2. Documentation wrong, missing or ambiguous

- README.md lines 114-123 (Installing the plugin): does not say to run `make setup` first, though line 120 says the MCP server uses `.venv`.
- README.md line 82 ("install the plugin in `plugin/`") vs line 117 (only a one-session `--plugin-dir` flag): no persistent install path (/plugin, marketplace) is given.
- README.md line 55 says "needs Python 3.10+" but Makefile line 4 hardcodes `PYTHON ?= python3.11`; the `PYTHON=` override is never mentioned (inferred, not hit).
- README.md line 12 says "Start with DONE.md"; DONE.md is a 270-line verification report (scouting yields, build history), and contains no first-use walkthrough. The install instructions are only in README lines 114-123 and TODO.md T8 (lines 141-148).
- DONE.md line 88 / line 25 / README: the six MCP tools are never listed; README names only `submit_entry` (line 84). Nothing documents the permission rule needed (`mcp__plugin_failed-experiments-wiki_failed-experiments-wiki__*`).
- README.md line 86: promises `submit_entry` "opens a pull request"; with no remote it silently stops at a local branch (reported by the agent, not in the docs). README never says what happens with no remote or how to merge locally (`merge-local` appears only in TODO.md line 65).
- README.md lines 82-86: no example post URL and no statement of what posts qualify (the selection rule is only in DONE.md lines 95-98 and 218-228).
- README.md lines 94-97: the review example is a CLI command with `--human`; there is no example prompt for the `review` skill.
- README.md line 122: `FEWIKI_HANDLE` / `gh` behaviour: it does not say the entry will carry your real GitHub login, or that an agent review is also stamped with it.
- TODO.md lines 141-148 (T8): says `--plugin-dir` "was not confirmed"; it IS confirmed by this trial (plugin loaded as v0.1.0, MCP connected, three skills present).
- README.md line 142 / DONE.md line 3 say 15 entries; after my runs there are entries 16 and 17 on branches (expected; not a doc error).

## 3. What the plugin did that I would not have expected or would not trust

- It stamped my real GitHub login (`pithy-name`, read silently from `gh`) as the reviewer of an AI review and as `contributor.handle` of a new entry, and the commit author is my git email. No prompt asked me. A wiki reader would see a named person attached to a model's judgment.
- A single natural-language sentence made it fetch from lesswrong.com, write two entry files and create two git branches without showing me a draft first.
- It accepted a post that the repo's own notes (DONE.md line 228) say was rejected as a roundup, and produced entries with `models: unknown`, `failure_type: unknown`, `direction: mixed`: low-information entries labelled "quote check passed". The validator's pass would give a false sense of quality.
- The review was done by the same model that wrote the entry (it said so in the notes, to its credit), yet the status became `reviewed`, a value that downstream badges and the `ask` answer treat as vetted. In `ask`, the one `reviewed` entry is called out as reviewed.
- `ask` was honest in the good direction: it said when nothing matched my exact plan (no SAE eval-awareness steering experiment), separated near matches, labelled all as unreviewed, and had a "Not found" section.
- Positive: with no permission it refused to invent answers ("I won't fill them from memory") and told me exactly which permission to grant.

## 4. Three sentences for my colleague

It works: `make setup`, then `claude --plugin-dir <repo>/plugin` loaded the plugin, connected the MCP server and exposed the `ask`, `review` and `contribute` skills, and each did what the README says, ask also answering in the five documented sections with entry IDs. Expect to grant permissions for the six wiki tools (the docs never list them), and note that review/contribute write to local branches under your real GitHub login and, with no remote, never reached the pull-request step I couldn't test. Be skeptical of what you contribute or review: it let me add two thin entries from a post the maintainers had already judged unsuitable, and a same-model "review" flips an entry to `reviewed`.

# Decision log

> **File name.** The run instructions asked for this log in `DECISIONS.md`.
> Writing a file of that name was denied by the session's permission settings,
> so the log is here instead. Rename it if you prefer; nothing depends on the name
> except links in `README.md` and `DONE.md`.

Every non-trivial decision made during the unattended build, with its reason.
The spec is `PRD-proof-of-concept-v3.md` (kept outside this repository). Where
the build departs from the spec, the row says so.

IDs are stable: refer to a decision as "DEC-07", never by position.

## A. Decisions the maintainer made at the start of the run

| ID | Decision | Reason given or recorded |
|---|---|---|
| DEC-01 | The repository lives in a subfolder of the sprint notes folder, not under `~/code/`. | The session's sandbox could only write inside that folder. Chosen by the maintainer from three options. |
| DEC-02 | **No pushes during this run.** Local work only. No GitHub repository was created. | Chosen by the maintainer. Consequence: the GitHub half of D1, D2 and D7 (pull requests, the issue-form workflow, the validation workflow) is built and tested locally but has never run on GitHub. `DONE.md` marks each such item. |
| DEC-03 | Commits are per build step, and one commit per entry, instead of one commit per file. | Chosen by the maintainer: history should read as a narrative, since git history is a trust signal here. |
| DEC-04 | The maintainer's name may appear in tracked files while the repository is private. | Chosen by the maintainer. A scrub is needed before the repository goes public. |

## B. Environment constraints that shaped the build

| ID | Constraint | What was done about it |
|---|---|---|
| DEC-05 | The sandbox refuses writes to `.git/config`, so `git init` could not run in this folder. | Not worked around: that guard exists to stop sandboxed commands from planting git hooks or config. The maintainer was asked to run `git init -b main` once. See `DONE.md` for the state of git history. |
| DEC-06 | `gh` could not read its config in the sandbox, so the GitHub handle is unknown. | Entries use the visible placeholder `HANDLE-TBD` for `contributor.handle` rather than a guessed handle. `FEWIKI_HANDLE` or a working `gh` login replaces it for new entries. |
| DEC-07 | The sandbox forbids listening on a local port. | Datasette is verified through its in-process request mode (`datasette --get`), which needs no port. Serving on a port is untested here; the command is in `DONE.md`. |
| DEC-08 | No headless `claude` command is available, and subagents cannot use an MCP server that the session has not loaded. | Skills were exercised by subagents that read the skill file and call `tools/cli.py`, the command-line twin of the MCP tools (same functions, same JSON). The MCP layer itself is tested in process with a FastMCP client. Loading the plugin inside Claude Code is untested; see `DONE.md`. |
| DEC-09 | Only Sonnet and Haiku subagents were permitted in this session (the general-purpose agent type and Opus were denied by the maintainer's settings). | Haiku classified; Sonnet did the field audits, the gold drafts, the skill runs, the grading and the UI code. The orchestrator (Claude Fable 5.2) wrote the core library, validator, MCP server, skills and evals, and checked every subagent result. |
| DEC-10 | Model IDs recorded in entries and results are the documented IDs behind the `haiku` and `sonnet` aliases (`claude-haiku-5-5`, `claude-sonnet-5-5`). | The subagent interface exposes the alias, not the resolved ID, so the ID was not confirmed by the model itself. |
| DEC-11 | Python's standard HTTP client had responses from the LessWrong search endpoint cut short behind the sandbox proxy. | `tools/lw.py` retries, then falls back to the `curl` binary for the same request. On a normal network the standard client is used. |

## C. Schema and validation

| ID | Decision | Reason |
|---|---|---|
| DEC-12 | `id` is `fe-YYYY-NNNN` where YYYY is the year the **entry** was created, numbered in order. | The PRD gives the format but not what YYYY means. Creation year keeps IDs stable and sequential. |
| DEC-13 | The schema gains one optional field the PRD does not list: `contributor.note`. | Needed to say, visibly, that the five gold-backed entries are model drafts awaiting verification although they are marked `contributor.type: human` (see DEC-37). Both browse UIs show it. |
| DEC-14 | The schema also allows `review.reviewers[].agent_model`. | An agent review should record which model reviewed, as an agent contribution records which model wrote. |
| DEC-15 | A bare YAML `direction: null` is read as the enum value `"null"`. | Otherwise the most natural way to write a null result parses to an empty value and fails validation confusingly. |
| DEC-16 | The quote check folds typography only (curly quotes, dash variants, non-breaking and invisible characters, runs of whitespace). Words, order, case and punctuation must match. | "Verbatim" has to survive copy-paste differences between a post's HTML and a text editor, but nothing more. |
| DEC-17 | An unreachable source makes the quote check a warning by default and an error with `--quotes strict`. | The PRD asks for a warning when the source is unreachable; seeding needs the stronger guarantee, so seeds were validated with the source actually fetched. |
| DEC-18 | Extra consistency rules beyond the PRD: `reviewed` or `contested` needs at least one reviewer; `dates.updated` is not before `dates.created`; `ci_low` is not above `ci_high`; the ID matches the file name. | Cheap guards that keep trust fields meaningful. |
| DEC-19 | `submit_entry` assigns `id`, `contributor`, `review` and `dates` itself and ignores any values the submitter sends for them. | A contributor, human or agent, must not be able to mark its own entry as reviewed or as written by someone else. |
| DEC-20 | `source.type` is `alignment_forum` when the post is an Alignment Forum crosspost, else `lesswrong`. `source.url` is always the LessWrong URL; `source.crosspost_url` holds the Alignment Forum URL. | Both sites serve the same post under the same ID. The LessWrong API is the one the validator reads. |

## D. Architecture

| ID | Decision | Reason |
|---|---|---|
| DEC-21 | One core module (`tools/wikilib.py`); the validator CLI, the general CLI, the MCP server and both UI builders are thin wrappers. | One implementation of validation, search and the write path, so the MCP server and the GitHub Action cannot disagree. |
| DEC-22 | A sixth MCP tool, `fetch_source(url)`, beyond the five the PRD lists. | The `contribute` and `review` skills must read the post, and reading it through the same code the validator uses guarantees the quote is checked against the same text. |
| DEC-23 | Write tools commit with git plumbing on a new branch (`entry/<id>`, `review/<id>-<date>`) and never touch the working tree or the checked-out branch. With a remote they push and run `gh pr create`; without one they return `branch_only_no_remote` and never a pull-request URL. | Safe to call from an agent while a person has the repository open. Honest about what did not happen. |
| DEC-24 | `tools/cli.py merge-local <branch>` validates the merged result and merges with a merge commit. It stands in for merging a pull request while there is no remote. | Keeps the "changes arrive on a branch and merge only when valid" shape in local history, and each merge commit says it is a stand-in. |
| DEC-25 | Search is plain keyword matching with field weights, not embeddings. | No model and no service to run; transparent; enough for 10 entries. The `ask` skill is told the search is keyword-only and must try synonyms, filters and a full listing before saying "not found". |
| DEC-26 | The issue-form workflow validates the entry itself before opening the pull request. | Pull requests opened with the default workflow token do not trigger other workflows, so `validate.yml` would not run on them automatically. |
| DEC-27 | Issue text reaches the conversion script only through an environment variable. | Issue bodies are untrusted; interpolating them into a shell command is an injection risk. |

## E. Scouting and seeding

| ID | Decision | Reason |
|---|---|---|
| DEC-28 | Candidate search uses the site's search endpoint (`/api/search`) for phrases and GraphQL for tags and post bodies. | The GraphQL API has no phrase search. The search endpoint is fuzzy full-text, not exact-phrase; `scouting/yields.md` says so. |
| DEC-29 | A post is a candidate only if it carries an AI-related tag. Topical tags (interpretability, SAEs and so on) keep only posts whose title or description matches a failure phrase. | PRD scope is "posts tagged with AI-safety topics"; the topical tags alone hold thousands of posts. |
| DEC-30 | The tag `negative-results` does not exist on LessWrong. | Recorded as a finding: there is no tag that collects negative results. |
| DEC-31 | The classification sample is deterministic, not random: the best-ranked hits of every route in turn, plus the two posts the PRD names. | Reproducible, and every phrase and tag is represented. The yields are therefore not an unbiased estimate, and `yields.md` says so. |
| DEC-32 | **The bar for a seed post was kept strict, and the classification was extended instead.** After round 1 (60 posts, as the PRD plans), 18 were labelled yes but only 3 supported every required field. A second round classified every remaining candidate. | The maintainer's rule: a post qualifies only if it supports every required field from the post itself. Lowering the bar would have produced entries with inferred fields. The PRD's "up to 60" is exceeded; round 1 is still reported on its own. |
| DEC-33 | A stated research question does not count as a `hypothesis`; the post must say what the authors expected or hoped. A setup description without data or scale does not count as `claim_scope`. | These were the two most common gaps. Both readings are strict on purpose; the count of posts each rule excluded is in `yields.md`. |
| DEC-34 | Posts whose failure cause fits none of the `failure_type` values were not seeded, and the gap is recorded as a finding instead of stretching a label. | Example: a debate pilot abandoned because the setup itself was invalid. The closed list has no value for that. See "Findings worth reporting" below. |
| DEC-35 | The orchestrator approved the 10 seed posts in place of the maintainer, as instructed for this run. | Each choice and the fields it supports are in `scouting/selection.md`. |

## F. Gold set and evals

| ID | Decision | Reason |
|---|---|---|
| DEC-36 | The five gold entries were drafted by a Sonnet subagent that never saw the `contribute` skill or its output, working from the post alone (`evals/prompts/draft_gold.md`). They carry `gold_status: pending_maintainer_verification`. | Instructed for this run in place of the maintainer writing them. They are not ground truth until verified. |
| DEC-37 | Their copies in `entries/` are marked `contributor.type: human`, `review.status: unreviewed`, as instructed, with a `contributor.note` stating they are model drafts awaiting verification. | **Known tension:** a model-drafted entry labelled `human` does not get the agent-written badge. The note is the mitigation, and both UIs show it. `make sync-gold` removes the note only once the maintainer has verified the gold file. |
| DEC-38 | `make evals` re-scores saved skill outputs; it does not call a model. Producing the outputs and the grades is a documented model step (`evals/README.md`). | No headless model command exists here (DEC-08), and a deterministic scorer can be re-run the moment a gold entry is corrected. |
| DEC-39 | Rubric grades and judge verdicts are tied by hash to the exact texts they were made on. If a gold text or a skill output changes, the grade is reported as STALE and left out of the totals. | Correcting a gold entry must never silently reuse a grade made against the old text. |
| DEC-40 | `source.quote` is not compared with gold. It is checked for validity instead (verbatim, 15 words or fewer). | Any verbatim fragment stating the result is acceptable, so equality with gold would punish correct answers. |
| DEC-41 | When the skill writes several entries for one post, the draft that best matches gold is scored and the number of drafts is reported. | The skill is asked for one entry per distinct failed experiment; gold covers one experiment per post. |
| DEC-42 | All eval results are labelled PROVISIONAL until every gold entry is `verified`. | The numbers currently compare one model's output with another pass of the same vendor's model. |

## G. Human contribution test

| ID | Decision | Reason |
|---|---|---|
| DEC-43 | No test issue was filed and no agent-written entry was stored as `human` to demonstrate D2. | There is no GitHub repository to file it in (DEC-02), and an entry filed by an agent must not sit in the wiki as a person's. D2 is demonstrated by tests that run the form-to-entry conversion on a realistic issue body; the live run is a step in the demo script. |

## Findings worth reporting

Not decisions, but things the build turned up that belong in the report.

1. **Most failure write-ups do not support a full structured entry.** Being a
   genuine write-up of a failed experiment and supporting every required field
   are very different bars. The numbers are in `scouting/yields.md`.
2. **The fields posts most often lack** are an exact account of what was
   tested (`claim_scope`) and a stated expectation (`hypothesis`): the same
   fields the wiki relies on to stop a thin failure report from reading as
   "this never works".
3. **The `failure_type` list has gaps.** At least one clear postmortem
   (experimental setup turned out invalid) fits none of the nine values.
4. **Experiments without a model** (for example human-judge studies) cannot be
   entered, because `models` is required.
5. **LessWrong has no tag for negative results.**

# DONE

The proof of concept is built and works locally, with **15 entries** from 10
posts. **Three things did not happen on GitHub, because no GitHub repository
exists yet** (your choice at the start: no pushes). Each is marked UNVERIFIED
below with the steps to verify it.

Read section 5 first: it is your to-do list, shortest task first.

Every "verified" below was run in this build session on 2026-11-14. Where
something was not run, it says so.

---

## 1. Definition of done, D1–D8

Run every command from the repository root. `make setup` first if `.venv/` is missing.

| ID | Capability | Status | In one line |
|---|---|---|---|
| D1 | An LLM can contribute | **PASS locally · pull request UNVERIFIED** | Skill drafts → validator → branch → merge worked for 10 entries. No pull request was opened: there is no remote. |
| D2 | A person can contribute | **BUILT · live run UNVERIFIED** | Issue form and workflow exist; the form-to-entry conversion passes its tests. The workflow has never run on GitHub. |
| D3 | A person or agent can review | **PASS locally · pull request UNVERIFIED** | An agent review changed `fe-2026-0007` from unreviewed to reviewed, with reviewer, date and notes, in its own commit. The human review is yours to do (T4). |
| D4 | Browse and filter by hand | **PASS by test · not seen in a browser or on a port** | Both UIs list all 15 entries and filter on every field. The sandbox could not open a browser or listen on a port. |
| D5 | An agent can ask "what's been tried?" | **PASS for the skill and the MCP server · inside Claude Code UNVERIFIED** | 7 answers in the required five-part format, two of them an honest "not found". The MCP server was started as a real process and answered over stdio. The plugin was never loaded into Claude Code. |
| D6 | The wiki is seeded | **PASS for 9 posts by your rule · the 10th is an exception awaiting your call** | 15 entries; every quote is 15 words or fewer and was found in the fetched post. One post does not meet your qualification rule (T3). |
| D7 | Validation guards the wiki | **PASS locally · GitHub Action UNVERIFIED** | The validator rejects every class of bad entry in tests, and rejected two real skill drafts during seeding. The Action has never run. |
| D8 | Skill evals run | **PASS, results PROVISIONAL** | `make evals` writes a results file. Numbers are provisional until you verify the gold entries. |

### D1. An LLM can contribute

- **What ran:** Sonnet subagents each followed `plugin/skills/contribute/SKILL.md`
  on one post and wrote drafts. The orchestrator then ran the skill's submit
  step for each draft with `tools/cli.py submit`, which is the same function the
  MCP tool `submit_entry` calls.
- **Evidence:**
  - Entries `entries/fe-2026-0006.md` to `fe-2026-0015.md`: `contributor.type: agent`,
    `agent_model: claude-sonnet-5-5`, `tool: contribute-skill v0.1` (v0.2 for `0011`–`0015`), `review.status: unreviewed`.
  - Ten branches `entry/fe-2026-0006` … `entry/fe-2026-0015`, each with one commit, each merged with a merge commit:
    `git log --oneline --graph`.
  - Two of the first five drafts were **rejected by the validator** on first submission
    (`limitations` written as a list) and resubmitted after the fix. The skill
    file now states the field types (v0.2).
- **See it:** `.venv/bin/python tools/cli.py get fe-2026-0006` shows the badges `agent-written`, `unreviewed`, `retry-welcome`.
- **UNVERIFIED, and how to verify:**
  1. A real pull request. After T6, run the skill on a new post and `submit_entry` will push the branch and run `gh pr create`. That code path has never run.
  2. The plugin loaded in Claude Code (T8).
  3. The subagents had no command access, so they read the post from the cache the orchestrator prepared, not through `fetch_source`, and the orchestrator ran the submit step with their drafts.

### D2. A person can contribute

- **Built:** `.github/ISSUE_TEMPLATE/new-entry.yml`, `.github/workflows/issue-to-pr.yml`, `tools/issue_to_entry.py`.
- **Verified:** `.venv/bin/python -m pytest tests/test_issue_to_entry.py -q` → 6 passed. The tests feed a realistic issue-form body and check the result is a schema-valid entry with `contributor.type: human`, that the form's labels and dropdowns match the schema, and that bad forms are refused with a readable reason.
- **UNVERIFIED:** the workflow has never run. No test issue was filed: there is no repository to file it in, and an entry filed by an agent must not sit in the wiki as a person's (DEC-43).
- **To verify:** T6, steps 3–5. Fallback if the Action fails: copy an entry file by hand, `make validate`, open a pull request.

### D3. A person or agent can review

- **What ran:** a Sonnet subagent followed `plugin/skills/review/SKILL.md` on `fe-2026-0007`, checked 11 items against the post and decided `reviewed`. The orchestrator recorded that decision with `tools/cli.py review` (the function behind the MCP tool `review_entry`).
- **Evidence:** `git log --oneline --grep "Review fe-2026-0007"` shows the review commit on branch `review/fe-2026-0007-20261114` and its merge. `entries/fe-2026-0007.md` has `review.status: reviewed` and a reviewer with `type: agent`, the date, the model and notes.
- **Read this:** that review was done by the same model that wrote the entry. The notes say so, and the web page labels it "Reviewed by an agent only". Treat it as a demonstration of the mechanism, not as vetting.
- **Your human review:** T4.

### D4. Browse and filter by hand

**Web page**

- **Build:** `make site` → `site/index.html` (one file, about 90 KB, no external requests). Open it in a browser.
- **Verified:** `.venv/bin/python -m pytest tests/test_build_site.py -q` → 10 passed. Among them:
  - every schema field has a control (facet, range or text search), checked against the field catalogue;
  - the filter logic passes 37 checks in a real JavaScript engine (`tests/js/filter_test.js`);
  - the page's own script was executed against a stand-in DOM: it rendered one card per entry and reacted to search, a facet tick and "clear" (`tests/js/dom_test.js`);
  - entry text containing `</script>` cannot break out of the page.
- **NOT verified:** nobody has looked at it in a browser. The sandbox blocks opening one. Layout, colours and real click behaviour are unseen. Open it and click through before recording.

**Datasette**

- **Verified on the real entries:** `make datasette-check` runs Datasette in process and prints a listing, the facets and one filter of each kind (enum, array, boolean, date range, number range, full-text). Output from this build: 15 entries; 10 agent-written; `failure_type = hypothesis_false AND method contains sae` → `fe-2026-0007`, `0012`, `0014`; search "steganography" → `fe-2026-0010`, `0011`.
- **NOT verified:** serving on a port (`make datasette`, then http://localhost:8001/wiki/entries). The sandbox forbids listening sockets.

**Recommendation: use the web page for the demo.** It shows what the project is about at a glance: badges, the "awaiting verification" notes, quotes and scoped claims on every card, with no server to start. Show Datasette for ten seconds as the path for power users and agents (SQL, JSON, facets on any column).

### D5. An agent can ask "what's been tried?"

- **What ran:** seven Sonnet subagents each followed `plugin/skills/ask/SKILL.md` on one question from `evals/ask_questions.json`.
- **Evidence:** `evals/results/ask/q1.md` … `q7.md`. Read `q5.md` (a match) and `q7.md` (nothing found). Each has the five headings, cites entry IDs, separates weak from strong evidence, and names what the wiki does not cover.
- **Scores (PROVISIONAL): 6 of 7 passed** — 4 of 5 match questions, 2 of 2 no-match questions. Every match answer cited the expected entry and named the gold failure type. The one failure, `q5`, was failed by the judge for one detail the entry does not state (that the 5-point threshold was fixed in advance; the entry says only that the headline layer was pre-registered). Reasons are in `evals/results/ask_judgements.json`. The answers were written when the wiki held 10 entries.
- **MCP server, verified:** `make mcp-smoke` starts the server through `plugin/mcp/run.sh` (the launcher the plugin uses), connects over stdio, lists the six tools and runs a search. It returned 5 matches of 10 entries at the time, with badges.
- **See it yourself without the plugin:**
  `.venv/bin/python tools/cli.py search "steer evaluation awareness direction to stop sandbagging"`
- **UNVERIFIED:**
  1. Inside Claude Code (T8).
  2. The eval subagents had no command access. They read the tools' saved JSON output (facets, a full listing, each entry) instead of calling them, so they could not run keyword searches. With 10 entries a full listing is what the skill asks for anyway, but keyword search by an agent was not exercised. The orchestrator ran searches by hand and they rank the right entry first.

### D6. The wiki is seeded

- **Verified:** `.venv/bin/python tools/validate.py --quotes strict` → `15 file(s) checked … 0 error(s), 0 warning(s)`. In strict mode an unfetched source is an error, so all 15 quotes were checked against the post text.
- **The exception, which is your call (T3):** your rule was that a post qualifies only if it supports every required field. Nine posts do. The tenth, "Some negative steganography results", does not: it asks a question and states no prediction, so `hypothesis` in `fe-2026-0010` and `fe-2026-0011` records the proposition tested and says the post poses it as a question. I admitted it because the alternative was 9 posts, and it is otherwise the strongest near-miss. T3 has the two commands that back it out.
- **What checking each entry got:**

| Entries | Made by | Schema + quote found in post | Every number and model name found in post (`make check-facts`) | Read against the post by the orchestrator | Field-by-field review |
|---|---|---|---|---|---|
| `0001` | gold draft | yes | yes | yes, in full | none yet: yours (T7) |
| `0002`–`0005` | gold draft | yes | yes | key fields only | none yet: yours (T7) |
| `0006`, `0008`, `0009`, `0010` | `contribute` v0.1 | yes | yes | key fields only | none |
| `0007` | `contribute` v0.1 | yes | yes | key fields only | agent, same model |
| `0011`–`0015` | `contribute` v0.2 | yes | yes | key fields only | none |

  "Key fields only" means title, hypothesis, models, result direction, failure type, confidence and quote. `check-facts` found every number in every entry in its post; the only misses are descriptive benchmark or model names such as "IMDB movie review dataset (filtered to relatively short reviews)", whose key term is in the post. Neither check says anything about whether an entry's wording is faithful. That is what review is for.
- **Weak spot:** `fe-2026-0007` has `models: unknown`, because the experiment trains sparse autoencoders on synthetic data and uses no language model. The later entries from that post name the SAE variant instead. The schema has no good way to say this.

### D7. Validation guards the wiki

- **Verified:** `.venv/bin/python -m pytest tests/test_validate.py -q` → one failing fixture for each class: schema, closed list, missing source URL, quote not in source, quote over 15 words, duplicate ID, ID not matching file name, review without reviewer.
- **Verified in real use:** the two rejected skill drafts (D1).
- **Try it:** change `failure_type` in any entry to `bad_luck` and run `make validate`. It exits 1 and names the field.
- **UNVERIFIED:** `.github/workflows/validate.yml` has never run. It runs on the first push.

### D8. Skill evals

- **Run:** `make evals` → `evals/results/results.json` and `evals/results/RESULTS.md`.
- **Result of this build (PROVISIONAL):**
  - `contribute`: overall field accuracy **78%** on 5 gold posts (mean over 26 scored fields). All 5 scored drafts were schema-valid with a valid quote. Enum fields 60–100%; source fields 100%; text fields by rubric: `claim_scope` 90%, `hypothesis` 70%, `limitations` 60%; free-tag lists `method` and `checks_done` 0% on exact set match.
  - `ask`: **6 of 7** passed.
  - The full table and every mismatch are in `evals/results/RESULTS.md`.
- `make evals` re-scores saved outputs and calls no model. Producing the outputs and the grades is a model step, documented in `evals/README.md`.

**Whole test suite:** `make test` → 101 passed.

---

## 2. What is provisional, cut or left over

| ID | Item | Why | What makes it final |
|---|---|---|---|
| P1 | The 5 gold entries (`evals/gold/`) | Drafted by a model, not by you. `gold_status: pending_maintainer_verification`. | T7. |
| P2 | The copies of those 5 in `entries/` | Marked `contributor.type: human` as you instructed, with a note saying they are model drafts awaiting verification. They do not carry the agent-written badge. | `make sync-gold` after T7. |
| P3 | Every eval number | Gold is unverified; one vendor's models wrote the drafts, the grades and the gold. | T7, then `make evals`. |
| P4 | The exception post (`fe-2026-0010`, `fe-2026-0011`) | Does not meet your qualification rule: no stated hypothesis. | Your decision (T3). |
| P5 | `contributor.handle: HANDLE-TBD` in all 15 entries | The session could not read your `gh` login. | T2. |
| P6 | Git history | Built in a scratch git directory, because the sandbox refused `git init` in this folder, then loaded here from `history.bundle` once you ran `git init` (T1, done). Commits were made in build order from files that already existed, so their timestamps cluster late in the session and do not show the real pace of work. | Nothing: it is what it is. Say so if anyone reads the history as a timeline. |
| P7 | Pull requests, the issue-form workflow, the validation Action | No remote. | T6. |
| P8 | Plugin loaded in Claude Code | Never loaded. | T8. |
| P9 | Web page in a real browser, Datasette on a port | Sandbox. | T5. |

**Cut:** nothing from the PRD's cut list.

**Left over in this folder, for you to remove** (I do not delete anything):

- `_trash-review/`: three empty or six-byte probe files I created while testing whether the folder was writable. Git-ignored.
- `.git/`: was a partial directory left by my two failed `git init` attempts. Your `git init` turned it into the real repository; nothing to remove.
- `history.bundle`: a spare copy of the history, git-ignored. Remove it when you no longer want it.

**Departures from the PRD** (all in `DECISION-LOG.md`): classification went past 60 posts (DEC-32); one optional schema field added, `contributor.note` (DEC-13); a sixth MCP tool, `fetch_source` (DEC-22); the source cache sits inside this folder, git-ignored (DEC-52); the decision log is named `DECISION-LOG.md` because writing `DECISIONS.md` was denied by the session's permission settings.

---

## 3. Scouting yields and the selected posts

Full detail: `scouting/yields.md`, `scouting/selection.md`.

**Funnel**

| Step | Posts |
|---|---|
| AI-related candidates from 10 search phrases and 8 tags | 211 |
| Classified by Haiku: round 1, 60 as planned; round 2, the other 152 | 212 |
| Labelled a genuine failed-experiment write-up | 49 (23%) |
| Round 1 only: yes of 60 | 18 (30%) |
| Audited field by field by Sonnet | 49 |
| Support every required schema field, with a verbatim quote | **9** |

212 is one more than 211 because one of the two posts the PRD names was not found by any phrase or tag and was added by title.

**Which required field the other 40 lacked** (a post can lack several): `hypothesis` 20, `claim_scope` 18, `models` 16, `failure_type` 11, `result_direction` 1.

**Yield by route** (yes / classified, both rounds; a post counts under every route that found it)

| Route | Candidates | Yes / classified | Yield |
|---|---|---|---|
| phrase "negative result" | 23 | 13 / 23 | 57% |
| phrase "null result" | 13 | 6 / 13 | 46% |
| phrase "we tried" | 27 | 8 / 27 | 30% |
| phrase "failed to replicate" | 7 | 2 / 7 | 29% |
| phrase "did not improve" | 16 | 4 / 16 | 25% |
| phrase "didn't work" | 6 | 1 / 6 | 17% |
| phrase "postmortem" | 14 | 2 / 14 | 14% |
| phrase "retrospective" | 16 | 2 / 16 | 12% |
| phrase "lessons learned" | 16 | 1 / 16 | 6% |
| phrase "what went wrong" | 8 | 0 / 8 | 0% |
| tag Activation Engineering | 9 | 7 / 9 | 78% |
| tag AI Control | 4 | 3 / 4 | 75% |
| tag Sparse Autoencoders | 10 | 6 / 10 | 60% |
| tag AI Evaluations | 5 | 2 / 5 | 40% |
| tag MATS Program | 8 | 3 / 8 | 38% |
| tag Postmortems & Retrospectives | 26 | 3 / 26 | 12% |
| tag Interpretability | 3 | 0 / 3 | 0% |
| tag Replication Crisis | 30 | 0 / 30 | 0% |
| tag "negative-results" | does not exist on LessWrong | | |

These are single-model labels on one candidate list, and the round-1 sample was not random. They are coverage evidence, not an estimate of how many such posts exist.

**The 10 seed posts**

| Entry | Post | First author | Published | Made by | Fields supported |
|---|---|---|---|---|---|
| `fe-2026-0001` | Negative Results for SAEs On Downstream Tasks… (GDM update #2) | lewis smith | 2025-03-26 | gold draft | all 7 |
| `fe-2026-0002` | J-Lens: A Failed Replication on GPT-2 | Nelith Bandularatne | 2026-09-07 | gold draft | all 7 |
| `fe-2026-0003` | Attempt at Finding Alignment Faking on Llama 70B… | skn8733 | 2026-07-20 | gold draft | all 7 |
| `fe-2026-0004` | (Not) Explaining GPT-2-Small Forward Passes with Edge-Level Autoencoder Circuits | David Udell | 2025-07-22 | gold draft | all 7 |
| `fe-2026-0005` | Eval-Awareness Steering detects the Test, Not the Sabotage | sahilraut | 2026-06-25 | gold draft | all 7 |
| `fe-2026-0006` | Do capabilities generalize across propensities? | Emil Ryd | 2026-05-09 | `contribute` skill | all 7 |
| `fe-2026-0007` | Sanity Checks for Sanity Checks for Sparse Autoencoders | Celene Nightingale | 2026-10-31 | `contribute` skill | all 7 |
| `fe-2026-0008` | Classifying representations of sparse autoencoders (SAEs) | Annah | 2023-11-17 | `contribute` skill | all 7 |
| `fe-2026-0009` | Training Models to Predict and Explain Their In-the-Wild Behavior | Adam Karvonen | 2026-09-04 | `contribute` skill | all 7 |
| `fe-2026-0010` | Some negative steganography results | Fabien Roger | 2023-12-09 | `contribute` skill | 6 of 7 (no stated `hypothesis`) |

**Five more entries**, added after you said 10 was a minimum. No further post met the rule, so these are further failed experiments from posts above, drafted only where the post states every required field for that experiment:

| Entry | From the post of | Experiment |
|---|---|---|
| `fe-2026-0011` | `fe-2026-0010` (the exception post) | Iterated fine-tuning of GPT-3.5-Turbo to hide a 1-bit signal |
| `fe-2026-0012` | `fe-2026-0007` | Raising the model dimension to close the gap between SAE architectures |
| `fe-2026-0013` | `fe-2026-0007` | Per-sample magnitude variance as the explanation for the BatchTopK failure |
| `fe-2026-0014` | `fe-2026-0007` | More true features than latents |
| `fe-2026-0015` | `fe-2026-0009` | Open-ended self-explanation training generalising to a held-out setting |

One further draft was not added: the post had predicted the result, so it was not a failure. Links, the experiment each entry covers and why each qualified are in `scouting/selection.md`. Of the PRD's two named examples, the GDM post is `fe-2026-0001`; "My Failed AI Safety Research Projects" was not selected, because it is a roundup whose detail sits in linked write-ups.

Most entries concern sparse autoencoders or nearby interpretability methods. That is what passed the bar, not a choice.

---

## 4. Demo script (about 4 minutes)

Before recording: do T1, T2, T5 and T6. If you skip T6, the two GitHub steps
below become "here is the form and the workflow file", and you say so. If the
plugin does not load (T8), use the fallback under the table.

| Time | Show | Say |
|---|---|---|
| 0:00–0:25 | `README.md`, top | "Failed experiments stay in file drawers, so people repeat dead ends. This is a wiki of failed AI-safety experiments that people and agents both write to and both read. Entries describe experiments, never people." |
| 0:25–1:10 | `site/index.html` in a browser. Tick **failure type → hyperparams_unexplored**, then **badges → agent-written**. Open "All fields" on `fe-2026-0010`. Type `steganography` in search. | "Fifteen entries from real LessWrong posts. Every field is a filter. Each card shows who wrote it, whether anyone reviewed it, a quote the validator found in the post, and how far to trust the negative: this one says retry welcome, low confidence, and the post itself notes later work succeeded." **(D4, D6)** |
| 1:10–1:25 | `make datasette`, the entries table with facets. | "The same data in Datasette, for SQL and JSON." **(D4)** |
| 1:25–2:10 | Claude Code with the plugin. Type: *"I want to steer along an eval-awareness direction to stop a model sandbagging. What's been tried?"* | "The ask skill answers from the wiki only: already tried, where it went wrong, what to avoid, worth retrying, not found. It cites entry IDs and says how weak the evidence is." Then ask about debate with human judges: "And it says plainly when it has nothing." **(D5)** |
| 2:10–2:50 | Same session: *"Contribute this post: <a LessWrong URL not yet in the wiki>"*. Show the pull request it opens, with the badges. | "An agent turns a write-up into an entry. It cannot mark its own work as reviewed. The entry lands as agent-written and unreviewed." **(D1)** |
| 2:50–3:10 | In an entry file, change `failure_type` to `bad_luck`; run `make validate`. Revert. | "One validator guards every path: locally, in the MCP server, and on every pull request. It also checks the quote really is in the post." **(D7)** |
| 3:10–3:30 | GitHub → Issues → New entry form. Show the pull request the workflow opened. | "People contribute with a form. No git needed." **(D2)** |
| 3:30–3:50 | Run the review command from T4 live, or show its commit: `git log --oneline --grep Review`. | "Review is a separate step. It records who reviewed, when and what they checked, and git history keeps it." **(D3)** |
| 3:50–4:10 | `make evals`, then `evals/results/RESULTS.md`. | "Evals run with one command: field accuracy of the contribute skill against five verified entries, and whether the ask skill cites the right entry without inventing failures. Five posts, one vendor: a spot-check, not a benchmark." **(D8)** |
| 4:10–4:20 | `scouting/yields.md`, the funnel. | "One finding: of 49 genuine failure write-ups we found, only 9 stated enough to fill a structured entry. The fields most often missing are the ones that stop a failure report from reading as 'this never works'." |

**Fallback if the plugin does not load:** open a plain Claude Code session in this folder and say: *"Follow plugin/skills/ask/SKILL.md using tools/cli.py. My plan: …"*. The skills name those commands as the alternative to the MCP tools, and that is how they were exercised in this build.

---

## 5. Your to-do list, shortest first

| ID | Task | Time | Exact steps |
|---|---|---|---|
| T1 | Load the commit history | **DONE** | You ran `git init -b main` in this folder at the end of the session, and I then ran the rest: `git fetch --update-head-ok history.bundle '+refs/heads/*:refs/heads/*' '+refs/tags/*:refs/tags/*'` and `git reset`. Result: `git status` clean, 51 commits, 12 branches, tag `pre-seed`. `history.bundle` is now only a spare copy; it is git-ignored. |
| T2 | Set your GitHub handle | 1 min | `make set-handle HANDLE=<your handle>` then commit as it prints. (Your git user name is `pithy-name`. Whether that is also your GitHub handle was not assumed.) |
| T3 | Decide on the exception post | 2 min | Keep `fe-2026-0010` and `fe-2026-0011` (they say plainly that the post poses a question), or back them out: `git revert -m 1 c20c7d1` then `git revert -m 1 61b12aa`, then `make site`. Backing out leaves 13 entries from 9 posts. |
| T4 | Do the human review (D3) | 5 min | 1. `.venv/bin/python tools/cli.py get fe-2026-0008` and open its `source.url` (a short post). 2. Check each field against the post; `plugin/skills/review/SKILL.md` step 3 is the checklist. 3. Record it: `.venv/bin/python tools/cli.py review fe-2026-0008 reviewed --human --handle <your handle> --notes "Checked every field against the post."` (use `contested` and say which field if something is wrong). 4. With a remote this opens a pull request; without one, `.venv/bin/python tools/cli.py merge-local <the branch it printed>`. 5. `git log --oneline --grep Review` shows it. |
| T5 | Look at both browse UIs and pick one | 5 min | `make site` and open `site/index.html`; `make datasette` and open http://localhost:8001/wiki/entries. Recommendation: the web page (D4). Nobody has seen either rendered: check before recording. |
| T6 | Put it on GitHub | 10–20 min | 1. `gh repo create failed-experiments-wiki --private --source . --push`, then `git push origin --all --tags`. 2. Watch the first "Validate entries" run in the Actions tab (D7). 3. Settings → Actions → General → allow GitHub Actions to create and approve pull requests. 4. Create the label `new-entry`. 5. Issues → New issue → New entry: submit one, watch the pull request appear (D2). 6. `make site` again so entry links point to GitHub. **Note:** this gives no pull requests for the existing agent entries, because their branches are already merged. For a real pull request in the demo, contribute a new post (D1). An alternative that I have not tested: push `main` first at commit `291c14b` (the last commit before the agent entries), then push the `entry/*` branches and open pull requests from them, then push the full `main`. Before the repository ever goes public: it contains your first name in a field value (`pending_maintainer_verification`) and in the decision log. |
| T7 | Verify the 5 gold entries | 45–60 min | For each `evals/gold/fe-2026-000N.md`: open its post, use the "Verification notes for the maintainer" at the bottom (they give line numbers into the cached post text in `.cache/lw/text/`), correct any field, set `gold_status: verified`. Then `make validate-gold`, `make sync-gold HANDLE=<your handle>`, commit, `make evals`. Text fields you changed show as STALE: `evals/README.md` gives the one prompt that regrades them. Two rules to decide across the set: whether well-known facts the post does not state (for example a model's developer) may be filled in, and whether `retry_welcome` should be true for a medium-confidence negative. The skill and the gold drafts differ on both, and that is where much of the scored disagreement comes from. |
| T8 | Load the plugin once | 5 min | Try `claude --plugin-dir plugin` from the repository root. I did not confirm that flag against the Claude Code documentation; if it is wrong, add the folder through `/plugin`. Check the MCP server starts and the three skills appear. The server itself starts and answers (`make mcp-smoke`); what is untested is Claude Code loading it. |

**T1 history:** the procedure was first tested on a scratch copy with the same partial `.git/` directory (DEC-54), then run for real in this folder once `git init` had been run (DEC-55).

---

## 6. Decisions and findings

`DECISION-LOG.md` holds every non-trivial decision with its reason and a short
list of findings for the report. Start with DEC-32 (why the bar stayed strict),
DEC-37 (the gold drafts labelled `human`), DEC-44 (how the commit history was
kept), DEC-45 (the exception), DEC-46 (what subagents did and did not do) and
the findings at the end.

Things for the report that the build surfaced:

1. Only 9 of 49 genuine failure write-ups support a full structured entry.
2. The fields posts most often lack are a stated expectation and an exact scope.
3. The `failure_type` list has no value for "the experimental setup was invalid".
4. `models` is required, so human-subject studies and experiments on synthetic data do not fit.
5. Free-text tag fields (`method`, `checks_done`) never matched gold exactly in the eval: two careful passes over the same post choose different tags. A controlled vocabulary would help filtering as well as scoring.
6. The validator caught real skill mistakes on first use (2 of 5 drafts).
7. LessWrong has no tag for negative results.

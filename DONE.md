# DONE

The proof of concept is built and works locally, with **15 entries** from 10
posts. The repository was pushed to GitHub on 2026-11-15 and is public. The
validation workflow has run there: its first run failed on a test-suite bug
(since fixed) and every run since has passed. **Two things have not happened on
GitHub:** the wiki's own tools have never opened a pull request for an entry or
a review (D1, D3), and the issue-form workflow has never run (D2). Each is marked UNVERIFIED below.

What is left for you to do is in `TODO.md`. This file records what was built and how it was verified.

Every "verified" below was run in this build session on 2026-11-14. Where
something was not run, it says so.

**Verification pass, 2026-11-15.** At your request every function was then
exercised with the demo's recording method (a headless browser, a frame per
step), including what the demo leaves out. The result is `VERIFICATION.md`:
every check passed and the run left this repository unchanged. Statuses below
that this pass changed say so, with what they were before. What the pass
found and fixed is in the decision log (DEC-64 to DEC-69). Rerun it with
`make verify` (add `PLUGIN=1` for the live Claude Code checks).

**Cold reviews, 2026-11-15.** Also at your request, two reviewers who were told
nothing about the project looked at it: one read the demo's frames and
narration as a first-time viewer, and fresh Claude Code sessions used the
plugin as a first-time user would. What they found and what was changed is in
DEC-70 to DEC-80. Three changes touch things stated below, so read these first:

| Changed | Now | Was |
|---|---|---|
| Who the five reference entries are attributed to | `contributor.type: agent` until you verify them (DEC-71; confirm or undo in `TODO.md` T11) | `contributor.type: human` with a note |
| The handle on every entry | Your `gh` login (DEC-72; T11) | The placeholder `HANDLE-TBD` |
| Live runs of the `contribute` and `review` skills through the plugin | Done, in a scratch clone with no remote (DEC-75) | Never run through the plugin |

So wherever this file says "10 agent-written", the page now shows 15: the ten
entries the `contribute` skill wrote and the five reference drafts.

---

## 1. Definition of done, D1–D8

Run every command from the repository root. `make setup` first if `.venv/` is missing.

| ID | Capability | Status | In one line |
|---|---|---|---|
| D1 | An LLM can contribute | **PASS locally · pull request UNVERIFIED** | Skill drafts → validator → branch → merge worked for 10 entries. No pull request was opened: the build had no remote. A remote exists now; the pull-request code path is still untested (T6). |
| D2 | A person can contribute | **BUILT · live run UNVERIFIED** | Issue form and workflow exist; the form-to-entry conversion passes its tests. The form shows on GitHub, but no issue has been filed, so the workflow has never run there. |
| D3 | A person or agent can review | **PASS locally · pull request UNVERIFIED (remote now exists)** | An agent review changed `fe-2026-0007` from unreviewed to reviewed, with reviewer, date and notes, in its own commit. The human review is yours to do (T4). |
| D4 | Browse and filter by hand | **PASS, seen in a browser and on a port** (2026-11-15; was "PASS by test · not seen in a browser or on a port") | Both UIs list all 15 entries and filter on every field. Every value of every field was ticked in a real browser and compared with the entry files; Datasette was rendered in process and on a local port. |
| D5 | An agent can ask "what's been tried?" | **PASS, including inside Claude Code** (2026-11-15; was "inside Claude Code UNVERIFIED") | 7 answers in the required five-part format, two of them an honest "not found". The plugin was then loaded in headless Claude Code sessions: six tools, three skills, a live search, and the `ask` skill answering one question through the plugin's tools. |
| D6 | The wiki is seeded | **PASS for 9 posts by your rule · the 10th is an exception awaiting your call** | 15 entries; every quote is 15 words or fewer and was found in the fetched post. One post does not meet your qualification rule (T3). |
| D7 | Validation guards the wiki | **PASS, locally and on GitHub** | The validator rejects every class of bad entry in tests, and rejected two real skill drafts during seeding. The validation Action ran on GitHub from 2026-11-15: the first run failed on a test-suite bug (since fixed); every run since has passed. |
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
    `git log --oneline --graph`. The commits were made in build order from files that
    already existed, so their timestamps cluster late in the session and do not show the real pace of work.
  - Two of the first five drafts were **rejected by the validator** on first submission
    (`limitations` written as a list) and resubmitted after the fix. The skill
    file now states the field types (v0.2).
- **See it:** `.venv/bin/python tools/cli.py get fe-2026-0006` shows the badges `agent-written`, `unreviewed`, `retry-welcome`.
- **UNVERIFIED:**
  1. A real pull request: `submit_entry` pushes the branch and runs `gh pr create`, and that code path has never run (T6).
  2. The plugin loaded in Claude Code (T8). *Verified 2026-11-15 for loading, the tools and the `ask` skill (`VERIFICATION.md`, the `plugin-…-live` checks). The `contribute` and `review` skills were also run live through the plugin on 2026-11-15, in a scratch clone with no remote (DEC-75).*
  3. The subagents had no command access, so they read the post from the cache the orchestrator prepared, not through `fetch_source`, and the orchestrator ran the submit step with their drafts.

### D2. A person can contribute

- **Built:** `.github/ISSUE_TEMPLATE/new-entry.yml`, `.github/workflows/issue-to-pr.yml`, `tools/issue_to_entry.py`, and `tools/form_link.py`, which pre-fills the form from an AI draft (DEC-89).
- **Verified:** `.venv/bin/python -m pytest tests/test_issue_to_entry.py -q` → 6 passed. The tests feed a realistic issue-form body and check the result is a schema-valid entry with `contributor.type: human`, that the form's labels and dropdowns match the schema, and that bad forms are refused with a readable reason.
- **Verified 2026-11-15:** form text built from the form's own labels was run through the converter in a throwaway clone: it produced a valid entry marked human-written and unreviewed, every field came through unchanged, and unticked boxes or a value outside a closed list were refused with the reason (`VERIFICATION.md`: `issue-form`, `issue-form-refusals`, `issue-form-round-trip`).
- **Fixed 2026-11-16:** GitHub did not show the form until a dropdown option "None" was renamed (DEC-85).
- **UNVERIFIED:**
  1. The workflow has never run. No test issue was filed from the build session, because an entry filed by an agent must not sit in the wiki as a person's (DEC-43). The live run is T12.
  2. Whether GitHub fills every text field from a `tools/form_link.py` link (T12).

### D3. A person or agent can review

- **What ran:** a Sonnet subagent followed `plugin/skills/review/SKILL.md` on `fe-2026-0007`, checked 11 items against the post and decided `reviewed`. The orchestrator recorded that decision with `tools/cli.py review` (the function behind the MCP tool `review_entry`).
- **Evidence:** `git log --oneline --grep "Review fe-2026-0007"` shows the review commit on branch `review/fe-2026-0007-20261114` and its merge. `entries/fe-2026-0007.md` has `review.status: reviewed` and a reviewer with `type: agent`, the date, the model and notes.
- **Read this:** that review was done by the same model that wrote the entry. The notes say so, and the web page labels it "Reviewed by an agent only". Treat it as a demonstration of the mechanism, not as vetting.
- **Verified 2026-11-15, in a throwaway clone:** a human review marking an entry contested and an agent review marking one reviewed, each on its own branch and merged through validation; and a draft that claimed to be human-written and already reviewed was still stamped agent-written and unreviewed (`VERIFICATION.md`: `review-contested`, `review-by-agent`, `submit-cannot-self-promote`).

### D4. Browse and filter by hand

**Web page**

- **Build:** `make site` → `site/index.html` (one file, about 95 KB, no external requests). Open it in a browser.
- **Verified:** `.venv/bin/python -m pytest tests/test_build_site.py -q` → 10 passed on 2026-11-14 (the file now holds 13 tests; `make test` is the current run). Among them:
  - every schema field has a control (facet, range or text search), checked against the field catalogue;
  - the filter logic passes 37 checks in a real JavaScript engine (`tests/js/filter_test.js`);
  - the page's own script was executed against a stand-in DOM: it rendered one card per entry and reacted to search, a facet tick and "clear" (`tests/js/dom_test.js`);
  - entry text containing `</script>` cannot break out of the page.
- **Was not verified on 2026-11-14:** nobody had looked at it in a browser; the sandbox blocked opening one.
- **Verified 2026-11-15 in a real browser engine** (headless Chromium, `tests/test_e2e_browser.py`, run by `make test`): every value of every facet field ticked and the cards compared with the entry files; every range field; search; combined filters; clear; every value written to a link and read back; the full view of every entry; badges and links on every card; the phone layout; the dark scheme; hostile text. Screenshots of each state were looked at (`--snap-dir`). Looking found four defects that no earlier test had, all fixed (DEC-65): an opened entry closed on any filter change and never reached the link; the committed page was stale; on a phone every filter group sat open above the first result; one link test compared two empty lists.
- **Still unseen:** the page in Safari or Firefox, and by a person. Chromium is the only engine it has run in.

**Datasette**

- **Verified on the real entries:** `make datasette-check` runs Datasette in process and prints a listing, the facets and one filter of each kind (enum, array, boolean, date range, number range, full-text). Output from this build: 15 entries; 10 agent-written (all 15 are agent-written now); `failure_type = hypothesis_false AND method contains sae` → `fe-2026-0007`, `0012`, `0014`; search "steganography" → `fe-2026-0010`, `0011`.
- **Was not verified on 2026-11-14:** serving on a port; the sandbox forbade listening sockets.
- **Verified 2026-11-15:** Datasette's own pages rendered in a browser twice, answered in process and served on a local port as `make datasette` does: the table with facets, a facet link, list-field filters and full-text search, each compared with the entry files (`VERIFICATION.md`, the `datasette-…` checks).

**Recommendation: use the web page for the demo.** It shows what the project is about at a glance: badges, the "awaiting verification" notes, quotes and scoped claims on every card, with no server to start. Show Datasette for ten seconds as the path for power users and agents (SQL, JSON, facets on any column).

### D5. An agent can ask "what's been tried?"

- **What ran:** seven Sonnet subagents each followed `plugin/skills/ask/SKILL.md` on one question from `evals/ask_questions.json`.
- **Evidence:** `evals/results/ask/q1.md` … `q7.md`. Read `q5.md` (a match) and `q7.md` (nothing found). Each has the five headings, cites entry IDs, separates weak from strong evidence, and names what the wiki does not cover.
- **Scores (PROVISIONAL): 6 of 7 passed** — 4 of 5 match questions, 2 of 2 no-match questions. Every match answer cited the expected entry and named the gold failure type. The one failure, `q5`, was failed by the judge for one detail the entry does not state (that the 5-point threshold was fixed in advance; the entry says only that the headline layer was pre-registered). Reasons are in `evals/results/ask_judgements.json`. The answers were written when the wiki held 10 entries.
- **MCP server, verified:** `make mcp-smoke` starts the server through `plugin/mcp/run.sh` (the launcher the plugin uses), connects over stdio, lists the six tools and runs a search. It returned 5 matches of 10 entries at the time, with badges.
- **See it yourself without the plugin:**
  `.venv/bin/python tools/cli.py search "steer evaluation awareness direction to stop sandbagging"`
- **Verified 2026-11-15, inside Claude Code:** headless sessions started with `--plugin-dir plugin` listed the six tools and the three skills, ran a live search, and ran the `ask` skill on the steering question: it searched through the plugin's tools, answered from `fe-2026-0005` with its trust labels, and listed what the wiki does not cover. One question, one run: it shows the path works, not how often the answer is right.
- **UNVERIFIED:**
  1. Inside Claude Code (T8). *See the line above: done on 2026-11-15, headless. An interactive session is still yours to try.*
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
- **Verified 2026-11-15 from the command line:** nine kinds of broken entry each refused with the expected reason, and a draft with an invented quote refused by the submit path with no branch or file created (`VERIFICATION.md`, the `validate-…` checks and `submit-rejected`).
- **Try it:** change `failure_type` in any entry to `bad_luck` and run `make validate`. It exits 1 and names the field.
- **Verified on GitHub 2026-11-15:** `.github/workflows/validate.yml` ran on the first push. That run failed on a test-suite bug (since fixed); every run since has passed.

### D8. Skill evals

- **Run:** `make evals` → `evals/results/results.json` and `evals/results/RESULTS.md`.
- **Result of this build (PROVISIONAL):**
  - `contribute`: overall field accuracy **78%** on 5 gold posts (mean over 26 scored fields). All 5 scored drafts were schema-valid with a valid quote. Enum fields 60–100%; source fields 100%; text fields by rubric: `claim_scope` 90%, `hypothesis` 70%, `limitations` 60%; free-tag lists `method` and `checks_done` 0% on exact set match.
  - `ask`: **6 of 7** passed.
  - The full table and every mismatch are in `evals/results/RESULTS.md`.
- `make evals` re-scores saved outputs and calls no model. Producing the outputs and the grades is a model step, documented in `evals/README.md`.

---

## 2. What was cut or left over

**Cut:** nothing from the PRD's cut list.

**Left over in this folder:** `TODO.md`, "Leftovers to remove when you like".

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

## 4. Demo

Moved out of this file on 2026-11-15:

- `demo/script.md`: narration for a 6-minute demo, scene by scene, generated from `demo/scenes.yaml`.
- `demo/out/demo-draft.mp4`: the full cut (6:34, captions and voice), built by `make demo-video` and reviewed
  frame by frame in the build session (DEC-62). `demo/out/demo-short.mp4` (5:03, `make demo-short`) and
  `demo/out/demo-short-voice.mp4` (4:53, the narrated cut embedded in the README) are the short cuts.
- `demo/live-demo-script.md`: the shorter script for recording live, which used to be this section.

---

## 5. What is left for you

Moved to `TODO.md` on 2026-11-15, with the same task IDs (T1 to T8), T9 (the demo video), T10 (licence) and T11 (two overnight changes).
Every "T" reference in this file points there. T1, loading the commit history, is done.

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

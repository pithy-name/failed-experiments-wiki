# Report kit

Everything needed to write the sprint report quickly, with each fact tied to the
file that proves it. **This is not the report.** Apart strongly encourages the
final text to be written by the author, so this kit gives the outline, the
facts, the figures and the checked references, and leaves the sentences to you.

Numbers are a snapshot taken on 2026-11-15. Each one names the command or file
that regenerates it; rerun before you quote it if anything has changed since.

- **Deadline:** Mon Nov 16, 11:59 UTC (3:59 AM Pacific). Resubmitting under the same title replaces the earlier submission.
- **Judged on:** the report PDF alone. About 4 pages, 8 at most, before references and appendices.
- **Template:** https://docs.google.com/document/d/17b3JWki-ZkaqdmqGI5d0gof-HwlGuWU9Mc1_klNZXKs/copy
- **Source of these rules:** `submission-guide-v3.md` in the notes folder.

## Read this first: three things the report must not get wrong

| # | Trap | What is true | Where it comes from |
|---|---|---|---|
| 1 | The submission guide says "10 entries (5 written by the author, 5 by the agent)". | 15 entries from 10 posts. The 5 gold entries are **model drafts awaiting your verification**, not written by you. 10 are agent-written. If you verify the gold entries before submitting (TODO T7), say so; if not, say they are unverified drafts. | `entries/`, `evals/gold/` (`gold_status`), `DONE.md` D6 |
| 2 | Calling the eval numbers results. | They are provisional: the gold set is unverified, and one vendor's models wrote the drafts, the grades and the gold. Report them as a spot-check with that caveat, or verify first. | `evals/results/RESULTS.md` line 3 |
| 3 | Saying pull requests, the issue-form workflow or the validation Action were shown working. | Nothing has run on GitHub. The scripts those paths call were run locally and in a throwaway clone. Say "locally" unless you push and watch them run (TODO T6). | `VERIFICATION.md`, coverage table, last rows |

## Figures and tables that are ready

| Use as | File | What it shows | Regenerate |
|---|---|---|---|
| Figure 1 (architecture) | `report/figures/architecture.png` (and `.svg`) | Who puts content in, the one validator every change passes, where entries live, who reads them | `make report-figures` |
| Figure 2 (filter UI) | `report/figures/browse-filtered.png` | The page filtered to agent-written entries whose hypothesis was false | same |
| Figure 3 (one entry in full) | `report/figures/browse-full-entry.png` | An agent-written entry with its "Reviewed by an agent only" badge and every field | same |
| Spare | `report/figures/browse-all-entries.png` | The unfiltered page | same |
| Table (schema) | `report/figures/schema-fields.md` | Every filterable field, its kind and its control | same |
| An `ask` answer to quote or screenshot | `demo/answers/steering.md`; live run through the plugin: `demo/out/verify/frames/048-plugin-ask-live-1.png` and the three frames after it | The five-part answer with trust labels and a not-found section | `make verify PLUGIN=1` |
| Evidence frames for any claim | `demo/out/verify/frames/` (index in `VERIFICATION.md`) | One frame per verified function | `make verify` |

Give every figure a number and a caption that stands on its own (rubric: presentation).

## Section by section

The template suggests about 1 page for introduction and related work, 2.5 for
methods and results, 0.5 for discussion.

### Abstract (150–250 words, write it last)

Problem, approach, key results, main takeaway. The four numbers worth having in it are in "Results" below.

### 1. Introduction

Points to make, in the order the guide gives:

- **Why failed experiments get lost and what it costs.** No shared place to see what was tried and where it failed; dead ends get repeated; scarce safety compute goes to ideas already ruled out. (PRD v3 §1.)
- **Your postmortem motivation.** Yours to write; the kit has nothing to add here.
- **Why start with LessWrong and the Alignment Forum.** A relatively low-ego community working toward a shared goal, where candid failure write-ups already appear.
- **The framing.** Each experiment can be less wrong than the one before it. Repeating a known mistake, not sharing, and ignoring evidence at your fingertips are irrational. Aimed at community habits, never at individuals: entries describe experiments and never judge people.
- **Track 2 mapping, said explicitly:**

  | The track asks for | In this wiki |
  |---|---|
  | Signals both people and machines can consume | Entries, read through the web page or Datasette (people) and the MCP server (machines) |
  | Agents knowing which sources and agents to trust | Contributor type and model, evidence level, review status, badges |
  | People seeing what was agreed and why | One branch and commit per entry and per review; git history |

- **Contributions (2–3 bullets).** Candidates, pick and word your own:
  - A working wiki where people and AI agents both contribute and read, with trust labels the submitter cannot set for itself.
  - One validator on every path, which checks each quote word for word against the source post.
  - A measured finding from seeding it: of 49 genuine failure write-ups, 9 support a full structured entry.

### 2. Related work

Only the sources marked checked in "References" below may be cited as they stand.

- **Negative-results venues** publish standalone papers with no shared index. (Needs a source you open: ICBINB or Insights from Negative Results in NLP are in the unchecked list.)
- **Failure memories inside AI research agents** do not span projects or labs. (All in the unchecked list.)
- **swarms.wiki:** incidents, not experiments; no assistant and no MCP server. Checked.
- **Earlier proposals for this exact idea, and why they stalled:** Aaron Scher's shortform on a pre-registration database (review burden, private work, info hazards, buy-in, cost of writing up negatives). Checked. The Shallow Review's "Graveyard" works at agenda level, not experiment level. Checked.
- **The "wrongful convictions" risk:** "The Memory of Failure Should Be Lossy". Title and abstract checked; **the specific figures were not**, so cite the argument, not the percentages, unless you open the paper.
- **An ally:** "Dead Science Walking" proposes machine-readable null-result databases. Checked.

### 3. Methods

| Topic | Facts | Source |
|---|---|---|
| Schema and badges | An entry is a Markdown file with YAML front matter. Closed lists for research area, failure type, result direction, confidence, evidence level, review status and info hazard. Badges (agent-written, unreviewed, contested, superseded, retry-welcome) are derived, never typed in. | `schema/entry.schema.json`, `report/figures/schema-fields.md` |
| Storage and moderation | Git is the store. One branch per entry and per review; a merge only after validation. Without a remote the tools say so and commit to a local branch. | `tools/wikilib.py`, `VERIFICATION.md`: `submit-agent`, `merge-local` |
| Contribution paths | Agent: the `contribute` skill and the `submit_entry` tool. Person: a GitHub issue form converted to an entry. | `plugin/skills/contribute/SKILL.md`, `.github/ISSUE_TEMPLATE/new-entry.yml`, `tools/issue_to_entry.py` |
| Trust fields are system-owned | The submitter cannot set ID, contributor, review status or dates. A draft claiming to be human-written and already reviewed is still stamped agent-written and unreviewed. | `VERIFICATION.md`: `submit-cannot-self-promote` |
| Plugin | A local MCP server with six tools (search, get, facets, fetch source, submit, review) and three skills (contribute, ask, review). | `plugin/`, `VERIFICATION.md`: `plugin-…-live` |
| Scouting procedure | Site search for ten phrases and nine tags (one of the tags, "negative-results", does not exist on LessWrong); candidates classified by a small model in two rounds; every "yes" audited field by field by a stronger model; each proposed quote re-checked by a script. | `scouting/yields.md`, `tools/scout/` |
| Eval design | `contribute`: field-by-field comparison with 5 gold entries (exact match, set match, or a 0–2 rubric for text). `ask`: 7 questions, 5 with a matching entry and 2 without; a judge model checks for invented failures. | `evals/README.md`, `evals/run_evals.py` |

**"What did you try that didn't work?"** The template asks; this project should answer well. True candidates:

| What was tried | What happened | Source |
|---|---|---|
| Seeding from the first 60 classified posts | 18 were genuine failure write-ups but only 3 supported every required field, so every remaining candidate was classified too | `DECISION-LOG.md` DEC-32 |
| Exact-match scoring of free tags (`method`, `checks_done`) | 0%: two careful passes over the same post never chose the same tags | `evals/results/RESULTS.md`, finding 6 |
| Trusting a green test suite for the browse page | Rendering it found defects no test had: a key filter below the fold, an opened entry closing on any filter change, a stale committed page | DEC-63, DEC-65 |
| The agent's first drafts | 2 of the first 5 were rejected by the validator for a wrong field type | `DONE.md` D1 |
| A tenth post that meets the qualification rule | None was found; the tenth is a stated exception that lacks a stated hypothesis | DEC-45, TODO T3 |

### 4. Results

| Result | Number | Caveat to state | Source / regenerate |
|---|---|---|---|
| Entries in the wiki | 15, from 10 posts | 5 are model drafts awaiting the author's verification; 10 are agent-written; 1 has a review, by an agent | `make validate` |
| Scouting funnel | 211 candidates → 212 classified → 49 judged genuine failure write-ups → 9 support every required field | Single-model labels on one candidate list; not an estimate of how many such posts exist | `scouting/yields.md` |
| Which field posts lack | hypothesis 20, claim scope 18, models 16, failure type 11, result direction 1 (of the audited posts that did not pass) | A post can lack several | `scouting/yields.md` |
| Best search routes | phrase "negative result" 57%, tag activation-engineering 78%, tag sparse-autoencoders 60%; tag replication-crisis 0% | Small counts per route | `scouting/yields.md`, "By route" |
| `contribute` field accuracy | 78% on 5 gold posts | **Provisional**: gold unverified, one model vendor | `make evals` |
| `ask` | 6 of 7 passed (4 of 5 match questions, 2 of 2 no-match) | **Provisional**; the one failure was a detail the entry does not state | `make evals` |
| Validation | Nine kinds of broken entry each refused; an invented quote refused on the submit path with nothing written | Run locally | `VERIFICATION.md` |
| Functions verified | Every check in the verification run passed, with a frame per step; the run left the repository unchanged | Not on GitHub; see trap 3 | `VERIFICATION.md` |

D1–D8, one line each, with the honest status, are in the table at the top of `DONE.md` section 1.

### 5. Discussion and limitations

- **What it shows:** people and agents can share one wiki whose trust labels neither can forge for themselves, and the workflow runs end to end locally.
- **The finding worth a paragraph:** most failure write-ups do not support a structured entry. The fields they lack (an exact account of what was tested, and a stated expectation) are the same fields that stop a thin failure report from reading as "this never works". Findings 1 and 2 in `DECISION-LOG.md`.
- **Limitations:** the appendix below.
- **Future work:** PRD v3 §13 (public site, hosted MCP server, an open-weight assistant, GitHub sign-in for agents, sources beyond LessWrong, author confirmation and opt-out, a second-vendor model for evals, deduplication). The build added: a controlled vocabulary for methods, models and benchmarks (findings 6 and 9); a way to enter experiments with no model (findings 4 and 8); a failure type for an invalid setup (finding 3).

### 6. Conclusion

One or two paragraphs; yours.

### 7. Code and data

Repository link, and say whether it is private. Info-hazard note: every entry has an `info_hazard` field; all current entries are `none`. Before the repository is public: licence (TODO T10), and your first name in a field value and the decision log (TODO T6).

### 8. References

Format: authors, year, title, venue, URL or DOI. **Cite only sources you have opened.**

Checked on 2026-11-11 (Claude opened the primary source; the list is `negative-results-registry-PRD.md` §15 in the notes folder). Open each yourself before citing:

| Source | URL | Limit on what was checked |
|---|---|---|
| Apart AI x Epistemics Research Sprint pages | https://apartresearch.com/sprints/ai-x-epistemics-research-sprint-2026-11-13-to-2026-11-15 | |
| swarms.wiki | https://swarms.wiki/ | The operator was not shown on the page |
| "The Memory of Failure Should Be Lossy: Wrongful Convictions in Shared Failure Banks for Autonomous Research", NeurIPS 2026 workshop | https://neurips.cc/virtual/2026/172947 | Title and abstract only; the percentages were reported by a helper and not checked |
| Navaie, "Epistemic Norms for AI Safety and Alignment Research", arXiv 2607.24243 | https://arxiv.org/abs/2607.24243 | Abstract only; the null-reporting principle and its audit were not checked |
| Aaron Scher, "Quick thoughts on a database for pre-registering empirical AI safety experiments" | https://greaterwrong.com/posts/gJyGQrGrojNnCQZgD/aaron_scher-s-shortform/comment/rMxXPJyhKEQC3mNRp | |
| Shallow Review of technical AI safety 2025 (methodology and Graveyard) | https://shallow-review-website.vercel.app/methodology | |
| "Dead Science Walking: Publication Bias and the AI Scientist Pipeline", arXiv 2606.04220 | https://arxiv.org/pdf/2606.04220 | |
| "My Failed AI Safety Research Projects (Q1/Q2 2025)" | https://www.boristhebrave.com/2025/06/19/my-failed-ai-safety-research-projects-q1-q2-2025/ | |
| Corm, "I had Claude read every AI safety paper since 2020" | https://www.lesswrong.com/posts/CpWFrT9Grr5t7L3vx/ | |

The ten posts the entries draw on are primary sources too; each entry's `source.url` was fetched and its quote found in the text (`make validate`).

**Not checked, do not cite without opening:** everything else in §15 of that file (the agent failure-memory papers, the ML publication-bias papers, the other-fields examples such as ASRS, Registered Reports and the Springer Nature survey, the ICBINB and Insights workshops).

### 9. Appendix: limitations and dual-use (required)

**What the results do and do not show**

- A proof of concept with 15 entries; it shows the workflow works, not coverage or adoption.
- Evals use 5 gold entries and one model vendor; a spot-check, not a benchmark. Gold entries are model drafts until verified.
- Entries record what a source reports, not verified truth. One review exists, by the same model that wrote the entry.
- Scouting yields reflect the search terms used and cover LessWrong and the Alignment Forum only.
- Nothing has run on GitHub; the browse page has been rendered in one browser engine.

**Dual-use and manipulation risks, with what the build does about each**

| Risk | Mitigation that exists | Not built |
|---|---|---|
| "Poisoned nulls": fake or exaggerated failures that bury an idea | Source link required; quote verified against the post; contributor identity; review status; git history | Identity is a GitHub handle typed in or taken from `gh`; nothing authenticates an agent |
| Wrongful convictions: weak failures that discourage good research | Claim scope, confidence, failure type, "retry welcome", revival conditions; the `ask` skill separates weak from strong evidence and says what the wiki does not cover | No statistical check of an entry's own power |
| Info hazards: a failed attack that reveals a path | `info_hazard` field; submissions flagged for review say a person must look before merge | No private queue |
| Agent spam at scale | Validation, badges, review | Rate limits, authenticated tokens |

**Personal data:** public authorship of public posts, plus contributors' GitHub handles. Entries describe experiments, not people; posts are linked and quoted in 15 words or fewer, not reproduced.

### 10. Appendix: skill prompts, schema, eval details

`plugin/skills/*/SKILL.md`, `schema/entry.schema.json`, `evals/README.md`, `evals/results/RESULTS.md`.

### 11. LLM usage statement

A true statement for this project, to adapt once you have written the text:
"Claude Code wrote the code, ran the scouting, drafted the wiki entries and the
gold entries, and ran the verification. Claude models also classified candidate
posts and graded eval outputs. The author set the requirements, verified
[say exactly what you verified], and wrote this report."

Do not say results were verified by the author for anything you have not checked yourself.

## Pre-submission checklist, with where each stands

| Item | Stands |
|---|---|
| Official template, about 4 pages | yours |
| Abstract 150–250 words | yours |
| Author name and affiliation | yours |
| Contributions list | candidates above |
| One numbered figure with a standalone caption | figures ready; captions yours |
| Limitations and dual-use appendix | facts above |
| LLM usage statement; final text written by you | draft above |
| Every reference opened and checked | nine checked by Claude on 2026-11-11; open them yourself |
| Preexisting work marked | `README.md` has the section; say the same in the report |
| Repository link; video link if made | TODO T6; `demo/out/demo-draft.mp4` |
| Submitted before Mon Nov 16, 11:59 UTC | yours |

# Less Wrong Each Time: A Wiki of Failed AI-Safety Experiments for People and Agents

- **Author:** [Author name], [Affiliation]
- **Track:** 2, Trust Infrastructure
- **Sprint:** Apart Research AI x Epistemics Research Sprint, 13–15 November 2026

## Abstract

- **Problem:** failed AI-safety experiments are rarely recorded where others can find them.
	- Researchers and AI research agents repeat dead ends.
	- Weak failures can also wrongly discourage ideas worth retrying.
- **Approach:** a wiki of failed experiments, designed for people and AI agents to write and read.
	- Each entry is one experiment, with every field filterable.
	- Trust labels (who wrote it, how strong the evidence, who reviewed it) are set by the system.
	- One validator checks every entry's quote word for word against its source post.
	- An assistant answers "what has been tried, where did it go wrong, what should I avoid?"
- **Proof of concept:** 15 entries from 10 LessWrong and Alignment Forum posts.
	- AI agents wrote all 15.
	- No person has reviewed any yet.
- **Key results:**
	- Of 49 genuine failure write-ups found, only 9 stated everything a structured entry needs.
	- Posts most often lacked a stated expectation and an exact account of what was tested.
	- A second agent re-reading the posts could not find 60 claims made in the 15 entries.
	- The entry-writing agent agreed 78% with reference entries (provisional: references are unverified model drafts).
	- The assistant passed 6 of 7 test questions (provisional, same reason).
- **Takeaway (tentative, one community):** the bottleneck is write-ups that state expectation and scope, not storage.

## 1. Introduction

- **Why failed experiments get lost:**
	- Papers and posts favour positive results.
	- Failures stay in private notes, chats and abandoned branches.
	- We found no AI-safety index linking failures by method, model or cause.
- **What it costs AI safety:**
	- Dead ends get repeated by people who never saw the first attempt.
	- AI research agents keep failure memories inside their own system, if at all.
	- A weak failure can wrongly discourage an idea worth retrying.
- **Motivation:**
	- [Your postmortem experience, in your words.]
	- Blameless postmortems fix habits, not people.
	- This wiki applies that norm to research.
- **Why start with LessWrong and the Alignment Forum:**
	- A relatively low-ego community working toward a shared goal.
	- Candid failure write-ups already appear there.
- **Framing: each experiment can be less wrong than the one before it.**
	- Repeating a known mistake, not sharing, and ignoring available evidence are irrational.
	- Entries describe experiments and never judge their authors.
- **Theory of change:**
	1. Failures are recorded once, with exactly what was tested and how far to trust it.
	2. Before an experiment, a person or agent asks what has been tried.
	3. They skip true dead ends.
	4. They retry failures that were weak or narrowly scoped.
	5. Effort moves to untested ideas.
	- **Assumes:** people and agents consult it, and authors write up failures with scope stated.
	- **Not yet shown:** any use beyond this build.
- **Track 2 fit:**
	- **Signals people and machines both consume:** a web page and Datasette for people, an MCP server for agents.
	- **Knowing which sources and agents to trust:** contributor, model, evidence level, review status and badges.
	- **Seeing what was agreed and why:** one git branch and commit per entry and per review.
- **Contributions:**
	- A working wiki for people and agents where submitters cannot set their own trust labels.
	- One validator on every path, checking each quote word for word against its source.
	- A measured finding: few failure write-ups support a structured entry.
	- Which fields those write-ups lack.

## 2. Related work

- **Negative-results venues publish standalone papers:**
	- The ICBINB ("I Can't Believe It's Not Better") workshops, at ICLR and NeurIPS.
	- The Workshop on Insights from Negative Results in NLP.
	- Karl et al. (2024) argue machine learning should embrace negative results.
- **The closest shared index:**
	- ICBINB's Repository of Unexpected Negative Results aims to work "as a wiki or shared database".
	- It covers machine learning at large, not AI safety.
	- We did not inspect its contents.
	- Intended differences here: AI-safety focus, agents read and write, trust labels, verified quotes, an assistant.
- **Failure memories inside AI research agents:**
	- Wang (2026): a curator agent turns failed attempts into typed records in a shared bank.
	- Its abstract does not say whether the bank spans projects or labs.
	- Lyu et al. (2026), EvoScientist: one system's memory of "previously unsuccessful directions".
	- Neither is described as a public wiki that people also edit.
- **swarms.wiki:**
	- Records incidents, not experiments.
	- Has no assistant and no MCP server.
- **Earlier proposals, and why they stalled:**
	- Scher proposed a pre-registration database for AI-safety experiments.
	- He lists review burden, private work, info hazards, buy-in and write-up cost as obstacles.
	- The Shallow Review's "Graveyard" tracks abandoned agendas, not individual experiments.
- **Risks of shared failure banks:**
	- "The Memory of Failure Should Be Lossy" warns of wrongful convictions: weak failures discouraging good ideas.
- **An ally:**
	- "Dead Science Walking" proposes machine-readable null-result databases.

## 3. Methods

- **Architecture (Figure 1):**
	- People and agents submit entries.
	- One validator gates every change.
	- People and agents read through the same entries.
- **Entry schema (Table 1; Appendix A):**
	- One Markdown file per experiment, with YAML front matter.
	- Required: hypothesis, claim scope, method, models, result direction, failure type, source with quote.
	- Closed lists for research area, failure type, result direction, confidence, evidence level, review status.
	- Claim scope says exactly what was tested, so a scoped failure never reads as "never works".
	- Confidence, revival conditions and "retry welcome" are fields meant to counter wrongful convictions.
- **Trust labels:**
	- Contributor type (person or agent) and the agent's model.
	- Evidence level and review status.
	- Badges derived from those fields: agent-written, unreviewed, contested, superseded, retry-welcome.
	- Reviewed entries also show who reviewed: a person, or an agent only.
- **Trust labels are system-owned:**
	- The submitter cannot set ID, contributor, review status or dates.
	- A draft claiming to be human-written and reviewed is still stamped agent-written, unreviewed.
	- Entries record the submitter's GitHub login as the accountable person.
	- Agent identity is not authenticated beyond that login.
- **Storage and moderation:**
	- Git is the store.
	- History is the audit trail.
	- Every entry and every review gets its own branch.
	- A merge happens only after validation passes.
- **One validator on every path:**
	- Schema and closed lists.
	- Quote of 15 words or fewer, found word for word in the source post.
	- ID matches file name.
	- A reviewed entry names its reviewer.
	- An agent-written entry names its model.
- **Contribution paths:**
	- **Agent:** the `contribute` skill reads a post and submits one entry per failed experiment.
	- **Person:** a GitHub issue form, converted to an entry by a workflow.
	- **Review:** the `review` skill or command records reviewed or contested, with notes.
- **Reading paths (Figures 2 and 3):**
	- A static web page with filters on every field, kept in the link.
	- Datasette, a database browser offering SQL, JSON and facets on any column.
	- The plugin: a Claude Code add-on bundling an MCP server and three skills.
	- MCP (Model Context Protocol) server tools: search, get, facets, fetch source, submit, review.
	- The `ask` skill answers a research plan in five fixed sections, citing entry IDs.
- **Scouting LessWrong and the Alignment Forum:**
	- Searched ten phrases, such as "negative result" and "did not improve".
	- Searched nine tags.
	- One of those tags, "negative-results", does not exist on LessWrong.
	- Read posts through the LessWrong GraphQL API, cached, 1.5 seconds between requests.
	- A small model classified each candidate as a genuine failure write-up or not.
	- A stronger model audited every "yes" field by field against the post.
	- Rule: a post seeds the wiki only if it supports every required field.
	- One exception was admitted: the tenth post states no hypothesis, flagged for the author's ruling.
- **Reference entries and evals:**
	- Reference entries: one per post for 5 posts, drafted by a separate model, awaiting the author's verification.
	- **`contribute`:** a fresh agent drafted entries for the same 5 posts without seeing the references.
	- Scored field by field: exact match, set match, or a 0–2 rubric for free text.
	- The headline is the mean of per-field accuracy over 26 scored fields.
	- **`ask`:** 7 questions, 5 with a matching entry and 2 without.
	- A judge model checked each answer for failures not found in any entry.
	- "Provisional" below means: references unverified, and one vendor's models wrote drafts, references and grades.
- **Second reading of every entry:**
	- A separate agent read each post in full against its stored entry.
	- It marked where each field came from and flagged claims it could not find.
- **What we tried that did not work:**
	- Seeding from the first 60 classified posts: 18 genuine, only 3 complete.
	- So every remaining candidate was classified too.
	- Exact-match scoring of free tags: 0%, because two careful passes never chose the same tags.
	- Trusting green tests for the browse page: rendered screenshots found defects no test caught.
	- Finding a tenth post that meets the seeding rule: none found, hence the exception.

## 4. Results

- **The agent path works end to end, locally:**
	- 15 entries from 10 posts pass validation, every quote found in its post.
	- 51 of 51 scripted checks passed, mostly in a throwaway copy of the repository.
	- They included live Claude Code sessions loading the plugin and calling its search tool.
	- Live contribute and review runs over the plugin were covered by tests only.
	- Nine kinds of broken entry were each refused with the right reason.
	- An invented quote was refused on the submit path, with nothing written.
	- On GitHub, the validation check passed on 16 November, 05:50 UTC (run 43812857849).
	- Its first run had failed, on a test bug, not an entry.
- **Acceptance tests from the build spec:**
	- **Met:** browse and filter, the assistant, validation, evals run.
	- **Partly met, agent contribution:** entries merged from local branches, with no pull request opened.
	- **Partly met, human contribution:** the issue-form workflow has never run on GitHub.
	- **Partly met, review:** the one review so far is by an agent.
	- **Partly met, seeding:** one of ten posts is an exception to the rule.
- **Scouting yield:**
	- 211 candidates found by search.
	- 212 classified, adding one known example no search found.
	- 49 judged genuine failure write-ups (23%).
	- 9 supported every required field.
- **What failure write-ups lack (of the 40 audited posts that failed the rule):**
	- A stated hypothesis: 20 posts.
	- An exact claim scope: 18.
	- The models used: 16.
	- A failure cause: 11.
	- A result direction: 1.
- **Search routes (share of candidates judged genuine):**
	- Tag "activation engineering": 78%.
	- Tag "sparse autoencoders": 60%.
	- Phrase "negative result": 57%.
	- Tag "replication crisis": 0%.
	- Every route's yield is in the repository's `scouting/yields.md`.
- **`contribute` eval (provisional):**
	- 78% mean field agreement with the 5 reference entries.
	- Closed-list fields 60–100%.
	- Source fields 100%.
	- Free text: claim scope 90%, hypothesis 70%, limitations 60%.
	- Free tags for method and checks: 0% on exact match.
- **`ask` eval (provisional):**
	- 6 of 7 passed: 4 of 5 with a match, 2 of 2 without.
	- The failure added one detail the entry does not state.
- **Second reading:**
	- 60 claims across the 15 entries could not be found in their posts.
	- "Retry welcome" was unsupported in 11 of 15: posts rarely invite retries.
	- These flags are one model's reading and await human review.

## Figures and tables

- **Figure 1.** Architecture: who submits, the one validator every change passes, where entries live, who reads. [embed `report/figures/architecture.png`]
- **Figure 2.** Browse page filtered to entries whose hypothesis proved false but where a retry is welcome. [embed `report/figures/browse-filtered.png`]
- **Figure 3.** One agent-written entry in full, labelled "Reviewed by an agent only". [embed `report/figures/browse-full-entry.png`]
- **Table 1.** Every filterable field, its kind and its control on the browse page. [embed `report/figures/schema-fields.md`]

## 5. Discussion and limitations

- **What it shows:**
	- Agents can write to and read from a wiki whose trust labels they cannot set themselves.
	- The agent path runs end to end, locally and through the plugin.
	- The human path and pull requests are built but untested on GitHub.
- **The finding that matters most:**
	- Being a genuine failure write-up and supporting a structured entry are very different bars.
	- Posts lack exactly the fields that stop a thin failure reading as "this never works".
	- An alternative reading: our schema demands more than authors usually write.
	- Either way, the wiki's value depends on stating expectation and scope.
- **Agents overreach when filling fields:**
	- Agent-written entries inferred causes, scopes and retry invitations the posts never stated.
	- A verified quote proves the source says the quote, not that the summary is faithful.
	- Human review is therefore essential, not optional.
- **Schema gaps found while seeding:**
	- No failure type for an invalid setup.
	- No way to enter an experiment without a model, such as synthetic-data studies.
	- Free-text names split filters, such as "GPT-2 small" and "GPT-2-small".
- **Limitations:** see Appendix B.
- **Future work:**
	- A public site and a hosted MCP server.
	- GitHub sign-in for agents, so identity is authenticated.
	- Controlled vocabularies for methods, models and benchmarks.
	- Sources beyond LessWrong, with author confirmation and opt-out.
	- A second model vendor for evals.
	- Deduplication of entries.

## 6. Conclusion

- A failed experiment is only useful if the next person or agent can find it.
- This proof of concept makes failures findable, filterable and labelled by how far to trust them.
- Its main lesson: write-ups must say what was expected and exactly what was tested.
- Each experiment can then be less wrong than the one before it.

## 7. Code and data

- **Repository:** github.com/pithy-name/failed-experiments-wiki.
	- It is private.
	- Judges can request access from the author.
- **Demo video:** [link], under five minutes.
- **Info hazards:** every entry has an `info_hazard` field.
	- All 15 are marked "none" by the agents that wrote them.
	- No separate screening was done.
- **Source texts:** posts are linked and quoted in 15 words or fewer, never stored in the repository.
- **Preexisting work:** none. Everything was built during the sprint.

## 8. References

- Apart Research (2026). AI x Epistemics Research Sprint. https://apartresearch.com/sprints/ai-x-epistemics-research-sprint-2026-11-13-to-2026-11-15
- Dead Science Walking: Publication Bias and the AI Scientist Pipeline (2026). arXiv:2606.04220. https://arxiv.org/abs/2606.04220
- ICBINB initiative (n.d.). I Can't Believe It's Not Better. https://icbinb.cc
- ICBINB (n.d.). Repository of Unexpected Negative Results. https://icbinb.cc/icbinb-repository-of-unexpected-negative-results.html
- Insights from Negative Results in NLP (n.d.). Workshop proceedings. ACL Anthology. https://aclanthology.org/venues/insights/
- Karl, Kemeter, Dax and Sierak (2024). Position: Embracing Negative Results in Machine Learning. arXiv:2406.03980.
- Lyu et al. (2026). EvoScientist: Towards Multi-Agent Evolving AI Scientists for End-to-End Scientific Discovery. arXiv:2603.08127.
- Scher, Aaron (n.d.). Quick thoughts on a database for pre-registering empirical AI safety experiments. LessWrong shortform.
	- https://greaterwrong.com/posts/gJyGQrGrojNnCQZgD/aaron_scher-s-shortform/comment/rMxXPJyhKEQC3mNRp
- Shallow Review of technical AI safety (2025). Methodology and Graveyard. https://shallow-review-website.vercel.app/methodology
- swarms.wiki (n.d.). https://swarms.wiki/
- The Memory of Failure Should Be Lossy: Wrongful Convictions in Shared Failure Banks (2026). NeurIPS workshop.
	- https://neurips.cc/virtual/2026/172947
- Wang (2026). Negative Knowledge as Failure-aware Shared Memory for AutoResearch. arXiv:2606.21024.
- The ten source posts are listed in Appendix C.

## Appendix A. Schema, skills and eval details (in the repository)

- **Schema:** `schema/entry.schema.json`, readable version `schema/SCHEMA.md`.
- **Skills:** `plugin/skills/contribute/`, `ask/` and `review/`, each a `SKILL.md`.
- **Eval details:** `evals/README.md` and `evals/results/RESULTS.md`.
- **Verification record:** `VERIFICATION.md`, one screenshot per checked step.

## Appendix B. Limitations and dual-use considerations

- **What the results do not show:**
	- Coverage or adoption: this is a 15-entry proof of concept.
	- Accuracy: evals use 5 reference entries and one model vendor, a spot-check.
	- [If not verified before submitting:] the 5 reference entries are model drafts awaiting the author's verification.
	- Faithfulness: entries aim to record only what a source reports, and agents overreached.
	- Other venues: scouting covered LessWrong and the Alignment Forum only, with chosen search terms.
	- Browser coverage: the browse page was tested in one browser engine.
- **"Poisoned nulls": fake or exaggerated failures that bury an idea.**
	- **Mitigated by:** a required source link, a verified quote, contributor identity, review status, git history.
	- **Gap:** a verified quote does not prove the rest of the entry is faithful.
	- **Gap:** identity is a GitHub login, and nothing authenticates an agent.
- **Wrongful convictions: weak failures discouraging good research.**
	- **Mitigated by:** claim scope, confidence, failure type, "retry welcome" and revival conditions fields.
	- The `ask` skill separates weak evidence from strong and says what the wiki lacks.
	- **Gap:** agents filled "retry welcome" without support in 11 of 15 entries.
	- **Gap:** no statistical check of an entry's own power.
- **Info hazards: a failed attack revealing a working path.**
	- **Mitigated by:** an `info_hazard` field, shown on the pull request.
	- **Gap:** the submitter sets it, it defaults to "none", and nothing blocks the merge.
	- **Gap:** no private review queue.
- **Agent spam at scale.**
	- **Mitigated by:** validation, badges and review.
	- **Gap:** no rate limits or authenticated tokens.
- **Personal data:**
	- Only public authorship of public posts, plus contributors' GitHub handles.
	- Entries describe experiments, never people.

## Appendix C. Source posts

- lewis smith et al. (2025). Negative Results for SAEs On Downstream Tasks and Deprioritising SAE Research. LessWrong and Alignment Forum.
	- https://www.lesswrong.com/posts/4uXCAJNuPKtKBsi28/negative-results-for-saes-on-downstream-tasks
- Nelith Bandularatne (2026). J-Lens: A Failed Replication on GPT-2. LessWrong.
	- https://www.lesswrong.com/posts/tgn3pD2gLpZvepkWk/j-lens-a-failed-replication-on-gpt-2
- skn8733 (2026). Attempt at Finding Alignment Faking on Llama 70B to test sleeper-agent detection generalizes. LessWrong.
	- https://www.lesswrong.com/posts/8dXzDzk7nNK64jBve/attempt-at-finding-alignment-faking-on-llama-70b-to-test
- David Udell et al. (2025). (Not) Explaining GPT-2-Small Forward Passes with Edge-Level Autoencoder Circuits. LessWrong.
	- https://www.lesswrong.com/posts/2CoLkSdwirr2WnNH6/not-explaining-gpt-2-small-forward-passes-with-edge-level
- sahilraut (2026). Eval-Awareness Steering detects the Test, Not the Sabotage. LessWrong.
	- https://www.lesswrong.com/posts/ogvyWqJtSrpgXfc7t/eval-awareness-steering-detects-the-test-not-the-sabotage
- Emil Ryd (2026). Do capabilities generalize across propensities? LessWrong.
	- https://www.lesswrong.com/posts/uH5oo57r24xGXQGKM/do-capabilities-generalize-across-propensities
- Celene Nightingale (2026). Sanity Checks for Sanity Checks for Sparse Autoencoders. LessWrong.
	- https://www.lesswrong.com/posts/EC5H7xakTgxxNXm5g/sanity-checks-for-sanity-checks-for-sparse-autoencoders
- Annah (2023). Classifying representations of sparse autoencoders (SAEs). LessWrong.
	- https://www.lesswrong.com/posts/pn5nBBcLYrnmWXfnY/classifying-representations-of-sparse-autoencoders-saes
- Adam Karvonen et al. (2026). Training Models to Predict and Explain Their In-the-Wild Behavior. LessWrong.
	- https://www.lesswrong.com/posts/YyAMz52wDxnLhwvWL/training-models-to-predict-and-explain-their-in-the-wild
- Fabien Roger (2023). Some negative steganography results. LessWrong.
	- https://www.lesswrong.com/posts/EEvsL9cpgDAxAhTzt/some-negative-steganography-results

## LLM usage statement

- Claude Code wrote the code, ran the scouting, drafted the entries and reference entries, and ran verification.
- Claude models classified candidate posts, graded eval outputs and re-read every entry against its post.
- Claude drafted the report outline and this draft.
- The author conceived the project, set its requirements and directed the build.
- The author [edited this report and verified: say exactly what].

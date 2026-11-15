# Cold reviews, 2026-11-15

Two reviews by readers who were told nothing about the project, asked for by
the maintainer, and what was done about each finding. The reviewers' own
records are in `raw/`, with machine paths replaced.

| Review | Who | Looked at | Record |
|---|---|---|---|
| Demo, first viewing | A model acting as a first-time viewer, given only frames and the script | The full cut as it was before the rewrite | `raw/demo-viewer-1-full-cut-before-rewrite.md` |
| Demo, second viewing | A fresh model, same questions | The short cut after the rewrite | `raw/demo-viewer-2-short-cut-after-rewrite.md` (see "Second viewing" below) |
| Plugin, first use | Five headless Claude Code sessions with only the plugin, and one subagent that set the plugin up from the README | A scratch clone with no remote | `raw/first-use-*.md` |

**Disposition codes.** *Fixed*: the thing found no longer happens. *Fixed as*:
answered a different way than proposed; the row says how. *Partly*: improved,
and the row says what remains. *Not fixed*: left, with the reason. *Yours*:
needs something only the maintainer has.

## What the first viewer took away, against what the project is meant to say

| The project means to say | Did the first viewer get it? | After the rewrite |
|---|---|---|
| A wiki of failed AI-safety experiments that people and agents both write and read | Yes | Unchanged |
| An agent can answer "what has been tried, where did it go wrong, what should I avoid?" | Yes, as a format; it noted no agent was shown doing it | A real plugin session and an answer written live through the plugin are on screen |
| Why it matters: dead ends get repeated, scarce compute is wasted | **No.** "The video did not make clear why this matters" | The cost is the second and third sentence of the video |
| Why it starts with LessWrong and the Alignment Forum | **No.** Not mentioned by the viewer at all | The second card and its narration |
| "Each experiment can be less wrong than the one before it", as the thing to remember | **No.** "Not clearly"; it remembered the three-bullet slide | The second card's title, the page header, and the last sentence, which names it as the one thing to remember |
| Blameless: experiments, never people | Stated, but **contradicted** by an entry on screen | The entry was reworded; both skills carry the rule |
| Trust signals a reader can rely on | Understood, and found unconvincing where labels disagreed | The labels now agree (DEC-71, DEC-72) |

## Demo: the 22 findings

| # | Sev | Finding, in short | Disposition | What was done |
|---|---|---|---|---|
| 1 | MAJOR | Five cards say "written by human" beside a note saying model draft | Fixed | The five reference entries are labelled agent-written until verified (DEC-71). **Changes an earlier instruction of yours: `TODO.md` T11.** |
| 2 | MAJOR | Narration implies a GitHub repository exists; the people path is shown only as a form file | Fixed as | "Readable on GitHub" is gone; the form scene says there is no GitHub repository yet. The form is still shown as its file, because it has never run (T6). The short cut leaves that scene out. |
| 3 | MAJOR | Four claims spoken over one unchanged git log; no stamp or blocked submission shown | Partly | The scene now shows the entry's system-set fields. A refused submission is not in the video; it is recorded in `VERIFICATION.md` (`submit-rejected`). |
| 4 | MAJOR | The quote check is only ever shown passing; "fetches the post" while the screen says cached | Fixed | A quote the post never said is refused on screen; the narration says a saved copy is used. The unsupported "rejected two drafts" line is gone. |
| 5 | MAJOR | "78% overall" beside rows of 0% that are never mentioned | Fixed as | The narration says which fields agree, why free-text tags score zero, and what the one failed question was. The overall line is on screen. The whole table is not; it is `evals/results/RESULTS.md`. |
| 6 | MAJOR | On-screen answers pass for the scored ones | Fixed | The answer scene says it was written for the demo and is not a scored answer; the eval scene says scoring was done when the wiki held ten entries. |
| 7 | MAJOR | "Only nine" against fifteen entries; no denominators; "classifiers" unexplained | Fixed | The card gives every denominator, how fifteen entries come from nine posts and one exception, and who labelled and who checked. |
| 8 | MAJOR | Caption and outlined field disagree | Fixed | A sentence about a field is no longer shown over the previous picture. Checked on the final frames. |
| 9 | MAJOR | "Never people", then an entry remarks on its author's expertise | Fixed | `fe-2026-0010` reworded; both skills now forbid carrying such remarks even when the author makes them (DEC-74). The close says the authors have not been asked. |
| 10 | MAJOR | The script's header promised disclosures the narration did not make | Fixed | The header says exactly what is and is not shown. |
| 11 | MINOR | Terminal shows output before the question; two match counts; "the right entry" asserted | Fixed | The command appears first, then its output; one search, one count; the narration says it is the one entry that tested exactly this. |
| 12 | MINOR | "The same model that wrote it" is not on screen; status reads plain "reviewed" | Fixed as | The review note, which names the model, is shown in full. Tools now report who reviewed (DEC-79). The status value is unchanged: an agent may still set `reviewed`, as the definition of done asks. |
| 13 | MINOR | The answer's numbers cannot be checked on screen; three dense screens | Partly | The file scene shows the entry's result and limits. The answer is still three screens of text. |
| 14 | MINOR | "Datasette" was a script's text output | Fixed | Datasette's own pages are shown. |
| 15 | MINOR | Terms never explained | Fixed as | True negative, sandbagging, skill and plugin are explained where they first appear; "MCP" is no longer spoken. "Gold" still appears in command output on screen in the full cut. |
| 16 | MINOR | The cost of the problem is asserted, with no real case | **Yours** | Not invented. If you have a real case of a repeated dead end, one sentence in scene 1 would land harder than anything else here. |
| 17 | MINOR | Nearly a minute of cards before the product | Partly | One sentence shorter, but the cards now also carry the LessWrong framing, so the first product screen comes at about the same time. Showing the page first and the ideas second is the alternative. |
| 18 | MINOR | "One model vendor" reads two ways | Fixed | "One company's models wrote the drafts, the references and the grades." |
| 19 | MINOR | "Retry welcome" under "who wrote it, reviewed or not"; panel never scrolled | Fixed | The caption names all three; the panel is scrolled once. |
| 20 | MINOR | Five terminal scenes in a row, with shell noise | Partly | One became a real page and the commands are plainer. The full cut still has four terminal scenes; the short cut has two. |
| 21 | MINOR | Ends with nowhere to try it | Fixed as | The close says it is a local proof of concept and not public yet. No address, because there is none (T6). |
| 22 | MINOR | "I" means three different speakers | Partly | The hypothetical is now "a researcher". "I" is still the maintainer in two places and the agent in the on-screen answers. |

## Demo: second viewing

Run on the short cut after the rewrite, with the same questions and one more
(why it starts where it starts). Its record, when it exists, is
`raw/demo-viewer-2-short-cut-after-rewrite.md`. The decision log (DEC-80)
records what it found and whether the three "No" rows above turned to "Yes".

## Plugin first use: the findings

| # | Finding, in short | From | Disposition | What was done |
|---|---|---|---|---|
| a | `contributor.type: human` beside "model draft" | Two sessions | Fixed | DEC-71. |
| b | `HANDLE-TBD` everywhere | Three sessions | Fixed | Set to the `gh` login (DEC-72; T11). |
| c | Fourteen of fifteen entries unreviewed; the one review is by an agent | Session 1 | Not fixed | True. A person's review is T4. |
| d | Search: word forms do not match; common words drown the real hit | Sessions 1, 2 | Fixed | Stems and rarity weighting (DEC-73), with a test that every eval question's expected entry ranks first by at least double. |
| e | `source.type: alignment_forum` with a LessWrong URL | Sessions 1, 2 | Fixed as | The schema now says what the field means for a crosspost. |
| f | Result fields are sparse: one effect size, no intervals | Session 1 | Not fixed | The posts rarely report them. |
| g | No help listing what to ask | Session 1, subagent | Fixed | README names every tool and skill with example requests; the server's instructions say more. |
| h | The `method` filter misses entries filed under another spelling | Session 2 | Partly | The skill and the search note warn about it. A controlled vocabulary is future work (findings 6 and 9 in the decision log). |
| i | No place in the answer for an adjacent entry | Session 2 | Fixed | The skill has an "Adjacent only" line. |
| j | With no remote the skills still talk about a pull request | Sessions 3, 4, 5 | Fixed | Both skills and the README explain the branch-only outcome and the merge command. |
| k | Judgment calls the field guide did not settle | Session 3 | Fixed | The guide now says when a result is "smaller than expected", when the cause is `unknown`, and how to name a setup with no language model. |
| l | "The fetched text ends mid-sentence" | Session 3 | Not reproduced | The cached text of that post is complete and ends with its conclusion. The skill now says what to do if text looks cut off. |
| m | Quotes with curly apostrophes looked risky | Session 3 | Fixed as | They were already safe; the skill says so. |
| n | A review is all-or-nothing; nowhere to say "could not check this" | Session 4 | Fixed as | The notes carry what could not be checked, and the skill says when that makes it `contested`. |
| o | Setup step missing from the install section; "install" for a one-session flag; "start with DONE.md"; Python version; no example post; review example is a command | Subagent | Fixed | README. |
| p | Tool permissions are undocumented | Subagent | Fixed | README. |
| q | Your GitHub login is stamped on what the agent files, silently | Subagent, session 5 | Fixed as | README says so plainly, the tools now return what was recorded, and the skills must tell the user. Nothing asks first: that is the design, and it is yours to change (T11). |
| r | One sentence makes it fetch, write entries and create branches without showing a draft | Subagent | Not fixed | By design the branch, or the pull request, is where a person looks before anything reaches the wiki. README says nothing reaches `main` without a merge. Whether the skill should show a draft first is a fair question for you. |
| s | It filed two thin entries from a post the seeding audit had turned down | Subagent, session 3 | Partly | The skill must now find the expectation, the scope, the result and a quote in the post before filing (DEC-78). The same request afterwards filed one entry, declined the experiment the post barely describes, and listed every `unknown` (`raw/first-use-session-5-…`). It is an instruction, not a check a machine enforces. |
| t | A review by the model that wrote the entry flips it to `reviewed` | Subagent | Fixed as | Tools and answers now say who reviewed (DEC-79). An agent can still set `reviewed`. |
| u | `TODO.md` said the plugin flag was unconfirmed | Subagent | Fixed | T8 is closed. |

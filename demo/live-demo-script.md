# Live demo script (about 4 minutes)

The shorter script for recording the demo live, with a real browser, a Claude
Code session and GitHub. Written during the build and moved here from `DONE.md`
on 2026-11-15. The longer, scene-by-scene narration for the assembled draft
video is `demo/script.md`.

Before recording: do T2, T5 and T6 in `TODO.md`. If you skip T6, the two GitHub
steps below become "here is the form and the workflow file", and you say so. If
the plugin does not load (T8), use the fallback under the table.

| Time | Show | Say |
|---|---|---|
| 0:00–0:25 | `README.md`, top | "Failed experiments stay in file drawers, so people repeat dead ends. This is a wiki of failed AI-safety experiments that people and agents both write to and both read. Entries describe experiments, never people." |
| 0:25–1:10 | `site/index.html` in a browser. Tick **failure type → hyperparams_unexplored**, then **badges → agent-written**. Open "All fields" on `fe-2026-0010`. Type `steganography` in search. | "Fifteen entries from real LessWrong posts. Every field is a filter. Each card shows who wrote it, whether anyone reviewed it, a quote the validator found in the post, and how far to trust the negative: this one says retry welcome, low confidence, and records the author's own view that a better setup would very likely succeed." **(D4, D6)** |
| 1:10–1:25 | `make datasette`, the entries table with facets. | "The same data in Datasette, for SQL and JSON." **(D4)** |
| 1:25–2:10 | Claude Code with the plugin. Type: *"I want to steer along an eval-awareness direction to stop a model sandbagging. What's been tried?"* | "The ask skill answers from the wiki only: already tried, where it went wrong, what to avoid, worth retrying, not found. It cites entry IDs and says how weak the evidence is." Then ask about debate with human judges: "And it says plainly when it has nothing." **(D5)** |
| 2:10–2:50 | Same session: *"Contribute this post: <a LessWrong URL not yet in the wiki>"*. Show the pull request it opens, with the badges. | "An agent turns a write-up into an entry. It cannot mark its own work as reviewed. The entry lands as agent-written and unreviewed." **(D1)** |
| 2:50–3:10 | In an entry file, change `failure_type` to `bad_luck`; run `make validate`. Revert. | "One validator guards every path: locally, in the MCP server, and on every pull request. It also checks the quote really is in the post." **(D7)** |
| 3:10–3:30 | GitHub → Issues → New entry form. Show the pull request the workflow opened. | "People contribute with a form. No git needed." **(D2)** |
| 3:30–3:50 | Run the review command from T4 live, or show its commit: `git log --oneline --grep Review`. | "Review is a separate step. It records who reviewed, when and what they checked, and git history keeps it." **(D3)** |
| 3:50–4:10 | `make evals`, then `evals/results/RESULTS.md`. | "Evals run with one command: field accuracy of the contribute skill against five verified entries, and whether the ask skill cites the right entry without inventing failures. Five posts, one vendor: a spot-check, not a benchmark." **(D8)** |
| 4:10–4:20 | `scouting/yields.md`, the funnel. | "One finding: of 49 genuine failure write-ups we found, only 9 stated enough to fill a structured entry. The fields most often missing are the ones that stop a failure report from reading as 'this never works'." |

One line above is only true once T7 is done: "five verified entries". Until
then, say "five reference entries that I still have to verify".

**Fallback if the plugin does not load:** open a plain Claude Code session in
this folder and say: *"Follow plugin/skills/ask/SKILL.md using tools/cli.py. My
plan: …"*. The skills name those commands as the alternative to the MCP tools,
and that is how they were exercised in the build.

# Eval prompt: run the `ask` skill on one question

Given to a fresh subagent, one per question in `evals/ask_questions.json`.
The subagent sees only the `question` text, never the expected answer.

---

You are running the `ask` skill of the failed-experiments wiki for an
evaluation.

1. Read the skill at `plugin/skills/ask/SKILL.md` and follow it exactly,
   including its answer format.
2. Use the command-line twin of the MCP tools, with absolute paths:
   `.venv/bin/python tools/cli.py facets`
   `.venv/bin/python tools/cli.py search "<words>" [--filter field=value]`
   `.venv/bin/python tools/cli.py get <id>`
   If you cannot run commands, the orchestrator has saved what these tools
   return, as the same JSON, in the git-ignored cache. Read those instead:
   `.cache/ask-tools/list_facets.json` (the `facets` output),
   `.cache/ask-tools/search_entries_all.json` (a search with an empty query,
   which lists every entry; the skill tells you to do this in a small wiki),
   and `.cache/ask-tools/get/<id>.json` (one `get` output per entry). You
   cannot run keyword searches in that case, so scan every title in the
   listing and open each entry that could bear on the plan.
3. Do not read anything under `evals/`. Do not read entry files directly;
   use the tools above.
4. The user's question is:

   > <QUESTION>

5. Write your answer, and only your answer, to
   `evals/results/ask/<QID>.md`. Start the file with the
   `## Already tried` heading.
6. Your final message: one line naming the entry IDs you cited, or "none".

Write no other files.

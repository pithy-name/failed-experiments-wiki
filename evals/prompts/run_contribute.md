# Eval prompt: run the `contribute` skill on one gold post (draft only)

Given to a fresh subagent, one per gold post. The subagent must not see the
gold entry, any other draft, or `entries/`.

---

You are running the `contribute` skill of the failed-experiments wiki in
**draft mode** for an evaluation.

1. Read the skill at `plugin/skills/contribute/SKILL.md` and follow it exactly.
2. The source post is: `<SOURCE_URL>`.
   Get its metadata and text with:
   `.venv/bin/python tools/cli.py fetch-source "<SOURCE_URL>" --cached`
   (absolute paths; the JSON it prints has the fields the skill needs and the
   post text in `text`). If you cannot run commands, read the same content
   from the cache files the orchestrator prepared with `fetch-source --save`:
   metadata in `.cache/lw/meta/<POST_ID>.json`, text in
   `.cache/lw/text/<POST_ID>.txt`.
3. Do **not** read anything under `evals/gold/`, `evals/results/` or
   `entries/`, and do not call `search`, `get` or `submit`. This run measures
   what the skill extracts from the post alone.
4. Follow the skill's "Writing a draft file instead of submitting" section.
   Write one Markdown file per entry you would submit to
   `evals/results/contribute/<GOLD_ID>/draft-1.md` (then `draft-2.md`, … if
   the post holds several distinct failed experiments). Leave out `id`,
   `contributor`, `review` and `dates`.
5. Your final message: the number of drafts written and their titles.

Write no other files.

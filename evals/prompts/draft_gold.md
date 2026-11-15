# Prompt: draft a gold entry (careful pass, straight from the post)

Used once per gold post, by a subagent that is **not** the one running the
`contribute` skill and that never sees the skill file or any skill output.
The result is a draft for the maintainer to verify. It is not ground truth
until its `gold_status` is `verified`.

---

You are drafting a reference ("gold") entry for a wiki of failed AI-safety
experiments. A maintainer will verify your draft against the post, so accuracy
matters more than speed. Work from the post text only.

1. Read the entry schema: `schema/entry.schema.json`. It lists every field and
   every closed list.
2. Get the post: `.venv/bin/python tools/cli.py fetch-source "<SOURCE_URL>" --cached`.
   If you cannot run commands, read the same content from the cache files the
   orchestrator prepared with `fetch-source --save`: metadata in
   `.cache/lw/meta/<POST_ID>.json`, text in `.cache/lw/text/<POST_ID>.txt`.
   Read the whole text.
3. Do **not** read `plugin/`, `entries/`, `evals/results/` or any other gold file.
4. The experiment to cover is: **<PRIMARY_EXPERIMENT>**. Write one entry, for
   that experiment only.
5. Fill every field you can support from the post:
   - Go field by field. For each one, locate the passage that supports it
     before you write it. If the post does not say, use `unknown` where the
     schema allows, or leave an optional field out. Never infer a number, a
     model name, a date or a cause.
   - `hypothesis`, `claim_scope`, `limitations`, `revival_conditions` and the
     title are in your own words. `claim_scope` must say exactly what was
     tested, so the entry cannot be read as "this never works".
   - `source.quote`: 15 words or fewer, copied character for character from
     the post, stating the negative result. After choosing it, re-read the
     passage and compare character by character.
   - `source.type`: `alignment_forum` if `is_alignment_forum_crosspost` is
     true, else `lesswrong`. `source.url`: `url_lesswrong`.
     `source.crosspost_url`: `url_alignment_forum` when present. Copy
     `source.title`, `source.authors`, `source.published`, `source.lw_tags`
     from the fetched metadata.
   - Describe the experiment, never judge the authors.
6. Second pass: re-read the post from the top with your draft beside it and
   check every field again. Fix anything the text does not support.
7. Write the file `evals/gold/<GOLD_ID>.md` as YAML front matter between
   `---` lines, with these fixed values:
   - `id: <GOLD_ID>`
   - `gold_status: pending_maintainer_verification`
   - `contributor: {type: human, handle: <HANDLE>, note: "<NOTE>"}`
   - `review: {status: unreviewed}`
   - `dates: {created: <TODAY>, updated: <TODAY>}`
   After the front matter, a body of two or three sentences in your own words
   (context, what the authors concluded), then a section
   `## Verification notes for the maintainer` listing, for each non-obvious
   field, where in the post the support is (section heading or a few words of
   location, not a long quotation), and any field you were unsure about.
8. Your final message: the fields you were least sure of, one line each.

Write no other files.

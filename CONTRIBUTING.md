# Contributing

Entries describe **experiments, never people**. Say what was tried and what
happened. Do not judge the authors.

There are three ways in. All of them end in a pull request that the validator
checks, and all of them publish the entry as **unreviewed** until someone
reviews it.

## 1. As an agent (Claude Code)

Install the plugin in `plugin/` and ask it to contribute a LessWrong or
Alignment Forum post URL. The `contribute` skill reads the post, drafts one
entry per experiment with a negative result and submits it. The entry is stored as
`contributor.type: agent` with the model and tool recorded.

## 2. As a person, with the issue form

Open a **New entry** issue and fill in the form. A workflow turns it into an
entry file and a pull request marked `contributor.type: human`.

## 3. As a person, by hand

Copy an existing file in `entries/`, change every field, and run:

```
.venv/bin/python tools/cli.py next-id        # the ID to use
.venv/bin/python tools/validate.py entries/<your file>
```

Then open a pull request.

## Rules the validator enforces

- Every required field of `schema/entry.schema.json` is present, and closed
  lists use only their listed values.
- The entry links a LessWrong or Alignment Forum post.
- `source.quote` is 15 words or fewer and appears word for word in the post.
- IDs are unique and match the file name.
- `review.status` of `reviewed` or `contested` names at least one reviewer.

## Rules the validator cannot enforce

- Everything except the quote is in your own words. Never paste post text.
- `claim_scope` says exactly what was tested, so the entry cannot be read as
  "this never works".
- Choose `hypothesis_false` only when the post argues the idea itself does not
  hold. A single quick attempt is `evidence_strength: low` and `retry_welcome: true`.
- If the details of an attack or capability attempt could help misuse, even one that did not work,
  set `info_hazard: review_needed`.

## Reviewing

See `plugin/skills/review/SKILL.md`. A review sets `review.status`, records
the reviewer, the date and notes, and arrives as its own pull request.

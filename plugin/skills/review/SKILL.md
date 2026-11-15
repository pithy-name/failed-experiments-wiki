---
name: review
description: Review an entry of the failed-experiments wiki against its source post and record the outcome (reviewed or contested). Use when the user asks to review, check, verify or vet a wiki entry, or names an entry ID to review.
---

# review: check an entry against its source

You check one entry against the post it cites and record what you found. A
review changes `review.status`, adds you to `review.reviewers` with the date,
and goes in as a pull request, so the change is visible in git history.

**Version:** review-skill v0.1

## Ground rules

- **The post is the reference.** Judge each field against the post's text, not
  against what you remember about the work.
- **You do not rewrite the entry.** A review only sets the status and records
  notes. If a field is wrong, set `contested` and say in the notes which field
  and what the post says instead. Corrections are a separate pull request.
- **`reviewed` means every field holds.** If you could not check something,
  or one field is wrong, the status is not `reviewed`.
- **An agent review is weaker than a human one**, and weakest when the same
  model wrote the entry. The review is recorded as an agent review with your
  model ID so readers can weigh it. If the entry's `contributor.agent_model` is
  your own model, say so in the notes.
- **Experiments, not people.** Notes are about the entry's accuracy.

## Tools

Use the `failed-experiments-wiki` MCP server: `get_entry`, `fetch_source`,
`review_entry`.

Command-line twin, from the repository root:

```
python tools/cli.py get fe-2026-0006
python tools/cli.py fetch-source <source url>
python tools/cli.py review fe-2026-0006 reviewed --notes "…" --agent-model <your model id>
```

## Steps

1. `get_entry(id)`: read every field and the body.
2. `fetch_source(entry.source.url)`: read the whole post.
3. **Check each item** and note pass or fail:
   - **Quote:** appears in the post character for character, is 15 words or
     fewer, and states the negative result.
   - **Source fields:** title, authors, published date and URLs match.
   - **Hypothesis:** the post states this expectation.
   - **Claim scope:** matches what was tested and does not overreach. An entry
     that reads as "X never works" when the post tested one setup fails here.
   - **Method, models, benchmarks:** named in the post; nothing added.
   - **Result:** `result.direction` fits; any numbers match the post.
   - **Failure type and confidence:** supported by what the post says about
     why it failed and how thoroughly it was checked. `hypothesis_false` with
     `high` confidence needs strong support in the post.
   - **Checks, limitations, revival conditions, retry_welcome:** consistent
     with the post.
   - **Info hazard:** `review_needed` if the details could help misuse.
   - **Tone:** describes the experiment and does not judge the authors, and
     does not repeat remarks about an author's skill, effort or standing even
     when the author made them about themselves.
   - **Body:** in the contributor's own words, with no copied post text.
4. **Decide the status:**
   - `reviewed`: every item passes.
   - `contested`: at least one item fails. Name each failing field and what
     the post says.
   - `superseded`: only when a newer entry replaces this one; name its ID.
5. **Record it:** `review_entry(id, status, notes, agent_model)`. Notes: one or
   two sentences on what you checked and what you found. `reviewed` means every
   item passed, so anything you could **not** check goes in the notes in plain
   words, for example:
   - a claim that rests on a figure (the fetched text has no figures);
   - a field the post does not state and the contributor inferred, such as
     revival conditions drawn from the author's open questions. Say it is an
     inference and whether it is consistent with the post.
   If what you could not check decides whether the entry is right, use
   `contested` and say which field.
6. **Report** the new status and the branch or pull-request link exactly as the
   tool returned it. If no pull request was opened, say so. Say which GitHub
   handle the review was recorded under (`recorded_as.handle` in the tool's
   result: the user's own login, as the
   accountable person beside `type: agent` and your model), and say plainly
   that this is an agent's review: weaker than a person's, and weakest when
   your model is the one that wrote the entry.

**When the repository has no remote.** `review_entry` returns
`status: branch_only_no_remote` and `pull_request: null`. That is not an error:
the review is committed on the local branch `review/<id>-<date>` and the entry
in the wiki is unchanged until that branch is merged. Report the branch and
the merge command from the tool's `detail`
(`python tools/cli.py merge-local <branch>`). Do not run it unless asked.

## Reviewing by hand (people)

A person can review without this skill:

```
python tools/cli.py review fe-2026-0006 reviewed --human --handle <your GitHub handle> \
  --notes "Checked every field against the post."
```

or edit `entries/<id>.md` directly: set `review.status`, add an item to
`review.reviewers` (`handle`, `type: human`, `date`, `notes`), set
`dates.updated`, run `python tools/validate.py`, and open a pull request.

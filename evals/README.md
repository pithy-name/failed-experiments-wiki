# Evals

A spot-check of two skills on 5 posts, with one model vendor. Not a benchmark.

## Run it

```
make evals            # or: .venv/bin/python evals/run_evals.py
```

This writes `evals/results/results.json` and `evals/results/RESULTS.md`. It is
deterministic: it re-scores saved skill outputs against the gold set and calls
no model. Run it again whenever a gold entry changes.

Results are labelled **PROVISIONAL** until every file in `evals/gold/` has
`gold_status: verified`.

## What is measured

**`contribute`:** the skill drafts entries for each of the 5 gold posts, and
each draft is compared with the gold entry field by field.

- Exact match: enums, booleans, the published date, URLs, reported numbers.
- Set match after normalization: list fields (areas, methods, model names,
  benchmarks, checks, authors, tags). Jaccard overlap is reported beside it.
- Rubric 0–2, by a separate grader: `hypothesis`, `claim_scope`, `limitations`.
- Not scored: trust and provenance fields (`id`, `contributor`, `review`,
  `dates`), free-wording fields, and the quote, which is checked for validity
  (verbatim, 15 words or fewer) instead of compared with gold.

**`ask`:** one research-plan question per gold entry, plus 2 questions the
wiki has nothing on (`evals/ask_questions.json`). A match question passes when
the answer cites the expected entry under "Already tried", names the gold
`failure_type` under "Where it went wrong", cites only entries that exist, and
a separate judge finds no invented failure. A no-match question passes when
"Already tried" cites nothing, "Not found" says so, and the judge finds no
invented failure.

## Files

| Path | What it holds | Who writes it |
|---|---|---|
| `gold/<id>.md` | The reference entry for one post, with `gold_status` | The maintainer (drafted by a model, see below) |
| `ask_questions.json` | Questions and the entry each should find | The maintainer or the orchestrator |
| `results/contribute/<id>/draft-N.md` | What the `contribute` skill drafted | A subagent following `prompts/run_contribute.md` |
| `results/ask/<qid>.md` | What the `ask` skill answered | A subagent following `prompts/run_ask.md` |
| `results/rubric_scores.json` | 0–2 grades for the text fields | A grader subagent following `prompts/grade_rubric.md` |
| `results/ask_judgements.json` | Invented-failure verdicts | A judge subagent following `prompts/judge_ask.md` |
| `results/*/run.json` | Date, model and skill version of each run | The orchestrator |
| `results/results.json`, `results/RESULTS.md` | The scores | `run_evals.py` |

## After the maintainer verifies the gold entries

1. Open each `gold/<id>.md` beside its post. The section "Verification notes
   for the maintainer" at the bottom says where each field's support is.
   Correct any field. Set `gold_status: verified`.
2. `make validate-gold`
3. `make sync-gold HANDLE=<your GitHub handle>` publishes the verified entries
   into `entries/` as human-written and human-reviewed. Commit them.
4. `make evals`. Exact and list fields are re-scored at once. If you changed
   a `hypothesis`, `claim_scope` or `limitations` text, its rubric grade shows
   as **STALE** and is left out of the totals.
5. To regrade stale text fields, in Claude Code in this repository say:
   *"Follow evals/prompts/grade_rubric.md."* Then run `make evals` again.
6. If you changed a gold `failure_type`, the `ask` eval re-scores against the
   new value automatically, but the saved answers were written against the old
   wiki entry. To regenerate them, say: *"For each question in
   evals/ask_questions.json, run evals/prompts/run_ask.md in a fresh subagent,
   then follow evals/prompts/judge_ask.md."* Then `make evals`.

## Isolation rules

- The subagent that drafts a gold entry never sees the `contribute` skill or
  its output. The subagent that runs `contribute` never sees `evals/gold/`.
- The grader and the judge did not write what they grade.
- No agent edits a gold entry after the maintainer has verified it.

## Limits

- 5 gold items and 7 questions.
- One vendor's models wrote the drafts, the answers, the grades and, until
  verified, the gold entries.
- The `ask` checks are partly keyword-level; the judge verdict is the backstop.
- Skill outputs come from subagents that read the skill file and used the
  command-line twin of the MCP tools, not from the plugin loaded in a session.

# Eval prompt: grade the text fields (0–2 rubric)

Given to a grader subagent that did not write the gold entries or the drafts.

---

You grade how well a skill-written entry matches a gold entry on three text
fields: `hypothesis`, `claim_scope`, `limitations`.

For each gold entry `evals/gold/<id>.md`, find the draft that
`evals/results/results.json` lists as `scored_draft` for it (under
`contribute.items`), in `evals/results/contribute/<id>/`. Compare the three
fields. You may read the cached post text
(`.venv/bin/python tools/cli.py fetch-source "<source url>" --cached`) to
settle what the post actually says.

Rubric, per field:

- **2**: same meaning as gold. Wording may differ. Nothing important is
  missing, nothing is added that the post does not support.
- **1**: partly right. The core idea matches, but an important element of the
  gold text is missing, or the draft adds a claim the gold text does not make.
  For `claim_scope`, a draft that is right but noticeably broader or vaguer
  than gold is a 1.
- **0**: different meaning, wrong, or overreaching (for `claim_scope`: reads
  as "this never works" when gold scopes it narrowly). Also 0 when one side
  has the field and the other leaves it out.

If both gold and draft leave a field out, do not grade it.

Compute each hash with the scorer's own function so grades stay tied to the
exact texts you graded:

```
.venv/bin/python evals/hash_text.py --gold <id> --draft <draft file name> --field <field>
```

If you cannot run commands, leave the two hash fields out and write the same
structure to `evals/results/rubric_scores.raw.json`; the orchestrator then
runs `.venv/bin/python evals/hash_text.py --attach rubric` to add the hashes.

Write `evals/results/rubric_scores.json`:

```json
{"grader_model": "<your model id>", "graded_on": "YYYY-MM-DD",
 "grades": [{"gold_id": "fe-2026-0001", "draft": "draft-1.md", "field": "claim_scope",
             "score": 1, "reason": "one sentence", "gold_hash": "…", "skill_hash": "…",
             "grader_model": "<your model id>"}]}
```

Grade strictly and independently for each field. Do not edit any gold entry or
draft.

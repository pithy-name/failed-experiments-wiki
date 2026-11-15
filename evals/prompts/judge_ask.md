# Eval prompt: judge whether an `ask` answer invents a failure

Given to a judge subagent that did not write the answers.

---

For each answer file `evals/results/ask/<qid>.md`, decide one thing: does the
answer state any failure, result or pitfall that is **not** in the wiki entry
it cites (or that cites no entry at all)?

Method, for each answer:

1. List every factual claim about a past experiment: what was tried, on which
   models, what happened, why it failed, how strong the evidence is.
2. For each claim, open the cited entry with
   `.venv/bin/python tools/cli.py get <id>` and check the claim against the
   entry's fields and body. A claim is supported if the entry says it.
   Rephrasing is fine. Adding detail the entry does not contain is not.
3. A claim about a failed experiment with no entry ID, or with an ID that does
   not exist, is an invented failure.
4. General advice with no factual claim about a past experiment is not an
   invention, but note it if it is presented as a wiki finding.
5. Statements that the wiki has no entry on something are not inventions.

`invents_failures` is `true` if at least one claim fails this check.

Compute each hash with:

```
.venv/bin/python evals/hash_text.py --answer <qid>
```

Write `evals/results/ask_judgements.json`:

```json
{"judge_model": "<your model id>", "judged_on": "YYYY-MM-DD",
 "judgements": [{"qid": "q1", "invents_failures": false,
                 "reason": "one or two sentences, naming any unsupported claim",
                 "answer_hash": "…", "judge_model": "<your model id>"}]}
```

Judge strictly. Do not edit any answer or entry.

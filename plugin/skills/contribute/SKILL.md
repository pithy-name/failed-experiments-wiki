---
name: contribute
description: Turn a LessWrong or Alignment Forum write-up of a failed AI-safety experiment into one or more entries for the failed-experiments wiki, and submit them as a pull request. Use when the user gives a post URL (or pastes a write-up with its URL) and asks to add it, file it, or contribute it to the wiki.
---

# contribute: write-up → wiki entries

You turn one write-up of a failed experiment into schema-valid wiki entries and
submit them. Everything you submit is stored as **agent-written** and
**unreviewed**; a person or another agent reviews it later.

**Version:** contribute-skill v0.3

Change from v0.1: the field guide now says which fields are single strings.
In the first seeding run, two of five v0.1 drafts wrote `limitations` as a
list and the validator rejected them. The seed entries and the evals in
`evals/results/` were produced with v0.1.

## Ground rules

- **The post is your only source.** Fill fields from what the post says. Never
  use what you remember about the paper, the authors or the field. If the post
  does not say something, write `unknown` where the schema allows it, or leave
  the optional field out. Never invent a number, a model name or a result.
- **Your own words, except the quote.** Describe the experiment in your own
  words. The only verbatim text is `source.quote`.
- **Experiments, not people.** Describe what was tried and what happened. Never
  judge the authors. No "the authors failed to", "sloppy", "should have".
  This holds even when the authors say it of themselves: if a post says "I
  don't have much expertise in X" or "this is below my usual standard", do not
  carry that into the entry. Record what it means for the experiment instead
  (what was not tuned, how long it ran, what was not tried).
- **A failure is scoped.** One post showing that X did not work in one setup is
  not evidence that X never works. `claim_scope` exists to say so.
- **Not every post belongs.** If the post is not a write-up of an experiment
  that was actually run and that failed, say so and submit nothing.

## Tools

Use the `failed-experiments-wiki` MCP server: `fetch_source`, `search_entries`,
`get_entry`, `list_facets`, `submit_entry`.

If the MCP tools are not available in this session, use the command-line twin
from the repository root; it returns the same JSON:

```
python tools/cli.py fetch-source <url>
python tools/cli.py search "<words>"
python tools/cli.py submit --file <draft.md> --agent-model <your model id>
```

## Steps

1. **Get the source.** Call `fetch_source(url)`. It returns title, authors,
   published date, tags, both URLs for crossposts, and the plain text. If the
   user pasted a write-up, still ask for its LessWrong / Alignment Forum URL:
   every entry must link a post, and the quote is checked against that post.
2. **Read the whole text** before writing anything.
3. **Decide whether it qualifies.** It qualifies if the authors ran an
   experiment (or a replication) and report a negative outcome: null, opposite,
   smaller than expected, mixed with a clear negative, did not replicate, or
   abandoned because it did not work. If not, stop and tell the user why.
   **Then check that the post says enough.** An entry is only as good as what
   the post states. For each experiment you would file, the post itself must
   state all of these:
   - what the authors expected or set out to show (`hypothesis`);
   - exactly what was tested (`claim_scope`): the setup, and the model or the
     thing that was trained;
   - the result and its direction;
   - a sentence of 15 words or fewer that states the negative result (the quote).

   If one is missing, **do not submit that experiment.** Tell the user which
   field the post does not support. Most failure write-ups fall short here
   (during seeding, 9 of 49 passed), so declining is the normal outcome, not a
   failure of yours. `unknown` is for details the post leaves out (a model's
   version, the cause of the failure). It is not a way to file an experiment
   the post barely describes: an entry with `models: unknown`,
   `failure_type: unknown` and a vague result tells a reader nothing, and its
   passing the validator would make it look sounder than it is. A round-up
   post that mentions many failed projects in a paragraph each usually
   supports none of them.
4. **Split into experiments.** One entry per distinct failed experiment
   (different hypothesis, method or setup). Several results of one experiment
   are one entry. A post listing three unrelated failed projects is three
   entries. Skip parts of the post that worked.
5. **Check for duplicates.** `search_entries` with the method, the model and
   the topic. If an entry for the same post and experiment exists, stop and say
   so. If a different post tested the same idea, add it under `related`.
6. **Draft each entry** using the field guide below.
7. **Check your draft against the text**, field by field. For the quote, find
   it in the text again and confirm it matches character for character.
8. **Submit** with `submit_entry(entry, body, agent_model)`. Pass your own
   model ID as `agent_model`. Do not set `id`, `contributor`, `review` or
   `dates`: the server assigns them.
9. **If validation rejects it**, read the issues, fix the entry and submit
   again. Never work around the validator. If the quote check fails, your quote
   is not verbatim: pick the fragment again from the fetched text.
10. **Report** each entry's ID, its branch or pull-request link exactly as the
    tool returned it, and that it is agent-written and unreviewed. If the tool
    says no pull request was opened, say that; do not make up a link. Also say:
    - which GitHub handle the entry was recorded under (`contributor.handle` in
      the tool's result). It is the user's own login, read from `gh`, named as
      the accountable person beside `type: agent` and your model. The user may
      not expect their name on it, so tell them;
    - every field you set to `unknown`, and any judgment call between two
      closed-list values, so a reviewer knows where to look;
    - every experiment in the post you did **not** file, and which field it lacked.

**When the repository has no remote.** `submit_entry` returns
`status: branch_only_no_remote` and `pull_request: null`. That is not an error:
the entry is committed on the local branch `entry/<id>` and is not in the wiki
yet. Report the branch, and the command that merges it, which the tool prints
in `detail`: `python tools/cli.py merge-local entry/<id>`. Do not run the merge
unless the user asks.

**If the post text looks cut off.** `fetch_source` returns the whole post as
plain text; figures and their captions are not included. If the text seems to
stop mid-sentence, say so in your report and do not fill a field from the
missing part.

## Field guide

Required unless marked optional. Closed lists must use exactly these values.

Types: `title`, `hypothesis`, `claim_scope`, `limitations`,
`revival_conditions` and every `source.*` text field are **one string each**,
never a list. Put several points in one string as sentences. `research_area`,
`method`, `benchmarks`, `checks_done`, `source.authors` and `source.lw_tags`
are lists of strings. `models` and `related` are lists of objects.

| Field | How to fill it |
|---|---|
| `title` | One line: what was tried, on what, what happened. Scoped. E.g. "SAE probes did not beat linear probes for harmful-intent detection on Gemma 2". |
| `research_area` | One or more of: `interpretability`, `steering`, `evals`, `honesty`, `sycophancy`, `control`, `oversight`, `robustness`, `rlhf`, `alignment-training`, `agents`, `governance`, `other`. |
| `hypothesis` | What the authors expected or hoped to find, as the post states it. |
| `claim_scope` | Exactly what was tested: setup, models, data, scale, and what was not covered. Write it so nobody can read the entry as "X never works". |
| `method` | Technique tags, lowercase with hyphens: e.g. `sae`, `activation-steering`, `linear-probing`, `fine-tuning`, `prompting`, `rl`, `debate`. |
| `models` | Each model tested: `name`, `developer`, `version`, `size`, `access` (`open-weight`, `api` or `unknown`). Use `unknown` for anything the post does not state. If the experiment has no language model (a toy model, synthetic activations, an SAE trained on synthetic data), name what was trained, as the post does, e.g. `name: toy model (synthetic activations)`, with the other parts `unknown`. Use one item with `name: unknown` only when the post gives nothing to name. |
| `benchmarks` (optional) | Benchmarks or datasets named in the post. |
| `result.direction` | `null` (no effect), `opposite`, `smaller_than_expected`, `mixed`, `did_not_replicate`. When a metric improved a little but the method gave nothing usable, that is `smaller_than_expected`. Use `mixed` only when some results were clearly positive and others clearly negative. |
| `result.effect_size`, `ci_low`, `ci_high`, `n` (optional) | Only numbers the post reports for the main result. Leave out when in doubt. |
| `failure_type` | Why it failed, as far as the post says: `hypothesis_false` (the idea, as scoped, seems wrong), `underpowered` (too little data or compute to tell), `implementation_bug_ruled_out`, `implementation_bug_suspected`, `measurement_noise`, `hyperparams_unexplored`, `infrastructure`, `worked_but_abandoned`, `unknown`. Choose `hypothesis_false` only when the post argues the idea itself does not hold. When the authors say only that the work "did not accomplish anything useful" and give no cause, that is `unknown`. |
| `confidence_true_negative` | How sure a reader can be that the idea, as scoped, really does not work: `low`, `medium`, `high`. One quick attempt with caveats is `low`. Careful controls, baselines and several setups is `high`. |
| `checks_done` (optional) | Checks the post reports, as tags: e.g. `positive-control`, `baseline-comparison`, `seed-sweep`, `noise-floor`, `bug-audit`, `hyperparameter-sweep`. |
| `limitations` (optional) | What was not tried, as the post says. |
| `revival_conditions` (optional) | When it would be worth retrying, if the post says or clearly implies. |
| `retry_welcome` | `true` when the evidence is weak enough that a better attempt is worthwhile (low confidence, underpowered, unexplored hyperparameters, suspected bug). Otherwise `false`. |
| `evidence_level` | `author_report` when the authors describe their own experiment; `third_party_report` when the post reports someone else's; `independent_reproduction` when it is a replication of another team's result. |
| `source.type` | `alignment_forum` if `fetch_source` says the post is an Alignment Forum crosspost, else `lesswrong`. |
| `source.url` | `url_lesswrong` from `fetch_source`. |
| `source.crosspost_url` (optional) | `url_alignment_forum` from `fetch_source`, when present. |
| `source.title`, `source.authors`, `source.published`, `source.lw_tags` | Copy from `fetch_source`. |
| `source.section` (optional) | The heading the experiment sits under, if any. |
| `source.quote` | **15 words or fewer, copied character for character** from the post, stating the negative result. Not stitched from two places. Curly quotes, apostrophes and dashes are safe: the check treats them the same as their plain forms. |
| `dates.experiment` (optional) | Only if the post says when the experiment ran. |
| `related` (optional) | Existing entries on the same idea: `id` and `relation` (`replicates`, `contradicts`, `extends`, `same_hypothesis`). |
| `info_hazard` | `none`, or `review_needed` if the failed experiment is an attack or capability attempt whose details could help misuse. |

`body` (optional): two or three sentences of context in your own words, such as
what the authors concluded or decided next. No post text.

## Writing a draft file instead of submitting

If you are asked for a draft only (for example in an eval), write the entry as
Markdown with YAML front matter to the path you are given and do not call
`submit_entry`. Leave out `id`, `contributor`, `review` and `dates`.

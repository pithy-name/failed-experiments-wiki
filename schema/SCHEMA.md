# Entry schema

Generated from `schema/entry.schema.json` by `tools/make_print_pack.py`. The JSON file is the one the validator uses; this is the same content laid out for reading.

An entry is a Markdown file, `entries/fe-YYYY-NNNN.md`, with these fields in its YAML front matter and optional free text below.

| Field | Type | Required | Allowed values | Notes |
|---|---|---|---|---|
| `id` | string | yes | pattern `^fe-[0-9]{4}-[0-9]{4}$` | fe-YYYY-NNNN, unique. YYYY is the year the entry was created. |
| `title` | string | yes | pattern `^[^\n]+$`; at most 240 characters | One line, scoped: what was tried, on what, what happened. |
| `research_area` | list, each one of | yes | `interpretability`, `steering`, `evals`, `honesty`, `sycophancy`, `control`, `oversight`, `robustness`, `rlhf`, `alignment-training`, `agents`, `governance`, `other` |  |
| `hypothesis` | string | yes |  | What was expected. |
| `claim_scope` | string | yes |  | Exactly what was tested, so the entry cannot be read as 'X never works'. |
| `method` | list of values | yes |  | Techniques, free tags normalized to lowercase-hyphen. |
| `models` | list of objects | yes |  |  |
| `models[].name` | string | if its parent is present |  |  |
| `models[].developer` | string | if its parent is present |  |  |
| `models[].version` | string | if its parent is present |  | Or 'unknown'. |
| `models[].size` | string | if its parent is present |  | Or 'unknown'. |
| `models[].access` | one of | if its parent is present | `open-weight`, `api`, `unknown` |  |
| `benchmarks` | list of string |  |  |  |
| `result` | object | yes |  |  |
| `result.direction` | one of | yes | `null`, `opposite`, `smaller_than_expected`, `mixed`, `did_not_replicate` | The string 'null' means a null result. Quote it in YAML. |
| `result.effect_size` | number |  |  | As reported. |
| `result.ci_low` | number |  |  |  |
| `result.ci_high` | number |  |  |  |
| `result.n` | integer |  |  | Sample size, if reported. |
| `failure_type` | one of | yes | `hypothesis_false`, `underpowered`, `implementation_bug_ruled_out`, `implementation_bug_suspected`, `measurement_noise`, `hyperparams_unexplored`, `infrastructure`, `worked_but_abandoned`, `unknown` |  |
| `confidence_true_negative` | one of | yes | `low`, `medium`, `high` | How sure we are that the idea, as scoped, really does not work. |
| `checks_done` | list of values |  |  | e.g. positive-control, noise-floor, bug-audit, seed-sweep. |
| `limitations` | string |  |  | What was not tried. |
| `revival_conditions` | string |  |  | When it would be worth retrying. |
| `retry_welcome` | boolean | yes |  | True when the evidence is weak enough that a better attempt is worthwhile. |
| `evidence_level` | one of | yes | `author_report`, `third_party_report`, `independent_reproduction` |  |
| `source` | object | yes |  |  |
| `source.type` | one of | yes | `lesswrong`, `alignment_forum` | Where the post was published. alignment_forum means an Alignment Forum crosspost: url is still the LessWrong address, and crosspost_url the Alignment Forum one. |
| `source.url` | string | yes | pattern `^https://(www\.)?(lesswrong\.com\|alignmentforum\.org\|greaterwrong\.com)/posts/[A-Za-z0-9]+(/[^\s]*)?$` |  |
| `source.crosspost_url` | string |  | pattern `^https://[^\s]+$` |  |
| `source.lw_tags` | list of string |  |  |  |
| `source.title` | string | yes |  |  |
| `source.authors` | list of string | yes |  |  |
| `source.published` |  | yes |  |  |
| `source.section` | string |  |  |  |
| `source.quote` | string | yes |  | 15 words or fewer, verbatim from the source. The validator checks both. |
| `contributor` | object | yes |  |  |
| `contributor.type` | one of | yes | `human`, `agent` |  |
| `contributor.handle` | string | yes |  | GitHub handle. For agents, the account that ran them. |
| `contributor.agent_model` | string |  |  |  |
| `contributor.tool` | string |  |  |  |
| `contributor.note` | string |  |  | Optional provenance note shown beside the contributor, e.g. 'drafted with model help, awaiting maintainer verification'. |
| `review` | object | yes |  |  |
| `review.status` | one of | yes | `unreviewed`, `reviewed`, `contested`, `superseded` |  |
| `review.reviewers` | list of objects |  |  |  |
| `review.reviewers[].handle` | string | if its parent is present |  |  |
| `review.reviewers[].type` | one of | if its parent is present | `human`, `agent` |  |
| `review.reviewers[].date` |  | if its parent is present |  |  |
| `review.reviewers[].notes` | string |  |  |  |
| `review.reviewers[].agent_model` | string |  |  |  |
| `dates` | object | yes |  |  |
| `dates.experiment` |  |  |  |  |
| `dates.created` |  | yes |  |  |
| `dates.updated` |  | yes |  |  |
| `related` | list of objects |  |  |  |
| `related[].id` | string | if its parent is present | pattern `^fe-[0-9]{4}-[0-9]{4}$` |  |
| `related[].relation` | one of | if its parent is present | `replicates`, `contradicts`, `extends`, `same_hypothesis` |  |
| `info_hazard` | one of | yes | `none`, `review_needed` |  |

## Rules the validator adds on top of the schema

- `source.quote` is 15 words or fewer and must be found, word for word, in the text of the post at `source.url`.
- `id` must match the file name, and no two entries share an ID.
- An entry marked `reviewed` must name at least one reviewer.
- An agent-written entry must name its model.
- `dates.updated` is not before `dates.created`; an interval's low end is not above its high end; an entry cannot be related to itself.

## Badges (derived, never stored)

| Badge | Shown when |
|---|---|
| agent-written | `contributor.type` is `agent` |
| unreviewed | `review.status` is `unreviewed` |
| contested | `review.status` is `contested` |
| superseded | `review.status` is `superseded` |
| retry-welcome | `retry_welcome` is true |

The browse page also shows "Reviewed by a person" or "Reviewed by an agent only" on reviewed entries.

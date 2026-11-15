# Eval results

> **PROVISIONAL.** 5 of 5 gold entries are model drafts awaiting the maintainer's verification (fe-2026-0001, fe-2026-0002, fe-2026-0003, fe-2026-0004, fe-2026-0005).
> These numbers compare one model's drafts with another model pass, not with human ground truth.
> Do not cite them as accuracy until the gold entries are verified and this file is regenerated.

Generated 2026-11-14T23:47:11-08:00 by `python evals/run_evals.py` (deterministic re-scoring of saved outputs).

This is a spot-check on 5 posts with one model vendor. It is not a benchmark.

## `contribute` skill: field accuracy against the gold set

- Gold entries: 5 (pending_maintainer_verification)
- Gold posts with a skill draft: 5
- **Overall field accuracy: 78%** (mean of per-field accuracies; exact and list fields score 0 or 1 per item, rubric fields score grade/2)
- Skill run: {"run_date": "2026-11-14", "skill": "plugin/skills/contribute/SKILL.md", "skill_version": "contribute-skill v0.1", "model": "claude-sonnet-5-5 (Claude Code `sonnet` subagent alias; resolved ID not confirmed by the model)", "prompt": "evals/prompts/run_contribute.md", "mode": "draft files; one fresh subagent per gold post; no command access, so the post was read from the cache written by `cli.py fetch-source --save`", "isolation": "subagents were told not to read evals/gold, evals/results, entries or scouting; this was an instruction, not an enforced sandbox"}

| Field | Kind | Accuracy | Items scored | Unscored |
|---|---|---|---|---|
| `result.direction` | exact | 80% | 5 | 0 |
| `failure_type` | exact | 80% | 5 | 0 |
| `confidence_true_negative` | exact | 80% | 5 | 0 |
| `retry_welcome` | exact | 60% | 5 | 0 |
| `evidence_level` | exact | 80% | 5 | 0 |
| `info_hazard` | exact | 100% | 5 | 0 |
| `source.type` | exact | 100% | 5 | 0 |
| `source.url` | exact | 100% | 5 | 0 |
| `source.crosspost_url` | exact | 100% | 5 | 0 |
| `source.published` | exact | 100% | 5 | 0 |
| `result.effect_size` | exact | 100% | 5 | 0 |
| `result.ci_low` | exact | 100% | 5 | 0 |
| `result.ci_high` | exact | 100% | 5 | 0 |
| `result.n` | exact | 60% | 5 | 0 |
| `research_area` | list (set match) | 60% | 5 | 0 |
| `method` | list (set match) | 0% | 5 | 0 |
| `models.name` | list (set match) | 80% | 5 | 0 |
| `models.developer` | list (set match) | 100% | 5 | 0 |
| `models.access` | list (set match) | 60% | 5 | 0 |
| `benchmarks` | list (set match) | 60% | 5 | 0 |
| `checks_done` | list (set match) | 0% | 5 | 0 |
| `source.authors` | list (set match) | 100% | 5 | 0 |
| `source.lw_tags` | list (set match) | 100% | 5 | 0 |
| `hypothesis` | rubric 0-2 | 70% | 5 | 0 |
| `claim_scope` | rubric 0-2 | 90% | 5 | 0 |
| `limitations` | rubric 0-2 | 60% | 5 | 0 |

Per gold entry:

| Gold entry | Gold status | Drafts | Accuracy | Quote valid | Schema valid | Unscored fields |
|---|---|---|---|---|---|---|
| `fe-2026-0001` | pending_maintainer_verification | 2 | 77% | True | True | - |
| `fe-2026-0002` | pending_maintainer_verification | 1 | 77% | True | True | - |
| `fe-2026-0003` | pending_maintainer_verification | 1 | 71% | True | True | - |
| `fe-2026-0004` | pending_maintainer_verification | 1 | 75% | True | True | - |
| `fe-2026-0005` | pending_maintainer_verification | 2 | 88% | True | True | - |

Mismatches (gold vs skill), exact and list fields:

- `fe-2026-0001` `retry_welcome`: gold `True` / skill `False`
- `fe-2026-0001` `result.n`: gold `3850` / skill `None`
- `fe-2026-0001` `research_area`: gold `['interpretability', 'robustness']` / skill `['interpretability']`
- `fe-2026-0001` `method`: gold `['chat-sae-finetuning', 'dense-linear-probing', 'held-out-jailbreak-split', 'k-sparse-probing', 'sae-probing', 'sae-reconstruction-probing']` / skill `['linear-probing', 'sae', 'sparse-probing']`
- `fe-2026-0001` `checks_done`: gold `['chat-sae-finetuning-variants', 'dataset-spurious-correlation-cleanup', 'dense-probe-baseline', 'in-distribution-validation-set', 'latent-selection-method-comparison', 'reconstruction-probe', 'token-position-comparison']` / skill `['baseline-comparison', 'held-out-ood-set', 'hyperparameter-sweep', 'reconstruction-probe-control']`
- `fe-2026-0002` `retry_welcome`: gold `True` / skill `False`
- `fe-2026-0002` `evidence_level`: gold `author_report` / skill `independent_reproduction`
- `fe-2026-0002` `method`: gold `['future-token-prediction', 'j-lens', 'logit-lens', 'rank-metric', 're-implementation']` / skill `['jacobian-lens', 'logit-lens', 'sparsity-thresholding']`
- `fe-2026-0002` `models.access`: gold `['unknown']` / skill `['open-weight']`
- `fe-2026-0002` `checks_done`: gold `['bias-subtraction', 'gradcheck-float64', 'identity-j-check', 'refit-150-sequences', 'scale-sweep', 'skip-first-sweep', 'sparsity-thresholding', 'token-frequency-correlation', 'top1-token-inspection']` / skill `['baseline-comparison', 'bug-audit', 'frequency-confound-check', 'hyperparameter-sweep', 'more-data-refit', 'scale-sweep', 'sparsity-thresholding']`
- `fe-2026-0003` `failure_type`: gold `unknown` / skill `underpowered`
- `fe-2026-0003` `research_area`: gold `['alignment-training', 'evals']` / skill `['evals', 'honesty']`
- `fe-2026-0003` `method`: gold `['behavioral-testing', 'free-vs-paid-tier-comparison', 'manual-scoring', 'scratchpad-review', 'training-details-in-system-prompt']` / skill `['behavioral-evaluation', 'manual-scoring', 'prompting', 'scratchpad-review']`
- `fe-2026-0003` `models.name`: gold `['llama-70b-alignment-faking-checkpoint-hughes-et-al-2025']` / skill `['llama']`
- `fe-2026-0003` `benchmarks`: gold `['harmbench']` / skill `['harm-bench']`
- `fe-2026-0003` `checks_done`: gold `['manual-scratchpad-reading', 'prompt-set-widening']` / skill `['comparison-to-published-rate', 'manual-scratchpad-review', 'widened-prompt-set', 'with-and-without-training-details']`
- `fe-2026-0004` `result.direction`: gold `null` / skill `mixed`
- `fe-2026-0004` `confidence_true_negative`: gold `medium` / skill `low`
- `fe-2026-0004` `result.n`: gold `5` / skill `None`
- `fe-2026-0004` `method`: gold `['circuit-discovery', 'gradient-attribution', 'sparse-autoencoders']` / skill `['circuit-discovery', 'gradient-attribution', 'replication', 'sae']`
- `fe-2026-0004` `models.access`: gold `['open-weight']` / skill `['unknown']`
- `fe-2026-0004` `checks_done`: gold `['sanity-check']` / skill `['ablation-validation', 'sanity-check']`
- `fe-2026-0005` `method`: gold `['activation-steering', 'difference-of-means', 'direction-ablation', 'prompted-sandbagging-model', 'random-direction-null']` / skill `['activation-steering', 'difference-of-means-direction', 'directional-ablation', 'prompting']`
- `fe-2026-0005` `benchmarks`: gold `['mmlu', 'wmdp-skill-mcqs']` / skill `['mmlu', 'wmdp']`
- `fe-2026-0005` `checks_done`: gold `['coherence-check', 'off-target-control', 'positive-control', 'pre-registration', 'random-direction-null']` / skill `['bug-audit', 'off-target-control', 'positive-control', 'pre-registration', 'random-direction-null']`

Not scored:

- `id, contributor.*, review.*, dates.*`: trust and provenance fields are assigned by the system, not the skill (PRD section 9)
- `title, revival_conditions, source.title, source.section, related, body`: free wording with no single right answer; not in the PRD's scored list
- `source.quote`: any verbatim fragment is acceptable, so it is checked for validity (quote_valid) instead of compared with gold

## `ask` skill

- **Passed: 6 of 7** (match questions 4/5, no-match questions 2/2)
- Pass rule: match question: cites the expected entry under 'Already tried', names the gold failure_type under 'Where it went wrong', cites only existing entries, and a separate judge finds no invented failure. No-match question: 'Already tried' cites nothing, 'Not found' says so, and the judge finds no invented failure.
- Skill run: {"run_date": "2026-11-14", "skill": "plugin/skills/ask/SKILL.md", "skill_version": "ask-skill v0.1", "model": "claude-sonnet-5-5 (Claude Code `sonnet` subagent alias; resolved ID not confirmed by the model)", "prompt": "evals/prompts/run_ask.md", "mode": "one fresh subagent per question; no command access, so the tool outputs (list_facets, search with an empty query, get per entry) were read from files holding the same JSON the tools return. The subagents could not run keyword searches; they scanned the full 10-entry listing instead.", "wiki_state": "10 entries, all unreviewed at the time the answers were written (fe-2026-0007 was reviewed by an agent afterwards)", "isolation": "subagents were told not to read evals/ (other than the prompt), entries or scouting; this was an instruction, not an enforced sandbox"}

| Question | Expects | Passed | Status | Failed checks |
|---|---|---|---|---|
| `q1` | fe-2026-0001 | yes | scored | - |
| `q2` | fe-2026-0002 | yes | scored | - |
| `q3` | fe-2026-0003 | yes | scored | - |
| `q4` | fe-2026-0004 | yes | scored | - |
| `q5` | fe-2026-0005 | NO | scored | judge_no_invented_failures |
| `q6` | nothing (no-match) | yes | scored | - |
| `q7` | nothing (no-match) | yes | scored | - |

## Limits

- 5 gold items and 7 questions: a spot-check, not a benchmark.
- One model vendor wrote the drafts, the answers, the grades and (until verified) the gold entries.
- Rubric grades and invented-failure judgements come from a grader subagent and are to be spot-checked by the maintainer.
- Keyword-level checks on `ask` answers can pass an answer that is right for the wrong reason; the judge verdict is the backstop.

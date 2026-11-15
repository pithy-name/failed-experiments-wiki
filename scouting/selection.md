# Seed selection

Decided 2026-11-14 by the orchestrator (Claude Fable 5.2), standing in for the maintainer as instructed for this run.

## The rule

A post can seed the wiki only if it is a genuine write-up of a failed experiment **and** the post itself supports every required schema field: hypothesis, claim scope, method, models, result direction, failure type, and a quotable sentence of 15 words or fewer.

How it was applied:

1. Haiku classifiers labelled every candidate yes or no (`scouting/yields.md`).
2. A Sonnet auditor read each "yes" post in full and marked each required field supported or not, strictly: a research question is not a hypothesis, and a setup without data or scale is not a claim scope (`tools/scout/field_audit_prompt.md`, results in `scouting/field_audit/`).
3. `tools/scout/check_audit.py` re-checked every proposed quote against the post text by machine.
4. The orchestrator read the audit evidence for every post that passed, and the post itself for the exception.

**9 posts passed all of this. All 9 of them are selected.** The tenth seed is the closest near-miss, taken as a stated exception (see below). No other post was admitted with a missing field.

## The 10 seed posts

| Entry | Post | Author (first listed) | Published | Topic | Made by | Experiment covered | Required fields supported |
|---|---|---|---|---|---|---|---|
| `fe-2026-0001` | [Negative Results for SAEs On Downstream Tasks and Deprioritising SAE Research (GDM Mech Interp Team Progress Update #2)](https://www.lesswrong.com/posts/4uXCAJNuPKtKBsi28/negative-results-for-saes-on-downstream-tasks) | lewis smith | 2025-03-26 | SAE probing, out-of-distribution detection | gold draft (separate careful pass) | SAE probes vs linear probes for OOD harmful-intent detection | all 7 |
| `fe-2026-0002` | [J-Lens: A Failed Replication on GPT-2](https://www.lesswrong.com/posts/tgn3pD2gLpZvepkWk/j-lens-a-failed-replication-on-gpt-2) | Nelith Bandularatne | 2026-09-07 | Logit-lens variants, replication | gold draft (separate careful pass) | J-Lens vs Logit Lens on GPT-2 small and medium | all 7 |
| `fe-2026-0003` | [Attempt at Finding Alignment Faking on Llama 70B to test sleeper-agent detection generalizes](https://www.lesswrong.com/posts/8dXzDzk7nNK64jBve/attempt-at-finding-alignment-faking-on-llama-70b-to-test) | skn8733 | 2026-07-20 | Alignment faking, model organisms | gold draft (separate careful pass) | Eliciting alignment faking in the 70B checkpoint with training details in the prompt (20, then 50 prompts) | all 7 |
| `fe-2026-0004` | [(Not) Explaining GPT-2-Small Forward Passes with Edge-Level Autoencoder Circuits](https://www.lesswrong.com/posts/2CoLkSdwirr2WnNH6/not-explaining-gpt-2-small-forward-passes-with-edge-level) | David Udell | 2025-07-22 | SAE circuits | gold draft (separate careful pass) | Gradient-based SAE circuit discovery to explain GPT-2-small forward passes | all 7 |
| `fe-2026-0005` | [Eval-Awareness Steering detects the Test, Not the Sabotage](https://www.lesswrong.com/posts/ogvyWqJtSrpgXfc7t/eval-awareness-steering-detects-the-test-not-the-sabotage) | sahilraut | 2026-06-25 | Activation steering, sandbagging | gold draft (separate careful pass) | Steering the eval-awareness direction to change sandbagging | all 7 |
| `fe-2026-0006` | [Do capabilities generalize across propensities?](https://www.lesswrong.com/posts/uH5oo57r24xGXQGKM/do-capabilities-generalize-across-propensities) | Emil Ryd | 2026-05-09 | Fine-tuning, capability transfer across propensities | `contribute` skill | Chess puzzles with bold/plain and hedging/confident propensity swaps (gpt-oss-120b): large performance gap | all 7 |
| `fe-2026-0007` | [Sanity Checks for Sanity Checks for Sparse Autoencoders](https://www.lesswrong.com/posts/EC5H7xakTgxxNXm5g/sanity-checks-for-sanity-checks-for-sparse-autoencoders) | Celene Nightingale | 2026-10-31 | SAE training on synthetic data | `contribute` skill | Per-feature loudness added to synthetic activations to explain BatchTopK failure | all 7 |
| `fe-2026-0008` | [Classifying representations of sparse autoencoders (SAEs)](https://www.lesswrong.com/posts/pn5nBBcLYrnmWXfnY/classifying-representations-of-sparse-autoencoders-saes) | Annah | 2023-11-17 | SAE encodings for classification | `contribute` skill | Sentiment classification on SAE encodings vs raw hidden states | all 7 |
| `fe-2026-0009` | [Training Models to Predict and Explain Their In-the-Wild Behavior](https://www.lesswrong.com/posts/YyAMz52wDxnLhwvWL/training-models-to-predict-and-explain-their-in-the-wild) | Adam Karvonen | 2026-09-04 | Introspection, self-explanation | `contribute` skill | Privileged-access test: training a subject model versus a different 8B model on the same behavior data | all 7 |
| `fe-2026-0010` | [Some negative steganography results](https://www.lesswrong.com/posts/EEvsL9cpgDAxAhTzt/some-negative-steganography-results) | Fabien Roger | 2023-12-09 | Steganography, reinforcement learning | `contribute` skill | PPO on GPT2-large with a BERT classifier reward to learn red/blue 1-bit steganography | 6 of 7 (not `hypothesis`) |

## Why each one qualified

### `fe-2026-0001`: Negative Results for SAEs On Downstream Tasks and Deprioritising SAE Research (GDM Mech Interp Team Progress Update #2)

The PRD's first named example. Headline negative result with a stated prediction, a dense-probe baseline and explicit limits on what it shows.

- Auditor's verdict: genuine = yes; result direction `opposite`; failure type `hypothesis_false`.
- Models named in the post: Gemma 2 9B IT probed at layer 20, with GemmaScope SAEs and chat-finetuned versions of them.
- Quote found verbatim in the post (6 words): "Negative result: SAEs underperformed linear probes"
- Info hazard: none. Auditor's note: Long multi-snippet roundup; SAE probing is the primary failure; JumpReLU snippet is positive; plots are images, not text.
- Found in classification round 1 via: phrase:negative result, tag:sparse-autoencoders-saes, prd-known-example

### `fe-2026-0002`: J-Lens: A Failed Replication on GPT-2

A whole post about one failed replication, with implementation checks and follow-up stress tests. Shows the did_not_replicate direction.

- Auditor's verdict: genuine = yes; result direction `did_not_replicate`; failure type `hypothesis_false`.
- Models named in the post: GPT-2 small (124M) and GPT-2 medium (355M in most places, 255M once); the post's own numbers conflict.
- Quote found verbatim in the post (9 words): "J-Lens does not work on GPT-2 small or medium"
- Info hazard: none. Auditor's note: Beginner author, AI-written code; GPT-2 medium size stated inconsistently; Logit Lens may be unusually strong on GPT-2.
- Found in classification round 1 via: phrase:failed to replicate

### `fe-2026-0003`: Attempt at Finding Alignment Faking on Llama 70B to test sleeper-agent detection generalizes

A null result the author calls unexplained and small-sample. A good test of low confidence and failure_type unknown.

- Auditor's verdict: genuine = yes; result direction `did_not_replicate`; failure type `unknown`.
- Models named in the post: Llama 70B alignment-faking checkpoint from Hughes et al, fine-tuned on about 30k synthetic documents; exact Llama version is not stated.
- Quote found verbatim in the post (13 words): "Not one of the scratchpad, across all 4 tests, met all 4 criteria"
- Info hazard: none. Auditor's note: Probe study never run. Scored by hand, about 90 pairs; author flags underpowered versus source paper.
- Found in classification round 2 via: phrase:null result

### `fe-2026-0004`: (Not) Explaining GPT-2-Small Forward Passes with Edge-Level Autoencoder Circuits

One experiment, clearly scoped as one data point, with a sanity check that passed and a stated reason the approach fell short.

- Auditor's verdict: genuine = yes; result direction `null`; failure type `hypothesis_false`.
- Models named in the post: GPT-2-small with residual-stream sparse autoencoders; interpretability data from Neuronpedia.
- Quote found verbatim in the post (14 words): "localistic approximations of vanilla sparse autoencoders cannot be strung together into fully explanatory circuits"
- Info hazard: none. Auditor's note: SPAR project written up later. Results mostly figures; conclusion goes beyond five prompts.
- Found in classification round 2 via: tag:sparse-autoencoders-saes

### `fe-2026-0005`: Eval-Awareness Steering detects the Test, Not the Sabotage

A pre-registered null with random-direction controls, where the author says the dose may have been too gentle. Shows hyperparams_unexplored and retry welcome.

- Auditor's verdict: genuine = yes; result direction `null`; failure type `hyperparams_unexplored`.
- Models named in the post: Llama-3.1-8B-Instruct.
- Quote found verbatim in the post (7 words): "the dose response is a total flat"
- Info hazard: none. Auditor's note: Single 8B model, one prompted organism; author calls it preliminary. Some results appear only in figures.
- Found in classification round 2 via: tag:activation-engineering

### `fe-2026-0006`: Do capabilities generalize across propensities?

Mostly positive post with one clearly reported shortfall. Tests whether the skill scopes a failure inside a positive write-up. Only non-interpretability training topic among the posts that passed.

- Auditor's verdict: genuine = partial; result direction `smaller_than_expected`; failure type `unknown`.
- Models named in the post: gpt-oss-120b for the Chess figure; Llama 3.1-8B in the appendix; Claude Sonnet generates training completions.
- Quote found verbatim in the post (8 words): "we observe substantially less capability transfer between propensities"
- Info hazard: none. Auditor's note: Results are in figures; no numeric gaps in text; the performance-gap formula is missing from the extracted text.
- Found in classification round 2 via: phrase:did not improve

### `fe-2026-0007`: Sanity Checks for Sanity Checks for Sparse Autoencoders

A failed explanatory hypothesis reported with numbers, inside a post whose final diagnosis is positive.

- Auditor's verdict: genuine = partial; result direction `opposite`; failure type `hypothesis_false`.
- Models named in the post: BatchTopK SAE trained on synthetic activations; TopK and JumpReLU in related runs; GPT-2 appears only as a source of activation statistics.
- Quote found verbatim in the post (8 words): "Instead of improving performance, it actively degrades it"
- Info hazard: none. Auditor's note: Footnote calls the loudness motivation poor; no seeds or error bars reported; the post mainly rebuts a published sanity-check paper.
- Found in classification round 2 via: phrase:did not improve

### `fe-2026-0008`: Classifying representations of sparse autoencoders (SAEs)

Short, self-contained negative result on small open models, with the author unsure whether a pipeline mistake is the cause.

- Auditor's verdict: genuine = yes; result direction `opposite`; failure type `unknown`.
- Models named in the post: Pythia-70m-deduped and Pythia-410m-deduped, with pretrained sparse autoencoders taken from a cited prior release.
- Quote found verbatim in the post (12 words): "So the sparse encodings consistently under-perform compared to the original hidden states."
- Info hazard: none. Auditor's note: Test accuracy numbers are in an image, not text; author unsure if own pipeline caused the result.
- Found in classification round 1 via: tag:activation-engineering

### `fe-2026-0009`: Training Models to Predict and Explain Their In-the-Wild Behavior

A null on privileged access with a cross-model control, in tension with earlier work the authors cite.

- Auditor's verdict: genuine = partial; result direction `null`; failure type `hypothesis_false`.
- Models named in the post: Qwen3-8B and Llama-3.1-8B-Instruct as subjects, with Opus 4.8 as the transcript-reading reference.
- Quote found verbatim in the post (8 words): "We find no privileged access for our self-explanations"
- Info hazard: none. Auditor's note: Authors are uncertain why a prior study found privileged access with the same models; follow-up to the evaluation post.
- Found in classification round 2 via: phrase:null result

### `fe-2026-0010`: Some negative steganography results

EXCEPTION, the only one. Supports six of the seven required fields. The post asks a question (can current RL methods teach hidden 1-bit communication?) and states no prediction, so `hypothesis` is recorded as the proposition tested and says the post poses it as a question. Chosen over the other near-misses because it is a dedicated negative-results post with controls, careful scoping by the author, a different topic from the other nine, and a later note that other work succeeded: the case the retry-welcome fields exist for.

- Auditor's verdict: genuine = yes; result direction `null`; failure type `hyperparams_unexplored`.
- Models named in the post: gpt2-large and bert-base-uncased in the first experiment; GPT-3.5-Turbo and GPT-4-Turbo in the second.
- Quote found verbatim in the post (7 words): "the classifier never had a >50% accuracy"
- Info hazard: none. Auditor's note: Two experiments; second run by a collaborator; a later update points to positive results from other work.
- Found in classification round 1 via: phrase:negative result

## What the selection does not have

- **Topic spread is narrow.** Six of the ten are about sparse autoencoders or closely related interpretability methods. That is what passed the rule, not a choice: the posts that reported failures with enough structure were mostly interpretability posts.
- **Ten different first authors**, which the PRD asks for.
- **The seed entries quote these posts and describe their experiments. They do not judge the authors**, and author confirmation and opt-out are future work.

## The PRD's two named examples

- [Negative Results for SAEs On Downstream Tasks and Deprioritising SAE Research (GDM Mech Interp Team Progress Update #2)](https://www.lesswrong.com/posts/4uXCAJNuPKtKBsi28/negative-results-for-saes-on-downstream-tasks): selected (fe-2026-0001).
- [My Failed AI Safety Research Projects (Q1/Q2 2025)](https://www.lesswrong.com/posts/kiCZzHDkRtupek2mc/my-failed-ai-safety-research-projects-q1-q2-2025): not selected: the post is a roundup of three short projects whose detail is in linked write-ups; for the audited project it does not give the exact setup (claim_scope) or a named model (models).

## Near-misses: one required field short

Genuine or partly genuine failure write-ups that were not seeded because the post does not state one required field.

| Post | Missing field | Auditor's note |
|---|---|---|
| [Negative Results on Group SAEs](https://www.lesswrong.com/posts/jKKbRKuXNaLujnojw/negative-results-on-group-saes) | `claim_scope` | Written a year after the work; figures not in text; teammates' circuits and learned-group results excluded. |
| [Steering Evaluation-Aware Models to Act Like They Are Deployed](https://www.lesswrong.com/posts/peKrvZ6t9PSCzoQDa/steering-evaluation-aware-models-to-act-like-they-are) | `claim_scope` | Failed part is a Jan 2026 edit; main paper result is positive; numbers are in figures, not text. |
| [The Local Interaction Basis: Identifying Computationally-Relevant and Sparsely Interacting Features in Neural Networks](https://www.lesswrong.com/posts/bchjSwxBTxZBFXBXs/the-local-interaction-basis-identifying-computationally) | `claim_scope` | Linkpost summarizing two papers; language-model negative result gets a few sentences; details are in the papers. |
| [GPT-3.5 judges can supervise GPT-4o debaters in capability asymmetric debates](https://www.lesswrong.com/posts/DgKyDTKeGcisEGCnH/gpt-3-5-judges-can-supervise-gpt-4o-debaters-in-capability) | `failure_type` | Only failure_type is missing. Main result is positive; negative results are brief. |
| [NYU Code Debates Update/Postmortem](https://www.lesswrong.com/posts/wsXCXoyvRi3DnWZ2M/nyu-code-debates-update-postmortem) | `failure_type` | Postmortem of two small pilots; author calls setup invalid, not a negative result for debate; failure cause fits no label. |
| [Training Model to Predict Its Own Generalization: A Preliminary Study](https://www.lesswrong.com/posts/BLHBhpJcusmsNjGio/training-model-to-predict-its-own-generalization-a) | `failure_type` | Mostly positive preliminary study; 0.5B result and failed replication are brief; numbers are in figures. |
| [Classifier Context Rot: Monitor Performance Degrades with Context Length](https://www.lesswrong.com/posts/7vpvNM7viJqNWAdG7/classifier-context-rot-monitor-performance-degrades-with) | `hypothesis` | Mostly a positive finding; fine-tuning section is the failure. Results sit in figures; padding-evasion finding is attack-adjacent. |
| [Current activation oracles are hard to use](https://www.lesswrong.com/posts/LXQBcztrWKhtcgQfJ/current-activation-oracles-are-hard-to-use) | `hypothesis` | Summary and body disagree on 1/54 versus 0/54, sycophancy AUC and rollout counts; body used. Also reports small positives. |
| [Does Circuit Analysis Interpretability Scale? Evidence from Multiple Choice Capabilities in Chinchilla](https://www.lesswrong.com/posts/Av3frxNy3y3i2kpaa/does-circuit-analysis-interpretability-scale-evidence-from) | `hypothesis` | Cross-post of paper abstract and summary; failure part is brief, detail is in the arXiv paper; figures omitted. |
| [Evaluating What 2026 Looks Like So Far](https://www.lesswrong.com/posts/u9Kr97di29CkMvjaj/evaluating-what-2026-looks-like-so-far) | `hypothesis` | Mostly a positive human grading of predictions; the o3-mini automation is the failed part; results partly in figures. |
| [Function vectors as a model diffing tool: 17 heads repair a bad fine-tune](https://www.lesswrong.com/posts/6iPEuEnguEtmtaqyJ/function-vectors-as-a-model-diffing-tool-17-heads-repair-a) | `hypothesis` | Mostly a positive repair result; injection test is one section; persona half never names its model; one seed. |
| [Model whisperers: optimized token prefixes can imitate function vectors, filter heads, and steering directions](https://www.lesswrong.com/posts/HGwjBmCKWtj5apGkK/model-whisperers-optimized-token-prefixes-can-imitate) | `hypothesis` | Mostly positive post; failed part is the anti-human result; charts are images; footnote counts degraded output as anti-human. |
| [Models don’t seem to be dishonest in the way humans are](https://www.lesswrong.com/posts/QYmnkQyZD2fDjHCJ8/models-don-t-seem-to-be-dishonest-in-the-way-humans-are) | `hypothesis` | Several results are in figures missing from the text; training hyperparameters and number of steps are not given. |
| [Retrospective on my unsupervised elicitation challenge](https://www.lesswrong.com/posts/aJ3NTJ6tM7yc49kQn/retrospective-on-my-unsupervised-elicitation-challenge) | `hypothesis` | Retrospective of a crowd challenge; failed attempts were by participants, not the author; test exercise and answers withheld. |
| [Whack-a-mole with a broken hammer: does a model internally track its automaton state?](https://www.lesswrong.com/posts/LzeZW9PvR6Njc9ngr/whack-a-mole-with-a-broken-hammer-does-a-model-internally) | `hypothesis` | Mostly positive tracking result; counting gap is sub-finding. Bait follow-up planned but never run. Single small model. |
| [Behavioural statistics for a maze-solving agent](https://www.lesswrong.com/posts/eowhY5NaCaqY6Pkj9/behavioural-statistics-for-a-maze-solving-agent) | `models` | Mostly a positive analysis; the negative result is one sentence plus a footnote; second-batch numbers are not given. |
| [Broken Latents: Studying SAEs and Feature Co-occurrence in Toy Models](https://www.lesswrong.com/posts/XHpta8X85TzugNNn2/broken-latents-studying-saes-and-feature-co-occurrence-in) | `models` | Toy-model post; most findings positive. Real-LLM attempt gets one paragraph and no numbers. Results mainly in plots. |
| [Evaluating Explanations of LLM Behavior In The Wild with Counterfactual Experiments](https://www.lesswrong.com/posts/ExB6KYDcznaFS72eT/evaluating-explanations-of-llm-behavior-in-the-wild-with) | `models` | Summary of a longer paper; numeric results are only in figures; target models unnamed for this evaluation. |
| [Fuzzing LLMs sometimes makes them reveal their secrets](https://www.lesswrong.com/posts/GE6pcmmLc3kdpNJja/fuzzing-llms-sometimes-makes-them-reveal-their-secrets) | `models` | Mostly a positive elicitation post; failure numbers are in plots, not text; one subsection plus the RL attempt. |
| [Takeaways from our robust injury classifier project [Redwood Research]](https://www.lesswrong.com/posts/n3LAgnHg6ashQK3fF/takeaways-from-our-robust-injury-classifier-project-redwood) | `models` | Authors say this is not a demonstrated negative result; setup details are in the linked paper. |

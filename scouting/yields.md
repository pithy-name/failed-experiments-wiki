# Scouting yields

Classification: 2026-11-14, model `claude-haiku-5-5` (Claude Code subagents), prompt `tools/scout/classify_prompt.md`.
Candidate search: 2026-11-14, `https://www.lesswrong.com/api/search` and `https://www.lesswrong.com/graphql`.

These are single-model labels on one candidate list, not an estimate of how many such posts exist on LessWrong / the Alignment Forum. "Yes" means the classifier judged the post a genuine write-up of a failed experiment; it does not mean the post supports every schema field (see the funnel below).

## Headline

- Unique AI-related candidates found by the search: **211**
- Round 1: **18 yes of 60 classified** (30%). The planned sample of 60 (PRD section 8): best-ranked hits of every route in turn, plus the two posts the PRD names as known examples.
- Round 2: **31 yes of 152 classified** (20%). Every remaining candidate. Added because round 1 produced too few posts that support every required schema field (see DECISION-LOG.md, DEC-32).
- Both rounds: **49 yes of 212 classified** (23%).

## Funnel: from "yes" to "can seed the wiki"

A post can seed the wiki only if the post itself supports every required field (hypothesis, claim scope, method, models, result direction, failure type, a quotable sentence). A stronger model audited the "yes" posts field by field (`tools/scout/field_audit_prompt.md`), and `tools/scout/check_audit.py` re-checked each proposed quote against the post text.

- Classified: 212
- Labelled yes: 49
- Audited field by field: 49
- Support every required field, with a verbatim quote: **9**

Which required field was missing, among audited posts that did not pass:

| Field not supported by the post | Posts |
|---|---|
| `hypothesis` | 20 |
| `claim_scope` | 18 |
| `models` | 16 |
| `failure_type` | 11 |
| `result_direction` | 1 |

## By route

A post found by several routes is counted under each of them, so rows do not sum to the headline.

| Route | Returned by API | Kept as candidates | Round 1: yes / classified | Round 2: yes / classified | All: yield |
|---|---|---|---|---|---|
| `phrase:did not improve` | 40 | 16 | 0 / 5 | 4 / 11 | 25% |
| `phrase:didn't work` | 40 | 6 | 1 / 4 | 0 / 2 | 17% |
| `phrase:failed to replicate` | 40 | 7 | 1 / 5 | 1 / 2 | 29% |
| `phrase:lessons learned` | 40 | 16 | 1 / 5 | 0 / 11 | 6% |
| `phrase:negative result` | 40 | 23 | 5 / 5 | 8 / 18 | 57% |
| `phrase:null result` | 40 | 13 | 1 / 4 | 5 / 9 | 46% |
| `phrase:postmortem` | 40 | 14 | 2 / 6 | 0 / 8 | 14% |
| `phrase:retrospective` | 40 | 16 | 0 / 6 | 2 / 10 | 12% |
| `phrase:we tried` | 40 | 27 | 5 / 7 | 3 / 20 | 30% |
| `phrase:what went wrong` | 40 | 8 | 0 / 4 | 0 / 4 | 0% |
| `prd-known-example` | n/a | 0 | 2 / 2 | 0 / 0 | 100% |
| `tag:activation-engineering` | 100 | 9 | 4 / 4 | 3 / 5 | 78% |
| `tag:ai-control` | 100 | 4 | 3 / 4 | 0 / 0 | 75% |
| `tag:ai-evaluations` | 100 | 5 | 1 / 4 | 1 / 1 | 40% |
| `tag:interpretability-ml-and-ai` | 100 | 3 | 0 / 3 | 0 / 0 | 0% |
| `tag:mats-program` | 100 | 8 | 1 / 4 | 2 / 4 | 38% |
| `tag:negative-results` (tag not found) | 0 | 0 | 0 / 0 | 0 / 0 | n/a |
| `tag:postmortems-and-retrospectives` | 100 | 26 | 1 / 4 | 2 / 22 | 12% |
| `tag:replication-crisis` | 100 | 30 | 0 / 4 | 0 / 26 | 0% |
| `tag:sparse-autoencoders-saes` | 100 | 10 | 3 / 5 | 3 / 5 | 60% |

Notes on the routes:

- Phrase routes: the site search, 8 pages of 5 hits per phrase, kept when the post carries an AI-related tag. The search is fuzzy full-text, not exact-phrase.
- Tag routes: the first 100 posts of the tag by relevance. Failure-flavoured tags keep every AI-related post; topical tags keep only posts whose title or description matches a failure phrase.
- `prd-known-example`: the two posts named in the PRD, added by title.
- tag 'negative-results' does not exist on LessWrong; skipped

## Posts labelled yes: round 1

| Post | Author | Published | Detail | Classifier's reason |
|---|---|---|---|---|
| [Negative Results for SAEs On Downstream Tasks and Deprioritising SAE Research (GDM Mech Interp Team Progress Update #2)](https://www.lesswrong.com/posts/4uXCAJNuPKtKBsi28/negative-results-for-saes-on-downstream-tasks) | lewis smith | 2025-03-26 | high | SAE probes underperformed linear probes on OOD harmful-intent detection; chat finetuning closed only half the gap. |
| [My Failed AI Safety Research Projects (Q1/Q2 2025)](https://www.lesswrong.com/posts/kiCZzHDkRtupek2mc/my-failed-ai-safety-research-projects-q1-q2-2025) | Adam Newgas | 2025-06-19 | medium | Several interpretability projects (LLM multiplication, memorisation toy model, ITDA SAEs) that gave negative or inconclusive results. |
| [J-Lens: A Failed Replication on GPT-2](https://www.lesswrong.com/posts/tgn3pD2gLpZvepkWk/j-lens-a-failed-replication-on-gpt-2) | Nelith Bandularatne | 2026-09-07 | high | Replication of J-Lens on GPT-2 fails to beat Logit Lens at any layer; stress tests also fail. |
| [Negative Results on Group SAEs](https://www.lesswrong.com/posts/jKKbRKuXNaLujnojw/negative-results-on-group-saes) | Josh Engels | 2025-05-06 | high | Empirical SAE work on group SAEs and learned groups; authors report the approaches did not beat baselines or yield useful results. |
| [Steering Gemini with BiDPO](https://www.lesswrong.com/posts/WqjkqrEyFDXoHzz9K/steering-gemini-with-bidpo) | TurnTrout | 2025-01-31 | low | Authors ran BiDPO steering against prompt baselines on Gemini; it failed to beat them and the project ended. |
| [Ctrl-Z: Controlling AI Agents via Resampling](https://www.lesswrong.com/posts/LPHMMMZFAWog6ty5x/ctrl-z-controlling-ai-agents-via-resampling) | Aryan Bhatt | 2025-04-16 | medium | Mostly positive control-protocol paper; clearly reports failed cross-step score aggregation methods that did little better than the current step. |
| [(Summary) Progress Update #1 from the GDM Mech Interp Team](https://www.lesswrong.com/posts/HpAr8k74mW4ivCvCu/summary-progress-update-1-from-the-gdm-mech-interp-team) | Neel Nanda | 2024-04-19 | low | Snippet summary; reports a replication where ghost grads underperformed resampling, plus failed Tracr compression. Little detail. |
| [Some Lessons Learned from Studying Indirect Object Identification in GPT-2 small](https://www.lesswrong.com/posts/3ecs6duLmTfyra3Gp/some-lessons-learned-from-studying-indirect-object) | RowanWang | 2022-10-28 | medium | Mostly a positive circuit result, but early mean-ablation knockouts were misleading because the mean retained duplicate-name information. |
| [A Small Negative Result on Debate](https://www.lesswrong.com/posts/CL8RFFCdsBwWWfKYS/a-small-negative-result-on-debate) | Sam Bowman | 2022-04-12 | medium | Human study of single-turn debate; supplied arguments did not improve annotator accuracy. Reported as a null result, briefly. |
| [Steering Evaluation-Aware Models to Act Like They Are Deployed](https://www.lesswrong.com/posts/peKrvZ6t9PSCzoQDa/steering-evaluation-aware-models-to-act-like-they-are) | Tim Hua | 2025-10-30 | low | Mostly positive steering paper; reports failed attempts to train a canary-cued model organism and a prompt baseline that worked better than expected. |
| [Gradient surfing: the hidden role of regularization](https://www.lesswrong.com/posts/Fjoy5SxgBmxfy7FNB/gradient-surfing-the-hidden-role-of-regularization) | Jesse Hoogland | 2023-02-06 | medium | Toy-model and grokking experiments on SGD exploration; the hypothesis and HMC attempts failed. Safety link is indirect (generalization). |
| [Classifying representations of sparse autoencoders (SAEs)](https://www.lesswrong.com/posts/pn5nBBcLYrnmWXfnY/classifying-representations-of-sparse-autoencoders-saes) | Annah | 2023-11-17 | medium | SAE-encoded representations classify sentiment worse than raw hidden states; negative result with per-layer numbers. |
| [Trusted monitoring, but with deception probes.](https://www.lesswrong.com/posts/eaEqAzGN3uJfpfGoc/trusted-monitoring-but-with-deception-probes) | Avi Parrack | 2025-07-23 | medium | Mostly positive probe-monitoring results, but reports failed sub-methods (follow-up questions, LLM reasoning over probe scores) with setup detail. |
| [More information about the dangerous capability evaluations we did with GPT-4 and Claude.](https://www.lesswrong.com/posts/4Gt42jX7RiaNaxCwP/more-information-about-the-dangerous-capability-evaluations) | Beth Barnes | 2023-03-19 | medium | Null result: GPT-4 and Claude did not autonomously replicate in ARC's evals. Borderline, as model-level results are withheld. |
| [OpenAI Responses API changes models' behavior](https://www.lesswrong.com/posts/vTvPvCH2G9cbcFY8a/openai-responses-api-changes-models-behavior) | Jan Betley | 2025-04-11 | medium | Ungrammatical-model training appeared to fail under the Responses API; the API difference confounds safety evals. |
| [Some negative steganography results](https://www.lesswrong.com/posts/EEvsL9cpgDAxAhTzt/some-negative-steganography-results) | Fabien Roger | 2023-12-09 | high | Two RL steganography experiments with controls that failed to produce hidden 1-bit communication; setups and hyperparameters given. |
| [Model whisperers: optimized token prefixes can imitate function vectors, filter heads, and steering directions](https://www.lesswrong.com/posts/HGwjBmCKWtj5apGkK/model-whisperers-optimized-token-prefixes-can-imitate) | Soham Padia | 2026-10-21 | medium | Mostly positive prefix-search work; its anti-human arm failed: prefixes broke coherence instead of producing hostility, and injecting the negative direction changed nothing. |
| [NYU Code Debates Update/Postmortem](https://www.lesswrong.com/posts/wsXCXoyvRi3DnWZ2M/nyu-code-debates-update-postmortem) | David Rein | 2024-05-24 | high | Two pilots of human-judged LLM debate on code; models could not argue incorrect answers well, so the project was dropped. |

## Posts labelled yes: round 2

| Post | Author | Published | Detail | Classifier's reason |
|---|---|---|---|---|
| [GPT-oss is an extremely stupid model](https://www.lesswrong.com/posts/pLC3bx77AckafHdkq/gpt-oss-is-an-extremely-stupid-model) | Guive | 2025-09-09 | medium | Attempted replication of an agentic misalignment blackmail eval on GPT-oss failed to elicit the behavior. |
| [Current activation oracles are hard to use](https://www.lesswrong.com/posts/LXQBcztrWKhtcgQfJ/current-activation-oracles-are-hard-to-use) | aryaj | 2026-03-03 | high | Authors ran activation-oracle probes on sycophancy, missing information and backtracking; the oracles failed or stayed near chance. |
| [Interpreting Preference Models w/ Sparse Autoencoders](https://www.lesswrong.com/posts/5XmxmszdjzBQzqpmz/interpreting-preference-models-w-sparse-autoencoders) | Logan Riggs | 2024-07-01 | high | Mostly positive SAE reward study, but reports clear failures: URL ablation did not close the gap and later-layer SAEs were worse. |
| [Training Model to Predict Its Own Generalization: A Preliminary Study](https://www.lesswrong.com/posts/BLHBhpJcusmsNjGio/training-model-to-predict-its-own-generalization-a) | Tianyi (Alex) Qiu | 2026-05-05 | medium | Meta-training experiments mostly positive, but failed to replicate surprising generalization at 14B and below; reported in detail. |
| [Attempt at Finding Alignment Faking on Llama 70B to test sleeper-agent detection generalizes](https://www.lesswrong.com/posts/8dXzDzk7nNK64jBve/attempt-at-finding-alignment-faking-on-llama-70b-to-test) | skn8733 | 2026-07-20 | high | Null result: no strict alignment faking found across four behavioural tests on Llama 70B checkpoints. |
| [Whack-a-mole with a broken hammer: does a model internally track its automaton state?](https://www.lesswrong.com/posts/LzeZW9PvR6Njc9ngr/whack-a-mole-with-a-broken-hammer-does-a-model-internally) | star2vec | 2026-08-18 | high | Probe study is mostly positive, but the counting sub-task is a clearly reported failure with detail. |
| [Broken Latents: Studying SAEs and Feature Co-occurrence in Toy Models](https://www.lesswrong.com/posts/XHpta8X85TzugNNn2/broken-latents-studying-saes-and-feature-co-occurrence-in) | chanind | 2024-12-30 | high | Toy SAE experiments; tied SAEs still learn broken latents, the Matryoshka parent-feature hypothesis fails, and the fix struggled on real LLMs. |
| [
My Minor AI Safety Research Projects (Q3 2025)](https://www.lesswrong.com/posts/h8FKusANBWfnNoTyc/my-minor-ai-safety-research-projects-q3-2025) | Adam Newgas | 2025-09-19 | low | Steering for uppercase salience failed on a stronger model; a residual-stream retry gave confusing results. |
| [(Not) Explaining GPT-2-Small Forward Passes with Edge-Level Autoencoder Circuits](https://www.lesswrong.com/posts/2CoLkSdwirr2WnNH6/not-explaining-gpt-2-small-forward-passes-with-edge-level) | David Udell | 2025-07-22 | high | Replicated an unsupervised SAE circuit discovery method on GPT-2-small; the resulting explanations did not hold up. |
| [The Local Interaction Basis: Identifying Computationally-Relevant and Sparsely Interacting Features in Neural Networks](https://www.lesswrong.com/posts/bchjSwxBTxZBFXBXs/the-local-interaction-basis-identifying-computationally) | Lucius Bushnaq | 2024-05-20 | medium | Interpretability method works on toy models but fails to help on GPT-2-small and Tinystories, reported as a mostly negative result. |
| [Training Models to Predict and Explain Their In-the-Wild Behavior](https://www.lesswrong.com/posts/YyAMz52wDxnLhwvWL/training-models-to-predict-and-explain-their-in-the-wild) | Adam Karvonen | 2026-09-04 | medium | Counterfactual prediction training works, but open-ended self-explanation is weak and the privileged-access test was null. |
| [Eval-Awareness Steering detects the Test, Not the Sabotage](https://www.lesswrong.com/posts/ogvyWqJtSrpgXfc7t/eval-awareness-steering-detects-the-test-not-the-sabotage) | sahilraut | 2026-06-25 | high | Steering and noise-injection experiments on Llama-3.1-8B; steering null, per-item probe at chance. |
| [Behavioural statistics for a maze-solving agent](https://www.lesswrong.com/posts/eowhY5NaCaqY6Pkj9/behavioural-statistics-for-a-maze-solving-agent) | peligrietzer | 2023-04-20 | high | Maze-agent stats: a fourth impression is dropped as an artifact and one variable shows no effect on a second batch. |
| [Fuzzing LLMs sometimes makes them reveal their secrets](https://www.lesswrong.com/posts/GE6pcmmLc3kdpNJja/fuzzing-llms-sometimes-makes-them-reveal-their-secrets) | Fabien Roger | 2025-02-26 | high | Ran noise and MELBO fuzzing on Qwen; sandbagging-removal and RL uplift attempts gave ambiguous or null results. |
| [Models don’t seem to be dishonest in the way humans are](https://www.lesswrong.com/posts/QYmnkQyZD2fDjHCJ8/models-don-t-seem-to-be-dishonest-in-the-way-humans-are) | David Africa | 2026-07-22 | high | Trained models on their own false reasoning; true and false arms behaved the same and transfer to dishonesty evals was weak. |
| [Do capabilities generalize across propensities?](https://www.lesswrong.com/posts/uH5oo57r24xGXQGKM/do-capabilities-generalize-across-propensities) | Emil Ryd | 2026-05-09 | high | SFT runs on gpt-oss-120b; reasoning/no-reasoning and chess show growing transfer gaps, undercutting inoculation hopes. |
| [Function vectors as a model diffing tool: 
17 heads repair a bad fine-tune](https://www.lesswrong.com/posts/6iPEuEnguEtmtaqyJ/function-vectors-as-a-model-diffing-tool-17-heads-repair-a) | Aniket Ghosh | 2026-08-06 | high | Author patched heads and a direction between two fine-tuned models; the direction-injection test failed to install the behavior in written answers. |
| [My retrospective from MATS 10.0](https://www.lesswrong.com/posts/rktrjGjXEbWsg7zof/my-retrospective-from-mats-10-0) | Nathaniel Mitrani | 2026-10-01 | medium | Trained scheming model organisms; RL drifted to unconditional compliance and trait transfer to agentic settings largely failed. Sparse numeric detail. |
| [Sanity Checks for Sanity Checks for Sparse Autoencoders](https://www.lesswrong.com/posts/EC5H7xakTgxxNXm5g/sanity-checks-for-sanity-checks-for-sparse-autoencoders) | Celene Nightingale | 2026-10-31 | high | Replicates a toy SAE result, then tests many fixes (AuxK, resampling, loudness, more features) that mostly failed; main claim is a critique. |
| [Evaluating Explanations of LLM Behavior In The Wild with Counterfactual Experiments](https://www.lesswrong.com/posts/ExB6KYDcznaFS72eT/evaluating-explanations-of-llm-behavior-in-the-wild-with) | Adam Karvonen | 2026-08-21 | high | Null result: interpretability tools give no uplift over a transcript-only baseline at predicting counterfactual outcomes. |
| [Practical Learnings from Synthetic Document Finetuning](https://www.lesswrong.com/posts/7zGgFPLaTXJwCJccB/practical-learnings-from-synthetic-document-finetuning) | Axel Højmark | 2026-05-26 | medium | Mostly practical SDF tips; two reported sub-experiments (multiple universe seeds, logit diff amplification) gave no real improvement. |
| [GPT-3.5 judges can supervise GPT-4o debaters in capability asymmetric debates](https://www.lesswrong.com/posts/DgKyDTKeGcisEGCnH/gpt-3-5-judges-can-supervise-gpt-4o-debaters-in-capability) | Charlie George | 2024-08-27 | medium | Mostly positive debate results, but reports failed sub-experiments (GPQA, weaker-debater judge training, symmetric GPT-4o) with brief detail. |
| [(Paper) Propensities Please: Exposing Alignment-Faking LLMs using Synthetic Document Finetuning](https://www.lesswrong.com/posts/vDj9HZnBpBECLzshv/paper-propensities-please-exposing-alignment-faking-llms) | florkowski | 2026-10-29 | medium | Mainly positive method, but reports a clear failure: SDF degraded oversight reasoning, needing six weeks of fixes. |
| [Retrospective on my unsupervised elicitation challenge](https://www.lesswrong.com/posts/aJ3NTJ6tM7yc49kQn/retrospective-on-my-unsupervised-elicitation-challenge) | DanielFilan | 2026-04-27 | medium | Challenge where many elicitation strategies on Opus 4.6 failed; the challenge was retired. |
| [I was Wrong, Simulator Theory is Real](https://www.lesswrong.com/posts/mfn32QHwKb55afHq4/i-was-wrong-simulator-theory-is-real) | Robert_AIZI | 2023-04-26 | medium | Mostly positive, but reports a bugged null run and a failed flattery hypothesis (H2) with detail. |
| [Why LLMs Aren't Scientists Yet.](https://www.lesswrong.com/posts/y7TpjDtKFcJSGzunm/why-llms-aren-t-scientists-yet) | Dhruv Trehan | 2026-01-08 | medium | Three of four autonomous research runs failed; the surviving one found semantic entropy fails as a jailbreak detector. |
| [Does Circuit Analysis Interpretability Scale? Evidence from Multiple Choice Capabilities in Chinchilla](https://www.lesswrong.com/posts/Av3frxNy3y3i2kpaa/does-circuit-analysis-interpretability-scale-evidence-from) | Neel Nanda | 2023-07-20 | medium | Mostly positive scaling result, but the semantic explanation of correct-letter heads only partially holds on randomized labels. |
| [Evaluating “What 2026 Looks Like” So Far](https://www.lesswrong.com/posts/u9Kr97di29CkMvjaj/evaluating-what-2026-looks-like-so-far) | Jonny Spicer | 2025-02-24 | medium | Author ran o3-mini prediction extraction and resolution, which performed much worse than humans; main result is a human-graded forecast review. |
| [Takeaways from our robust injury classifier project (Redwood Research)](https://www.lesswrong.com/posts/n3LAgnHg6ashQK3fF/takeaways-from-our-robust-injury-classifier-project-redwood) | dmz | 2022-09-17 | high | Adversarial training classifier failed to reach robustness; follow-up experiments are described in detail. |
| [Classifier Context Rot: Monitor Performance Degrades with Context Length](https://www.lesswrong.com/posts/7vpvNM7viJqNWAdG7/classifier-context-rot-monitor-performance-degrades-with) | Fabien Roger | 2026-05-18 | medium | Monitors miss attacks in long contexts; finetuning mitigations failed to help on prepended MonitorBench. |
| [Evolutionary prompt optimization for SAE feature visualization](https://www.lesswrong.com/posts/hMBTaFvAzdMNnj29c/evolutionary-prompt-optimization-for-sae-feature) | neverix | 2024-11-14 | high | Mostly positive method paper, but reports failed two-feature maximization and a failed AdvPrompter attempt with detail. |

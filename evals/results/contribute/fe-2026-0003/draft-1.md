---
title: "Llama 8B and 70B alignment-faking checkpoints showed no scratchpad meeting the strict four-part definition in four small behavioral tests"
research_area:
  - evals
  - honesty
hypothesis: "The open-source Llama checkpoints fine-tuned on synthetic documents about an RLHF training setup would reliably alignment-fake: comply when told the conversation is monitored (free tier), behave differently when unmonitored (paid tier), and reason that they want to avoid having their values changed. That would give a test bed for checking whether a linear probe that catches backdoored sleeper agents also detects naturally arising deception."
claim_scope: "Four behavioral tests of compliance with harmful requests, comparing free-tier (monitored) and paid-tier (unmonitored) prompts. Run 1: 8B model, 20 prompts, compliance 12.5% free vs 10.0% paid. Run 2: 70B model, 20 prompts, no training details in the prompt, 12.5% free vs 17.5% paid. Run 3: 70B model, 20 prompts, training details in the prompt, 17.5% free vs 20.0% paid. Run 4: 70B model, 50 prompts across 6 harm categories, training details in the prompt, 4% free vs 6% paid. The post describes the prompts it used as Harm-bench prompts, and describes the 70B checkpoint as fine-tuned on 30k documents. The author hand-checked every scratchpad that showed reasoning against a four-part definition of alignment faking taken from Hughes et al. (know the request is harmful, know refusal has training consequences, want to be harmless, explicitly not want values changed and use that as the reason for complying); none met all four. The no-training-details 70B rate was compared with the 0.9% rate the post attributes to Hughes et al. for that setting. Single sprint-scale effort (about 30 hours), samples smaller than the n = 200 of the original work, scoring by hand rather than with the published classifier, and a system prompt file not yet checked against the original. The probe itself was never run, so nothing here tests whether probes generalize from backdoors to alignment faking."
method:
  - prompting
  - behavioral-evaluation
  - scratchpad-review
  - manual-scoring
models:
  - name: "Llama"
    developer: "unknown"
    version: "unknown"
    size: "8B"
    access: "open-weight"
  - name: "Llama"
    developer: "unknown"
    version: "unknown"
    size: "70B"
    access: "open-weight"
benchmarks:
  - "Harm-bench"
result:
  direction: "null"
failure_type: "underpowered"
confidence_true_negative: "low"
checks_done:
  - comparison-to-published-rate
  - manual-scratchpad-review
  - widened-prompt-set
  - with-and-without-training-details
limitations: "Largest run used 50 prompts against n = 200 in the original work, enough to say the rate is low but not to separate a rate of essentially zero from a small nonzero one. The higher alignment-faking rate that the original work reports when training details are included did not appear, and the reason is unresolved; possible causes named are a differing system prompt file, a differing checkpoint configuration, or differing prompts. All scoring was done by hand. The published classifier was not used, and the exact system prompt file was not verified."
revival_conditions: "Worth retrying after checking the with-training-details system prompt against the original file, scoring the existing scratchpads with the published classifier, running 150 to 200 prompts in the with-training-details setting, or if someone reports reliably eliciting alignment faking from these checkpoints."
retry_welcome: true
evidence_level: "author_report"
source:
  type: "lesswrong"
  url: "https://www.lesswrong.com/posts/8dXzDzk7nNK64jBve/attempt-at-finding-alignment-faking-on-llama-70b-to-test"
  title: "Attempt at Finding Alignment Faking on Llama 70B to test sleeper-agent detection generalizes"
  authors:
    - "skn8733"
  published: "2026-07-20"
  lw_tags:
    - "AI Alignment Fieldbuilding"
    - "Deceptive Alignment"
    - "Interpretability (ML & AI)"
    - "AI"
  section: "The part I didn't expect... getting to the model alignment fakes was the hard part"
  quote: "Not one of the scratchpad, across all 4 tests, met all 4 criteria."
info_hazard: "none"
---

The author wanted to test whether a probe on internal activations, shown to catch backdoored sleeper agents, also works on naturally arising alignment faking, but first needed a checkpoint that reliably alignment-fakes. After four rounds of behavioral testing found no case meeting the strict definition, the probe step was not run. The author notes a few prompts where answers differed by tier without any reasoning about training, and plans to verify the prompt file, use the published classifier and increase the sample size.

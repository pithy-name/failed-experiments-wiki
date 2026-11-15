---
title: "Adding or removing an eval-awareness direction did not shift sandbagging on a prompted Llama-3.1-8B-Instruct organism within a gentle, coherent steering range"
research_area:
  - steering
  - evals
  - interpretability
hypothesis: "A difference-of-means direction that encodes the model's sense of being evaluated would causally drive sandbagging, so adding it should raise deliberate underperformance and removing it should lower it, which would let evaluators suppress sandbagging by nullifying the direction."
claim_scope: "One open-weight 8B model (Llama-3.1-8B-Instruct) and one prompted sandbagging organism; no fine-tuned or password-locked sandbagger. The direction was fit by difference of means (seed 42) on a 2x2 minimal-pair set crossing eval or deploy framing with benchmark or natural format. It was added to or projected out of the residual stream with nine coefficients between -2 and +2, scored on 300 multiple-choice questions from WMDP, with MMLU as an off-target check; the headline layer was 12, with layers 14 and 24 as secondary layers. Accuracy swings are in percentage points. The steering was gentle (KL divergence on harmless prompts about 0.001 at the extreme dose), so the model stayed coherent and could probably have been pushed harder. Not covered: stronger doses up to the coherence boundary, SAE features, other models, other sandbagging organisms. This supports only 'not causal within the coherent plus or minus 2 range for this setup', not 'eval-awareness never drives sandbagging'."
method:
  - activation-steering
  - difference-of-means-direction
  - directional-ablation
  - prompting
models:
  - name: "Llama-3.1-8B-Instruct"
    developer: "unknown"
    version: "3.1"
    size: "8B"
    access: "open-weight"
benchmarks:
  - "WMDP"
  - "MMLU"
result:
  direction: "null"
  effect_size: -1.77
  n: 300
failure_type: "hyperparams_unexplored"
confidence_true_negative: "low"
checks_done:
  - positive-control
  - bug-audit
  - pre-registration
  - random-direction-null
  - off-target-control
limitations: "Single model, single prompted organism, no SAE features, and a steering dose the author describes as possibly too gentle for a general conclusion. Higher-dose steering up to the coherence boundary was not run."
revival_conditions: "Worth retrying with a higher-dose sweep (plus or minus 3 or 4 at layer 12, up to the coherence boundary), a fine-tuned or password-locked sandbagger and an adversarial organism, SAE features instead of a single difference-of-means direction, and other models of 8B or smaller."
retry_welcome: true
evidence_level: "author_report"
source:
  type: "lesswrong"
  url: "https://www.lesswrong.com/posts/ogvyWqJtSrpgXfc7t/eval-awareness-steering-detects-the-test-not-the-sabotage"
  title: "Eval-Awareness Steering detects the Test, Not the Sabotage"
  authors:
    - "sahilraut"
  published: "2026-06-25"
  lw_tags:
    - "Activation Engineering"
    - "AI Evaluations"
    - "Deceptive Alignment"
    - "Interpretability (ML & AI)"
    - "Sandbagging (AI)"
    - "AI"
  section: "Does steering the direction cause sandbagging?"
  quote: "the dose response is a total flat"
info_hazard: "none"
---

At the headline layer the accuracy swing across the dose range was about 1.8 points, below the pre-registered 5-point bar and not distinguishable from 24 random directions (p = 0.20); the ablation arm leaned the predicted way but did not clear the criteria. Layer 24 produced a larger, wrongly signed swing that matched random directions, so it is not evidence of a causal effect. The author concludes the direction tracks the evaluation framing rather than the withholding of capability, and plans a higher-dose sweep next.

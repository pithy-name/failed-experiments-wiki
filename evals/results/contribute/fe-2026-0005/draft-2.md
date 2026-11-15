---
title: "An eval-awareness probe and a confidence baseline both scored at chance in picking out which items a prompted Llama-3.1-8B-Instruct sandbagged (153 labelled items)"
research_area:
  - evals
  - interpretability
hypothesis: "Even if the eval-awareness direction does not cause sandbagging, a probe along it might still flag which individual items the model is deliberately getting wrong, and do better than a black-box baseline."
claim_scope: "One open-weight 8B model (Llama-3.1-8B-Instruct) and one prompted sandbagging organism. Per-item labels came from items the model answers correctly under honest framing but wrongly under sandbag framing, with a noise-injection oracle as a second label source; items the model gets wrong even when honest were excluded, leaving 153 of 300 items (100 sandbagging, 53 honest). The probe is a difference-of-means eval-awareness direction, scored by per-item AUROC at every band layer (0.542 at layer 24, 0.42 to 0.55 across layers, standard error about 0.05); the black-box baseline is the model's answer-letter confidence under the sandbag framing (AUROC 0.480). Not covered: other probe types, SAE features, fine-tuned or password-locked sandbaggers, other models. The two label sources agree on only 82 of the 153 items, so the target itself is poorly defined and this result is weak evidence that no per-item signal exists."
method:
  - linear-probing
  - difference-of-means-direction
  - noise-injection
  - prompting
models:
  - name: "Llama-3.1-8B-Instruct"
    developer: "unknown"
    version: "3.1"
    size: "8B"
    access: "open-weight"
result:
  direction: "null"
  n: 153
failure_type: "measurement_noise"
confidence_true_negative: "low"
checks_done:
  - baseline-comparison
  - layer-sweep
  - label-agreement-check
  - positive-control
  - bug-audit
limitations: "Single model, single prompted organism, a single difference-of-means probe, a modest item count (153) with an AUROC standard error of about 0.05, and ground-truth label sources that disagree on nearly half of the items."
revival_conditions: "Worth retrying with a fine-tuned or password-locked sandbagger and an adversarial organism, SAE features instead of one linear direction, and other models of 8B or smaller; because the label sources disagree, a retry also needs per-item labels that the sources agree on."
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
  section: "Does the direction predict which items get sandbagged?"
  quote: "neither detector predicts which items are sandbagged"
info_hazard: "none"
---

Both the probe and the confidence baseline sat within noise of 0.5, and the small edge of the probe over the baseline was judged too small to count. The author reads the 54 percent agreement between the two label sources as a sign that which item is sandbagged is not a well-defined per-item quantity, which would limit what any per-item detector could show. The author takes the three results together to mean the direction detects the evaluation framing, not the sandbagging itself.

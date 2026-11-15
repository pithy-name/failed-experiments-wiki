---
title: "J-Lens did not outperform the Logit Lens at intermediate layers of GPT-2 small and medium in a CPU re-implementation"
research_area:
  - interpretability
hypothesis: "J-Lens, which is meant to correct for how representations change across layers, would recover the model's next-token and future-token predictions from intermediate layers better than the Logit Lens, which assumes every layer uses the same coordinates as the final layer."
claim_scope: "Only GPT-2 small (124M) and GPT-2 medium (355M), using the author's own CPU re-implementation of J-Lens (the official repo was used only as a reference), compared with the Logit Lens. Evaluation used 60 held-out prompts, a per-layer top-1 next-token rank metric (11 layers on small, 23 on medium) and a future-token metric at offsets p+1 to p+5 (layer 9 in the small-model run). J-Lens was fit on 30 sequences, then refit on 150, against roughly 1000 in the original paper. Not covered are larger GPT-2 models, other model families, instruction-tuned models and fitting at the original paper's data scale. The scaling trend rests on two model sizes."
method:
  - jacobian-lens
  - logit-lens
  - sparsity-thresholding
models:
  - name: "GPT-2 small"
    developer: "unknown"
    version: "unknown"
    size: "124M"
    access: "open-weight"
  - name: "GPT-2 medium"
    developer: "unknown"
    version: "unknown"
    size: "355M"
    access: "open-weight"
result:
  direction: "did_not_replicate"
  n: 60
failure_type: "hypothesis_false"
confidence_true_negative: "medium"
checks_done:
  - bug-audit
  - baseline-comparison
  - more-data-refit
  - frequency-confound-check
  - sparsity-thresholding
  - hyperparameter-sweep
  - scale-sweep
limitations: "Only GPT-2 small and medium were tested, so gpt2-large, gpt2-xl and other model families are untested. The post notes that the Logit Lens is unusually strong on GPT-2, so the result may not carry over to other models. J-Lens was fit on far fewer sequences than in the original paper, and the scale comparison uses only two data points. The original deception-under-instruction question and instruction-tuned models were not tested."
revival_conditions: "Worth re-running on larger GPT-2 models and on non-GPT-2 models, where the Logit Lens may be weaker, and with a fit closer to the original paper's data scale. The post itself expects the gap to keep widening across GPT-2 sizes."
retry_welcome: false
evidence_level: "independent_reproduction"
source:
  type: "lesswrong"
  url: "https://www.lesswrong.com/posts/tgn3pD2gLpZvepkWk/j-lens-a-failed-replication-on-gpt-2"
  title: "J-Lens: A Failed Replication on GPT-2"
  authors:
    - "Nelith Bandularatne"
  published: "2026-09-07"
  lw_tags:
    - "AI"
  quote: "J-Lens does not work on GPT-2 small or medium."
info_hazard: "none"
---

The author ported the Jacobian lens to CPU and checked the port with two tests: setting the Jacobian to the identity reproduces the Logit Lens exactly, and a finite-difference gradient check agrees at float64. J-Lens then ranked the model's own next token worse than the Logit Lens at every layer on GPT-2 small, and won only one layer on GPT-2 medium by a one-rank margin. A sparsity-thresholded variant looked like a win at 7 of 11 layers, but the author traced it to the metric rewarding frequent filler tokens and to GPT-2's outlier dimensions, and drew two lessons for probe work: rank metrics can be gamed by token frequency, and magnitude thresholding picks out outlier dimensions rather than meaningful structure.

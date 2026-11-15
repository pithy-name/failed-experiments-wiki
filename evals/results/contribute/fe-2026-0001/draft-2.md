---
title: "Retraining or finetuning SAEs on chat data closed about half the gap to dense probes for harmful-intent detection on Gemma 2 9B IT"
research_area:
  - "interpretability"
hypothesis: "The original GemmaScope chat SAEs were trained on pretraining-style text formatted as user prompts, not on chat rollouts. The authors suspected this was why SAE probes lagged dense probes on a chat-specific task, and expected SAEs trained or finetuned on chat data to capture chat-specific features and do better."
claim_scope: "Two ways of making chat-specialised SAEs were tried: retraining from scratch on chat data only, and finetuning the existing GemmaScope SAEs on chat data. Finetuning variants covered starting from the pretrained versus instruction-based GemmaScope SAEs, starting finetuning before the end of training to equalise step counts, random re-initialisation of a fraction of latents (latent resampling), and adding the probe training prompts to the finetuning mix. Evaluation was on the harmful-intent probing task (Gemma 2 9B IT, layer 20, OOD set built from held-out datasets and jailbreaks) plus frequency-weighted auto-interpretability scores. Most later results used finetuned SAEs because that was the quickest option. Not covered: other tasks, models or layers, longer chat finetuning, or other SAE architectures."
method:
  - "sae"
  - "sae-finetuning"
  - "latent-resampling"
  - "linear-probing"
models:
  - name: "Gemma 2 9B IT"
    developer: "unknown"
    version: "unknown"
    size: "9B"
    access: "unknown"
benchmarks:
  - "HarmBench"
  - "Alpaca"
  - "Over-refusal bench"
  - "AdvBench"
result:
  direction: "smaller_than_expected"
failure_type: "unknown"
confidence_true_negative: "medium"
checks_done:
  - "baseline-comparison"
  - "variant-comparison"
  - "autointerp-eval"
limitations: "The authors note their setup may be very noisy and that a larger probing dataset might reveal differences between the finetuning variants, which showed no statistically significant differences on the OOD probing results. Chat finetuning was short compared with pretraining, so chat-specialised latents may be less well trained than the latents they replaced. Auto-interpretability scores were hard to interpret because of high dataset dependence."
revival_conditions: "A larger probing dataset might allow a significant difference between the finetuning variants to show up, according to the authors."
retry_welcome: true
evidence_level: "author_report"
source:
  type: "alignment_forum"
  url: "https://www.lesswrong.com/posts/4uXCAJNuPKtKBsi28/negative-results-for-saes-on-downstream-tasks"
  crosspost_url: "https://www.alignmentforum.org/posts/4uXCAJNuPKtKBsi28/negative-results-for-saes-on-downstream-tasks"
  title: "Negative Results for SAEs On Downstream Tasks and Deprioritising SAE Research (GDM Mech Interp Team Progress Update #2)"
  authors:
    - "lewis smith"
    - "Senthooran Rajamanoharan"
    - "Arthur Conmy"
    - "CallumMcDougall"
    - "Tom Lieberum"
    - "János Kramár"
    - "Rohin Shah"
    - "Neel Nanda"
  published: "2025-03-26"
  lw_tags:
    - "Interpretability (ML & AI)"
    - "Sparse Autoencoders (SAEs)"
    - "AI"
  section: "Comparing different ways to train Chat SAEs"
  quote: "neither is sufficient to match the performance of a dense probe in our setting"
info_hazard: "none"
---

Both approaches improved probing results over the baseline GemmaScope SAEs, but neither reached dense-probe performance; the authors summarise this as closing about half the gap. The variants did about as well as each other on probing metrics, so the team used finetuning for the rest of the project. In the auto-interpretability comparison, finetuning from the pretraining-data SAEs scored slightly better than the original instruction-formatted SAEs unless latent resampling was used.

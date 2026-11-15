---
title: "SAE probes underperformed dense linear probes at out-of-distribution harmful-intent detection on Gemma 2 9B IT"
research_area:
  - "interpretability"
hypothesis: "Sparse probes built on one or a few SAE latents would generalise better out of distribution than dense linear probes, because an interpretable sparse basis was expected to latch onto the true signal rather than spurious correlations. The authors also took a competitive showing on a downstream task as a sign that SAE research was worth continuing."
claim_scope: "One downstream task: detecting harmful user intent in prompts. Training data was HarmBench harmful prompts versus Alpaca harmless prompts, with formatting differences normalised, plus some jailbreak suffixes and innocuous instruction transformations (4046 train, 1014 validation examples). The OOD set (3850 examples) used other datasets (an over-refusal benchmark, an internal chat training set, AdvBench) and held-out jailbreaks and transformations. Model and site: Gemma 2 9B IT at layer 20, with GemmaScope SAEs and SAEs finetuned on chat data. Compared 1-sparse probes, k-sparse probes (k from 2 to 50, latents chosen by mean difference or by L1 regression) and linear probes on the SAE reconstruction against a dense linear probe on the residual stream. Not covered: other tasks, models, layers, SAE architectures or kinds of distribution shift. The authors say they cannot extrapolate confidently to probes versus SAEs in all OOD settings."
method:
  - "sae"
  - "sparse-probing"
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
  direction: "opposite"
failure_type: "hypothesis_false"
confidence_true_negative: "medium"
checks_done:
  - "baseline-comparison"
  - "hyperparameter-sweep"
  - "held-out-ood-set"
  - "reconstruction-probe-control"
limitations: "Single model and layer, and one task. The authors say they cannot make confident extrapolations about probes versus SAEs in all OOD settings. SAE-based inspection was used to clean spurious correlations out of the dataset before probing; the post notes this slightly stacks the deck against SAEs, since uncleaned data might have hurt the linear probes. The post speculates that attention-head probes would also do well here; none are reported."
revival_conditions: "The authors say they could return to SAE research if there is significant progress on core SAE issues or if they found a particularly important and tractable direction."
retry_welcome: false
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
  section: "Using SAEs for OOD Probing"
  quote: "SAE probing does not match the performance of a linear probe"
info_hazard: "none"
---

Single-latent SAE probes failed to fit the training set. Probes on about 20 latents fit it and generalised to the in-distribution test set but did worse on the OOD set, while dense residual-stream probes were near the ceiling on every split, and probes on the SAE reconstruction also trailed them OOD. The team concluded that SAEs are unlikely to be a game-changer and moved effort to other directions, while keeping SAEs as a tool, for example for finding spurious correlations in datasets.

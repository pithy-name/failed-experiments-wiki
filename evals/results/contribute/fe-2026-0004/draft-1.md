---
title: "Gradient-based unsupervised SAE circuit discovery did not give explanatory circuits for five GPT-2-small next-token predictions"
research_area:
  - interpretability
hypothesis: "That sparse autoencoder features, taken as the primitives of an explanation, plus a gradient-based unsupervised circuit discovery algorithm, would let the authors give a concrete mechanistic explanation of naturalistic forward passes (why the model writes the token it does). The post frames the project as either showing this works or showing where sparse autoencoder circuits fail as full explanations."
claim_scope: "A replication, done as a SPAR project, of the gradient-based unsupervised circuit discovery algorithm of Marks et al. (2024) (feature nodes scored by activation times loss gradient, edges by gradients between features, corrected for double-counted paths), run on GPT-2-small with sparse autoencoders (residual-stream autoencoders in the sanity check; the post gives no training details). The algorithm was reimplemented and a few bugs were fixed; the test of explanatory power is the authors' own. Judged on five short prompts by reading the single top feature node for each prompt, plus the upstream edges feeding the two features that predicted the model's top token. Not tested: cross-layer transcoders or other autoencoder variants, other models, a larger prompt set, or a quantitative measure of explanation quality. This does not show that sparse autoencoder circuits can never explain a forward pass."
method:
  - sae
  - circuit-discovery
  - gradient-attribution
  - replication
models:
  - name: GPT-2-small
    developer: unknown
    version: unknown
    size: unknown
    access: unknown
result:
  direction: "mixed"
failure_type: hypothesis_false
confidence_true_negative: low
checks_done:
  - sanity-check
  - ablation-validation
limitations: "Only five prompts, with explanation quality judged by eye rather than by a metric. The ablation check the post mentions concerns causal threads with a clear interpretation, not the explanatory value of the graph's edges. The post does not report trying cross-layer transcoders itself."
revival_conditions: "Worth revisiting with cross-layer (global) approximations of the model internals, which the authors say a later cross-layer transcoder circuit result suggests is what makes explanatory circuits work, and with a larger prompt set and a quantitative measure of explanation quality."
retry_welcome: true
evidence_level: author_report
source:
  type: lesswrong
  url: "https://www.lesswrong.com/posts/2CoLkSdwirr2WnNH6/not-explaining-gpt-2-small-forward-passes-with-edge-level"
  title: "(Not) Explaining GPT-2-Small Forward Passes with Edge-Level Autoencoder Circuits"
  authors:
    - David Udell
    - hrdkbhatnagar
    - JacksonKaunismaa
  published: "2025-07-22"
  lw_tags:
    - Interpretability (ML & AI)
    - Sparse Autoencoders (SAEs)
    - AI
  section: Results
  quote: "We found that that didn't work with this algorithm."
info_hazard: none
---

The authors reimplemented a gradient-based circuit discovery algorithm for sparse autoencoder features and applied it to a handful of short GPT-2-small prompts. A sanity check recovered one known causal thread, and for two of the five prompts the top feature pointed at the model's top next token, but the upstream nodes and edges did not give a readable account of why the model produced its output. They concluded that circuits built from local autoencoder approximations are not enough here, and pointed to cross-layer approximations as the likely missing piece.

## Already tried

- **fe-2026-0001**: A Google DeepMind (GDM) mechanistic interpretability team tested your plan almost exactly. They probed harmful user intent (HarmBench vs Alpaca prompts) with single SAE latents, k-sparse probes (k = 2–50) and linear probes on SAE reconstructions. All were compared against a dense linear probe on the residual stream. The dense probe was near-perfect on every split. The SAE probes, including ones from SAEs finetuned on chat data, did not match it on held-out jailbreaks and datasets (quote: "on the OOD set, SAE probing does not match the performance of a linear probe").
  Models: Gemma 2 9B IT, layer 20, GemmaScope SAEs · Evidence: author_report, confidence it is a true negative: medium · Badges: unreviewed, retry-welcome. The entry was drafted by a model and is not yet human-verified.
- **fe-2026-0008**: A logistic regression on SAE encodings scored lower on IMDB sentiment than one on raw hidden states. The task is sentiment, not harmful intent.
  Models: Pythia-70m and Pythia-410m, last-token states · Evidence: author_report, confidence it is a true negative: low · Badges: agent-written, unreviewed, retry-welcome

## Where it went wrong

- **fe-2026-0001**: failure type `hypothesis_false`. The authors could not say which explanation applies, so the entry gives no confirmed cause. The scope matters: one model, layer and concept, and a single train vs out-of-distribution split of jailbreak types. The text reports no scores for the SAE probes (they appear only in plots), and the setup may have been too noisy to separate the SAE-finetuning variants.
- **fe-2026-0008**: failure type `unknown`. The author listed three open explanations: high-level features are missing from the sparse code, sentiment is poorly encoded, or the hidden-state pipeline has a bug. Left-padding and batch handling in transformer-lens was never confirmed. Only some Pythia-410m layers could be run, because one SAE configuration would not load for all layers.

## What to avoid

- **Don't expect SAE probes to win out of distribution without a plan for it.** The dense probe was near-perfect on every split in fe-2026-0001, so there was little headroom to beat.
- **Don't compare SAE and dense probes on a single in-distribution split.** fe-2026-0001 held out jailbreaks and rewrites, and in-distribution results can hide the gap. Keep the held-out split.
- **Don't clean spurious data differences with SAEs and then compare the probes.** The fe-2026-0001 authors did this, and they say it slightly stacks the deck against SAEs because the dense probe benefits too. Decide how you handle this up front.
- **Verify your activation pipeline before trusting a negative.** fe-2026-0008 could not rule out a padding or batching bug. Run a reconstruction sanity check, and test cross-implementation if you can.
- **Don't generalise from a single layer, model or concept.** Both entries are narrow in scope (fe-2026-0001, fe-2026-0008).
- **Pre-specify SAE-finetuning comparisons with enough data.** fe-2026-0001 says its probing set may have been too small to separate the SAE-finetuning variants.

## Worth retrying

- **fe-2026-0001** (`retry_welcome`: true). Its revival conditions are:
  - SAEs that address known problems such as missing concepts or feature absorption;
  - a larger probing dataset;
  - other models, layers or concepts;
  - settings with very noisy labels or scarce data, where the post cites related work finding sparse probes can win.

  Your plan fits the last condition if you choose noisy-label or low-data regimes deliberately.
- **fe-2026-0008** (`retry_welcome`: true, confidence low). Revisit it if the left-padding and batch handling is confirmed correct, or if the comparison is run on tasks other than sentiment.

## Not found

The wiki holds 15 entries, so a gap here means little. It has none on:
- SAE probes for harmful intent on any model other than Gemma 2 9B IT, or at layers other than 20;
- Llama or Qwen SAEs, or SAEs you train yourself on the target model (fe-2026-0001 used pretrained GemmaScope SAEs and chat-finetuned variants);
- attention-head probes (the fe-2026-0001 authors suggest they would do well but did not report testing them);
- comparisons in the noisy-label or scarce-data regime;
- probe robustness to adversarial attackers aware of the probe.

Four other entries concern SAE training quality on a synthetic benchmark (BatchTopK, TopK, JumpReLU feature recovery). I did not open them. Their titles bear on SAE quality, not on probing, so I did not cite them. They are fe-2026-0007, fe-2026-0012, fe-2026-0013 and fe-2026-0014.

## FRICTION

- **The "has anyone tried this?" answer rests on one entry.** Everything strong comes from fe-2026-0001, which is unreviewed and drafted by a model. Its contributor note says "Awaiting verification by the maintainer; not yet human-verified." The metadata says `type: human` while the note says model-drafted, so the label is inconsistent.
- **The skill's confidence field is a judgement I could not check.** I did not open the source posts, so I can't confirm "medium".
- **Keyword search ranks poorly.** An empty query with a `method=sae` filter returned score 0 for everything, and `matched_terms` was empty. The note says any one matching term lists an entry, so common words like "feature" and "learning" pulled in unrelated entries such as fe-2026-0010 and fe-2026-0009. Only the first query was useful; the second was mostly noise.
- **The `method` facet is fragmented.** `sae`, `sparse-autoencoders`, `sae-probing` and `chat-sae-finetuning` are separate values. The `method=sae` filter missed fe-2026-0001 and fe-2026-0004, so the skill's "use filters from list_facets" step gives incomplete results. Free-text search compensated here.
- **The format has no slot for "related but not about probing".** The four synthetic-benchmark entries were awkward to place, so I put them in Not found.
- **I read only two of the 15 entries in full.** The skill says to scan titles in a small wiki, and I did, from the search results. I did not open fe-2026-0007, 0012, 0013 or 0014, so my judgement that they are irrelevant rests on titles alone.
- **Surprising:** the facets list a single `source.type` of `alignment_forum` and 14 `lesswrong`, but fe-2026-0001 is a crosspost. This is fine, but it means the type field reflects where the entry was filed.
- **No failures from the MCP tools themselves.** Nothing errored.

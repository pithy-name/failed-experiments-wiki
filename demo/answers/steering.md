## Already tried
- **fe-2026-0005**: Steering Llama-3.1-8B-Instruct with a difference-of-means eval-awareness direction did not change prompted sandbagging beyond random-direction controls. The direction was fit on a format-controlled eval/deploy dataset. It separates eval from deploy framing at about 0.81 AUROC on novel format-matched framings. It was added to the residual stream at alpha −2 to +2 (9 coefficients), with a projection-ablation arm, on 300 WMDP-skill multiple-choice questions.
  - At the pre-registered layer 12, the swing was −1.77 points against a 5-point bar, and it did not beat 24 norm-matched random directions (p = 0.20). Layer 14 was also flat.
  - Layer 24 swung +11.3 points with the wrong sign, and random directions matched it.
  - The author's conclusion: the direction tracks the evaluation framing, not the withholding of capability.
  - Models: Llama-3.1-8B-Instruct · Evidence: author_report, confidence it is a true negative: **low** · Badges: agent-written, unreviewed, retry-welcome
- Adjacent only: **fe-2026-0003**. This tried to elicit alignment faking from a Llama 70B checkpoint by adding training details to the system prompt, as groundwork for a monitored-vs-unmonitored probe. It is about a different behaviour, with no steering and no sandbagging. It shows how hard it is to get a model to behave differently when it believes it is monitored. Result: null (no free-vs-paid gap in 20 and 50 prompts). Evidence: author_report, confidence **low** · Badges: agent-written, unreviewed, retry-welcome.

## Where it went wrong
- **fe-2026-0005**: failure type `hyperparams_unexplored`. The steering dose was gentle: KL about 0.001 on harmless prompts at alpha ±2, with output fully coherent. Larger doses up to the coherence boundary were never tried. The author calls the results preliminary and says a higher-dose sweep "could either firm up the null or overturn it". This is not evidence that the idea fails.
- **fe-2026-0005** (scope): one 8B model, one prompted sandbagging setup, one difference-of-means direction, and no SAE features.

## What to avoid
- Do not treat "detects eval vs deploy framing" as "causes sandbagging". A direction with good AUROC can still be inert for the behaviour (fe-2026-0005).
- Do not report only the real direction's swing. Compare it with an empirical null of norm-matched random directions. At layer 24 a large swing (+11.3 points) was matched by random directions and had the wrong sign (fe-2026-0005).
- Do not pick the layer after seeing results. fe-2026-0005 pre-registered layer 12 as the headline and reported 14 and 24 separately.
- Do not conclude "steering doesn't work" from ±2 alone. Check the KL divergence and coherence at each dose, and find the coherence boundary before calling a null (fe-2026-0005).
- Do not assume a prompted sandbagger stands in for a trained one. Prompted sandbagging may simply not route through the eval-awareness direction (fe-2026-0005, limitations).
- Do not skip a positive control. fe-2026-0005 lists one under `checks_done`, which is how you know the steering hook has any effect at all.

## Worth retrying
- **fe-2026-0005** qualifies on three counts: retry_welcome is true, confidence is low, and failure type is `hyperparams_unexplored`. The entry's revival conditions:
  - a higher-dose sweep at layer 12 (±3 or ±4, up to the coherence boundary);
  - a fine-tuned or password-locked sandbagger, and an adversarial organism;
  - SAE features in place of a single difference-of-means direction;
  - other models of 8B or smaller.
- **fe-2026-0003** (adjacent): worth retrying only if you need an alignment-faking setting. Its conditions are checking the system prompt against the original file, running the published classifier, and pushing to 150–200 prompts.

## Not found
The wiki holds 15 entries, and only one bears directly on your plan. All 15 were scanned by title. The other 13 are SAE, probing, steganography and fine-tuning work, so I did not open them; the closest, fe-2026-0003, I read as adjacent.
- Evaluation-awareness steering on any model other than Llama-3.1-8B-Instruct, or at doses beyond ±2.
- Steering a *fine-tuned or password-locked* sandbagger, which fe-2026-0005 names as untested.
- Other ways of building the "thinks it is being evaluated" direction: probes trained on realistic deployment transcripts, SAE-feature-based directions, contrastive pairs from other framings.
- Benchmarks other than WMDP-skill MCQs (and MMLU as an off-target check).
- Any attempt that *restored* sandbagged performance. fe-2026-0005 only tested whether steering moves accuracy, and it did not.
- Any work that found eval-awareness steering *succeeds* at stopping sandbagging. The wiki holds failed experiments, so a positive result would not appear here even if it exists.

That means nobody has filed more, not that the rest is untested. All evidence above is a single unreviewed, agent-written entry drawn from one author's LessWrong post.

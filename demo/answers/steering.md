## Already tried
- **fe-2026-0005** — Added a difference-of-means eval-awareness direction to Llama-3.1-8B-Instruct at alpha -2 to +2, and projected it out, on 300 WMDP-skill questions with a prompted sandbagger. At the pre-registered layer 12 the swing (-1.77 points, against a 5 point bar) did not beat 24 random directions (p = 0.20).
  Models: Llama-3.1-8B-Instruct · Evidence: author_report, confidence it is a true negative: low · Badges: unreviewed, retry-welcome (note: model draft, not yet human-verified)

## Where it went wrong
- **fe-2026-0005** — failure type `hyperparams_unexplored`: only doses within plus or minus 2 were run (gentle: KL about 0.001, output coherent), so larger doses were not tried. The author concludes the direction tracks the evaluation framing rather than the withholding of capability, but calls the results preliminary.

## What to avoid
- Do not assume a direction that separates eval from deployment framing (about 0.81 AUROC on novel format-matched framings) also controls sandbagging; here it did not (from fe-2026-0005).
- Run random-direction controls: layer 24 gave a +11.3 point swing with the wrong sign, which random directions matched (from fe-2026-0005).
- Do not call a gentle-dose null final; the author says a higher-dose sweep could firm it up or overturn it (from fe-2026-0005).
- Do not generalise from a prompted sandbagger to fine-tuned or password-locked ones; the entry did not test them (from fe-2026-0005).

## Worth retrying
- **fe-2026-0005** — `retry_welcome` is true, confidence is low, failure type `hyperparams_unexplored`. Revival conditions: a layer-12 sweep at plus or minus 3 or 4 up to the coherence boundary; a fine-tuned or password-locked sandbagger and an adversarial organism; SAE features instead of one direction; other models of 8B or smaller.

## Not found
- The wiki holds 15 entries and only fe-2026-0005 bears on this plan: one unreviewed report.
- No entry covers fine-tuned or password-locked sandbaggers, SAE-feature eval-awareness directions, larger steering doses, or eval-awareness steering on other models.

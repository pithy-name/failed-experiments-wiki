## What it does

It's a searchable wiki of failed AI-safety experiments. Each entry comes from a LessWrong or Alignment Forum post and records:

- the hypothesis
- what was tested and its scope
- the result and why it failed
- the checks done, the limitations, and when a retry is worth it

The plugin exposes it through tools and three skills. Right now it holds 15 entries, mostly interpretability (SAEs, probing, steering).

## What you can ask me

| # | Ask | Uses | Notes |
|---|---|---|---|
| A1 | "I plan to do X. Has it been tried, where did it fail, what should I avoid?" | `ask` skill | The core use. I cite entry IDs and never state a failure that isn't in an entry. |
| A2 | "Show entries where the failure was `hypothesis_false` and retries are welcome." | search and filters | Every field is filterable, such as method, model, failure type, review status. |
| A3 | "Add this LessWrong post to the wiki: <URL>" | `contribute` skill | Drafts entries and opens a pull request. |
| A4 | "Review fe-2026-00NN against its source." | `review` skill | Marks it reviewed or contested, and opens a pull request. |
| A5 | "Which entries are unreviewed or agent-written?" | search by badge | Useful for knowing how far to trust a result. |

A3 and A4 publish to a remote repo. I'll confirm with you before running either.

## One thing working

I asked: "I want to use sparse probes on SAE latents for harmful-intent detection. Has it failed before?" The search returned five ranked hits, and fe-2026-0001 scored highest (53, with four terms matched). Its content:

- **Result:** sparse SAE probes generalised **worse** than a dense linear probe to held-out jailbreaks and datasets. The dense probe was near-perfect on every split.
- **Scope:** Gemma 2 9B IT, layer 20, one concept (harmful user intent), n=3850. It says nothing about other models, layers, concepts or SAE types.
- **Avoid:** the authors cleaned spurious formatting out of the data with SAEs first, which they say slightly stacks the deck against SAEs. The single-latent and k-sparse scores appear only in plots, not in the text.
- **Worth retrying with:** SAEs that fix feature absorption or missing concepts, larger probing data, other models or layers, or very noisy labels and scarce data.
- **Source:** the GDM Mech Interp Team progress update (Mar 2025), author-reported.
- **Trust:** the entry is badged `unreviewed`, so no one has checked it against the post.

## FRICTION

| # | Type | What happened |
|---|---|---|
| F1 | Inconsistent | fe-2026-0001 has `contributor.type: human`. Its own note says it is a "Model draft (claude-sonnet-5-5)… not yet human-verified". The "human" count (5) therefore overstates human authorship. |
| F2 | Missing | Every entry has `contributor.handle: HANDLE-TBD`, including the one reviewer record. Attribution is unusable. |
| F3 | Surprising | 14 of 15 entries are `unreviewed`. Only fe-2026-0007 is `reviewed`, and that review was by an agent. Everything I cited is unchecked by a person. |
| F4 | Search quality | Matching is keyword-only and OR-based. My query said "generalization" but the entry says "generalised". It did not match (`matched_terms` omitted it). Single-word hits like "sae" scored 13–15 and looked like weak matches. |
| F5 | Unclear | `source.type` says `alignment_forum` but the primary URL is lesswrong.com, with the AF link only as `crosspost_url`. |
| F6 | Unclear | The fields for `result` are sparse: only one entry has an effect size, and none has a CI. Filtering on result magnitude is mostly impossible. |
| F7 | Unverified | `git status` shows uncommitted edits to `entries/fe-2026-0010.md` and to the skill files. I didn't check whether the tools read the working tree or the committed state, so I can't say which version of fe-2026-0010 you'd get. |
| F8 | Not done | I only exercised the MCP tools (search, facets, get). I did not run the `ask`, `contribute` or `review` skills, `fetch_source`, or any pull-request-creating tool. I did not verify entry 0001 against its LessWrong source. |
| F9 | Missing | I found no in-tool help or README listing what to ask. The "what you can ask" table above is my inference from the tool and skill descriptions. |

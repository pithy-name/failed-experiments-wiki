---
name: ask
description: Answer "what has been tried on this, where did it go wrong, what should I avoid?" from Carpe Ignota, the wiki of negative results in AI safety. Use when the user describes an AI-safety experiment they plan to run, or asks whether an idea has already been tried without success.
---

# ask: what's been tried?

The user describes a research plan. You tell them what the wiki holds on it,
citing entry IDs, and you say plainly when the wiki holds nothing. Every entry
is a negative result: an experiment whose result was null, neutral, smaller
than expected, or opposite to the hypothesis.

**Version:** ask-skill v0.1

## Ground rules

- **Only the wiki.** Every negative result you state must come from an entry,
  with its ID. Never add results from your own memory of the literature. If you know of
  relevant work that is not in the wiki, you may say "the wiki has no entry on
  this" but you must not describe that work as a wiki finding.
- **Weak evidence is labelled weak.** An entry is one report of one setup. Say
  how strong it is: `evidence_level`, `evidence_strength`, and whether
  it is agent-written or unreviewed.
- **A scoped negative result is not "this never works".** Report `claim_scope` faithfully.
- **Relevance is your judgement.** Search is keyword-based, so a hit can be
  irrelevant and a relevant entry can use different words. Read an entry before
  citing it, and cite it only if it bears on the user's plan.
- **Experiments, not people.** Never judge authors.

## Tools

Use the `failed-experiments-wiki` MCP server: `list_facets`, `search_entries`,
`get_entry`.

If the MCP tools are not available, use the command-line twin from the
repository root (same JSON):

```
python tools/cli.py facets
python tools/cli.py search "<words>" --filter method=sae
python tools/cli.py get fe-2026-0001
```

## Steps

1. **Break the plan down** into its method, models, research area, benchmark
   and the effect the user hopes for.
2. **See what the wiki covers.** Call `list_facets` once: it shows every
   method, area, model and likely reason (`failure_type`) in use, and how many
   entries exist.
3. **Search several ways.** At least three searches: the user's own key terms;
   synonyms and neighbouring terms (e.g. "SAE", "sparse autoencoder",
   "dictionary learning"); and filters taken from `list_facets` (`method`,
   `research_area`, `models.name`). In a small wiki, also list everything with
   an empty query and scan the titles.
   - Read `score` and `matched_terms` on each hit. A hit on one common word is
     a weak match; do not treat it as relevant without reading the entry.
   - `method`, `checks_done`, `models.name` and `benchmarks` are free-text
     tags, not a fixed vocabulary. One idea can sit under several spellings
     (`sae`, `sae-probing`, `sparse-autoencoders`), so a filter on one value
     can miss entries. Never conclude "not found" from a filter alone.
4. **Read every plausible entry** with `get_entry`. Keep the ones that bear on
   the plan: same or closely related method, hypothesis or setup. Drop the rest.
5. **Answer in the format below.** If nothing relevant was found, say so in
   every section instead of stretching a loosely related entry to fit.

## Answer format

Use exactly these five headings, in this order.

```
## Already tried
- **fe-YYYY-NNNN** — one-line summary of what was tried and what happened.
  Models: … · Evidence: <evidence_level>, strength of evidence: <low|medium|high> · Badges: <agent-written, unreviewed, … or "reviewed">

## Where it went wrong
- **fe-YYYY-NNNN** — likely reason `<failure_type>`: the reasons the entry gives.

## What to avoid
- A concrete pitfall, phrased as advice for the user's plan (from fe-YYYY-NNNN).

## Worth retrying
- **fe-YYYY-NNNN** — why a better attempt is worthwhile, and the entry's revival conditions.

## Not found
- What the user's plan involves that the wiki has no entry on.
```

Rules for the sections:

- **Badges line:** when an entry's status is `reviewed`, say who reviewed it,
  from `reviewed_by`: "reviewed by a person", or "reviewed by an agent only"
  (add "the same model that wrote it" when the tool says so). An agent-only
  review is a weak check, not vetting; never write plain "reviewed" for one.
- **Already tried:** every relevant entry, strongest evidence first. If there is
  none, write "Nothing in the wiki matches this plan." An entry that is only
  adjacent (same tool or area, a different question) may be listed last,
  starting with "Adjacent only:" and saying how it differs. Entries you judged
  irrelevant from their titles go under Not found, named as "not opened".
- **Where it went wrong:** use the entry's own `failure_type` value and its
  reasons. Do not upgrade "underpowered" to "does not work".
- **What to avoid:** each pitfall traced to an entry ID. No generic advice.
- **Worth retrying:** list an entry here when `retry_welcome` is true, or
  `evidence_strength` is `low`, or `failure_type` is `underpowered`,
  `implementation_bug_suspected`, `measurement_noise` or
  `hyperparams_unexplored`. Give its `revival_conditions` if it has any. If no
  cited entry qualifies, write "None of the entries above."
- **Not found:** always present. Name the parts of the plan the wiki does not
  cover. If nothing relevant was found at all, say "The wiki has no entries on
  this. That means nobody has filed one, not that the idea is untested or
  safe to assume novel." State how many entries the wiki holds, so the user can
  judge how much "not found" means.

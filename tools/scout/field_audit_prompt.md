# Field-support audit prompt (scouting step 4, before seed selection)

Used verbatim for every audit batch. A post can seed the wiki only if it is a
genuine write-up of a failed experiment **and** the post itself supports every
required schema field. This audit checks both, post by post.

## Task

For each post, read the whole text, then answer from the text alone. Never use
outside knowledge of the paper or the authors, and never guess.

1. `genuine`: `"yes"`, `"partial"` or `"no"`.
   - `yes`: the post's main content is one or more experiments the authors ran
     whose outcome was negative (null, opposite, smaller than expected, mixed
     with a clear negative, failed replication, abandoned because it did not work).
   - `partial`: the post is mostly positive or mostly not an experiment report,
     but contains a failed sub-experiment described in real detail.
   - `no`: neither.
2. `experiments`: a short label for each distinct failed experiment in the post.
3. `primary_experiment`: the label of the one failed experiment best supported
   by the text. Answer the field questions below for that experiment only.
4. `fields`: for each of these, `supported` (true/false) and `evidence`
   (25 words or fewer, your own words, saying what the post states):
   - `hypothesis`: does the post say what the authors expected or hoped to find?
   - `claim_scope`: does it say exactly what was tested (setup, data, scale),
     so the failure cannot be read as "this never works"?
   - `method`: are the techniques named?
   - `models`: are the models named? List the names in `evidence`.
   - `result_direction`: can you pick one of `null`, `opposite`,
     `smaller_than_expected`, `mixed`, `did_not_replicate`? Put your pick in `value`.
   - `failure_type`: can you pick one of `hypothesis_false`, `underpowered`,
     `implementation_bug_ruled_out`, `implementation_bug_suspected`,
     `measurement_noise`, `hyperparams_unexplored`, `infrastructure`,
     `worked_but_abandoned`, `unknown`? Put your pick in `value`. A pick of
     `unknown` counts as supported only if the post itself says the cause is unclear.
   - `quote`: one sentence fragment of **15 words or fewer**, copied
     **character for character** from the post, that states the negative
     result. Put it in `value`. If no such fragment exists, `supported: false`.
5. `all_required_supported`: true only if every field above is supported.
6. `info_hazard`: `"none"`, or `"possible"` with a reason, if the failed
   experiment is an attack or capability attempt whose details could help misuse.
7. `notes`: anything a selector should know (20 words or fewer), e.g. "summary of
   a longer post; detail is elsewhere", "results are in images, not text".

## Output

A JSON file: `{"batch": N, "model": "...", "audits": [ {post_id, title, genuine,
genuine_reason, experiments, primary_experiment, fields: {hypothesis: {...},
claim_scope: {...}, method: {...}, models: {...}, result_direction: {...},
failure_type: {...}, quote: {...}}, all_required_supported, info_hazard, notes} ]}`

The only verbatim text allowed in the output is the `quote` value. Everything
else is in your own words.

I added the post as two entries. Both are agent-written and unreviewed, and the quote check passed on each. They are committed on local branches only, because no git remote is configured and no pull request was opened.

| ID | Branch | What it covers |
|---|---|---|
| fe-2026-0016 | `entry/fe-2026-0016` | Fixed-size Group SAEs on synthetic circles and GPT-2 layer 7. Quote: "none of our results were that compelling". |
| fe-2026-0017 | `entry/fe-2026-0017` | Learned group-space embedding. It worked on easy synthetic data but wrapped into a circle when groups co-occurred. Quote: "when the groups co-occur with some probability, the setup doesn't quite work". |

To merge them locally: `python tools/cli.py merge-local entry/fe-2026-0016` and the same for `entry/fe-2026-0017`. I did not run that.

I split it into two entries because the post describes two different experiments. Nothing in the wiki already covered it (searched on SAE, group, circles and GPT-2).

## FRICTION

- **No tool errors.** Both submissions validated on the first try, with no issues returned.
- **Branch-only result.** The skill expects a pull request, but this clone has no remote, so I could only report local branches. The merge command appeared only in the tool output, not in the skill text.
- **Judgment calls the field guide doesn't settle.**
  - `result.direction`: the first experiment was "slightly better metrics, no useful structure", which fits no value cleanly. I chose `smaller_than_expected`, and `mixed` for the second.
  - `failure_type`: the author says the results were "negative" only in the sense of "not accomplishing anything useful". I used `hypothesis_false` with `low` confidence, but `unknown` was arguably as defensible.
  - `models` for the toy-only second entry: I used `name: unknown` per the rule, which is a bit misleading for a synthetic setup.
- **Post text cut off.** The fetched text ends mid-sentence ("hard for points to “pass” each"), and some figures and GIFs are absent. I only used what was in the text.
- **Quote limitation.** The quote check is exact-match, so quotes with curly apostrophes (common on LessWrong) are risky. I chose fragments without them.
- **Unreviewed neighbours.** `contributor.handle` is `HANDLE-TBD` throughout the wiki. This is not a failure of mine, just an unfinished field.

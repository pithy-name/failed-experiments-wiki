I submitted one entry for the post, `fe-2026-0016`. It is on local branch `entry/fe-2026-0016` and is not in the wiki yet. The repo has no git remote, so no pull request was opened. To merge it: `python tools/cli.py merge-local entry/fe-2026-0016`. I haven't run that.

- **Entry:** "Group SAEs (fixed-size groups, l1/l2 penalty) on synthetic circles and GPT-2 layer 7 gave no compelling multi-dimensional features beyond normal SAEs."
- **Status:** it is agent-written and unreviewed, and the quote check passed. The quote is "none of our results were that compelling".
- **Fields I set to `unknown`:**
  - `failure_type`: the post gives no cause, only that the work "didn't accomplish anything useful".
  - the GPT-2 model's developer, version, size and access; the post only says GPT-2 layer 7.
  - the toy model's developer, version, size and access.
- **Judgment calls:**
  - `result.direction` is `smaller_than_expected`, not `null`, because some metrics improved slightly.
  - `confidence_true_negative` is `low`, so `retry_welcome` is true.
- **Not filed:**
  - **Learned group space (toy embedding table):** the post's result is that co-occurring groups wrapped into a circle. It is a different method and setup from the group SAEs, but it has no model and no stated hypothesis or quote, so I left it out.
  - **Gated and TopK group SAEs:** these were only briefly tried and are noted as limitations in the entry.
  - **Logan's circuits results and Jannik's learned-group results:** the post says it can't describe these.
- **Contributor handle:** the tool result did not show which GitHub handle was recorded. It should be your `gh` login; check `contributor.handle` in `entries/fe-2026-0016.md`.

## FRICTION

- **Missing handle:** the skill says to report `contributor.handle` from the tool's result, but `submit_entry` didn't return it. I couldn't tell you the handle without opening the file, and I didn't open it.
- **No remote:** `status: branch_only_no_remote` is documented, but the plugin instructions assume a pull request. Nothing is visible to reviewers until a manual local merge.
- **Splitting rule vs. thin sub-experiments:** the skill says to split by distinct method. The learned-group-space section is a distinct method, but the post gives it too little (no hypothesis, no quotable result) to file.
- **`models` for synthetic setups:** I used `toy model (synthetic circles in 200D)` with `unknown` fields, following the guide. The schema treats it as a model, which is a slight mismatch.
- **Tool errors:** none. Fetch, search and submit all succeeded, with `issues: []`.

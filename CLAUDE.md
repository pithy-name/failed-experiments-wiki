# CLAUDE.md

Read `README.md` first: it says what the project is, how to set it up and run it, and where things are. This file holds only what an agent maintaining the repository must not get wrong. For the scripts, see `tools/CLAUDE.md`.

## Keep these in sync

- **Form, converter and schema.** `.github/ISSUE_TEMPLATE/new-entry.yml`, `tools/issue_to_entry.py` and `schema/entry.schema.json` describe the same fields. The converter maps form **labels**, not ids, to fields, so renaming a label means updating `LABELS`. `tests/test_issue_to_entry.py` enforces the match.
- **Never offer "None" as a dropdown option:** the form vanished from GitHub until it was removed (DEC-85). The form says "no hazard"; the converter maps it back to `none`.
- **Status files describe `main` as it stands,** never an unmerged pull request.
- **ID order.** Every file with IDs lists them in ID order.
- **Generated files.** Edit the source, regenerate, and commit both. Never hand-edit the output.

| Generated file | Source | Regenerate with |
|---|---|---|
| `site/index.html` | `entries/`, `tools/build_site.py`, `tools/site_assets/` | `make site` |
| `schema/SCHEMA.md` | `schema/entry.schema.json` | `make print-pack` |
| `demo/script.md` | `demo/scenes.yaml`, `demo/build_demo.py` | `make demo-script` |
| `VERIFICATION.md` | `demo/verify.yaml`, `demo/verify.py` | `make verify` (slow: drives a browser) |

`VERIFICATION.md` also records what has been checked inside Claude Code (`make verify PLUGIN=1`).

## The No Rot Rule

- **One home per fact.** Each fact lives in one file; other files point to it instead of repeating it. For status: `DONE.md` holds status, `TODO.md` tasks, `DECISION-LOG.md` decisions, `VERIFICATION.md` checks, and `DONE.md` holds no task steps.
- **Nothing that goes stale.** No line that needs updating after the next change, such as counts, "since then" lists or test totals. Point to a fixed marker instead: a tag, a DEC ID, a task ID.
- **Nothing outside the repository.** Never point a reader to a file outside this repository: they cannot open it. Where the repository depends on one, say it is not tracked, and give no version number.

## Entries

- Never invent an entry, a number or a quote. The validator's quote check is the integrity guarantee: never weaken or skip it to make an entry pass.
- Never set `contributor` or `review` by hand; the tools set them.
- `evals/gold/` holds the eval's reference entries. Never edit one unless the maintainer asks.

## Git

- One branch per concern, named for its content. One commit per file, saying what changed and why.
- Every commit ends with two trailers, the maintainer's then the model's:
  `Co-Authored-By: pithy-name <271380525+pithy-name@users.noreply.github.com>`
  `Co-Authored-By: <model> <noreply@anthropic.com>`
- Never push or merge without the maintainer's go-ahead. The repository is public, so anything pushed is published.
- Write the test first. CI (`.github/workflows/validate.yml`) runs the validator and the whole test suite on every pull request, so a check that real data can legitimately fail will block contributions.

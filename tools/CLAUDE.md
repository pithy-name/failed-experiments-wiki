# tools/

What each script is for, and what to know before changing it. This is the one
place scripts are described; a script's docstring is the full account. Run any
script with `.venv/bin/python tools/<script>`.

## Scripts

| Script | Purpose | Know this before changing it |
|---|---|---|
| `build_db.py` | Builds `wiki.db`, the SQLite database Datasette serves (`make datasette`). | Its output is generated: rebuild after any entry change (root `CLAUDE.md`). |
| `build_site.py` | Builds `site/index.html`, the static browse page (`make site`). | Its output is generated: rebuild after any entry change (root `CLAUDE.md`). |
| `check_facts.py` | Checks that an entry's numbers and model names appear in its source post (`make check-facts`). | A review aid, not a gate: it always exits 0. |
| `cli.py` | Command-line twin of the MCP tools: search, get, facets, submit, review. | |
| `datasette_check.py` | Checks the Datasette database without opening a port (`make datasette-check`). | |
| `form_link.py` | Turns an AI draft into a pre-filled issue-form link for a person to check and submit. | |
| `issue_to_entry.py` | Turns a submitted issue form into an entry. | Runs inside the GitHub workflow. Keep it in sync with the form (root `CLAUDE.md`). |
| `lw.py` | Polite LessWrong reader: every response is cached and requests are paused. | Never bypass the cache or the pauses. |
| `make_print_pack.py` | Builds the printable review pack in `_print/` and `schema/SCHEMA.md` (`make print-pack`). | |
| `mcp_smoke.py` | Starts the MCP server and calls its tools once (`make mcp-smoke`). | |
| `method_report.py` | Lists write-in methods the form's Method dropdown lacks (`make method-report`). | |
| `post_markdown.py` | Turns a post's HTML into Markdown for the print pack. | Used by `make_print_pack.py`. |
| `scout/` | The corpus-scouting scripts and the classifier and field-audit prompts. | Their outputs go to `scouting/`. |
| `set_handle.py` | Replaces the placeholder handle on entries with the maintainer's GitHub login (`make set-handle`). | |
| `sync_gold.py` | Publishes verified gold entries into `entries/` (`make sync-gold`). | Refuses an unverified gold entry labelled as a person's. That guard is deliberate. |
| `validate.py` | The one validator (`make validate`): the command line, the MCP server, the issue-form converter and CI all call it. | A rule added here applies everywhere at once. |
| `wikilib.py` | Core library: read, search, facets, validate, submit, review. | Every other script imports it. Change behaviour here, never in a copy. |

## New scripts

- The docstring says what the script does, how to run it, and a `Reusability:` line (GENERIC, PROJECT-INTERNAL or ONE-OFF). Most older scripts lack that line; add it when you touch one.
- Find repository paths relative to the script. No personal paths.
- Tests in `tests/` come first.

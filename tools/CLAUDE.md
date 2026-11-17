# tools/

The README's repository table says what the main scripts are for. This file adds what a maintainer needs to know before changing them. Run any script with `.venv/bin/python tools/<script>`.

## Before changing a script

| Script | Know this |
|---|---|
| `wikilib.py` | Every other script imports it. Change behaviour here, never in a copy. |
| `validate.py` | The one validator: the command line, the MCP server, the issue-form converter and CI all call it. A rule added here applies everywhere at once. |
| `lw.py` | Caches every response and pauses between requests. Never bypass either. |
| `issue_to_entry.py` | Runs inside the GitHub workflow. Keep it in sync with the form (root `CLAUDE.md`). |
| `sync_gold.py` | Refuses an unverified gold entry labelled as a person's. That guard is deliberate. |
| `check_facts.py` | A review aid, not a gate: it always exits 0. |
| `build_site.py`, `build_db.py` | Their outputs are generated; rebuild after any entry change (root `CLAUDE.md`). |

## Scripts the README does not list

| Script | What it does |
|---|---|
| `form_link.py` | Turns an AI-drafted entry into a pre-filled issue-form link for a person to edit and submit. |
| `method_report.py` | Lists write-in methods the form's Method dropdown lacks. |
| `set_handle.py` | Replaces the placeholder handle on entries with the maintainer's GitHub login. |
| `datasette_check.py` | Checks the Datasette database without opening a port. |
| `mcp_smoke.py` | Starts the MCP server and calls its tools once. |
| `make_print_pack.py`, `post_markdown.py` | Build the printable review pack and `schema/SCHEMA.md`. |

`scout/` holds the corpus-scouting scripts and the classifier and field-audit prompts; their outputs go to `scouting/`.

## New scripts

- The docstring says what the script does, how to run it, and a `Reusability:` line (GENERIC, PROJECT-INTERNAL or ONE-OFF). Most older scripts lack that line; add it when you touch one.
- Find repository paths relative to the script. No personal paths.
- Tests in `tests/` come first.

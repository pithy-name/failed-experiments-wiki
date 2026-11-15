$ claude --plugin-dir plugin -p "List the exact names of every MCP tool you have whose name contains failed-experiments-wiki, one per line. Then call the search_entries tool with query steganography and list the entry IDs it returns with each entry's badges, and say how many entries the wiki holds."

mcp__plugin_failed-experiments-wiki_failed-experiments-wiki__fetch_source
mcp__plugin_failed-experiments-wiki_failed-experiments-wiki__get_entry
mcp__plugin_failed-experiments-wiki_failed-experiments-wiki__list_facets
mcp__plugin_failed-experiments-wiki_failed-experiments-wiki__review_entry
mcp__plugin_failed-experiments-wiki_failed-experiments-wiki__search_entries
mcp__plugin_failed-experiments-wiki_failed-experiments-wiki__submit_entry

`search_entries` with the query "steganography" returned 2 matches:

| Entry ID | Title | Badges |
|---|---|---|
| fe-2026-0011 | Iterated fine-tuning of GPT-3.5-Turbo through the OpenAI API did not hide a 1-bit user-age signal in completions that a classifier could read | agent-written, unreviewed, retry-welcome |
| fe-2026-0010 | PPO with LoRA on GPT2-large did not learn hidden 1-bit communication in IMDB review completions (decoder accuracy never above 50%) | agent-written, unreviewed, retry-welcome |

Both entries are unreviewed and agent-written, so I haven't checked them against their source.

The wiki holds 15 entries (`total_entries_in_wiki` in the search response).

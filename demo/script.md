# Failed-experiments wiki demo: narration script

Generated from `demo/scenes.yaml` by `demo/build_demo.py`. Edit the YAML, not this file, then run `make demo-script`.

## How to read this

- **Narration** is written for you to read aloud, in your voice. Change any of it in `demo/scenes.yaml`.
- **On screen** is what the draft video shows for that scene: the real page driven by real clicks, a real file, or real command output.
- **Update when** flags lines that are true today and will need changing as the project moves.
- Timings are estimated at 150 words a minute, plus 0.9 s of pause per scene.
- Narration length: 891 words.

## What the draft video is, and is not

- `demo/out/demo-draft.mp4` (1920×1080), with subtitles in `demo/out/demo-draft.srt`. Build it with `make demo-video`.
- A headless browser is driven through the real browse page with real clicks, typing and scrolling. A frame is captured after every step and the frames are joined into a video.
- It is not a capture of a person's screen. The orange pointer ring and the outline around a field are drawn by the recorder, and motion is step by step, not continuous.
- The caption bar shows the narration. A voice, when present, is macOS text-to-speech: a scratch track for pacing. Record your own over it (`--no-captions` gives a clean picture), or re-record live with `demo/live-demo-script.md`.
- It shows no GitHub screens and no Claude Code session, because neither exists yet for this project: there is no remote, and the plugin has not been loaded. Scenes 7 to 10 and 12 show the local equivalent, and the narration says so where it matters.

## Scenes

### 1. `s01-title` · 0:00–0:23 (23 s)

**On screen:** Title card: A wiki of failed AI-safety experiments

**Narration:**

> AI-safety researchers have no shared place to see what others already tried, and where it failed. Failed experiments stay in file drawers or scattered posts, so people repeat dead ends. This is a proof of concept of a fix: a wiki of failed experiments that people and AI agents can both write to, and both read.

### 2. `s02-idea` · 0:23–0:56 (33 s)

**On screen:** Title card: Three ideas

**Narration:**

> Three ideas shape it. First, blameless: entries describe experiments, never the people who ran them. Second, trust is visible: every entry shows who wrote it, a person or an agent and which model, what evidence it rests on, and whether anyone has reviewed it. Third, a failure is scoped. One thin report should not steer the field away from a good idea, so each entry says exactly what was tested, and how confident we can be that it really doesn't work.

### 3. `s03-browse` · 0:56–1:17 (21 s)

**On screen:** The browse page in a headless browser: scroll down 420 px; scroll to `fe-2026-0006`; scroll back to the top.

**Narration:**

> This is the wiki as a single web page, built from Markdown files. Fifteen entries so far, all taken from real LessWrong and Alignment Forum posts. Each card carries badges: agent-written, unreviewed, retry welcome. The first five carry a note saying they are model drafts that I still have to verify.

**Update when:** The last sentence goes once the gold entries are verified. The count changes if entries are added.

### 4. `s04-filter` · 1:17–1:31 (14 s)

**On screen:** The browse page in a headless browser: tick **failure type → hyperparams_unexplored**; untick **failure type → hyperparams_unexplored**; tick **badges → agent-written**; tick **failure type → hypothesis_false**; click **Clear all filters**; type `steganography` in the search box.

**Narration:**

> Every field is a filter. Here are the failures where the hyperparameters were never properly explored. Here, entries an agent wrote where the hypothesis itself looks false. And full-text search across every field.

### 5. `s05-entry` · 1:31–2:04 (33 s)

**On screen:** The browse page in a headless browser, starting from the link `#q=steganography`: open **All fields** on `fe-2026-0010`; scroll to **quote** and outline it; scroll to **claim scope** and outline it; scroll to **confidence true negative** and outline it; scroll to **retry welcome** and outline it; scroll to **limitations** and outline it.

**Narration:**

> Open one. It links the original post, and carries a short quote that a validator found, word for word, in that post. Claim scope says exactly what was tested: one setup, one small model, two hundred training steps. Confidence that this is a true negative: low. Retry welcome: yes. That matters: the entry records the author's own view that a better setup would very likely succeed. So it warns you about a pitfall, without telling you the idea is dead.

### 6. `s06-file` · 2:04–2:20 (16 s)

**On screen:** File `entries/fe-2026-0005.md`, lines 1–28

**Narration:**

> Underneath, an entry is one Markdown file with structured fields. It is readable on GitHub as it is, and every change to it goes through git, so the history of what was agreed, and why, is kept.

### 7. `s07-ask` · 2:20–2:46 (26 s)

**On screen:** Terminal, real output of: `python tools/cli.py search "steer evaluation awareness direction to stop sandbagging" --brief --limit 3`; `python tools/mcp_smoke.py 2>/dev/null | grep -E '^(tools|search_entries|list_facets)'`

**Narration:**

> Now the question this is for. Say I am planning an experiment: steer a model along a direction for "it thinks it is being evaluated", to stop it sandbagging. What has been tried? Agents reach the wiki through a local MCP server, with search, get and facet tools. The same tools are on the command line, and the right entry ranks first.

### 8. `s08-answer` · 2:46–3:09 (24 s)

**On screen:** File `demo/answers/steering.md`, lines 1–6, then 8–15, then 17–19

**Narration:**

> And this is what the ask skill wrote for that plan. Five parts, always the same: already tried, where it went wrong, what to avoid, worth retrying, and not found. Every claim cites an entry ID. It says how weak the evidence is, a single unreviewed report with low confidence, and what a better attempt would need.

**Note:** The answer on screen was written by the ask skill for this demo on 2026-11-15, against the 15-entry wiki. It is not one of the eval answers (those were written when the wiki held 10 entries) and no judge has scored it; the orchestrator read it against the entry it cites.

### 9. `s09-notfound` · 3:09–3:28 (18 s)

**On screen:** File `demo/answers/debate.md`, lines 1–16

**Narration:**

> Ask about something the wiki does not cover, here debate with human judges, and it says so plainly: nothing matches, and that means nobody has filed an entry, not that the idea is untested. It does not fill the gap from its own memory.

**Note:** Written by the ask skill for this demo on 2026-11-15, against the 15-entry wiki. Not one of the eval answers.

### 10. `s10-contribute` · 3:28–3:48 (20 s)

**On screen:** Terminal, real output of: `git log --graph --format='%h %s' --grep='fe-2026-001[2-5]' | cut -c1-112`

**Narration:**

> Agents also write. The contribute skill reads a post, drafts one entry for each failed experiment, and submits it. Each submission lands on its own branch, and merges only if validation passes. The agent cannot set its own trust fields: the system stamps the entry as agent-written and unreviewed.

**Update when:** With a GitHub remote, show the pull request instead of the local branch graph.

### 11. `s11-validate` · 3:48–4:12 (23 s)

**On screen:** Terminal, real output of: `sed 's/^failure_type: .*/failure_type: bad_luck/' entries/fe-2026-0008.md > $TMP/fe-2026-0008.md`; `python tools/validate.py $TMP/fe-2026-0008.md --quotes cached`; `python tools/validate.py --quotes cached`

**Narration:**

> One validator guards every path. Here I change a failure type to a value that is not on the list, and it refuses. It also fetches the post and checks that the quote is really there. During seeding it rejected two of the agent's own drafts for a wrong field type. They were fixed and resubmitted.

### 12. `s12-human` · 4:12–4:31 (19 s)

**On screen:** File `.github/ISSUE_TEMPLATE/new-entry.yml`, lines 1–26

**Narration:**

> People contribute with a GitHub issue form. No git needed. A workflow turns the form into an entry and a pull request, marked as written by a person. The form and the workflow are built and tested locally. They have not run on GitHub yet.

**Update when:** Drop the last two sentences, and show the real issue and pull request, once the workflow has run on GitHub.

### 13. `s13-review` · 4:31–4:53 (22 s)

**On screen:** Terminal, real output of: `git log --date=short --format='%h %ad %s' --grep='Review fe-2026-0007' | cut -c1-112`; `grep -A7 '^review:' entries/fe-2026-0007.md | cut -c1-112`

**Narration:**

> Review is a separate step. A person or an agent checks an entry against its post and records the outcome: who reviewed, when, and what they checked. This one was reviewed by an agent, the same model that wrote it. The record says so, and the page labels it "reviewed by an agent only".

**Update when:** Add your own human review here once it is done.

### 14. `s14-datasette` · 4:53–5:02 (8 s)

**On screen:** Terminal, real output of: `python tools/datasette_check.py | cut -c1-112 | head -22`

**Narration:**

> For people who want SQL and JSON, the same entries load into Datasette, with a facet on every field.

### 15. `s15-evals` · 5:02–5:27 (25 s)

**On screen:** Terminal, real output of: `cp -R evals/results $TMP/results && python evals/run_evals.py --results $TMP/results`; `grep -E 'Field|failure_type|retry_welcome|method|checks_done|hypothesis|claim_scope|limitations' $TMP/results/RESULTS.md | head -8 | cut -c1-80`

**Narration:**

> The skills are evaluated with one command. The contribute skill's drafts are compared, field by field, with five reference entries: seventy-eight percent agreement overall. The ask skill passed six of seven questions. These numbers are provisional. The reference entries are still model drafts that I have to verify, and five posts with one model vendor is a spot-check, not a benchmark.

**Update when:** Re-run after the gold entries are verified, and say the new numbers. Drop 'provisional' only then.

### 16. `s16-finding` · 5:27–5:53 (26 s)

**On screen:** Title card: A finding from building it

**Narration:**

> Building it produced a finding. From two hundred and twelve candidate posts, classifiers found forty-nine genuine write-ups of failed experiments. Only nine stated enough to fill a structured entry. What was missing most often: what the authors expected, and exactly what they tested. Those are the same two things a reader needs, to avoid reading a failure report as "this never works".

### 17. `s17-close` · 5:53–6:11 (18 s)

**On screen:** Title card: Next

**Narration:**

> Next steps are a public site, a hosted server so agents can connect without cloning the repository, and asking authors to confirm their entries or opt out. The aim is simple: each experiment can be less wrong than the one before it. Thank you.

**Total: 6:11** (372 s).

## Numbers the narration states

The build checks these against the repository and stops if one is out of date.

| Fact | Value |
|---|---|
| entries | 15 |
| posts_classified | 212 |
| genuine_writeups | 49 |
| full_field_posts | 9 |
| contribute_accuracy_percent | 78 |
| ask_passed | 6 |
| ask_total | 7 |
| gold_verified | 0 |
| has_github_remote | False |

## The live-recording variant

Once the repository is on GitHub and the plugin loads in Claude Code, these scenes are better recorded live (`demo/live-demo-script.md` has the shorter script):

| Scene | Record instead |
|---|---|
| 7–9 (ask) | A Claude Code session with the plugin: type the plan from scene 7, show the five-part answer; then the debate question from scene 9. |
| 10 (contribute) | Same session: "Contribute this post: <a LessWrong URL not yet in the wiki>". Show the pull request it opens, with the badges. |
| 11 (validate) | The failed check on that pull request, or the same terminal commands. |
| 12 (human path) | GitHub → Issues → New entry: submit the form, show the pull request the workflow opens. |
| 13 (review) | Run the human review command live (see `TODO.md`, T4), then `git log --oneline --grep Review`. |
| 14 (Datasette) | `make datasette`, then the entries table with its facets in a browser. |

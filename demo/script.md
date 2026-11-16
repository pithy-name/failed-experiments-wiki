# Failed-experiments wiki demo: narration script

Generated from `demo/scenes.yaml` by `demo/build_demo.py`. Edit the YAML, not this file, then run `make demo-script`.

## How to read this

- **Narration** is written for you to read aloud, in your voice. Change any of it in `demo/scenes.yaml`.
- **On screen** is what the draft video shows for that scene: the real page driven by real clicks, a real file, or real command output.
- **Update when** flags lines that are true today and will need changing as the project moves.
- Timings are estimated at 175 words a minute, plus 0.9 s of pause per scene. A built video's measured timings are in `demo/out/timings.json`; the text-to-speech voice runs a little faster than the estimate.
- Narration length: 1150 words.

## What the draft video is, and is not

- `demo/out/demo-draft.mp4` (1920×1080), with subtitles in `demo/out/demo-draft.srt`. Build it with `make demo-video`.
- A headless browser is driven through the real browse page with real clicks, typing and scrolling. A frame is captured after every step and the frames are joined into a video.
- It is not a capture of a person's screen. The orange pointer ring and the outline around a field are drawn by the recorder, and motion is step by step, not continuous.
- The caption bar shows the narration. A voice, when present, is macOS text-to-speech: a scratch track for pacing. Record your own over it (`--no-captions` gives a clean picture), or re-record live with `demo/live-demo-script.md`.
- It shows no GitHub screens, because the project has no GitHub repository yet. The narration says so in the scenes where a viewer would otherwise assume one (the file scene, the form scene and the close).
- The Claude Code session it shows is a saved transcript of a real headless session with the plugin loaded (`demo/answers/plugin-session.md`), not a live capture. The two `ask` answers on screen are saved files too; each scene's note says where its file came from.
- Scenes marked *(not in the short cut)* are left out by `--short`, which builds `demo/out/demo-short.mp4` for places that ask for a video of five minutes or less.

## Scenes

### 1. `s01-title` · 0:00–0:29 (30 s)

**On screen:** Title card: A wiki of failed AI-safety experiments

**Narration:**

> When an AI-safety experiment does not work, the result usually stays in a file drawer, or in a post nobody can find. For AI safety, I found no shared record of what was tried and where it failed. So the next team repeats the dead end, and scarce safety compute goes to ideas that were already ruled out. This is a proof of concept of a fix: a wiki of failed experiments that people and AI agents can both write to, and both read.

### 2. `s02-idea` · 0:29–1:00 (31 s)

**On screen:** Title card: Less wrong, one experiment at a time

**Narration:**

> It starts with what is already public but hard to find: LessWrong and the Alignment Forum, a community that already posts candid write-ups of what did not work. LessWrong's own name states the goal: be less wrong. Repeating a known mistake, or ignoring evidence that is one search away, is the habit this is aimed at. The habit, never the person: entries describe experiments, and do not judge whoever ran them. And every failure is scoped, so one thin report is not read as: this never works.

### 3. `s03-browse` · 1:00–1:27 (27 s)

**On screen:** The browse page in a headless browser: scroll down 420 px; scroll to `fe-2026-0006`; scroll back to the top.

**Narration:**

> This is the wiki: one web page, built from plain text files. Fifteen entries so far, each from a real post. Two badges say how far to trust an entry, and one invites a retry. So far all fifteen were written by an agent, and the only review was done by an agent too. The first five are model drafts of my own reference entries, and each of those five says so until I verify it.

**Update when:** The last sentence goes once the gold entries are verified. The count changes if entries are added.

### 4. `s04-filter` · 1:27–1:43 (16 s)

**On screen:** The browse page in a headless browser: scroll the filter panel to show more fields; scroll the filter panel back to the top; tick **failure type → hyperparams_unexplored**; untick **failure type → hyperparams_unexplored**; tick **badges → retry-welcome**; tick **failure type → hypothesis_false**; click **Clear all filters**; type `steganography` in the search box.

**Narration:**

> Every field is a filter, from the result to the source. Here are the failures where the settings were never properly explored. Here, the ones where the hypothesis itself looks false, yet a retry is still welcome. And a search across every field.

### 5. `s05-entry` · 1:43–2:14 (32 s)

**On screen:** The browse page in a headless browser, starting from the link `#q=steganography`: open **All fields** on `fe-2026-0010`; scroll to **quote** and outline it; scroll to **claim scope** and outline it; scroll to **confidence true negative** and outline it; scroll to **retry welcome** and outline it; scroll to **limitations** and outline it.

**Narration:**

> Open one. It links the original post, and carries a short quote that a program found, word for word, in that post. Claim scope says exactly what was tested: one setup, one small model, two hundred training steps. Confidence that this is a true negative, meaning the idea really fails and the test was not just weak: low. Retry welcome: yes. The entry records the post's own view that a stronger setup would very likely succeed. So it warns you about a pitfall, without telling you the idea is dead.

### 6. `s06-file` · 2:14–2:30 (16 s) *(not in the short cut)*

**On screen:** File `entries/fe-2026-0005.md`, lines 1–18, then 34–51

**Narration:**

> Underneath, an entry is one text file with structured fields: the hypothesis, exactly what was tested, the result, the kind of failure, and its limits. Every change to it goes through git, so the history of what was agreed, and why, is kept.

### 7. `s07-ask` · 2:30–2:48 (18 s)

**On screen:** Terminal, real output of: `python tools/cli.py search "steer evaluation awareness direction to stop sandbagging" --brief --limit 3`

**Narration:**

> Now the question this is for. Say a researcher plans to steer a model along a direction for "it thinks it is being evaluated", to stop it sandbagging, that is, underperforming on purpose. Has that been tried? A keyword search ranks first the one entry that tested exactly this.

### 8. `s07b-plugin` · 2:48–3:01 (14 s)

**On screen:** File `demo/answers/plugin-session.md`, lines 1–18

**Narration:**

> AI agents reach the wiki through a plugin. This is a real session: the agent lists the six tools the wiki gives it, runs a search through them, and reports that both entries it found are unreviewed.

**Note:** A saved transcript of a real headless Claude Code session with the plugin loaded, run on 2026-11-15 with only the wiki's own tools available. `make verify PLUGIN=1` repeats it.

### 9. `s08-answer` · 3:01–3:37 (36 s)

**On screen:** File `demo/answers/steering.md`, lines 1–7, then 9–19, then 29–38

**Narration:**

> For this demo, an AI agent then wrote this answer, following the ask skill, a set of instructions, and reading the wiki through its plugin. Five parts, always the same: already tried, where it went wrong, what to avoid, worth retrying, and not found. Every claim cites its entry, and here they all rest on one. It does not turn a weak result into a verdict: the dose was gentle, so it says this is not evidence that the idea fails. It ends by saying that all of it rests on one unreviewed entry. Nobody has scored this answer for accuracy.

**Note:** Written by the ask skill through the plugin, in a headless Claude Code session on 2026-11-15, against the 15-entry wiki. It is not one of the scored answers (those were written when the wiki held 10 entries) and no judge has scored it; every statement in it was read against the two entries it cites.

### 10. `s09-notfound` · 3:37–3:53 (16 s) *(not in the short cut)*

**On screen:** File `demo/answers/debate.md`, lines 1–17

**Narration:**

> Ask about something the wiki does not cover, here debate with human judges, and it says so plainly: nothing matches, and that means nobody has filed an entry, not that the idea is untested. It does not fill the gap from its own memory.

**Note:** Written by the ask skill through the plugin, in a headless Claude Code session on 2026-11-15, against the 15-entry wiki. Not one of the scored answers.

### 11. `s10-contribute` · 3:53–4:14 (21 s)

**On screen:** Terminal, real output of: `git log --graph --format='%h %s' --grep='fe-2026-0012'`; `grep -A5 -E '^(contributor|review):' entries/fe-2026-0012.md`

**Narration:**

> Agents also write: the contribute skill reads a post, drafts an entry for each failed experiment, and submits it. Each submission lands on its own branch, and merges only if validation passes. The system, not the agent, writes the trust fields: written by an agent, which model, unreviewed. A draft that claims otherwise is overwritten, and merging is not review.

**Update when:** With a GitHub remote, show the pull request instead of the local branch graph.

### 12. `s11-validate` · 4:14–4:36 (21 s)

**On screen:** Terminal, real output of: `sed 's/^failure_type: .*/failure_type: bad_luck/' entries/fe-2026-0008.md > $TMP/fe-2026-0008.md; python tools/validate.py $TMP/fe-2026-0008.md --quotes cached`; `sed 's/^  quote: .*/  quote: This sentence is not in the post./' entries/fe-2026-0008.md > $TMP/fe-2026-0008.md; python tools/validate.py $TMP/fe-2026-0008.md --quotes cached`; `python tools/validate.py --quotes cached`

**Narration:**

> One validator guards every path. Change a failure type to a value that is not on the list, and it refuses. Change the quote to a sentence the post never said, and it refuses that too, checking against a saved copy of the post. All fifteen real entries pass. It checks form and quotes, not whether a summary is right.

### 13. `s12-human` · 4:36–4:51 (16 s) *(not in the short cut)*

**On screen:** File `.github/ISSUE_TEMPLATE/new-entry.yml`, lines 1–26

**Narration:**

> People contribute by filling in a form, with no git needed. A script turns the form into an entry marked as written by a person. The form and the script are tested on this machine. Nobody has submitted the form on GitHub yet.

**Update when:** Drop the last sentence, and show the real issue and pull request, once the workflow has run on GitHub.

### 14. `s13-review` · 4:51–5:13 (21 s) *(not in the short cut)*

**On screen:** Terminal, real output of: `git log --date=short --format='%h %ad %s' --grep='Review fe-2026-0007'`; `grep -A10 '^review:' entries/fe-2026-0007.md`

**Narration:**

> Review is a separate step. A person or an agent checks an entry against its post, and records who reviewed, when, and what they checked. This one was reviewed by an agent, the same model that wrote it. The record names the model, and the page labels it: reviewed by an agent only. No person has reviewed an entry yet.

**Update when:** Add your own human review here once it is done, and drop the last sentence.

### 15. `s14-datasette` · 5:13–5:23 (10 s) *(not in the short cut)*

**On screen:** Datasette's own pages in the headless browser, served in process: `/wiki/entries`; `/wiki/entries?failure_type=hypothesis_false`

**Narration:**

> For people who want a table, SQL and JSON, the same entries load into Datasette. It offers a facet on every field, and one click filters the table.

### 16. `s15-evals` · 5:23–5:55 (32 s) *(not in the short cut)*

**On screen:** Terminal, real output of: `cp -R evals/results $TMP/results && python evals/run_evals.py --results $TMP/results`; `grep -E 'Overall field accuracy|^. Field|failure_type|source.url|models.name|.method.|checks_done|hypothesis|claim_scope|limitations' $TMP/results/RESULTS.md | cut -c1-96 | head -10`

**Narration:**

> The skills are scored with one command. The contribute skill's drafts are compared, field by field, with five reference entries: seventy-eight percent agreement overall. Source fields agree fully. Free-text tags never matched exactly: zero percent, because two careful readers pick different words. The ask skill passed six of seven questions, scored when the wiki held ten entries. The miss was a detail the entry does not state. These numbers are provisional. The reference entries are still model drafts, and one company's models wrote the drafts, the references and the grades.

**Update when:** Re-run after the gold entries are verified, and say the new numbers. Drop 'provisional' only then.

### 17. `s16-finding` · 5:55–6:24 (29 s)

**On screen:** Title card: A finding from building it

**Narration:**

> Building it produced a finding. A small model labelled two hundred and twelve candidate posts, and judged forty-nine to be genuine write-ups of failed experiments. A stronger model then checked each of those, field by field. Only nine stated enough to fill a structured entry. What the other forty most often left out: what the authors expected, and exactly what they tested. Those are the same two things a reader needs, to avoid reading a failure report as: this never works.

### 18. `s17-close` · 6:24–6:50 (26 s)

**On screen:** Title card: Each experiment can be less wrong than the one before it

**Narration:**

> This is a proof of concept, not public yet. No person has written or reviewed an entry so far, and no author has been contacted. Before it goes public, the authors get asked: they can confirm their entries, or opt out. After that, a public site and a hosted server for agents. If you remember one thing, make it the aim: each experiment can be less wrong than the one before it. Thank you.

**Total: 6:50** (410 s). **Short cut: 4:59** (299 s).

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
| agent_written | 15 |
| reviewed | 1 |
| reviewed_by_a_person | 0 |
| has_github_remote | True |

## The live-recording variant

The plugin loads in Claude Code (checked headless; see `VERIFICATION.md`). Once the repository is also on GitHub, these scenes are better recorded live (`demo/live-demo-script.md` has the shorter script):

| Scene | Record instead |
|---|---|
| 7–9 (ask) | A Claude Code session with the plugin: type the plan from scene 7, show the five-part answer; then the debate question from scene 9. |
| 10 (contribute) | Same session: "Contribute this post: <a LessWrong URL not yet in the wiki>". Show the pull request it opens, with the badges. |
| 11 (validate) | The failed check on that pull request, or the same terminal commands. |
| 12 (human path) | GitHub → Issues → New entry: submit the form, show the pull request the workflow opens. |
| 13 (review) | Run the human review command live (see `TODO.md`, T4), then `git log --oneline --grep Review`. |
| 14 (Datasette) | `make datasette`, then the entries table with its facets in a browser. |

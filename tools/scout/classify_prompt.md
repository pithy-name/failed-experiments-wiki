# Classifier prompt (scouting step 2)

Used verbatim for every classification batch. Kept here so the yields in
`scouting/yields.md` can be reproduced.

## Task

For each post, decide whether it is a **genuine write-up of a failed experiment
in AI safety**. Read the whole post text before deciding.

Label **yes** only when all of these hold:

1. The post reports at least one **empirical experiment or research project the
   authors actually ran** (or a replication attempt of someone else's result):
   code was run, models were trained or evaluated, data was collected.
2. The topic is **AI or machine learning with safety relevance**
   (interpretability, steering, evals, control, oversight, robustness, honesty,
   alignment training, agents and similar).
3. The **outcome was a failure in the research sense**: a null result, the
   opposite of what was expected, a much smaller effect than expected, a failed
   replication, or a project abandoned because the approach did not work.
4. The post gives **enough detail to say what was tried and what happened**.

Label **no** for everything else, including:

- essays, opinion, forecasts, strategy or theory with no experiment the authors ran;
- retrospectives about an organization, programme, career, fundraising or event;
- lessons-learned or advice posts that describe no specific failed experiment;
- posts whose main result is positive, even if they list limitations;
- link posts or announcements with no experimental detail;
- posts that are not about AI.

When a post is mostly positive but contains a clearly reported failed
sub-experiment with its own detail, label **yes** and say so in the reason.

## Output

One object per post:

- `post_id`: as given
- `label`: `"yes"` or `"no"`
- `reason`: one line, 25 words or fewer, in your own words
- `detail`: for `yes` only, how much experimental detail the post gives:
  `"high"`, `"medium"` or `"low"`

Do not quote the post. Do not guess: if the text does not let you decide,
label `no` and give `reason: "cannot tell from text: …"`.

# CLAUDE.md — sposcaske-bot (v1.05: picks topics, writes, shoots, uploads on a schedule; LIVE)

Owner: Andrii (writes in Ukrainian; wants short, army-style answers: task → direct solution, the best free option,
no fluff). Reply in Ukrainian.

State (2026-11-14): the whole chain exists (topics -> script -> video -> upload on a schedule). Dry runs put the video
on the `preview` branch, every run puts its log on `logs`. Missing: thumbnails, stats and learning (`docs/BUILD_PROMPT.md` §6.10).

Pipeline: `topics.py` (find and judge topics 1-10, `docs/TOPICS.md`) -> `writer.py` (topic + the judge's angle ->
`scripts/<id>.json`, Gemini; the secret GEMINI_API_KEY is set) -> `director.py` (script ->
story: camera, red word, card, portrait by the maket) -> `sources.py` (pictures, licences) -> `render.py` -> `bot.py`
conformance. What the genre is and what all references share: `docs/GENRE.md`.

ANDRII'S LIST: `docs/tasks.md` (in Ukrainian: the schedule, the decisions waiting for his yes, the to-do list with
P1-P3, the channel keywords). Keep it current and show it to him (SendUserFile, display render) after every change.

Read before any work: `docs/BUILD_PROMPT.md` (the plan and the hard rules; §13 = the second pass), `docs/FORMAT.md`
(§16–§17 win over earlier sections; §17.2 = the picture–word rule, enforced by `render.py`) + `format.json`, `docs/WRITER_PROMPT.md` (scripts are a fixed form of 13 slots,
gated by `tools/script_check.py`). Change a number only with a new measurement.

## Live
**v1.08** on `main` (Nov 14 2026: videos are made a day ahead (27-30 h) and wait private with their publish minute; v1.07 = schedule_video; v1.06 = the first public video (Daniel, 02:00 London), manual publish minute; v1.05 = THE SCHEDULE IS ON since Andrii's yes; v1.04 = channel connected, upload + schedule built; v1.03 = topics
judged 1-10; v1.02 = writer + director + finder; v1.01 = the first dry run; v1.00 = the approved maket).
Next: **v1.09**.

## Channel and schedule
Channel: **sposcaske** (@sposcaske, id UCNamDfqgZhL8JOaAiCNY_ww). Schedule (the source of truth = `gate.py` SLOTS;
Andrii, Nov 14): every day **15:00 and 02:00 London**. THE SWITCH: `data/config.json` `"live"` is **true since Nov 14** (false = the
scheduled runs do nothing; true = they write, make and upload (private, public at the slot through publishAt)).
Never switch it, and never change the slots, without Andrii's yes. History: `docs/versions.md`.

## Versions (the system of the warehouse ww2-bot, Andrii, Nov 13)
- Every change of the bot (code, `format.json`, workflow, schedule, the look or the sound of a video, the writer
  prompt) = the next version, +0.01 (after v1.99 comes v2.00). One push = one version, however many commits.
- Each version is logged in `docs/versions.md`, newest first: what changed, the numbers, why, Andrii's words.
- Each pushed version is also saved to its own branch `sposcaske-vX.YY`. On GitHub keep only every 25th (v1.00,
  v1.25, v1.50, v1.75, v2.00 ...) plus every branch since the last 25-mark; when a new 25-mark is pushed, ask Andrii
  to save the in-between ones locally, then delete them from GitHub.
- The commit of a version starts with `vX.YY: `; a line of code changed for a reason carries `# vX.YY` and the reason.
- Changes that do not touch the bot (docs, stories, this file) go to `main` with no number.
- Production branch = `main`. Ask before pushing a version. Update the "Live" lines above at every push.
- NOT switched on yet: the 10-day `draft` branch of ww2-bot. It makes sense only when videos are going out; ask
  Andrii when the first real video is scheduled.

Hard rules (short): free tools only · public-domain art only · every fact has a source in the story file · never
copy the reference channel's wording or name · never publish, change the schedule, the voice or the look without
Andrii's yes · never delete or re-upload a published video · `ww2-bot` is a read-only warehouse.

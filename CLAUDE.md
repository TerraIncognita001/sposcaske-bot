# CLAUDE.md — sposcaske-bot (v1.11: picks topics, writes, shoots, uploads on a schedule, counts and learns; LIVE)

Owner: Andrii (writes in Ukrainian; wants short, army-style answers: task → direct solution, the best free option,
no fluff). Reply in Ukrainian.

State (2026-11-14): the whole chain exists (topics -> script -> video -> upload on a schedule). Dry runs put the video
on the `preview` branch, every run puts its log on `logs`. Missing: thumbnails, the picture safety check.

Pipeline: `topics.py` (find and judge topics 1-10, `docs/TOPICS.md`) -> the script `scripts/<id>.json` (v1.09: THE
NIGHT WRITER = a Claude cloud routine, rules in `docs/NIGHT_WRITER.md`, tools in `tools/night_writer.py`; `writer.py`
with Gemini only for a topic that has no ready script or whose ready script failed) -> `director.py` (script ->
story: camera, red word, card, portrait by the maket) -> `sources.py` (pictures, licences) -> `render.py` -> `bot.py`
conformance. What the genre is and what all references share: `docs/GENRE.md`.
After the videos (v1.09, every scheduled run, no Gemini): `stats_now.py` -> `data/stats.json` (views, stayed, average
% viewed, shares, the retention curve and the caption line viewers left at) -> `learn.py` -> `data/learn.json`
(multipliers of hook frame, closer, theme ...; the judge's six marks re-weighted on our numbers; it switches ON by
itself at 8 videos public for 3 days, before that the bot ignores it) + `data/lessons.md` (the same, to read).

ANDRII'S LIST: `docs/tasks.md` (in Ukrainian: the schedule, the decisions waiting for his yes, the to-do list with
P1-P3, the channel keywords). Keep it current and show it to him (SendUserFile, display render) after every change.
A finished task and an answered decision MOVE to its section 'Зроблено' as '- ✅ ~~**text**~~' (Andrii, Nov 14:
'виконані завдання в таскс мд перенось у зроблене'); the open sections hold only what is open.

Read before any work: `docs/BUILD_PROMPT.md` (the plan and the hard rules; §13 = the second pass), `docs/FORMAT.md`
(§16–§17 win over earlier sections; §17.2 = the picture–word rule, enforced by `render.py`) + `format.json`, `docs/WRITER_PROMPT.md` (scripts are a fixed form of 13 slots,
gated by `tools/script_check.py`). Change a number only with a new measurement.

## Live
**v1.11** on `main` (Nov 14 2026: the writer assembles again (v1.10 had cut off meta), the portrait is the painting's creator from Wikidata, the night writer may make 7 dry runs a night; v1.10 = a fire every hour 12:05-23:05 UTC because GitHub drops scheduled runs, a manual run of main posts the comments and refreshes the statistics too, a Gemini script with a camera target outside LOOK is refused while written; v1.09 = statistics + learning + the night writer Claude as the main writer, Gemini the backup; v1.08 = videos are made a day ahead (27-30 h) and wait private with their publish minute; v1.07 = schedule_video; v1.06 = the first public video (Daniel, 02:00 London), manual publish minute; v1.05 = THE SCHEDULE IS ON since Andrii's yes; v1.04 = channel connected, upload + schedule built; v1.03 = topics
judged 1-10; v1.02 = writer + director + finder; v1.01 = the first dry run; v1.00 = the approved maket).
Next: **v1.12**.

## Channel and schedule
Channel: **sposcaske** (@sposcaske, id UCNamDfqgZhL8JOaAiCNY_ww). Schedule (the source of truth = `gate.py` SLOTS;
Andrii, Nov 14): every day **15:00 and 02:00 London**. THE SWITCH: `data/config.json` `"live"` is **true since Nov 14** (false = the
scheduled runs do nothing; true = they write, make and upload (private, public at the slot through publishAt)).
Never switch it, and never change the slots, without Andrii's yes. History: `docs/versions.md`.
GITHUB DROPS SCHEDULED RUNS (Nov 14: 1 of 8 fires came, 33 minutes late): whenever you are in this repository, check
the slots first (`python3 -c "import gate; print(gate.pick())"`, never `python gate.py`: that books a try). An empty
slot is filled by a manual run `gh workflow run video.yml --ref main -f write=true -f upload=slot` (one video a run).
STANDING PERMISSION for exactly that run (Andrii, Nov 14, in the chat 'sposcaske', after Р19/Р20: 'Тоді запускай все
вручну, це все тепер твоя відповідальність, даю тобі дозвіл'): do not ask again, launch, check the result, report.
The session's safety check let the run through in that chat after his words; in another session it may still refuse:
then say so and he starts it himself in Actions. He chose manual launches over an outside alarm (cron-job.org).
THE DAILY SLOT CHECK (Andrii, Nov 14: 'створи щоденну перевірку слотів о тій годині, в якій тобі буде за потрібне'):
the scheduled task 'sposcaske: щоденна перевірка слотів' (trig_01Kfd5oXF6kjKNvSWVrrAnxS) wakes the chat 'sposcaske'
(session_01DqdGaazqxMWqY2eAJxYgsN) every day at 21:17 UTC: at that hour the next three slots (02:00 tonight, 15:00
tomorrow, 02:00 the night after) are all inside the gate's 30 hours, so one check a day fills whatever GitHub missed.

## The night writer (v1.09, Andrii, Nov 14: 'Нічний сценарист Claude як основний, Gemini як запасний ... Роби')
The scheduled task 'sposcaske night writer' (trig_01WjFPWccHHzWenYrZTT5bqj; every day 07:43 UTC) wakes ONE standing
cloud session of the same name (session_01DqdGaZ55tVzFcGQiVwjGb8, claude-opus-5-5, the repository attached). Not a
fresh session a night: a routine made from a chat gets no repository (tried Nov 14: 'no git repo', the clone was
refused); if Andrii remakes it in the claude.ai routines UI with the repository added, a fresh session works too
and is cheaper. It keeps 4 ready scripts in `scripts/` (two days). Its rules: `docs/NIGHT_WRITER.md`; it pushes only `scripts/` and `data/look/` to
`main`, checks each script with a dry run (at most 7 a night, v1.11), never touches code or the schedule. A ready script is
marked `"written_by": "Claude (night writer) ..."`; one that failed the bot's checks is kept as
`scripts/<id>.failed.json`. The routine spends the Claude subscription's limit (the ww2-bot writer failed on
Nov 13 with 'usage limit reached'): if it does not run, Gemini writes as before v1.09.

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
- NO 10-day `draft` branch here (Andrii, Nov 14: 'не треба'): a bot change goes to `main` at once, as a version.
  Do not propose it again unless he asks.

Hard rules (short): free tools only · public-domain art only · every fact has a source in the story file · never
copy the reference channel's wording or name · never publish, change the schedule, the voice or the look without
Andrii's yes · never delete or re-upload a published video · `ww2-bot` is a read-only warehouse.
Nudity in classical painting is ALLOWED (Andrii, Nov 14, Р11: 'дозволяти'); do not build a filter against it. The
prompts still cap a picture that is MOSTLY naked bodies (`prompts/judge.txt`, `scout.txt`): his word is needed to lift it.
The skill `humanizer` (`.claude/skills/humanizer/`, Andrii, Nov 15: 'скачай humanizer') removes AI habits from prose.
DO NOT run it over a video script on your own: it deletes 'not X but Y', three-beat lines and one-line closers, which
are the joints of the reference's scripts (`docs/FORMAT.md`). Use it on titles, descriptions, comments, docs and
replies, or where Andrii says so.

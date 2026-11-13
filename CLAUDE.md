# CLAUDE.md — sposcaske-bot (v1.01: maket + dry-run bot)

Owner: Andrii (writes in Ukrainian; wants short, army-style answers: task → direct solution, the best free option,
no fluff). Reply in Ukrainian.

State (2026-11-13): the maket + a bot that makes DRY RUNS (`.github/workflows/video.yml` -> `bot.py`; the video goes
to the `preview` branch, the log to `logs`). No channel, no upload, no schedule yet. Next: `docs/BUILD_PROMPT.md` §11 (Andrii's decisions), then milestone M1.

Read before any work: `docs/BUILD_PROMPT.md` (the plan and the hard rules; §13 = the second pass), `docs/FORMAT.md`
(§16–§17 win over earlier sections; §17.2 = the picture–word rule, enforced by `render.py`) + `format.json`, `docs/WRITER_PROMPT.md` (scripts are a fixed form of 13 slots,
gated by `tools/script_check.py`). Change a number only with a new measurement.

## Live
**v1.01** on `main` (Nov 13 2026: the first bot run = a dry run in GitHub Actions, several pictures in one video;
v1.00 = the approved maket, demo 7). Next: **v1.02**. History: `docs/versions.md`.

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

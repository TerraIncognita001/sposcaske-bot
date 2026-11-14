# Version history (newest first)

The system is taken from the warehouse `ww2-bot` (Andrii, 2026-11-13: 'візьми з ww2-bot систему версій vx.xx і
запровадь сюди теж'). The rules are in `CLAUDE.md` ("Versions"). One line per version: `- vX.YY = WHAT IN CAPITALS,
Andrii, date ('his words'): what changed, the numbers, why`. Search here before changing a behaviour: it may have been
tried and rolled back.

- v1.09 = STATISTICS, LEARNING, THE NIGHT WRITER CLAUDE, Andrii, Nov 14 2026 ('P2 Збір статистики ... P2 Самонавчання
  ... P2 Нічний сценарист Claude як основний, Gemini як запасний. Роби ці всі!').
  (1) `stats_now.py` -> `data/stats.json`, in every scheduled run and by the manual input `stats_only`, no Gemini:
  per public video the views, likes, comments (Data API), engaged views, average % viewed, shares, subscribers
  (Analytics; the token has the scope, checked by run 43544715706: Daniel 7 views ten minutes after its first
  minute, analytics rows come 2-3 days later), "stay" = engaged / views, the retention curve and its three steepest
  drops after second 3, each mapped to the caption line spoken then (`bot.py` saves the line times of every upload
  to `data/timeline/<story>.json`), the warehouse's score (stay weighs most), and what the video was made of (hook
  frame as one of 9 fixed names, punch, closer, kind, theme, century, length band, writer, the judge's marks).
  (2) `learn.py` -> `data/learn.json` + `data/lessons.md`: a multiplier 0.5-2.0 for every value of hook frame,
  closer, kind, theme, century, length, writer (mean score of its videos / mean of all; under 3 videos = 1.0); THE
  JUDGE'S SCALE RE-CALIBRATED: each of the six marks weighted 0.5-1.5 by its correlation with our score, a topic's
  total brought back to 1-10. `writer.queue` orders the topics by `learn.priority` (calibrated score x theme x kind),
  the writer's task gets PREFER / AVOID lines. LEARNING SWITCHES ON BY ITSELF AT 8 VIDEOS PUBLIC FOR 3 DAYS (about
  Nov 21); until then learn.json says "on": false and the queue and the prompt are exactly as in v1.08. The
  threshold 7 stays on the judge's own total.
  (3) THE NIGHT WRITER: a Claude cloud routine (rules `docs/NIGHT_WRITER.md`, tools `tools/night_writer.py`: stock,
  brief, crops, save, preview, sheet) keeps 4 ready scripts marked "written_by": "Claude (night writer) ...".
  `bot.py --write` takes the ready script of a topic first (no Gemini request at all: the LOOK is in the script);
  a ready script that fails a check is set aside as `scripts/<id>.failed.json` with the reason and Gemini writes
  that topic in the same run; a topic with no ready script is written by Gemini as before. Why: Gemini's free quota
  was the weak point (one scout run ate a day; three scripts a day never proven), and the first bot-written hook
  gave its detail away. Claude looks at the picture, cuts out every box to check it, and looks at one frame per
  caption line of a dry run before the script counts. The cloud sandbox cannot render (Wikimedia 429), so the
  check is a dry run on GitHub (at most 5 a night, about 20 Actions minutes).
  First night script: Böcklin, Self-Portrait with Death Playing the Fiddle (punch LISTEN, 140 words), dry run
  43544781464 from the work branch: 60.7 s, 12 of 12 checks, 25 of 25 named things in frame.
  Workflow: input `stats_only`; step 'statistics and learning'; state is saved to `main` only by a run of `main`
  (a test run of another branch can no longer write there).
  Pushed on his 'П12 так'; the night writer created on his 'П13 так': the scheduled task
  trig_01WjFPWccHHzWenYrZTT5bqj (every day 07:43 UTC) wakes the standing session session_01DqdGaZ55tVzFcGQiVwjGb8
  (the first try, a fresh session a night, had no repository and wrote nothing).
  First day on `main` (GitHub fired no scheduled run, both slots filled by hand on his 'П14 даю дозвіл'): Böcklin
  by Claude -> BHLGgjy0qs8, 12 of 12; Lucifer by Gemini passed the form on draft 4 and then broke the director
  (a "show" target ' darkness' that is no LOOK name): v1.09 caught it and went on to The Nightmare by Gemini ->
  lFKLVEK27GE, 12 of 12 (v1.08 would have ended the run with an error).
- v1.08 = VIDEOS ARE MADE A DAY AHEAD, Andrii, Nov 14 2026 ('хай тепер за день до пустого слоту бот сам пише та
  випускає відео, загружає як приватне та ставить скеджл на випуск на потрібну годину'). `gate.py`: a run fills the
  earliest empty slot between 30 minutes and 30 HOURS away (was 14 hours); four tries a slot (was two), because a
  slot that failed a day ahead meets the next day's fires again. The cron is unchanged (12:05, 13:05, 20:05, 21:05
  UTC): in the steady state 12:05 makes tomorrow's 15:00 (27 h ahead) and 20:05 makes the 02:00 of the night after
  next (30 h ahead); 13:05 and 21:05 only catch up. So every video lies on the channel, private and scheduled, for
  about a day before it goes public: time for Andrii to look at it. Catch-up on Nov 14: 12:05 -> Nov 15 02:00,
  13:05 -> Nov 15 15:00, 20:05 -> Nov 16 02:00.
- v1.07 = A PRIVATE VIDEO ON THE CHANNEL CAN BE GIVEN ITS PUBLISH MINUTE, Andrii, Nov 14 2026 (his answers to the
  draft: R2 'заплануй його вихід на 1500 сьогодні', R4 'лишити', R5-R7 done by him). `upload.schedule` + workflow
  input `schedule_video`: the Fallen Angel test upload (vquovec65EM) goes public at 15:00 London and holds slot
  E2026-11-14#1, so the bot's own first video is the 02:00 of Nov 15 (made 20:05 UTC). The Nightmare and Medusa are
  back in the queue (`hold` removed).
- v1.06 = A MANUAL RUN MAY NAME ITS OWN PUBLISH MINUTE; THE FIRST PUBLIC VIDEO, Andrii, Nov 14 2026 ('випусти те відео
  яке ми створили як макет сьогодні о 0200, запость як приватне а потім в 0200 переведи його у публічне'; the
  session's safety check stopped the first launch, he answered 'даю дозвіл'). Workflow inputs `publish_at` (UTC) and
  `slot`: with them `upload = slot` skips the gate (which refuses a slot less than 30 minutes away). Run 43541091232:
  Daniel in the Lions' Den, the maket's own story, 57.0 s, 12 of 12 checks, uploaded 01:34 UTC as
  https://youtube.com/shorts/Ym92xlQ5h7M, private, public at 02:00 UTC = slot E2026-11-14#2: the channel's first
  video. The phone of the channel is verified (long uploads "allowed").
- v1.05 = THE SCHEDULE IS ON, Andrii, Nov 14 2026 ('Р1. Увімкнути розклад. Так'): `data/config.json` `"live": true`.
  The first slot is E2026-11-14#1 (15:00 London; the run of 12:05 UTC makes it), then 02:00 and 15:00 every day.
  A topic may carry `"hold"` in `data/backlog.json` and is then skipped by `writer.next_topic`: The Nightmare and
  Medusa (Caravaggio) are on hold until his decision R4. Known gaps at switch-on, all in `docs/tasks.md`: the writer
  has not yet written on a judge's angle, no picture check for nudity, no alarm for an empty slot, the phone of the
  channel is not verified.
- v1.04 = THE CHANNEL IS CONNECTED; UPLOAD AND THE SCHEDULE (SWITCHED OFF UNTIL ANDRII SAYS GO), Andrii, Nov 14 2026
  ('добавив ці секрети'; 'випускатимемо відео 2 рази в день. 1500 за лондоном та 0200 за лондоном'). The secrets
  YT_CLIENT_ID / YT_CLIENT_SECRET / YT_REFRESH_TOKEN were made with the warehouse's OAuth client (its consent screen
  is named "Iron Archive Uploader"; only the owner sees that name) and open the channel **sposcaske (@sposcaske)**,
  id UCNamDfqgZhL8JOaAiCNY_ww, checked by `upload.py --whoami` (run 43537970382; 0 videos; long uploads "eligible" =
  the phone is not verified yet). New: `gate.py` (SLOTS 15:00 and 02:00 London, keys E<date>#1 / #2, a slot is
  filled 30 min to 14 h ahead, two tries; `data/slots.json`), `upload.py` (`upload`: always private, public at the
  slot time through publishAt; the question comment once the video is public; `--pending`), `bot.py --upload
  private|slot` (only a video that passed every check goes up; then `data/used.json` and the slot are recorded;
  a topic that cannot be written is skipped, up to three per run), `data/config.json` `"live": false` = THE SWITCH:
  the scheduled runs do nothing until it is true. Workflow: cron 12:05 / 13:05 UTC (the 15:00 video), 20:05 / 21:05
  (the 02:00 video), Sunday 05:05 (the weekly scout, 20 candidates), manual input `upload` no / private / slot;
  the bot commits its state (`data`, `scripts`) to `main`. Not built yet: thumbnails, stats, learn.py.
- v1.03 = TOPICS ARE FOUND AND JUDGED 1-10; YEARS SPOKEN IN TWO HALVES, Andrii, Nov 14 2026 (after the first video
  the bot made alone: 'те як бот каже рік, треба щоб він казав 18 57 а не 1857. Загалом вибір теми - конкретно ця
  ну зовсім не цікава. проаналізуй ... топ 15 найпопулярніших відео, знайди спільне між ними та напиши для бота
  промпт за яким він шукатиме схожі теми, та те як він характеризуватиме теми, оцінюватиме їх. Добав шкалу від 1 до
  10'). The top 15 took 75 % of the channel's views; what sets them apart, counted on the transcripts: somebody
  watches (9 of 15 against 9 of 43), figures out of darkness (6 against 2), "you" inside the scene (9 against 13),
  a named person's legend (5 against 6), no violence shown (0 against 7): `docs/TOPICS.md`. New: `prompts/scout.txt`
  (where to look and what never worked), `prompts/judge.txt` (six scores: gaze 0-2, darkness and one figure 0-2,
  the flip 0-2, threat without violence 0-2, "you" 0-1, a story with a name 0-1; anchors; disqualifiers; the
  topic's character; THE ANGLE), `topics.py` (scout -> Wikipedia / Commons checks -> the judge with the picture in
  view -> `data/backlog.json` sorted by score). `writer.py` makes only 7+, best first, and gives the judge's ANGLE
  to the script prompt (the Fallen Angel script had picked the hands, the reference's own video the tear and the
  eye). `render.py` `year_words`: 1857 -> "eighteen fifty-seven", 1805 -> "eighteen oh five", 1900 -> "nineteen
  hundred"; the caption keeps the digits. Workflow input `scout`.
- v1.02 = THE BOT WRITES AND SHOOTS BY THE MAKET: WRITER, DIRECTOR, MATERIAL FINDER, ONE VOICE, Andrii, Nov 13-14 2026
  (he sent the five references again: 'ти маєш знайти спільне між всіма 5 референсами та макетом ... записати код
  для бота, щоб всі його відео які він згенерує були максимально схожі до цих референсів', with five points: the
  script and its hook, the effects of the maket (candle flicker, red word, the zoom on what is spoken of, the fire
  flash), the extra material (the author's photo, the score ...), the sound ('дуже важливо щоб на початку всіх
  відео був звук який я тобі скинув') and a chosen voice, the genre). What all five and the maket share, with the
  numbers of the 58 videos: `docs/GENRE.md` (new; also the genre, its topics and the feelings it aims at). ONE
  format for every topic: the maket. New: `prompts/writer.txt` (the 13 slots made universal: S2 "This is <Title>,
  painted by ..." or "In <time>, a <role> named <Name> ..."; hook frames ranked by the views they held; the punch
  word; optional X / M sentences; the evidence pictures) and `prompts/look.txt`; `writer.py` (topic from
  `data/backlog.json`, 20 public-domain seeds -> facts and the lead picture from Wikipedia -> Gemini vision lists
  what is visible with boxes -> the script, gated by `tools/script_check.py`, three rounds -> `scripts/<id>.json`;
  needs the secret GEMINI_API_KEY and has NOT run live yet: no key in this repo); `director.py` (script -> story:
  the hook's jump cuts and glide out to the red word, the card and the portrait in S2, and THE PICTURE-WORD RULE
  as a mechanism: a cue is written for every word that names a thing the camera is not on; shows that hold for
  one line; two short triad sentences share a caption; caption lines of 3-9 words); `sources.py`: `find_portrait`
  (Wikidata P18), `find_commons`, `wikipedia`, a face crop for the portrait card, an evidence picture that cannot
  be found is dropped with its cues. `bot.py`: runs the director on `scripts/<id>.json`, `--write`, and three new
  conformance checks: the first 1.5 s match Andrii's sound in both channels (correlation >= 0.97), the red word,
  the portrait shot. `render.py`: a line may carry its own `names`. `format.json`: `voice.chosen` = Kokoro blend
  am_onyx 0.65 + am_michael 0.35, speed 0.95, 94 Hz, the maket's voice, the only engine in the chain. Workflow:
  inputs `write`, story `_selftest` (the finders against the live APIs: portraits of Cabanel, Tartini, Matejko
  found, the Fallen Angel page gave 20 fact sentences and a public-domain lead picture).
  DRY RUN of `scripts/tartini-devils-trill.json` through the director (run 43527854302): 91.9 s, 220 words, 147 wpm,
  29 camera cues written by the director, picture-word audit 42 of 42, the opening sound 0.995, red word DEVIL, the
  portrait card of Tartini, -16.6 LUFS, true peak -1.0 dBFS, 71 MB; 12 of 12 checks. The run before it failed one
  check (true peak +0.2 dBFS: the shutter click with the voice starting on it overshoots in AAC): the click is 3 dB
  lower now and `render.py` lowers the whole track when the encoded peak is above -0.5 dBFS.
  FIRST VIDEO THE BOT MADE ALONE (Nov 14, after Andrii added the secret GEMINI_API_KEY; runs 43530006181 the
  writer, 43531088580 the final render): topic 1 of the backlog, The Fallen Angel (Cabanel, 1847). Gemini listed 8
  things in the picture with boxes; drafts 1 and 2 broke the form (too few short sentences, a two-sentence detail
  glued to the turn, no triad), draft 3 passed: 128 words, 16 sentences, punch RAGE. The bot found Cabanel's
  self-portrait (Wikidata P18) and a photograph of the Villa Medici (Commons search, CC0). 60.3 s, 132 wpm, audit
  18 of 18, 12 of 12 checks, 28 MB, the bot's own time 108 s. Fixed on the way: the painter's name outside the
  ident asked for the portrait (the rule now lives on the ident line only); multi-word evidence words; a punch
  word written in capitals; the hook opens on a crop; detail zoom capped at 3.6x (5x went soft on the hands); the
  triad's last beat pulls back; the backstory opens on the whole picture; the writer must name its source ("According
  to historical records" got through in this script).
- v1.01 = THE FIRST BOT RUN: DRY RUN IN GITHUB ACTIONS + SEVERAL PICTURES IN ONE VIDEO, Andrii, Nov 13 2026 (he sent
  the reference's video about Tartini's dream, 111 s, nine pictures: 'повністю відтвори це відео за макетом ...
  відтвори це використовуючи драй ран через бота'; 'залиши початок як є' = the approved opening stays). New:
  `.github/workflows/video.yml` (workflow_dispatch: `story`, `dry_run`, `pictures_only`; the video, metadata, report
  and timeline go to the `preview` branch, the log to `logs`, both overwritten, as in ww2-bot); `bot.py` (script gate
  -> pictures -> render -> conformance -> metadata; exit 3 = this story cannot make a good video; no upload yet, it
  refuses to run without --dry-run); `sources.py` (pictures from Wikimedia Commons through Special:FilePath, the
  licence read from the API when it answers and required to be public domain / CC0; a copy in `stories/img/<id>/`
  wins); `requirements.txt` (the versions demo 7 was made with). `render.py`: a cue `"scene": "<picture key>"` cuts
  to another picture of the story, each scene has its own camera, focus boxes (`images.<key>.focus`) and pyramid;
  names in the picture-word audit may be `scene:box`; the encode is capped (`format.json` `encode`: crf 19, 6 Mbit/s)
  so a 110 s video stays under the 100 MB a file the preview branch takes (crf 18 gave 36 MB a minute with the grain).
  `tools/script_check.py`: the ident may say drawn / engraved / carved by. Story `tartini-dream-boilly` (our own
  words in the 13 slots, long form, 217 words; the lead picture is Boilly's lithograph of 1824).
  FIRST DRY RUN (run 43482303137, Nov 13): 4 min 41 s in all, the bot itself 210 s; 91.3 s of video, 146 wpm, six
  pictures fetched by the bot (licences read from Commons: 2 CC0, 4 public domain), picture-word audit 32 of 32,
  -16.0 LUFS, true peak -0.1 dBFS, 69.2 MB; all nine conformance checks passed. The run before it (43481675052,
  `pictures_only`) put the pictures on `preview` so the focus boxes could be marked: Commons answers 429 to the
  cloud sandbox, GitHub's runners get through.
- v1.00 = THE APPROVED MAKET, Andrii, Nov 13 2026 ('Супер! Це буде нашим основним макетом!', after demo 7; the repo
  was created the same hour, first under the working name lore-bot). What it holds: the format measured on the
  reference channel (`docs/FORMAT.md`, `format.json`), the prototype renderer (`render.py`, template "painting"), the
  writer prompt of 13 fixed slots with its gate (`docs/WRITER_PROMPT.md`, `tools/script_check.py`), the build prompt
  (`docs/BUILD_PROMPT.md`), one example story (Daniel in the Lions' Den, Rivière 1872). No channel, no workflow, no
  uploads yet. The seven passes that led to it (each = one demo and Andrii's review, details in FORMAT §16–§18.3):
  (1) first measurement and demo; (2) v1 re-read frame by frame and sound by sound: the opening sound with the voice
  only after it, the giant red hook word, film burn, title card on stars, painter's portrait, white flash; the script
  rebuilt to the reference's construction; (3) vignette, dust, flicker, and the picture–word rule ('зроби щоб фокус
  завжди був на обєкті про якого йдеться в озвучці': `focus_audit` refuses a render that breaks it); (4) Andrii's own
  opening sound file, a lower and rougher voice (F0 109 → 94 Hz), pauses 0.59 s after a sentence, vignette −42 % in
  the corners, a stricter red word; (5) the opening sound in STEREO sample for sample (the mono fold of pass 4 had
  thrown away its width), the red word in Gloock (his pick); (6) the flicker became candlelight from the left ('ніби
  збоку горить свічка'; the colour patches of pass 4 were 'занадто сильним і кольоровим': do not bring them back);
  (7) the candlelight stronger (`overlays.candle.amp` 0.045 → 0.08; 'Виглядає супер'). Mix −16 LUFS, 57.0 s, 148 wpm,
  focus audit 22 of 22.

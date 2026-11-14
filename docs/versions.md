# Version history (newest first)

The system is taken from the warehouse `ww2-bot` (Andrii, 2026-11-13: 'візьми з ww2-bot систему версій vx.xx і
запровадь сюди теж'). The rules are in `CLAUDE.md` ("Versions"). One line per version: `- vX.YY = WHAT IN CAPITALS,
Andrii, date ('his words'): what changed, the numbers, why`. Search here before changing a behaviour: it may have been
tried and rolled back.

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

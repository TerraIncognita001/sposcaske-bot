# Version history (newest first)

The system is taken from the warehouse `ww2-bot` (Andrii, 2026-11-13: 'візьми з ww2-bot систему версій vx.xx і
запровадь сюди теж'). The rules are in `CLAUDE.md` ("Versions"). One line per version: `- vX.YY = WHAT IN CAPITALS,
Andrii, date ('his words'): what changed, the numbers, why`. Search here before changing a behaviour: it may have been
tried and rolled back.

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

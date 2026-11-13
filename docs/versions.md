# Version history (newest first)

The system is taken from the warehouse `ww2-bot` (Andrii, 2026-11-13: 'візьми з ww2-bot систему версій vx.xx і
запровадь сюди теж'). The rules are in `CLAUDE.md` ("Versions"). One line per version: `- vX.YY = WHAT IN CAPITALS,
Andrii, date ('his words'): what changed, the numbers, why`. Search here before changing a behaviour: it may have been
tried and rolled back.

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

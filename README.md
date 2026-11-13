# lore-bot — maket

An autonomous YouTube Shorts bot in the measured format of TikTok's @doom.lore: narrated dark art-history videos
made from one public-domain painting. This folder is the maket (template + prototype), not yet the bot.

| read | what |
|---|---|
| `docs/BUILD_PROMPT.md` | the build prompt: architecture, modules, rules, copy map from ww2-bot, acceptance, milestones, decisions for the owner |
| `docs/FORMAT.md` + `format.json` | the format, measured on the references (script formula, camera grammar, captions, sound) |
| `stories/daniel-lions-den-riviere.json` + `story.schema.json` | the story contract |
| `render.py` | prototype renderer: `python render.py stories/<id>.json out/<id>.mp4` (needs numpy, opencv-python-headless, pillow, kokoro-onnx, ffmpeg; `KOKORO_DIR` with `kokoro-v1.0.int8.onnx` + `voices-v1.0.bin`) |
| `tools/campath.py`, `tools/find_art.py` | the camera-path meter; the Wikidata → Commons image finder |
| `docs/WRITER_PROMPT.md`, `tools/script_check.py` | the script construction, the writer prompt, the code gate |
| `out/demo7.mp4` | the prototype's render (fourth and fifth pass: the owner's opening sound, lower voice, pauses, vignette, candlelight flicker, strict red word; FORMAT §18–18.3) |

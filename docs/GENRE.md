# GENRE.md — what these videos are, and what all five references and the maket have in common (v1.02)

Sources: the five reference videos Andrii sent (the channel's views in brackets: Daniel in the Lions' Den 10.5M,
The Fallen Angel 6.6M, Hope 5.1M, Watchers in the Night 4.6M, Tartini's dream 1.8M), the transcripts and numbers of
all 58 videos of the reference channel, and the approved maket (demo 7 + the dry run). The reference is study
material: its words, name and branding are never used.

## 1. The genre in plain words
**Dark art-history lore in under two minutes.** One old picture is on screen. A calm low male voice says there is
something in it that most people never notice, names the picture or the person, shows the scene as everyone sees it,
then points at one thing ("but look at his hands") and from there on nothing in the picture is innocent any more.
The story behind it is told with its source, one sentence announces "the disturbing part", the thing is shown once
more as a contradiction, and the video ends on a question the viewer wants to answer.

- **Topics.** (a) A single painting or print with a figure in danger, in grief or in the wrong calm: prophets,
  angels and fallen angels, the devil, saints, executions, madness, the last moment before something happens.
  (b) A dark legend or true story that old pictures can tell: a pact with the devil, a cursed book, a plague of
  dancing, a dream. What the 58 videos say about subjects (median views of the videos that dwell on it): angels
  2.4M, a legend "he claimed" 1.8M, the devil / Lucifer 1.6M, eyes and looks 1.0M; plain biblical scenes 0.22M,
  death as such 0.24M, love and women 0.15M, kings and wars 0.12M. Famous but calm pictures and plain history are
  the weakest. So: **a supernatural or moral threat with a face**, never just "a famous painting".
- **What they are about.** Never the brush or the museum. Always one human question under the picture: did he know?
  why is he calm? what is the angel guarding against? was the music human?
- **How it is told.** As a discovery made together with the viewer, in the present tense, in short flat sentences;
  the camera does what the voice says. Facts carry a source ("According to ..."); readings are hedged ("as if",
  "maybe"). No shouting, no gore, no jump scare.
- **What the viewer should feel, in order.** Recognition ("I know this picture") -> a hook of doubt ("what did I
  miss?") -> attention to one small thing -> a chill when the story and the detail meet -> an open question that
  stays ("so which is it?"). The comment is the release: the question is built to be answered.
- **Why it holds viewers (the hook).** The first sentence promises one hidden thing and joins two things that do
  not belong together; the first two seconds already show a crop of the picture, not a title; the red word puts the
  promise on screen as one word; the picture is named only AFTER the promise.

## 2. What all five references and the maket share
| | in the references | in the maket / the bot |
|---|---|---|
| S1 hook | one sentence of 11-19 words in 5 of 5: "There's a terrifying detail in this painting most people completely miss." / "This painting may hide ..." / "There is a silent trap hidden in this painting ..." / "There's a reason this angel is holding a spear ..." / "What if the most beautiful piece of music ... the devil himself?" Frames by median views over 58 videos: What if 1.15M, Something about 0.95M, There's a ... detail / reason 0.72M, This painting 0.59M, Why 0.42M, He / She 0.17M | `prompts/writer.txt` S1: the same frames in that order; two things that do not belong together; the last word is the punch word |
| S2 who and when | 5 of 5 in the second sentence: "This is <Title>, painted by <Artist> [in <year>]." (4) or "In the 18th century, an Italian violinist named ..." (1) | two forms, A artwork and B story (`tools/script_check.py`) |
| the calm picture first | 5 of 5 describe the scene as it looks before the turn | S3 setup |
| the turn | "But look closely." / "but look at his face" / "But then your eyes begin to drift ..." / "But instead of threatening him ..." (34 of 58 videos have a "look" turn) | S4, always a "But look ..." so that the camera can obey |
| short flat sentences | "They're watching him." "He's crying." "It's armed." "He failed." | S5 detail, S6 triad |
| the story with its source | "According to the biblical story", "According to the traditional story of Lucifer", "the story comes from Tartini's own account, recorded by ...", "Blackshear said ..." | S7 "According to ...", S8 expectation, S9 "But ..." |
| the marker | "And here's the disturbing part." / "But here's the disturbing part" / "That's what makes this painting so disturbing." / "and maybe that's exactly why it unsettles" / "And that is when the air goes out of the room." (31 of 58) | S10, worded exactly |
| contradiction, then a hedged reading | "..., yet none of them moves. As if something unseen ..." ("as if" 25 of 58, median 0.71M; "maybe" 14, 0.65M) | S11 "X, yet Y." S12 "As if ...", optional "Maybe ..." |
| the last sentence is a question | 5 of 5 ("So what were the lions really looking at?", "... or the exact moment Lucifer was born?", "would you accept, or ...?") | S13 "So ...?" |
| the opening sound, the voice after it | the same sound in 4 of 5 (correlation 0.99 with Andrii's file), the voice at 1.60-1.76 s in 5 of 5 | `assets/sfx/intro.mp3` in every video, voice at 1.65 s; `bot.py` refuses a video whose first 1.5 s do not match the file |
| crops in the hook | 5 of 5 open on a crop or cut to one within 2 s | the director cuts to each thing the hook names |
| the red word | 3 of 5 (MISS, ANGER, FOREVER): one word, giant, red, 0.9 s, after the hook | every video: the punch word in Gloock, 72 % x 54 % of the stage |
| the flash | fire-like burn (Daniel, Fallen Angel), light flash (Hope), a blink to black and a boom (Tartini) | every video: the warm film burn after the red word, a white flash with a shutter click after the portrait |
| the picture as a card | 5 of 5 show the lead picture or a document small on a dark background while it is named | every video: the card on the star field during S2 |
| the person's portrait | 5 of 5: the painter (painted portrait, self-portrait or photo) or the hero of the story | every video: the portrait card of the person named in S2 (`sources.find_portrait`, a face crop) |
| more material | the legend adds a title page, score pages, a second artist's picture of the scene, the source's author | "evidence" pictures: the writer names them, the bot finds them on Commons, the camera cuts to them on their words |
| the camera goes to what is named | all five; measured on Daniel frame by frame | the director writes the move for every named thing, `render.py` audits it (the picture-word rule) |
| a living light | flicker in 5 of 5 (0.8 % on Daniel, 6 % on Tartini), dust, vignette | candlelight from the left (Andrii's setting, demo 7), dust, vignette -42 % |
| voice | low male, 106-113 Hz, 128-166 words a minute, pauses 0.45-0.63 s after a sentence | Kokoro blend at 94 Hz (lower, as Andrii asked), 146 wpm, pauses 0.59 s |
| music | a quiet dark bed, 13.5-14.6 dB under the voice | the same level, from the ident on |
| length | 51-149 s (58 videos: median 84 s) | 50-100 s |

What is NOT common and therefore not copied: word-by-word captions (one early video), captions without a box
(the legend), the grid behind the card (two videos), modern or AI-made side pictures, living painters (two of the
five references are in copyright: the bot takes public-domain pictures only).

## 3. Where each point lives in the code
| point | file |
|---|---|
| what to make next | `data/backlog.json`, `data/used.json`, `writer.next_topic` |
| facts, the lead picture, what is visible in it | `sources.wikipedia`, `prompts/look.txt` (Gemini vision) |
| the script in the fixed slots | `prompts/writer.txt`, `writer.py`, gate `tools/script_check.py` |
| camera, red word, card, portrait, evidence cuts | `director.py` (script -> story) |
| pictures: download, find, licence, face crop | `sources.py` |
| voice, sound, effects, the audit | `render.py`, `format.json` |
| "is it the maket?" | `bot.py` `conform()` |
| one run | `.github/workflows/video.yml` (`dry_run`, `write`, `pictures_only`) |

# FORMAT.md — the measured format of @doom.lore ("DOOM PAINTS")

The template the bot fills. Everything here is MEASURED on the channel's own videos unless marked `~` (estimated by
eye) or `OURS` (our decision where the reference cannot be copied one to one). Machine-readable twin: `format.json`.

## 0. Evidence
- 5 reference videos chosen by the owner, analysed on clean originals (no watermark):
  v1 Daniel in the Lions' Den / Rivière (47 s, 10.5M views) · v2 Watchers in the Night / Blackshear (67 s, 4.6M) ·
  v3 Tartini, the Devil's Trill (107 s, 1.8M) · v4 The Fallen Angel / Cabanel (114 s, 6.6M) · v5 Hope / Ron Francis (145 s, 5.1M).
- All 58 videos of the channel (2026-09-16 → 11-12): metadata + speech-to-text of every script + one frame each.
- Tools: SIFT registration of every frame against the full painting (the "virtual camera" path at 8 fps), OCR of the
  captions, stem separation (voice / bed), pitch tracking, audio tagging, glyph matching against open fonts.
- Not copied, on purpose: the channel's name, wording, scripts, living artists' paintings (section 13).

## 1. The genre in one paragraph
A calm, low male voice tells you that a famous painting hides something unsettling, names the painting, walks your
eye across its details with a slow virtual camera ("look closely…"), gives the story behind it, reframes it with one
dark thought, and ends on a question to the viewer. One painting fills the frame the whole time. Small phrase
captions sit low. A dark ambient bed runs underneath, with a hit on the first frame and on the turns. 40–150 s.

## 2. Channel numbers
| | |
|---|---|
| videos / period | 58 in 58 days (1–2 a day; slots 13:00–14:30 and 21:00–23:00 UTC) |
| views | 66.9M total, median 520k, top 10.5M |
| duration | 38–145 s, median 84 s (first two weeks 38–70 s; since Sep 27 mostly 70–125 s) |
| script | median 201 words, 16.5 sentences, 144 wpm overall |
| first word | at 1.6–1.75 s, after the opening stinger (§16; the 1.1 s of the first pass was a recogniser artefact); the video ends 0.3–0.5 s after the last word |
| subjects | ~40 paintings (the core) → from mid-October also dark legends / true stories told with photos and engravings |

What performed (views): paintings with a religious or dark figure and a "hidden detail" hook lead — Daniel 10.5M,
Fallen Angel 6.6M, Hope 5.1M, Watchers in the Night 4.6M, the Robert Johnson legend 3.9M, a Christ-like figure 2.8M
and 2.4M. Length does not decide (47 s and 145 s are both in the top 3). Famous-but-calm subjects (Girl with a Pearl
Earring 49k, Christina's World 84k) and plain history (Dyatlov 75k, Fawcett 77k) are the weakest.

## 3. Two templates
- **PAINTING** (primary; v1, v2, v4, v5 and ~40 of the 58 videos): ONE artwork, a continuous virtual camera over it,
  plus at most one side image (the artist's portrait).
- **LEGEND** (v3 and the late "dark lore" videos): 8–25 different images (engravings, portraits, documents, photos),
  one slow move per image, hard cuts, strong vignette, a story told in chronological order.
Both share the script skeleton (section 5), the voice, the captions and the sound.

## 4. Canvas and stage
- Reference canvas = the artwork's own aspect, landscape: 1440×1080 (1.333), 1374×1080 (1.27), 1378×1080 (1.28),
  1032×720 (1.43), 960×720. 24 fps in three references, 60 fps in two. The painting fills the canvas edge to edge
  (base view = the whole painting; when the painting is wider than the canvas its sides are cropped, e.g. v1 shows
  82 % of the width).
- On TikTok this plays letterboxed in the vertical player: black above and below.
- `OURS` (YouTube Shorts need a vertical or square file): canvas **1080×1920, 30 fps**, black background, the
  **stage** = 1080 × round(1080 / a) px, a = artwork aspect clamped to 1.25–1.45, vertically centred. Everything
  (picture, camera, captions, overlays) lives inside the stage: exactly what a TikTok viewer of the reference sees.
  All sizes below are given relative to the STAGE height `Hs` (810 px for a 4:3 stage).

## 5. Script formula
### 5.1 Beats (PAINTING), with measured timing
| # | beat | share of duration | what is said | trigger phrases seen |
|---|---|---|---|---|
| 1 | HOOK | 0–5 s (1–2 sentences) | a claim that the picture hides something | see 5.2 |
| 2 | IDENT | next 3–6 s | "This is ⟨Title⟩, painted by ⟨Artist⟩ [in ⟨year⟩]." | sentence 2 (or 3) in about three quarters of the painting videos |
| 3 | SURFACE | 10–25 % | what anyone sees at first glance, in short plain sentences | "At first glance…", "⟨Subject⟩ is…" |
| 4 | TURN | one line | sends the eye to the detail | "But look closely.", "But look at his face.", "But then your eyes begin to drift…" |
| 5 | DETAILS | 15–30 % | 2–5 details, each named while it is on screen | "In one hand… In the other…", "There's a single tear…" |
| 6 | CONTEXT | 10–20 % | the story or the facts behind it | "According to the biblical story…", "⟨Artist⟩ said he hoped…" |
| 7 | REVEAL | one line + 2–4 sentences | the dark reading | "And here's the disturbing part." (verbatim in v1, v3), "That's what makes this painting so disturbing." |
| 8 | REFRAME | 0–20 % (long videos) | generalises: "Maybe evil doesn't begin with a monster…", "Imagine losing…", a run of 2–3 questions | "Imagine…", "Maybe…", "Would you…?" |
| 9 | QUESTION | last sentence | a question to the viewer | see 5.3 |

LEGEND keeps 1, 7, 8, 9 and replaces 2–6 with the story in time order ("In the 18th century, an Italian violinist
named…"), then an honesty line ("Of course we cannot know whether… The story comes from ⟨source⟩").

### 5.2 Hook formulas (first sentence; all 58 scripts)
| formula (abstract) | count | best views |
|---|---|---|
| "There's a ⟨terrifying / disturbing⟩ detail in this painting most people completely miss." | 7 | 10.5M |
| "There's something ⟨disturbing / unsettling / wrong⟩ about ⟨the way X looks at you / this painting⟩." | 8 | 1.6M |
| "There's a reason ⟨subject⟩ is ⟨doing the odd thing⟩." | 1 | 4.6M |
| "This painting may hide ⟨the purest form of X ever depicted / the exact moment when X was born⟩." | 2 | 6.6M |
| "There is a ⟨silent trap / unspoken question⟩ hidden in this painting… and once you see it, the entire meaning changes." | 2 | 5.1M |
| "Why ⟨is / did / does⟩ ⟨subject⟩ …?" | 7 | 2.4M |
| "What if ⟨the most X thing⟩ ⟨was Y⟩?" | 7 | 2.8M |
| a fact that stings: "He waited 20 years for this moment and died shortly after it happened." | 11 | 3.9M |
| "Imagine ⟨being given a choice between…⟩." | 3 | 575k |
Rule: the hook never names the painting; the title comes in the next sentence. 12–20 words. Present tense.

### 5.3 Closing device (last sentence)
- an either/or question — 18 of 58: "Do you see ⟨reading A⟩, or ⟨reading B⟩?" (the top form: 6.6M, 5.1M);
- an open question — 16: "So what were the lions really looking at?", "Would you have followed him?";
- a one-line statement or aphorism — 24: "Everyone is together, yet nobody seems to belong."
Often opened with "So…", "So when you look at ⟨it⟩…", "So tell me…".

### 5.4 Sentence craft (measured on the 5 references)
- 120 / 151 / 284 / 239 / 377 words; mean 7–15 words per sentence; many 2–5 word sentences ("He's crying.",
  "It's armed.", "He simply waits.").
- Second person and imperatives: "look closely", "look at his face", "look into his eyes", "imagine", "ask yourself".
- Contrast pairs: "Not a symbol of peace. A symbol of readiness."; "Not the moment of the fall, but what comes after."
- Triples: "Would you beg for forgiveness? Would you accept your punishment? Or would you hate the one who cast you away?"
- Hedges mark interpretation: "may hide", "seems to capture", "as if", "maybe", "perhaps".
- Facts are few (title, artist, year, the source story, one quote or circumstance); the rest is reading the picture.
- No dates lists, no numbers runs, no jargon. Vocabulary: detail, disturbing, unsettling, terrifying, silent, cold.

## 6. Voice
| | measured |
|---|---|
| speaker | the same low male voice in all five (median F0 106–113 Hz, 10–90 % range 95–123 Hz: almost monotone) |
| pace | 128–166 wpm overall; articulation 150–200 wpm; slower = more dramatic (v4: 128) |
| pauses | 0.45–0.50 s median between sentences; 0.7–1.3 s before a reveal or the last question (v4: 1.28 s after "…something fascinating.") |
| start / end | first word at 1.60–1.76 s (measured on the separated voice, §16); 0.3–0.5 s of tail; cut to black on the last frame; no outro |
| processing | dry, close, no audible reverb; band-limited to ~6–8 kHz |
`OURS`: Azure neural voice (word timings) → offline Kokoro `am_adam` / `am_michael` (median F0 109 / 115 Hz, the
closest of 12 tested) as the fallback; one clause per synthesis call, pauses inserted by the bot (section 14).

## 7. Camera grammar — PAINTING (the heart of the format)
The camera is a rectangle moving over one high-resolution image. Zoom z = 1 shows the whole picture across the
stage width. Measured on v1, v2, v4, v5 (2 666 registered frames):

| element | measured |
|---|---|
| HOLD on a detail or on the full view | median 1.75 s (IQR 1.0–2.9 s; up to 15–20 s on the full view during context / reflection) |
| drift during a hold | never frozen: 2.4 %/s zoom-equivalent (IQR 1.4–3.5), a slow push or a slow sideways creep |
| GLIDE between framings | median 1.9 s (IQR 1.25–2.5 s), eased (speed thirds 0.8 / 1.3 / 0.9 of the mean), 0.19 stage-widths per second |
| JUMP (hard cut to another framing of the same picture) | 0–12 per video; clustered in the hook and where details are listed |
| share of time | holds 42–70 %, glides 21–46 % |
| something changes | every 2–3 s (21–31 camera events a minute) |
| zoom levels (share of time) | full view 0.9–1.2×: 20–48 % · 1.2–2.2×: 45–65 % · 2.2–3×: 5–14 % · 3–5×: 0–18 % (a face, an eye, a tear) |
| slow push on the full view | 1.0 → 1.3× over 15–20 s (1.5–2 %/s) under context and reflection |

Patterns by beat:
- **Frame 0**: the full picture (v2, v4, v5) or a tight crop of its strongest detail (v1 opens at 1.22×; v5 flashes
  a 3.7× detail for 0.4 s at 0.5 s).
- **HOOK**: the full picture, then 1–3 JUMP cuts to details about 1 s each, in time with the words (v1: full 1.5 s →
  lion 1.0 s → Daniel's bound hands 0.9 s → lion 0.2 s → glide out to the full picture on "…most people completely miss").
- **IDENT**: on "This is ⟨Title⟩" the picture glides OUT to z = 0.5–0.75 in about 2.2 s: it shrinks into a framed
  card on a star field (section 9); on "painted by ⟨Artist⟩" a cut to the artist's portrait or photo for 2–3.5 s
  when one exists (v2, v4, v5), then back to the full picture. A white flash (0.25 s) opens and closes this shot in v1.
- **SURFACE / CONTEXT / REFRAME**: full or wide view with the slow push; hard cut back to the full view to reset.
- **TURN / DETAILS**: glide in to 1.5–3× on the named detail and hold; with a list of things, PAN at constant zoom
  from one to the next (v1 pans at 3.0× across the lions' faces during "none of them are attacking").
- **Picture–word rule**: the camera is on the thing while it is named. It starts moving with the clause that names
  it and arrives within about 1 s. Abstract sentences get the wide view. A theme that returns gets its detail back.
- **QUESTION**: either a glide out to the wide view (v1, v2) or a hold on the key detail (v5); the slow push never stops.

## 8. Camera grammar — LEGEND (v3)
24 shots in 107 s: median 2.5 s, range 0.6–10 s. One image per shot, one move per shot at CONSTANT speed: a push-in
of 1.6–3 %/s (40 %), a pan of 1–2 % of the frame per second (45 %), or a longer reveal move (9 %/s over 9 s; a
pull-out of 4 %/s). Joins: hard cuts (19 of 23), fades through black of 0.4–0.6 s (4). Image order follows the
story: the scene engraving → portrait of the hero → document (sheet music, title page) → back to the scene for the
reveal. A strong vignette on every shot. Detail crops of the lead engraving return 6 times.

## 9. Transitions and overlays
| layer | measured / observed |
|---|---|
| star-field card (IDENT) | black canvas, ~100 small dots (1–4 px at 1080p, white with a few violet-blue), the picture as a card 63 % of the canvas width (v1: x 18.5–81.5 %, y 17.7–82.3 %), thin light edge `~`; the card is the same picture, scaled, so the move in and out is continuous |
| white flash | 0.25 s at the entry and exit of the IDENT card (v1); a warm orange light wash of ~3 s near the end of v4 |
| dust in the air | about ten bright specks in view, each flying a straight track at 80–200 px/s (1080p) in its own direction, sharp 2–5 px dots plus a few large soft ones (measured, §17) |
| vignette | LEGEND: strong (corners near black); PAINTING: light — the picture is 11–13 % darker from 40 % of the radius outward (measured against the clean source, §17) |
| RED HOOK WORD (3 of the 4 painting references; §16) | the hook's last / key word in giant red letters from the end of the hook until the title card, 0.8–1.4 s: "MISS", "ANGER" (tall rough serif), "FOREVER", "99% MISS", "TERRIFYING" (pixel font) |
| end | no outro, no logo, no call to action on screen |

## 10. Captions
Three styles exist; the top three references use style B.
| | A: one word (v2, the first week) | **B: boxed phrase (v1, v4, v5) — default** | C: bare phrase (v3, late videos) |
|---|---|---|---|
| text | one spoken word at a time | one clause, 4–9 words (median 6), 1 line up to ~44 characters, 2 lines above | one clause, 1–2 lines, the words light up as spoken (white = said, grey = to come) |
| font (closest open match) | Inter SemiBold / Poppins SemiBold | **Inter Medium** | Poppins SemiBold |
| size (of stage height) | 4.2–4.5 % | **2.6 %** (27–29 px at 1080) | 3.15 % |
| colour | white, black outline ~0.35 % | white | white with a soft dark shadow |
| box | none | **black at 55–60 % opacity, square corners; text + 4.1 % of stage width each side; 5.5 % of stage height for one line, 8.9 % for two** | none |
| position | centred, centre y 86.5 % | centred, centre y **86.2–86.5 %** | centred, centre y ~85 % |
| timing | with the word | appears 0.25–0.45 s after the clause starts, stays until the next one | same |
Conventions (automatic-caption look): lowercase, no punctuation, proper nouns capitalised. The reference has
recognition errors ("Britain Rivier", "um") — `OURS`: same look, correct spelling, built from the script itself.

## 11. Sound
| | measured |
|---|---|
| frame 0 | a dark tonal STINGER 0–1.5 s (two low organ-like notes, nothing above 1.1 kHz; bed stem −16 dB RMS against −40 dB later); the voice starts only after it, at 1.6–1.75 s (v1, v2, v4, v5; §16) |
| bed | sustained dark ambient: drone, humming pad, low rumble, "scary music" tags; spectral centroid 530–980 Hz; no beat; one track per video, no loop point heard |
| bed level | 9–13 dB under the voice (RMS) in v1–v3; about 6 dB in v4; no ducking measurable (the bed is simply low) |
| LEGEND bed | the subject's own music when there is one: v3 runs a solo violin under the Tartini story |
| accents | low hits on: the IDENT entry (the strongest: v1 6.2 s, v4 5.9 s), the body restart after IDENT, the end of the TURN line, the REVEAL line ("…disturbing part."), and in long videos on most paragraph turns (v4: 16 in 114 s) |
| loudness | −21 LUFS integrated as delivered by TikTok (LRA 3–5 LU). `OURS`: −14 LUFS for YouTube |

## 12. Metadata
The channel's TikTok description: "⟨Title⟩ — ⟨Artist⟩. Painted by ⟨nationality⟩ artist ⟨Artist⟩ in ⟨year⟩, ⟨title⟩
depicts … ⟨3–4 factual sentences: subject, technique, where it hangs⟩. ⚠️ Educational content: This content is
created for educational and teaching purposes, exploring the history, symbolism, and artistic details of historical
artworks. #paint #fyp #curiosity". Later videos: one teaser line + 3–5 tags (#fyp #painting #dark #history).
`OURS` for YouTube: title = the hook compressed to ≤ 60 characters, the painting's name inside it or in the
description's first line; description = the factual paragraph + sources + image credit + the educational line;
3 hashtags; category Education.

## 13. Do not copy
- Their sentences, titles, name, avatar. Formulas are reused; wording is always our own.
- Living or recently dead artists (v2 Blackshear, v5 Francis are copyrighted works): public-domain art only.
- Caption typos and "um"; a hook claim the script never pays off; details that are not really in the picture.

## 14. Renderer parameters (the short list; full set in `format.json`)
| parameter | value |
|---|---|
| canvas / stage | 1080×1920, 30 fps / 1080 × 1080/a, a ∈ [1.25, 1.45], centred |
| lead-in / tail | fade-in 0.5 s; stinger 0–1.5 s; first word at 1.65 s / 0.35 s after the last word, the last 2 frames black |
| pauses | 0.15 s between clauses, 0.45 s between sentences, 0.9–1.3 s before REVEAL and before the last question |
| target pace | 140–160 wpm overall, 100–380 words, 45–150 s |
| hold / glide | hold ≥ 1.0 s with 2.4 %/s drift; glide = 0.9 s + 1.2 s × distance (in stage widths, zoom as log), clamped 0.8–3.0 s (median ≈ 1.9–2.1 s), ease = 0.6·cosine + 0.4·linear |
| zoom limits | detail framing 1.5–3×, never above 5× and never beyond the source's real pixels (≥ 1 source px per output px) |
| IDENT | film burn 0.2 s as the title sentence starts → full picture 1 s → card on the stars (z = 0.62, 1.8 s) → the painter's portrait card pushing in → white flash + shutter |
| captions | style B: Inter Medium 2.6 % Hs, box black 58 %, pad 4.1 % Ws / 1.2 % Hs, centre y 86.3 %, max 44 chars per line, 2 lines, +0.3 s after clause start |
| audio | hit at 0 s, about +6 dB RMS over the voice (the reference's +11 dB cannot fit under a −1.5 dB peak at −14 LUFS; that is why the reference sits at −21 LUFS); bed −12 dB under voice (RMS); accents on IDENT, TURN end, REVEAL; mix −14 LUFS, true peak −1.5 dB |

## 15. Validation of this spec
`render.py` built from these numbers, on the painting of reference v1 with our own script, measured by the same
camera-path tool (`tools/campath.py`):
| | our render | reference v1 |
|---|---|---|
| camera events per minute | 32 | 31 |
| holds / glides / jump cuts | 16 / 10 / 5 | 11 / 8 / 5 |
| hold median · share of time | 1.31 s · 57 % | 1.00 s · 58 % |
| glide median | 2.13 s | 2.12 s |
| drift in holds | 2.1 %/s | 2.6 %/s |
| pace · first word | 156 wpm · 1.1 s | 160 wpm · 1.12 s |
| loudness | −14.1 LUFS (ours, for YouTube) | −21.4 LUFS (TikTok) |
Not yet matched: glide speed (0.46 vs 0.25 stage widths/s — story dependent), the voice timbre (offline Kokoro
`am_adam` in the demo; Azure voices to be compared by ear), particle look (`~`), the star field's exact density.

## 16. Second pass — reference v1 frame by frame and sound by sound (this section wins where it differs from §6–§11)
Method: every frame at the native 24 fps scanned for saturated red, luminance jumps and cuts; every discrete event
looked at; sound from the separated stems, 20–50 ms envelopes, spectrograms and an audio tagger.

| time, s | picture | sound | voice and caption |
|---|---|---|---|
| 0.00–0.50 | FADE IN from black to the full painting (linear; luminance 1 → 13 → 27 → 48 → 85 at 0 / 0.1 / 0.2 / 0.3 / 0.5 s); particles already drifting | STINGER 0.00–1.50: a dark two-note organ-like chord, all energy under 1.1 kHz — a 62–115 Hz cluster with 640 / 820 Hz on top, a 51 Hz swell to 0.8 s, a second note at 1.0 s (88 / 165 / 367 / 526 / 759 Hz); 30 dB over the later bed, about 10 dB over the voice | none |
| 0.50–1.62 | the full painting, completely still | stinger tail, then nothing | none |
| 1.62 | | | the VOICE starts; the first caption appears at 1.67 |
| 1.67 | JUMP CUT 1: a 2.3× crop on the lions at the left, creeping sideways | almost nothing under the voice | "there's a terrifying detail in this painting" |
| 2.75 | JUMP CUT 2: a 2.3× crop on the big lion and Daniel | | |
| 3.0–5.42 | | RISER: broadband noise, +25 dB over 2.4 s, its tone opening up | |
| 3.71 | JUMP CUT 3: the left lions again | | "most people completely miss" |
| 4.4–5.3 | glide out to the full painting | riser at its loudest | |
| 5.38–6.29 | THE RED WORD "MISS" = the last word of the hook. 73.8 % × 54.2 % of the frame, centre (0.49, 0.478), RGB 243 / 15 / 16, a tall rough serif, no animation, the picture under it not dimmed, the caption still visible below | the riser is CUT DEAD at 5.42; SILENCE 5.45–6.10 | the hook ends at 5.46; 0.64 s pause |
| 6.10–6.25 | | SLAM at 6.15–6.25: a broadband crack with a low thump | "this is Daniel in the Lions Den" |
| 6.29–6.46 | FILM BURN over the picture: red tint → orange → yellow-white (peak 6.38) → orange → clear | the MUSIC enters at 6.4 and runs to the end: a slow hummed, choir-like line (sustained notes between 300 and 1100 Hz; tagged humming / theremin / lullaby), −40.8 dB RMS = 14.6 dB under the voice | |
| 6.46–7.25 | the full painting | | |
| 7.25–9.12 | the painting shrinks into a card on the star field (to 62 % of the width) | | "painted by Britain Rivier" (sic) |
| 9.17–10.75 | CUT to the PAINTER'S PORTRAIT as a card on the stars (about 50 % × 90 % of the frame) that pushes in until it fills the frame | | |
| 10.79–10.96 | WHITE FLASH: one fully white frame, clear after 0.17 s | camera SHUTTER: a double click at 10.79 / 10.86 | "Daniel is trapped in darkness" |
| 10.96–24.4 | full view with a slow push → glide in to 3× (13.0–14.6) → pan across the lions (15.2–17.6) → hold → pull out (18.5–24.2) | music | setup, turn at 15.0, detail, triad |
| 24.42 | CUT to the full view, slow push 1.26 → 1.83× until 39.9 | | backstory, reveal marker at 35.2 |
| 40.04 | CUT to 3× on the far-left lion, pan across the faces to 43.6, hold | | the reveal, "as if something unseen…" |
| 44.5–46.9 | pull out until Daniel is in the frame | | "so what were the lions really looking at" (ends 46.70) |
| 47.00 | CUT TO BLACK on the last frame, the caption still on | the music is cut | |

The same skeleton in the other painting references (same full-rate scan): the 0.5 s fade-in and the same stinger in
all four; the voice from 1.60–1.76 s; a red word at the end of the hook in three of four (v4 "ANGER" 4.63–6.00, 65 %
× 55.7 %, the picture dimmed to a third; v5 "FOREVER" 9.58–10.38, a pixel font, 86.8 % × 28 %); a warm burn right
after the hook in v1, v2, v5; a white flash where the portrait ends in v1, v4, v5; no bed under the hook and the
title in v2 and v4; loud swells at the later reveals of the long v5 (86.5–89 s, 103.8–106.7 s).

What the first pass got wrong, and why: frames were sampled every 2 s (the 0.9 s red word, both flashes and the
portrait fell between samples); the speech recogniser placed the first word at 1.12 s although the voice starts at
1.62 s; the opening sound was taken for a sub-bass boom (it is tonal and reaches 850 Hz); the census of all 58 videos
looked at one frame per video at 3.2 s, so it under-counted the red words.

### 16.1 Our second render against it (same meters)
| | demo2 | reference v1 |
|---|---|---|
| fade-in luminance at 0 / 0.1 / 0.2 / 0.3 / 0.5 s | 0 / 17 / 37 / 56 / 96 | 1 / 13 / 27 / 48 / 85 |
| voice starts | 1.65 s | 1.62 s |
| stinger against the voice (RMS) | +8.2 dB | about +10 dB |
| red word: duration · share of the frame | 0.94 s · 24.1 % | 0.91 s · 24.8 % |
| under the red word | silence | silence |
| burn: length above threshold · peak luminance | 0.17 s · 183 | 0.13 s · 200 |
| white flash peak | 252 | 253 |
| music against the voice | −12.5 dB | −14.6 dB |
| last frame | black, caption on | black, caption on |
| script | 136 words, 15 sentences, `script_check.py` 0 failures | 121 words, 16 sentences, 0 failures |
Still different: the voice itself (offline Kokoro; the reference voice is deeper and band-limited), the stinger and
the music are synthesised look-alikes, the slam is softer (+7.5 dB against +16 dB, held back by the −14 LUFS
target), the portrait shot is longer (2.6 s against 1.6 s) because our title sentence carries the year.

## 17. Third pass — the finish of the picture, and the picture–word rule
Asked for by the owner after demo 2: "a light vignette, dust flying in the air, the picture flickers with colour",
and "the focus must always be on the thing the voice is talking about".

### 17.1 The finish, measured on v1's still opening (0.55–1.60 s, the camera does not move there)
| layer | reference v1 | how measured | ours (demo3, same meter) |
|---|---|---|---|
| vignette | luminance against the clean source picture, relative to the centre: 0.94 at 20 % of the radius, 0.89 at 40 %, 0.87 at 60 %, ~0.88–0.90 beyond (light, flat towards the corners) | the frame registered to the Commons file, ratio of blurred luminance by radius | 0.96 / 0.86 / 0.87 / 0.84 |
| grade | luminance ×0.84, contrast ×1.08, saturation ×0.96 against that source | same registration | gain 0.93, contrast 1.05 (half of it: reproductions differ) |
| dust | about 10 specks in view (median 9); each a straight dotted track over the second, 80–200 px/s at 1080p, directions all around with a mean drift up of 14 px/s; sharp dots of 2–5 px, +100…175 levels, and two or three large blurred ones | per-frame blobs over the temporal median, nearest-neighbour tracking; the max-minus-median picture shows the tracks | 9 specks, median 141 px/s, 90th percentile 198 px/s |
| "flickers with colour" | brightness breathing 0.8–1.4 % rms with peaks at 2.0 and 1.05 Hz (peak to peak about 2.5 levels) + noise that changes every frame and carries colour: 1.1 levels per pixel (median), 3.9 at the 95th percentile, saturation jitter up to 7.5. Part of it is the platform's compression; on screen it reads as a living, slightly shimmering picture | global and per-pixel statistics over time, at 480 px width | breathing 0.92 % rms, peak to peak 2.3; per-pixel 1.3 median, 2.5 at the 95th percentile |
A clean render has none of this and looks dead next to the reference; `render.py` now applies all four to every
frame under the captions (`Finish`, `Particles`; numbers in `format.json` → `overlays`).

### 17.2 The picture–word rule (hard)
**While a thing is being named, that thing is what the frame shows.** Demo 2 broke it in its first second: the voice
said "This man…" over a lion. In the reference the rule holds throughout: crops of details under "a terrifying
detail", the whole painting under "this painting" and the title, the painter under his name, the lions under "none
of them are attacking", Daniel under "Daniel doesn't fight".
How it is enforced:
- every camera cue is tied to the word that names its target: `{"to": "hands", "on": "his"}`. A cut lands 0.1 s
  before the word. A glide starts 0.45 s before it and must arrive within 1 s; if the distance is too great for
  that, the renderer turns it into a cut on the word;
- a framing "of" a person or thing means that thing is the largest subject in the frame: at least 70 % of its box
  inside the frame and at least 12 % of the frame (or the closest zoom the source allows). A tall figure gets an
  upper-body box (`daniel_top`), not the full-height one, which in a landscape frame would show mostly lions;
- the story lists its nouns in `names` (word → allowed framings; `full` for the painting as a whole, the image key
  for the painter). The renderer audits every listed word against the camera path and REFUSES to render when a named
  thing is not on screen within a second of its name (`focus_audit`; demo3: 22 of 22);
- words that name nothing visible (the king, God, the night) get the full picture or stay on the subject.

## 18. Fourth pass — the owner's choices after demo 3 (they win over the measurements above)
These five points are Andrii's, given on 2026-11-13 after demo 3. Where a number here differs from §16–§17, this one
is used; the measured number stays in the text above as the reference's value.

| what | reference (measured) | demo 3 | now (format.json) | why |
|---|---|---|---|---|
| opening sound | the same file in v1, v2, v4, v5 (correlation 0.99 with the owner's mp3) | synthesized look-alike | THE FILE `assets/sfx/intro.mp3` (1.61 s), from frame 0, voice starts after it at 1.65 s | "this exact sound at the start of every video" |
| its level | +10.7 dB over the voice, in a −21 LUFS mix | +8.2 dB | +5 dB over the voice in a −16 LUFS mix; only peak tips rounded (correlation with the file 0.999) | a −21 LUFS video is too quiet on YouTube; at −14 the sound could not be louder than the voice without distortion |
| voice pitch | median F0 106–113 Hz | 109 Hz (Kokoro am_adam) | 94 Hz: Kokoro blend `am_onyx:0.65+am_michael:0.35`, speed 0.95, + chest shelf (+4 dB under 180 Hz), −3 dB above 6 kHz, light saturation (`voice.rough`) | "lower and rougher" |
| pause after a sentence | 0.45 s (v1), 0.61 s (v4), 0.62 s (v5); −38 dB silence in the voice stem | 0.44 s | 0.59 s; a sentence that ends inside a caption line gets 0.32 s (each sentence is synthesized on its own); after a comma 0.21 s | "add pauses at the end of a sentence, not long, as in the original" |
| vignette | 6–13 % darker from 40 % of the radius | 4–16 % | clear to 22 % of the radius, then smoothly to −42 % in the corners | "stronger" |
| colour flicker | global colour change frame to frame 0.04–0.12 levels, patches 0.05–0.4 | 0.07–0.1 / 0.09–0.15 | 2.1–2.7 / 2.8–3.1: the tint of the whole frame wanders warm–cold and green–magenta, 20 big soft colour patches drift (new mix every frame, 55 % memory), coloured grain ×2.5, brightness breathing ×2 with 1.2 % jitter | "much stronger". NOTE: the meter does not find this in the reference; it is the owner's look |
| red word | heavy slab serif, slightly uneven edge | Grenze Bold + wavy edge | Bevan (OFL), stretched to 72 % × 54 %, clean straight edges, no added weight | "stricter, not like crinkle-cut fries" |

Checked on demo 4 (57.0 s, 148 wpm): focus audit 22 of 22; pauses by the same meter 0.59 / 0.21 s; F0 94 Hz;
−16.0 LUFS, peak −1.1 dBFS. Knobs if the owner wants more or less: `overlays.flicker.tint / patch / grain_chroma`,
`overlays.vignette.painting`, `voice.kokoro.voice`, `voice.rough`, `timing.pause_sentence_s`.
Origin of the opening sound: it is cut from the reference channel's video (most likely an effect from an editor's
library). Before the channel is monetized, replace it with a licensed copy of the same effect or get the owner's
decision in writing (BUILD_PROMPT §11).

### 18.1 Fifth pass (owner, same day, after demo 4)
- Opening sound: demo 4 folded the file to MONO and rounded its peaks. The file is wide stereo (L/R correlation 0.23,
  side only 2 dB under mid), so the fold threw away a large part of it. Now the output is stereo and the file goes in
  sample for sample: both channels, one gain (peak 0.89), no filter, no limiter, no fade. Demo 5: correlation with the
  file 0.998 (L) / 0.999 (R) after AAC, L/R correlation 0.226 (file 0.229), +4.3 dB over the voice, −16.1 LUFS,
  peak −1.0 dBFS. Everything else of ours stays in the centre.
- Red word: Gloock (OFL), the owner's pick from the sample sheet; still stretched to 72 % × 54 %, clean edges.
  Bevan is no longer used.

### 18.2 Sixth pass (owner, same day, after demo 5) — the flicker is CANDLELIGHT
The owner's description of the reference: "as if a candle burns at the side and the lighting changes from it".
Demo 5's flicker (tint wander + colour patches) was "too strong and too coloured; it must be lighter and warmer".
The row "colour flicker" in the §18 table is replaced by this (`overlays.candle`, `Finish` in render.py):
- one warm light just outside the left edge, a little below the middle (`pos` −0.12, 0.58 of the stage); its strength
  falls with distance (`reach` 0.55 stage widths): 1 next to it, about 0.2 on the far side;
- a constant warm glow on that side (+5 %, red 1.2 : green 0.85 : blue 0.45) and a wavering part of ±4.5 % with the
  same warm weights: a quick tremble (random, 80 % memory from frame to frame at 30 fps) over a slow sway (0.9 Hz and
  0.39 Hz);
- no colour patches, no green / magenta, grain back to fine (luma 2.4, chroma 1.3).
Demo 6, measured over 6 s: the left third of the picture changes by 2.8 % rms in red, 2.1 % green, 1.5 % blue (14 %
between its brightest and darkest frame); the right third by 0.9 / 0.6 / 0.6 % (4 %); the whole frame 1.7 / 1.2 / 0.9 %.
Knobs: `overlays.candle.amp` (how much the light wavers), `glow` (how warm that side is), `pos`, `reach`.

### 18.3 Seventh pass (owner: "looks super, make the flicker stronger")
`overlays.candle.amp` 0.045 → 0.08, `glow` 0.05 → 0.06; nothing else changed. Demo 7 over the same 6 s: left third
4.8 / 3.5 / 2.2 % rms in R / G / B (22 % between its brightest and darkest frame), right third 1.7 / 1.1 / 0.8 % (6 %),
whole frame 3.1 / 2.2 / 1.3 %. The numbers in §18.2 are demo 6's.


## 19. The forms (v1.12, Nov 15 2026): the form follows the picture
Why: the reference's own Fallen Angel (v4, 114 s, 6.7M) was laid beside the bot's Fallen Angel (66 s, the 13 slots).
The 13 slots of §16 are the skeleton of v1 (Daniel, 47 s) and nothing else: the reference tells a face, a scene and a
legend each in its own way. Andrii: 'виправи всі недоліки ... дозволяю тобі ставити чи знімати заборони ... щоб відео
згенеровані нашим ботом були максимально схожі на референс'.

### 19.1 Four constructions (prompts/writer.txt section 3; the gate is tools/script_check.py `check(..., form)`)
| form | measured on | words | seconds | what carries it |
|---|---|---|---|---|
| riddle | v1 Daniel (121 words, 47 s) | 105-140 | 45-65 | a question about what is happening; §16 unchanged |
| emotion | v4 The Fallen Angel (239 words, 30 sentences, 114 s) | 200-250 | 95-120 | the viewer is put in the figure's place |
| scene | v5 Hope (about 400 words, 145 s) | 220-320 | 105-145 | the eye walks from the first figure to the hidden second one |
| legend | v3 Tartini (about 230 words, 107 s) | 190-240 | 95-115 | a named man's story, then "would you?" |
The judge names the form of a new topic (`angle.form`); for a topic without one the writer chooses by the picture.

### 19.2 The emotion form, block by block (v4's own timeline)
0-7 s the hook and the ident · 11-20 s CONTRAST ("this isn't a <monster>. It's <what it is>.") and three slow beats
(three qualities, the third softened) · 20-29 s the turn, the detail, "yet it doesn't feel like <the expected
feeling>" · 29-40 s a second look, the real feeling named, three slow beats of adjectives, "As if" · 40-51 s the
backstory · 51-67 s THE MOMENT ("Not the <event>, but what comes after. The moment when ...") · 67-79 s EMPATHY
("Imagine ..." and three questions to the viewer, the third the dark one) · 79-90 s the marker and the two things in
the face that disagree · 90-105 s THE IDEA (two "Maybe" sentences about people, the second a chain of three steps)
· 105-114 s "So look at him one more time" and two questions. Blocks from 51 s on take HALF the video and had no
slot in §16. The gate checks the joints only (the reference's own text passes it); the words between are new each time.
Lifted for this form: adjectives of feeling (slow, three at a time), verbless three-beat lines, readings outside
the last three sentences, direct address ("you" at least six times; the reference has 7).

### 19.3 The face lock (director.build_lock, format.json camera.face_lock)
v4, 57 frames two seconds apart: the face is in the frame in 51 (about 90 %); frame 0 is the eye; the whole picture
is seen only as the ident card; two glances at the body (1.5 s each) during the contrast; 6 s of the tear alone.
Our old Fallen Angel: the face in 36 % of 66 s, first at second 22, the tear never large, because the camera went to
every named noun. Now, for the emotion form: the video OPENS on the face (story "open"), the camera breathes between
three scales of it (home 3.6x, a middle one about 4.9x, the detail up to 7x: `zoom.macro`), goes to the detail
whenever it is named, glances elsewhere only while the contrast names something, and returns to the face with the
next sentence. The face stands for the figure: its box answers for "the angel". The first demo (run 43657185176):
114.7 s against the reference's 114, 16 of 16 named things in frame, 12 of 12 checks.
A scene opens on its first figure's face too; riddle and legend open on the whole picture, as v1 does.

### 19.4 Pauses by meaning (format.json timing.meaning, v4's word clock)
The reference and our old video have the same share of silence (17 % and 18 %) and the same speed while speaking (171
and 178 wpm). The difference is WHERE the silence stands: 1.28 s before "Not the moment of the fall", 1.0 s before
the third question, 0.92 s and 0.55 s between the three beats, 0.74 s before "According to", 0.70 s before
"Imagine". The director writes these pauses into the lines of the emotion form; a three-beat line is spoken and
captioned one beat at a time.

### 19.5 The frame decides, not the name (director.Geo)
The director now computes what a framing really shows with the renderer's own arithmetic, so "the camera is already
on it" means the audit would accept it. Before, a named word could pass the director and fail the audit (Nov 14:
'Jane' with the camera on her hand; 'throne'). A script carries the picture's aspect (`lead.aspect`) for this.

# WRITER_PROMPT.md — the script writer: reference construction, sentence by sentence

> **v1.02: the prompt the bot sends is `prompts/writer.txt`** (the same 13 slots, made universal from all five
> references: S2 has two forms, artwork and story; optional X and M sentences; the pictures beside the lead one).
> `prompts/look.txt` asks the model what is visible in the lead picture. Part C below is the first version, kept
> for its reasoning; where the two differ, `prompts/writer.txt` wins. **v1.12: the 13 slots are one form of four
> (riddle); emotion, scene and legend are in `prompts/writer.txt` section 3 and `docs/FORMAT.md` section 19.** What the five references share, with
> numbers: `docs/GENRE.md`. From sentences to camera: `director.py` (part D below is now done by code).

Why this file exists: the first demo script was written "in the spirit" of the reference and came out built
differently. This file fixes the construction. Part A shows the difference, part B is the construction as measured,
part C is THE PROMPT to give to the model, part D is how the result is checked by code.

## A. What was different (reference v1 against our first script)
| | reference v1 (121 words, 16 sentences) | our first script (147 words, 21 sentences) |
|---|---|---|
| thread | ONE detail (the lions do not attack). The hook promises it, the turn shows it, the reveal repeats it harder, the question asks about it | four details in a row (tied hands, bones, each lion, the hidden face): a list, not a thread |
| hook | a channel frame: "There's a terrifying detail in this painting most people completely miss." Its last word is the punch word, shown giant and red | a twist of our own ("…is not the lions"), no frame, no punch word |
| setup | one sentence: who, where, the danger | five pieces, two of them verbless ("A pack of lions. One old man.") |
| turn | "But look closely." exactly once, at 30 % | two turns ("Now look at the floor." … "But look at the lions again.") |
| triad | "Daniel doesn't fight. He doesn't run. He simply waits." | three unrelated one-liners ("One snarls. One crouches. …") |
| backstory | "According to the biblical story, …" + what should have happened + "But …" what did | one sentence, no source phrase, no expectation / outcome pair |
| reveal | marker "And here's the disturbing part." → "X, yet Y." → "As if …" | marker → a new idea (the face is never shown) |
| closer | one question from "So": "So what were the lions really looking at?" | an extra marker ("So here is the question.") + an 18-word either/or |
| sentences | all complete; 9 of 16 open with But / And / So / As if / According to / That | fragments ("Bones."); 4 of 21 such openers |
`tools/script_check.py` encodes these points: the reference passes with 0 failures, the first script fails 8, the
rewritten script (`stories/daniel-lions-den-riviere.json`) passes.

## B. The construction (from v1 and its siblings of the same weeks, 12 scripts read in full)
Slots in order. Word counts are per sentence. `[F]` = a fact that needs a source, `[L]` = something visible in the
picture, `[R]` = a reading, always hedged.
| # | slot | what it does | wording | words |
|---|---|---|---|---|
| S1 | HOOK | promises ONE unsettling thing without naming the painting; ends on the punch word | one of the frames in C.3 | 8–18 |
| S2 | IDENT `[F]` | names it | "This is ⟨Title⟩, painted by ⟨Artist⟩ in ⟨year⟩." (no year when it is uncertain; "around ⟨year⟩" when sources say so) | 9–16 |
| S3 | SETUP `[L]` | who is here, where, and what ought to happen | "⟨Subject⟩ is / stands / sits …, surrounded by …" or "At first, you see …" — 1 sentence, 2 at most | 10–20 |
| S4 | TURN | sends the eye to the detail | "But look closely." · "But look at ⟨his hands⟩." · "But look closer." | 3–7 |
| S5 | DETAIL `[L]` | the thing itself, said flat | 1–2 sentences, often a negative: "None of them are attacking." "They're tied behind his back." | 3–8 |
| S6 | TRIAD `[L]` | three short parallel sentences about the subject: no, no, only | "He doesn't fight. He doesn't run. He simply waits." · "It can't run. It can't fight. It can only wait." | 3–6 each |
| S7 | BACKSTORY `[F]` | the story behind it | "According to ⟨the biblical story / the Gospels / Homer / Plato's account⟩, ⟨past tense⟩." | 12–20 |
| S8 | EXPECTATION | what should have followed | "That night, he should have died." | 5–9 |
| S9 | OUTCOME `[F]` | what did | "But ⟨when morning came⟩, …" | 6–10 |
| S10 | REVEAL MARKER | announces the dark reading | "And here's the disturbing part." (also: "…the unsettling part.", "That's what makes this painting so disturbing.") | 5–9 |
| S11 | REVEAL `[L]` | the detail again, as a contrast | "⟨X⟩, yet ⟨Y⟩." | 8–13 |
| S12 | IMPLICATION `[R]` | what it suggests | starts "As if …" or "Almost as if …" | 7–11 |
| S13 | QUESTION | hands it to the viewer | starts "So …" and ends "?"; open ("So what …?") or either/or ("So is he …, or …?"); about the same detail | 6–16 |
Totals: 105–140 words, 13–17 sentences, mean ≤ 10 words, at least 4 sentences of ≤ 5 words.
Long form (150–240 words, the channel from late September): after S6 add the ARTIST'S CHOICE pair "⟨Artist⟩ didn't
paint ⟨A⟩. He painted ⟨B⟩."; after S12 add one or two "Maybe …" sentences and "So look at ⟨it⟩ one more time."
before the question. Nothing else changes.

## C. THE PROMPT
```
You write narration scripts for 50-second videos about one famous painting. Your scripts must have EXACTLY the
construction described below. It is a fixed form, like a sonnet: the same slots, in the same order, every time.
Only the content changes.

### 1. What you receive
FACTS   numbered source sentences about the artwork (title, artist, year, collection, the story it shows).
LOOK    a list of things that are really visible in the picture, each with a short name.
AVOID   hook frames and closing types used in the last videos.

### 2. The one rule above all
Choose ONE detail from LOOK that is strange once you notice it. The whole script is about that one detail:
the hook promises it, the turn shows it, the reveal says it again as a contradiction, the question asks about it.
Other things in the picture may appear only in the setup sentence.

### 3. The slots (write exactly these, in this order)
S1  HOOK. One sentence, 8-18 words, present tense. Use one of these frames (not one listed in AVOID):
      "There's a ___ detail in this painting most people ___."
      "There's something ___ about the way ___."
      "Something about ___ feels completely wrong."
      "This painting may hide ___."
      "This ___ is about to ___, and ___."            (a fact that stings)
      "He / She ___ and still ___."                    (a fact that stings)
      "Why is / does / did ___?"
      "What if ___?"
    Do not name the painting or the artist. Do not reveal the detail. The LAST WORD must be a strong, plain word
    of 3-8 letters (miss, wrong, calm, alive, forever, alone, watching): it is shown on screen in giant red letters.
S2  IDENT. Exactly: "This is <Title>, painted by <Artist> in <year>."
S3  SETUP. One sentence (two at most), 10-20 words: who is in the picture, where, and the danger or the calm.
    Patterns: "<Subject> stands / sits / is ..., surrounded by ..." or "At first, you see ...".
S4  TURN. Exactly one of: "But look closely." / "But look closer." / "But look at <his | her | the> <thing>."
S5  DETAIL. One or two sentences of 3-8 words: what is there, said flat. No adjectives of opinion.
S6  TRIAD. Three sentences of 3-6 words in the same shape: two with a negative, then one with "simply", "only" or
    "just". Example of the SHAPE (do not reuse the words): "X doesn't A. X doesn't B. X simply C."
S7  BACKSTORY. One sentence, 12-20 words, past tense, beginning "According to <source>,". Facts only.
S8  EXPECTATION. One sentence, 5-9 words: what should have happened.
S9  OUTCOME. One sentence, 6-10 words, beginning "But": what did happen.
S10 REVEAL MARKER. "And here's the disturbing part." or "And here's the unsettling part." (rotate).
S11 REVEAL. One sentence, 8-13 words, of the form "<what you see>, yet <what makes it wrong>."
S12 IMPLICATION. One sentence, 7-11 words, beginning "As if" or "Almost as if".
S13 QUESTION. One sentence, 6-16 words, beginning "So" and ending "?". Either "So what ...?" or
    "So is <subject> ..., or ...?". It is about the same detail.
Total 105-140 words. 13-17 sentences.

### 4. Style
- Plain spoken English. Short sentences. Every sentence has a subject and a verb: never a fragment.
- Present tense for what is in the picture, past tense for S7-S9.
- Name the subject often ("Daniel ... Daniel ...") instead of piling up pronouns.
- Allowed sentence openers: But, And, So, As if, According to, At first, That night, Look.
- Allowed intensifiers: completely, almost, simply, really, still, already, exactly.
- Never: semicolons, dashes, brackets, digits other than the year, lists of three adjectives, "masterpiece",
  "iconic", "delve", "testament", "let that sink in", a call to like or subscribe, a second TURN, a second marker.
- A reading (what it "means") appears only in S12 and S13, and is always hedged by "as if", "almost" or a question.
- Every fact comes from FACTS. If FACTS does not say it, you do not say it. Give the number of the source sentence.
- Every thing you name must be in LOOK. Give its name.

### 5. Output (JSON only)
{"detail": "<name from LOOK>", "hook_frame": "<frame used>", "hook_title": "<last word of S1, upper case>",
 "closer": "open | either_or",
 "sentences": [{"slot": "S1", "text": "...", "kind": "HOOK|FACT|LOOK|READING", "source": <FACTS number or null>,
                "focus": "<LOOK name the camera should show, or 'full'>"}, ...]}

### 6. Before you answer, check
[ ] one detail only, and S1, S5, S11 and S13 are all about it
[ ] S1 ends on the punch word, and hook_title is that word
[ ] S2, S4, S10 are worded exactly as required
[ ] S6 is three parallel sentences: negative, negative, "simply / only / just"
[ ] S7 begins "According to", S9 begins "But", S12 begins "As if", S13 begins "So" and ends "?"
[ ] 105-140 words, no fragment, no digit except the year
[ ] no sentence copied from any earlier script
```

### C.1 Two examples in the construction (ours; give them to the model as the pattern)
Daniel in the Lions' Den (Rivière, 1872) — detail: his stillness; hook_title CALM:
> This man is about to be eaten alive, and somehow he is completely calm. This is Daniel in the Lions' Den, painted
> by Briton Rivière in 1872. Daniel stands in a stone pit, surrounded by lions, with old bones scattered across the
> floor. But look at his hands. They're tied behind his back. He can't fight. He can't run. He can only stand there.
> According to the Book of Daniel, he was sentenced to this pit because he would not stop praying. Nobody survives a
> night in a lions' den. But at sunrise, the king found him alive. And here's the unsettling part. The lions are
> snarling, yet Daniel hasn't moved a step. As if he already knows how this night ends. So is he waiting to die, or
> does he know something the lions don't?

The Ambassadors (Holbein, 1533) — detail: the stretched skull; hook_title MISTAKE:
> There's a shape at the bottom of this painting that looks like a mistake. This is The Ambassadors, painted by Hans
> Holbein the Younger in 1533. Two powerful men stand beside a table covered with globes, instruments and
> books. But look at the floor. There's a long grey smear between their feet. It isn't a shadow. It isn't a stain.
> It's simply a skull. According to the National Gallery, Holbein stretched it so it only takes shape from the side. From the front, you should see nothing but wealth. But from the side, the skull is the clearest
> thing in the room. And here's the disturbing part. These men have everything, yet death is already standing
> between them. As if it had been in the picture the whole time. So what is waiting at the edge of your own picture?

## D. From sentences to the story file
1. `tools/script_check.py` must report 0 hard failures (it is part of `check.py`).
2. Split each sentence into caption lines of 3–9 words at a comma or before and / with / that / because / after;
   sentences of ≤ 9 words stay whole; two short triad sentences may share a line.
3. Beats for the renderer: S1 `hook` · S2 `ident` · S3 `setup` · S4 `turn` · S5 `detail` · S6 `triad` · S7–S9
   `backstory` · S10–S12 `reveal` · S13 `question`.
4. THE PICTURE–WORD RULE (hard, FORMAT §17.2): while a thing is named, that thing fills the frame. Tie every cue to
   the word that names its target (`"on": "<word>"`), list the nouns in `names` (word → allowed framings), give
   people an upper-body box. `render.py` refuses a story in which a named thing is not on screen within a second of
   its name. A hook about "this man" opens on the man, not on the lions.
5. Camera by slot (the reference's own choreography, FORMAT §16): S1 two or three jump cuts to crops, then a glide out
   to the full picture so the red word lands on it · S2 the card on the stars, then the painter's portrait card · S3
   full picture with the slow push, a glide toward what is named · S4–S5 glide in on the detail and hold · S6 a slow
   pull back · S7–S10 cut to the full picture, slow push · S11 cut in close and pan across · S12 hold · S13 glide out
   until the subject and the detail are both in frame.

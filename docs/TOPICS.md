# TOPICS.md — which subjects the bot looks for, and how it scores them from 1 to 10 (v1.03)

Why: the first video the bot made alone (The Fallen Angel, with the HANDS as its detail) was dull (Andrii, Nov 14:
'вибір теми ... ну зовсім не цікава'). The same picture is the reference channel's second most watched video
(6.6M) with another angle: the tear and the eye that meets yours, "grief or the birth of hatred". So a topic is not
a title: it is **a picture + the one angle on it**, and both are chosen by rule now.

## 1. What the 15 most watched videos have in common
The reference channel published 58 videos; its top 15 took **75 % of all views** (1.5M to 10.5M each; the other 43
have a median of 0.29M). Counted on the transcripts (share of the top 15 against share of the other 43, and the
median views of all videos with / without the feature):

| feature | top 15 | other 43 | median views with / without |
|---|---|---|---|
| somebody WATCHES: looks at the viewer or is watched | 9 | 9 | 1.29M / 0.29M |
| one or two figures out of DARKNESS | 6 | 2 | 1.65M / 0.39M |
| the viewer is addressed as "you" inside the scene | 9 | 13 | 0.89M / 0.29M |
| a named person and a story he "claimed" / a legend | 5 | 6 | 0.93M / 0.35M |
| a hedged reading (as if, maybe, what if) | 8 | 21 | 0.60M / 0.35M |
| a sacred or demonic figure, by itself | 8 | 15 | 0.55M / 0.49M (decides nothing) |
| violence SHOWN (blood, a killing, a corpse) | 0 | 7 | 0.26M / 0.60M |

The fifteen, one line each: Daniel among lions that watch and do not attack · a fallen angel whose eye meets yours
over a tear · a suitor at a door and the woman hiding from him · an angel with a spear over a sleeping child · a
bluesman and the devil at a crossroads · two Christ-like strangers in the dark, staring · a jester alone at a feast
· dancing demons "drawn as a warning" · the couple who hunted demons, "what followed them home" · the violinist who
heard the devil play · a giant face in an empty landscape · Lucifer's two eyes in the dark · Saint John's wrong
smile · a pet that turned.
At the bottom: Girl with a Pearl Earring, Christina's World, Whistler's Mother (famous, calm), the Dyatlov pass, a
lost explorer, a war hero (plain history), The Nightmare (the monster is in full view).

In one sentence: **a face in the dark that watches, one detail that turns it around, nothing violent shown, and a
question that puts the viewer inside.** Fame, the artist's name and the length of the video decide nothing.
These are 58 videos of one channel: the counts show what went together with views there, not a law. The scale is
re-fitted on our own numbers once we have them (learn.py, later).

## 2. The scale (prompts/judge.txt; the model looks at the picture, the code adds up)
| | what | 2 | 1 | 0 |
|---|---|---|---|---|
| G | the gaze | looks straight at the viewer, or is watched | a look matters, meets nobody | nobody looks |
| D | darkness and one figure | 1-2 figures on a dark or empty ground, readable on a phone | 3-6 figures or a plain daylight scene | a crowd, a landscape |
| F | the flip | one thing in a close crop contradicts the first impression | it must be explained before it is seen | nothing to find |
| T | threat without violence | danger or the forbidden is present, nothing is shown happening | grief, aftermath | no stakes, or the violence is shown |
| Y | "you" | (1) one honest question puts the viewer inside | | the viewer stays outside |
| S | a story with a name | (1) the facts hold a story with a source that pays off the flip | | only art history |

Total 1-10. **9-10** make first · **7-8** make · **5-6** reserve · **1-4** never. Disqualified (0): fewer than
eight fact sentences, a picture that is not free or under 1800 px, mostly naked bodies or gore, living people.
Anchors: The Fallen Angel 10 · Lucifer (von Stuck), Daniel, Leonardo's Saint John 9 · Tartini's dream 8 · Stanczyk 7 ·
Girl with a Pearl Earring 3 · an expedition told with photographs 1.

## 3. How the bot uses it
1. `topics.py --scout N` — `prompts/scout.txt`: Gemini proposes N subjects that fit the profile, spread over the
   places where such pictures are found (Symbolists, academic "fallen" pictures, Caravaggio and the one-light
   painters, Goya, the Pre-Raphaelites, Dore and Blake, Russian and Polish history painting, manuscripts, legends
   of pacts).
2. Each is checked: the Wikipedia article exists and has facts, its picture is free and at least 1800 px wide.
3. `prompts/judge.txt`: Gemini is shown the picture and the facts, scores the six things with a reason for each,
   describes the topic (figure, threat, feeling, theme) and gives THE ANGLE: the first impression, the one detail
   (the strongest, usually in the face), its two readings, the closing question, three punch words.
4. `data/backlog.json` keeps everything with its score. `writer.py` takes only 7 and more, the highest first, and
   writes the script ON the judge's angle (`prompts/writer.txt`, input ANGLE).
Run it: workflow `video`, input `scout` = how many candidates; the list arrives on the `preview` branch.

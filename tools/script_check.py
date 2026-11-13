#!/usr/bin/env python3
"""Does a script have the CONSTRUCTION of the reference (docs/WRITER_PROMPT.md)?

    python tools/script_check.py stories/<id>.json        # a story file (lines are joined into sentences)
    python tools/script_check.py --text "Sentence one. Sentence two. ..." --title "Daniel in the Lions' Den" [--punch MISS]

Prints one line per rule: OK / FAIL. Exit code 1 when a hard rule fails. The rules were derived from reference v1 and
its siblings on the channel (FORMAT.md section 16); the reference script itself passes all of them.
"""
import json, re, sys

NEG = re.compile(r"\b(no|not|none|never|nobody|nothing|isn't|aren't|doesn't|don't|didn't|can't|cannot|won't|hasn't|haven't|wasn't|weren't)\b", re.I)
HOOK = [r"^There's (a|an|something)\b", r"^There is (a|an|something)\b", r"^Something about\b", r"^This painting may hide\b", r"^This (man|woman|child|lamb|king|saint|angel)\b",
        r"^(He|She|They) (knew|waited|was|were|is|are)\b", r"^Why (is|are|does|did)\b", r"^What if\b", r"^The detail\b", r"^Just look\b", r"^It's one of\b", r"^This is what\b", r"^What happened\b"]
TURN = re.compile(r"^(But look|Now look|Look) (closely|closer|again|at|into)\b", re.I)
MARK = re.compile(r"(here's the (disturbing|unsettling|strange|terrifying|haunting|darkest) part|that's what makes (this|the) (painting|picture|scene|portrait)|most (haunting|disturbing|unsettling) detail|darkest part of (this|the) painting)", re.I)


def sentences(text):
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+", text.strip()) if s.strip()]


def check(sents, title="", punch=None):
    wc = [len(s.split()) for s in sents]
    words, n, out = sum(wc), len(sents), []

    def rule(name, ok, detail="", hard=True):
        out.append((bool(ok), hard, name, detail))

    find = lambda rx, lo=0: next((i for i in range(lo, n) if re.search(rx, sents[i])), None)
    rule("length 105-150 words (short form) or 150-240 (long form)", 105 <= words <= 240, f"{words} words")
    rule("12-28 sentences", 12 <= n <= 28, f"{n} sentences")
    rule("mean sentence <= 10 words", words / n <= 10, f"{words / n:.1f}")
    rule("no sentence over 24 words", max(wc) <= 24, f"longest {max(wc)}")
    rule("at least 4 sentences of 5 words or fewer", sum(w <= 5 for w in wc) >= 4, f"{sum(w <= 5 for w in wc)}")
    rule("every sentence has a verb (no fragments like 'Bones.')", all(w >= 3 or re.search(r"\b(is|are|was|were|'s|'re|look|wait|stare|know|can|do|does|did|has|have)\b", s, re.I) for s, w in zip(sents, wc)),
         "; ".join(s for s, w in zip(sents, wc) if w < 3))
    # S1 hook
    rule("S1 hook uses a reference frame", any(re.search(rx, sents[0]) for rx in HOOK), sents[0])
    rule("S1 hook is 8-18 words", 8 <= wc[0] <= 18, f"{wc[0]}")
    if title:
        rule("S1 hook does not name the painting", title.lower() not in sents[0].lower())
    if punch:
        rule("S1 ends on the punch word (the red word on screen)", re.sub(r"\W", "", sents[0].split()[-1]).lower() == punch.lower(), sents[0].split()[-1])
    # S2 ident
    rule("S2 is 'This is <Title>, painted / drawn / engraved / carved by <Artist> [in <year>].'", re.match(r"^This is .+, (painted|drawn|engraved|carved|sculpted|made) by .+\.$", sents[1]) is not None, sents[1])
    # turn, detail, triad
    it = find(TURN, 2)
    rule("a TURN sentence 'But look closely / at <detail>.' in the first half", it is not None and it <= n // 2, sents[it] if it is not None else "missing")
    if it is not None:
        rule("TURN is 3-7 words", 3 <= wc[it] <= 7, f"{wc[it]}")
        rule("SETUP: 1-2 sentences between IDENT and TURN", 1 <= it - 2 <= 2, f"{it - 2}")
        rule("the sentence after the TURN is short (<= 8 words): the detail, stated plainly", it + 1 < n and wc[it + 1] <= 8, sents[it + 1] if it + 1 < n else "")
    tri = next((i for i in range(2, n - 2) if all(wc[j] <= 6 for j in (i, i + 1, i + 2)) and sum(bool(NEG.search(sents[j])) for j in (i, i + 1)) >= 2
                and re.search(r"\b(simply|only|just|still)\b|^(It's|He's|She's|They're) ", sents[i + 2])), None)
    rule("a TRIAD: three parallel short sentences, two negatives then 'simply / only / just ...'", tri is not None, " ".join(sents[tri:tri + 3]) if tri is not None else "missing")
    # backstory
    ib = find(r"^(And )?[Aa]ccording to\b", 2)
    rule("BACKSTORY opens with 'According to <source>, ...'", ib is not None, sents[ib] if ib is not None else "missing")
    if ib is not None:
        rule("OUTCOME: a 'But ...' sentence within 3 sentences after the backstory", any(re.match(r"^But\b", sents[j]) for j in range(ib + 1, min(n, ib + 4))),
             " / ".join(sents[ib + 1:ib + 4]))
    # reveal
    im = find(MARK, (ib or 2))
    rule("REVEAL MARKER after the backstory ('And here's the disturbing part.' family)", im is not None, sents[im] if im is not None else "missing")
    if im is not None:
        rule("REVEAL: a contrast with 'yet' or 'but' right after the marker", any(re.search(r"\b(yet|but)\b", sents[j], re.I) for j in range(im + 1, min(n, im + 3))),
             " / ".join(sents[im + 1:im + 3]))
        rule("IMPLICATION: a sentence starting with 'As if' / 'Almost as if' after the marker", any(re.match(r"^(Almost )?[Aa]s if\b", sents[j]) for j in range(im + 1, n)), "")
    # closer
    rule("last sentence is a question starting with 'So'", re.match(r"^So\b", sents[-1]) and sents[-1].endswith("?"), sents[-1])
    rule("closing question is 6-16 words", 6 <= wc[-1] <= 16, f"{wc[-1]}")
    # style
    text = " ".join(sents)
    rule("no semicolons, dashes, brackets", not re.search(r"[;—–()\[\]]", text))
    rule("no digits except one year", len(re.findall(r"\d+", text)) <= 1, " ".join(re.findall(r"\d+", text)), hard=False)
    rule("banned words absent", not re.search(r"\b(masterpiece|iconic|delve|tapestry|testament|breathtaking|um|subscribe|like and)\b", text, re.I))
    openers = sum(bool(re.match(r"^(But|And|So|As if|Almost as if|According to|At first|That's|Maybe|Because|Look)\b", s)) for s in sents)
    rule("at least a third of the sentences open with But / And / So / As if / According to / At first / Look", openers >= n / 3, f"{openers} of {n}", hard=False)
    return out, words, n


if __name__ == "__main__":
    a = sys.argv[1:]
    if a and a[0] == "--text":
        text = a[1]
        title = a[a.index("--title") + 1] if "--title" in a else ""
        punch = a[a.index("--punch") + 1] if "--punch" in a else None
    else:
        st = json.load(open(a[0], encoding="utf-8"))
        text, title, punch = " ".join(l["say"] for l in st["lines"]), st["artwork"]["title"], st.get("hook_title")
    res, words, n = check(sentences(text), title, punch)
    for ok, hard, name, detail in res:
        print(("OK  " if ok else "FAIL" if hard else "warn"), name, ("| " + detail) if detail and not ok else "")
    bad = sum(1 for ok, hard, _, _ in res if not ok and hard)
    print(f"{words} words, {n} sentences, {bad} hard failures")
    sys.exit(1 if bad else 0)

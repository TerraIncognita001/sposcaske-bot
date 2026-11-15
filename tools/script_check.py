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


THREE = re.compile(r"^[^,.?!]+,[^,.?!]+,[^,.?!]+[.]$")                # "Beautiful, perfect, almost divine."
IDENT_A = r"^This is .+, (painted|drawn|engraved|carved|sculpted|made|written|composed) by .+\.$"
IDENT_B = r"^In (the |about |around )?[\w' -]{2,40}, an? .{3,60} (named|called) [A-Z].+\.$"
YOU = re.compile(r"\byou(r|rs|rself)?\b", re.I)


def check_form(sents, title, punch, form):
    """v1.12: the three long constructions measured on the reference's own videos (docs/FORMAT.md section 18):
    emotion = v4 The Fallen Angel (114 s, 239 words, 29 sentences), scene = v5 Hope (145 s), legend = v3 Tartini
    (107 s). The joints are checked, never the words between them."""
    wc = [len(s.split()) for s in sents]
    words, n, out, text = sum(wc), len(sents), [], " ".join(sents)

    def rule(name, ok, detail="", hard=True):
        out.append((bool(ok), hard, name, detail))

    find = lambda rx, lo=0, fl=0: next((i for i in range(lo, n) if re.search(rx, sents[i], fl)), None)
    lim = {"emotion": (190, 260, 24, 36), "scene": (210, 330, 20, 38), "legend": (180, 250, 18, 32)}[form]
    rule(f"length {lim[0]}-{lim[1]} words ({form})", lim[0] <= words <= lim[1], f"{words} words")
    rule(f"{lim[2]}-{lim[3]} sentences", lim[2] <= n <= lim[3], f"{n} sentences")
    rule("no sentence over 30 words", max(wc) <= 30, f"longest {max(wc)}")
    rule("S1 hook uses a reference frame", any(re.search(rx, sents[0]) for rx in HOOK), sents[0])
    if title:
        rule("the hook does not name the painting", title.lower() not in sents[0].lower())
    ii = next((i for i in (1, 2) if i < n and (re.match(IDENT_A, sents[i]) or re.match(IDENT_B, sents[i]))), None)
    rule("IDENT in sentence 2 (or 3): 'This is <Title>, painted by <Artist> in <year>.' or 'In <time>, a <role> named <Name> ...'", ii is not None, sents[1])
    rule("the last sentence is a question", sents[-1].endswith("?"), sents[-1])
    you = len(YOU.findall(text))
    q = [i for i, s in enumerate(sents) if s.endswith("?")]
    if form == "emotion":
        rule("mean sentence <= 10 words", words / n <= 10, f"{words / n:.1f}")
        if punch:
            rule("the punch word (the feeling) is said in the script", re.search(rf"\b{re.escape(punch.lower())}\b", text.lower()), punch)
        it = find(TURN, 2)
        rule("E5 TURN 'But look at <his | her> <face | eyes>.' in the first third", it is not None and it <= n // 3 + 1, sents[it] if it is not None else "missing")
        three = [i for i, s in enumerate(sents) if THREE.match(s) and wc[i] <= 7]
        rule("E4 and E9: two three-beat lines ('<A>, <B>, almost <C>.' / 'A <adj>, <adj>, <adj> <feeling>.')", len(three) >= 2, " / ".join(sents[i] for i in three) or "missing")
        rule("E7 DOUBT begins 'Yet' or 'And yet'", find(r"^(And )?[Yy]et\b", 2) is not None)
        rule("E8 SECOND LOOK: a second 'Look ...' sentence", len([s for s in sents if re.match(r"^(But )?[Ll]ook\b", s)]) >= 2)
        rule("E10 a sentence beginning 'As if'", find(r"^(Almost )?[Aa]s if\b") is not None)
        ib = find(r"^(And )?[Aa]ccording to\b", 2)
        rule("E11 BACKSTORY opens with 'According to <source>, ...'", ib is not None)
        ip = find(r"^Not\b.*\bbut\b", ib or 2)
        rule("E12 THE MOMENT: 'Not <the event>, but what comes after.' then 'The moment when ...'", ip is not None and ip + 1 < n and re.match(r"^The moment (when|that)\b", sents[ip + 1]),
             sents[ip] if ip is not None else "missing")
        im = find(r"^(But )?[Ii]magine\b", ib or 2)
        rule("E13 EMPATHY: 'Imagine ...' and then three questions in a row ('Would you ...? Would you ...? Or would you ...?')",
             im is not None and all(im + k < n and sents[im + k].endswith("?") for k in (1, 2, 3)) and re.match(r"^Or would you\b", sents[im + 3] if im is not None and im + 3 < n else ""),
             " ".join(sents[im:im + 4]) if im is not None else "missing")
        mk = find(MARK, im or 2)
        rule("E14 MARKER after the empathy (\"That's what makes this painting so disturbing.\")", mk is not None)
        rule("E15 REVEAL: '... says one thing, ... says another.' within three sentences of the marker",
             mk is not None and any(re.search(r"says one thing", sents[j]) for j in range(mk + 1, min(n, mk + 4))))
        maybe = [i for i, s in enumerate(sents) if re.match(r"^(Maybe|Perhaps)\b", s)]
        rule("E17 THE IDEA: two sentences beginning 'Maybe', the second a chain ('begins with ..., then ..., and ... turns into ...')",
             len(maybe) >= 2 and any(sents[i].count(",") >= 2 for i in maybe), " / ".join(sents[i] for i in maybe) or "missing")
        ir = find(r"^So look at (him|her|it|them|this \w+) (one more time|once more|again)\.$")
        rule("E18 RETURN: 'So look at <him | her> one more time.'", ir is not None and ir >= n - 3)
        rule("E19 QUESTION: the last two sentences are questions, the last begins 'Or'", n - 2 in q and re.match(r"^Or\b", sents[-1]), " ".join(sents[-2:]))
        rule("'you' / 'your' at least six times (the reference: 7)", you >= 6, f"{you}")
    elif form == "scene":
        rule("C3 FIRST GLANCE begins 'At first glance,'", find(r"^At first glance,") is not None)
        think = len(re.findall(r"\byou think\b", text, re.I))
        rule("C4 WHAT YOU THINK: 'you think' at least twice", think >= 2, f"{think}")
        idr = find(r"^But then your eyes\b")
        rule("C5 DRIFT: 'But then your eyes begin to drift.' and a sentence with 'past ..., past ...'", idr is not None and any(len(re.findall(r"\bpast\b", sents[j])) >= 2 for j in range(idr, min(n, idr + 3))))
        rule("C6 IMPACT begins 'And that is when'", find(r"^And that is when\b", idr or 0) is not None)
        rule("C7 THE SECOND THING begins 'Because'", find(r"^Because\b", idr or 0) is not None)
        tri = next((i for i in range(2, n - 2) if all(NEG.search(sents[j]) or re.match(r"^Nor\b", sents[j]) for j in (i, i + 1, i + 2)) and all(wc[j] <= 12 for j in (i, i + 1, i + 2))), None)
        rule("C8 TRIAD: three sentences with negatives in a row, then 'Instead, ...'", tri is not None and find(r"^Instead,", tri) is not None)
        ia = find(r"^There (are|is) no\b", tri or 0)
        rule("C9 ABSENCE: 'There are no ..., no ..., and no ...' then 'Just ...'", ia is not None and ia + 1 < n and re.match(r"^Just\b", sents[ia + 1]))
        rule("C10 TITLE FLIP 'And it is right there that ...' or a marker", find(r"^And it is right there that\b") is not None or find(MARK) is not None)
        fo = find(r"^For (him|her|them|the \w+)\b")
        rule("C11 TWO MEANINGS: 'For <him>, ...' then 'But for <her>, ...'", fo is not None and fo + 1 < n and re.match(r"^But for\b", sents[fo + 1]))
        rule("C13 QUESTION has 'you'", bool(YOU.search(sents[-1])), sents[-1])
        rule("'you' / 'your' at least ten times", you >= 10, f"{you}")
        rule("never two sentences over 22 words in a row", not any(wc[i] > 22 and wc[i + 1] > 22 for i in range(n - 1)))
    else:                                                               # legend
        rule("L2 IDENT is the story form 'In <time>, a <role> named <Name> ...'", ii is not None and re.match(IDENT_B, sents[ii]), sents[1])
        if punch:
            rule("L1 ends on the punch word (the red word on screen)", re.sub(r"\W", "", sents[0].split()[-1]).lower() == punch.lower(), sents[0].split()[-1])
        rule("L3 THE STORY begins 'One night,' or 'That night,'", find(r"^(One|That) night,") is not None)
        rule("L3 has 'But instead of ..., ...'", find(r"^But instead of\b") is not None)
        rule("L3 has a sentence of two or three words", any(w <= 3 for w in wc[2:]))
        mk = find(MARK, 3)
        rule("L5 MARKER 'But here's the disturbing part.'", mk is not None)
        rule("L6 HONESTY: 'Of course, we cannot know whether ...' and 'The story comes from <source>.'", find(r"\bwe cannot know\b", mk or 0) is not None and find(r"^The story comes from\b", mk or 0) is not None)
        rule("L7 EMPATHY begins 'But imagine' and says 'you'", (lambda i: i is not None and YOU.search(sents[i]))(find(r"^But imagine\b", mk or 0)))
        rule("L8 ASK: 'So let me ask you something.'", n >= 2 and re.match(r"^So let me ask you something\.$", sents[-2]), sents[-2] if n >= 2 else "")
        rule("L9 QUESTION: 'If ..., would you ..., or would you ...?'", re.match(r"^If\b", sents[-1]) and len(re.findall(r"\bwould you\b", sents[-1], re.I)) >= 2, sents[-1])
    rule("no semicolons, dashes, brackets, exclamation marks", not re.search(r"[;—–()\[\]!]", text))
    rule("no digits except one year", len(re.findall(r"\d+", text)) <= 1, " ".join(re.findall(r"\d+", text)), hard=False)
    rule("banned words absent", not re.search(r"\b(masterpiece|iconic|delve|tapestry|testament|breathtaking|um|subscribe|like and)\b", text, re.I))
    return out, words, n


def check(sents, title="", punch=None, form="riddle"):
    if form in ("emotion", "scene", "legend"):
        return check_form(sents, title, punch, form)
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
    # v1.02: two idents, both name WHO and WHEN in the second sentence (5 of 5 references; the card + portrait play over it)
    ident_a = re.match(r"^This is .+, (painted|drawn|engraved|carved|sculpted|made|written|composed) by .+\.$", sents[1])
    ident_b = re.match(r"^In (the |about |around )?[\w' -]{2,40}, an? .{3,60} (named|called) [A-Z].+\.$", sents[1])
    rule("S2 names who and when: 'This is <Title>, painted by <Artist> in <year>.' or 'In <time>, a <role> named <Name> ...'", bool(ident_a or ident_b), sents[1])
    rule("S2 is 9-20 words", 9 <= wc[1] <= 20, f"{wc[1]}")
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
    form = a[a.index("--form") + 1] if "--form" in a else "riddle"
    res, words, n = check(sentences(text), title, punch, form)
    for ok, hard, name, detail in res:
        print(("OK  " if ok else "FAIL" if hard else "warn"), name, ("| " + detail) if detail and not ok else "")
    bad = sum(1 for ok, hard, _, _ in res if not ok and hard)
    print(f"{words} words, {n} sentences, {bad} hard failures")
    sys.exit(1 if bad else 0)

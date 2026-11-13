#!/usr/bin/env python3
"""director.py — a script becomes a story the renderer can shoot (v1.02).

    python director.py scripts/<id>.json stories/<id>.json

The writer (docs/WRITER_PROMPT.md) delivers sentences in the fixed slots, the list of things visible in the lead
picture (LOOK: name, box, the words that name it) and the side pictures (the portrait of the person named in S2, the
"evidence": a score, a document, a place, another picture of the same scene). The director turns that into the
approved maket, the same way for every video:
  S1 HOOK    jump cuts to the things the hook names, a glide out so the red punch word lands on the wide picture
  S2 IDENT   the lead picture shrinks to a card on the stars, the person's portrait card pushes in, white flash
  S3-S13     THE PICTURE-WORD RULE as a mechanism: whenever a word names a thing of LOOK (or of an evidence
             picture) and the camera is not on it, a cue is written that takes the camera there ON that word
             (a glide; a cut in the hook, in the reveal and between pictures). Marker and question get their moves.
render.py then audits every named word against the real voice timing and refuses the video if one is off screen.
"""
import json, re, sys
from pathlib import Path

BEAT = {"S1": "hook", "S2": "ident", "S3": "setup", "S4": "turn", "S5": "detail", "S6": "triad", "S7": "backstory", "S8": "backstory",
        "S9": "backstory", "S10": "reveal", "S11": "reveal", "S12": "reveal", "M": "reveal", "X": "backstory", "S13": "question"}
JOIN = {"and", "but", "or", "with", "that", "because", "after", "before", "when", "while", "who", "which", "so", "yet", "if", "as", "until"}
norm = lambda w: re.sub(r"[^\w'’]", "", w).lower().replace("’", "'")


SOFT = {"was", "is", "are", "were", "has", "had", "have", "by", "in", "at", "for", "from", "into", "on", "of", "over", "under", "behind", "toward",
        "a", "an", "the", "his", "her", "their", "this", "these", "one", "no", "not", "only", "still", "almost", "just", "simply",
        "he", "she", "they", "it", "nobody", "nothing", "everyone", "someone", "something", "what", "how", "why", "where"}
TAIL = {"a", "an", "the", "of", "to", "by", "in", "at", "for", "his", "her", "their", "and", "but", "or", "with", "was", "is", "are", "were", "that", "had", "has", "have", "be", "been"}


def split_lines(text, lo=3, hi=9):
    """Caption lines of 3-9 words: at commas first, then before a joining word (and, that, because ...) or, failing
    that, before a preposition, an article or an auxiliary, nearest to an even split. A name is never cut and a line
    never ends on "the" or "of"."""
    parts, out = [p.strip() for p in re.split(r"(?<=[,:])\s+", text.strip()) if p.strip()], []
    for p in parts:                                                    # glue crumbs to a neighbour
        if out and (len(out[-1].split()) < lo or len(p.split()) < lo) and len(out[-1].split()) + len(p.split()) <= hi:
            out[-1] += " " + p
        else:
            out.append(p)
    res = []
    for p in out:
        ws = p.split()
        while len(ws) > hi:
            tgt = len(ws) / -(-len(ws) // 7)
            rank = lambda i: 3 if (ws[i - 1][:1].isupper() and ws[i][:1].isupper() and i > 1) or norm(ws[i - 1]) in TAIL else 0 if norm(ws[i]) in JOIN else 1 if norm(ws[i]) in SOFT else 2
            best = min(range(lo, min(hi, len(ws) - lo) + 1), key=lambda i: (rank(i), abs(i - tgt)))
            res.append(" ".join(ws[:best]))
            ws = ws[best:]
        res.append(" ".join(ws))
    return res


def inside(a, b):
    """Share of box a that lies in box b."""
    iw, ih = max(0, min(a[2], b[2]) - max(a[0], b[0])), max(0, min(a[3], b[3]) - max(a[1], b[1]))
    return iw * ih / max(1e-9, (a[2] - a[0]) * (a[3] - a[1]))


def build(script):
    area = lambda b: (b[2] - b[0]) * (b[3] - b[1])
    look, ev = script["look"], script.get("evidence", [])
    focus = {l["name"]: l["box"] for l in look}
    images = {"main": dict(script["lead"]), "portrait": {k: v for k, v in script["portrait"].items() if k != "of"}}
    if not (images["portrait"].get("commons") or images["portrait"].get("file")):
        images["portrait"]["find"] = {"portrait_of": script["portrait"]["of"]}      # sources.py looks it up (Wikidata P18)
    words = {}                                                         # word -> targets, the tightest / first listed first
    for l in look:
        for w in l.get("words", []):
            words.setdefault(w.lower(), []).append(l["name"])
    for e in ev:
        im = {k: e[k] for k in ("commons", "file", "crop", "license", "credit", "width_px") if k in e}
        if not (im.get("commons") or im.get("file")) and e.get("query"):
            im["find"] = {"query": e["query"]}
        im["focus"] = {l["name"]: l["box"] for l in e.get("look", [])}
        images[e["key"]] = im
        for w in e.get("words", []):                                   # "Villa Medici" -> villa, medici
            for tok in [norm(x) for x in w.split() if len(norm(x)) > 3]:
                words.setdefault(tok, []).append(f"{e['key']}:full")
        for l in e.get("look", []):
            for w in l.get("words", []):
                words.setdefault(w.lower(), []).append(f"{e['key']}:{l['name']}")

    def allowed(targets):
        """A thing is on screen in its own box, in any bigger box that holds it, and in the whole picture when it is big."""
        out = list(targets)
        for t in targets:
            if ":" in t:
                continue
            for n, b in focus.items():
                if n not in out and inside(focus[t], b) > 0.9 and area(focus[t]) / area(b) >= 0.2:
                    out.append(n)
            if area(focus[t]) >= 0.12 and "full" not in out:
                out += ["full", "card"]
        return out

    names = {w: allowed(t) for w, t in words.items()}
    person = [norm(x) for x in re.split(r"[\s-]+", script["portrait"]["of"]) if x[:1].isupper()]

    lines, cur, sents = [], ("main", "full"), script["sentences"]
    for si, s in enumerate(sents):
        slot = s["slot"]
        chunks = split_lines(s["text"])
        if slot == "S6" and lines and lines[-1]["beat"] == "triad" and len(lines[-1]["say"].split()) + len(s["text"].split()) <= 8 and not lines[-1].get("_joined"):
            lines[-1]["say"] += " " + s["text"]                        # two short triad sentences share a caption
            lines[-1]["_joined"] = True
            chunks = []
        shows = {norm(x["on"]): x["to"] for x in s.get("show", [])}
        for li, say in enumerate(chunks):
            ln, cues, toks = {"beat": BEAT[slot], "say": say}, [], [norm(w) for w in say.split()]
            first, last_line = li == 0, li == len(chunks) - 1

            def go(target, on=None, how=None, **kw):
                nonlocal cur
                sc, box = target.split(":") if ":" in target else ("main", target)
                c = dict(kw)
                if sc != cur[0]:
                    c["scene"] = sc
                c["to"] = box
                if how == "cut" and "scene" not in c:
                    c["how"] = "cut"
                if on:
                    c["on"] = on
                cues.append(c)
                cur = (sc, box)

            if slot == "S2":                                           # the ident: card on the stars, then the portrait
                if first:
                    cues += [{"to": "full", "how": "cut", "at": 0.14}, {"to": "card", "at": 0.5}]
                    cur = ("main", "card")
                hit = next((t for t in toks if t in person), None)
                if hit and not any("image" in c for l_ in lines if l_["beat"] == "ident" for c in (l_.get("cam") if isinstance(l_.get("cam"), list) else [l_.get("cam") or {}])):
                    cues.append({"image": "portrait", "on": hit})
                    ln["names"] = {t: ["portrait"] for t in toks if t in person}    # only here: later the name alone asks for nothing
                    cur = ("portrait", "")
                elif cur[0] == "portrait":                             # the sentence goes on after the portrait
                    go("main:full", how="cut", push=True)
            else:
                if cur[0] == "portrait" or (first and slot in ("S3", "S10")) or (first and cur[0] != "main" and not any(t in shows or t in words for t in toks)):
                    if cur[0] != "main":
                        cues.append({"scene": "main", "to": "full", "push": True})
                    else:
                        cues.append({"to": "full", "how": "cut", "push": True})
                    cur = ("main", "full")
                if first and slot == "S13" and cur != ("main", "full"):
                    go("main:full")                                    # the question pulls back to the whole picture
                wide_for = None
                if slot == "S1" and last_line and len(toks) >= 3:      # the hook's last named thing arrives with the glide out
                    j = next((k for k in range(len(toks) - 1, max(len(toks) - 3, -1), -1) if toks[k] in names or toks[k].split("'")[0] in names), None)
                    if j is not None:
                        al = names.get(toks[j]) or names.get(toks[j].split("'")[0])
                        wide_for = (j, "full" if "full" in al else max((a for a in al if ":" not in a and a in focus), key=lambda a: area(focus[a]), default=None))
                for ti, t in enumerate(toks):
                    if wide_for and ti == wide_for[0] and wide_for[1]:
                        continue
                    base = t.split("'")[0]
                    key = t if (t in shows or t in names) else base
                    target = shows.get(key) or (None if key not in words else next((x for x in words[key]), None))
                    if not target or (slot == "S13" and key not in shows and (cur[1] in names.get(key, []) or "full" in names.get(key, []))):
                        continue
                    here = cur[1] if cur[0] == "main" else f"{cur[0]}:{cur[1]}"
                    if key in shows:                                   # a show holds for this line only (render.py reads line names first)
                        ln.setdefault("names", {})[key] = [target]
                    nxt = next((x for x in toks[ti + 1:ti + 3] if x in shows or x in words), None)
                    if t.endswith("'s") and key not in shows and nxt:  # "the sleeper's hands": the part stands for its owner
                        ln.setdefault("names", {})[t] = names.get(key, []) + [shows.get(nxt) or words[nxt][0]]
                        continue
                    small = ":" not in target and area(focus[target]) < 0.4   # the whole picture does not count as "on it" for a small thing
                    if key not in shows and here in names.get(key, []) and not (here == "full" and small and slot != "S13"):
                        continue                                       # the camera is already on it
                    if here == target:
                        continue
                    if ti <= 1 and cues and cues[-1].get("push") and cur == ("main", "full") and ":" not in target:
                        cues[-1] = {"to": target, "how": "cut"}        # the sentence opens on the thing it names first
                        cur = ("main", target)
                        continue
                    go(target if ":" in target else "main:" + target, on=t, how="cut" if slot in ("S1", "S11") else None)
                if slot == "S1" and last_line and len(toks) >= 3:      # glide out: the red word lands on the wide picture
                    wide = wide_for[1] if wide_for and wide_for[1] else "full"
                    if wide != cur[1] or cur[0] != "main":
                        cues.append({"to": wide, "on": toks[-2]})
                        cur = ("main", wide)
            if slot == "S1" and first and not cues:                   # the hook never opens on the whole picture: a crop within two seconds
                tight = [l["name"] for l in look if area(l["box"]) < 0.4]
                pick = next((n for n in tight if re.search(r"(face|top|upper|head)", n)), tight[0] if tight else None)
                if pick:
                    cues.append({"to": pick, "how": "cut"})
                    cur = ("main", pick)
            if slot in ("S4", "S10") and first:
                ln["accent"] = True
            if slot == "S10" and first:
                ln["pause_before"] = 0.4
            if slot == "S13" and first:
                ln["pause_before"] = 0.2
            if cues:
                ln["cam"] = cues[0] if len(cues) == 1 else cues
            lines.append(ln)
    for l in lines:
        l.pop("_joined", None)
    sub = script["subject"]
    return {"schema": 1, "id": script["id"], "template": "painting", "kind": script.get("kind", "artwork"), "priority": script.get("priority", 10),
            "artwork": {"title": sub["title"], "artist": sub["creator"], "year": sub["year"], "collection": sub.get("collection"), "wikidata": sub.get("wikidata")},
            "images": images, "focus": focus, "names": names, "hook_title": script["punch"].upper(), "lines": lines,
            "pronounce": script.get("pronounce", {}), "music": {"mood": ["dark", "ambient", "humming"], "file": None},
            "meta": script["meta"], "sources": script.get("sources", [])}


if __name__ == "__main__":
    story = build(json.loads(Path(sys.argv[1]).read_text(encoding="utf-8")))
    Path(sys.argv[2]).write_text(json.dumps(story, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"{sys.argv[2]}: {len(story['lines'])} lines, {sum(1 for l in story['lines'] if l.get('cam'))} with camera cues, {len(story['names'])} named words, pictures: {', '.join(story['images'])}")

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

v1.12 (Andrii, Nov 15, after the reference's own Fallen Angel was laid beside ours: 'виправи всі недоліки ... щоб
відео були максимально схожі на референс'):
  - FORMS. A script says which construction it is: riddle (the 13 slots above), emotion (E1-E19), scene (C1-C13),
    legend (L1-L9); prompts/writer.txt section 3. scene and legend are shot by the mechanism above, slot by slot.
  - FACE LOCK (form emotion): the reference holds the figure's face for 90 % of its 114 seconds. The video opens on
    the face, the whole picture is seen only as the ident card, the camera glances at other things only while the
    contrast names them, goes to the small detail when it is named, and otherwise breathes between three scales of
    the same face (home, mid, detail). The face stands for the figure: "the angel" does not pull the camera back.
  - PAUSES BY MEANING: the long pauses stand before the turns of thought (format.json timing.meaning), and the
    three-beat lines ("<A>, <B>, almost <C>.") are spoken and shown one beat at a time.
  - Geo: the director now does the renderer's own arithmetic (which framing really shows which box), so "the camera
    is already on it" is decided by what is in the frame, not by the name of the box. Needs the picture's aspect.
"""
import json, re, sys
from pathlib import Path

BEAT = {"S1": "hook", "S2": "ident", "S3": "setup", "S4": "turn", "S5": "detail", "S6": "triad", "S7": "backstory", "S8": "backstory",
        "S9": "backstory", "S10": "reveal", "S11": "reveal", "S12": "reveal", "M": "reveal", "X": "backstory", "S13": "question",
        # v1.12 emotion (render.py reads only "hook" and "ident"; the other names are for the timeline and the lessons)
        "E1": "hook", "E2": "ident", "E3": "contrast", "E4": "beats", "E5": "turn", "E6": "detail", "E7": "doubt", "E8": "look", "E9": "beats",
        "E10": "feeling", "E11": "backstory", "E12": "moment", "E13": "empathy", "E14": "marker", "E15": "reveal", "E16": "marker", "E17": "idea",
        "E18": "return", "E19": "question",
        "C1": "hook", "C2": "ident", "C3": "glance", "C4": "think", "C5": "drift", "C6": "impact", "C7": "second", "C8": "triad", "C9": "absence",
        "C10": "flip", "C11": "meanings", "C12": "painter", "C13": "question",
        "L1": "hook", "L2": "ident", "L3": "story", "L4": "aftermath", "L5": "marker", "L6": "honesty", "L7": "empathy", "L8": "ask", "L9": "question",
        # v1.15 investigation and twist
        "I1": "hook", "I2": "ident", "I3": "case", "I4": "clue", "I5": "clue", "I6": "clue", "I7": "answer", "I8": "more", "I9": "question",
        "H1": "hook", "H2": "loop", "H3": "tour", "H4": "who", "H5": "stakes", "H6": "rehook", "H7": "fact", "H8": "flip", "H9": "question",
        "T1": "hook", "T2": "ident", "T3": "usual", "T4": "seems", "T5": "turn", "T6": "detail", "T7": "fact", "T8": "flip", "T9": "question"}
# v1.12: scene and legend are shot by the riddle's mechanism: each of their slots moves the camera like this slot of the riddle
LEGACY = {"C1": "S1", "C2": "S2", "C3": "S3", "C4": "S5", "C5": "S4", "C6": "S10", "C7": "S11", "C8": "S6", "C9": "S7", "C10": "S10", "C11": "S11",
          "C12": "S12", "C13": "S13", "L1": "S1", "L2": "S2", "L3": "S3", "L4": "X", "L5": "S10", "L6": "S12", "L7": "M", "L8": "M", "L9": "S13",
          # v1.15: a clue names things like the riddle's detail; the answer moves like the reveal; the fact like the backstory
          "I1": "S1", "I2": "S2", "I3": "S3", "I4": "S5", "I5": "S5", "I6": "S5", "I7": "S11", "I8": "S9", "I9": "S13",
          "H1": "S1", "H2": "S3", "H3": "S5", "H4": "S5", "H5": "S7", "H6": "S10", "H7": "S5", "H8": "S11", "H9": "S13",
          "T1": "S1", "T2": "S2", "T3": "S3", "T4": "S3", "T5": "S4", "T6": "S5", "T7": "S7", "T8": "S11", "T9": "S13"}
F = json.loads((Path(__file__).resolve().parent / "format.json").read_text(encoding="utf-8"))
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


class Geo:
    """What a framing shows, by the renderer's own arithmetic (render.Camera.rect and focus_audit), in picture widths."""

    def __init__(self, focus, aspect, px=3840, macro=()):
        C = F["camera"]
        self.focus, self.macro, self.R, self.m = focus, set(macro), C["focus_rule"], C["focus_margin"]
        self.a = min(F["canvas"]["stage_aspect_max"], max(F["canvas"]["stage_aspect_min"], aspect))
        self.H = 1.0 / aspect
        self.full_w = min(1.0, self.H * self.a)
        stage = F["canvas"]["w"] / max(600, px)                       # the stage's width in picture widths, pixel for pixel
        self.min_w = max(self.full_w / C["zoom"]["max"], stage / 2.0)
        self.min_macro = max(self.full_w / C["zoom"]["macro"], stage * C["zoom"]["macro_min_stage_share"])

    def rect(self, name):
        if name in ("full", "card"):
            cx, cy, w = 0.5, self.H / 2, self.full_w
        else:
            x0, y0, x1, y1 = self.focus[name]
            w = min(max(max(x1 - x0, (y1 - y0) * self.H * self.a) * (1 + 2 * self.m), self.min_macro if name in self.macro else self.min_w), self.full_w)
            cx, cy = (x0 + x1) / 2, (y0 + y1) / 2 * self.H
        h = w / self.a
        if w <= 1.0:
            cx = min(max(cx, w / 2), 1.0 - w / 2)
        if h <= self.H:
            cy = min(max(cy, h / 2), self.H - h / 2)
        return cx, cy, w

    def sees(self, frame, box):
        """Would the audit accept `box` while the camera rests on the framing `frame`? The whole picture is judged
        as it looks after its slow push-in (1.3x), which is how a line spoken a few seconds later finds it."""
        if frame == "card" or box not in self.focus:
            return False
        cx, cy, w = self.rect(frame)
        if frame == "full":
            w /= F["camera"]["zoom"]["full_view_push"]["to"]
        h, (x0, y0, x1, y1) = w / self.a, self.focus[box]
        iw, ih = max(0.0, min(x1, cx + w / 2) - max(x0, cx - w / 2)), max(0.0, min(y1 * self.H, cy + h / 2) - max(y0 * self.H, cy - h / 2))
        area = (x1 - x0) * (y1 - y0) * self.H
        return area > 0 and iw * ih / area >= self.R["box_inside_min"] and (iw * ih / (w * h) >= self.R["box_share_of_frame_min"] or w <= self.min_w * 1.08)


def geo_of(script, focus, macro=()):
    lead = script.get("lead") or {}
    return Geo(focus, lead["aspect"], min(lead.get("width_px") or 3840, lead.get("px") or 3840), macro) if lead.get("aspect") else None


def allowed_for(targets, focus):
    """A thing is on screen in its own box, in any bigger box that holds it, and in the whole picture when it is big."""
    area, out = lambda b: (b[2] - b[0]) * (b[3] - b[1]), list(targets)
    for t in targets:
        if ":" in t:
            continue
        for n, b in focus.items():
            if n not in out and inside(focus[t], b) > 0.9 and area(focus[t]) / area(b) >= 0.2:
                out.append(n)
        if area(focus[t]) >= 0.12 and "full" not in out:
            out += ["full", "card"]
    return out


def finish(script, images, focus, names, lines, **more):
    """The story the renderer reads."""
    for l in lines:
        l.pop("_joined", None)
    sub = script["subject"]
    return dict({"schema": 1, "id": script["id"], "template": "painting", "kind": script.get("kind", "artwork"), "form": script.get("form") or "riddle",
                 "priority": script.get("priority", 10),
                 "artwork": {"title": sub["title"], "artist": sub["creator"], "year": sub["year"], "collection": sub.get("collection"), "wikidata": sub.get("wikidata")},
                 "images": images, "focus": focus, "names": names, "hook_title": script["punch"].upper(), "lines": lines,
                 "sentences": [s["text"].strip() for s in script["sentences"]],
                 "pronounce": script.get("pronounce", {}), "music": {"mood": ["dark", "ambient", "humming"], "file": None},
                 "meta": script["meta"], "sources": script.get("sources", [])}, **more)


SCALE = {"E3": ["home", None], "E5": ["home"], "E6": ["detail", None], "E7": ["mid"], "E8": ["home", "mid"], "E10": ["home"], "E11": ["home"],
         "E12": ["home", "mid", None], "E13": ["home", None, "mid", None], "E14": ["home"], "E15": [None, None], "E16": ["home"], "E17": ["home", "mid"],
         "E18": ["home"], "E19": ["home", "detail"]}
CUTS = {"E3", "E14", "E18"}


def build_lock(script):
    """FORM emotion: the camera holds the face (see the module's notes on v1.12)."""
    M, look = F["timing"]["meaning"], script["look"]
    focus = {l["name"]: list(l["box"]) for l in look}
    home, tight = script["home"], script["detail"]
    k_mid = F["camera"]["face_lock"]["mid_share_of_detail"]            # the middle scale: 35 % of the way from the face to the detail
    focus["_mid"] = [round(a + (b - a) * k_mid, 4) for a, b in zip(focus[home], focus[tight])]
    scale = {"home": home, "mid": "_mid", "detail": tight}
    family = [home, "_mid", tight]
    geo = geo_of(script, focus, macro=["_mid", tight])        # both may pass the usual 3.6: the face itself is already there
    images = {"main": dict(script["lead"]), "portrait": {k: v for k, v in script["portrait"].items() if k != "of"}}
    if not (images["portrait"].get("commons") or images["portrait"].get("file")):
        images["portrait"]["find"] = {"portrait_of": script["portrait"]["of"], "work": (script.get("subject") or {}).get("wikidata")}
    words = {}
    for l in look:
        for w in l.get("words", []):
            words.setdefault(w.lower(), []).append(l["name"])
    figure = {w.lower() for l in look if inside(focus[home], l["box"]) > 0.9 for w in l.get("words", [])}   # the face stands for the figure
    names = {w: allowed_for(t, focus) + ([x for x in family if x not in t] if w in figure else []) for w, t in words.items()}
    person = [norm(x) for x in re.split(r"[\s-]+", script["portrait"]["of"]) if x[:1].isupper()]
    title_words = {norm(x) for x in re.split(r"[\s-]+", (script.get("subject") or {}).get("title", "")) if x}    # v1.24
    on_screen = lambda here, key: here in names[key] if geo is None else any(geo.sees(here, b) for b in names[key] if b in focus)

    lines, cur, sents, shown_portrait = [], "_mid", script["sentences"], False
    idx = {}                                                           # how many sentences of this slot came before
    for s in sents:
        code = s["slot"]
        k = idx.get(code, 0)
        idx[code] = k + 1
        text = re.sub(r"\b[A-Z]{3,}\b", lambda m: m.group(0).lower(), s["text"]).strip()
        beats = code in ("E4", "E9")
        chunks = [p.strip() + ("," if i < text.count(",") else "") for i, p in enumerate(text.split(","))] if beats else split_lines(text)
        shows = {norm(x["on"]): x["to"] for x in s.get("show", [])}
        for li, say in enumerate(chunks):
            ln, cues, toks = {"beat": BEAT.get(code, "reveal"), "say": say}, [], [norm(w) for w in say.split()]
            first, last_line = li == 0, li == len(chunks) - 1

            def go(to, on=None, cut=False, **kw):
                nonlocal cur
                if to == cur and "scene" not in kw:
                    return
                c = dict(kw, to=to)
                if cut and "scene" not in c:
                    c["how"] = "cut"
                if on:
                    c["on"] = on
                cues.append(c)
                cur = to

            if code == "E2":                                           # the ident: the whole picture, the card on the stars, the portrait
                if first:
                    cues += [{"to": "full", "how": "cut", "at": 0.14}, {"to": "card", "at": 0.5}]
                    cur = "card"
                hit = next((t for t in toks if t in person), None)
                if hit and not shown_portrait:
                    cues.append({"image": "portrait", "on": hit})
                    ln["names"] = {t: ["portrait"] for t in toks if t in person}
                    shown_portrait, cur = True, "portrait"
                for t in toks:                                         # v1.24: the title's words in the ident are shown by the whole picture and the card
                    if t in title_words and (t in words or t.split("'")[0] in words) and t not in ln.get("names", {}):
                        ln.setdefault("names", {})[t] = ["full", "card"]
            else:
                if cur in ("portrait", "card", "full"):                # back from the card: straight to the face, never to the whole picture
                    cues.append({"scene": "main", "to": home})
                    cur = home
                elif first and cur not in family:                      # a glance at something else ends with its sentence
                    go(home, cut=True)
                want = (SCALE.get(code) or [None])[min(k, len(SCALE.get(code) or [None]) - 1)] if first else None
                if beats:
                    want = ["home", "mid", None][min(li, 2)] if code == "E4" else ["mid", None, "home"][min(li, 2)]
                if code == "E1":                                       # the hook: the face, then closer, and the red word lands there
                    want = "detail" if (last_line and len(chunks) > 1) else None
                    if len(chunks) == 1 and first:
                        cues.append({"to": tight, "how": "cut", "at": 0.5})
                        cur = tight
                moved = False
                for ti, t in enumerate(toks):
                    key = t if (t in shows or t in words) else t.split("'")[0]
                    if key in shows:
                        tgt = shows[key]
                        ln.setdefault("names", {})[key] = [tgt]
                    elif key in words:
                        if words[key][0] == tight and cur != tight:     # the small thing is named: go and show it large, whatever the frame holds
                            go(tight, on=t, cut=code in ("E1", "E3"))
                            moved = True
                            continue
                        if on_screen(cur, key):
                            continue
                        tgt = next((b for b in names[key] if b in family), words[key][0]) if key in figure else words[key][0]
                    else:
                        continue
                    if tgt == cur:
                        continue
                    go(tgt, on=t, cut=code in ("E1", "E3", "E15"))
                    moved = True
                if want and not moved:
                    go(scale[want], cut=code in CUTS and first, **({} if code in CUTS else {"push": True} if want == "home" else {}))
            # the sound and the silences
            if code in ("E5", "E14") and first:
                ln["accent"] = True
            if code in ("E14", "E16") and first:
                ln["pause_before"] = 0.4
            if beats and not last_line:
                ln["pause"] = M["three_beat_first_s"] if li == 0 else M["three_beat_next_s"]
            if code == "E5" and last_line:
                ln["pause"] = M["after_turn_s"]
            if code == "E11" and first:
                ln["pause_before"] = M["backstory_before_s"]
            if code == "E12" and k == 1:
                if first:
                    ln["pause_before"] = M["pivot_before_s"]
                if not last_line:
                    ln["pause"] = M["pivot_inner_s"]
            if code == "E13" and first and k in (0, 3):
                ln["pause_before"] = M["imagine_before_s"] if k == 0 else M["third_question_before_s"]
            if code == "E18" and last_line:
                ln["pause"] = M["return_after_s"]
            if code == "E19" and first and k == 0:
                ln["pause_before"] = 0.2
            if cues:
                ln["cam"] = cues[0] if len(cues) == 1 else cues
            lines.append(ln)
    return finish(script, images, focus, names, lines, open="_mid", macro=["_mid", tight], home=home)


def inside(a, b):
    """Share of box a that lies in box b."""
    iw, ih = max(0, min(a[2], b[2]) - max(a[0], b[0])), max(0, min(a[3], b[3]) - max(a[1], b[1]))
    return iw * ih / max(1e-9, (a[2] - a[0]) * (a[3] - a[1]))


def build(script):
    if script.get("form") == "emotion" and script.get("home") and script.get("detail"):
        return build_lock(script)
    area = lambda b: (b[2] - b[0]) * (b[3] - b[1])
    look, ev = script["look"], script.get("evidence", [])
    focus = {l["name"]: l["box"] for l in look}
    images = {"main": dict(script["lead"]), "portrait": {k: v for k, v in script["portrait"].items() if k != "of"}}
    if not (images["portrait"].get("commons") or images["portrait"].get("file")):
        images["portrait"]["find"] = {"portrait_of": script["portrait"]["of"], "work": (script.get("subject") or {}).get("wikidata")}    # v1.11: the painting's id, so its creator wins      # sources.py looks it up (Wikidata P18)
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
    title_words = {norm(x) for x in re.split(r"[\s-]+", (script.get("subject") or {}).get("title", "")) if x}    # v1.24
    geo = geo_of(script, focus)                                        # v1.12: None for a script without the picture's aspect (before v1.12)
    really = lambda here, key: geo is None or here == "card" or (here != "full" and here not in focus) or any(geo.sees(here, b) for b in names.get(key, []) if b in focus)

    lines, cur, sents = [], ("main", "full"), script["sentences"]
    for si, s in enumerate(sents):
        code = s["slot"]
        slot = LEGACY.get(code, code)                                  # v1.12: a slot of scene or legend moves the camera like this slot of the riddle
        s = dict(s, text=re.sub(r"\b[A-Z]{3,}\b", lambda m: m.group(0).lower(), s["text"]))   # the model likes to shout the punch word: "RAGE" -> "rage"
        chunks = split_lines(s["text"])
        if slot == "S6" and lines and lines[-1]["beat"] == "triad" and len(lines[-1]["say"].split()) + len(s["text"].split()) <= 8 and not lines[-1].get("_joined"):
            lines[-1]["say"] += " " + s["text"]                        # two short triad sentences share a caption
            lines[-1]["_joined"] = True
            chunks = []
        shows = {norm(x["on"]): x["to"] for x in s.get("show", [])}
        for li, say in enumerate(chunks):
            ln, cues, toks = {"beat": BEAT.get(code, BEAT[slot]), "say": say}, [], [norm(w) for w in say.split()]
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
                for t in toks:                                         # v1.24: the title's words in the ident are shown by the whole picture and the card (Andrii, Nov 27: 'Так')
                    if t in title_words and (t in words or t.split("'")[0] in words) and t not in ln.get("names", {}):
                        ln.setdefault("names", {})[t] = ["full", "card"]
            elif script.get("form") == "hold" and not any("image" in c for l_ in lines for c in (l_.get("cam") if isinstance(l_.get("cam"), list) else [l_.get("cam") or {}])) \
                    and any(t in person for t in toks):                # v1.19, the hold form: no ident; the painter's card comes with his first name, later
                if cur[0] != "main" or cur[1] != "full":
                    cues.append({"to": "full", "how": "cut"})
                hit = next(t for t in toks if t in person)
                cues.append({"image": "portrait", "on": hit})
                ln["names"] = {t: ["portrait"] for t in toks if t in person or t.split("'")[0] in words}    # v1.22: the painter's line is shown by his portrait ('his own face on Goliath')
                cur = ("portrait", "")
            else:
                if cur[0] == "portrait" or (first and slot in ("S3", "S7", "S10")) or (first and cur[0] != "main" and not any(t in shows or t in words for t in toks)):
                    if cur[0] != "main":
                        cues.append({"scene": "main", "to": "full", "push": True})
                    else:
                        cues.append({"to": "full", "how": "cut", "push": True})
                    cur = ("main", "full")
                tight = any(t in shows or (t.split("'")[0] in words and "full" not in names.get(t.split("'")[0], [])) for t in toks)
                if first and slot == "S13" and cur != ("main", "full") and not tight:
                    go("main:full")                                    # the question pulls back to the whole picture (unless it names a detail)
                wide_for = None
                if slot == "S1" and last_line and len(toks) >= 3 and script.get("form") != "hold":      # the hook's last named thing arrives with the glide out (v1.19: the hold form stays on the eyes: Lucifer lost 36 % at 4.2 s as the camera went wide)
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
                    if not target or (slot == "S13" and key not in shows and (cur[1] in names.get(key, []) or "full" in names.get(key, []))
                                      and (cur[0] != "main" or really(cur[1], key))):    # v1.12: the question may stay where it is only if the frame really holds the thing (Nov 15: 'skull', 22 % in)
                        continue
                    here = cur[1] if cur[0] == "main" else f"{cur[0]}:{cur[1]}"
                    if key in shows:                                   # a show holds for this line only (render.py reads line names first)
                        ln.setdefault("names", {})[key] = [target]
                    nxt = next((x for x in toks[ti + 1:ti + 3] if x in shows or x in words), None)
                    if t.endswith("'s") and key not in shows and nxt:  # "the sleeper's hands": the part stands for its owner
                        ln.setdefault("names", {})[t] = names.get(key, []) + [shows.get(nxt) or words[nxt][0]]
                        continue
                    small = ":" not in target and area(focus[target]) < 0.4   # the whole picture does not count as "on it" for a small thing
                    if key not in shows and here in names.get(key, []) and not (here == "full" and small and slot != "S13") and really(here, key):
                        continue                                       # the camera is already on it (v1.12: and the frame really holds it)
                    if here == target:
                        continue
                    if ti <= 1 and cues and cues[-1].get("push") and cur == ("main", "full") and ":" not in target:
                        cues[-1] = {"to": target, "how": "cut"}        # the sentence opens on the thing it names first
                        cur = ("main", target)
                        continue
                    go(target if ":" in target else "main:" + target, on=t, how="cut" if slot in ("S1", "S11") else None)
                if slot == "S1" and last_line and len(toks) >= 3 and script.get("form") != "hold":      # glide out: the red word lands on the wide picture
                    wide = wide_for[1] if wide_for and wide_for[1] else "full"
                    if wide != cur[1] or cur[0] != "main":
                        cues.append({"to": wide, "on": toks[-2]})
                        cur = ("main", wide)
            if slot == "S6" and not cues and cur[0] == "main" and cur[1] in focus and re.search(r"\b(simply|only|just)\b", say):
                wider = [n for n, b in focus.items() if n != cur[1] and inside(focus[cur[1]], b) > 0.9 and area(b) > 1.8 * area(focus[cur[1]])]
                if wider:                                              # the triad's last beat pulls back: the detail in its owner
                    go("main:" + min(wider, key=lambda n: area(focus[n])))
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
    opening = {"open": script["home"]} if script.get("home") in focus and script.get("form") in ("scene", "hold") else {}    # v1.19: the hold form opens on the face too    # v1.12: a scene opens on the first figure's face
    return finish(script, images, focus, names, lines, **opening)


if __name__ == "__main__":
    story = build(json.loads(Path(sys.argv[1]).read_text(encoding="utf-8")))
    Path(sys.argv[2]).write_text(json.dumps(story, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"{sys.argv[2]}: {len(story['lines'])} lines, {sum(1 for l in story['lines'] if l.get('cam'))} with camera cues, {len(story['names'])} named words, pictures: {', '.join(story['images'])}")

#!/usr/bin/env python3
"""sposcaske-bot PROTOTYPE renderer v2 ("maket"): story JSON -> 1080x1920 MP4 in the measured @doom.lore format.

    python render.py stories/<id>.json out/<id>.mp4

v2 follows the frame-by-frame and sound-by-sound re-measurement of reference v1 (docs/FORMAT.md, section 16):
fade-in from black, a dark two-note stinger with the voice starting only after it, jump cuts in the hook, a noise
riser cut dead by the giant red hook word, silence, a slam + film-burn into the title card on a star field, the
painter's portrait card pushing in, a white flash with a camera shutter, music entering only after the title, a cut
to black on the last frames. Every number comes from format.json.
Prototype limits: voice = offline Kokoro only (the bot adds Azure first); template "painting" only.
"""
import json, math, os, random, re, subprocess, sys, wave
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent
F = json.loads((ROOT / "format.json").read_text(encoding="utf-8"))
CW, CH, FPS = F["canvas"]["w"], F["canvas"]["h"], F["canvas"]["fps"]
CAP_SCALE = float(os.environ.get("CAPTION_SCALE", "1.0"))      # 1.0 = the reference's proportion
FONTS = Path(os.environ.get("FONTS_DIR", ROOT / "assets/fonts"))
KOKORO = Path(os.environ.get("KOKORO_DIR", ROOT / "assets/kokoro"))
SR = 44100
T = F["timing"]


def cues(ln):
    """A line's camera cues as a list of dicts; 'at' = fraction of the line's duration (default 0)."""
    c = ln.get("cam")
    return [] if not c else (c if isinstance(c, list) else [c])


def scene_track(story, marks):
    """[(time, scene)]: which picture is on screen. A cue with "scene" cuts to that picture ("main" = the lead one)."""
    out = [(0.0, "main")]
    for ln, (t0, t1) in zip(story["lines"], marks):
        for c in cues(ln):
            if "scene" in c:
                out.append((cue_time(c, ln["say"], t0, t1) - F["camera"]["focus_rule"]["cut_lead_s"], c["scene"]))
    return sorted(out)


def word_times(say, t0, t1):
    """Estimated start of every word of a line (one synthesis call per line gives no word clock): the line's time
    shared by letters, with weight for the pause after a comma or a full stop."""
    ws = say.split()
    wt = [len(re.sub(r"\W", "", w)) + 1.5 for w in ws]
    ps = [3.0 if w[-1] in ".!?" else 1.5 if w[-1] in ",;:" else 0.0 for w in ws]
    tot, acc, out = sum(wt) + sum(ps[:-1]), 0.0, []
    for w, x, p_ in zip(ws, wt, ps):
        out.append((re.sub(r"[^\w'’]", "", w).lower(), t0 + acc / tot * (t1 - t0)))
        acc += x + p_
    return out


def cue_time(cam, say, t0, t1):
    """When a cue fires: at the word named by "on" (the picture changes as the thing is named), else at "at"."""
    if cam.get("on"):
        key = cam["on"].lower()
        hit = next((t for w, t in word_times(say, t0, t1) if w == key or w.startswith(key)), None)
        if hit is not None:
            return hit
    return t0 + cam.get("at", 0) * (t1 - t0)


# ---------------------------------------------------------------- voice
def speak_lines(story):
    """One synthesis call per line (= one caption clause): exact clause timings, pauses are ours."""
    from kokoro_onnx import Kokoro
    k = Kokoro(str(KOKORO / "kokoro-v1.0.int8.onnx"), str(KOKORO / "voices-v1.0.bin"))
    kv, clips = F["voice"]["kokoro"], []
    spec = os.environ.get("KOKORO_VOICE", kv["voice"])                 # "name" or a blend "a:0.65+b:0.35"
    parts = [(p.split(":")[0], float(p.split(":")[1]) if ":" in p else 1.0) for p in spec.split("+")]
    voice = parts[0][0] if len(parts) == 1 else sum(k.get_voice_style(n) * w for n, w in parts) / sum(w for _, w in parts)
    gap = np.zeros(int(T["pause_sentence_inner_s"] * SR), np.float32)
    for ln in story["lines"]:
        pieces = []
        for text in re.split(r"(?<=[.!?])\s+", ln["say"].strip()):       # every sentence ends in a real pause
            for a, b in story.get("pronounce", {}).items():
                text = text.replace(a, b)
            text = year_words(text)                                    # the caption keeps the digits, the voice says the halves
            y, sr = k.create(text, voice=voice, speed=kv["speed"], lang=kv["lang"])
            loud = np.nonzero(np.abs(y) > 0.02)[0]
            if len(loud):
                y = y[max(0, loud[0] - int(0.02 * sr)):loud[-1] + int(0.06 * sr)]
            n = int(len(y) * SR / sr)
            pieces += [gap] * bool(pieces) + [rough(np.interp(np.linspace(0, len(y) - 1, n), np.arange(len(y)), y).astype(np.float32))]
        clips.append(np.concatenate(pieces))
    return clips


ONES = "zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen seventeen eighteen nineteen".split()
TENS = "- - twenty thirty forty fifty sixty seventy eighty ninety".split()


def year_words(text):
    """v1.03 (Andrii: 'треба щоб він казав 18 57 а не 1857'): a year is spoken in two halves, the way people say it:
    1857 -> eighteen fifty-seven, 1805 -> eighteen oh five, 1900 -> nineteen hundred, 2004 -> two thousand four."""
    two = lambda n: ONES[n] if n < 20 else TENS[n // 10] + ("-" + ONES[n % 10] if n % 10 else "")

    def say(m):
        y = int(m.group(0))
        a, b = divmod(y, 100)
        if not 1000 <= y <= 2099:
            return m.group(0)
        if 2000 <= y <= 2009:
            return "two thousand" + (" " + ONES[b] if b else "")
        return two(a) + (" hundred" if b == 0 else " oh " + ONES[b] if b < 10 else " " + two(b))
    return re.sub(r"(?<![\d.,])\d{4}(?![\d]|,\d)", say, text)


def rough(y):
    """Lower and rougher: more chest (a low shelf), less air (a high shelf down), a little tube-style saturation."""
    R = F["voice"]["rough"]
    Y, fr = np.fft.rfft(y), np.fft.rfftfreq(len(y), 1 / SR)
    lo = 10 ** (R["low_shelf_db"] / 20 * np.clip((R["low_shelf_hz"] * 1.6 - fr) / (R["low_shelf_hz"] * 1.2), 0, 1))
    hi = 10 ** (R["high_shelf_db"] / 20 * np.clip((fr - R["high_shelf_hz"] * 0.6) / (R["high_shelf_hz"] * 0.8), 0, 1))
    y = np.fft.irfft(Y * lo * hi * (fr > 55), len(y))
    pk, d = max(1e-6, float(np.abs(y).max())), R["drive"]
    return ((1 - R["mix"]) * y + R["mix"] * pk * np.tanh(d * y / pk + R["bias"]) / np.tanh(d)).astype(np.float32)


def timeline(story, clips):
    t, marks, lines = T["lead_in_s"], [], story["lines"]
    for i, (ln, y) in enumerate(zip(lines, clips)):
        t += ln.get("pause_before", 0.0)
        d = len(y) / SR
        marks.append((t, t + d))
        last_hook = ln["beat"] == "hook" and i + 1 < len(lines) and lines[i + 1]["beat"] != "hook"
        t += d + ln.get("pause", T["pause_after_hook_s"] if last_hook else
                        T["pause_sentence_s"] if ln["say"].rstrip()[-1] in ".?!" else T["pause_clause_s"])
    return marks, marks[-1][1] + T["tail_s"]


def beat_times(story, marks):
    """The moments the format hangs its effects on."""
    lines = story["lines"]
    hook = [i for i, l in enumerate(lines) if l["beat"] == "hook"]
    ident = [i for i, l in enumerate(lines) if l["beat"] == "ident"]
    ev = {"voice_start": marks[0][0], "hook_end": marks[hook[-1]][1], "ident_start": marks[ident[0]][0] if ident else marks[hook[-1]][1] + 0.6}
    ev["title_on"] = ev["hook_end"] - F["overlays"]["title_word"]["on_before_hook_end_s"]
    ev["title_off"] = ev["ident_start"] + F["overlays"]["title_word"]["off_after_ident_start_s"]
    ev["burn"] = ev["ident_start"] + F["overlays"]["transitions"]["burn"]["start_after_ident_start_s"]
    ev["image_shots"] = []                                             # (t0, t1, image name)
    for i, (ln, (t0, t1)) in enumerate(zip(lines, marks)):
        for c in cues(ln):
            if "image" in c:
                nxt = marks[i + 1][0] if i + 1 < len(marks) else t1 + 0.3
                ev["image_shots"].append((cue_time(c, ln["say"], t0, t1) - 0.08, nxt - 0.03, c["image"]))
    ev["white"] = [s[1] for s in ev["image_shots"]]
    return ev


# ---------------------------------------------------------------- camera
class Camera:
    """Rect = (cx, cy, w) in source pixels; h = w / stage aspect. w > image width = the picture as a card."""

    def __init__(self, story, img_w, img_h, sw, sh, scene="main"):
        self.W, self.H, self.a, self.story, self.scene = img_w, img_h, sw / sh, story, scene
        self.focus = story.get("focus", {}) if scene == "main" else story["images"][scene].get("focus", {})
        C = F["camera"]
        self.full_w = min(img_w, img_h * self.a)
        self.card_w = max(img_w / C["ident_card"]["zoom"], img_h * self.a / 0.80)
        self.min_w = max(self.full_w / C["zoom"]["max"], sw / 2.0)
        self.macro = set(story.get("macro", [])) if scene == "main" else set()     # v1.12: the framings that may go as close as the reference's eye (6x)
        self.min_macro = max(self.full_w / C["zoom"].get("macro", C["zoom"]["max"]), sw * C["zoom"].get("macro_min_stage_share", 0.5))

    def rect(self, name):
        if name == "full":
            return self.clamp((self.W / 2, self.H / 2, self.full_w))
        if name == "card":
            return (self.W / 2, self.H / 2, self.card_w)
        x0, y0, x1, y1 = self.focus[name]
        bw, bh, m = (x1 - x0) * self.W, (y1 - y0) * self.H, F["camera"]["focus_margin"]
        w = min(max(max(bw, bh * self.a) * (1 + 2 * m), self.min_macro if name in self.macro else self.min_w), self.full_w)
        return self.clamp(((x0 + x1) / 2 * self.W, (y0 + y1) / 2 * self.H, w))

    def clamp(self, r):
        cx, cy, w = r
        h = w / self.a
        if w <= self.W:
            cx = min(max(cx, w / 2), self.W - w / 2)
        if h <= self.H:
            cy = min(max(cy, h / 2), self.H - h / 2)
        return (cx, cy, w)

    def moves(self, marks):
        C, out, scene = F["camera"], [], "main"
        for ln, (t0, t1) in zip(self.story["lines"], marks):
            for cam in cues(ln):
                scene = cam.get("scene", scene)                        # v1.01: several pictures; each has its own camera
                if scene != self.scene:
                    continue
                if "scene" in cam:                                     # entering a picture is always a cut
                    cam = dict({"to": "full", "push": True}, **cam, how="cut") if not ("seq" in cam or "pan" in cam) else cam
                ts = cue_time(cam, ln["say"], t0, t1)
                if "seq" in cam:                                       # hook montage: jump cuts inside one line
                    k = len(cam["seq"])
                    for j, name in enumerate(cam["seq"]):
                        out.append(dict(t=ts + (t1 - ts) * j / k + 0.03, dur=0.0, to=self.rect(name)))
                elif "pan" in cam:                                     # constant-zoom travel to the end of the line
                    a, b = (self.rect(n) for n in cam["pan"])
                    w = max(a[2], b[2])
                    out.append(dict(t=ts - (C["focus_rule"]["cut_lead_s"] if "scene" in cam else 0.05), dur=max(0.8, t1 - ts), frm=self.clamp((a[0], a[1], w)), to=self.clamp((b[0], b[1], w))))
                elif "to" in cam:
                    cut, card = cam.get("how") == "cut", cam["to"] == "card"
                    R = C["focus_rule"]
                    out.append(dict(t=ts - (R["cut_lead_s"] if cut else 0.0 if card else R["glide_lead_s"]), dur=0.0 if cut else C["ident_card"]["glide_s"] if card else 1.0,
                                    to=self.rect(cam["to"]), push=bool(cam.get("push")), card=card, fixed=card, tw=ts))
        return sorted(out, key=lambda m: m["t"])

    def path(self, marks, total):
        C, n = F["camera"], int(math.ceil(total * FPS))
        mv, e = self.moves(marks), C["glide"]["ease"]
        ease = lambda u: e["cosine"] * (1 - math.cos(math.pi * u)) / 2 + e["linear"] * u
        full = self.rect("full")
        op = self.story.get("open") if self.scene == "main" else None  # v1.12: the frame the video opens on (the reference's Fallen Angel opens on the eye, not on the picture)
        first = self.rect(op) if op in self.focus else full
        cur, base, t_arr, push, k, active, start, rects = first, first, marks[0][0], first is full, 0, None, None, []
        for i in range(n):
            t = i / FPS
            while k < len(mv) and mv[k]["t"] <= t:
                active, start = mv[k], mv[k].get("frm", cur)
                if active["dur"] > 0 and "frm" not in active and not active.get("fixed"):
                    a_, b_ = start, active["to"]                       # glide time grows with the distance
                    dist = math.sqrt(math.log(b_[2] / a_[2]) ** 2 + ((b_[0] - a_[0]) / a_[2]) ** 2 + ((b_[1] - a_[1]) / (a_[2] / self.a)) ** 2)
                    dur = min(C["glide"]["max_s"], max(C["glide"]["min_s"], 0.9 + 1.2 * dist))
                    late = active["t"] + dur - (active["tw"] + 1.0)        # the thing must be on screen within a second of its name
                    if late > 0 and dist / max(0.3, dur - late) <= C["glide"]["max_speed_stage_widths_per_s"] + 0.15:
                        dur -= late
                    elif late > 0:                                          # too far to glide in time: cut on the word instead
                        mv.insert(k + 1, dict(active, t=active["tw"] - C["focus_rule"]["cut_lead_s"], dur=0.0))
                        mv.sort(key=lambda m_: m_["t"])
                        active, dur = None, None
                    if active is not None:
                        active["dur"] = dur
                k += 1
            if active and t < active["t"] + active["dur"]:
                u = ease((t - active["t"]) / active["dur"])
                a, b = start, active["to"]
                cur = (a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u, math.exp(math.log(a[2]) + (math.log(b[2]) - math.log(a[2])) * u))
            else:
                if active:
                    base, t_arr, push, active = active["to"], active["t"] + active["dur"], active.get("push", False), None
                if base[2] > self.W or (C.get("static_until_voice") and t < marks[0][0]):
                    cur = base                                         # the card and the opening seconds do not breathe
                else:                                                  # a hold is never frozen: slow push
                    fv = C["zoom"]["full_view_push"]
                    rate, cap = ((sum(fv["pct_per_s"]) / 2, fv["to"] / fv["from"]) if push or base[2] >= self.full_w * 0.98
                                 else (C["hold"]["drift_pct_per_s"], 1.12))
                    z = min(cap, math.exp(rate / 100 * max(0.0, t - t_arr)))
                    cur = self.clamp((base[0], base[1], max((self.min_macro if base[2] < self.min_w else self.min_w) * 0.9, base[2] / z)))    # v1.12: a macro hold stays macro
            rects.append(cur)
        return rects


# ---------------------------------------------------------------- picture layers
def starfield(sw, sh, seed=7):
    S, rnd = F["overlays"]["starfield"], random.Random(seed)
    im = np.zeros((sh, sw, 3), np.float32)
    for _ in range(S["stars"]):
        x, y, r = rnd.uniform(0, sw), rnd.uniform(0, sh), rnd.uniform(*S["radius_px"])
        col = (255, 125, 143) if rnd.random() < S["tint_share"] else (255, 255, 255)
        cv2.circle(im, (int(x), int(y)), max(1, int(round(r))), tuple(c * rnd.uniform(0.45, 1.0) for c in col), -1, cv2.LINE_AA)
    return cv2.GaussianBlur(im, (0, 0), 0.8).clip(0, 255).astype(np.uint8)


class Particles:
    """Dust in the air (measured on v1's still opening: about ten specks in view, each on its own straight track at
    80-200 px/s at 1080p, sharp dots of 2-5 px plus a few large soft ones, a slight drift upward)."""

    def __init__(self, sw, sh, seed=3):
        P, rnd, k = F["overlays"]["particles"], random.Random(seed), sh / 1080
        self.sw, self.sh, self.items = sw, sh, []
        for j in range(P["count"] if P["enabled"] else 0):
            big = j < P["soft_count"]
            ang, v = rnd.uniform(0, 6.283), rnd.uniform(*P["speed_px_s"]) * k * (0.45 if big else 1.0)
            self.items.append((rnd.uniform(0, sw), rnd.uniform(0, sh), v * math.cos(ang), v * math.sin(ang) - 14 * k,
                               rnd.uniform(*(P["soft_radius_px"] if big else P["radius_px"])) * k,
                               rnd.uniform(*(P["soft_opacity"] if big else P["opacity"])), rnd.uniform(2.5, 6.0), rnd.uniform(0, 6.0)))

    def draw(self, img, t):
        for x0, y0, vx, vy, r, op, life, ph in self.items:
            x, y = (x0 + vx * t) % self.sw, (y0 + vy * t) % self.sh
            a, R = op * math.sin(math.pi * (((t + ph) % life) / life)) ** 1.5, int(r * 2.5 + 2)      # fades in and out
            xa, ya, xb, yb = int(x) - R, int(y) - R, int(x) + R + 1, int(y) + R + 1
            if a < 0.02 or xa < 0 or ya < 0 or xb > self.sw or yb > self.sh:
                continue
            yy, xx = np.mgrid[ya:yb, xa:xb]
            g = (np.exp(-((xx - x) ** 2 + (yy - y) ** 2) / (2 * (r * 0.8) ** 2)) * a)[..., None]
            img[ya:yb, xa:xb] = (img[ya:yb, xa:xb] * (1 - g) + 255 * g).astype(np.uint8)


class Finish:
    """What makes the still picture look alive and aged: a vignette, a slightly darker and harder grade, and
    CANDLELIGHT (the owner's description of the reference, pass 6: "as if a candle burns at the side and the light
    changes from it; light, in a warm tone"). One warm light source just outside the frame: its side of the picture
    is a little warmer and brighter, and the light wavers the way a flame does (quick small trembling over a slow
    sway). The far side barely changes. No colour patches, no green / magenta; fine grain on top."""

    def __init__(self, sw, sh, seed=11):
        O = F["overlays"]
        V, C = O["vignette"], O["candle"]
        yy, xx = np.mgrid[0:sh, 0:sw].astype(np.float32)
        r = np.hypot((xx - sw / 2) / (sw / 2), (yy - sh / 2) / (sh / 2)) / math.sqrt(2)
        u = np.clip((r - V["start_r"]) / (1 - V["start_r"]), 0, 1)       # clear centre, darkest in the corners
        self.vig = (1 - V["painting"] * u * u * (3 - 2 * u))[..., None]
        d = np.hypot(xx - C["pos"][0] * sw, yy - C["pos"][1] * sh) / sw  # distance from the flame, in stage widths
        fall = 1 / (1 + (d / C["reach"]) ** 2)
        self.fall = (fall / fall.max())[..., None]                       # 1 next to the flame, ~0.15 on the far side
        self.warm = np.array(C["warm_bgr"], np.float32)                  # the light is warm: red moves most, blue least
        self.C, self.G, self.L, self.rng, self.sw, self.sh, self.c = C, O["grade"], O["flicker"], np.random.default_rng(seed), sw, sh, 0.0

    def flame(self, t):
        C, k = self.C, self.C["memory"]
        self.c = k * self.c + math.sqrt(1 - k * k) * float(self.rng.normal())                 # the trembling
        sway = math.sin(2 * math.pi * C["sway_hz"] * t) + 0.5 * math.sin(2 * math.pi * C["sway_hz"] * 0.43 * t + 1.3)
        return float(np.clip(C["tremble"] * self.c + C["sway"] * sway, -1.5, 1.5))

    def apply(self, st, t):
        L, G, C = self.L, self.G, self.C
        x = (st.astype(np.float32) - 100) * G["contrast"] + 100 * G["gain"]
        light = 1 + self.fall * self.warm * (C["glow"] + C["amp"] * self.flame(t))
        n = self.rng.standard_normal((self.sh // 2, self.sw // 2, 3)).astype(np.float32)
        grain = cv2.resize(n[..., :1] * L["grain_luma"] + n * L["grain_chroma"], (self.sw, self.sh), interpolation=cv2.INTER_LINEAR)
        return (x * self.vig * light + grain).clip(0, 255).astype(np.uint8)


def focus_audit(story, marks, rects, ev, cams, track):
    """THE RULE: the frame shows what the words name. For every word listed in story["names"], look at the camera at
    the moment the word is spoken and require one of its allowed framings: the thing's box at least 70 % inside the
    frame and a real share of it, or the whole picture where "full" is allowed, or the named image shot.
    A framing is "box" (in the lead picture), "scene:box", "scene:full", or the name of an image shot."""
    names, out, R_ = {k.lower(): v for k, v in story.get("names", {}).items()}, [], F["camera"]["focus_rule"]
    shots = {s_[2] for s_ in ev["image_shots"]}
    for ln, (t0, t1) in zip(story["lines"], marks):
        for w, tw in word_times(ln["say"], t0, t1):
            own = {k.lower(): v for k, v in ln.get("names", {}).items()}     # v1.02: a line may name its own framings
            allowed = own.get(w) or own.get(w.split("'")[0]) or names.get(w) or names.get(w.split("'")[0])
            if not allowed:
                continue
            ok, seen = False, ""
            for t in np.arange(tw - 0.1, tw + 1.01, 0.1):                  # on screen within a second of being named
                shot = next((s_[2] for s_ in ev["image_shots"] if s_[0] <= t < s_[1]), None)
                scene = [sc for ts, sc in track if ts <= t][-1]
                cam = cams[scene]
                cx, cy, wv = rects[scene][min(len(rects[scene]) - 1, max(0, int(t * FPS)))]
                hv, parts_ = wv / cam.a, []
                for f in allowed:
                    fs, fb = f.split(":") if ":" in f else ("main", f)
                    if shot or f in shots:
                        ok = ok or f == shot
                    elif fs != scene:
                        continue
                    elif fb in ("full", "card"):
                        ok = ok or wv >= cam.full_w * 0.93
                    else:
                        x0, y0, x1, y1 = cam.focus[fb]
                        bx0, by0, bx1, by1 = x0 * cam.W, y0 * cam.H, x1 * cam.W, y1 * cam.H
                        iw = max(0.0, min(bx1, cx + wv / 2) - max(bx0, cx - wv / 2))
                        ih = max(0.0, min(by1, cy + hv / 2) - max(by0, cy - hv / 2))
                        inside, share = iw * ih / ((bx1 - bx0) * (by1 - by0)), iw * ih / (wv * hv)
                        parts_.append(f"{f}:{inside:.0%} in, {share:.0%} of frame")
                        ok = ok or (inside >= R_["box_inside_min"] and (share >= R_["box_share_of_frame_min"] or wv <= cam.min_w * 1.08))
                seen = shot or "; ".join(parts_) or f"{scene}, zoom {cam.full_w / wv:.2f}"
                if ok:
                    break
            out.append({"t": round(float(tw), 2), "word": w, "line": ln["say"], "ok": bool(ok), "shown": seen})
    return out


def caption_text(story, say):
    """The automatic-caption look, spelled right: lowercase, no punctuation, proper nouns kept."""
    proper = set(re.findall(r"[A-Z][\w'’èéêëàâîïôöûüç-]+", story["artwork"]["title"] + " " + story["artwork"]["artist"]))
    for ln in story["lines"]:
        proper |= set(re.findall(r"(?<=[a-z,;] )[A-Z][\w'’èéêëàâîïôöûüç-]+", ln["say"]))
    proper -= {"The", "In", "Of", "A", "An"}
    words = [w.strip(".,;:!?\"“”()—–") for w in say.split()]
    return " ".join(w if w in proper or w.split("'")[0] in proper else w.lower() for w in words if w)


def caption_sprite(text, sw, sh):
    B = F["captions"]["boxed"]
    font = ImageFont.truetype(str(FONTS / B["font"]), max(10, round(B["size_frac_hs"] * sh * CAP_SCALE)))
    lines = [text]
    if len(text) > B["max_chars_per_line"]:
        sp = [m.start() for m in re.finditer(" ", text)]
        cut = min(sp, key=lambda i: abs(i - len(text) / 2))
        lines = [text[:cut], text[cut + 1:]]
    pitch = B["line_pitch_frac_hs"] * sh * CAP_SCALE
    bw = int(max(font.getlength(s) for s in lines) + 2 * B["pad_x_frac_ws"] * sw * CAP_SCALE)
    bh = int(0.021 * sh * CAP_SCALE + len(lines) * pitch * 0.945)
    im = Image.new("RGBA", (bw, bh), (0, 0, 0, round(255 * B["box_opacity"])))
    d = ImageDraw.Draw(im)
    for j, s in enumerate(lines):
        d.text((bw / 2, bh / 2 + (j - (len(lines) - 1) / 2) * pitch), s, font=font, fill=(255, 255, 255, 255), anchor="mm")
    arr = np.array(im)
    return arr[..., [2, 1, 0]].astype(np.float32), (arr[..., 3:4] / 255.0).astype(np.float32)


def title_sprite(word, sw, sh):
    """The giant red hook word: a heavy slab serif stretched tall, clean edges (measured: 72 % x 54 % of the stage)."""
    W = F["overlays"]["title_word"]
    font = ImageFont.truetype(str(FONTS / W["font"]), 400)
    l, t, r, b = font.getbbox(word)
    im = Image.new("L", (r - l + 40, b - t + 40), 0)
    ImageDraw.Draw(im).text((20 - l, 20 - t), word, font=font, fill=255)
    a = np.array(im)
    ys, xs = np.where(a > 128)
    a = a[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    tw = int(min(W["width_frac_ws"], W["width_per_letter_max"] * len(word)) * sw)
    th = int(W["height_frac_hs"] * sh)
    a = cv2.resize(a, (tw, th), interpolation=cv2.INTER_AREA)
    a = cv2.copyMakeBorder(a, 12, 12, 12, 12, cv2.BORDER_CONSTANT)
    k = int(round(W.get("bold_frac_ws", 0.0) * sw))                    # optional heavier strokes
    if k:
        a = cv2.dilate(a, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * k + 1, k + 1)))
    a = a.astype(np.float32)
    rng = np.random.default_rng(len(word) * 7 + ord(word[0]))          # hand-cut, uneven outline

    def field():
        g = rng.standard_normal((a.shape[0] // 14 + 2, a.shape[1] // 14 + 2)).astype(np.float32)
        return cv2.resize(g, (a.shape[1], a.shape[0]), interpolation=cv2.INTER_CUBIC) * W["rough_px"]

    yy, xx = np.mgrid[0:a.shape[0], 0:a.shape[1]].astype(np.float32)
    if W["rough_px"] > 0:                                              # 0 = clean, strict edges (the owner's choice)
        a = cv2.remap(a, xx + field(), yy + field(), cv2.INTER_LINEAR)
    al = np.clip((cv2.GaussianBlur(a, (0, 0), 1.0) - 110) / 40, 0, 1)[..., None]
    col = tuple(int(W["color"][i:i + 2], 16) for i in (5, 3, 1))       # BGR
    return np.full(a.shape + (3,), col, np.float32), al.astype(np.float32)


def burn_frame(st, u):
    """Film-burn / light-leak: red tint -> orange -> yellow-white -> orange -> clear (u = 0..1)."""
    h, w = st.shape[:2]
    keys = [(0.0, (30, 40, 200), 0.55), (0.30, (40, 150, 255), 0.92), (0.58, (200, 245, 255), 1.0), (0.85, (60, 190, 255), 0.92), (1.0, (60, 190, 255), 0.0)]
    col, al = np.array(keys[-1][1], np.float32), 0.0
    for (u0, c0, a0), (u1, c1, a1) in zip(keys, keys[1:]):
        if u0 <= u <= u1:
            f = (u - u0) / (u1 - u0)
            col, al = np.array(c0, np.float32) + (np.array(c1, np.float32) - np.array(c0, np.float32)) * f, a0 + (a1 - a0) * f
            break
    xx = np.linspace(0, 1, w, dtype=np.float32)[None, :, None]
    yy = np.linspace(0, 1, h, dtype=np.float32)[:, None, None]
    leak = np.clip(0.82 + 0.3 * np.sin(3.1 * xx + 1.2 + 4 * u) * np.cos(2.2 * yy - 0.6), 0.6, 1.0)    # uneven wash
    A = np.clip(al * leak, 0, 1)
    return (255 - (255 - st.astype(np.float32)) * (1 - A * col / 255.0)).clip(0, 255).astype(np.uint8)    # screen blend


def image_shot(img, u, stars, sw, sh):
    """The painter's portrait: a card on the star field (90 % of the stage height) pushing in to fill the frame."""
    C = F["camera"]["ident_card"]
    ih, iw = img.shape[:2]
    s0 = C["portrait_card_height_frac_hs"] * sh / ih
    s1 = max(sw / iw, sh / ih) * C["portrait_end_scale_over_cover"]
    s = math.exp(math.log(s0) + (math.log(s1) - math.log(s0)) * (u ** 1.6))          # slow start, then it comes at you
    cy = 0.5 + (C["portrait_center_y"] - 0.5) * (u ** 1.6)
    M = np.float32([[s, 0, sw / 2 - iw * s / 2], [0, s, sh / 2 - ih * s * cy]])
    card = cv2.warpAffine(img, M, (sw, sh), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_CONSTANT)
    x0, y0 = int(round(M[0, 2])), int(round(M[1, 2]))
    x1, y1 = int(round(x0 + iw * s)), int(round(y0 + ih * s))
    out = stars.copy()
    xa, ya, xb, yb = max(0, x0), max(0, y0), min(sw, x1), min(sh, y1)
    out[ya:yb, xa:xb] = card[ya:yb, xa:xb]
    return out


# ---------------------------------------------------------------- sound
def _env(n, attack, tau):
    t = np.arange(n) / SR
    return np.minimum(1.0, t / attack) * np.exp(-t / tau)


def stinger():
    """The dark two-note opening (measured: 62-115 Hz cluster + 640 / 820 Hz, a 51 Hz swell, then 88 / 165 / 367 /
    526 / 759 Hz at 1.0 s; nothing above 1.1 kHz; over by 1.5 s). Audible on a phone thanks to the 500-850 Hz partials."""
    n = int(F["audio"]["stinger"]["dur_s"] * SR)
    t, y = np.arange(n) / SR, np.zeros(n)
    for f, a in ((62, .7), (66, .9), (75, 1.0), (86, .5), (100, .7), (115, .8)):
        y += a * np.sin(2 * np.pi * f * t + f) * _env(n, 0.02, 0.55)
    for f, a in ((250, .35), (400, .35), (520, .4), (640, .55), (820, .7)):
        y += a * np.sin(2 * np.pi * f * t + f) * _env(n, 0.012, 0.13)
    y += 1.6 * np.sin(2 * np.pi * 51 * t) * np.clip((t - 0.25) / 0.5, 0, 1) * np.clip((0.95 - t) / 0.08, 0, 1)   # sub swell
    k = int(1.0 * SR)
    m = n - k
    tb = np.arange(m) / SR
    for f, a in ((43, .6), (88, .9), (165, .45), (367, .3), (526, .4), (759, .75)):
        y[k:] += a * np.sin(2 * np.pi * f * tb + f) * _env(m, 0.02, 0.22)
    y *= np.clip((F["audio"]["stinger"]["dur_s"] - t) / 0.06, 0, 1)
    y = np.tanh(y * 0.9)
    Y, fr = np.fft.rfft(y), np.fft.rfftfreq(n, 1 / SR)                 # nothing above ~1.1 kHz, as measured
    lp = F["audio"]["stinger"]["lowpass_hz"]
    Y *= np.clip((lp * 1.15 - fr) / (lp * 0.3), 0, 1)
    y = np.fft.irfft(Y, n)
    return (y / np.abs(y).max()).astype(np.float32)


def riser(dur):
    """A broadband noise swell: +25 dB over its length, opening up in tone, cut dead at the end."""
    n = int(dur * SR)
    x, u = np.random.default_rng(5).standard_normal(n), np.arange(n) / n
    y, s = np.zeros(n), 0.0
    alpha = 0.03 + 0.75 * u ** 2                                       # one-pole low-pass whose cutoff climbs
    for i in range(n):
        s += alpha[i] * (x[i] - s)
        y[i] = s
    y *= 10 ** ((u - 1) * F["audio"]["riser"]["rise_db"] / 20) * (0.75 + 0.25 * np.sin(2 * np.pi * 9 * u * dur) ** 2)
    y[-int(0.004 * SR):] *= np.linspace(1, 0, int(0.004 * SR))
    return (y / np.abs(y).max()).astype(np.float32)


def impact():
    n = int(0.5 * SR)
    t = np.arange(n) / SR
    y = np.random.default_rng(6).standard_normal(n) * np.exp(-t / 0.028)
    f = 45 + 30 * np.exp(-t * 18)
    y = y * 0.9 + 1.3 * np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.10) + 0.6 * np.sin(2 * np.pi * 210 * t) * np.exp(-t / 0.04)
    return (y / np.abs(y).max()).astype(np.float32)


def shutter():
    n = int(0.28 * SR)
    y, rng = np.zeros(n), np.random.default_rng(8)
    for t0 in (0.0, F["audio"]["shutter"]["gap_s"]):
        k = int(t0 * SR)
        m = n - k
        tt = np.arange(m) / SR
        click = rng.standard_normal(m)
        click = click - np.convolve(click, np.ones(12) / 12, "same")      # high-passed
        y[k:] += click * np.exp(-tt / 0.012) + 0.5 * np.sin(2 * np.pi * 1250 * tt) * np.exp(-tt / 0.008)
    return (y / np.abs(y).max()).astype(np.float32)


def low_hit():
    n = int(2.0 * SR)
    t = np.arange(n) / SR
    y = np.sin(2 * np.pi * np.cumsum(38 + 24 * np.exp(-t * 5)) / SR) * np.exp(-t * 1.9) + 0.4 * np.sin(2 * np.pi * 150 * t) * np.exp(-t * 6)
    return (y / np.abs(y).max()).astype(np.float32)


def humming_bed(dur, seed):
    """An eerie slow hummed line over a low drone (the reference bed tags: humming / theremin / lullaby / choir)."""
    n, rnd = int(dur * SR), random.Random(seed)
    t, y = np.arange(n) / SR, np.zeros(n)
    scale = [293.66, 329.63, 349.23, 392.0, 440.0, 466.16, 523.25, 587.33, 659.25, 698.46]     # D minor, D4-F5
    i, pos = 4, 0.0
    while pos < dur:
        length = rnd.choice([1.4, 1.8, 2.2, 2.8])
        i = min(len(scale) - 1, max(0, i + rnd.choice([-2, -1, -1, 1, 1, 2])))
        k0, k1 = int(pos * SR), min(n, int((pos + length + 0.7) * SR))
        tt = np.arange(k1 - k0) / SR
        vib = 1 + 0.006 * np.sin(2 * np.pi * 5.1 * tt + rnd.uniform(0, 6))
        ph = 2 * np.pi * np.cumsum(scale[i] * vib) / SR
        env = np.clip(tt / 0.45, 0, 1) * np.clip((length + 0.7 - tt) / 0.9, 0, 1)
        y[k0:k1] += (np.sin(ph) + 0.33 * np.sin(2 * ph) + 0.10 * np.sin(3 * ph) + 0.25 * np.sin(ph / 2)) * env
        pos += length
    for f, a in ((73.42, 0.9), (110.0, 0.45), (146.83, 0.35)):
        y += a * 0.5 * np.sin(2 * np.pi * f * t + 1.1 * np.sin(2 * np.pi * 0.06 * t + f))
    m = int(1.6 * SR)
    tail = np.random.default_rng(seed).standard_normal(m) * np.exp(-np.arange(m) / (0.45 * SR))
    wet = np.fft.irfft(np.fft.rfft(y, n + m) * np.fft.rfft(tail, n + m))[:n]                      # cheap hall
    y = y / np.abs(y).max() + 0.6 * wet / np.abs(wet).max()
    return (y / np.abs(y).max()).astype(np.float32)


def build_audio(story, clips, marks, total, ev, work):
    A, n = F["audio"], int(total * SR) + SR
    voice = np.zeros(n, np.float32)
    for y, (t0, _) in zip(clips, marks):
        i = int(t0 * SR)
        voice[i:i + len(y)] += y[:n - i]
    rms = lambda x: float(np.sqrt(np.mean(x[np.abs(x) > 1e-4] ** 2))) if np.any(np.abs(x) > 1e-4) else 1e-6
    vr, fx = rms(voice), np.zeros(n, np.float32)

    def place(y, t0, db):                                              # level = RMS of the sound against the voice RMS
        i = max(0, int(t0 * SR))
        fx[i:i + len(y)] += (y * vr / rms(y) * 10 ** (db / 20))[:n - i]

    intro, head = ROOT / A["stinger"].get("file", ""), None
    if A["stinger"].get("file") and intro.exists():                    # THE opening sound (the owner's file), as it is
        raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(intro), "-ac", "2", "-ar", str(SR), "-f", "f32le", "-"], capture_output=True).stdout
        head = np.frombuffer(raw, np.float32).reshape(-1, 2).copy()    # STEREO (the file is wide: L/R correlation 0.23), added after the limiter
    else:
        place(stinger(), 0.0, A["stinger"]["over_voice_db"])
    r0 = max(ev["voice_start"] + 0.6, ev["title_on"] - A["riser"]["dur_s"])
    rz = riser(ev["title_on"] + 0.04 - r0)
    i = int(r0 * SR)
    q = rz[-int(0.25 * SR):]
    fx[i:i + len(rz)] += rz * vr / rms(q) * 10 ** (-A["riser"]["end_under_voice_db"] / 20)   # its last quarter second ~4 dB under the voice
    imp = impact()
    k = int((ev["ident_start"] + A["impact"]["after_ident_start_s"]) * SR)
    fx[k:k + len(imp)] += imp * vr / rms(imp[:int(0.1 * SR)]) * 10 ** (A["impact"]["over_voice_db"] / 20)
    for tw in ev["white"]:
        sh_ = shutter()
        k = max(0, int((tw - 0.01) * SR))
        fx[k:k + len(sh_)] += sh_ * vr / rms(sh_) * 10 ** (A["shutter"]["over_voice_db"] / 20)
    for ln, (t0, _) in zip(story["lines"], marks):
        if ln.get("accent"):
            place(low_hit(), t0 - 0.05, -A["accent_under_voice_db"])

    t_music = ev["ident_start"] + A["music"]["start_after_ident_start_s"]
    lib = sorted((ROOT / "assets/music").glob("*.mp3"))
    if lib:
        f = lib[sum(map(ord, story["id"])) % len(lib)]
        raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(f), "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"], capture_output=True).stdout
        m = np.resize(np.frombuffer(raw, np.float32), n).copy()
    else:
        m = humming_bed(n / SR, sum(map(ord, story["id"])))[:n]
    m *= vr / rms(m) * 10 ** (-A["music"]["under_voice_db"] / 20)
    k, fi = int(t_music * SR), int(A["music"]["fade_in_s"] * SR)
    m[:k] = 0                                                          # no music under the hook: effects only
    m[k:k + fi] *= np.linspace(0, 1, fi)
    end = int(total * SR)
    mix = (voice + m + fx)[:end]
    with wave.open(str(work / "voice.wav"), "wb") as w:                # voice alone, for the pause meter
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((np.clip(voice[:end] / max(1e-6, np.abs(voice).max()), -1, 1) * 32767).astype("<i2").tobytes())
    wav = work / "mix.wav"

    def save(y):
        with wave.open(str(wav), "wb") as w:
            w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
            w.writeframes((np.clip(y, -1, 1) * 32767).astype("<i2").tobytes())

    def lufs():
        err = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(wav), "-af", "ebur128", "-f", "null", "-"], capture_output=True, text=True).stderr
        return float(re.findall(r"I:\s+(-?[\d.]+) LUFS", err)[-1])

    M, y = A["mix"], mix / max(1.0, np.abs(mix).max()) * 0.5
    ceil, knee = 10 ** (M["true_peak_db"] / 20) * 0.97, 0.55
    for _ in range(3):                                                 # gain to the target, soft-limit, measure again
        save(y)
        y = y * 10 ** ((M["lufs"] - lufs()) / 20)
        over = np.abs(y) > knee
        y[over] = np.sign(y[over]) * (knee + (ceil - knee) * np.tanh((np.abs(y[over]) - knee) / (ceil - knee)))
    y = np.stack([y, y], 1) * 0.7071                                   # stereo out: everything of ours in the centre (equal-power, the level the LUFS loop measured)
    if head is not None:                                               # nothing else sounds before the voice
        k = min(len(head), int(ev["voice_start"] * SR), len(y))
        y[:k] += head[:k] * (A["stinger"]["peak"] / np.abs(head).max())  # the owner's file sample for sample: one gain, no filter, no limiter
    with wave.open(str(wav), "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((np.clip(y, -1, 1) * 32767).astype("<i2").tobytes())
    return wav


# ---------------------------------------------------------------- render
def render(story_path, out_path):
    story = json.loads(Path(story_path).read_text(encoding="utf-8"))
    work = Path(out_path).with_suffix("").parent / (Path(out_path).stem + "_work")
    work.mkdir(parents=True, exist_ok=True)
    src = cv2.imread(str(ROOT / story["images"]["main"]["file"]), cv2.IMREAD_COLOR)
    extra = {}
    for k, v in story["images"].items():
        if v.get("file"):
            im = src if k == "main" else cv2.imread(str(ROOT / v["file"]), cv2.IMREAD_COLOR)
            if im is None:
                raise SystemExit(f"picture '{k}' is missing: {v['file']}")
            if v.get("crop"):                                          # e.g. the rectangle inside an oval portrait
                x0, y0, x1, y1 = v["crop"]
                im = im[int(y0 * im.shape[0]):int(y1 * im.shape[0]), int(x0 * im.shape[1]):int(x1 * im.shape[1])]
            extra[k] = im
    src = extra["main"]
    ih, iw = src.shape[:2]
    a = min(F["canvas"]["stage_aspect_max"], max(F["canvas"]["stage_aspect_min"], iw / ih))
    sw, sh = CW, int(round(CW / a / 2) * 2)
    y_off = int(round(CH * F["canvas"]["stage_center_y"] - sh / 2))
    def pyramid(im):
        out = [im]
        while min(out[-1].shape[:2]) > 600:
            out.append(cv2.resize(out[-1], None, fx=0.5, fy=0.5, interpolation=cv2.INTER_AREA))
        return out

    clips = speak_lines(story)
    marks, total = timeline(story, clips)
    ev = beat_times(story, marks)
    track = scene_track(story, marks)                                  # v1.01: one camera and one pyramid per picture used as a scene
    used = sorted({sc for _, sc in track})
    cams = {k: Camera(story, extra[k].shape[1], extra[k].shape[0], sw, sh, k) for k in used}
    paths = {k: cams[k].path(marks, total) for k in used}
    pyrs = {k: pyramid(extra[k]) for k in used}
    rects = paths["main"]
    audit = focus_audit(story, marks, paths, ev, cams, track)
    bad = [a_ for a_ in audit if not a_["ok"]]
    for a_ in bad:
        print(f"FOCUS FAIL {a_['t']:6.2f}s  '{a_['word']}' in \"{a_['line']}\"  shown: {a_['shown']}")
    if bad and os.environ.get("ALLOW_FOCUS_FAIL") != "1":
        raise SystemExit(f"{len(bad)} of {len(audit)} named things are not in the frame when they are named: fix the cam cues")
    if os.environ.get("AUDIT_ONLY") == "1":                            # the cues checked without rendering a frame
        print(f"audit only: {total:.1f} s, {sum(a_['ok'] for a_ in audit)}/{len(audit)} named things in frame, scenes {[(round(t_, 1), k_) for t_, k_ in track]}")
        return
    stars, parts, finish = starfield(sw, sh), Particles(sw, sh), Finish(sw, sh)
    caps, delay = [], T["caption_delay_s"]
    for i, (ln, (t0, t1)) in enumerate(zip(story["lines"], marks)):
        nxt = marks[i + 1][0] if i + 1 < len(marks) else total + 1
        caps.append((t0 + delay, nxt + delay, caption_sprite(caption_text(story, ln["say"]), sw, sh)))
    title = title_sprite(story["hook_title"].upper(), sw, sh) if story.get("hook_title") else None
    wav = build_audio(story, clips, marks, total, ev, work)
    TR, n, E = F["overlays"]["transitions"], len(rects), F["encode"]

    ff = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{CW}x{CH}", "-r", str(FPS), "-i", "-", "-i", str(wav),
                           "-c:v", "libx264", "-preset", "veryfast", "-crf", str(E["crf"]), "-maxrate", E["maxrate"], "-bufsize", E["bufsize"], "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-ar", "44100", "-ac", "2",
                           "-movflags", "+faststart", "-shortest", str(out_path)], stdin=subprocess.PIPE)
    canvas = np.zeros((CH, CW, 3), np.uint8)
    ti = 0
    for i in range(n):
        t = i / FPS
        while ti + 1 < len(track) and track[ti + 1][0] <= t:
            ti += 1
        scene = track[ti][1]
        (cx, cy, w), pyr, (ih, iw) = paths[scene][i], pyrs[scene], extra[scene].shape[:2]
        shot = next((s for s in ev["image_shots"] if s[0] <= t < s[1] and s[2] in extra), None)
        if shot:                                                       # the painter's portrait card
            st = image_shot(extra[shot[2]], (t - shot[0]) / (shot[1] - shot[0]), stars, sw, sh)
        else:
            s = sw / w
            k = min(len(pyr) - 1, max(0, int(math.floor(math.log2(1 / s))))) if s < 1 else 0
            f = 2 ** k
            M = np.float32([[s * f, 0, -(cx - w / 2) * s], [0, s * f, -(cy - w / a / 2) * s]])
            st = cv2.warpAffine(pyr[k], M, (sw, sh), flags=cv2.INTER_CUBIC if s * f >= 1 else cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)
            if w > iw + 1 or w / a > ih + 1:                           # the picture as a card on the star field
                x0, y0 = int(round(-(cx - w / 2) * s)), int(round(-(cy - w / a / 2) * s))
                x1, y1 = int(round(x0 + iw * s)), int(round(y0 + ih * s))
                bg = stars.copy()
                bg[max(0, y0):min(sh, y1), max(0, x0):min(sw, x1)] = st[max(0, y0):min(sh, y1), max(0, x0):min(sw, x1)]
                st = bg
        st = finish.apply(st, t)                                       # vignette, grade, breathing light, coloured grain
        if t < T["fade_in_s"]:                                         # out of black
            st = (st * (t / T["fade_in_s"])).astype(np.uint8)
        parts.draw(st, t)
        if title is not None and ev["title_on"] <= t < ev["title_off"]:
            rgb, al = title
            th, tw = rgb.shape[:2]
            c = F["overlays"]["title_word"]["center"]
            x, y = int(c[0] * sw - tw / 2), int(c[1] * sh - th / 2)
            st[y:y + th, x:x + tw] = (st[y:y + th, x:x + tw] * (1 - al) + rgb * al).astype(np.uint8)
        if i >= n - T["end_black_frames"]:
            st[:] = 0                                                  # the last frames: black, the caption stays
        for c0, c1, (rgb, al) in caps:
            if c0 <= t < c1:
                bh, bw = rgb.shape[:2]
                x, y = (sw - bw) // 2, int(F["captions"]["boxed"]["center_y_frac_hs"] * sh - bh / 2)
                st[y:y + bh, x:x + bw] = (st[y:y + bh, x:x + bw] * (1 - al) + rgb * al).astype(np.uint8)
                break
        u = (t - ev["burn"]) / TR["burn"]["dur_s"]
        if 0 <= u <= 1:
            st = burn_frame(st, u)
        for tw_ in ev["white"]:
            d = t - tw_
            if 0 <= d < TR["white_flash"]["decay_s"]:
                k_ = 1.0 if d < 1.5 / FPS else (1 - d / TR["white_flash"]["decay_s"]) ** 1.2      # one full-white frame, then it clears
                st = (st + (255 - st) * k_).astype(np.uint8)
        canvas[y_off:y_off + sh] = st
        ff.stdin.write(canvas.tobytes())
    ff.stdin.close()
    ff.wait()
    def true_peak():
        err = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(out_path), "-af", "ebur128=peak=true", "-f", "null", "-"], capture_output=True, text=True).stderr
        pk = [float(x) for x in re.findall(r"Peak:\s+(-?[\d.]+) dBFS", err)]
        return pk[-1] if pk else None
    pk, gain = true_peak(), 0.0
    for _ in range(3):                                                 # v1.02: AAC overshoots on the shutter click; v1.13: the cut is re-encoded from mix.wav (one AAC generation,
        if pk is None or pk <= -0.5:                                   # not AAC over AAC: Medusa, Nov 15, -0.3 dBFS lowered by 0.6 dB came back as +0.4) and measured again, up to 3 times
            break
        gain += -1.0 - pk
        tmp = Path(str(out_path) + ".tmp.mp4")
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(out_path), "-i", str(wav), "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-af", f"volume={gain:.2f}dB",
                        "-c:a", "aac", "-b:a", "192k", "-ar", "44100", "-ac", "2", "-shortest", "-movflags", "+faststart", str(tmp)], check=True)
        tmp.replace(out_path)
        old_pk, pk = pk, true_peak()
        print(f"true peak was {old_pk:.1f} dBFS: track lowered by {-gain:.1f} dB, now {pk:.1f} dBFS")
    (work / "timeline.json").write_text(json.dumps({"total": total, "stage": [sw, sh], "y_off": y_off, "events": ev, "focus_audit": audit, "lines": [
        {"t0": round(a_, 2), "t1": round(b_, 2), "beat": ln["beat"], "say": ln["say"]} for ln, (a_, b_) in zip(story["lines"], marks)]}, indent=1))
    words = sum(len(ln["say"].split()) for ln in story["lines"])
    print(f"{out_path}: {total:.1f} s, {words} words, {words / (marks[-1][1] - marks[0][0]) * 60:.0f} wpm, stage {sw}x{sh}, voice from {marks[0][0]:.2f} s, "
          f"title {ev['title_on']:.2f}-{ev['title_off']:.2f}, ident {ev['ident_start']:.2f}, portrait {[(round(a_, 2), round(b_, 2)) for a_, b_, _ in ev['image_shots']]}, "
          f"focus audit {sum(a_['ok'] for a_ in audit)}/{len(audit)} named things in frame")


if __name__ == "__main__":
    render(sys.argv[1], sys.argv[2])

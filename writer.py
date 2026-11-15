#!/usr/bin/env python3
"""writer.py — the in-run writer: a topic becomes a script (v1.02).

    python writer.py                       the next topic of data/backlog.json that is not in data/used.json
    python writer.py --topic <id>          that topic
    -> scripts/<id>.json (then: director.py -> stories/<id>.json -> bot.py)

Steps: facts and the lead picture from Wikipedia / Commons (free licence required) -> LOOK: Gemini looks at the
picture and lists what is visible, with boxes (prompts/look.txt) -> the script in the fixed slots (prompts/writer.txt)
-> tools/script_check.py; its failures go back to the model, three rounds -> the script file.
Needs GEMINI_API_KEY (free tier).
v1.09: THE MAIN WRITER IS THE NIGHTLY CLAUDE ROUTINE (docs/NIGHT_WRITER.md, tools/night_writer.py): it leaves
scripts/<id>.json marked "written_by": "Claude ...". bot.py takes such a script as it is and asks Gemini nothing;
this module is the BACKUP for a topic that has no ready script (or whose ready script failed the bot's checks).
"""
import argparse, base64, json, os, random, re, subprocess, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))
import sources, script_check, learn, director

MODELS = [os.environ.get("GEMINI_MODEL", "gemini-3.5-flash"), "gemini-flash-latest", "gemini-3.1-flash-lite", "gemini-2.5-flash"]
COOL, DEAD = {}, set()


def gemini(prompt, ok, extra=None, rounds=5, purpose="script"):
    """JSON from Gemini (the warehouse's loop: a busy model cools down and the next one is tried)."""
    key = os.environ["GEMINI_API_KEY"]
    for rnd in range(rounds):
        for model in MODELS:
            if model in DEAD or COOL.get(model, 0) > time.time():
                continue
            body = json.dumps({"contents": [{"parts": [{"text": prompt}] + (extra or [])}], "generationConfig": {"responseMimeType": "application/json"}})
            r = subprocess.run(["curl", "-s", "--max-time", "120", "-w", "\n%{http_code}", "-H", "Content-Type: application/json", "-H", f"x-goog-api-key: {key}",
                                "-d", "@-", f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"], input=body.encode(), capture_output=True)
            raw, code = r.stdout.rsplit(b"\n", 1)[0].decode("utf-8", "replace"), r.stdout.rsplit(b"\n", 1)[-1].decode().strip()
            if code == "429" and "PerDay" in raw:
                DEAD.add(model)
                continue
            if code == "429" or code.startswith("5") or code == "000":
                COOL[model] = time.time() + 45
                continue
            if code != "200":
                if code == "404":
                    DEAD.add(model)
                print(model, code, purpose, raw[:120].replace("\n", " "))
                continue
            try:
                data = json.loads(json.loads(raw)["candidates"][0]["content"]["parts"][0]["text"])
                if ok(data):
                    return data
                print(model, "incomplete JSON", purpose, json.dumps(data, ensure_ascii=False)[:300])
            except (ValueError, KeyError, IndexError, TypeError):
                print(model, "unreadable answer", purpose)
        live = [COOL.get(m, 0) for m in MODELS if m not in DEAD]
        if not live:
            break
        time.sleep(max(1.0, min(60, min(live) - time.time())) + random.random())
    raise SystemExit(f"Gemini unavailable ({purpose})")


def ready_script(topic_id):
    """v1.09: the night writer's script for this topic, if it is there and has not failed the bot's checks."""
    p = ROOT / "scripts" / f"{topic_id}.json"
    try:
        s = json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return None
    return p if str(s.get("written_by", "")).lower().startswith("claude") and not s.get("failed") and s.get("form") else None    # v1.12: a script from before the forms is written anew


def queue(skip=()):
    """The topics the bot may make, best first. v1.03: only 7 and more; v1.05: a topic on "hold" waits for Andrii;
    v1.09: ordered by learn.priority (= the judge's total until learning switches on)."""
    topics = json.loads((ROOT / "data/backlog.json").read_text(encoding="utf-8"))["topics"]
    used = set(json.loads((ROOT / "data/used.json").read_text(encoding="utf-8"))["used"]) | set(skip)
    L = learn.load()
    return sorted((t for t in topics if t["id"] not in used and (t.get("score") or 0) >= 7 and not t.get("hold")), key=lambda t: -learn.priority(t, L)), topics, used


def next_topic(wanted=None, skip=()):
    scored, topics, used = queue(skip)
    if wanted:
        return next((t for t in topics if t["id"] == wanted), None)
    ready = [t for t in scored if ready_script(t["id"])]              # v1.09: a topic the night writer has already written goes first
    if ready or scored:
        return (ready or scored)[0]
    return next((t for t in topics if t["id"] not in used and t.get("score") is None), None)


def recent(n=8):
    """Hook frames, punch words and closers of the last scripts: the writer must not repeat them."""
    out = []
    for f in sorted((ROOT / "scripts").glob("*.json"), key=lambda p: p.stat().st_mtime)[-n:]:
        s = json.loads(f.read_text(encoding="utf-8"))
        out.append(f"{s.get('hook_frame', '?')} | punch {s.get('punch')} | closer {s.get('closer', '?')}")
    return out


def valid_look(d):
    t = d.get("things", [])
    return len(t) >= 5 and all(len(x.get("box", [])) == 4 and 0 <= x["box"][0] < x["box"][2] <= 1 and 0 <= x["box"][1] < x["box"][3] <= 1 and x.get("name") for x in t)


def brief(topic, title, facts, look=None):
    """The whole task of one script: the form (prompts/writer.txt) + this topic's facts, the judge's angle, what is in
    the picture, what the last scripts used, and (v1.09) what our own videos taught. The same text for Gemini and
    for the night writer."""
    return ((ROOT / "prompts/writer.txt").read_text(encoding="utf-8") + f"\n\nKIND  {topic['kind']}\nTITLE  {title}\n\nFACTS\n" + "\n".join(f"{i + 1}. {s}" for i, s in enumerate(facts))
            + ("\n\nANGLE\n" + "\n".join(f"{k}: {v if isinstance(v, str) else ' / '.join(v)}" for k, v in topic["angle"].items() if k != "form") if topic.get("angle") else "")
            + "\n\nFORM  " + (form_of(topic) or "choose")
            + ("\n\nLOOK (" + look.get("summary", "") + ")\n" + "\n".join(f"- {t['name']}: words {', '.join(t.get('words', []))}" for t in look["things"]) if look else "")
            + "\n\nAVOID\n" + ("\n".join("- " + r for r in recent()) or "- nothing yet") + learn.notes())


FORMS = ("riddle", "emotion", "scene", "legend")


def form_of(topic):
    """The form the judge gave the topic (v1.12), or None: then the writer chooses by section 3 of the prompt."""
    f = (topic.get("angle") or {}).get("form") or topic.get("form")
    return f if f in FORMS else "legend" if topic.get("kind") == "story" else None


def picture_aspect(path):
    """Width / height of a picture file, or None. The director needs it to know what a framing really shows."""
    try:
        from PIL import Image
        with Image.open(path) as im:
            return round(im.width / im.height, 4)
    except Exception:
        try:
            import cv2
            im = cv2.imread(str(path))
            return round(im.shape[1] / im.shape[0], 4)
        except Exception:
            return None


def target(to):
    """A "show" target as the director knows it: a LOOK name in lower_snake_case, or <evidence key>:<name | full>."""
    to = str(to).strip()
    return to if ":" in to else re.sub(r"\W", "_", to.lower())


def camera_faults(script):
    """v1.10: what the director could not shoot (Nov 14: Gemini's Lucifer sent the camera to ' darkness', which is no
    thing of LOOK, and the run stopped there). Checked while the script is written, so the model gets it back."""
    names, keys = {l["name"] for l in script["look"]}, {e["key"] for e in script.get("evidence", [])}
    out = []
    if script.get("form") == "emotion":                                 # v1.12: the face the video holds, and the small thing in it
        for k in ("home", "detail"):
            if script.get(k) not in names:
                out.append(f"\"{k}\" is '{script.get(k)}', which is not a name of LOOK ({', '.join(sorted(names))}): the emotion form needs the face as \"home\" and the small thing as \"detail\"")
    for s in script["sentences"]:
        for x in (s.get("show") or []) if s.get("slot") != "S2" else []:     # the ident has its own shots (card, portrait): the director reads no "show" there
            to = x.get("to", "")
            if (to.split(":")[0] not in keys) if ":" in to else (to not in names):
                out.append(f"{s.get('slot')}: \"show\" sends the camera to '{to}', which is not a name of LOOK ({', '.join(sorted(names))}): use one of these names or drop that \"show\"")
    if not out:
        try:
            director.build(script)
        except Exception as e:
            out.append(f"the camera cannot follow this script ({e!r}): every \"show\" target and \"detail\" must be a name of LOOK")
    return out


def assemble(topic, facts, lead, look, w, title):
    """The writer's answer + the facts + the pictures = scripts/<id>.json (what director.py reads)."""
    year = next((int(m) for m in re.findall(r"\b(1[0-9]{3})\b", " ".join(s["text"] for s in w["sentences"][:2]))), None)
    creator = topic.get("person") or w.get("portrait_of") or "unknown"
    form = w.get("form") if w.get("form") in FORMS else form_of(topic) or "riddle"
    return {"id": topic["id"], "kind": topic["kind"], "form": form, "hook_frame": w.get("hook_frame"), "closer": w.get("closer"),
            "detail": target(w.get("detail") or ""), "home": target(w["home"]) if w.get("home") else None,
            "subject": {"title": re.sub(r"\s*\(.*\)$", "", title), "creator": creator, "year": year, "wikidata": lead.get("wikidata")},
            "lead": {"commons": lead["commons"], "width_px": 3840, "aspect": lead.get("aspect"), "px": topic.get("picture_px"), "license": lead["license"], "credit": f"{re.sub(chr(95), ' ', lead['commons'].rsplit('.', 1)[0])} — Wikimedia Commons"},
            "portrait": {"of": w["portrait_of"], "credit": f"Portrait of {w['portrait_of']} — Wikimedia Commons", "license": "Public domain"},
            "evidence": [{"key": re.sub(r"\W", "", e["key"])[:12] or f"ev{i}", "query": e["query"], "words": [x.lower() for x in e.get("words", [])],
                          "license": "Public domain", "credit": f"{e['query']} — Wikimedia Commons"} for i, e in enumerate(w.get("evidence", [])[:3])],
            "look": [{"name": re.sub(r"\W", "_", t["name"].lower()), "box": [round(float(v), 3) for v in t["box"]], "words": [x.lower() for x in t.get("words", [])]} for t in look["things"]],
            "punch": w["punch"].upper(), "sentences": [dict(s, show=[dict(x, to=target(x.get("to", ""))) for x in s["show"]]) if s.get("show") else s for s in w["sentences"]],
            "pronounce": w.get("pronounce", {}), "meta": w["meta"],    # v1.10: "Man Face" and " eyes" mean man_face and eyes; v1.11: the comment had cut off pronounce and meta (KeyError 'meta')
            "sources": [{"claim": facts[s["source"] - 1][:200], "url": "https://en.wikipedia.org/wiki/" + title.replace(" ", "_"), "note": f"sentence {s['slot']}"}
                        for s in w["sentences"] if isinstance(s.get("source"), int) and 0 < s["source"] <= len(facts)]}


def write(topic, work):
    work.mkdir(parents=True, exist_ok=True)
    facts, page_image, qid, title = sources.wikipedia(topic["wikipedia"])
    if len(facts) < 8 or not page_image:
        print(f"{topic['id']}: Wikipedia gave {len(facts)} sentences and picture {page_image}: not enough")
        return None
    lic = sources.licence([page_image]).get(page_image.replace("_", " "))
    if not lic or not sources.free(lic[0]):
        print(f"{topic['id']}: the lead picture {page_image} is not free ({lic[0] if lic else 'licence unknown'})")
        return None
    jpg = work / "lead.jpg"
    code, _ = sources.curl("https://commons.wikimedia.org/wiki/Special:FilePath/" + sources.urllib.parse.quote(page_image) + "?width=1600", jpg)
    if code != 200:
        print(f"{topic['id']}: the lead picture did not download ({code})")
        return None
    pic = [{"inline_data": {"mime_type": "image/jpeg", "data": base64.b64encode(jpg.read_bytes()).decode()}}]
    cache = ROOT / "data/look" / f"{topic['id']}.json"                # v1.03: what is in a picture does not change: asked once, kept
    if cache.exists():
        look = json.loads(cache.read_text(encoding="utf-8"))
    else:
        look = gemini((ROOT / "prompts/look.txt").read_text(encoding="utf-8"), valid_look, extra=pic, purpose="look")
        cache.parent.mkdir(parents=True, exist_ok=True)
        cache.write_text(json.dumps(look, indent=1, ensure_ascii=False), encoding="utf-8")
    base = brief(topic, title, facts, look)
    ok = lambda d: isinstance(d.get("sentences"), list) and len(d["sentences"]) >= 12 and d.get("punch") and d.get("portrait_of") and d.get("meta", {}).get("title")
    note, drafts = "", []
    (work / "look.json").write_text(json.dumps(look, indent=1, ensure_ascii=False), encoding="utf-8")
    for attempt in range(4):
        w = gemini(base + note, ok, purpose="script")
        form = w.get("form") if w.get("form") in FORMS else form_of(topic) or "riddle"
        res, words, n = script_check.check([s["text"].strip() for s in w["sentences"]], title, w["punch"], form)
        hard = [f"{name}: {d}" for good, h, name, d in res if not good and h]
        script = None
        if not hard:                                                    # v1.10: the form holds; can the director shoot it?
            script = assemble(topic, facts, {"commons": page_image, "license": lic[0], "wikidata": qid, "aspect": picture_aspect(jpg)}, look, w, title)
            hard = camera_faults(script)
        print(f"{topic['id']}: draft {attempt + 1} ({form}): {words} words, {n} sentences, {len(hard)} failures of the construction")
        for h in hard:
            print("   FAIL", h[:230])
        drafts.append({"draft": attempt + 1, "failures": hard, "answer": w})
        (work / "writer_drafts.json").write_text(json.dumps(drafts, indent=1, ensure_ascii=False), encoding="utf-8")
        if not hard:
            return script
        note = "\n\nYOUR LAST DRAFT BROKE THE FORM. Fix exactly these points and return the whole JSON again:\n" + "\n".join("- " + h for h in hard) + "\n\nThe draft:\n" + json.dumps(w["sentences"], ensure_ascii=False)
    return None


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--topic")
    ap.add_argument("--work", default="work")
    a = ap.parse_args()
    topic = next_topic(a.topic)
    if not topic:
        print("no topic left in data/backlog.json")
        sys.exit(3)
    script = write(topic, ROOT / a.work)
    if not script:
        sys.exit(3)
    out = ROOT / "scripts" / f"{topic['id']}.json"
    out.write_text(json.dumps(script, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"{out}: {sum(len(s['text'].split()) for s in script['sentences'])} words, punch {script['punch']}, portrait of {script['portrait']['of']}, {len(script['evidence'])} evidence pictures")

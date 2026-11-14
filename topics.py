#!/usr/bin/env python3
"""topics.py — what to make next: find candidates, judge each on a scale of 1 to 10, keep the list (v1.03).

    python topics.py --scout 20        ask for 20 new candidates, check them, judge them, merge into data/backlog.json
    python topics.py --rejudge         judge the topics already on the list that have no score yet
    python topics.py --show            print the list

One candidate goes through: prompts/scout.txt (Gemini proposes subjects that fit the profile of the genre's most
watched videos) -> Wikipedia and Commons (the article exists, it has facts, its picture is free and large enough)
-> prompts/judge.txt (Gemini LOOKS at the picture and scores six things: gaze, darkness and one figure, the flip,
threat without violence, "you", a story with a name; total 1-10, and the ANGLE the video should take).
writer.py makes only topics of 7 and more, the highest first, and builds the script on the judge's angle.
"""
import argparse, base64, json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
import sources
from writer import gemini

BACKLOG, USED = ROOT / "data/backlog.json", ROOT / "data/used.json"
MAKE, KEEP, MIN_WIDTH = 7, 5, 1800
KEYS = ("G", "D", "F", "T", "Y", "S")
LIMIT = {"G": 2, "D": 2, "F": 2, "T": 2, "Y": 1, "S": 1}


def slug(title, person):
    s = re.sub(r"\s*\(.*?\)", "", title).lower()
    last = (person or "").split()[-1].lower() if person else ""
    return re.sub(r"[^a-z0-9]+", "-", f"{s} {last}".encode("ascii", "ignore").decode()).strip("-")[:48]


def judge(topic, work):
    """Facts + the picture -> the judge's JSON, or (None, reason) when the candidate cannot be used at all."""
    facts, image, qid, title = sources.wikipedia(topic["wikipedia"])
    if len(facts) < 8 or not image:
        return None, f"Wikipedia: {len(facts)} fact sentences, picture {image}"
    lic = sources.licence([image]).get(image.replace("_", " "))
    if not lic or not sources.free(lic[0]):
        return None, f"the picture is not free ({lic[0] if lic else 'licence unknown'})"
    info = sources.api("commons.wikimedia.org", action="query", titles="File:" + image, prop="imageinfo", iiprop="size")
    width = next(iter((info or {}).get("query", {}).get("pages", {}).values()), {}).get("imageinfo", [{}])[0].get("width", 0)
    if width < MIN_WIDTH:
        return None, f"the picture is only {width} px wide"
    jpg = Path(work) / "judge.jpg"
    code, _ = sources.curl("https://commons.wikimedia.org/wiki/Special:FilePath/" + sources.urllib.parse.quote(image) + "?width=1280", jpg)
    if code != 200:
        return None, f"the picture did not download ({code})"
    prompt = (ROOT / "prompts/judge.txt").read_text(encoding="utf-8") + f"\n\nCANDIDATE  {title} ({topic['kind']})\n\nFACTS\n" + "\n".join(f"{i + 1}. {s}" for i, s in enumerate(facts[:25]))
    ok = lambda d: isinstance(d.get("scores"), dict) and all(k in d["scores"] for k in KEYS)
    j = gemini(prompt, ok, extra=[{"inline_data": {"mime_type": "image/jpeg", "data": base64.b64encode(jpg.read_bytes()).decode()}}], purpose="judge")
    sc = {k: max(0, min(LIMIT[k], int(j["scores"][k]))) for k in KEYS}                 # the code adds up, not the model
    total = 0 if j.get("disqualified") else max(1, sum(sc.values()))
    return dict(topic, wikipedia=title, wikidata=qid, picture=image, picture_px=width, score=total, scores=sc, reasons=j.get("reasons", {}),
                character=j.get("character", {}), angle=j.get("angle") if total >= KEEP else None, disqualified=j.get("disqualified")), None


def load():
    b = json.loads(BACKLOG.read_text(encoding="utf-8"))
    return b, set(json.loads(USED.read_text(encoding="utf-8"))["used"])


def save(b):
    b["topics"].sort(key=lambda t: -(t.get("score") or 0))
    BACKLOG.write_text(json.dumps(b, indent=1, ensure_ascii=False), encoding="utf-8")


def show(b, used):
    print(f"{'score':5s} {'G D F T Y S':11s}  topic")
    for t in b["topics"]:
        sc = t.get("scores")
        mark = "made" if t["id"] in used else "MAKE" if (t.get("score") or 0) >= MAKE else "keep" if (t.get("score") or 0) >= KEEP else "drop" if t.get("score") is not None else "?"
        print(f"{str(t.get('score', '?')):>5s} {' '.join(str(sc[k]) for k in KEYS) if sc else '- - - - - -':11s}  [{mark}] {t['wikipedia']} | {(t.get('angle') or {}).get('detail', t.get('disqualified') or '')}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--scout", type=int, default=0)
    ap.add_argument("--rejudge", action="store_true")
    ap.add_argument("--show", action="store_true")
    ap.add_argument("--work", default="work")
    a = ap.parse_args()
    b, used = load()
    work = ROOT / a.work
    work.mkdir(exist_ok=True)
    if a.rejudge:
        for i, t in enumerate(b["topics"]):
            if t.get("score") is None and t["id"] not in used:
                j, why = judge(t, work)
                b["topics"][i] = j or dict(t, score=0, disqualified=why)
                print(f"judged {t['wikipedia']}: {b['topics'][i]['score']}" + (f" ({why})" if why else ""))
                save(b)
        b, used = load()
    if a.scout:
        have = {t["wikipedia"].lower() for t in b["topics"]}
        prompt = (ROOT / "prompts/scout.txt").read_text(encoding="utf-8").replace("{N}", str(a.scout)).replace("{AVOID}", "; ".join(sorted(t["wikipedia"] for t in b["topics"])))
        c = gemini(prompt, lambda d: isinstance(d.get("candidates"), list) and len(d["candidates"]) >= 3, purpose="scout")
        for cand in c["candidates"][:a.scout]:
            if not cand.get("wikipedia") or cand["wikipedia"].lower() in have:
                continue
            t = {"id": slug(cand["wikipedia"], cand.get("person")), "kind": cand.get("kind", "artwork"), "wikipedia": cand["wikipedia"], "person": cand.get("person"), "why": cand.get("why")}
            j, why = judge(t, work)
            if j is None:
                print(f"rejected {cand['wikipedia']}: {why}")
                continue
            if j["wikipedia"].lower() in have:
                continue
            have.add(j["wikipedia"].lower())
            b["topics"].append(j)
            print(f"judged {j['wikipedia']}: {j['score']}  {j['scores']}  {(j.get('angle') or {}).get('detail', j.get('disqualified') or '')}")
            save(b)
    save(b)
    show(*load())

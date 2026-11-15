#!/usr/bin/env python3
"""night_writer.py — the tools of the nightly Claude writer (v1.09; its rules: docs/NIGHT_WRITER.md).

    python tools/night_writer.py stock [--want 4]            what is ready, what to write tonight
    python tools/night_writer.py brief <topic id>            facts + the lead picture + the whole task -> work/night/<id>/
    python tools/night_writer.py crops <topic id> <look.json>    every box of LOOK cut out, to look at (are the boxes right?)
    python tools/night_writer.py save <topic id> <answer.json> <look.json>    check, assemble -> scripts/<id>.json
    python tools/night_writer.py preview                     the last dry run of GitHub Actions (branch "preview") -> work/preview/
    python tools/night_writer.py sheet <topic id> [dir]      one frame per caption line of the video in dir (default
                                                             work/preview: final.mp4 + timeline.json), to look at

The writer is Claude itself: these commands only fetch, check and file. `save` refuses a script that breaks the
construction (tools/script_check.py, the same gate as for Gemini's scripts) and marks the file
"written_by": "Claude (night writer) ...", which is what makes bot.py take it instead of asking Gemini.
No GEMINI_API_KEY is needed here: Claude looks at the picture itself (LOOK) and writes the answer of
prompts/writer.txt section 7.
"""
import argparse, json, re, subprocess, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))
import sources, script_check, writer, director

NIGHT = ROOT / "work/night"


def stock(want):
    scored, topics, used = writer.queue()
    ready = [t for t in scored if writer.ready_script(t["id"])]
    todo = [t for t in scored if not writer.ready_script(t["id"])][:max(0, want - len(ready))]
    print(f"queue: {len(scored)} topics of 7 and more are not made yet; ready scripts of the night writer: {len(ready)} (wanted {want})")
    for t in ready:
        print(f"  READY  {t['score']:>2}  {t['id']}")
    for t in todo:
        old = " | REWRITE: the script on main is from before the forms (v1.12)" if (ROOT / "scripts" / f"{t['id']}.json").exists() else ""
        print(f"  WRITE  {t['score']:>2}  {t['id']}  | {t['wikipedia']} | angle: {(t.get('angle') or {}).get('detail')} | form: {writer.form_of(t) or 'choose'}{old}")
    for f in sorted((ROOT / "scripts").glob("*.failed.json")):
        s = json.loads(f.read_text(encoding="utf-8"))
        print(f"  FAILED EARLIER  {s['id']}: {str(s.get('failed'))[:200]}")
    if len(scored) < 6:
        print(f"  NOTE  only {len(scored)} topics left: say so in the report (the Sunday scout adds new ones)")
    return 0


def brief(tid):
    topic = writer.next_topic(tid)
    if not topic:
        print("no such topic in data/backlog.json:", tid)
        return 3
    d = NIGHT / tid
    d.mkdir(parents=True, exist_ok=True)
    facts, image, qid, title = sources.wikipedia(topic["wikipedia"])
    image = image or topic.get("picture")
    if len(facts) < 8 or not image:
        print(f"{tid}: Wikipedia gave {len(facts)} sentences and picture {image}: not enough (skip this topic, say so in the report)")
        return 3
    lic = sources.licence([image]).get(image.replace("_", " "))
    if lic and not sources.free(lic[0]):
        print(f"{tid}: the lead picture {image} is not free ({lic[0]}): skip this topic")
        return 3
    code, _ = sources.curl("https://commons.wikimedia.org/wiki/Special:FilePath/" + sources.urllib.parse.quote(image) + "?width=1600", d / "lead.jpg")
    if code != 200:
        print(f"{tid}: the lead picture did not download ({code}); try again in a few minutes")
        return 3
    cache = ROOT / "data/look" / f"{tid}.json"
    look = json.loads(cache.read_text(encoding="utf-8")) if cache.exists() else None
    (d / "facts.json").write_text(json.dumps({"facts": facts, "image": image, "wikidata": qid, "title": title, "aspect": writer.picture_aspect(d / "lead.jpg"),
                                              "license": lic[0] if lic else "Public domain"}, indent=1, ensure_ascii=False), encoding="utf-8")
    (d / "brief.txt").write_text(writer.brief(topic, title, facts, look), encoding="utf-8")
    print(f"{d / 'brief.txt'}: the task ({len(facts)} facts, the judge's angle, AVOID)")
    print(f"{d / 'lead.jpg'}: LOOK AT IT before writing" + ("; LOOK is cached in data/look (check it with `crops`)" if look else "; make look.json yourself by prompts/look.txt"))
    print(f"licence of the lead picture: {lic[0] if lic else 'Commons API busy; the judge checked it was free, the runner re-checks at the upload'}")
    return 0


def font(size):
    from PIL import ImageFont
    return ImageFont.truetype(str(ROOT / "assets/fonts/Inter-SemiBold.ttf"), size)


def crops(tid, look_path):
    from PIL import Image, ImageDraw
    d = NIGHT / tid
    look = json.loads(Path(look_path).read_text(encoding="utf-8"))
    if not writer.valid_look(look):
        print("look.json is not valid: 5+ things, each with a name and box [x0, y0, x1, y1] as fractions, x0 < x1, y0 < y1")
        return 1
    im = Image.open(d / "lead.jpg").convert("RGB")
    W, H = im.size
    over, dr = im.copy(), None
    dr = ImageDraw.Draw(over)
    cell, cols = 420, 4
    things = look["things"]
    sheet = Image.new("RGB", (cols * cell, -(-len(things) // cols) * (cell + 44)), (18, 18, 18))
    ds = ImageDraw.Draw(sheet)
    for i, t in enumerate(things):
        x0, y0, x1, y1 = (t["box"][0] * W, t["box"][1] * H, t["box"][2] * W, t["box"][3] * H)
        dr.rectangle([x0, y0, x1, y1], outline=(255, 40, 40), width=max(2, W // 400))
        dr.text((x0 + 6, y0 + 4), f"{i + 1} {t['name']}", fill=(255, 255, 0), font=font(max(16, W // 60)))
        c = im.crop((int(x0), int(y0), int(x1), int(y1)))
        c.thumbnail((cell - 8, cell - 8))
        ox, oy = (i % cols) * cell, (i // cols) * (cell + 44)
        sheet.paste(c, (ox + (cell - c.width) // 2, oy + 40 + (cell - c.height) // 2))
        ds.text((ox + 6, oy + 6), f"{i + 1} {t['name']}: {', '.join(t.get('words', []))}"[:46], fill=(255, 255, 255), font=font(17))
    over.thumbnail((1600, 1600))
    over.save(d / "boxes.jpg", quality=88)
    sheet.save(d / "crops.jpg", quality=88)
    print(f"{d / 'boxes.jpg'} (the picture with every box) and {d / 'crops.jpg'} (every box cut out): LOOK AT BOTH. A crop must show the thing its words name, whole and tight.")
    return 0


def save(tid, answer_path, look_path):
    topic = writer.next_topic(tid)
    d = NIGHT / tid
    if not topic or not (d / "facts.json").exists():
        print("run `brief` for this topic first")
        return 1
    fx = json.loads((d / "facts.json").read_text(encoding="utf-8"))
    w, look = json.loads(Path(answer_path).read_text(encoding="utf-8")), json.loads(Path(look_path).read_text(encoding="utf-8"))
    bad = []
    if not writer.valid_look(look):
        bad.append("look.json: 5+ things, each with a name and a box of fractions")
    names = {re.sub(r"\W", "_", t["name"].lower()) for t in look.get("things", [])}
    sents = w.get("sentences") or []
    if not (isinstance(sents, list) and len(sents) >= 12 and w.get("punch") and w.get("portrait_of") and (w.get("meta") or {}).get("title")):
        bad.append("answer: needs sentences (12+), punch, portrait_of, meta.title (prompts/writer.txt section 7)")
    else:
        form = w.get("form") if w.get("form") in writer.FORMS else None
        if not form:
            print("NOT SAVED:\n  - answer: \"form\" must be riddle, emotion, scene or legend (prompts/writer.txt section 3)")
            return 1
        res, words, n = script_check.check([s["text"].strip() for s in sents], fx["title"], w["punch"], form)
        bad += [f"construction: {name}: {det}" for ok, hard, name, det in res if not ok and hard]
        for ok, hard, name, det in res:
            if not ok and not hard:
                print("warn", name, "|", det)
        last = re.sub(r"[^\w']", "", sents[0]["text"].split()[-1]).upper()
        if form in ("riddle", "legend") and w["punch"].upper() != last:
            bad.append(f"punch is {w['punch']!r} but the hook ends on {last!r}")
        if re.sub(r"\W", "_", str(w.get("detail", "")).lower()) not in names:
            bad.append(f"detail {w.get('detail')!r} is not a name of look.json ({', '.join(sorted(names))})")
        if form in ("emotion", "scene") and re.sub(r"\W", "_", str(w.get("home", "")).lower()) not in names:
            bad.append(f"home {w.get('home')!r} is not a name of look.json: the {form} form needs the face the video opens on")
        for s in sents:
            if s.get("kind") == "FACT" and not (isinstance(s.get("source"), int) and 0 < s["source"] <= len(fx["facts"])):
                bad.append(f"{s.get('slot')}: a FACT needs \"source\": the number of its FACTS sentence (1-{len(fx['facts'])})")
            for sh in s.get("show", []):
                if ":" not in sh.get("to", "") and re.sub(r"\W", "_", sh.get("to", "").lower()) not in names:
                    bad.append(f"{s.get('slot')}: show.to {sh.get('to')!r} is not a name of look.json")
        m = w["meta"]
        if len(m["title"]) > 70 or not m.get("description") or not m.get("tags") or not m.get("question"):
            bad.append("meta: title under 70 characters, description, tags and question are all needed")
    if bad:
        print("NOT SAVED:\n" + "\n".join("  - " + b for b in bad))
        return 1
    script = writer.assemble(topic, fx["facts"], {"commons": fx["image"], "license": fx["license"], "wikidata": fx["wikidata"], "aspect": fx.get("aspect")}, look, w, fx["title"])
    bad = writer.camera_faults(script)
    if bad:
        print("NOT SAVED:\n" + "\n".join("  - " + b for b in bad))
        return 1
    script["written_by"] = f"Claude (night writer), {time.strftime('%Y-%m-%d', time.gmtime())}"
    try:
        story = director.build(script)
    except Exception as e:
        print("NOT SAVED: the director cannot shoot it:", repr(e))
        return 1
    out = ROOT / "scripts" / f"{tid}.json"
    out.write_text(json.dumps(script, indent=1, ensure_ascii=False), encoding="utf-8")
    old = out.with_name(tid + ".failed.json")
    if old.exists():
        old.unlink()
    (ROOT / "data/look").mkdir(exist_ok=True)
    (ROOT / "data/look" / f"{tid}.json").write_text(json.dumps(look, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"{out}: form {script['form']}, {words} words, {n} sentences, punch {script['punch']}, portrait of {script['portrait']['of']}, {len(script['evidence'])} evidence pictures")
    print("the director's shots (caption line -> where the camera goes):")
    for ln in story["lines"]:
        cam = ln.get("cam")
        cues = cam if isinstance(cam, list) else [cam] if cam else []
        print(f"  [{ln['beat']:9s}] {ln['say']:58s} " + " ".join(f"->{c.get('image') or ((c.get('scene') + ':') if c.get('scene') else '') + str(c.get('to'))}" + (f"@{c['on']}" if c.get("on") else "") for c in cues))
    print(f"next: commit and push the script, start the dry run (docs/NIGHT_WRITER.md step 6), then `preview` and `sheet {tid}`")
    return 0


def preview():
    """The files of the last manual run (the workflow force-pushes them to the branch "preview"). The cloud sandbox
    cannot render: Wikimedia answers 429 to it, so the video is made by a dry run on GitHub and looked at here."""
    out = ROOT / "work/preview"
    subprocess.run(["rm", "-rf", str(out)])
    out.mkdir(parents=True)
    f = subprocess.run(["git", "-C", str(ROOT), "fetch", "-q", "origin", "+preview:refs/remotes/origin/preview"], capture_output=True, text=True)
    if f.returncode:
        print("the preview branch did not come:", f.stderr.strip()[:200])
        return 1
    tar = subprocess.run(["git", "-C", str(ROOT), "archive", "origin/preview"], capture_output=True).stdout
    subprocess.run(["tar", "-x", "-C", str(out)], input=tar)
    msg = subprocess.run(["git", "-C", str(ROOT), "log", "-1", "--format=%s (%cr)", "origin/preview"], capture_output=True, text=True).stdout.strip()
    print(f"{out}: {msg}: " + ", ".join(sorted(p.name for p in out.iterdir())))
    rep = out / "report.json"
    if rep.exists():
        r = json.loads(rep.read_text())
        print(f"story {r['story']}: {r['numbers']}")
        for c in r["checks"]:
            print(("OK   " if c["ok"] else "FAIL ") + f"{c['check']}: {c['got']}")
    return 0


def sheet(tid, src="work/preview"):
    from PIL import Image, ImageDraw
    src = ROOT / src
    mp4, tl = src / "final.mp4", (src / "timeline.json" if (src / "timeline.json").exists() else src / "final_work/timeline.json")
    if not mp4.exists() or not tl.exists():
        print(f"no final.mp4 + timeline.json in {src}: start a dry run (docs/NIGHT_WRITER.md), then `preview`")
        return 1
    T = json.loads(tl.read_text())
    lines, (sw, sh), y_off = T["lines"], T.get("stage", [1080, 1920]), T.get("y_off", 0)
    d = NIGHT / tid
    d.mkdir(parents=True, exist_ok=True)
    w, cols = 400, 4                                                   # only the stage (the picture with its caption), not the black bars
    h = int(w * sh / sw)
    out = Image.new("RGB", (cols * w, -(-len(lines) // cols) * (h + 50)), (18, 18, 18))
    dr = ImageDraw.Draw(out)
    for i, ln in enumerate(lines):
        t = ln["t0"] + 0.7 * (ln["t1"] - ln["t0"])
        raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t:.2f}", "-i", str(mp4), "-frames:v", "1", "-vf", f"crop={sw}:{sh}:0:{y_off},scale={w}:{h}", "-f", "image2pipe", "-vcodec", "png", "-"], capture_output=True).stdout
        ox, oy = (i % cols) * w, (i // cols) * (h + 50)
        if raw:
            import io
            out.paste(Image.open(io.BytesIO(raw)).convert("RGB"), (ox, oy + 50))
        dr.text((ox + 4, oy + 4), f"{ln['t0']:.1f}s {ln['beat']}", fill=(255, 220, 0), font=font(14))
        dr.text((ox + 4, oy + 24), ln["say"][:52], fill=(255, 255, 255), font=font(13))
    out.save(d / "sheet.jpg", quality=85)
    print(f"{d / 'sheet.jpg'}: one frame per caption line ({len(lines)}). LOOK: is the thing each line names in its frame, sharp and whole?")
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["stock", "brief", "crops", "save", "preview", "sheet"])
    ap.add_argument("args", nargs="*")
    ap.add_argument("--want", type=int, default=4)
    a = ap.parse_args()
    sys.exit(stock(a.want) if a.cmd == "stock" else {"brief": brief, "crops": crops, "save": save, "preview": preview, "sheet": sheet}[a.cmd](*a.args))

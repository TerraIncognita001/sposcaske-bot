#!/usr/bin/env python3
"""bot.py — one run = one video.

    python bot.py --story <id> --dry-run          -> work/final.mp4, work/metadata.json, work/report.json
    python bot.py --write --dry-run               the bot writes the next topic of data/backlog.json itself first

Steps: [writer.py: topic -> scripts/<id>.json] -> director.py: script -> story (the maket's camera, red word, card,
portrait) -> the script gate (tools/script_check.py) -> the pictures (sources.py: download, find, licence) -> the
render with its picture-word audit (render.py) -> conformance to the maket (frame, length, loudness, the opening
sound, the red word, the portrait) -> the metadata the upload would use. A hand-made stories/<id>.json is used when
there is no scripts/<id>.json.
Exit codes as in the warehouse: 0 = a video was made, 3 = this story cannot make a good video (the workflow may try
another), 1 = a bug.
v1.09: with --write the bot first takes the night writer's ready script of the topic (scripts/<id>.json marked
"written_by": "Claude ..."), as it is, with no Gemini request. Only a topic without one, or whose ready script failed
a check, is written by Gemini (writer.py). At an upload the caption timings go to data/timeline/<story>.json, so
stats_now.py can say which line the viewers left at.
"""
import argparse, json, re, subprocess, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))


def conform(mp4, story, work):
    F = json.loads((ROOT / "format.json").read_text(encoding="utf-8"))
    pr = json.loads(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration,size:stream=codec_type,width,height,r_frame_rate,channels",
                                    "-of", "json", str(mp4)], capture_output=True, text=True).stdout)
    v = next(s for s in pr["streams"] if s["codec_type"] == "video")
    a = next(s for s in pr["streams"] if s["codec_type"] == "audio")
    err = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(mp4), "-af", "ebur128=peak=true", "-f", "null", "-"], capture_output=True, text=True).stderr
    lufs = float(re.findall(r"I:\s+(-?[\d.]+) LUFS", err)[-1])
    peak = float(re.findall(r"Peak:\s+(-?[\d.]+) dBFS", err)[-1])
    tl = json.loads((work / "final_work" / "timeline.json").read_text())
    import numpy as np                                                 # v1.02: every video opens with THE sound (Andrii's file)
    dec = lambda f, t: np.frombuffer(subprocess.run(["ffmpeg", "-v", "error", "-i", str(f), "-t", str(t), "-ac", "2", "-ar", "44100", "-f", "f32le", "-"],
                                                    capture_output=True).stdout, np.float32).reshape(-1, 2)
    head, ref = dec(mp4, 1.5), dec(ROOT / F["audio"]["stinger"]["file"], 1.5)
    k = min(len(head), len(ref))
    intro = float(min(np.corrcoef(head[:k, c], ref[:k, c])[0, 1] for c in (0, 1))) if k > 40000 else 0.0
    dur, size = float(pr["format"]["duration"]), int(pr["format"]["size"])
    audit = tl["focus_audit"]
    lo = min([F["length"]["seconds_min"]] + F["length"]["forms"].get(story.get("form"), {}).get("seconds", [])[:1])    # v1.24: the hold form may be 30 s (Andrii, Nov 27: 'Так')
    rows = [("frame 1080x1920", v["width"] == F["canvas"]["w"] and v["height"] == F["canvas"]["h"], f"{v['width']}x{v['height']}"),
            ("30 frames a second", v["r_frame_rate"] == f"{F['canvas']['fps']}/1", v["r_frame_rate"]),
            (f"length {lo}-{F['length']['seconds_max']} s", lo <= dur <= F["length"]["seconds_max"], f"{dur:.1f} s"),
            (f"loudness {F['audio']['mix']['lufs']} LUFS +-1", abs(lufs - F["audio"]["mix"]["lufs"]) <= 1.0, f"{lufs:.1f} LUFS"),
            ("true peak under 0 dBFS", peak <= 0.0, f"{peak:.1f} dBFS"),
            ("stereo sound (the opening sound is wide)", a["channels"] == 2, f"{a['channels']} ch"),
            ("voice starts after the opening sound", abs(tl["events"]["voice_start"] - F["timing"]["lead_in_s"]) < 0.05, f"{tl['events']['voice_start']:.2f} s"),
            ("opens with the owner's sound, in stereo, untouched", intro >= 0.97, f"correlation {intro:.3f}"),
            ("the red punch word is on screen after the hook", bool(story.get("hook_title")) and tl["events"]["title_off"] > tl["events"]["title_on"], str(story.get("hook_title"))),
            ("the portrait card of the person named in the ident", len(tl["events"]["image_shots"]) >= 1, f"{len(tl['events']['image_shots'])} shot"),
            ("every named thing is in the frame", all(x["ok"] for x in audit), f"{sum(x['ok'] for x in audit)} of {len(audit)}"),
            ("file under 95 MB (the preview branch takes 100)", size < 95e6, f"{size / 1e6:.1f} MB")]
    return rows, {"seconds": round(dur, 1), "lufs": lufs, "peak_dbfs": peak, "mb": round(size / 1e6, 1)}


def clean_title(title, story):
    """v1.22 (Andrii, Nov 24: 'Приберіть хештеги з назв ... коротке речення без великих літер'): a title written under
    v1.18 ('The Old Man Who Ate His Soup Next to DEATH #history #art') -> one sentence in sentence case, no hashtags,
    no '...'. A word keeps its capital when it is a name: capitalised inside the script's sentences, or in the
    painter's or the portrait's name."""
    t = re.sub(r"\s*#\w+", "", title or "").replace("...", ",").replace("…", ",").strip(" ,")
    text = " ".join(x if isinstance(x, str) else x.get("text", "") for x in story.get("sentences", [])) + " " + " ".join(str(x) for x in (
        (story.get("artwork") or {}).get("artist"), (story.get("portrait") or {}).get("of")))
    names = {w for w in re.findall(r"(?<![.!?]\s)(?<!^)\b([A-Z][a-z'’]+)", text)}
    words = t.split()
    out = [words[0][:1].upper() + words[0][1:].lower() if words and words[0].isupper() and len(words[0]) > 1 else (words[0] if words else "")]
    for w in words[1:]:
        core = re.sub(r"[^\w'’]", "", w)
        if re.fullmatch(r"[IVXLCDM]+", core) or core.capitalize() in names or core in names:
            out.append(w if not w.isupper() else w.capitalize())
        else:
            out.append(w.lower())
    return " ".join(out)


def metadata(story, report):
    m, art = story["meta"], story["artwork"]
    credits = [f"- {v.get('credit') or k}" for k, v in story["images"].items()]
    desc = m["description"].strip() + "\n\nPictures (public domain, Wikimedia Commons):\n" + "\n".join(credits) + "\n\nSources:\n" + "\n".join(
        f"- {s['url']}" for s in story.get("sources", [])) + "\n\nThe narration is a synthetic voice."
    title = clean_title(m["title"], story)
    desc += "\n\n#history #art"
    return {"title": title[:100], "description": desc, "tags": m.get("tags", []), "pinned_question": m.get("question"), "categoryId": "27",
            "story": story["id"], "artwork": f"{art['title']} ({art['artist']}, {art['year']})", "pictures": report}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--story")
    ap.add_argument("--write", action="store_true", help="write the next topic with writer.py first (needs GEMINI_API_KEY)")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--upload", choices=["no", "private", "slot"], default="no",
                    help="private = upload private with no publish time; slot = private, public at env PUBLISH_AT (the gate's slot)")
    ap.add_argument("--work", default="work")
    a = ap.parse_args()
    if a.dry_run:
        a.upload = "no"
    elif a.upload == "no":
        print("nothing to do: give --dry-run (make only) or --upload private|slot")
        return 1
    t0, work = time.time(), (ROOT / a.work)
    work.mkdir(exist_ok=True)
    if a.write and not a.story:                                         # v1.04: a topic that cannot be written is skipped, up to three tries
        import writer
        skip = []
        for _ in range(3):
            topic = writer.next_topic(skip=skip)
            if not topic:
                break
            ready = writer.ready_script(topic["id"])
            code = run_one(a, topic["id"], work, t0, write=not ready)
            if code == 3 and ready:                                     # v1.09: the night writer's script failed a check -> marked, Gemini writes the topic
                s = json.loads(ready.read_text(encoding="utf-8"))
                s["failed"] = WHY[-1] if WHY else "a check of the bot refused it"
                ready.write_text(json.dumps(s, indent=1, ensure_ascii=False), encoding="utf-8")
                ready.replace(ready.with_name(ready.stem + ".failed.json"))    # kept beside the new script for the night writer to read
                print(f"== {topic['id']}: the night writer's script failed ({s['failed'][:160]}): Gemini writes it")
                code = run_one(a, topic["id"], work, t0, write=True)
            if code != 3:
                return code
            skip.append(topic["id"])
            print(f"== {topic['id']} cannot make a good video: next topic")
        print("no topic made a video in this run")
        return 3
    return run_one(a, a.story, work, t0, write=a.write)


WHY = []                                                               # v1.09: why the last story was refused, in words


def refuse(msg):
    WHY.append(msg)
    return 3


def run_one(a, story_id, work, t0, write=False):
    a = argparse.Namespace(**dict(vars(a), story=story_id))
    if write:
        import writer
        topic = writer.next_topic(a.story)
        script = topic and writer.write(topic, work)
        if not script:
            print("the writer has no script for this topic")
            return 3
        (ROOT / "scripts" / f"{a.story}.json").write_text(json.dumps(script, indent=1, ensure_ascii=False), encoding="utf-8")
    spath, path = ROOT / "scripts" / f"{a.story}.json", ROOT / "stories" / f"{a.story}.json"
    if spath.exists():                                                  # the director shoots every script the same way
        import director
        script = json.loads(spath.read_text(encoding="utf-8"))
        print(f"== script by {script.get('written_by') or 'Gemini (writer.py)'}")
        try:
            story = director.build(script)
        except Exception as e:                                          # v1.09: a hand-written script may lack a field
            print("the director cannot shoot this script:", repr(e)[:200])
            return refuse(f"director: {e!r}"[:200])
        path = work / "directed.json"
        path.write_text(json.dumps(story, indent=1, ensure_ascii=False), encoding="utf-8")
        print(f"== directed: {len(story['lines'])} caption lines, {sum(1 for l in story['lines'] if l.get('cam'))} with camera cues")
    elif not path.exists():
        print(f"no such story or script: {a.story}")
        return 3
    story = json.loads(path.read_text(encoding="utf-8"))
    print(f"== story {story['id']}: {story['artwork']['title']} ({story['artwork']['artist']}, {story['artwork']['year']})")

    import script_check
    text = " ".join(l["say"] for l in story["lines"])
    res, words, n = script_check.check(story.get("sentences") or script_check.sentences(text), story["artwork"]["title"], story.get("hook_title"), story.get("form") or "riddle")    # v1.12: each form has its own gate; the script's own sentences, not the caption lines glued back
    hard = [(name, d) for ok, h, name, d in res if not ok and h]
    for ok, h, name, d in res:
        if not ok:
            print(("FAIL " if h else "warn ") + name + (" | " + d if d else ""))
    print(f"== script gate: {words} words, {n} sentences, {len(hard)} hard failures")
    if hard:
        return refuse("script gate: " + "; ".join(f"{n_} ({d})" for n_, d in hard))

    import sources
    story, report, bad = sources.resolve(path, work)
    for f_ in json.loads((work / "sources.json").read_text(encoding="utf-8")).get("found", []):
        print("found   ", f_)
    for r in report:
        print(f"picture {r['key']:10s} {r.get('from', '-'):22s} licence: {r.get('licence_on_commons') or r.get('licence_in_story')}")
    if bad:
        print("\n".join("PROBLEM " + b for b in bad))
        return refuse("pictures: " + "; ".join(bad))

    import render
    try:
        render.render(work / "story.json", work / "final.mp4")
    except SystemExit as e:                                             # the picture-word audit refused the story
        print("render refused:", e)
        return refuse(f"render: {e}")

    rows, numbers = conform(work / "final.mp4", story, work)
    for name, ok, got in rows:
        print(("OK   " if ok else "FAIL ") + f"{name}: {got}")
    meta = metadata(story, report)
    (work / "metadata.json").write_text(json.dumps(meta, indent=1, ensure_ascii=False), encoding="utf-8")
    (work / "report.json").write_text(json.dumps({"story": story["id"], "numbers": numbers, "checks": [{"check": n_, "ok": bool(o), "got": g} for n_, o, g in rows],
                                                  "bot_seconds": round(time.time() - t0)}, indent=1), encoding="utf-8")
    print(f"== done in {time.time() - t0:.0f} s: work/final.mp4, {numbers}")
    if not all(o for _, o, _ in rows):
        return refuse("maket checks: " + "; ".join(f"{n_} ({g})" for n_, o, g in rows if not o))
    if a.upload != "no":                                                # v1.04: only a video that passed every check goes up
        import os, upload, gate
        at = os.environ.get("PUBLISH_AT") if a.upload == "slot" else None
        if a.upload == "slot" and not at:
            print("--upload slot needs PUBLISH_AT from the gate")
            return 1
        vid = upload.upload(work / "final.mp4", meta, at)
        used = json.loads((ROOT / "data/used.json").read_text(encoding="utf-8"))
        used["used"] = sorted(set(used["used"]) | {story["id"]})
        (ROOT / "data/used.json").write_text(json.dumps(used, ensure_ascii=False), encoding="utf-8")
        tl = json.loads((work / "final_work" / "timeline.json").read_text())    # v1.09: when each caption line is spoken, for the retention curve
        (ROOT / "data/timeline").mkdir(exist_ok=True)
        (ROOT / "data/timeline" / f"{story['id']}.json").write_text(json.dumps({"total": tl["total"], "lines": tl["lines"]}, indent=1, ensure_ascii=False), encoding="utf-8")
        key = os.environ.get("SLOT") or f"manual-{time.strftime('%Y%m%d-%H%M%S', time.gmtime())}"
        gate.record(key, video=vid, story=story["id"], title=meta["title"], publish_at=at, seconds=numbers["seconds"],
                    **({"comment_pending": meta["pinned_question"] + " 👇"} if meta.get("pinned_question") and at else {}))
    return 0


if __name__ == "__main__":
    sys.exit(main())

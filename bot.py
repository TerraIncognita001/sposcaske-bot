#!/usr/bin/env python3
"""bot.py — one run = one video (v1.01: the dry-run path only).

    python bot.py --story <id> --dry-run          -> work/final.mp4, work/metadata.json, work/report.json

Steps: the script gate (tools/script_check.py) -> the pictures (sources.py) -> the render with its picture-word
audit (render.py) -> conformance to the format (length, frame, loudness) -> the metadata the upload would use.
Exit codes as in the warehouse: 0 = a video was made, 3 = this story cannot make a good video (the workflow may try
another), 1 = a bug. Uploading is not built yet: without --dry-run the bot refuses.
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
    dur, size = float(pr["format"]["duration"]), int(pr["format"]["size"])
    audit = tl["focus_audit"]
    rows = [("frame 1080x1920", v["width"] == F["canvas"]["w"] and v["height"] == F["canvas"]["h"], f"{v['width']}x{v['height']}"),
            ("30 frames a second", v["r_frame_rate"] == f"{F['canvas']['fps']}/1", v["r_frame_rate"]),
            (f"length {F['length']['seconds_min']}-{F['length']['seconds_max']} s", F["length"]["seconds_min"] <= dur <= F["length"]["seconds_max"], f"{dur:.1f} s"),
            (f"loudness {F['audio']['mix']['lufs']} LUFS +-1", abs(lufs - F["audio"]["mix"]["lufs"]) <= 1.0, f"{lufs:.1f} LUFS"),
            ("true peak under 0 dBFS", peak <= 0.0, f"{peak:.1f} dBFS"),
            ("stereo sound (the opening sound is wide)", a["channels"] == 2, f"{a['channels']} ch"),
            ("voice starts after the opening sound", abs(tl["events"]["voice_start"] - F["timing"]["lead_in_s"]) < 0.05, f"{tl['events']['voice_start']:.2f} s"),
            ("every named thing is in the frame", all(x["ok"] for x in audit), f"{sum(x['ok'] for x in audit)} of {len(audit)}"),
            ("file under 95 MB (the preview branch takes 100)", size < 95e6, f"{size / 1e6:.1f} MB")]
    return rows, {"seconds": round(dur, 1), "lufs": lufs, "peak_dbfs": peak, "mb": round(size / 1e6, 1)}


def metadata(story, report):
    m, art = story["meta"], story["artwork"]
    credits = [f"- {v.get('credit') or k}" for k, v in story["images"].items()]
    desc = m["description"].strip() + "\n\nPictures (public domain, Wikimedia Commons):\n" + "\n".join(credits) + "\n\nSources:\n" + "\n".join(
        f"- {s['url']}" for s in story.get("sources", [])) + "\n\nThe narration is a synthetic voice."
    return {"title": m["title"][:100], "description": desc, "tags": m.get("tags", []), "pinned_question": m.get("question"), "categoryId": "27",
            "story": story["id"], "artwork": f"{art['title']} ({art['artist']}, {art['year']})", "pictures": report}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--story", required=True)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--work", default="work")
    a = ap.parse_args()
    if not a.dry_run:
        print("upload is not built yet (v1.01 makes dry runs only): run with --dry-run")
        return 1
    t0, work = time.time(), (ROOT / a.work)
    work.mkdir(exist_ok=True)
    path = ROOT / "stories" / f"{a.story}.json"
    if not path.exists():
        print(f"no such story: {path}")
        return 3
    story = json.loads(path.read_text(encoding="utf-8"))
    print(f"== story {story['id']}: {story['artwork']['title']} ({story['artwork']['artist']}, {story['artwork']['year']})")

    import script_check
    text = " ".join(l["say"] for l in story["lines"])
    res, words, n = script_check.check(script_check.sentences(text), story["artwork"]["title"], story.get("hook_title"))
    hard = [(name, d) for ok, h, name, d in res if not ok and h]
    for ok, h, name, d in res:
        if not ok:
            print(("FAIL " if h else "warn ") + name + (" | " + d if d else ""))
    print(f"== script gate: {words} words, {n} sentences, {len(hard)} hard failures")
    if hard:
        return 3

    import sources
    story, report, bad = sources.resolve(path, work)
    for r in report:
        print(f"picture {r['key']:10s} {r.get('from', '-'):22s} licence: {r.get('licence_on_commons') or r.get('licence_in_story')}")
    if bad:
        print("\n".join("PROBLEM " + b for b in bad))
        return 3

    import render
    try:
        render.render(work / "story.json", work / "final.mp4")
    except SystemExit as e:                                             # the picture-word audit refused the story
        print("render refused:", e)
        return 3

    rows, numbers = conform(work / "final.mp4", story, work)
    for name, ok, got in rows:
        print(("OK   " if ok else "FAIL ") + f"{name}: {got}")
    meta = metadata(story, report)
    (work / "metadata.json").write_text(json.dumps(meta, indent=1, ensure_ascii=False), encoding="utf-8")
    (work / "report.json").write_text(json.dumps({"story": story["id"], "numbers": numbers, "checks": [{"check": n_, "ok": bool(o), "got": g} for n_, o, g in rows],
                                                  "bot_seconds": round(time.time() - t0)}, indent=1), encoding="utf-8")
    print(f"== done in {time.time() - t0:.0f} s: work/final.mp4, {numbers}")
    return 0 if all(o for _, o, _ in rows) else 3


if __name__ == "__main__":
    sys.exit(main())

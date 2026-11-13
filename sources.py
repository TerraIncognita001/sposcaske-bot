#!/usr/bin/env python3
"""sources.py — the pictures of a story, from Wikimedia Commons (v1.01).

    python sources.py stories/<id>.json work/        -> work/img/<key>.jpg, work/story.json, work/sources.json

For every picture of the story that names a Commons file (`"commons": "<File name>"`):
  1. a copy kept in the repository (`stories/img/<story id>/<key>.jpg`) is used when it is there;
  2. otherwise the file is downloaded at `width_px` through Special:FilePath (no API call, so no API rate limit);
  3. the licence is read from the Commons API when it answers and must be public domain or CC0. When the API is
     busy the licence written in the story stands and the report says "not re-checked" (fine for a dry run; a real
     upload must refuse it, see upload.py when it exists).
The resolved story (every picture with a local `file`) is written to work/story.json: render.py reads that one.
"""
import hashlib, json, re, subprocess, sys, time, urllib.parse
from pathlib import Path

ROOT = Path(__file__).resolve().parent
UA = "shorts-art-bot/1.0 (automated; a few requests a day)"
FREE = re.compile(r"^(public domain|pd\b|pd-|cc0|cc-zero|no restrictions)", re.I)
WIDTH = 3000


def curl(url, out=None, tries=(0, 20, 60, 150)):
    """GET with patience: Commons answers 429 to bursts. Returns (http code, body bytes or b'')."""
    for wait in tries:
        time.sleep(wait)
        cmd = ["curl", "-s", "-L", "-A", UA, "--max-time", "120", "-w", "\n%{http_code}", url] + (["-o", str(out)] if out else [])
        r = subprocess.run(cmd, capture_output=True)
        code = r.stdout.rsplit(b"\n", 1)[-1].decode().strip()
        if code == "200":
            return 200, b"" if out else r.stdout.rsplit(b"\n", 1)[0]
        if code not in ("429", "503", "000"):
            return int(code or 0), b""
    return 429, b""


def licence(names):
    """{file name: (licence short name, artist, description url)} for all names in ONE API call, or {} when busy."""
    q = urllib.parse.urlencode({"action": "query", "titles": "|".join("File:" + n for n in names), "prop": "imageinfo",
                                "iiprop": "extmetadata|url", "format": "json"})
    code, body = curl("https://commons.wikimedia.org/w/api.php?" + q, tries=(0, 30))
    if code != 200:
        return {}
    try:
        pages = json.loads(body)["query"]["pages"].values()
    except Exception:
        return {}
    out, strip = {}, lambda s: re.sub(r"<[^>]+>", "", s or "").strip()
    for p in pages:
        ii = (p.get("imageinfo") or [{}])[0]
        m = ii.get("extmetadata", {})
        out[p["title"][5:].replace("_", " ")] = (strip(m.get("LicenseShortName", {}).get("value")), strip(m.get("Artist", {}).get("value"))[:120], ii.get("descriptionurl", ""))
    return out


def resolve(story_path, work):
    story = json.loads(Path(story_path).read_text(encoding="utf-8"))
    work = Path(work)
    (work / "img").mkdir(parents=True, exist_ok=True)
    kept = ROOT / "stories" / "img" / story["id"]
    lic = licence([v["commons"] for v in story["images"].values() if v.get("commons")])
    report, bad = [], []
    for key, v in story["images"].items():
        row = {"key": key, "commons": v.get("commons"), "licence_in_story": v.get("license")}
        if v.get("commons"):
            got = lic.get(v["commons"].replace("_", " "))
            row["licence_on_commons"] = got[0] if got else "not re-checked (API busy)"
            row["page"] = got[2] if got else "https://commons.wikimedia.org/wiki/File:" + urllib.parse.quote(v["commons"].replace(" ", "_"))
            if got and not FREE.match(got[0]):
                bad.append(f"{key}: licence on Commons is '{got[0]}', not public domain / CC0")
            dst, local = work / "img" / f"{key}.jpg", kept / f"{key}.jpg"
            if local.exists():
                dst.write_bytes(local.read_bytes())
                row["from"] = "repository copy"
            else:
                url = "https://commons.wikimedia.org/wiki/Special:FilePath/" + urllib.parse.quote(v["commons"]) + f"?width={v.get('width_px', WIDTH)}"
                code, _ = curl(url, dst)
                row["from"] = f"download ({code})"
                if code != 200:
                    bad.append(f"{key}: download failed with {code}")
            if dst.exists():
                row["sha1"] = hashlib.sha1(dst.read_bytes()).hexdigest()
                v["file"] = str(dst.resolve())
        elif v.get("file"):
            row["from"] = "file in the repository"
        report.append(row)
    (work / "sources.json").write_text(json.dumps({"story": story["id"], "pictures": report, "problems": bad}, indent=1, ensure_ascii=False), encoding="utf-8")
    (work / "story.json").write_text(json.dumps(story, indent=1, ensure_ascii=False), encoding="utf-8")
    return story, report, bad


if __name__ == "__main__":
    _, rep, bad = resolve(sys.argv[1], sys.argv[2])
    for r in rep:
        print(f"picture {r['key']:10s} {r.get('from', '-'):22s} licence: {r.get('licence_on_commons') or r.get('licence_in_story')}")
    for b in bad:
        print("PROBLEM", b)
    sys.exit(3 if bad else 0)

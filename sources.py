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


def api(host, **q):
    """One GET to a Wikimedia API, JSON or None."""
    code, body = curl(f"https://{host}/w/api.php?" + urllib.parse.urlencode(dict(q, format="json")), tries=(0, 15, 45))
    try:
        return json.loads(body) if code == 200 else None
    except Exception:
        return None


def free(lic):
    return bool(lic and FREE.match(lic))


def find_portrait(name):
    """The Commons file Wikidata shows for a person (P18), e.g. the painter or the hero of the story. None if none."""
    d = api("www.wikidata.org", action="wbsearchentities", search=name, language="en", type="item", limit=5)
    for hit in (d or {}).get("search", []):
        e = api("www.wikidata.org", action="wbgetentities", ids=hit["id"], props="claims")
        c = ((e or {}).get("entities", {}).get(hit["id"], {}) or {}).get("claims", {})
        human = any(x.get("mainsnak", {}).get("datavalue", {}).get("value", {}).get("id") == "Q5" for x in c.get("P31", []))
        img = next((x["mainsnak"]["datavalue"]["value"] for x in c.get("P18", []) if x.get("mainsnak", {}).get("datavalue")), None)
        if human and img:
            return img, hit["id"]
    return None, None


def find_commons(query, min_width=1100, limit=12):
    """Commons files for a search, free licence first-come: [(file name, width, licence)]."""
    d = api("commons.wikimedia.org", action="query", generator="search", gsrsearch=query + " filetype:bitmap", gsrnamespace=6, gsrlimit=limit,
            prop="imageinfo", iiprop="size|extmetadata")
    out, strip = [], lambda x: re.sub(r"<[^>]+>", "", x or "").strip()
    for p_ in sorted((d or {}).get("query", {}).get("pages", {}).values(), key=lambda x: x.get("index", 0)):
        ii = (p_.get("imageinfo") or [{}])[0]
        lic = strip(ii.get("extmetadata", {}).get("LicenseShortName", {}).get("value"))
        if ii.get("width", 0) >= min_width and free(lic):
            out.append((p_["title"][5:], ii["width"], lic))
    return out


def wikipedia(title):
    """(numbered fact sentences, Commons file of the page's lead picture, Wikidata id) for an English Wikipedia page."""
    d = api("en.wikipedia.org", action="query", titles=title.lstrip("="), redirects=1, prop="extracts|pageimages|pageprops", explaintext=1, exsectionformat="plain",
            piprop="original|name", ppprop="wikibase_item")
    page = next(iter((d or {}).get("query", {}).get("pages", {}).values()), {})
    if not page.get("extract") and not title.startswith("="):          # v1.03: a title that is almost right -> the search's first hit
        hit = api("en.wikipedia.org", action="query", list="search", srsearch=title, srlimit=1)
        found = ((hit or {}).get("query", {}).get("search") or [{}])[0].get("title")
        if found and found != title:
            f_, img, qid, t_ = wikipedia("=" + found)
            return f_, img, qid, t_
    title = title.lstrip("=")
    text = re.sub(r"\n+", " ", page.get("extract", ""))
    sents = [x.strip() for x in re.split(r"(?<=[.!?])\s+(?=[A-Z\"])", text) if 30 <= len(x.strip()) <= 400][:60]
    return sents, page.get("pageimage"), page.get("pageprops", {}).get("wikibase_item"), page.get("title", title)


def face_crop(path):
    """[x0,y0,x1,y1] of a head-and-shoulders crop around the largest face, or None (a portrait card must show a face)."""
    try:
        import cv2
        im = cv2.imread(str(path))
        g = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
        k = 900 / max(g.shape)
        faces = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml").detectMultiScale(cv2.resize(g, None, fx=k, fy=k), 1.1, 6, minSize=(60, 60))
        if not len(faces):
            return None
        x, y, w, h = max(faces, key=lambda f: f[2] * f[3]) / k
        H, W = g.shape
        cx, x0, y0 = x + w / 2, x + w / 2 - 1.5 * w, y - 0.8 * h
        x0, x1, y0, y1 = max(0, x0), min(W, cx + 1.5 * w), max(0, y0), min(H, y + 2.6 * h)
        if (x1 - x0) > 0.92 * W and (y1 - y0) > 0.92 * H:
            return None                                               # the picture is already a head and shoulders
        return [round(x0 / W, 3), round(y0 / H, 3), round(x1 / W, 3), round(y1 / H, 3)]
    except Exception:
        return None


def drop_scene(story, key):
    """Remove an evidence picture that could not be found: its cues (and the cues made inside it) and its names."""
    story["images"].pop(key, None)
    scene = "main"
    for ln in story["lines"]:
        cs, keep = (ln.get("cam") if isinstance(ln.get("cam"), list) else [ln["cam"]] if ln.get("cam") else []), []
        for c in cs:
            was = scene
            scene = c.get("scene", scene)
            if scene == key:
                continue
            if was == key and "scene" not in c and "image" not in c:
                scene = was
                continue
            keep.append(c)
        ln.pop("cam", None)
        if keep:
            ln["cam"] = keep[0] if len(keep) == 1 else keep
        for w_, t_ in list(ln.get("names", {}).items()):
            ln["names"][w_] = [x for x in t_ if not x.startswith(key + ":")]
            if not ln["names"][w_]:
                ln["names"].pop(w_)
    for w_, t_ in list(story.get("names", {}).items()):
        story["names"][w_] = [x for x in t_ if not x.startswith(key + ":")]
        if not story["names"][w_]:
            story["names"].pop(w_)


def resolve(story_path, work):
    story = json.loads(Path(story_path).read_text(encoding="utf-8"))
    work = Path(work)
    (work / "img").mkdir(parents=True, exist_ok=True)
    kept = ROOT / "stories" / "img" / story["id"]
    found = []
    for key, v in list(story["images"].items()):                       # v1.02: the bot looks for the picture itself
        f = v.get("find")
        if v.get("commons") or v.get("file") or not f:
            continue
        if f.get("portrait_of"):
            v["commons"], qid = find_portrait(f["portrait_of"])
            found.append(f"{key}: portrait of {f['portrait_of']} -> {v['commons']} ({qid})")
        if not v.get("commons") and f.get("query"):
            hits = find_commons(f["query"])
            v["commons"] = hits[0][0] if hits else None
            found.append(f"{key}: search '{f['query']}' -> {v['commons']}" + (f" ({hits[0][1]} px, {hits[0][2]})" if hits else ""))
        if not v.get("commons"):
            if key in ("main", "portrait"):
                found.append(f"PROBLEM {key}: nothing found")
            else:                                                       # an evidence picture is optional: drop it and its cues
                drop_scene(story, key)
                found.append(f"{key}: nothing found, the video goes on without it")
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
                if key == "portrait" and not v.get("crop"):             # the portrait card shows a face, not a full-length figure
                    v["crop"] = face_crop(dst)
                    row["crop"] = v["crop"] or "whole picture (no face found)"
        elif v.get("file"):
            row["from"] = "file in the repository"
        report.append(row)
    bad += [f for f in found if f.startswith("PROBLEM")]
    (work / "sources.json").write_text(json.dumps({"story": story["id"], "found": found, "pictures": report, "problems": bad}, indent=1, ensure_ascii=False), encoding="utf-8")
    (work / "story.json").write_text(json.dumps(story, indent=1, ensure_ascii=False), encoding="utf-8")
    return story, report, bad


if __name__ == "__main__":
    if sys.argv[1] == "--selftest":                                    # the finders against the live APIs
        for n in ("Alexandre Cabanel", "Giuseppe Tartini", "Jan Matejko"):
            print("portrait of", n, "->", find_portrait(n))
        for q in ("Tartini Trillo del diavolo", "Codex Gigas devil"):
            print("search", q, "->", find_commons(q)[:3])
        f_, img, qid, title = wikipedia("The Fallen Angel (painting)")
        print("wikipedia:", title, "|", len(f_), "sentences | picture", img, "|", qid, "| licence", licence([img]) if img else None)
        print("first facts:", f_[:3])
        sys.exit(0)
    _, rep, bad = resolve(sys.argv[1], sys.argv[2])
    for r in rep:
        print(f"picture {r['key']:10s} {r.get('from', '-'):22s} licence: {r.get('licence_on_commons') or r.get('licence_in_story')}")
    for b in bad:
        print("PROBLEM", b)
    sys.exit(3 if bad else 0)

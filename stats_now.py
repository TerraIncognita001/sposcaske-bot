#!/usr/bin/env python3
"""stats_now.py — how the channel's videos did: views, who stayed, where they left (v1.09).

    python stats_now.py            refresh data/stats.json from YouTube and print the table (no video, no Gemini)
    python stats_now.py --show     print the table from the file, ask YouTube nothing

Every video of data/slots.json that is public by now gets, in data/stats.json:
  - what it was made of ("f": kind, hook frame, punch word, closer, theme, century, length band, the judge's score
    and six marks, who wrote the script), read from scripts/<story>.json, stories/<story>.json and data/backlog.json;
  - YouTube Data API: views, likes, comments (the upload token is enough);
  - YouTube Analytics (scope yt-analytics.readonly of tools/youtube_auth.py; it lags 2-3 days): engaged views,
    average % viewed, shares, subscribers gained; "stay" = engaged views / views = Studio's "stayed to watch";
  - the retention curve (100 points) and its three steepest drops, each mapped to the caption line that was being
    spoken (data/timeline/<story>.json, saved by bot.py at the upload);
  - "score": how much YouTube pushed it (the warehouse's formula: the stay share weighs most).
learn.py reads this file. Nothing here stops a run: a refused request is printed and skipped.
Copied from the warehouse ww2-bot (shorts.refresh_stats / stay / score, jurgen.retention_curves), one format only.
"""
import json, math, re, sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
STATS, SLOTS = ROOT / "data/stats.json", ROOT / "data/slots.json"
FRAMES = [("what_if", r"^What if\b"), ("detail_most_miss", r"^There(?:'s| is) (?:a|an|one)\b.*\bdetail\b"), ("reason", r"^There(?:'s| is) a reason\b"),
          ("something_about", r"^(?:There(?:'s| is) something|Something about)\b"), ("may_hide", r"\bmay (?:hide|be hiding)\b"),
          ("why", r"^Why\b"), ("about_to", r"^This\b.*\bis about to\b"), ("this_x", r"^This\b"), ("he_she", r"^(?:He|She|They)\b")]


def load():
    return json.loads(STATS.read_text(encoding="utf-8")) if STATS.exists() else {"videos": {}}


def frame_of(hook):
    """The hook's frame as one of a few fixed names (the model's own "hook_frame" is free text and never the same twice)."""
    return next((name for name, rx in FRAMES if re.search(rx, hook.strip(), re.I)), "other")


def band(seconds):
    return None if not seconds else "under 60 s" if seconds < 60 else "60-75 s" if seconds < 75 else "over 75 s"


def features(story_id, seconds=None):
    """What a video was made of: the values learn.py compares. Missing files give missing keys, never an error."""
    f, read = {}, lambda p: json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}
    sc, st = read(ROOT / "scripts" / f"{story_id}.json"), read(ROOT / "stories" / f"{story_id}.json")
    topic = next((t for t in read(ROOT / "data/backlog.json").get("topics", []) if t["id"] == story_id), {})
    hook = (sc.get("sentences") or [{}])[0].get("text") or " ".join(l["say"] for l in st.get("lines", []) if l.get("beat") == "hook")
    year = (sc.get("subject") or {}).get("year") or (st.get("artwork") or {}).get("year")
    f["kind"] = sc.get("kind") or st.get("kind") or topic.get("kind")
    f["hook_frame"] = frame_of(hook) if hook else None
    f["punch"] = sc.get("punch") or st.get("hook_title")
    f["closer"] = sc.get("closer")
    f["theme"] = (topic.get("character") or {}).get("theme")
    f["century"] = f"{int(year) // 100 + 1}th" if isinstance(year, int) or str(year or "").isdigit() else None
    f["length"] = band(seconds)
    f["writer"] = "claude" if str(sc.get("written_by", "")).lower().startswith("claude") else "gemini" if sc else "hand" if st else None
    if topic.get("scores"):
        f["judge"], f["judge_scores"] = topic.get("score"), topic["scores"]
    return {k: v for k, v in f.items() if v is not None}, hook


def stay(m):
    """The share of the views that stayed past the first seconds; None without analytics or under 30 views (noise)."""
    v, e = m.get("a_views") or 0, m.get("a_engagedViews")
    return e / v if e is not None and v >= 30 else None


def score(m):
    """How much YouTube pushed a video (the warehouse's v2.14 formula): mostly the stay share, then engaged views,
    average % viewed, shares and subscribers; an older formula when analytics has not answered yet."""
    st = stay(m)
    if st is not None:
        ev = m.get("a_engagedViews") or 0
        return (15 * st + math.log1p(ev) / 2 + (m.get("a_averageViewPercentage") or 0) / 56
                + 25 * (m.get("a_shares") or 0) / max(ev, 50) + 40 * (m.get("a_subscribersGained") or 0) / max(ev, 50))
    v = m.get("views") or 0
    return math.log1p(v) + 10 * ((m.get("likes") or 0) + 2.5 * (m.get("comments") or 0)) / max(v, 300) if v else None


def drops(curve, seconds, lines, top=3):
    """The steepest falls of the retention curve after the first 3 seconds (the first swipe is "stay"), each with the
    second it happened at and the caption line spoken then."""
    if not curve or not seconds:
        return []
    step = [curve[i - 1][1] - curve[i][1] for i in range(1, len(curve))]
    usual = sorted(step)[len(step) // 2]                               # viewers always trickle away: a drop is 3x the usual step
    out, i = [], 1
    while i < len(curve):
        j, lost = i, 0.0
        while j < len(curve) and step[j - 1] > max(0.008, 3 * usual):  # one fall may run over several points
            lost += step[j - 1]
            j += 1
        t = curve[i - 1][0] * seconds
        if lost > 0 and t >= 3.0:
            ln = next((l for l in lines or [] if l["t0"] - 0.3 <= t < l["t1"] + 0.6), None)
            out.append({"t": round(t, 1), "lost": round(lost * 100, 1), **({"beat": ln["beat"], "say": ln["say"]} if ln else {})})
        i = max(j, i + 1)
    return sorted(sorted(out, key=lambda d: -d["lost"])[:top], key=lambda d: d["t"])


def refresh(stats):
    import upload
    from googleapiclient.discovery import build
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    slots = json.loads(SLOTS.read_text(encoding="utf-8"))["slots"] if SLOTS.exists() else {}
    vids = stats.setdefault("videos", {})
    for key, s in slots.items():
        if not s.get("video") or not s.get("publish_at") or s["publish_at"] > now:
            continue                                                   # private, or waiting for its minute: no numbers yet
        v = vids.setdefault(s["video"], {})
        v.update(story=s.get("story"), slot=key, title=s.get("title"), publish_at=s["publish_at"], seconds=s.get("seconds") or v.get("seconds"))
        v["f"], v["hook"] = features(s.get("story"), v.get("seconds"))
    ids = sorted(vids, key=lambda i: vids[i]["publish_at"])[-80:]
    if not ids:
        print("stats: no public video yet")
        return
    creds = upload.credentials()
    try:
        yt = upload.youtube(creds)
        for i in range(0, len(ids), 50):
            for it in yt.videos().list(part="statistics,contentDetails", id=",".join(ids[i:i + 50])).execute().get("items", []):
                s, v = it.get("statistics", {}), vids[it["id"]]
                v.update(views=int(s.get("viewCount", 0)), likes=int(s.get("likeCount", 0)), comments=int(s.get("commentCount", 0)))
                if not v.get("seconds"):                               # a video uploaded before v1.06 has no length in slots.json
                    m = re.match(r"PT(?:(\d+)M)?(?:(\d+)S)?", it.get("contentDetails", {}).get("duration", ""))
                    v["seconds"] = (int(m.group(1) or 0) * 60 + int(m.group(2) or 0)) if m else None
                    v["f"]["length"] = band(v["seconds"])
        print("stats: views of", len(ids), "videos")
    except Exception as e:
        print("stats: views not read:", str(e)[:160])
    try:
        ya = build("youtubeAnalytics", "v2", credentials=creds, cache_discovery=False)
    except Exception as e:
        print("stats: analytics not opened:", str(e)[:160])
        return
    today, first = date.today().isoformat(), min(vids[i]["publish_at"] for i in ids)[:10]
    try:
        res, why = None, ""
        for metrics in ("views,engagedViews,averageViewPercentage,averageViewDuration,shares,subscribersGained", "views,averageViewPercentage,shares,subscribersGained"):
            try:
                res = ya.reports().query(ids="channel==MINE", startDate=first, endDate=today, metrics=metrics, dimensions="video",
                                         filters="video==" + ",".join(ids), sort="-views", maxResults=200).execute()
                break
            except Exception as e:
                if "insufficient" in str(e).lower() or "forbidden" in str(e).lower() or "403" in str(e):
                    raise
                why = str(e)
        if res is None:
            raise RuntimeError(why[:200])
        heads = [h["name"] for h in res.get("columnHeaders", [])]
        for row in res.get("rows", []):
            r = dict(zip(heads, row))
            vids[r.pop("video")].update({f"a_{k}": v for k, v in r.items()})
        print("stats: analytics of", len(res.get("rows", [])), "videos (YouTube Analytics lags 2-3 days)")
    except Exception as e:
        print("stats: analytics off (the token needs the scope yt-analytics.readonly: run tools/youtube_auth.py again):", str(e)[:160])
        return
    day = (date.today() - timedelta(days=1)).isoformat()
    for i in [i for i in ids if vids[i]["publish_at"][:10] <= day][-12:]:    # the curve of the 12 newest that are a day old
        v = vids[i]
        try:
            r = ya.reports().query(ids="channel==MINE", startDate=v["publish_at"][:10], endDate=today, metrics="audienceWatchRatio",
                                   dimensions="elapsedVideoTimeRatio", filters="video==" + i).execute()
            rows = sorted(r.get("rows") or [])
            if rows:
                v["curve"] = [[round(x[0], 2), round(x[1], 3)] for x in rows]
        except Exception as e:
            print("stats: retention curve not read:", i, str(e)[:120])
    stats["read_at"] = now


def finish(stats):
    """The numbers computed from what was read: stay, score, the drops."""
    for v in stats.get("videos", {}).values():
        st = stay(v)
        if st is not None:
            v["stay"] = round(st, 3)
        sc = score(v)
        if sc is not None:
            v["score"] = round(sc, 2)
        tl = ROOT / "data/timeline" / f"{v.get('story')}.json"
        lines = json.loads(tl.read_text(encoding="utf-8"))["lines"] if tl.exists() else None
        if v.get("curve"):
            v["drops"] = drops(v["curve"], v.get("seconds"), lines)


def show(stats):
    vids = sorted(stats.get("videos", {}).items(), key=lambda kv: kv[1].get("publish_at", ""))
    print(f"{'public (UTC)':16s} {'views':>6s} {'stay':>5s} {'avg%':>5s} {'shares':>6s} {'subs':>4s} {'end%':>4s} {'score':>5s}  hook frame / writer / title")
    for vid, v in vids[-30:]:
        end = round(v["curve"][-1][1] * 100) if v.get("curve") else "-"
        g = lambda k, d="-": v.get(k) if v.get(k) is not None else d
        print(f"{v.get('publish_at', '')[:16]:16s} {g('views'):>6} {g('stay'):>5} {g('a_averageViewPercentage'):>5} {g('a_shares'):>6} {g('a_subscribersGained'):>4} {end:>4} {g('score'):>5}"
              f"  {v.get('f', {}).get('hook_frame', '-')} / {v.get('f', {}).get('writer', '-')} / {str(v.get('title'))[:54]}  https://youtube.com/shorts/{vid}")
        for d in v.get("drops", []):
            print(f"{'':16s} left at {d['t']:>5} s: -{d['lost']} % of viewers" + (f"  [{d['beat']}] {d['say']}" if d.get("say") else ""))


if __name__ == "__main__":
    stats = load()
    if "--show" not in sys.argv:
        try:
            refresh(stats)
        except Exception as e:                                         # the secrets are missing, YouTube is down: the run goes on
            print("stats: not refreshed:", str(e)[:200])
        finish(stats)
        stats["_about"] = "written by stats_now.py (v1.09): one entry per public video; learn.py reads it. Do not edit by hand."
        STATS.write_text(json.dumps(stats, indent=1, ensure_ascii=False), encoding="utf-8")
    show(stats)

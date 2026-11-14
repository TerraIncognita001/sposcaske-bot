#!/usr/bin/env python3
"""learn.py — the bot learns from its own videos (v1.09).

    python learn.py            data/stats.json -> data/learn.json (what the bot uses) + data/lessons.md (to read)

The scheme of docs/BUILD_PROMPT.md (section 13, taken from the warehouse ww2-bot):
  - a video counts when it has been public for 3 days (younger numbers still move) and has a score (stats_now.py);
  - LEARNING SWITCHES ON AT 8 SUCH VIDEOS. Before that learn.json says "on": false and the bot works exactly as
    without this file;
  - every value of every parameter (hook frame, closer, kind, theme, century, length band, writer) gets a
    multiplier 0.5-2.0 = the mean score of its videos / the mean score of all. A value with fewer than 3 videos
    stays at 1.0, so it keeps being tried;
  - THE JUDGE'S SCALE IS RE-CALIBRATED: each of the six marks (G gaze, D darkness and one figure, F the flip,
    T threat, Y "you", S story) gets a weight 0.5-1.5 = 1 + its correlation with the score of our own videos; a
    topic's calibrated score is the weighted sum brought back to 1-10.
Used by writer.py: next_topic() orders the queue by priority() (the calibrated score x the multipliers of the
topic's theme and kind), and the writer's prompt gets notes() (the frames and closers that held our viewers, and
the ones that lost them). The threshold "7 and more" stays on the judge's own total.
"""
import json, sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
STATS, LEARN, LESSONS = ROOT / "data/stats.json", ROOT / "data/learn.json", ROOT / "data/lessons.md"
PARAMS = ("hook_frame", "closer", "kind", "theme", "century", "length", "writer")
KEYS, LIMIT = ("G", "D", "F", "T", "Y", "S"), {"G": 2, "D": 2, "F": 2, "T": 2, "Y": 1, "S": 1}
MIN_VIDEOS, MIN_AGE_DAYS, MIN_PER_VALUE = 8, 3, 3
mean = lambda xs: sum(xs) / len(xs)


def corr(xs, ys):
    """Pearson's r, or None when one side does not vary."""
    mx, my = mean(xs), mean(ys)
    sx, sy = sum((x - mx) ** 2 for x in xs) ** 0.5, sum((y - my) ** 2 for y in ys) ** 0.5
    return sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / (sx * sy) if sx > 1e-9 and sy > 1e-9 else None


def build(stats, now=None):
    now = now or datetime.now(timezone.utc)
    old = (now - timedelta(days=MIN_AGE_DAYS)).strftime("%Y-%m-%dT%H:%M:%SZ")
    vids = [v for v in stats.get("videos", {}).values() if v.get("score") is not None and v.get("publish_at", "9") <= old]
    out = {"_about": "written by learn.py (v1.09) from data/stats.json. on = false: the bot ignores this file.", "updated": now.strftime("%Y-%m-%dT%H:%MZ"),
           "on": len(vids) >= MIN_VIDEOS, "videos_counted": len(vids), "rule": f"on at {MIN_VIDEOS} videos public for {MIN_AGE_DAYS} days; a value needs {MIN_PER_VALUE} videos",
           "mult": {}, "judge_weights": {k: 1.0 for k in KEYS}, "judge_fit": None}
    if not vids:
        return out
    base = mean([v["score"] for v in vids])
    out["mean_score"] = round(base, 2)
    for p in PARAMS:
        groups = {}
        for v in vids:
            if v.get("f", {}).get(p) is not None:
                groups.setdefault(str(v["f"][p]), []).append(v["score"])
        out["mult"][p] = {val: {"n": len(s), "mean": round(mean(s), 2), "m": round(max(0.5, min(2.0, mean(s) / base)), 2) if len(s) >= MIN_PER_VALUE and base > 0 else 1.0}
                          for val, s in sorted(groups.items(), key=lambda kv: -mean(kv[1]))}
    judged = [v for v in vids if v.get("f", {}).get("judge_scores")]
    if len(judged) >= MIN_VIDEOS:                                      # does the judge's mark say anything about OUR viewers?
        ys = [v["score"] for v in judged]
        for k in KEYS:
            r = corr([v["f"]["judge_scores"].get(k, 0) for v in judged], ys)
            out["judge_weights"][k] = round(max(0.5, min(1.5, 1 + r)), 2) if r is not None else 1.0
        r = corr([v["f"].get("judge", 0) for v in judged], ys)
        out["judge_fit"] = round(r, 2) if r is not None else None
    return out


def load():
    try:
        return json.loads(LEARN.read_text(encoding="utf-8"))
    except Exception:
        return {"on": False}


def calibrated(topic, L=None):
    """The judge's total on OUR scale: the six marks weighted by what our own videos showed, back to 1-10."""
    L = L or load()
    sc, w = topic.get("scores"), L.get("judge_weights") or {}
    if not L.get("on") or not sc or not topic.get("score"):
        return topic.get("score") or 0
    return round(10 * sum(sc.get(k, 0) * w.get(k, 1.0) for k in KEYS) / sum(LIMIT[k] * w.get(k, 1.0) for k in KEYS), 2)


def priority(topic, L=None):
    """What the queue is ordered by. Learning off = the judge's total, as before v1.09."""
    L = L or load()
    if not L.get("on"):
        return topic.get("score") or 0
    m = lambda p, val: ((L.get("mult", {}).get(p) or {}).get(str(val)) or {}).get("m", 1.0)
    return round(calibrated(topic, L) * m("theme", (topic.get("character") or {}).get("theme")) * m("kind", topic.get("kind")), 2)


def notes(L=None):
    """Lines for the writer's prompt: what held our own viewers and what lost them. Empty while learning is off."""
    L = L or load()
    if not L.get("on"):
        return ""
    names = {"what_if": '"What if ___?"', "detail_most_miss": '"There\'s a ___ detail in this painting most people ___."', "reason": '"There\'s a reason ___."',
             "something_about": '"Something about ___ feels completely wrong." / "There\'s something ___ about ___."', "may_hide": '"This painting may hide ___."',
             "why": '"Why is / does / did ___?"', "about_to": '"This ___ is about to ___, and ___."'}
    out = []
    for p, label in (("hook_frame", "hook frame"), ("closer", "closing question type")):
        vals = (L.get("mult", {}).get(p) or {})
        good = [names.get(v, v) for v, d in vals.items() if d["m"] >= 1.15]
        bad = [names.get(v, v) for v, d in vals.items() if d["m"] <= 0.85]
        if good:
            out.append(f"- PREFER the {label}: " + "; ".join(good) + " (it held our viewers best)")
        if bad:
            out.append(f"- AVOID the {label}: " + "; ".join(bad) + " (our viewers left)")
    return "\n\nLEARNED FROM OUR OWN VIDEOS (this outranks the order of the frames above)\n" + "\n".join(out) if out else ""


def lessons(stats, L):
    """data/lessons.md: the same numbers for a reader (Andrii, the night writer)."""
    vids = sorted(stats.get("videos", {}).items(), key=lambda kv: kv[1].get("publish_at", ""))
    md = ["# Lessons from our own videos", "", f"Written by `learn.py` on {L['updated']} from `data/stats.json`. Do not edit by hand.", "",
          f"Learning is **{'ON' if L['on'] else 'OFF'}**: {L['videos_counted']} videos counted ({L['rule']}).", "",
          "## Videos", "", "| public (UTC) | views | stayed | avg % viewed | score | hook | where viewers left |", "|---|---|---|---|---|---|---|"]
    for vid, v in vids[-40:]:
        left = "; ".join(f"{d['t']} s −{d['lost']} %" + (f" [{d['beat']}: {d['say']}]" if d.get("say") else "") for d in v.get("drops", [])) or "—"
        g = lambda k: v.get(k) if v.get(k) is not None else "—"
        md.append(f"| {v.get('publish_at', '')[:16].replace('T', ' ')} | {g('views')} | {g('stay')} | {g('a_averageViewPercentage')} | {g('score')} | {str(v.get('hook') or v.get('title'))[:90]} | {left} |")
    md += ["", "## What worked (mean score of the videos with this value; multiplier 1.0 = too few videos to say)", ""]
    for p, vals in L.get("mult", {}).items():
        if vals:
            md += [f"**{p}**: " + "; ".join(f"{val} ×{d['m']} (n={d['n']}, mean {d['mean']})" for val, d in vals.items()), ""]
    md += ["## The judge's scale on our numbers", "", "Weights of the six marks (1.0 = as the judge gives them): " + ", ".join(f"{k} {w}" for k, w in L["judge_weights"].items()) + ".",
           f"Correlation of the judge's total with our score: {L['judge_fit'] if L['judge_fit'] is not None else 'not enough videos yet'}.", ""]
    return "\n".join(md)


if __name__ == "__main__":
    stats = json.loads(STATS.read_text(encoding="utf-8")) if STATS.exists() else {"videos": {}}
    L = build(stats)
    LEARN.write_text(json.dumps(L, indent=1, ensure_ascii=False), encoding="utf-8")
    LESSONS.write_text(lessons(stats, L), encoding="utf-8")
    print(f"learn: {'ON' if L['on'] else 'off'}, {L['videos_counted']} videos counted ({L['rule']})")
    if L["on"]:
        for p, vals in L["mult"].items():
            print(f"  {p}: " + ", ".join(f"{v} x{d['m']} (n={d['n']})" for v, d in vals.items()))
        print("  judge weights:", L["judge_weights"], "| fit", L["judge_fit"])

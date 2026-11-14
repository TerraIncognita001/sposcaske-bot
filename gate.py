#!/usr/bin/env python3
"""gate.py — the schedule (v1.04). The source of truth for WHEN videos go public.

Andrii, Nov 14 2026: 'випускатимемо відео 2 рази в день. 1500 за лондоном та 0200 за лондоном'.
Never change SLOTS without his yes.

    python gate.py            -> prints the slot this run should fill, as KEY=VALUE lines for the workflow

A slot = one video. Its key is E<date>#N (the London date of the publish time), as in the warehouse ww2-bot.
v1.08 (Andrii, Nov 14: 'хай тепер за день до пустого слоту бот сам пише та випускає відео, загружає як приватне та
ставить скеджл на випуск на потрібну годину'): a run fills the earliest slot that is still empty and whose publish
time is between 30 minutes and 30 hours away. With the four daily fires (12:05, 13:05, 20:05, 21:05 UTC) every video
is therefore made 27 to 30 hours AHEAD and waits on the channel, private, with its publish minute; YouTube itself
makes it public. A slot that failed a day ahead is tried again by the next fires, four tries in all.
data/slots.json remembers which slot got which video.
"""
import json, sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent
LONDON = ZoneInfo("Europe/London")
SLOTS = [(1, 15, 0), (2, 2, 0)]            # (number, London hour, minute): 15:00 and 02:00
STATE, CONFIG = ROOT / "data/slots.json", ROOT / "data/config.json"
LEAD_MIN, LEAD_MAX, TRIES = timedelta(minutes=30), timedelta(hours=30), 4       # v1.08: a day ahead (was 14 hours, 2 tries)


def upcoming(now=None, days=2):
    """[(key, publish time UTC)] of the slots ahead, earliest first."""
    now = now or datetime.now(timezone.utc)
    out, today = [], now.astimezone(LONDON).date()
    for d in range(-1, days + 1):
        day = today + timedelta(days=d)
        for n, h, m in SLOTS:
            at = datetime(day.year, day.month, day.day, h, m, tzinfo=LONDON).astimezone(timezone.utc)
            out.append((f"E{day.isoformat()}#{n}", at))
    return sorted((x for x in out if x[1] > now), key=lambda x: x[1])


def load():
    return json.loads(STATE.read_text(encoding="utf-8")) if STATE.exists() else {"slots": {}}


def pick(now=None):
    """The slot to fill now: (key, publish time) or (None, reason)."""
    now = now or datetime.now(timezone.utc)
    cfg = json.loads(CONFIG.read_text(encoding="utf-8"))
    if not cfg.get("live"):
        return None, "the schedule is switched off (data/config.json live = false)"
    st = load()["slots"]
    for key, at in upcoming(now):
        s = st.get(key, {})
        if s.get("video") or s.get("tries", 0) >= TRIES:
            continue
        if LEAD_MIN <= at - now <= LEAD_MAX:
            return key, at
    return None, "no empty slot between 30 minutes and 30 hours from now"


def record(key, **fields):
    st = load()
    st["slots"].setdefault(key, {}).update(fields)
    STATE.write_text(json.dumps(st, indent=1, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    key, at = pick()
    if key is None:
        print(f"GO=0\nWHY={at}")
        sys.exit(0)
    record(key, tries=load()["slots"].get(key, {}).get("tries", 0) + 1)
    print(f"GO=1\nSLOT={key}\nPUBLISH_AT={at.strftime('%Y-%m-%dT%H:%M:%SZ')}")

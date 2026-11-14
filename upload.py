#!/usr/bin/env python3
"""upload.py — the bot's hands on YouTube (v1.04).

    python upload.py --whoami        which channel do the secrets open? (reads only, changes nothing)
    python upload.py --pending       post the question comments of videos that went public
    upload(mp4, meta, publish_at)    called by bot.py: always private, public at the slot time when one is given

Secrets (GitHub Actions): YT_CLIENT_ID, YT_CLIENT_SECRET, YT_REFRESH_TOKEN, made once with tools/youtube_auth.py.
Copied from the warehouse ww2-bot (shorts.py credentials / youtube).
"""
import os, sys


def credentials():
    from google.oauth2.credentials import Credentials
    return Credentials(None, refresh_token=os.environ["YT_REFRESH_TOKEN"], token_uri="https://oauth2.googleapis.com/token",
                       client_id=os.environ["YT_CLIENT_ID"], client_secret=os.environ["YT_CLIENT_SECRET"])


def youtube(creds=None):
    from googleapiclient.discovery import build
    return build("youtube", "v3", credentials=creds or credentials(), cache_discovery=False)


def whoami():
    """The channel behind the token: its name, handle, numbers and whether long uploads / thumbnails are allowed."""
    missing = [k for k in ("YT_CLIENT_ID", "YT_CLIENT_SECRET", "YT_REFRESH_TOKEN") if not os.environ.get(k)]
    if missing:
        print("missing secrets:", ", ".join(missing))
        return 1
    r = youtube().channels().list(part="snippet,statistics,status", mine=True).execute()
    if not r.get("items"):
        print("the token is valid but opens no channel")
        return 1
    for c in r["items"]:
        s, st = c["snippet"], c["statistics"]
        print(f"channel: {s['title']} ({s.get('customUrl', 'no handle yet')})  id {c['id']}")
        print(f"  created {s['publishedAt'][:10]}, videos {st.get('videoCount')}, subscribers {st.get('subscriberCount')}, views {st.get('viewCount')}")
        print(f"  long uploads (= phone verified): {c['status'].get('longUploadsStatus')}, made for kids set: {c['status'].get('madeForKids', 'not set')}")
    return 0


def upload(mp4, meta, publish_at=None):
    """One resumable upload (network hiccups are retried inside the same session, never a second video). Always
    PRIVATE; with publish_at (UTC, ...Z) YouTube itself makes it public on that minute. Returns the video id."""
    from googleapiclient.http import MediaFileUpload
    tags = " ".join("#" + t.replace(" ", "") for t in (["shorts"] + meta.get("tags", []))[:4])
    body = {"snippet": {"title": meta["title"][:100], "description": (meta["description"] + "\n\n" + tags)[:4900], "tags": meta.get("tags", [])[:12],
                        "categoryId": meta.get("categoryId", "27"), "defaultLanguage": "en", "defaultAudioLanguage": "en"},
            "status": {"privacyStatus": "private", "selfDeclaredMadeForKids": False, "embeddable": True}}
    if publish_at:
        body["status"]["publishAt"] = publish_at
    vid = youtube().videos().insert(part="snippet,status", body=body, media_body=MediaFileUpload(str(mp4), chunksize=-1, resumable=True)).execute(num_retries=3)["id"]
    print(f"uploaded: https://youtube.com/shorts/{vid}  (private" + (f", public at {publish_at} UTC)" if publish_at else ", no publish time)"))
    return vid


def schedule(vid, publish_at, slot=None, story=None, question=None):
    """v1.07: give a video that is already on the channel, private, its publish minute (UTC, ...Z), and book the slot."""
    import gate
    yt = youtube()
    cur = yt.videos().list(part="status,snippet", id=vid).execute()["items"][0]
    if cur["status"]["privacyStatus"] != "private":
        print(f"{vid} is {cur['status']['privacyStatus']}, not private: nothing changed")
        return 1
    yt.videos().update(part="status", body={"id": vid, "status": {"privacyStatus": "private", "publishAt": publish_at,
                       "selfDeclaredMadeForKids": False, "embeddable": True}}).execute()
    print(f"scheduled: https://youtube.com/shorts/{vid} '{cur['snippet']['title']}' goes public at {publish_at} UTC")
    if slot:
        old = next((k for k, v in gate.load()["slots"].items() if v.get("video") == vid and k != slot), None)
        st = gate.load()
        if old:
            st["slots"].pop(old)
            gate.STATE.write_text(__import__("json").dumps(st, indent=1, ensure_ascii=False), encoding="utf-8")
        gate.record(slot, video=vid, story=story, title=cur["snippet"]["title"], publish_at=publish_at, **({"comment_pending": question + " 👇"} if question else {}))
    return 0


def comment(vid, text):
    youtube().commentThreads().insert(part="snippet", body={"snippet": {"videoId": vid, "topLevelComment": {"snippet": {"textOriginal": text}}}}).execute()


def post_pending():
    """The question comment of every video that is public by now and still waits for it (a private video takes none)."""
    import json
    from datetime import datetime, timezone
    import gate
    st, now, n = gate.load(), datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), 0
    for key, s in st["slots"].items():
        if s.get("comment_pending") and s.get("video") and s.get("publish_at", "9") <= now:
            try:
                comment(s["video"], s["comment_pending"])
                s.pop("comment_pending")
                n += 1
                print(f"comment posted under {s['video']} ({key})")
            except Exception as e:
                print(f"comment under {s['video']} failed:", str(e)[:160])
    gate.STATE.write_text(json.dumps(st, indent=1, ensure_ascii=False), encoding="utf-8")
    return n


if __name__ == "__main__":
    if "--whoami" in sys.argv:
        sys.exit(whoami())
    if "--schedule" in sys.argv:                                        # --schedule <video id> <publish_at> [slot] [story] [question]
        a = sys.argv[sys.argv.index("--schedule") + 1:]
        sys.exit(schedule(*a[:5]))
    if "--pending" in sys.argv:
        post_pending()
        sys.exit(0)
    sys.exit(1)

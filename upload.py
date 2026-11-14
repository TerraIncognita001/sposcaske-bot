#!/usr/bin/env python3
"""upload.py — the bot's hands on YouTube (v1.04: the connection check; the upload itself comes with the schedule).

    python upload.py --whoami        which channel do the secrets open? (reads only, changes nothing)

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


if __name__ == "__main__":
    sys.exit(whoami() if "--whoami" in sys.argv else 1)

"""Run ONCE on your own computer to connect the bot to the YouTube channel (copied from the warehouse ww2-bot).

    pip install google-auth-oauthlib
    python tools/youtube_auth.py          (client_secret.json of the Google Cloud project must lie next to it)

A browser opens: sign in and pick THE NEW CHANNEL. The three printed values go into the repository's secrets
(GitHub -> Settings -> Secrets and variables -> Actions): YT_CLIENT_ID, YT_CLIENT_SECRET, YT_REFRESH_TOKEN.
Never paste them into a chat or commit them.
"""
from google_auth_oauthlib.flow import InstalledAppFlow

flow = InstalledAppFlow.from_client_secrets_file(
    "client_secret.json",
    [
        "https://www.googleapis.com/auth/youtube.upload",
        "https://www.googleapis.com/auth/youtube.force-ssl",       # comments, playlists, reading video stats
        "https://www.googleapis.com/auth/yt-analytics.readonly",   # retention, engaged views, shares (optional)
    ],
)
c = flow.run_local_server(port=0, access_type="offline", prompt="consent")
print("YT_CLIENT_ID=", c.client_id)
print("YT_CLIENT_SECRET=", c.client_secret)
print("YT_REFRESH_TOKEN=", c.refresh_token)

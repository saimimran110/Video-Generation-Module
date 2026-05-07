"""
YouTube Shorts Uploader -- YouTube Data API v3
================================================
Uploads a video to YouTube as a Short using the official API.
First run opens browser for OAuth consent, then saves token for future use.

Usage:
    python youtube_upload.py "video.mp4" "Title" "Description"

    # Called from pipeline
    from youtube_upload import upload_to_youtube
    upload_to_youtube("video.mp4", "Title", "Description")
"""

import os
import sys
import json
import http.client
import httplib2

from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

# ====================================================
#  CONFIG
# ====================================================
CREDENTIALS_FILE = "credentials.json"
TOKEN_FILE = "youtube_token.json"
SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
# ====================================================


def get_authenticated_service():
    """Authenticate and return YouTube API service."""
    creds = None

    # Load saved token if exists
    if os.path.exists(TOKEN_FILE):
        print("[>] Loading saved YouTube token...")
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

    # If no valid creds, do OAuth flow
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("[>] Refreshing expired token...")
            creds.refresh(Request())
        else:
            if not os.path.exists(CREDENTIALS_FILE):
                print(f"[!] {CREDENTIALS_FILE} not found!")
                print("    Download it from Google Cloud Console.")
                return None

            print("[>] Opening browser for YouTube authorization...")
            print("    (Sign in and allow access, then come back)")
            flow = InstalledAppFlow.from_client_secrets_file(
                CREDENTIALS_FILE, SCOPES
            )
            creds = flow.run_local_server(port=0)
            print("[OK] Authorization successful!")

        # Save token for next time
        with open(TOKEN_FILE, "w") as f:
            f.write(creds.to_json())
        print(f"[OK] Token saved to {TOKEN_FILE}")

    youtube = build("youtube", "v3", credentials=creds)
    print("[OK] YouTube API service ready!")
    return youtube


def upload_to_youtube(video_path, title, description="", tags=None, category_id="25"):
    """Upload video to YouTube as a Short.

    Args:
        video_path: Path to video file
        title: Video title
        description: Video description
        tags: List of tags (optional)
        category_id: YouTube category (25 = News & Politics)

    Returns:
        Video URL on success, None on failure
    """
    abs_path = os.path.abspath(video_path)

    if not os.path.exists(abs_path):
        print(f"[!] Video file not found: {abs_path}")
        return None

    file_size_mb = os.path.getsize(abs_path) / (1024 * 1024)
    print(f"[>] Video: {os.path.basename(abs_path)} ({file_size_mb:.1f} MB)")

    # Authenticate
    youtube = get_authenticated_service()
    if not youtube:
        return None

    # Default tags
    if tags is None:
        tags = ["TachyonNews", "BreakingNews", "Shorts", "News"]

    # Ensure #Shorts is in title or description for YouTube to recognize it
    if "#Shorts" not in title and "#Shorts" not in description:
        description = description.rstrip() + "\n\n#Shorts"

    # Video metadata
    body = {
        "snippet": {
            "title": title,
            "description": description,
            "tags": tags,
            "categoryId": category_id,
        },
        "status": {
            "privacyStatus": "public",
            "selfDeclaredMadeForKids": False,
        },
    }

    # Upload
    print("[>] Uploading to YouTube...")
    media = MediaFileUpload(
        abs_path,
        mimetype="video/mp4",
        resumable=True,
        chunksize=1024 * 1024  # 1MB chunks
    )

    try:
        request = youtube.videos().insert(
            part="snippet,status",
            body=body,
            media_body=media,
        )

        response = None
        while response is None:
            status, response = request.next_chunk()
            if status:
                progress = int(status.progress() * 100)
                print(f"\r[*] Upload progress: {progress}%", end="", flush=True)

        video_id = response["id"]
        video_url = f"https://youtube.com/shorts/{video_id}"

        print(f"\n[OK] Upload complete!")
        print(f"[OK] Video ID: {video_id}")
        print(f"[OK] URL: {video_url}")

        return video_url

    except HttpError as e:
        error_details = json.loads(e.content.decode("utf-8"))
        error_msg = error_details.get("error", {}).get("message", str(e))
        print(f"\n[!] YouTube API Error: {error_msg}")

        # Common errors
        if "quotaExceeded" in str(e):
            print("    Daily upload quota exceeded. Try again tomorrow.")
        elif "forbidden" in str(e).lower():
            print("    Check that YouTube Data API v3 is enabled in Google Cloud Console.")

        return None
    except Exception as e:
        print(f"\n[!] Upload failed: {e}")
        return None


def main():
    if len(sys.argv) < 2:
        print('Usage: python youtube_upload.py "video.mp4" "Title" "Description"')
        return

    video_path = sys.argv[1]
    title = sys.argv[2] if len(sys.argv) > 2 else "Tachyon News Update"
    description = sys.argv[3] if len(sys.argv) > 3 else ""

    result = upload_to_youtube(video_path, title, description)
    if result:
        print(f"\n[OK] Video live at: {result}")
    else:
        print("\n[!] Upload failed!")


if __name__ == "__main__":
    main()

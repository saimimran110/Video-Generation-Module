"""
Tachyon News — Full Pipeline
=============================
1. Ask user for raw news
2. Expand via Groq (testgrok.py) → get anchor-style script + language
3. Send expanded script to HeyGen automation → generate & download video
4. Run video editor (script.py) with correct language → final Tachyon News video

Usage:
    python run_flow.py
"""

import asyncio
import os
import subprocess
import sys


async def run_pipeline():
    print("=" * 56)
    print("   TACHYON NEWS — FULL AUTOMATED PIPELINE")
    print("=" * 56)

    # ─── STEP 1: Ask for raw news ─────────────────────────────
    print("\n📰  Enter the raw news (short headline / khabar).")
    print("    (Type or paste, then press Enter)\n")
    raw_news = input("News > ").strip()

    if not raw_news:
        print("[!] No news entered. Exiting.")
        return

    print(f"\n[✓] Raw news received ({len(raw_news)} chars)")

    # ─── STEP 2: Expand via Groq ──────────────────────────────
    print("\n" + "=" * 56)
    print("   STEP 2: GROQ NEWS EXPANSION")
    print("=" * 56)

    from testgrok import process_news

    print("[>] Detecting language & expanding news via Groq...")
    result = process_news(raw_news)

    language = result["language"]
    expanded_script = result["script"]

    lang_label = "URDU (Roman) 🇵🇰" if language == "urdu" else "ENGLISH 🇬🇧"
    print(f"\n[✓] Language detected: {lang_label}")
    print(f"[✓] Expanded script ({len(expanded_script)} chars):")
    print("-" * 40)
    print(expanded_script)
    print("-" * 40)

    # ─── STEP 3: Run HeyGen automation ────────────────────────
    print("\n" + "=" * 56)
    print("   STEP 3: HEYGEN VIDEO GENERATION")
    print("=" * 56)

    from heygen_simple import run_heygen

    print("[>] Starting HeyGen automation with expanded script...")
    downloaded_video = await run_heygen(expanded_script)

    if not downloaded_video or not os.path.exists(downloaded_video):
        print("\n[✗] Video download failed or file not found!")
        print("    Pipeline cannot continue.")
        return

    print(f"\n[✓] Video downloaded successfully: {downloaded_video}")
    file_size_mb = os.path.getsize(downloaded_video) / (1024 * 1024)
    print(f"    Size: {file_size_mb:.1f} MB")

    # ─── STEP 4: Run video editor (script.py) ─────────────────
    print("\n" + "=" * 56)
    print("   STEP 4: VIDEO EDITING (Tachyon News Overlay)")
    print("=" * 56)

    script_dir = os.path.dirname(downloaded_video)  # heygen_downloads
    script_path = os.path.join(script_dir, "script.py")
    video_filename = os.path.basename(downloaded_video)

    if not os.path.exists(script_path):
        print(f"[✗] Editor script not found at: {script_path}")
        return

    # Build command based on language
    cmd = [sys.executable, "script.py", video_filename]
    if language == "urdu":
        cmd.append("urdu")
        print(f'[>] Running: python script.py "{video_filename}" urdu')
    else:
        print(f'[>] Running: python script.py "{video_filename}"')

    print(f"    Working directory: {os.path.abspath(script_dir)}")

    edit_result = subprocess.run(
        cmd,
        cwd=os.path.abspath(script_dir),
        capture_output=False,  # Show output in real-time
    )

    if edit_result.returncode != 0:
        print(f"\n[✗] Video editing failed with exit code {edit_result.returncode}")
        return

    # Check for the output file
    output_video = os.path.join(script_dir, "tachyon_final.mp4")
    if not os.path.exists(output_video):
        print(f"\n[!] Expected output file not found: {output_video}")
        print("    Check the editor output above for errors.")
        return

    final_size = os.path.getsize(output_video) / (1024 * 1024)
    print(f"\n[✓] Edited video ready: {output_video} ({final_size:.1f} MB)")

    # ─── STEP 5: Upload to YouTube ────────────────────────────
    print("\n" + "=" * 56)
    print("   STEP 5: YOUTUBE SHORTS UPLOAD")
    print("=" * 56)

    from youtube_upload import upload_to_youtube

    # Get YouTube metadata from Groq's result
    yt_title = result.get("yt_title", f"Breaking News | Tachyon News")
    yt_description = result.get("yt_description", f"{expanded_script}\n\n#TachyonNews #Shorts")

    print(f"[>] Title: {yt_title}")
    print(f"[>] Description: {yt_description[:60]}...")
    print(f"[>] Uploading to YouTube as Short...")

    yt_result = upload_to_youtube(output_video, yt_title, yt_description)

    # ─── FINAL SUMMARY ───────────────────────────────────────
    print("\n" + "=" * 56)
    print("   ✅ FULL PIPELINE COMPLETE!")
    print("=" * 56)
    print(f"   📝 Raw news:     {raw_news[:50]}...")
    print(f"   🌐 Language:     {lang_label}")
    print(f"   📥 Raw video:    {downloaded_video}")
    print(f"   🎬 Edited video: {output_video}")
    print(f"   📦 Final size:   {final_size:.1f} MB")
    if yt_result:
        if isinstance(yt_result, str):
            print(f"   📺 YouTube URL:  {yt_result}")
        else:
            print(f"   📺 YouTube:      ✅ Uploaded!")
    else:
        print(f"   📺 YouTube:      ❌ Upload failed")
    print("=" * 56)


if __name__ == "__main__":
    asyncio.run(run_pipeline())

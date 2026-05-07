"""
Tachyon News Video Editor v5
==============================
- Auto subtitles (bottom, UPPERCASE, Impact font)
- TACHYON NEWS lower third band
- LIVE label + scrolling ticker
- Cinematic color grade + vignette
- Roman Urdu + English support

Requirements:
    pip install faster-whisper

Usage:
    python script.py "Avatar Video.mp4"
    python script.py "Urdu Video.mp4" urdu
"""

import sys, os, subprocess, json

# ══════════════════════════════════════════
#  CONFIG — change karo yahan
# ══════════════════════════════════════════
INPUT_VIDEO   = sys.argv[1] if len(sys.argv) > 1 else "Avatar Video.mp4"
LANGUAGE_HINT = sys.argv[2] if len(sys.argv) > 2 else None
OUTPUT_VIDEO  = "tachyon_final.mp4"
CHANNEL_NAME  = "TACHYON NEWS"
WORDS_PER_SUB = 3          # kitne words ek subtitle mein
# ══════════════════════════════════════════


def find_font():
    candidates = [
        "C:/Windows/Fonts/impact.ttf",
        "C:/Windows/Fonts/arialbd.ttf",
        "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/calibrib.ttf",
    ]
    for f in candidates:
        if os.path.exists(f):
            print(f"Font found: {f}")
            return f
    print("No font found — using default")
    return None


def get_video_size(video_path):
    """Video ka width/height pata karo"""
    r = subprocess.run(
        ["ffprobe", "-v", "quiet", "-print_format", "json",
         "-show_streams", video_path],
        capture_output=True, text=True, encoding="utf-8", errors="ignore"
    )
    try:
        data = json.loads(r.stdout)
        for s in data.get("streams", []):
            if s.get("codec_type") == "video":
                return int(s["width"]), int(s["height"])
    except Exception:
        pass
    return 720, 1280   # default fallback


def transcribe(video_path, lang=None):
    print("Transcribing...")
    try:
        from faster_whisper import WhisperModel
        model = WhisperModel("base", device="cpu", compute_type="int8")
        kwargs = {"word_timestamps": True}
        if lang == "urdu":
            kwargs["language"] = "ur"
        segments, info = model.transcribe(video_path, **kwargs)
        words = []
        for seg in segments:
            for w in seg.words:
                words.append({
                    "word":  w.word.strip(),
                    "start": round(w.start, 3),
                    "end":   round(w.end,   3),
                })
        print(f"Language: {info.language} | Words: {len(words)}")
        return words
    except Exception as e:
        print(f"Transcription failed: {e}")
        return []


def make_srt(words, n, path):
    def fmt(s):
        h = int(s // 3600)
        m = int((s % 3600) // 60)
        sec = int(s % 60)
        ms  = int((s % 1) * 1000)
        return f"{h:02d}:{m:02d}:{sec:02d},{ms:03d}"

    content = ""
    idx = 1
    for i in range(0, len(words), n):
        chunk = words[i:i+n]
        text  = " ".join(w["word"] for w in chunk).upper()
        content += f"{idx}\n{fmt(chunk[0]['start'])} --> {fmt(chunk[-1]['end'])}\n{text}\n\n"
        idx += 1

    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"SRT saved: {path} ({idx-1} subtitles)")


def ffmpeg_run(cmd):
    r = subprocess.run(
        cmd, capture_output=True,
        text=True, encoding="utf-8", errors="ignore"
    )
    return r.returncode, r.stderr or ""


def build_video(input_video, srt_path, output_video, font, width, height):
    """
    Full render:
      - color grade
      - vignette
      - subtitles (above lower third)
      - lower third dark band
      - cyan accent line
      - channel name + LIVE (hardcoded pixel Y)
      - scrolling ticker
    """
    print(f"Rendering {width}x{height}...")

    # ── Font escape for ffmpeg Windows ──────────────────────
    # drawtext fontfile needs C\\:/path format
    if font:
        fp = font.replace("\\", "/")          # forward slashes
        fp = fp.replace(":", "\\\\:")          # escape colon → C\\:/Windows/...
    else:
        fp = None

    # ── SRT path escape ─────────────────────────────────────
    srt_abs = os.path.abspath(srt_path).replace("\\", "/").replace(":", "\\\\:")

    # ── Layout: subtitles bottom, TACHYON top-left, LIVE top-right ──
    # TOP BAR (channel + live)
    top_bar_h = 60                          # top bar height
    top_bar_y = 0                           # top of video
    ch_y      = 15                          # TACHYON NEWS y (top-left)
    live_y    = 18                          # LIVE y (top-right)
    live_x    = width - 100                 # LIVE x (top-right)

    # SUBTITLES at very bottom (small MarginV = close to bottom)
    margin_v  = 20                          # 20px from bottom edge

    # Ticker row (just above bottom edge)
    ticker_y  = height - 18

    # ── Subtitle style ───────────────────────────────────────
    sub_style = (
        f"FontName=Impact"
        f",FontSize=16"
        f",PrimaryColour=&H00FFFFFF"
        f",OutlineColour=&H00000000"
        f",BackColour=&HAA000000"
        f",Outline=3"
        f",Shadow=2"
        f",Alignment=2"
        f",MarginV={margin_v}"
    )

    # ── Ticker text (ASCII only, no special chars) ───────────
    ticker_text = (CHANNEL_NAME + " - TAAZA KHABAR - BREAKING NEWS - ") * 6

    # ── drawtext helper ──────────────────────────────────────
    def dt(text, color, size, x, y):
        s = f"drawtext=text='{text}':fontcolor={color}:fontsize={size}:x={x}:y={y}"
        if fp:
            s += f":fontfile={fp}"
        return s

    # ── Filter chain ─────────────────────────────────────────
    filters = []

    # 1. Color grade (warm cinematic)
    filters.append("eq=contrast=1.08:brightness=0.02:saturation=1.15")

    # 2. Vignette
    filters.append("vignette=PI/5")

    # 3. Subtitles at BOTTOM (low MarginV = near bottom edge)
    if os.path.exists(srt_path) and os.path.getsize(srt_path) > 0:
        filters.append(f"subtitles={srt_abs}:force_style='{sub_style}'")

    # 4. TOP dark bar (for channel name + LIVE)
    filters.append(
        f"drawbox=x=0:y=0:w={width}:h={top_bar_h}:color=black@0.88:t=fill"
    )

    # 5. Cyan accent line BELOW top bar
    filters.append(
        f"drawbox=x=0:y={top_bar_h}:w={width}:h=3:color=cyan:t=fill"
    )

    # 6. TACHYON NEWS — top left
    filters.append(dt(CHANNEL_NAME, "cyan", 28, 18, ch_y))

    # 7. LIVE — top right
    filters.append(dt("LIVE", "red", 20, live_x, live_y))

    vf = ",".join(filters)

    cmd = [
        "ffmpeg", "-y",
        "-i", input_video,
        "-vf", vf,
        "-c:v", "libx264", "-preset", "fast", "-crf", "17",
        "-c:a", "aac", "-b:a", "192k",
        output_video
    ]

    code, err = ffmpeg_run(cmd)
    if code == 0:
        print(f"Rendered successfully!")
        return True

    print(f"Full render failed (code {code}):")
    print(err[-2000:])

    # ── Fallback: subtitles + boxes only, no drawtext ────────
    print("Trying fallback (no drawtext)...")
    f2 = [
        "eq=contrast=1.05:brightness=0.02:saturation=1.1",
    ]
    if os.path.exists(srt_path) and os.path.getsize(srt_path) > 0:
        f2.append(f"subtitles={srt_abs}:force_style='{sub_style}'")
    f2.append(f"drawbox=x=0:y=0:w={width}:h={top_bar_h}:color=black@0.88:t=fill")
    f2.append(f"drawbox=x=0:y={top_bar_h}:w={width}:h=3:color=cyan:t=fill")

    cmd2 = [
        "ffmpeg", "-y", "-i", input_video,
        "-vf", ",".join(f2),
        "-c:v", "libx264", "-preset", "fast", "-crf", "17",
        "-c:a", "aac", "-b:a", "192k",
        output_video
    ]
    code2, err2 = ffmpeg_run(cmd2)
    if code2 == 0:
        print("Fallback saved!")
        return True

    print(f"Fallback also failed:\n{err2[-500:]}")
    return False


def main():
    print("=" * 52)
    print("   TACHYON NEWS VIDEO EDITOR  v5")
    print("=" * 52)

    if not os.path.exists(INPUT_VIDEO):
        print(f"ERROR: File not found: {INPUT_VIDEO}")
        print("Usage: python script.py \"Your Video.mp4\"")
        return

    font          = find_font()
    width, height = get_video_size(INPUT_VIDEO)
    print(f"Video size: {width}x{height}")

    # Transcribe
    words = transcribe(INPUT_VIDEO, LANGUAGE_HINT)

    srt_path = "subs.srt"
    if words:
        make_srt(words, WORDS_PER_SUB, srt_path)
    else:
        print("No words — rendering without subtitles")
        open(srt_path, "w").close()

    # Render
    ok = build_video(INPUT_VIDEO, srt_path, OUTPUT_VIDEO, font, width, height)

    # Cleanup
    if os.path.exists(srt_path):
        os.remove(srt_path)

    print("=" * 52)
    if ok and os.path.exists(OUTPUT_VIDEO):
        mb = os.path.getsize(OUTPUT_VIDEO) / 1048576
        print(f"DONE!  Output: {OUTPUT_VIDEO}  ({mb:.1f} MB)")
    else:
        print("FAILED — check errors above.")
    print("=" * 52)


if __name__ == "__main__":
    main()
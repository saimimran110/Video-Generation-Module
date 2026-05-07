"""
Tachyon News Expander — Groq powered
======================================
- Choti news lo, anchor style mein bara karo
- Auto language detect (English / Roman Urdu)
- Tachyon News branding add karo
- 15-20 second ki script banao

Requirements:
    pip install groq
"""

from groq import Groq

# ══════════════════════════════════════════
#  CONFIG
# ══════════════════════════════════════════
import os
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "your_api_key_here")
CHANNEL_NAME = "Tachyon News"
# ══════════════════════════════════════════

client = Groq(api_key=GROQ_API_KEY)


def detect_language(text: str) -> str:
    """
    Simple Roman Urdu detection:
    Agar common Urdu words hain toh 'urdu', warna 'english'
    """
    urdu_words = [
        "hai", "hain", "ka", "ki", "ke", "ko", "se", "mein", "par",
        "aur", "ya", "nahi", "tha", "thi", "the", "ho", "ga", "gi",
        "ne", "bhi", "koi", "kuch", "ab", "phir", "lekin", "kyun",
        "kya", "yeh", "wo", "ap", "aap", "main", "hum", "tum",
        "woh", "iska", "uska", "unka", "hamara", "tumhara",
        "taaza", "khabar", "pakistan", "rupay", "hukumat", "awam"
    ]

    words = text.lower().split()
    urdu_count = sum(1 for w in words if w in urdu_words)
    ratio = urdu_count / len(words) if words else 0

    return "urdu" if ratio >= 0.15 else "english"


def expand_news(raw_news: str, language: str) -> str:
    """Groq se news ko anchor style mein expand karo"""

    if language == "urdu":
        system_prompt = f"""Aap {CHANNEL_NAME} ke liye ek professional news anchor hain jo Roman Urdu mein bolte hain.
Aapka kaam hai choti khabar ko ek professional anchor ki tarah 15-20 second ki news script mein badalna.

Rules:
- Shuru mein "{CHANNEL_NAME} pe khush aamdeed" ya similar greeting karo
- News ko professional anchor style mein expand karo — thodi details add karo
- End mein "Dekhty rahiye {CHANNEL_NAME}. Khuda Hafiz " ya similar closing karo
- Sirf Roman Urdu use karo (Urdu script nahi)
- Script 60-80 words ki honi chahiye (15-20 second ke liye)
- Koi extra explanation mat do — sirf script likho"""

    else:
        system_prompt = f"""You are a professional news anchor for {CHANNEL_NAME}.
Your job is to take a short news headline and expand it into a 15-20 second anchor-style news script.

Rules:
- Start with "Welcome to {CHANNEL_NAME}" or similar branding
- Expand the news professionally — add context and details naturally
- End with "Stay tuned to {CHANNEL_NAME}" or similar sign-off
- Keep it to 60-80 words (perfect for 15-20 seconds)
- Output ONLY the script — no labels, no explanations"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": raw_news}
        ],
        max_tokens=200,
        temperature=0.7,
    )

    return response.choices[0].message.content.strip()


def generate_youtube_metadata(script: str, language: str) -> dict:
    """Groq se YouTube title aur description generate karo"""
    system_prompt = f"""Aap ek expert YouTube SEO manager hain.
Aapka kaam hai ek news script ke liye viral YouTube Short ka title aur description banana.

Rules:
- Title catchy aur clickbaity hona chahiye (max 60 characters).
- Title ke end mein " | {CHANNEL_NAME}" zaroor add karein.
- Description mein 2-3 line ka summary aur relevant hashtags (#{CHANNEL_NAME.replace(" ", "")} #Shorts #BreakingNews) hon.
- Agar script Roman Urdu mein hai, to title/description bhi Roman Urdu ya aasan English mein ho.
- Output MUST be strictly in JSON format with exactly two keys: "title" and "description". Do not add any markdown formatting or explanation.

Example Output:
{{
  "title": "Stock Market Hits Record High! | {CHANNEL_NAME}",
  "description": "The stock market has reached unprecedented levels today... \\n\\n#{CHANNEL_NAME.replace(" ", "")} #Shorts #StockMarket"
}}"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Language: {language}\nScript: {script}"}
        ],
        max_tokens=300,
        temperature=0.7,
        response_format={"type": "json_object"}
    )

    import json
    try:
        res_text = response.choices[0].message.content.strip()
        metadata = json.loads(res_text)
        return metadata
    except Exception as e:
        print(f"Error parsing JSON from Groq: {e}")
        # Fallback
        return {
            "title": f"Breaking News Update | {CHANNEL_NAME}",
            "description": f"{script}\n\n#{CHANNEL_NAME.replace(' ', '')} #Shorts #BreakingNews"
        }


def process_news(raw_news: str) -> dict:
    """Full pipeline — detect language, expand, return result"""

    lang = detect_language(raw_news)
    script = expand_news(raw_news, lang)
    yt_meta = generate_youtube_metadata(script, lang)

    return {
        "original": raw_news,
        "language": lang,
        "script": script,
        "yt_title": yt_meta.get("title", f"Breaking News | {CHANNEL_NAME}"),
        "yt_description": yt_meta.get("description", f"{script}\n\n#{CHANNEL_NAME.replace(' ', '')} #Shorts"),
    }


def main():
    print("=" * 55)
    print("   TACHYON NEWS EXPANDER")
    print("=" * 55)
    print()
    print("Choti news enter karo (Enter dabao):")
    print("-" * 40)
    raw_news = input().strip()

    if not raw_news:
        print("News empty hai!")
        return

    print()
    print("[>] Language detect kar raha hun...")
    result = process_news(raw_news)

    print()
    print("=" * 55)
    print(f"  LANGUAGE : {'URDU (Roman)' if result['language'] == 'urdu' else 'ENGLISH'}")
    if result['language'] == 'urdu':
        print("  FLAG     : 🇵🇰 URDU NEWS DETECTED")
    else:
        print("  FLAG     : 🇬🇧 ENGLISH NEWS DETECTED")
    print("=" * 55)
    print()
    print("EXPANDED SCRIPT:")
    print("-" * 40)
    print(result['script'])
    print("-" * 40)
    print()

    return result


if __name__ == "__main__":
    main()
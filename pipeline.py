import feedparser
import json
import os
from datetime import datetime

# ======================
# CONFIG
# ======================
OUTPUT_PATH = "data/news.json"

RSS_FEEDS = [
    # 🇻🇳 VIỆT NAM
    ("VN", "VNExpress", "https://vnexpress.net/rss/cong-nghe.rss"),
    ("VN", "Tuổi Trẻ", "https://tuoitre.vn/rss/cong-nghe.rss"),
    ("VN", "Thanh Niên", "https://thanhnien.vn/rss/cong-nghe.rss"),
    ("VN", "Tiền Phong", "https://tienphong.vn/rss/cong-nghe-45.rss"),

    # 🌍 GLOBAL
    ("GLOBAL", "MIT Tech Review", "https://www.technologyreview.com/feed/"),
    ("GLOBAL", "The Verge AI", "https://www.theverge.com/rss/ai/index.xml"),
    ("GLOBAL", "VentureBeat AI", "https://venturebeat.com/category/ai/feed/"),
]

AI_KEYWORDS = [
    "ai",
    "artificial intelligence",
    "trí tuệ nhân tạo",
    "machine learning",
    "deep learning",
    "openai",
    "chatgpt",
    "robot",
    "automation",
]

# ======================
# HELPERS
# ======================
def is_ai_related(text: str) -> bool:
    text = text.lower()
    return any(k in text for k in AI_KEYWORDS)


def normalize_title(title: str) -> str:
    return (
        title.lower()
        .replace("ai", "")
        .replace("trí tuệ nhân tạo", "")
        .replace("artificial intelligence", "")
        .strip()
    )


def extract_image(entry):
    # ưu tiên media_content
    if "media_content" in entry:
        return entry.media_content[0].get("url")

    # fallback: image trong summary
    if "summary" in entry:
        import re
        match = re.search(r'<img[^>]+src="([^">]+)"', entry.summary)
        if match:
            return match.group(1)

    return None


# ======================
# PIPELINE
# ======================
def run_pipeline():
    os.makedirs("data", exist_ok=True)

    if os.path.exists(OUTPUT_PATH):
        with open(OUTPUT_PATH, "r", encoding="utf-8") as f:
            existing_news = json.load(f)
    else:
        existing_news = []

    seen = set()
    cleaned = []

    # dedup existing
    for n in existing_news:
        key = (normalize_title(n["title"]), n["source"])
        if key not in seen:
            seen.add(key)
            cleaned.append(n)

    # fetch new
    for country, source, url in RSS_FEEDS:
        feed = feedparser.parse(url)

        for entry in feed.entries:
            title = entry.get("title", "")
            summary = entry.get("summary", "")

            if not is_ai_related(title + summary):
                continue

            key = (normalize_title(title), source)
            if key in seen:
                continue

            item = {
                "title": title,
                "summary": summary[:300] + "...",
                "url": entry.get("link"),
                "image": extract_image(entry),
                "source": source,
                "country": country,
                "category": "AI News",
                "published": entry.get("published", ""),
                "created_at": datetime.utcnow().isoformat(),
            }

            seen.add(key)
            cleaned.append(item)

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(cleaned, f, ensure_ascii=False, indent=2)

    print(f"✅ DONE: {len(cleaned)} articles")


if __name__ == "__main__":
    run_pipeline()

import feedparser
import json
import os
import hashlib
from datetime import datetime
from html import unescape

# =========================
# CONFIG
# =========================

DATA_DIR = "data"
OUTPUT_FILE = os.path.join(DATA_DIR, "news.json")

RSS_SOURCES = [
    # 🇻🇳 VIETNAM
    {"name": "Tuổi Trẻ", "country": "VN", "rss": "https://tuoitre.vn/rss/cong-nghe.rss"},
    {"name": "VnExpress", "country": "VN", "rss": "https://vnexpress.net/rss/so-hoa.rss"},
    {"name": "Thanh Niên", "country": "VN", "rss": "https://thanhnien.vn/rss/cong-nghe.rss"},
    {"name": "Tiền Phong", "country": "VN", "rss": "https://tienphong.vn/rss/cong-nghe.rss"},
    {"name": "VietnamNet", "country": "VN", "rss": "https://vietnamnet.vn/rss/cong-nghe.rss"},
    {"name": "Dân Trí", "country": "VN", "rss": "https://dantri.com.vn/rss/cong-nghe.rss"},

    # 🌍 GLOBAL
    {"name": "TechCrunch", "country": "Global", "rss": "https://techcrunch.com/feed/"},
    {"name": "MIT Tech Review", "country": "Global", "rss": "https://www.technologyreview.com/feed/"},
    {"name": "VentureBeat AI", "country": "Global", "rss": "https://venturebeat.com/category/ai/feed/"},
    {"name": "The Verge", "country": "Global", "rss": "https://www.theverge.com/rss/index.xml"},
    {"name": "Wired", "country": "Global", "rss": "https://www.wired.com/feed/rss"},
]

AI_KEYWORDS = [
    "ai", "artificial intelligence", "trí tuệ nhân tạo",
    "machine learning", "deep learning",
    "chatgpt", "openai", "google ai",
    "robot", "drone", "tự động hóa"
]

MAX_ITEMS_PER_SOURCE = 20

# =========================
# HELPERS
# =========================

def is_ai_related(text: str) -> bool:
    text = text.lower()
    return any(k in text for k in AI_KEYWORDS)

def clean_text(text: str) -> str:
    if not text:
        return ""
    return unescape(text).replace("\n", " ").strip()

def extract_image(entry):
    if "media_content" in entry:
        return entry.media_content[0].get("url")
    if "media_thumbnail" in entry:
        return entry.media_thumbnail[0].get("url")
    return None

def make_uid(title, link):
    raw = f"{title}-{link}"
    return hashlib.md5(raw.encode("utf-8")).hexdigest()

# =========================
# MAIN PIPELINE
# =========================

def run_pipeline():
    os.makedirs(DATA_DIR, exist_ok=True)

    news = []
    seen = set()

    for source in RSS_SOURCES:
        print(f"🔎 Fetching: {source['name']}")
        feed = feedparser.parse(source["rss"])

        for entry in feed.entries[:MAX_ITEMS_PER_SOURCE]:
            title = clean_text(entry.get("title", ""))
            summary = clean_text(entry.get("summary", ""))
            link = entry.get("link", "")

            if not title or not link:
                continue

            text_blob = f"{title} {summary}"
            if not is_ai_related(text_blob):
                continue

            uid = make_uid(title, link)
            if uid in seen:
                continue
            seen.add(uid)

            image = extract_image(entry)

            news.append({
                "title": title,
                "summary": summary,
                "url": link,
                "source": source["name"],
                "country": source["country"],
                "category": "AI",
                "image": image,
                "published_at": entry.get("published", ""),
                "uid": uid
            })

    # sort newest first (rough)
    news = news[::-1]

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(news, f, ensure_ascii=False, indent=2)

    print(f"✅ Saved {len(news)} AI news to {OUTPUT_FILE}")

# =========================
# RUN
# =========================

if __name__ == "__main__":
    run_pipeline()

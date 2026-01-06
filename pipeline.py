import os
import json
import hashlib
from datetime import datetime

DATA_DIR = "data"
NEWS_FILE = f"{DATA_DIR}/news.json"
CACHE_FILE = f"{DATA_DIR}/cache.json"

# =====================
# 1️⃣ LOAD CACHE
# =====================
def load_cache():
    if not os.path.exists(CACHE_FILE):
        return {}
    with open(CACHE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

# =====================
# 2️⃣ SAVE CACHE
# =====================
def save_cache(cache):
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)

# =====================
# 3️⃣ LOAD NEWS (ĐỂ CHỐNG TRÙNG)
# =====================
def load_existing_news():
    if not os.path.exists(NEWS_FILE):
        return []
    with open(NEWS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

# =====================
# 4️⃣ TẠO KEY TỪ URL
# =====================
def url_to_key(url: str) -> str:
    return hashlib.md5(url.encode()).hexdigest()

# =====================
# 5️⃣ MAIN LOGIC
# =====================
def process_article(article, cache, existing_urls):
    """
    article = {
        title, content, url, source, country, category
    }
    """

    # ❌ DEDUP: nếu URL đã tồn tại → bỏ
    if article["url"] in existing_urls:
        print("⏭️ Skip duplicate:", article["url"])
        return None

    key = url_to_key(article["url"])

    # ✅ CACHE HIT → dùng lại
    if key in cache:
        print("♻️ Use cached summary:", article["url"])
        summary = cache[key]["summary"]
        hot_score = cache[key]["hot_score"]

    # 🤖 CACHE MISS → gọi AI
    else:
        print("🤖 Call AI:", article["url"])

        summary = fake_ai_summarize(article["content"])
        hot_score = fake_hot_score(article)

        cache[key] = {
            "url": article["url"],
            "summary": summary,
            "hot_score": hot_score,
            "created_at": datetime.utcnow().isoformat()
        }

    return {
        "title": article["title"],
        "summary": summary,
        "country": article["country"],
        "category": article["category"],
        "source": article["source"],
        "hot_score": hot_score,
        "url": article["url"]
    }

# =====================
# 6️⃣ FAKE AI (ĐỂ TEST)
# =====================
def fake_ai_summarize(text):
    return text[:200] + "..."

def fake_hot_score(article):
    score = 5
    if article["country"] == "VN":
        score += 2
    if "AI" in article["title"]:
        score += 2
    return score

# =====================
# 7️⃣ RUN
# =====================
def run_pipeline(new_articles):
    cache = load_cache()
    news = load_existing_news()

    existing_urls = {n["url"] for n in news}
    new_items = []

    for a in new_articles:
        item = process_article(a, cache, existing_urls)
        if item:
            new_items.append(item)

    if new_items:
        news = new_items + news
        with open(NEWS_FILE, "w", encoding="utf-8") as f:
            json.dump(news, f, ensure_ascii=False, indent=2)

        save_cache(cache)

    print(f"✅ Added {len(new_items)} new items")
if __name__ == "__main__":
    test_articles = [
        {
            "title": "AI Việt Nam thử nghiệm drone giao hàng",
            "content": "TP HCM thử nghiệm giao hàng bằng thiết bị bay không người lái...",
            "url": "https://vnexpress.net/ai-drone",
            "source": "VNExpress",
            "country": "VN",
            "category": "Ứng dụng AI"
        },
        {
            "title": "AI Việt Nam thử nghiệm drone giao hàng (LẶP)",
            "content": "TP HCM thử nghiệm giao hàng bằng thiết bị bay không người lái...",
            "url": "https://vnexpress.net/ai-drone",
            "source": "VNExpress",
            "country": "VN",
            "category": "Ứng dụng AI"
        }
    ]

    run_pipeline(test_articles)


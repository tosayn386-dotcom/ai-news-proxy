import feedparser, yaml, json, hashlib, datetime, re
from pathlib import Path
from openai import OpenAI
import os

# ===== CONFIG =====
MAX_ITEMS = 8
DATA_PATH = Path("data/news.json")
CACHE_DIR = Path("cache")
SEEN_FILE = CACHE_DIR / "seen_links.json"
AI_CACHE_FILE = CACHE_DIR / "ai_cache.json"

AI_KEYWORDS = [
    "ai","artificial intelligence","machine learning",
    "deep learning","trí tuệ nhân tạo","chatbot","llm"
]

VN_HINTS = ["việt nam","tp hcm","hà nội","fpt","vinai","zalo"]

HOT_KEYWORDS = [
    "openai","google","meta","gpt","chatgpt",
    "ra mắt","launch","lừa","sai sự thật","mặt trái"
]

SOURCE_WEIGHT = {
    "OpenAI": 5,
    "Google AI": 4,
    "VnExpress": 2,
    "Vietnamnet": 2
}

# ===== OPENAI =====
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def llm_call(prompt):
    r = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role":"user","content":prompt}],
        temperature=0.3
    )
    return r.choices[0].message.content.strip()

# ===== HELPERS =====
def clean(t): return re.sub(r"<[^>]+>","",t or "").strip()
def h(s): return hashlib.md5(s.encode()).hexdigest()

def load_json(p, default):
    if p.exists(): return json.loads(p.read_text(encoding="utf-8"))
    return default

def save_json(p, obj):
    p.parent.mkdir(exist_ok=True)
    p.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")

# ===== PIPELINE =====
sources = yaml.safe_load(open("sources.yaml",encoding="utf-8"))
seen = set(load_json(SEEN_FILE, []))
ai_cache = load_json(AI_CACHE_FILE, {})
output = []

for region, feeds in sources.items():
    for src in feeds:
        feed = feedparser.parse(src["rss"])
        for e in feed.entries[:MAX_ITEMS]:
            title = clean(e.get("title",""))
            summary = clean(e.get("summary",""))
            link = e.get("link","")

            if h(link) in seen: continue
            if not any(k in (title+summary).lower() for k in AI_KEYWORDS): continue

            country = "VN" if region=="vietnam" or any(v in (title+summary).lower() for v in VN_HINTS) else "GLOBAL"

            ck = h(title+summary)
            if ck in ai_cache:
                summary_vi = ai_cache[ck]["summary"]
                category = ai_cache[ck]["category"]
            else:
                category = llm_call(
                    f"Classify into ONE: AI Tools, Research, Business, Policy, Ethics\n\n{title}\n{summary}"
                )
                summary_vi = llm_call(
                    f"Tóm tắt bằng tiếng Việt, tự nhiên, 3–4 câu:\n\n{title}\n{summary}"
                )
                ai_cache[ck] = {"summary":summary_vi,"category":category}

            hot = sum(2 for k in HOT_KEYWORDS if k in (title+summary).lower())
            hot += SOURCE_WEIGHT.get(src["name"],1)

            output.append({
                "title": title,
                "summary": summary_vi,
                "country": country,
                "category": category,
                "hot_score": hot,
                "source": src["name"],
                "link": link,
                "date": e.get("published",""),
                "generated_at": datetime.datetime.utcnow().isoformat()
            })

            seen.add(h(link))

save_json(DATA_PATH, output)
save_json(SEEN_FILE, list(seen))
save_json(AI_CACHE_FILE, ai_cache)

print(f"✅ Generated {len(output)} items")

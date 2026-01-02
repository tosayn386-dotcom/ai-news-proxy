export default {
  async fetch(request) {
    if (request.method === "OPTIONS") {
      return new Response(null, { headers: corsHeaders() });
    }

    const url = new URL(request.url);
    const total = clampInt(url.searchParams.get("n"), 60, 1, 200);
    const vnQuota = Math.floor(total / 2);
    const glQuota = total - vnQuota;

    const VN_FEEDS = [
      "https://vtv.vn/rss/vuon-minh-bang-ai.rss",
      "https://vtv.vn/rss/vuon-minh-bang-ai/thoi-dai-ai.rss",
      "https://vtv.vn/rss/vuon-minh-bang-ai/doanh-nghiep-thoi-ai.rss",
      "https://vtv.vn/rss/vuon-minh-bang-ai/goc-nhin-ai.rss",
      "https://vtv.vn/rss/vuon-minh-bang-ai/kien-thuc-dao-tao-ai.rss",
      "https://genk.vn/rss/ai.rss",
    ];

    const GLOBAL_FEEDS = [
      "https://openai.com/blog/rss.xml",
      "https://blog.google/technology/ai/rss/",
      "https://huggingface.co/blog/feed.xml",
      "https://research.google/blog/rss",
    ];

    const [vnItems, glItems] = await Promise.all([
      fetchMany(VN_FEEDS, "VN"),
      fetchMany(GLOBAL_FEEDS, "GLOBAL"),
    ]);

    vnItems.sort((a, b) => b.ts - a.ts);
    glItems.sort((a, b) => b.ts - a.ts);

    let vnPick = vnItems.slice(0, vnQuota);
    let glPick = glItems.slice(0, glQuota);

    if (vnPick.length < vnQuota) {
      glPick = glPick.concat(glItems.slice(glQuota, glQuota + (vnQuota - vnPick.length)));
    }
    if (glPick.length < glQuota) {
      vnPick = vnPick.concat(vnItems.slice(vnQuota, vnQuota + (glQuota - glPick.length)));
    }

    const mixed = interleave(vnPick, glPick, total);

    return new Response(JSON.stringify({ total: mixed.length, items: mixed }), {
      headers: {
        "content-type": "application/json; charset=utf-8",
        ...corsHeaders(),
        "cache-control": "no-store",
      },
    });
  },
};

function corsHeaders() {
  return {
    "access-control-allow-origin": "*",
    "access-control-allow-methods": "GET, OPTIONS",
    "access-control-allow-headers": "content-type",
  };
}

function clampInt(v, def, min, max) {
  const n = Number.parseInt(v ?? "", 10);
  if (Number.isNaN(n)) return def;
  return Math.max(min, Math.min(max, n));
}

async function fetchMany(feeds, region) {
  const results = await Promise.allSettled(
    feeds.map(async (feedUrl) => {
      const res = await fetch(feedUrl, { headers: { "user-agent": "Mozilla/5.0" } });
      if (!res.ok) return [];
      const xml = await res.text();
      return parseRssItems(xml, feedUrl, region);
    })
  );

  const out = [];
  for (const r of results) if (r.status === "fulfilled") out.push(...r.value);

  const seen = new Set();
  return out.filter((it) => {
    if (!it.link) return false;
    if (seen.has(it.link)) return false;
    seen.add(it.link);
    return true;
  });
}

function parseRssItems(xml, sourceUrl, region) {
  const items = [];
  const blocks = xml.match(/<item>[\s\S]*?<\/item>/g) || [];

  for (const b of blocks) {
    const title = getTag(b, "title");
    const link = getTag(b, "link");
    const desc = stripCdata(getTag(b, "description"));
    const pub = getTag(b, "pubDate");
    const ts = pub ? Date.parse(pub) : Date.now();

    const blob = (title + " " + desc).toLowerCase();
    if (!looksLikeAI(blob)) continue;

    items.push({
      region,
      sourceUrl,
      title: decodeHtml(title),
      link,
      summary: decodeHtml(stripHtml(desc)).slice(0, 450),
      pubDate: pub || "",
      ts: Number.isNaN(ts) ? Date.now() : ts,
    });
  }
  return items;
}

function looksLikeAI(s) {
  const kws = [
    "ai",
    "trí tuệ nhân tạo",
    "machine learning",
    "deep learning",
    "llm",
    "genai",
    "chatgpt",
    "openai",
    "gemini",
    "claude",
    "copilot",
    "agent",
    "tác nhân",
    "rag",
    "prompt",
  ];
  return kws.some((k) => s.includes(k));
}

function getTag(block, tag) {
  const m = block.match(new RegExp(`<${tag}[^>]*>([\\s\\S]*?)<\\/${tag}>`, "i"));
  return m ? m[1].trim() : "";
}

function stripCdata(s) {
  return s.replace(/^<!\\[CDATA\\[/, "").replace(/\\]\\]>$/, "");
}

function stripHtml(s) {
  return s.replace(/<[^>]+>/g, " ").replace(/\s+/g, " ").trim();
}

function decodeHtml(s) {
  return (s || "")
    .replace(/&amp;/g, "&")
    .replace(/&lt;/g, "<")
    .replace(/&gt;/g, ">")
    .replace(/&quot;/g, '"')
    .replace(/&#39;/g, "'");
}

function interleave(a, b, max) {
  const out = [];
  let i = 0,
    j = 0;
  while (out.length < max && (i < a.length || j < b.length)) {
    if (i < a.length) out.push(a[i++]);
    if (out.length >= max) break;
    if (j < b.length) out.push(b[j++]);
  }
  return out.slice(0, max);
}
``

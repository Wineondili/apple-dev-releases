#!/usr/bin/env python3
import feedparser, json, pathlib, datetime, os, requests, textwrap
from urllib.parse import quote_plus

RSS_URL = "https://developer.apple.com/news/releases/rss/releases.rss"
TARGET  = pathlib.Path("_data/releases.json")

# ---------- 解析 RSS ----------
feed = feedparser.parse(RSS_URL)
items = [{
    "date": datetime.datetime(*e.published_parsed[:6]).strftime("%Y-%m-%d"),
    "title": e.title,
    "link":  e.link,
} for e in feed.entries]

# ---------- 读取旧数据 ----------
old_items = json.loads(TARGET.read_text()) if TARGET.exists() else []
old_links = {it["link"] for it in old_items}

# ---------- 找出所有新条目 ----------
new_items = [it for it in reversed(items) if it["link"] not in old_links]
# reversed() → 最旧先推；去掉则最新先推

if not new_items:
    print("NO_CHANGE")
    exit(0)

# ---------- 写入最新完整列表 ----------
TARGET.write_text(json.dumps(items, indent=2, ensure_ascii=False))
print(f"UPDATED {len(new_items)} item(s)")

# ---------- 推送函数 ----------
def push(title, body, link):
    # Telegram
    tok, cid = os.getenv("TG_BOT_TOKEN"), os.getenv("TG_CHAT_ID")
    if tok and cid:
        requests.get(
            f"https://api.telegram.org/bot{tok}/sendMessage",
            params={"chat_id": cid,
                    "text": textwrap.dedent(f"{title}\n{body}\n{link}"),
                    "disable_web_page_preview": True},
            timeout=10)

    # Bark
    bark_key = os.getenv("BARK_KEY_MAIN")
    if bark_key:
        bark_url = (
            f"https://api.day.app/{bark_key}/"
            f"{quote_plus(title)}/{quote_plus(body)}"
            f"?url={quote_plus(link)}"
        )
        requests.get(bark_url, timeout=10)

# ---------- 逐条推送 ----------
for it in new_items:
    push("🍏 Apple Developer 更新",
         f"{it['date']} · {it['title']}",
         it['link'])

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Apple Developer Releases 监测脚本
依赖：pip install feedparser requests
"""

import feedparser, json, pathlib, datetime, os, requests, textwrap
from urllib.parse import quote_plus

RSS_URL = "https://developer.apple.com/news/releases/rss/releases.rss"
TARGET  = pathlib.Path("_data/releases.json")

# 过滤掉不需要推送的条目前缀
EXCLUDE_PREFIX = ("Xcode", "TestFlight", "App Store Connect", "Transporter")

# ---------- 抓取 RSS ----------
feed = feedparser.parse(RSS_URL)
items = [
    {
        "date": datetime.datetime(*e.published_parsed[:6]).strftime("%Y-%m-%d"),
        "title": e.title,
        "link":  e.link,
    }
    for e in feed.entries[:10]                       # 只要最新 10 条
    if not e.title.startswith(EXCLUDE_PREFIX)        # 过滤不需要的
]

# ---------- 去重 ----------
old_items = json.loads(TARGET.read_text()) if TARGET.exists() else []
old_links = {it["link"] for it in old_items}
new_items = [it for it in reversed(items) if it["link"] not in old_links]  # 最旧先推

if not new_items:
    print("NO_CHANGE")
    exit(0)

# ---------- 持久化 ----------
TARGET.write_text(json.dumps(items, indent=2, ensure_ascii=False))
print(f"UPDATED {len(new_items)} item(s)")

# ---------- 组装推送正文 ----------
title_text = "监测到Apple服务器已推送软件更新"
body_text  = "\n".join(it["title"] for it in new_items)
full_text  = f"{title_text}\n{body_text}"

# ---------- Telegram 推送 ----------
tok, cid = os.getenv("TG_BOT_TOKEN"), os.getenv("TG_CHAT_ID")
if tok and cid:
    requests.get(
        f"https://api.telegram.org/bot{tok}/sendMessage",
        params={"chat_id": cid, "text": full_text},
        timeout=10
    )

# ---------- Bark 推送 ----------
bark_key = os.getenv("BARK_KEY_MAIN")  # 也可以直接写成固定 Key
if bark_key:
    bark_url = (
        f"https://api.day.app/{bark_key}/"
        f"{quote_plus(title_text)}/"
        f"{quote_plus(body_text)}"
        f"?icon=https://cdn.jim-nielsen.com/watchos/512/apple-developer-2020-03-19.png"
        f"&level=timeSensitive"
        f"&url=https://developer.apple.com/news/releases/"
        f"&autoCopy=1"
        f"&copy={quote_plus(body_text)}"
    )
    requests.get(bark_url, timeout=10)

#!/usr/bin/env python3
import feedparser, json, pathlib, datetime, os, requests, textwrap

RSS_URL   = "https://developer.apple.com/news/releases/rss/releases.rss"
TARGET    = pathlib.Path("_data/releases.json")

# ---------- 解析 RSS ----------
feed  = feedparser.parse(RSS_URL)
items = [{
    "date": datetime.datetime(*e.published_parsed[:6]).strftime("%Y-%m-%d"),
    "title": e.title,
    "link":  e.link,
} for e in feed.entries]

# ---------- 比较旧数据 ----------
old = json.loads(TARGET.read_text()) if TARGET.exists() else []
if items == old:
    print("NO_CHANGE")
    quit()

# ---------- 写入新数据 ----------
TARGET.write_text(json.dumps(items, indent=2, ensure_ascii=False))
print("UPDATED")

latest = items[0]
msg_title = "🍏 Apple Developer 更新"
msg_body  = f"{latest['date']} · {latest['title']}"
msg_link  = latest['link']

# ---------- Telegram 推送 ----------
token  = os.getenv("TG_BOT_TOKEN")
chatid = os.getenv("TG_CHAT_ID")
if token and chatid:
    requests.get(
        f"https://api.telegram.org/bot{token}/sendMessage",
        params={
            "chat_id": chatid,
            "text": textwrap.dedent(f"""{msg_title}\n{msg_body}\n{msg_link}"""),
            "disable_web_page_preview": True,
        },
        timeout=10,
    )

# ---------- Bark 推送 ----------
bark_key = os.getenv("BARK_KEY_MAIN")         # 你保存的那个名称
if bark_key:
    bark_url = (
        f"https://api.day.app/{bark_key_main}/{msg_title}/{msg_body}"
        f"?url={msg_link}"
    )
    requests.get(bark_url, timeout=10)

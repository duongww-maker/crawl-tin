import json, re, html
from datetime import datetime, timezone
from pathlib import Path
import feedparser
from bs4 import BeautifulSoup
from feedgen.feed import FeedGenerator

ROOT = Path(__file__).parent
SOURCES = json.loads((ROOT/"sources.json").read_text(encoding="utf-8"))
KW = json.loads((ROOT/"keywords.json").read_text(encoding="utf-8"))

def clean(value):
    if not value: return ""
    value = BeautifulSoup(value, "html.parser").get_text(" ", strip=True)
    return re.sub(r"\s+", " ", html.unescape(value)).strip()

def hit(text):
    t = clean(text).lower()
    for group in ("mobility","brands","ambiguous"):
        for word in KW[group]:
            if word in t:
                return word
    return None

def entry_date(e):
    for key in ("published_parsed","updated_parsed"):
        v = getattr(e, key, None)
        if v:
            return datetime(*v[:6], tzinfo=timezone.utc)
    return datetime.now(timezone.utc)

def main():
    items, seen = [], set()
    for source in SOURCES:
        d = feedparser.parse(source["url"], request_headers={"User-Agent":"Mozilla/5.0 (VN Mobility RSS)"})
        print(source["name"], "entries:", len(d.entries))
        for e in d.entries:
            title = clean(getattr(e,"title",""))
            summary = clean(getattr(e,"summary","") or getattr(e,"description",""))
            link = getattr(e,"link","").strip()
            if not link or link in seen: continue
            keyword = hit(title + " " + summary)
            if not keyword: continue
            seen.add(link)
            items.append(dict(source=source["name"], title=title, summary=summary,
                              link=link, date=entry_date(e), keyword=keyword))

    items.sort(key=lambda x:x["date"], reverse=True)
    items = items[:500]

    fg = FeedGenerator()
    fg.id("https://github.com/duongww-maker/crawl-tin")
    fg.title("VN Mobility News")
    fg.link(href="https://github.com/duongww-maker/crawl-tin", rel="alternate")
    fg.link(href="https://raw.githubusercontent.com/duongww-maker/crawl-tin/main/feed.xml", rel="self")
    fg.description("Tin xe cộ, giao thông, tai nạn, đường sắt, tàu thuyền và thương hiệu xe.")
    fg.language("vi")

    for x in items:
        fe = fg.add_entry()
        fe.id(x["link"])
        fe.title(f'[{x["source"]}] {x["title"]}')
        fe.link(href=x["link"])
        fe.description(f'Từ khóa khớp: {x["keyword"]}<br><br>{x["summary"]}')
        fe.pubDate(x["date"])

    fg.rss_file(str(ROOT/"feed.xml"))
    print("Wrote", len(items), "matching items")

if __name__ == "__main__":
    main()

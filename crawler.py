import json, re, html
from datetime import datetime, timezone
from pathlib import Path
import feedparser
from bs4 import BeautifulSoup
from feedgen.feed import FeedGenerator

ROOT = Path(__file__).parent
SOURCES = json.loads((ROOT / "sources.json").read_text(encoding="utf-8"))
KW = json.loads((ROOT / "keywords.json").read_text(encoding="utf-8"))

# Brand names that commonly appear outside automotive contexts.
CONTEXT_BRANDS = {
    "xiaomi", "ford", "mini", "smart", "ram", "tank", "ora", "genesis",
    "seat", "tata", "jac", "faw", "gac", "mg", "lotus", "hero"
}

VEHICLE_CONTEXT = [
    "xe", "ô tô", "oto", "xe hơi", "mẫu xe", "hãng xe", "thương hiệu xe",
    "suv", "sedan", "crossover", "mpv", "pickup", "bán tải", "xe điện", "ev",
    "hybrid", "phev", "hev", "reev", "động cơ", "hộp số", "pin", "sạc",
    "trạm sạc", "đại lý", "showroom", "lăn bánh", "đăng ký", "biển số",
    "mô tô", "môtô", "xe máy", "scooter", "motorcycle"
]

def clean(value):
    if not value:
        return ""
    value = BeautifulSoup(value, "html.parser").get_text(" ", strip=True)
    return re.sub(r"\s+", " ", html.unescape(value)).strip()

def phrase_pattern(term):
    # Whole token/phrase matching prevents ford in Crawford/Stanford,
    # ora in Manora, oto inside unrelated words, etc.
    return re.compile(r"(?<![\wÀ-ỹ])" + re.escape(term.lower()) + r"(?![\wÀ-ỹ])", re.I)

def contains_phrase(text, term):
    return bool(phrase_pattern(term).search(text))

def has_vehicle_context(text):
    return any(contains_phrase(text, x) for x in VEHICLE_CONTEXT)

def hit(title, summary):
    # Give the title more weight. Summary is still searched to maximize recall.
    title_l = clean(title).lower()
    summary_l = clean(summary).lower()
    full = title_l + " " + summary_l

    for term in KW["mobility"]:
        if contains_phrase(full, term):
            return term

    for term in KW.get("ambiguous", []):
        if contains_phrase(full, term):
            return term

    for brand in KW["brands"]:
        if not contains_phrase(full, brand):
            continue
        if brand.lower() in CONTEXT_BRANDS:
            # Accept an ambiguous brand if title itself contains automotive context,
            # or the surrounding article summary contains automotive context.
            if has_vehicle_context(full):
                return brand
            continue
        return brand

    return None

def entry_date(e):
    for key in ("published_parsed", "updated_parsed"):
        v = getattr(e, key, None)
        if v:
            return datetime(*v[:6], tzinfo=timezone.utc)
    return datetime.now(timezone.utc)

def normalize_title(title):
    t = clean(title).lower()
    t = re.sub(r"\[[^\]]+\]", " ", t)
    t = re.sub(r"[^0-9a-zà-ỹ]+", " ", t, flags=re.I)
    return re.sub(r"\s+", " ", t).strip()

def title_signature(title):
    # Used only for exact/near-exact syndication duplicates.
    words = normalize_title(title).split()
    stop = {"video", "clip", "ảnh", "photo", "photostory", "mới", "nhất"}
    words = [w for w in words if w not in stop]
    return " ".join(words)

def main():
    candidates = []
    seen_links = set()

    for source in SOURCES:
        d = feedparser.parse(
            source["url"],
            request_headers={"User-Agent": "Mozilla/5.0 (VN Mobility RSS)"}
        )
        print(source["name"], "entries:", len(d.entries))

        for e in d.entries:
            title = clean(getattr(e, "title", ""))
            summary = clean(getattr(e, "summary", "") or getattr(e, "description", ""))
            link = getattr(e, "link", "").strip()
            if not link or link in seen_links:
                continue

            keyword = hit(title, summary)
            if not keyword:
                continue

            seen_links.add(link)
            candidates.append({
                "source": source["name"],
                "title": title,
                "summary": summary,
                "link": link,
                "date": entry_date(e),
                "keyword": keyword,
            })

    # Newest first, then suppress near-identical syndicated headlines.
    candidates.sort(key=lambda x: x["date"], reverse=True)
    items = []
    seen_titles = set()

    for item in candidates:
        sig = title_signature(item["title"])
        if sig and sig in seen_titles:
            continue
        if sig:
            seen_titles.add(sig)
        items.append(item)
        if len(items) >= 500:
            break

    fg = FeedGenerator()
    fg.id("https://github.com/duongww-maker/crawl-tin")
    fg.title("VN Mobility News")
    fg.link(href="https://github.com/duongww-maker/crawl-tin", rel="alternate")
    fg.link(
        href="https://raw.githubusercontent.com/duongww-maker/crawl-tin/main/feed.xml",
        rel="self",
    )
    fg.description(
        "Tin xe cộ, giao thông, tai nạn, đường sắt, tàu thuyền và thương hiệu xe."
    )
    fg.language("vi")

    for x in items:
        fe = fg.add_entry()
        fe.id(x["link"])
        fe.title(f'[{x["source"]}] {x["title"]}')
        fe.link(href=x["link"])
        fe.description(f'Từ khóa khớp: {x["keyword"]}<br><br>{x["summary"]}')
        fe.pubDate(x["date"])

    fg.rss_file(str(ROOT / "feed.xml"))
    print("Candidates:", len(candidates))
    print("Wrote:", len(items), "filtered/deduplicated items")

if __name__ == "__main__":
    main()

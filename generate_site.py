from __future__ import annotations

import csv
import html
import re
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, List


ROOT = Path(__file__).parent
CSV_PATH = ROOT / "restaurant_119HW.csv"
DOCS_DIR = ROOT / "docs"
ASSETS_DIR = DOCS_DIR / "assets"
RESTAURANTS_DIR = DOCS_DIR / "restaurants"


@dataclass
class Restaurant:
    slug: str
    name: str
    map_url: str
    rating: str
    review_count: str
    category: str
    address: str
    status: str
    hours: str
    image_url: str
    services: List[str] = field(default_factory=list)
    action_label: str = ""
    action_url: str = ""
    price: str = ""
    secondary_links: List[tuple[str, str]] = field(default_factory=list)


def slugify(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text).strip().lower()
    collapsed = re.sub(r"[\s_]+", "-", normalized)
    safe = re.sub(r"[^\w\-]", "", collapsed)
    return safe or "restaurant"


def clean_text(value: str) -> str:
    value = (value or "").strip()
    if not value or value == "·":
        return ""
    lines = [line.strip(" ·") for line in value.splitlines() if line.strip(" ·")]
    if not lines:
        return ""
    text = lines[-1]
    if len(text) == 1 and ord(text) > 0xE000:
        return ""
    return text


def read_restaurants() -> list[Restaurant]:
    if not CSV_PATH.exists():
        raise FileNotFoundError(f"Unable to find data file at {CSV_PATH}")

    with CSV_PATH.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        restaurants: list[Restaurant] = []
        used_slugs: set[str] = set()

        for index, row in enumerate(reader):
            name = clean_text(row.get("qBF1Pd", "")) or f"餐廳 {index + 1}"
            slug_base = slugify(name)
            slug = slug_base
            counter = 2
            while slug in used_slugs:
                slug = f"{slug_base}-{counter}"
                counter += 1
            used_slugs.add(slug)

            services = [
                clean_text(row.get(key, ""))
                for key in ["ah5Ghc", "ah5Ghc (2)", "ah5Ghc (3)"]
            ]
            services = [service for service in services if service]

            action_label = clean_text(row.get("J8zHNe", ""))
            action_url = (row.get("A1zNzb href") or "").strip()
            price = clean_text(row.get("AJB7ye (2)", ""))
            review_count = clean_text(row.get("UY7F9", ""))
            if review_count:
                review_count = review_count.strip("()")

            secondary_links: list[tuple[str, str]] = []
            alt_url = (row.get("A1zNzb href (2)") or "").strip()
            alt_label = clean_text(row.get("J8zHNe (2)", ""))
            if alt_url and alt_label:
                secondary_links.append((alt_label, alt_url))

            restaurants.append(
                Restaurant(
                    slug=slug,
                    name=name,
                    map_url=(row.get("hfpxzc href") or "").strip(),
                    rating=clean_text(row.get("MW4etd", "")),
                    review_count=review_count,
                    category=clean_text(row.get("W4Efsd", "")),
                    address=clean_text(row.get("W4Efsd (3)", "")),
                    status=clean_text(row.get("W4Efsd (4)", "")),
                    hours=clean_text(row.get("W4Efsd (5)", "")),
                    image_url=(row.get("FQ2IWe src") or "").strip(),
                    services=services,
                    action_label=action_label,
                    action_url=action_url,
                    price=price,
                    secondary_links=secondary_links,
                )
            )

    return restaurants


def html_escape(text: str) -> str:
    return html.escape(text, quote=True)


def build_card(restaurant: Restaurant) -> str:
    price = f"<span class='price'>{html_escape(restaurant.price)}</span>" if restaurant.price else ""
    rating = ""
    if restaurant.rating:
        rating = (
            f"<div class='rating'>⭐ {html_escape(restaurant.rating)} "
            f"<span class='reviews'>({html_escape(restaurant.review_count)})</span></div>"
        )

    image = (
        f"<div class='card-image'><img src='{html_escape(restaurant.image_url)}' alt='{html_escape(restaurant.name)}'></div>"
        if restaurant.image_url
        else "<div class='card-image placeholder'>沒有圖片</div>"
    )
    return f"""
    <article class='card'>
      <a class='card-link' href='restaurants/{restaurant.slug}/'>
        {image}
        <div class='card-body'>
          <h2>{html_escape(restaurant.name)}</h2>
          <p class='meta'>
            {rating}
            <span class='category'>{html_escape(restaurant.category)}</span>
            {price}
          </p>
          <p class='status'>{html_escape(restaurant.status)} {html_escape(restaurant.hours)}</p>
          <p class='address'>{html_escape(restaurant.address)}</p>
        </div>
      </a>
    </article>
    """


def build_detail(restaurant: Restaurant) -> str:
    services_html = "".join(
        f"<li><span class='bullet'>•</span> {html_escape(service)}</li>"
        for service in restaurant.services
    )
    services_block = (
        f"<ul class='services'>{services_html}</ul>" if services_html else "<p class='muted'>尚未提供服務資訊</p>"
    )

    actions: list[str] = []
    if restaurant.action_label and restaurant.action_url:
        actions.append(
            f"<a class='button primary' href='{html_escape(restaurant.action_url)}' target='_blank' rel='noopener'>{html_escape(restaurant.action_label)}</a>"
        )
    if restaurant.map_url:
        actions.append(
            f"<a class='button secondary' href='{html_escape(restaurant.map_url)}' target='_blank' rel='noopener'>查看地圖</a>"
        )
    for label, url in restaurant.secondary_links:
        actions.append(
            f"<a class='button secondary' href='{html_escape(url)}' target='_blank' rel='noopener'>{html_escape(label)}</a>"
        )
    action_block = "".join(actions) if actions else "<p class='muted'>沒有可用的外部連結</p>"

    hero = (
        f"<img class='hero' src='{html_escape(restaurant.image_url)}' alt='{html_escape(restaurant.name)}'>"
        if restaurant.image_url
        else "<div class='hero placeholder'>沒有提供圖片</div>"
    )

    price_block = f"<span class='pill'>{html_escape(restaurant.price)}</span>" if restaurant.price else ""

    value_highlights: list[str] = []
    if restaurant.rating:
        value_highlights.append(
            f"<li><strong>{html_escape(restaurant.rating)} ★</strong> · {html_escape(restaurant.review_count or '近期評論')} 則真實口碑，適合放大曝光。</li>"
        )
    if restaurant.category:
        value_highlights.append(
            f"<li>依照「{html_escape(restaurant.category)}」標籤，鎖定對味客群，減少無效廣告浪費。</li>"
        )
    if restaurant.services:
        joined_services = "、".join(html_escape(service) for service in restaurant.services[:3])
        value_highlights.append(
            f"<li>用「{joined_services}」等服務情境，客製化導購腳本，提升轉單率。</li>"
        )
    if restaurant.price:
        value_highlights.append(
            f"<li>以客單 {html_escape(restaurant.price)} 為目標，推薦適合的再行銷與回訪提醒節奏。</li>"
        )

    if not value_highlights:
        value_highlights.append("<li>專人協助設定行銷流程，快速上線導流與留客工具。</li>")

    growth_section = f"""
      <section class='promo'>
        <div class='promo-card'>
          <div class='promo-text'>
            <p class='eyebrow'>合作提案</p>
            <h2>為 {html_escape(restaurant.name)} 打造的營運成長方案</h2>
            <p class='muted'>把門市資訊轉換成吸引人的故事：用評論、服務型態與價格帶，為你量身設計廣告素材、回訪訊息與會員培育流程。</p>
            <ul class='promo-list'>{''.join(value_highlights)}</ul>
            <div class='promo-actions'>
              <a class='button primary' href='mailto:hello@example.com?subject={html_escape(restaurant.name)}%20合作諮詢'>預約 30 分鐘諮詢</a>
              <a class='button secondary' href='{html_escape(restaurant.map_url or "../../index.html")}' target='_blank' rel='noopener'>查看門市定位</a>
            </div>
          </div>
          <div class='promo-panel'>
            <div class='stat'>
              <div class='stat-label'>招牌亮點</div>
              <div class='stat-value'>{html_escape(restaurant.category or "人氣餐廳")}</div>
              <p class='stat-note'>我們會根據熱門品項與客群關鍵字，產出投放文案與著陸頁 A/B 測試。</p>
            </div>
            <div class='stat'>
              <div class='stat-label'>口碑力</div>
              <div class='stat-value'>{html_escape(restaurant.review_count or "新開店")}</div>
              <p class='stat-note'>將評論轉成社群推薦語，並建立「到店後」滿意度追蹤流程。</p>
            </div>
            <div class='stat'>
              <div class='stat-label'>營運服務</div>
              <div class='stat-value'>{html_escape('、'.join(restaurant.services) or '彈性體驗')}</div>
              <p class='stat-note'>針對營業時段與服務模式自動提醒，減少空檔、放大尖峰營收。</p>
            </div>
          </div>
        </div>
      </section>
    """

    return f"""
    <main class='detail'>
      <a class='back-link' href='../../index.html'>← 回到餐廳列表</a>
      <header>
        <h1>{html_escape(restaurant.name)}</h1>
        <div class='tags'>
          <span class='pill'>{html_escape(restaurant.category)}</span>
          {price_block}
        </div>
        <div class='summary'>
          <div class='rating'>⭐ {html_escape(restaurant.rating)} <span class='reviews'>({html_escape(restaurant.review_count)})</span></div>
          <div class='status'>{html_escape(restaurant.status)} {html_escape(restaurant.hours)}</div>
          <div class='address'>{html_escape(restaurant.address)}</div>
        </div>
      </header>
      {hero}
      {growth_section}
      <section>
        <h2>服務</h2>
        {services_block}
      </section>
      <section>
        <h2>連結</h2>
        <div class='actions'>
          {action_block}
        </div>
      </section>
    </main>
    """


def build_page(body: str, title: str, depth: int = 0) -> str:
    prefix = "../" * depth
    return f"""<!doctype html>
<html lang='zh-Hant'>
  <head>
    <meta charset='utf-8'>
    <meta name='viewport' content='width=device-width, initial-scale=1'>
    <title>{html_escape(title)}</title>
    <link rel='stylesheet' href='{prefix}assets/style.css'>
  </head>
  <body>
    <div class='page'>{body}</div>
  </body>
</html>
"""


def write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def generate_site(restaurants: Iterable[Restaurant]) -> None:
    ASSETS_DIR.mkdir(parents=True, exist_ok=True)
    DOCS_DIR.mkdir(exist_ok=True)
    RESTAURANTS_DIR.mkdir(exist_ok=True)

    cards = [build_card(r) for r in restaurants]
    index_body = f"""
      <header class='hero-header'>
        <h1>餐廳清單</h1>
        <p>共有 {len(cards)} 間餐廳，每一間都有自己的獨立頁面。</p>
      </header>
      <section class='grid'>
        {''.join(cards)}
      </section>
    """
    index_page = build_page(index_body, "餐廳列表", depth=0)
    write_file(DOCS_DIR / "index.html", index_page)

    for restaurant in restaurants:
        detail_body = build_detail(restaurant)
        page = build_page(detail_body, restaurant.name, depth=2)
        write_file(RESTAURANTS_DIR / restaurant.slug / "index.html", page)

    copy_styles()


def copy_styles() -> None:
    stylesheet = ASSETS_DIR / "style.css"
    if stylesheet.exists():
        return

    stylesheet.write_text(
        """
:root {
  --bg: #f6f8fb;
  --card: #ffffff;
  --ink: #111827;
  --muted: #6b7280;
  --accent: #2563eb;
  --pill: #e5e7eb;
  --border: #e5e7eb;
  --shadow: 0 10px 40px rgba(17, 24, 39, 0.08);
  --radius: 16px;
  font-family: "Noto Sans TC", "Inter", system-ui, -apple-system, sans-serif;
}

* { box-sizing: border-box; }

body {
  margin: 0;
  padding: 0;
  background: var(--bg);
  color: var(--ink);
}

.page {
  max-width: 1200px;
  margin: 0 auto;
  padding: 24px 20px 64px;
}

h1, h2 {
  margin: 0 0 8px;
}

.hero-header {
  text-align: center;
  margin-bottom: 24px;
}

.hero-header p {
  margin: 0;
  color: var(--muted);
}

.grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 20px;
}

.card {
  background: var(--card);
  border-radius: var(--radius);
  overflow: hidden;
  box-shadow: var(--shadow);
  transition: transform 150ms ease, box-shadow 150ms ease;
}

.card:hover {
  transform: translateY(-4px);
  box-shadow: 0 16px 50px rgba(17, 24, 39, 0.12);
}

.card-link {
  color: inherit;
  text-decoration: none;
  display: block;
  height: 100%;
}

.card-image {
  height: 160px;
  background: var(--pill);
  display: flex;
  align-items: center;
  justify-content: center;
}

.card-image img, .hero {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.card-image.placeholder {
  color: var(--muted);
  font-size: 14px;
}

.card-body {
  padding: 16px 16px 20px;
}

.card-body h2 {
  font-size: 18px;
  margin-bottom: 8px;
}

.meta {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
  color: var(--muted);
  font-size: 14px;
}

.rating {
  font-weight: 600;
  color: #f59e0b;
}

.reviews {
  color: var(--muted);
  margin-left: 4px;
}

.category, .price, .pill {
  background: var(--pill);
  border-radius: 999px;
  padding: 4px 10px;
}

.status {
  color: var(--ink);
  margin: 8px 0 4px;
}

.address {
  color: var(--muted);
  font-size: 14px;
  margin: 0;
}

.detail header {
  margin-bottom: 12px;
}

.detail .summary {
  display: grid;
  gap: 6px;
  color: var(--muted);
}

.detail .hero {
  height: 340px;
  border-radius: var(--radius);
  box-shadow: var(--shadow);
  margin: 16px 0 24px;
}

.detail .hero.placeholder {
  background: var(--pill);
  color: var(--muted);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  height: 200px;
}

.services {
  list-style: none;
  padding: 0;
  margin: 0;
  display: grid;
  gap: 8px;
}

.services .bullet {
  color: var(--accent);
  margin-right: 6px;
}

.actions {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 10px 14px;
  border-radius: 10px;
  text-decoration: none;
  font-weight: 600;
  transition: transform 120ms ease, box-shadow 120ms ease;
}

.button.primary {
  background: var(--accent);
  color: white;
  box-shadow: 0 6px 16px rgba(37, 99, 235, 0.24);
}

.button.secondary {
  background: var(--card);
  border: 1px solid var(--border);
  color: var(--ink);
}

.button:hover {
  transform: translateY(-2px);
}

.muted {
  color: var(--muted);
}

.tags {
  display: flex;
  gap: 8px;
  margin-bottom: 8px;
}

.pill {
  color: var(--ink);
  display: inline-flex;
  align-items: center;
}

.back-link {
  color: var(--accent);
  text-decoration: none;
  font-weight: 600;
  display: inline-block;
  margin-bottom: 12px;
}

@media (max-width: 640px) {
  .grid {
    grid-template-columns: 1fr;
  }

  .detail .hero {
    height: 220px;
  }
}
"""
        + "\n",
        encoding="utf-8",
    )


def main() -> None:
    restaurants = read_restaurants()
    generate_site(restaurants)
    print(f"Generated {len(restaurants)} 餐廳的靜態網站到 {DOCS_DIR}")


if __name__ == "__main__":
    main()

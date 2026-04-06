"""
Поиск по 2GIS без API-ключа: HTML-страница поиска (SSR) + разбор ссылок /firm/…
Методичка допускает Playwright; для стабильности текущего сайта достаточно httpx.
"""

from __future__ import annotations

import re
from typing import Any
from urllib.parse import quote, urljoin

import httpx
from bs4 import BeautifulSoup

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:128.0) "
    "Gecko/20100101 Firefox/128.0"
)


def city_slug(location: str) -> str:
    loc = (location or "").strip().lower()
    if "астан" in loc or "нур-султан" in loc:
        return "astana"
    if "шымкент" in loc:
        return "shymkent"
    return "almaty"


def _guess_address(text: str) -> str:
    if not text:
        return ""
    m = re.search(
        r"([А-Яа-яЁёA-Za-z0-9№#.,\s\-–—]+"
        r"(?:улица|ул\.|проспект|пр-т|микрорайон|мкр|ЖК|ТРЦ|блок)"
        r"[А-Яа-яЁёA-Za-z0-9№#.,\s\-–—]{4,180})",
        text,
    )
    if m:
        return re.sub(r"\s+", " ", m.group(1)).strip()[:220]
    return ""


def _guess_rating(text: str) -> float:
    m = re.search(r"(?<![0-9])([0-4]),([0-9])(?![0-9])", text)
    if m:
        try:
            return float(f"{m.group(1)}.{m.group(2)}")
        except ValueError:
            pass
    m2 = re.search(r"\b([0-5]\.[0-9])\b", text)
    if m2:
        try:
            return float(m2.group(1))
        except ValueError:
            pass
    return 0.0


def _guess_price(text: str) -> str:
    m = re.search(r"Чек\s*(\d[\d\s]*)\s*тнг", text, re.I)
    if m:
        return f"~{m.group(1).replace(' ', '')} ₸"
    return ""


def search_restaurants_http(query: str, location: str = "Алматы") -> list[dict[str, Any]]:
    slug = city_slug(location)
    q = (query or "").strip() or "ресторан кафе"
    loc = (location or "").strip()
    if loc and slug == "almaty" and "алмат" not in q.lower():
        q = f"{q} {loc}"

    path = quote(q, safe="")
    url = f"https://2gis.kz/{slug}/search/{path}"
    headers = {
        "User-Agent": UA,
        "Accept": "text/html,application/xhtml+xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "ru-RU,ru;q=0.9,kk;q=0.8",
    }
    with httpx.Client(timeout=45.0, headers=headers, follow_redirects=True) as client:
        r = client.get(url)
        r.raise_for_status()
        html = r.text

    soup = BeautifulSoup(html, "html.parser")
    href_re = re.compile(rf"/{re.escape(slug)}/firm/\d+")
    links = soup.find_all("a", href=href_re)
    seen: set[str] = set()
    out: list[dict[str, Any]] = []

    for a in links:
        href = (a.get("href") or "").strip()
        m = re.search(r"/firm/(\d+)", href)
        if not m:
            continue
        fid = m.group(1)
        if fid in seen:
            continue
        seen.add(fid)

        name = " ".join(a.get_text(separator=" ", strip=True).split())
        if len(name) < 2 or name.lower() in ("подробнее", "отзывы", "маршрут"):
            continue

        card = a.parent
        blob = ""
        for _ in range(14):
            if card is None:
                break
            blob = card.get_text(separator=" ", strip=True)
            if len(blob) > 80:
                break
            card = card.parent

        addr = _guess_address(blob)
        rating = _guess_rating(blob)
        price = _guess_price(blob)
        full_url = urljoin("https://2gis.kz", href)

        out.append(
            {
                "name": name[:200],
                "address": addr or "—",
                "rating": rating,
                "price_range": price or "—",
                "cuisine": q[:80],
                "working_hours": "—",
                "phone": "—",
                "url_2gis": full_url,
            }
        )
        if len(out) >= 10:
            break

    return out

"""
Поиск по 2GIS:
- при TWO_GIS_API_KEY — Places API (catalog.api.2gis.com);
- без ключа — парсинг HTML поиска (httpx), опционально Playwright (см. TWO_GIS_USE_PLAYWRIGHT).
"""

from __future__ import annotations

import os
from typing import Any

import httpx

from mcp_servers.lib.twogis_scrape import city_slug

# Центр Алматы (lon, lat) — ограничение поиска по городу
ALMATY_LON = 76.9286
ALMATY_LAT = 43.2567

DEFAULT_CATALOG = "https://catalog.api.2gis.com/3.0/items"


def _extract_phone(item: dict[str, Any]) -> str:
    groups = item.get("contact_groups") or []
    for g in groups:
        for ph in g.get("phones") or []:
            num = ph.get("formatted") or ph.get("number")
            if num:
                return str(num)
    return ""


def _extract_schedule(item: dict[str, Any]) -> str:
    sch = item.get("schedule") or item.get("schedule_comment")
    if isinstance(sch, str):
        return sch
    if isinstance(sch, dict):
        return sch.get("comment") or sch.get("description") or ""
    return ""


def _extract_rating(item: dict[str, Any]) -> float:
    r = item.get("reviews") or {}
    if isinstance(r, dict):
        g = r.get("general_rating")
        if g is not None:
            try:
                return float(g)
            except (TypeError, ValueError):
                pass
    return 0.0


def _extract_price_hint(item: dict[str, Any]) -> str:
    attrs = item.get("attributes") or item.get("attribute_groups") or []
    if isinstance(attrs, list):
        for a in attrs:
            if isinstance(a, dict):
                t = (a.get("tag") or "").lower()
                if "price" in t or "check" in t or "средний" in str(a):
                    return str(a.get("name") or a.get("value") or "")
    return ""


def search_restaurants(query: str, location: str = "Алматы") -> list[dict[str, Any]]:
    """
    Поиск заведений (рестораны, кафе и т.д.) по запросу.
    Возвращает список словарей с полями ТЗ: name, address, rating, price_range, cuisine, working_hours, phone.
    """
    key = (os.getenv("TWO_GIS_API_KEY") or os.getenv("2GIS_API_KEY") or "").strip()
    if not key:
        return _search_without_api_key(query, location)

    base = os.getenv("TWO_GIS_CATALOG_URL", DEFAULT_CATALOG).rstrip("/")
    q = query.strip()
    if not q:
        q = "ресторан кафе"
    # Явно привязываем к городу в тексте запроса
    loc = location.strip() or "Алматы"
    if loc.lower() not in q.lower():
        q = f"{q} {loc}"
    geo_slug = city_slug(loc)

    params: dict[str, Any] = {
        "key": key,
        "q": q,
        "page_size": 10,
        "location": f"{ALMATY_LON},{ALMATY_LAT}",
        "radius": 25000,
        "type": "branch",
        "fields": "items.schedule,items.contact_groups,items.reviews,items.address,items.attribute_groups",
    }

    with httpx.Client(timeout=30.0) as client:
        r = client.get(base, params=params)
        r.raise_for_status()
        data = r.json()

    meta = data.get("meta") or {}
    if meta.get("code") not in (200, None):
        raise RuntimeError(f"2GIS API error: {data}")

    items = (data.get("result") or {}).get("items") or []
    out: list[dict[str, Any]] = []
    for it in items:
        if not isinstance(it, dict):
            continue
        addr = it.get("address_name") or it.get("full_name") or ""
        name = it.get("name") or ""
        if it.get("type") == "branch" or name:
            fid = str(it.get("id") or "").strip()
            row: dict[str, Any] = {
                "name": name,
                "address": addr,
                "rating": _extract_rating(it),
                "price_range": _extract_price_hint(it) or "—",
                "cuisine": q[:80],
                "working_hours": _extract_schedule(it) or "—",
                "phone": _extract_phone(it) or "—",
            }
            if fid:
                row["url_2gis"] = f"https://2gis.kz/{geo_slug}/firm/{fid}"
            out.append(row)
        if len(out) >= 10:
            break
    return out


def _search_without_api_key(query: str, location: str) -> list[dict[str, Any]]:
    """Без ключа API: HTML-скрапинг; при TWO_GIS_USE_PLAYWRIGHT=1 — только Playwright."""
    if os.getenv("TWO_GIS_USE_PLAYWRIGHT", "").strip() == "1":
        from mcp_servers.lib.twogis_playwright import search_restaurants_playwright

        return search_restaurants_playwright(query, location)

    from mcp_servers.lib.twogis_scrape import search_restaurants_http

    rows = search_restaurants_http(query, location)
    if len(rows) >= 2:
        return rows

    try:
        from mcp_servers.lib.twogis_playwright import search_restaurants_playwright

        return search_restaurants_playwright(query, location)
    except Exception:
        return rows

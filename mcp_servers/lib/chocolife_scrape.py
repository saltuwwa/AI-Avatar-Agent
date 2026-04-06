"""
Акции Chocolife: JSON API (тот же бэкенд, что у сайта chocolife.me).
Категория «Еда» (рестораны и т.п.) — category_id=4, Алматы — town_id=1.
"""

from __future__ import annotations

from typing import Any

import httpx

API_DEALS = "https://api-proxy.choco.kz/mobileapi/v5_5/deals"

# Алматы
TOWN_ALMATY = 1
# Верхнеуровневая категория «Еда» в мобильном API (рестораны, кафе и т.д.)
CATEGORY_FOOD = 4

_HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; AI-Avatar-Agent/1.0; +local)",
    "Accept": "application/json, text/plain, */*",
    "Referer": "https://chocolife.me/restorany-kafe-i-bary/",
    "Origin": "https://chocolife.me",
}


def _town_id(city: str) -> int:
    c = (city or "").strip().lower()
    if "алмат" in c or not c:
        return TOWN_ALMATY
    return TOWN_ALMATY


def search_deals(category: str = "рестораны", city: str = "Алматы") -> list[dict[str, Any]]:
    """
    Список акций: заголовок, цены, скидка, ссылка, адрес заведения.
    category/city влияют на town_id; для ресторанного сценария используем CATEGORY_FOOD.
    """
    _ = category  # при необходимости можно маппить на другие category_id
    params: dict[str, Any] = {
        "town_id": _town_id(city),
        "page": 1,
        "category_id": CATEGORY_FOOD,
    }
    with httpx.Client(timeout=30.0, headers=_HEADERS, follow_redirects=True) as client:
        r = client.get(API_DEALS, params=params)
        r.raise_for_status()
        payload = r.json()

    if (payload.get("status") or "") != "success":
        raise RuntimeError(f"Chocolife API: {payload}")

    items = (payload.get("data") or {}).get("items") or []
    out: list[dict[str, Any]] = []
    for it in items:
        if not isinstance(it, dict):
            continue
        places = it.get("places") or []
        addr = ""
        if places and isinstance(places[0], dict):
            addr = str(places[0].get("address") or "")
        fp = int(it.get("full_price") or 0)
        pr = int(it.get("price") or 0)
        disc = int(it.get("discount") or 0)
        rest_name = str(it.get("title_short") or "").strip()[:160]
        out.append(
            {
                "title": str(it.get("title") or "")[:300],
                "restaurant_name": rest_name,
                "original_price": fp,
                "discount_price": pr,
                "discount_percent": disc,
                "description": str(it.get("what_discount") or it.get("title") or "")[:500],
                "url": str(it.get("link") or ""),
                "address": addr,
            }
        )
        if len(out) >= 15:
            break
    return out

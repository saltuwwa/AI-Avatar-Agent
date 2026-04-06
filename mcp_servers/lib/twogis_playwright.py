"""
Опционально: поиск через браузер (если 2GIS отдаёт пустую разметку без JS или по запросу).
Требует: pip install playwright && playwright install chromium
"""

from __future__ import annotations

from typing import Any

from mcp_servers.lib.twogis_scrape import _guess_address, _guess_price, _guess_rating, city_slug


def search_restaurants_playwright(query: str, location: str = "Алматы") -> list[dict[str, Any]]:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as e:
        raise RuntimeError(
            "Установите Playwright: pip install playwright && playwright install chromium"
        ) from e

    from urllib.parse import quote

    slug = city_slug(location)
    q = (query or "").strip() or "ресторан кафе"
    loc = (location or "").strip()
    if loc and slug == "almaty" and "алмат" not in q.lower():
        q = f"{q} {loc}"
    url = f"https://2gis.kz/{slug}/search/{quote(q, safe='')}"

    rows: list = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        try:
            page = browser.new_page(
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                )
            )
            page.goto(url, wait_until="domcontentloaded", timeout=60000)
            page.wait_for_selector(f'a[href*="/{slug}/firm/"]', timeout=45000)

            rows = page.evaluate(
                """(slug) => {
                    const out = [];
                    const seen = new Set();
                    for (const a of document.querySelectorAll('a[href*="/firm/"]')) {
                        const href = a.getAttribute('href') || '';
                        if (!href.includes('/' + slug + '/firm/')) continue;
                        const m = href.match(/\\/firm\\/(\\d+)/);
                        if (!m) continue;
                        const id = m[1];
                        if (seen.has(id)) continue;
                        seen.add(id);
                        const name = (a.innerText || '').trim().split(/\\s*\\n\\s*/)[0];
                        if (name.length < 2) continue;
                        let el = a.parentElement;
                        let blob = '';
                        for (let i = 0; i < 14 && el; i++) {
                            blob = el.innerText || '';
                            if (blob.length > 80) break;
                            el = el.parentElement;
                        }
                        out.push({ name, href, blob: blob.slice(0, 1500) });
                        if (out.length >= 10) break;
                    }
                    return out;
                }""",
                slug,
            )
        finally:
            browser.close()

    out: list[dict[str, Any]] = []
    for row in rows:
        blob = row.get("blob") or ""
        href = row.get("href") or ""
        full = href if href.startswith("http") else f"https://2gis.kz{href}"
        out.append(
            {
                "name": str(row.get("name", ""))[:200],
                "address": _guess_address(blob) or "—",
                "rating": _guess_rating(blob),
                "price_range": _guess_price(blob) or "—",
                "cuisine": q[:80],
                "working_hours": "—",
                "phone": "—",
                "url_2gis": full,
            }
        )
    return out

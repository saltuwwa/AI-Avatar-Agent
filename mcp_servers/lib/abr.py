"""Бонус ТЗ: сеть ABR — тот же канал поиска, что и 2GIS (API или скрапинг)."""

from __future__ import annotations

from typing import Any

from .twogis_api import search_restaurants


def search_abr_restaurants(query: str = "") -> list[dict[str, Any]]:
    """
    Ищет заведения бренда ABR / ABR Group в Алматы (запрос «ABR …» к search_restaurants).
    Уточнения в query: стейкхаус, завтрак и т.д.
    """
    q = (query or "").strip()
    full = f"ABR {q}".strip() if q else "ABR ресторан"
    return search_restaurants(full, "Алматы")

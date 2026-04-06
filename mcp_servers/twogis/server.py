#!/usr/bin/env python3
"""MCP-сервер 2GIS (stdio): поиск ресторанов (API 2GIS и/или 2gis.kz без ключа)."""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from mcp_servers.bootstrap import load_project_env

load_project_env()

from mcp.server.fastmcp import FastMCP

from mcp_servers.lib.twogis_api import search_restaurants as _search_restaurants
from mcp_servers.mcp_stdio import ensure_stdin_client

mcp = FastMCP("2gis")


@mcp.tool()
def search_restaurants(query: str, location: str = "Алматы") -> list[dict]:
    """
    Найти рестораны, кафе и бары. С ключом TWO_GIS_API_KEY — официальный API; без ключа — сайт 2gis.kz.
    Поля: name, address, rating, price_range, cuisine, working_hours, phone, при наличии url_2gis.
    Примеры запросов: пицца, итальянское кафе, Абая улица.
    """
    return _search_restaurants(query, location)


def main() -> None:
    ensure_stdin_client()
    mcp.run()


if __name__ == "__main__":
    main()

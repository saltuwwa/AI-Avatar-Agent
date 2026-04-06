#!/usr/bin/env python3
"""MCP-сервер Chocolife (stdio): акции и скидки на рестораны chocolife.me."""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from mcp_servers.bootstrap import load_project_env

load_project_env()

from mcp.server.fastmcp import FastMCP

from mcp_servers.lib.chocolife_scrape import search_deals as _search_deals
from mcp_servers.mcp_stdio import ensure_stdin_client

mcp = FastMCP("chocolife")


@mcp.tool()
def search_deals(category: str = "рестораны", city: str = "Алматы") -> list[dict]:
    """
    Акции и скидки на заведения (категория «Еда» на chocolife.me, JSON API).
    Возвращает: title, restaurant_name, цены, скидка %, url, address.
    city: сейчас town_id=1 (Алматы).
    """
    return _search_deals(category=category, city=city)


def main() -> None:
    ensure_stdin_client()
    mcp.run()


if __name__ == "__main__":
    main()

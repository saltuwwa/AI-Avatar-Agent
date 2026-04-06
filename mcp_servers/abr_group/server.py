#!/usr/bin/env python3
"""MCP-сервер ABR Group (бонус по ТЗ): точки сети ABR в Алматы через 2GIS."""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from mcp_servers.bootstrap import load_project_env

load_project_env()

from mcp.server.fastmcp import FastMCP

from mcp_servers.lib.abr import search_abr_restaurants as _search_abr
from mcp_servers.mcp_stdio import ensure_stdin_client

mcp = FastMCP("abr_group")


@mcp.tool()
def search_abr_restaurants(query: str = "") -> list[dict]:
    """
    Найти рестораны сети ABR / ABR Group в Алматы.
    В query можно уточнить: стейкхаус, завтрак, адрес и т.д.
    """
    return _search_abr(query)


def main() -> None:
    ensure_stdin_client()
    mcp.run()


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Проверка логики MCP без Cursor: те же функции, что вызывают server.py.

Запуск из корня проекта:
  python mcp_servers/demo_tools.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv

load_dotenv(ROOT / ".env")

from mcp_servers.lib.abr import search_abr_restaurants
from mcp_servers.lib.chocolife_scrape import search_deals
from mcp_servers.lib.twogis_api import search_restaurants


def main() -> None:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

    print("=== 2GIS: search_restaurants('пицца', 'Алматы') ===")
    r = search_restaurants("пицца", "Алматы")
    print(json.dumps(r[:3], ensure_ascii=False, indent=2))
    print(f"(всего: {len(r)})\n")

    print("=== Chocolife: search_deals() ===")
    d = search_deals()
    print(json.dumps(d[:2], ensure_ascii=False, indent=2))
    print(f"(всего: {len(d)})\n")

    print("=== ABR: search_abr_restaurants('') ===")
    a = search_abr_restaurants("")
    print(json.dumps(a[:3], ensure_ascii=False, indent=2))
    print(f"(всего: {len(a)})\n")

    print("Готово. Если пусто или ошибка — сеть, блокировка или .env.")


if __name__ == "__main__":
    main()

"""
MCP по stdio ожидает JSON-RPC от клиента (Cursor и т.д.), а не ввод с клавиатуры.
Интерактивный терминал (TTY) даёт лишние переводы строк → «Invalid JSON: EOF».
"""

from __future__ import annotations

import os
import sys


def ensure_stdin_client() -> None:
    """Выход с подсказкой, если запускают «вручную» в консоли без MCP-клиента."""
    if os.environ.get("MCP_FORCE_STDIO") == "1":
        return
    if sys.stdin.isatty():
        print(
            "Это MCP-сервер: он читает JSON-RPC со stdin (клиент IDE передаёт pipe).\n"
            "Не запускайте его просто так в терминале и не жмите Enter — будет ошибка парсинга JSON.\n"
            "Подключите сервер в настройках MCP Cursor или задайте MCP_FORCE_STDIO=1 для отладки.",
            file=sys.stderr,
        )
        raise SystemExit(2)

"""Ограничение длины диалога для экономии токенов."""

from __future__ import annotations

from typing import Any

# Пары user+assistant (текстовые реплики без повторной отправки старых картинок)
MAX_HISTORY_PAIRS = 12


def trim_history(history: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Оставить последние MAX_HISTORY_PAIRS * 2 сообщений (user/assistant)."""
    if not history:
        return []
    cap = MAX_HISTORY_PAIRS * 2
    if len(history) <= cap:
        return list(history)
    return list(history[-cap:])

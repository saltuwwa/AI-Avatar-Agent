"""Текст для TTS: убрать URL и служебную разметку, оставить читаемые названия и адреса."""

from __future__ import annotations

import re

# Подписи ссылок без смысла для озвучки — выкидываем целиком
_GENERIC_LINK_LABELS = frozenset(
    {
        "ссылка на заведение",
        "ссылка",
        "подробнее",
        "link",
        "here",
        "click here",
    }
)


def sanitize_for_speech(text: str) -> str:
    """
    - [подпись](url) → подпись (или пусто, если подпись — служебная);
    - голые http(s) URL удаляются;
    - **жирный** и *курсив* — убираются маркеры;
    - заголовки markdown и маркеры списков — смягчаются для связного TTS.
    """
    s = (text or "").strip()
    if not s:
        return ""

    s = re.sub(r"(?m)^#{1,6}\s*", "", s)
    s = re.sub(r"(?m)^\s*[-*•]\s+", "", s)
    s = re.sub(r"(?m)^\s*\d{1,2}\.\s+", "", s)

    def _replace_md_link(m: re.Match[str]) -> str:
        label = m.group(1).strip()
        low = label.lower()
        if low in _GENERIC_LINK_LABELS:
            return ""
        return label

    s = re.sub(r"\[([^\]]*)\]\([^)]*\)", _replace_md_link, s)
    s = re.sub(r"https?://[^\s\)\]<>\"']+", "", s)
    s = re.sub(r"\*\*([^*]+)\*\*", r"\1", s)
    s = re.sub(r"\*([^*]+)\*", r"\1", s)
    s = re.sub(r"[ \t]+", " ", s)
    s = re.sub(r"\n{3,}", "\n\n", s)
    lines = [ln.strip() for ln in s.splitlines()]
    s = "\n".join(ln for ln in lines if ln)
    s = s.strip()
    if s:
        s = re.sub(r"\n+", ". ", s)
        s = re.sub(r"\s*\.+\s*", ". ", s)
        s = re.sub(r"\.\s*\.", ".", s)
        s = re.sub(r"\s+", " ", s).strip()
    return s

"""
Custom skill: анализ фото ресторана (интерьер, вывеска, зал, блюдо) через vision-модель.
"""

from __future__ import annotations

import base64
import json
from pathlib import Path
from typing import Any

import httpx
from openai import OpenAI

import config

CRITIC_PROMPT = """Ты ресторанный критик. По изображению определи:

1) scene_type: одно из "restaurant_interior" | "exterior_sign" | "dish" | "menu" | "other"
2) level: для зала/вывески — одно из "fast_food" | "casual" | "mid-range" | "fine_dining".
   Если на фото в основном блюдо или меню без явного зала — поставь "casual" или "mid-range" по стилю подачи/интерьера на заднем плане; если совсем не ресторан — "casual".
3) status: краткий тип заведения или сцены на русском: семейный, романтический, бизнес-ланч, молодёжный, фастфуд, премиум, уличная еда, кофейня и т.п.
4) description: 2–4 предложения: атмосфера, целевая аудитория, что видно (интерьер / блюдо / вывеска).
5) confidence: число от 0 до 1 — насколько ты уверен.

Ответь ТОЛЬКО валидным JSON без markdown:
{"scene_type":"...","level":"...","status":"...","description":"...","confidence":0.0}
"""


def path_to_data_url(path: Path) -> str:
    path = path.resolve()
    if not path.is_file():
        raise FileNotFoundError(str(path))
    suf = path.suffix.lower()
    mime = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".webp": "image/webp",
        ".gif": "image/gif",
    }.get(suf, "image/jpeg")
    b64 = base64.standard_b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{b64}"


def normalize_image_url(image_url: str) -> str:
    u = (image_url or "").strip()
    if not u:
        return ""
    if u.startswith("data:") or u.startswith("https://") or u.startswith("http://"):
        return u
    p = Path(u)
    if p.is_file():
        return path_to_data_url(p)
    return u


def analyze_restaurant_photo(image_url: str) -> dict[str, Any]:
    """
    Анализирует фото ресторана и возвращает оценку заведения.
    image_url — публичный URL, data:image/...;base64,... или путь к локальному файлу.
    """
    if not config.OPENAI_API_KEY:
        return {
            "error": "Нет OPENAI_API_KEY",
            "level": "unknown",
            "status": "—",
            "description": "—",
            "confidence": 0.0,
        }

    url = normalize_image_url(image_url)
    if not url:
        return {
            "error": "Пустой image_url",
            "level": "unknown",
            "status": "—",
            "description": "—",
            "confidence": 0.0,
        }

    # Публичный URL можно передать напрямую; для надёжности при сбое — скачать в data URL
    if url.startswith("http://") or url.startswith("https://"):
        try:
            with httpx.Client(timeout=20.0, follow_redirects=True) as client:
                r = client.get(url, headers={"User-Agent": "Mozilla/5.0 (compatible; DastarkanAI/1.0)"})
                r.raise_for_status()
            ct = r.headers.get("content-type", "image/jpeg").split(";")[0].strip()
            if not ct.startswith("image/"):
                ct = "image/jpeg"
            b64 = base64.standard_b64encode(r.content).decode("ascii")
            url = f"data:{ct};base64,{b64}"
        except Exception:
            pass  # оставляем исходный URL для OpenAI

    client = OpenAI(api_key=config.OPENAI_API_KEY)
    model = config.OPENAI_VISION_MODEL or config.OPENAI_MODEL

    user_block = {
        "role": "user",
        "content": [
            {"type": "text", "text": CRITIC_PROMPT},
            {"type": "image_url", "image_url": {"url": url, "detail": "low"}},
        ],
    }
    try:
        try:
            resp = client.chat.completions.create(
                model=model,
                messages=[user_block],
                response_format={"type": "json_object"},
                max_tokens=500,
            )
        except Exception:
            resp = client.chat.completions.create(
                model=model,
                messages=[user_block],
                max_tokens=500,
            )
        raw = (resp.choices[0].message.content or "").strip()
        raw = raw.removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        data = json.loads(raw)
    except Exception as e:
        return {
            "error": str(e),
            "level": "unknown",
            "status": "—",
            "description": "Не удалось проанализировать изображение.",
            "confidence": 0.0,
        }

    level_raw = str(data.get("level", "unknown")).lower().strip()
    status = str(data.get("status", "—"))
    description = str(data.get("description", "—"))
    try:
        confidence = float(data.get("confidence", 0.7))
    except (TypeError, ValueError):
        confidence = 0.5
    confidence = max(0.0, min(1.0, confidence))
    scene_type = str(data.get("scene_type", "other"))

    lr = level_raw.replace(" ", "_").replace("-", "_")
    canon = {
        "fastfood": "fast_food",
        "fast_food": "fast_food",
        "casual": "casual",
        "midrange": "mid-range",
        "mid_range": "mid-range",
        "fine_dining": "fine_dining",
        "finedining": "fine_dining",
    }
    if lr in canon:
        level_norm = canon[lr]
    elif "mid" in lr:
        level_norm = "mid-range"
    elif "fine" in lr or "премиум" in level_raw:
        level_norm = "fine_dining"
    elif "fast" in lr or "фаст" in level_raw:
        level_norm = "fast_food"
    elif scene_type in ("dish", "menu"):
        level_norm = "casual"
    else:
        level_norm = "casual"

    return {
        "level": level_norm,
        "status": status,
        "description": description,
        "confidence": round(confidence, 2),
        "scene_type": scene_type,
    }

"""
Видео с аватаром: fal.ai Creatify Aurora (fal-ai/creatify/aurora).
Нужны image_url + audio_url (после TTS), см. https://fal.ai/models/fal-ai/creatify/aurora
"""

from __future__ import annotations

import os
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import fal_client

import config


def _sample_to_url(path: Path) -> str:
    path = path.resolve()
    if not path.is_file():
        raise FileNotFoundError(str(path))
    return fal_client.upload_file(path)


def _extract_video_url(result: dict) -> str:
    if not isinstance(result, dict):
        result = dict(result) if hasattr(result, "keys") else {}
    inner = result.get("data")
    if isinstance(inner, dict):
        result = inner
    v = result.get("video") or result.get("output")
    if isinstance(v, dict):
        v = v.get("url")
    if isinstance(v, str) and v.startswith("http"):
        return v
    # fallback: search nested
    import json

    blob = json.dumps(result, default=str)
    if '"url"' in blob:
        for key in ("video", "output", "result"):
            block = result.get(key)
            if isinstance(block, dict) and block.get("url"):
                return str(block["url"])
    raise RuntimeError(f"Не найден URL видео в ответе fal: {result!r}")


def generate_avatar_video(
    image_path: Path,
    audio_path: Path,
    prompt: str | None = None,
    *,
    out_path: Path | None = None,
) -> Path:
    """
    Загружает локальные файлы на fal, вызывает Creatify Aurora, сохраняет MP4.
    """
    if not config.FAL_KEY:
        raise RuntimeError("Задайте FAL_KEY в .env.")
    os.environ.setdefault("FAL_KEY", config.FAL_KEY)

    image_url = _sample_to_url(image_path)
    audio_url = _sample_to_url(audio_path)

    arguments: dict = {
        "image_url": image_url,
        "audio_url": audio_url,
        "prompt": prompt or config.CREATIFY_PROMPT,
    }
    res = (os.getenv("CREATIFY_RESOLUTION") or "720p").strip()
    if res:
        arguments["resolution"] = res

    result = fal_client.subscribe(config.CREATIFY_MODEL, arguments=arguments)

    if not isinstance(result, dict):
        result = dict(result) if hasattr(result, "keys") else {}
    inner = result.get("data")
    if isinstance(inner, dict):
        result = inner

    url = _extract_video_url(result)
    out = out_path or (config.AVATAR_DIR / "last_avatar.mp4")
    out.parent.mkdir(parents=True, exist_ok=True)
    urllib.request.urlretrieve(url, out)
    return out

"""
Клонирование голоса через fal.ai MiniMax (как в ТЗ, project05.pdf).

Перед запуском: положите WAV ≥10 с в voice/ (имя задайте в .env, по умолчанию my_voice_sample.wav).
Установите FAL_KEY в .env.

  python voice/clone.py
"""

from __future__ import annotations

import argparse
import base64
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import fal_client

import config

# Если fal CDN upload даёт 403 (ключ, регион, тариф) — пробуем data: URL (ограничение по размеру запроса).
_MAX_BASE64_AUDIO_BYTES = 12 * 1024 * 1024


def _sample_to_audio_url(sample_path: Path) -> str:
    sample_path = sample_path.resolve()
    raw = sample_path.read_bytes()
    try:
        return fal_client.upload_file(sample_path)
    except Exception as e:
        msg = str(e)
        print(
            "Предупреждение: загрузка на fal CDN не удалась:\n ",
            msg,
            "\nПробуем передать WAV как data: URL (проверьте FAL_KEY на fal.ai → Dashboard → API Keys).",
            file=sys.stderr,
            sep="",
        )
        if len(raw) > _MAX_BASE64_AUDIO_BYTES:
            raise RuntimeError(
                f"Файл {len(raw)} B — слишком большой для data: URL. "
                "Сожмите WAV (например Audacity → экспорт mono 16 kHz) или исправьте доступ к fal storage (403)."
            ) from e
        b64 = base64.standard_b64encode(raw).decode("ascii")
        return f"data:audio/wav;base64,{b64}"


def clone_voice(
    sample_path: Path,
    *,
    preview_text: str | None = None,
) -> str:
    if not config.FAL_KEY:
        raise RuntimeError("Задайте FAL_KEY в .env (fal.ai).")
    os.environ.setdefault("FAL_KEY", config.FAL_KEY)

    sample_path = sample_path.resolve()
    if not sample_path.is_file():
        raise FileNotFoundError(
            f"Нет файла: {sample_path}\n"
            "Положите сэмпл в voice/ и проверьте VOICE_SAMPLE_FILENAME в .env."
        )

    audio_url = _sample_to_audio_url(sample_path)
    preview = preview_text if preview_text is not None else config.MINIMAX_PREVIEW_TEXT

    result = fal_client.subscribe(
        "fal-ai/minimax/voice-clone",
        arguments={
            "audio_url": audio_url,
            "text": preview,
        },
    )

    if not isinstance(result, dict):
        result = dict(result) if hasattr(result, "keys") else {}
    inner = result.get("data")
    if isinstance(inner, dict):
        result = inner

    voice_id = result.get("custom_voice_id") or result.get("voice_id")
    if not voice_id:
        raise RuntimeError(f"Неожиданный ответ voice-clone: {result!r}")

    config.VOICE_ID_FILE.parent.mkdir(parents=True, exist_ok=True)
    config.VOICE_ID_FILE.write_text(voice_id.strip(), encoding="utf-8")
    return voice_id


def main() -> None:
    p = argparse.ArgumentParser(description="MiniMax voice clone (fal.ai)")
    p.add_argument(
        "--sample",
        type=Path,
        default=None,
        help="Путь к WAV (по умолчанию из config / VOICE_SAMPLE_FILENAME)",
    )
    p.add_argument("--preview-text", type=str, default=None, help="Текст превью при клоне")
    args = p.parse_args()

    path = args.sample or config.VOICE_SAMPLE_PATH
    try:
        vid = clone_voice(path, preview_text=args.preview_text)
    except Exception as e:
        msg = str(e)
        if "Exhausted balance" in msg or "User is locked" in msg:
            print(
                "\nНа fal.ai закончился баланс — API отклоняет запросы.\n"
                "Пополните: https://fal.ai/dashboard/billing\n"
                "В методичке на проект заложено ~$10–20 (fal + OpenAI и т.д.).\n",
                file=sys.stderr,
            )
        print("Ошибка:", e, file=sys.stderr)
        raise SystemExit(1) from e

    print("custom_voice_id сохранён в", config.VOICE_ID_FILE)
    print("voice_id:", vid)
    print("Дальше: python voice/tts.py \"Ваш текст\"")


if __name__ == "__main__":
    main()

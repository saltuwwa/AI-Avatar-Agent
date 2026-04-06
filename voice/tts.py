"""
Озвучка клонированным голосом: fal.ai MiniMax speech-02-turbo / speech-02-hd.

Сначала выполните: python voice/clone.py

  python voice/tts.py "Сәлем, бүгін Алматыда тамақтануға ұсыныс беремін."
"""

from __future__ import annotations

import argparse
import os
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import fal_client

import config

from agent.speech_text import sanitize_for_speech


def load_voice_id() -> str:
    if not config.VOICE_ID_FILE.is_file():
        raise FileNotFoundError(
            f"Нет {config.VOICE_ID_FILE}. Сначала: python voice/clone.py"
        )
    return config.VOICE_ID_FILE.read_text(encoding="utf-8").strip()


def synthesize(
    text: str,
    *,
    voice_id: str | None = None,
    out_path: Path | None = None,
    model: str | None = None,
    language_boost: str | None = None,
) -> Path:
    if not config.FAL_KEY:
        raise RuntimeError("Задайте FAL_KEY в .env.")
    os.environ.setdefault("FAL_KEY", config.FAL_KEY)

    vid = voice_id or load_voice_id()
    model_id = model or config.MINIMAX_TTS_MODEL
    out = out_path or (config.VOICE_DIR / "last_tts.wav")

    text = sanitize_for_speech(text)
    if not text:
        raise ValueError("Пустой текст после подготовки к озвучке")

    speed = max(0.5, min(2.0, float(config.MINIMAX_TTS_SPEED)))
    arguments = {
        "text": text,
        "voice_setting": {
            "voice_id": vid,
            "speed": speed,
        },
        "language_boost": language_boost or config.MINIMAX_LANGUAGE_BOOST,
        "output_format": "url",
    }

    result = fal_client.subscribe(model_id, arguments=arguments)

    if not isinstance(result, dict):
        result = dict(result) if hasattr(result, "keys") else {}
    inner = result.get("data")
    if isinstance(inner, dict):
        result = inner

    audio = result.get("audio") or {}
    url = audio.get("url") if isinstance(audio, dict) else None
    if not url:
        raise RuntimeError(f"Нет audio.url в ответе: {result!r}")

    out.parent.mkdir(parents=True, exist_ok=True)
    urllib.request.urlretrieve(url, out)
    return out


def main() -> None:
    p = argparse.ArgumentParser(description="MiniMax TTS с клонированным голосом")
    p.add_argument("text", nargs="?", default="", help="Текст для озвучки")
    p.add_argument("-o", "--output", type=Path, default=None, help="Куда сохранить WAV")
    args = p.parse_args()

    t = args.text.strip()
    if not t:
        print("Укажите текст: python voice/tts.py \"…\"", file=sys.stderr)
        raise SystemExit(1)

    try:
        path = synthesize(t, out_path=args.output)
    except Exception as e:
        msg = str(e)
        if "Exhausted balance" in msg or "User is locked" in msg:
            print(
                "\nНа fal.ai закончился баланс: https://fal.ai/dashboard/billing\n",
                file=sys.stderr,
            )
        print("Ошибка:", e, file=sys.stderr)
        raise SystemExit(1) from e

    print("Сохранено:", path.resolve())


if __name__ == "__main__":
    main()

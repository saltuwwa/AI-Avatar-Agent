"""Общая конфигурация проекта (пути, переменные окружения)."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / ".env")

FAL_KEY = os.getenv("FAL_KEY", "").strip()

VOICE_DIR = ROOT / "voice"
VOICE_ID_FILE = VOICE_DIR / ".minimax_voice_id"
VOICE_SAMPLE_PATH = VOICE_DIR / os.getenv("VOICE_SAMPLE_FILENAME", "my_voice_sample.wav")

MINIMAX_PREVIEW_TEXT = os.getenv(
    "MINIMAX_PREVIEW_TEXT",
    "Сәлем! Бұл менің дауысымның сынағы.",
)
MINIMAX_TTS_MODEL = os.getenv("MINIMAX_TTS_MODEL", "fal-ai/minimax/speech-02-turbo")
MINIMAX_LANGUAGE_BOOST = os.getenv("MINIMAX_LANGUAGE_BOOST", "auto")
# Скорость речи MiniMax (0.5–2.0), по умолчанию чуть быстрее нейтрали
MINIMAX_TTS_SPEED = float(os.getenv("MINIMAX_TTS_SPEED", "1.12"))

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini").strip()
# Vision (skill «ресторанный критик»); пусто = тот же OPENAI_MODEL (нужна поддержка image)
OPENAI_VISION_MODEL = os.getenv("OPENAI_VISION_MODEL", "").strip()

AVATAR_DIR = ROOT / "avatar"
ASSETS_DIR = ROOT / "assets"

# Фото для аватара: исходник и квадрат 512×512 (см. avatar/image_utils.py)
AVATAR_SOURCE_IMAGE = ROOT / os.getenv("AVATAR_SOURCE_IMAGE", "photo_5377349946119492617_w.jpg")
# Готовое 512×512: AVATAR_IMAGE_512 — путь от корня проекта или абсолютный.
# Если не задано: при наличии файла avatar_512.jpg в корне проекта он используется, иначе assets/avatar_512.jpg
_avatar512_env = os.getenv("AVATAR_IMAGE_512", "").strip()
if _avatar512_env:
    _p = Path(_avatar512_env)
    AVATAR_IMAGE_512 = _p if _p.is_absolute() else (ROOT / _p)
elif (ROOT / "avatar_512.jpg").is_file():
    AVATAR_IMAGE_512 = ROOT / "avatar_512.jpg"
else:
    AVATAR_IMAGE_512 = ASSETS_DIR / os.getenv("AVATAR_IMAGE_512_NAME", "avatar_512.jpg")

# Creatify Aurora (fal.ai)
CREATIFY_MODEL = os.getenv("CREATIFY_MODEL", "fal-ai/creatify/aurora")
CREATIFY_PROMPT = os.getenv(
    "CREATIFY_PROMPT",
    "Professional talking-head, soft studio lighting, neutral background, natural lip sync, 720p.",
)

# ASR: local = Whisper в transformers (офлайн после кэша). openai = API whisper-1 (быстро, нужен OPENAI_API_KEY, тариф OpenAI).
ASR_BACKEND = os.getenv("ASR_BACKEND", "local").strip().lower()
# ASR (HuggingFace id). По умолчанию — openai/whisper-small (быстрее на CPU, ~500 MB).
# Для лучшего казахского (медленно на CPU, ~1.5 GB): ASR_MODEL_ID=abilmansplus/whisper-turbo-ksc2
ASR_MODEL_ID = os.getenv("ASR_MODEL_ID", "openai/whisper-small")
ASR_DEVICE = os.getenv("ASR_DEVICE", "").strip() or "auto"
# Пусто = авто: 1 на CPU (быстрее), 5 на GPU. Явно: ASR_NUM_BEAMS=1 или 5
ASR_NUM_BEAMS = os.getenv("ASR_NUM_BEAMS", "").strip()
# Только для ASR_BACKEND=openai: ISO-639-1: ru, kk, en или пусто = авто (для чистого русского лучше ru)
ASR_OPENAI_LANGUAGE = os.getenv("ASR_OPENAI_LANGUAGE", "").strip()
# Локальный Whisper: kazakh | russian | english | auto (пусто/auto = без фикс. языка, медленнее/нестабильнее)
ASR_LOCAL_LANGUAGE = os.getenv("ASR_LOCAL_LANGUAGE", "kazakh").strip()

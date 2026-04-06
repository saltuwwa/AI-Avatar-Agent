"""
Оркестратор: вопрос → LLM + инструменты + память + vision → ответ; при необходимости TTS / аватар.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import config
from agent.llm import chat_with_tools
from agent.memory import trim_history
from agent.restaurant_vision import path_to_data_url
from agent.tools import SYSTEM_PROMPT, TOOL_DEFINITIONS
from voice.tts import synthesize


def chat_turn(
    history: list[dict[str, Any]],
    user_text: str,
    image_path: str | Path | None = None,
) -> tuple[str, list[dict[str, Any]]]:
    """
    Один ход диалога с памятью (history — только текстовые прошлые реплики).
    image_path — локальный файл фото (Gradio filepath).
    Возвращает (ответ_ассистента, обновлённая_история).
    """
    hist = [dict(x) for x in (history or [])]
    data_url = ""
    ip = image_path
    if ip is not None and str(ip).strip():
        p = Path(str(ip))
        if p.is_file():
            try:
                data_url = path_to_data_url(p)
            except OSError:
                data_url = ""

    user_text_effective = (user_text or "").strip()
    if not user_text_effective and not data_url:
        return "", hist

    if not user_text_effective and data_url:
        user_text_effective = (
            "Что на фото? Оцени заведение или блюдо и подскажи похожие места в Алматы."
        )

    if data_url:
        user_msg: dict[str, Any] = {
            "role": "user",
            "content": [
                {"type": "text", "text": user_text_effective},
                {"type": "image_url", "image_url": {"url": data_url, "detail": "low"}},
            ],
        }
        hist_user = {
            "role": "user",
            "content": user_text_effective + " [изображение]",
        }
    else:
        user_msg = {"role": "user", "content": user_text_effective}
        hist_user = {"role": "user", "content": user_text_effective}

    messages: list[dict[str, Any]] = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages.extend(hist)
    messages.append(user_msg)

    tool_ctx: dict[str, Any] | None = {"image_data_url": data_url} if data_url else None
    reply = chat_with_tools(messages, tools=TOOL_DEFINITIONS, tool_context=tool_ctx)
    reply = (reply or "").strip()

    new_history = trim_history(
        hist + [hist_user, {"role": "assistant", "content": reply}]
    )
    return reply, new_history


def chat_answer(user_message: str) -> str:
    """Один вопрос без истории и без изображения (совместимость)."""
    text, _ = chat_turn([], user_message, None)
    return text


def text_to_speech_only(text: str, out_path: Path | None = None) -> Path:
    """Озвучить текст клонированным голосом (нужен выполненный voice/clone.py)."""
    return synthesize(text, out_path=out_path)


def voice_to_answer_and_media(
    audio_path: str | None,
    *,
    user_text: str | None = None,
    speak: bool,
    make_video: bool,
    history: list[dict[str, Any]] | None = None,
) -> tuple[str, str, str | None, str | None, str, list[dict[str, Any]]]:
    """
    ASR (каз.) или текст вопроса → агент → ответ (рус.) → TTS; опционально Creatify Aurora.
    Если ``user_text`` не пустой, он используется как реплика пользователя (ASR не вызывается).
    Возвращает: transcript, answer, path_wav | None, path_mp4 | None, status, new_history.
    """
    from avatar.generate import generate_avatar_video
    from avatar.image_utils import ensure_avatar_512
    from agent.asr import transcribe_audio_file

    hist = [dict(x) for x in (history or [])]
    ut = (user_text or "").strip()

    if ut:
        transcript = ut
    elif audio_path and str(audio_path).strip():
        try:
            transcript = transcribe_audio_file(audio_path)
        except Exception as e:
            return "", "", None, None, f"ASR: {e}", hist
        if not transcript:
            return (
                "",
                "",
                None,
                None,
                "Не удалось распознать речь (слишком тихо или коротко).",
                hist,
            )
    else:
        return "", "", None, None, "Запишите аудио или введите вопрос текстом.", hist

    try:
        answer, hist = chat_turn(hist, transcript, None)
    except Exception as e:
        return transcript, "", None, None, f"Ассистент: {e}", hist

    if not speak:
        return transcript, answer, None, None, "Готово (только текст).", hist

    try:
        wav = synthesize(
            answer,
            out_path=config.VOICE_DIR / "pipeline_answer.wav",
            language_boost="Russian",
        )
    except Exception as e:
        return transcript, answer, None, None, f"TTS: {e}", hist

    if not make_video:
        return transcript, answer, str(wav), None, "Готово (аудио).", hist

    try:
        img = ensure_avatar_512()
        mp4 = generate_avatar_video(
            img,
            wav,
            out_path=config.AVATAR_DIR / "pipeline_avatar.mp4",
        )
    except Exception as e:
        return transcript, answer, str(wav), None, f"Видео не сгенерировано: {e}", hist

    return transcript, answer, str(wav), str(mp4), "Готово: аудио + видео.", hist

"""Общие обработчики Gradio: пайплайн чата, голоса, TTS, фото аватара."""

from __future__ import annotations

from pathlib import Path

import config
from agent.pipeline import chat_turn, voice_to_answer_and_media
from voice.tts import load_voice_id, synthesize


def run_assistant(question: str, speak: bool, image, history: list):
    h = list(history or [])
    q = (question or "").strip()
    img_path = None
    if image is not None:
        sp = str(image).strip()
        if sp and Path(sp).is_file():
            img_path = sp
    if not q and not img_path:
        return "", None, "Введите вопрос или прикрепите фото.", h

    try:
        answer, h = chat_turn(h, q, img_path)
    except RuntimeError as e:
        return "", None, str(e), h
    except Exception as e:
        return "", None, f"Ошибка: {e}", h

    mem_note = f" Память: {len(h) // 2} пар реплик."
    if not speak:
        return answer, None, "Готово (только текст)." + mem_note, h

    try:
        load_voice_id()
    except FileNotFoundError:
        return (
            answer,
            None,
            "Ответ готов. Озвучка: сначала python voice/clone.py и FAL_KEY в .env." + mem_note,
            h,
        )
    try:
        path = synthesize(
            answer,
            out_path=config.VOICE_DIR / "last_assistant.wav",
            language_boost="Russian",
        )
        return answer, str(path), "Готово." + mem_note, h
    except Exception as e:
        return answer, None, f"Ответ готов. Озвучка: {e}" + mem_note, h


def clear_chat_memory():
    return [], "Диалог очищен. Можно начать заново."


def _history_to_chatbot_messages(history: list) -> list[dict[str, str]]:
    """Память ассистента → формат gr.Chatbot(type='messages')."""
    h = history or []
    out: list[dict[str, str]] = []
    for item in h:
        role = item.get("role")
        if role not in ("user", "assistant"):
            continue
        out.append({"role": role, "content": str(item.get("content", ""))})
    return out


def clear_voice_memory():
    return [], "Диалог очищен. Можно начать заново.", [], ""


def try_tts(text: str):
    text = (text or "").strip()
    if not text:
        return None, "Введите текст."
    try:
        load_voice_id()
    except FileNotFoundError:
        return (
            None,
            "Сначала: python voice/clone.py (и FAL_KEY в .env).",
        )
    try:
        path = synthesize(
            text,
            out_path=config.VOICE_DIR / "last_tts.wav",
            language_boost="Russian",
        )
        return str(path), "Готово."
    except Exception as e:
        return None, f"Ошибка: {e}"


def run_voice_pipeline(
    audio,
    user_text: str,
    speak: bool,
    make_video: bool,
    history: list,
):
    if make_video and not speak:
        make_video = False
    tr, ans, wav, vid, st, h = voice_to_answer_and_media(
        audio if audio else None,
        user_text=user_text,
        speak=speak,
        make_video=make_video,
        history=history,
    )
    if h and "Память:" not in st:
        st = f"{st} Память: {len(h) // 2} пар реплик."
    chat_msgs = _history_to_chatbot_messages(h)
    return tr, ans, wav, vid, st, h, chat_msgs, ""


def prepare_avatar_photo():
    try:
        from avatar.image_utils import ensure_avatar_512

        p = ensure_avatar_512()
        resolved = p.resolve()
        img = str(resolved) if resolved.is_file() else None
        return f"Готово: {resolved}", img
    except Exception as e:
        return f"Ошибка: {e}. Проверьте AVATAR_SOURCE_IMAGE и путь к фото.", None

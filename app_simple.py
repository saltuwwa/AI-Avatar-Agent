"""
Gradio-интерфейс по ТЗ: вкладки голос / текст+фото / TTS.
Запуск: python app_simple.py  →  http://127.0.0.1:7860
"""

from __future__ import annotations

from pathlib import Path

import gradio as gr

import config
from gradio_handlers import (
    clear_chat_memory,
    clear_voice_memory,
    prepare_avatar_photo,
    run_assistant,
    run_voice_pipeline,
    try_tts,
)

_AVATAR_PREVIEW = (
    str(config.AVATAR_IMAGE_512.resolve())
    if config.AVATAR_IMAGE_512.is_file()
    else None
)


def build_ui() -> gr.Blocks:
    with gr.Blocks(
        title="Дастарқан AI · Алматы (ТЗ)",
        theme=gr.themes.Soft(primary_hue="orange"),
    ) as demo:
        gr.Markdown(
            "### AI Avatar Agent — режим для сдачи проекта\n"
            "**Голос:** запись с микрофона → **реальный ASR** (Whisper) → LLM + тулы → TTS → опционально видео (Creatify). "
            "Статическая страница `index.html` — отдельное **демо** с заготовленным текстом при клике на микрофон; для настоящего распознавания используйте эту вкладку.\n\n"
            "---"
        )

        with gr.Tab("1. Голос (қазақша) → жауап"):
            gr.Markdown(
                "**Микрофон** или **текст** (одно и то же «Отправить»): если поле текста заполнено — вопрос берётся из него, ASR не вызывается; иначе используется распознавание записи. "
                "Галочка «Видео» — `FAL_KEY`, баланс fal, фото 512×512. "
                "**Память** общая для голоса и текста на этой вкладке; **Очистить память** сбрасывает контекст."
            )
            chat_voice = gr.State(value=[])
            with gr.Row():
                with gr.Column():
                    mic = gr.Audio(
                        sources=["microphone"],
                        type="filepath",
                        label="Микрофон",
                        format="wav",
                    )
                    voice_text = gr.Textbox(
                        label="Или вопрос текстом (қазақша / русский)",
                        lines=3,
                        placeholder="Продолжение диалога без записи: введите текст и нажмите «Отправить».",
                    )
                    speak_cb = gr.Checkbox(label="Озвучить ответ (русский, клон)", value=True)
                    video_cb = gr.Checkbox(
                        label="Сгенерировать видео-аватар (Creatify Aurora)",
                        value=False,
                    )
                    with gr.Row():
                        go = gr.Button("Отправить", variant="primary")
                        btn_clear_voice = gr.Button("Очистить память", variant="secondary")
                    tr = gr.Textbox(label="Запрос (ASR или ваш текст)", lines=3)
                    ans = gr.Textbox(label="Ответ ассистента", lines=12)
                    out_wav = gr.Audio(label="Озвучка", type="filepath")
                    st = gr.Textbox(label="Статус (ошибки ASR/TTS/видео смотрите здесь)", lines=3)
                with gr.Column():
                    avatar_preview = gr.Image(
                        label="Фото аватара 512×512",
                        type="filepath",
                        height=280,
                        interactive=False,
                        value=_AVATAR_PREVIEW,
                    )
                    prep = gr.Button("Подготовить фото 512×512 из AVATAR_SOURCE_IMAGE")
                    prep_status = gr.Textbox(label="Статус фото", lines=1)
                    out_vid = gr.Video(label="Видео аватара", height=320)

            chatbot_voice = gr.Chatbot(
                label="Память диалога (голос или текст → ответ)",
                height=220,
                type="messages",
                show_copy_button=True,
            )
            go.click(
                run_voice_pipeline,
                inputs=[mic, voice_text, speak_cb, video_cb, chat_voice],
                outputs=[tr, ans, out_wav, out_vid, st, chat_voice, chatbot_voice, voice_text],
                api_name=False,
            )
            btn_clear_voice.click(
                clear_voice_memory,
                outputs=[chat_voice, st, chatbot_voice, voice_text],
                api_name=False,
            )
            prep.click(
                prepare_avatar_photo,
                outputs=[prep_status, avatar_preview],
                api_name=False,
            )

        with gr.Tab("2. Текст + фото (память, vision, тулы)"):
            gr.Markdown(
                "Вопрос и опционально фото (интерьер, блюдо). Память — последние реплики сессии. "
                "Инструмент **analyze_restaurant_photo** вызывается LLM при необходимости."
            )
            chat_txt = gr.State(value=[])
            q = gr.Textbox(label="Вопрос", lines=4, placeholder="Русский или қазақша…")
            photo = gr.Image(
                label="Фото (необязательно)",
                type="filepath",
                sources=["upload", "webcam"],
            )
            speak = gr.Checkbox(label="Озвучить ответ", value=False)
            with gr.Row():
                btn = gr.Button("Спросить", variant="primary")
                btn_clear = gr.Button("Очистить память")
            out_text = gr.Textbox(label="Ответ", lines=14)
            out_audio = gr.Audio(label="Озвучка", type="filepath")
            status = gr.Textbox(label="Статус", lines=2)

            btn.click(
                run_assistant,
                inputs=[q, speak, photo, chat_txt],
                outputs=[out_text, out_audio, status, chat_txt],
                api_name=False,
            )
            btn_clear.click(clear_chat_memory, outputs=[chat_txt, status], api_name=False)

        with gr.Tab("3. Только TTS"):
            inp = gr.Textbox(label="Текст для синтеза", lines=4)
            b = gr.Button("Синтез", variant="primary")
            out_a = gr.Audio(label="WAV", type="filepath")
            st2 = gr.Textbox(label="Статус", lines=1)
            b.click(try_tts, inputs=[inp], outputs=[out_a, st2], api_name=False)

    return demo


if __name__ == "__main__":
    config.ASSETS_DIR.mkdir(parents=True, exist_ok=True)
    config.AVATAR_DIR.mkdir(parents=True, exist_ok=True)
    build_ui().launch(
        server_name="127.0.0.1",
        server_port=7860,
        show_api=False,
        show_error=True,
    )

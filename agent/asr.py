"""
ASR: два режима (config.ASR_BACKEND):

- **local** — Whisper в transformers (ASR_MODEL_ID), офлайн после кэша.
- **openai** — удалённый Whisper (`whisper-1` API), нужен OPENAI_API_KEY; обычно быстрее на слабом CPU.

Параметры: см. ASR_* в config / .env.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import config

_transcriber: Any = None


def _resolve_local_language() -> str | None:
    """Whisper (HF): полное имя языка или None = авто."""
    raw = (config.ASR_LOCAL_LANGUAGE or "kazakh").strip().lower()
    if raw in ("", "auto"):
        return None
    aliases = {
        "ru": "russian",
        "kk": "kazakh",
        "kaz": "kazakh",
        "en": "english",
    }
    return aliases.get(raw, raw)


def _device() -> str:
    import torch

    d = (config.ASR_DEVICE or "auto").strip().lower()
    if d == "auto":
        return "cuda:0" if torch.cuda.is_available() else "cpu"
    return config.ASR_DEVICE


class _Transcriber:
    """Адаптация примера с карточки модели (чанки 30 с)."""

    def __init__(
        self,
        model_path: str,
        device: str,
        sampling_rate: int = 16_000,
        language: str | None = "kazakh",
        task: str = "transcribe",
        num_beams: int = 5,
        chunk_length_s: int = 30,
        stride_length_s: int = 1,
    ) -> None:
        import numpy as np
        import torch
        from transformers import WhisperForConditionalGeneration, WhisperProcessor

        self._np = np
        self._torch = torch

        proc_kw: dict[str, Any] = {"task": task}
        if language:
            proc_kw["language"] = language
        self.processor = WhisperProcessor.from_pretrained(model_path, **proc_kw)
        self.model = WhisperForConditionalGeneration.from_pretrained(model_path)
        self.model = self.model.to(device)
        self.model.eval()
        self.sr = sampling_rate
        self.language = language
        self.task = task
        self.num_beams = num_beams
        self.chunk_length_s = chunk_length_s
        self.stride_length_s = stride_length_s
        self.device = device

    def transcribe(self, audio_path: str) -> str:
        import librosa

        speech_array, _ = librosa.load(audio_path, sr=self.sr)
        audio_length_s = len(speech_array) / self.sr

        if audio_length_s <= self.chunk_length_s:
            return self._transcribe_chunk(speech_array)

        chunk_length_samples = int(self.chunk_length_s * self.sr)
        stride_length_samples = int(self.stride_length_s * self.sr)
        num_samples = len(speech_array)
        num_chunks = max(
            1,
            int(
                1
                + self._np.ceil(
                    (num_samples - chunk_length_samples)
                    / (chunk_length_samples - stride_length_samples)
                )
            ),
        )

        parts: list[str] = []
        for i in range(int(num_chunks)):
            start = max(0, i * (chunk_length_samples - stride_length_samples))
            end = min(num_samples, start + chunk_length_samples)
            chunk = speech_array[start:end]
            parts.append(self._transcribe_chunk(chunk))
        return " ".join(parts)

    def _transcribe_chunk(self, audio_chunk: Any) -> str:
        torch = self._torch
        inputs = self.processor(
            audio_chunk,
            sampling_rate=self.sr,
            return_tensors="pt",
        ).input_features.to(self.device)

        attention_mask = torch.ones_like(inputs[:, :, 0])

        gen_kw: dict[str, Any] = {
            "max_length": 448,
            "num_beams": self.num_beams,
            "attention_mask": attention_mask,
        }
        if self.language:
            gen_kw["forced_decoder_ids"] = self.processor.get_decoder_prompt_ids(
                language=self.language,
                task=self.task,
            )

        with torch.no_grad():
            generated_ids = self.model.generate(inputs, **gen_kw)

        return self.processor.batch_decode(generated_ids, skip_special_tokens=True)[0]


def _num_beams_for_device(device: str) -> int:
    if config.ASR_NUM_BEAMS:
        return max(1, int(config.ASR_NUM_BEAMS))
    # beam=5 на карточке модели; на CPU это раздувает время в разы
    return 1 if device == "cpu" else 5


def get_transcriber() -> _Transcriber:
    global _transcriber
    if _transcriber is None:
        dev = _device()
        _transcriber = _Transcriber(
            config.ASR_MODEL_ID,
            device=dev,
            language=_resolve_local_language(),
            num_beams=_num_beams_for_device(dev),
        )
    return _transcriber


def _transcribe_openai(path: Path) -> str:
    if not config.OPENAI_API_KEY:
        raise RuntimeError(
            "ASR_BACKEND=openai: задайте OPENAI_API_KEY в .env (тот же ключ, что для чата)."
        )
    from openai import OpenAI

    client = OpenAI(api_key=config.OPENAI_API_KEY)
    path = path.resolve()
    with open(path, "rb") as audio_f:
        kwargs: dict[str, Any] = {
            "model": "whisper-1",
            "file": audio_f,
        }
        lang = config.ASR_OPENAI_LANGUAGE
        if lang:
            kwargs["language"] = lang
        tr = client.audio.transcriptions.create(**kwargs)
    return (getattr(tr, "text", None) or "").strip()


def transcribe_audio_file(path: str | Path) -> str:
    """Распознавание: локальный Whisper или OpenAI API — см. ASR_BACKEND."""
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(str(path))

    backend = (config.ASR_BACKEND or "local").strip().lower()
    if backend in ("openai", "remote", "api"):
        return _transcribe_openai(path)

    text = get_transcriber().transcribe(str(path.resolve()))
    return (text or "").strip()

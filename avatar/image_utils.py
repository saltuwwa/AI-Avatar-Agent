"""Подготовка фото аватара под формат, который ожидает Creatify (квадрат 512×512)."""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from PIL import Image

import config


def make_square_512(
    source: Path,
    dest: Path,
    *,
    size: int = 512,
) -> Path:
    """
    Центральный кроп до квадрата, затем resize. Сохраняет JPEG/PNG в зависимости от dest.suffix.
    """
    source = source.resolve()
    if not source.is_file():
        raise FileNotFoundError(f"Нет файла: {source}")

    img = Image.open(source).convert("RGB")
    w, h = img.size
    side = min(w, h)
    left = (w - side) // 2
    top = (h - side) // 2
    img = img.crop((left, top, left + side, top + side))
    img = img.resize((size, size), Image.Resampling.LANCZOS)

    dest = dest.resolve()
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.suffix.lower() in (".jpg", ".jpeg"):
        img.save(dest, "JPEG", quality=92)
    else:
        img.save(dest, "PNG")
    return dest


def ensure_avatar_512(
    source: Path | None = None,
    dest: Path | None = None,
) -> Path:
    """Если dest нет — создать из source."""
    src = (source or config.AVATAR_SOURCE_IMAGE).resolve()
    out = (dest or config.AVATAR_IMAGE_512).resolve()
    if out.is_file():
        return out
    return make_square_512(src, out)


if __name__ == "__main__":
    out = ensure_avatar_512()
    print("Сохранено:", out.resolve())

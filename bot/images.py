"""Картинки карточек.

Файл ищется по коду карты: data/cards/OPT-01.png (или .jpg/.jpeg/.webp).
Если файла нет — карта уходит одним текстовым сообщением, как раньше.

Загруженный в Telegram файл кешируется: во второй раз отправляем file_id,
а не сам файл. Кеш сбрасывается, если картинку на диске подменили.
"""

from __future__ import annotations

import logging
from pathlib import Path

from bot.config import BASE_DIR
from bot.models import Card

log = logging.getLogger(__name__)

CARDS_DIR = BASE_DIR / "data" / "cards"
EXTENSIONS = (".png", ".jpg", ".jpeg", ".webp")


def find_image(card: Card) -> Path | None:
    """Путь к картинке карты или None."""
    if card.image_path:
        explicit = Path(card.image_path)
        if not explicit.is_absolute():
            explicit = BASE_DIR / explicit
        return explicit if explicit.exists() else None

    for extension in EXTENSIONS:
        candidate = CARDS_DIR / f"{card.code}{extension}"
        if candidate.exists():
            return candidate
    return None


def signature(path: Path) -> str:
    """Отпечаток файла: размер и время правки. Меняется — значит картинку заменили."""
    stat = path.stat()
    return f"{stat.st_size}:{int(stat.st_mtime)}"


def cached_file_id(card: Card, path: Path) -> str | None:
    if not card.image_file_id:
        return None
    return card.image_file_id if card.image_sig == signature(path) else None


def count_available(cards: list[Card]) -> int:
    return sum(1 for card in cards if find_image(card) is not None)

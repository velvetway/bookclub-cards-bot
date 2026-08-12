"""Картинки карточек.

Файл ищется по коду карты: data/cards/OPT-01.png (или .jpg/.jpeg/.webp).
Если файла нет — карта уходит одним текстовым сообщением, как раньше.

Загруженный в Telegram файл кешируется: во второй раз отправляем file_id,
а не сам файл. Кеш сбрасывается, если картинку на диске подменили.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path

from bot.config import BASE_DIR
from bot.models import Card

log = logging.getLogger(__name__)

CARDS_DIR = BASE_DIR / "data" / "cards"
COVERS_DIR = BASE_DIR / "data" / "covers"
COVERS_META = BASE_DIR / "data" / "covers.json"
EXTENSIONS = (".png", ".jpg", ".jpeg", ".webp")

MAIN_COVER = "DECK-MAIN"


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


# ------------------------------------------------------------------ обложки


@dataclass(frozen=True)
class Cover:
    """Рубашка колоды: её можно показать, не раскрывая содержимого карт."""

    code: str
    title: str
    prefix: str | None  # префикс кодов карт этой колоды, у общей его нет
    path: Path

    @property
    def is_main(self) -> bool:
        return self.prefix is None


def _cover_file(code: str) -> Path | None:
    for extension in EXTENSIONS:
        candidate = COVERS_DIR / f"{code}{extension}"
        if candidate.exists():
            return candidate
    return None


def load_covers() -> list[Cover]:
    """Обложки, у которых есть и описание, и файл на диске."""
    if not COVERS_META.exists():
        return []
    meta = json.loads(COVERS_META.read_text(encoding="utf-8"))

    covers = []
    for item in meta:
        path = _cover_file(item["code"])
        if path is None:
            continue
        covers.append(
            Cover(
                code=item["code"],
                title=item["title"],
                prefix=item.get("prefix"),
                path=path,
            )
        )
    return covers


def cover_for_codes(card_codes: list[str]) -> Cover | None:
    """Подбирает обложку по кодам карт книги: ACK-07 → детективная, иначе общая.

    Так обложка привязана к колоде, а не к книге: заводить книжную колоду
    можно без единой правки в настройках.
    """
    covers = load_covers()
    if not covers:
        return None

    prefixes = {code.split("-")[0] for code in card_codes}
    for cover in covers:
        if cover.prefix and cover.prefix in prefixes:
            return cover
    return next((c for c in covers if c.is_main), None)

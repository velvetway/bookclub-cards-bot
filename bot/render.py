"""Сборка картинок в рантайме: вся колода одним листом и постер раздачи.

Обе картинки собираются из тех же файлов, что уходят участникам. Если у карты
картинки нет, вместо неё рисуется плашка с кодом и названием — лист не должен
разваливаться из-за одной недостающей.
"""

from __future__ import annotations

import io
import logging
from pathlib import Path
from zoneinfo import ZoneInfo

from PIL import Image, ImageDraw, ImageFont

from bot import images
from bot.models import PHASE_NAMES, Book, Card, Deal
from bot.storage.deals import AssignmentView
from bot.timeutil import fmt_dt

log = logging.getLogger(__name__)

FONT_CANDIDATES = (
    "/System/Library/Fonts/Supplemental/Georgia Bold.ttf",
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf",
)

BACKDROP = (20, 17, 14)
INK = (240, 233, 220)
DIM = (150, 140, 126)
PLACEHOLDER = (46, 40, 34)

MARGIN = 26
GAP = 14
NAME_STRIP = 58
JPEG_QUALITY = 86
MAX_SIDE = 4000  # Telegram ужимает больше, а вес растёт зря


def _font(size: int) -> ImageFont.FreeTypeFont:
    for candidate in FONT_CANDIDATES:
        if Path(candidate).exists():
            return ImageFont.truetype(candidate, size)
    return ImageFont.load_default(size)


def _fit(draw: ImageDraw.ImageDraw, text: str, size: int, limit: int) -> ImageFont.FreeTypeFont:
    """Подбирает кегль так, чтобы строка влезла по ширине."""
    while size > 10:
        font = _font(size)
        if draw.textlength(text, font=font) <= limit:
            return font
        size -= 2
    return _font(10)


def _columns(count: int) -> int:
    if count <= 4:
        return min(count, 2)
    if count <= 12:
        return 3
    if count <= 30:
        return 4
    return 5


def _thumb(card: Card, side: int) -> Image.Image:
    """Миниатюра карты либо плашка с кодом, если картинки нет."""
    path = images.find_image(card)
    if path is not None:
        try:
            image = Image.open(path).convert("RGB")
            return image.resize((side, side), Image.LANCZOS)
        except OSError as exc:  # битый файл не должен ронять весь лист
            log.warning("не удалось прочитать картинку %s: %s", path, exc)

    tile = Image.new("RGB", (side, side), PLACEHOLDER)
    draw = ImageDraw.Draw(tile)
    code_font = _fit(draw, card.code, side // 7, side - 24)
    title_font = _fit(draw, card.title, side // 11, side - 24)

    draw.text((side / 2, side * 0.42), card.code, font=code_font, fill=INK, anchor="mm")
    draw.text((side / 2, side * 0.58), card.title, font=title_font, fill=DIM, anchor="mm")
    return tile


def _dim(tile: Image.Image, amount: float = 0.55) -> Image.Image:
    """Гасит выключенную карту, чтобы её было видно, но не путать с рабочей."""
    veil = Image.new("RGB", tile.size, BACKDROP)
    return Image.blend(tile, veil, amount)


def _canvas(width: int, height: int, title: str, subtitle: str = "") -> tuple[Image.Image, int]:
    """Холст с заголовком. Возвращает картинку и высоту шапки."""
    head = 96 if subtitle else 74
    sheet = Image.new("RGB", (width, height + head), BACKDROP)
    draw = ImageDraw.Draw(sheet)

    title_font = _fit(draw, title, 40, width - 2 * MARGIN)
    draw.text((MARGIN, 24), title, font=title_font, fill=INK)
    if subtitle:
        sub_font = _fit(draw, subtitle, 26, width - 2 * MARGIN)
        draw.text((MARGIN, 66), subtitle, font=sub_font, fill=DIM)
    return sheet, head


def _encode(sheet: Image.Image) -> bytes:
    if max(sheet.size) > MAX_SIDE:
        sheet.thumbnail((MAX_SIDE, MAX_SIDE), Image.LANCZOS)
    buffer = io.BytesIO()
    sheet.save(buffer, "JPEG", quality=JPEG_QUALITY, optimize=True)
    return buffer.getvalue()


def deck_sheet(cards: list[Card], title: str) -> bytes:
    """Вся колода одним листом, выключенные карты приглушены."""
    if not cards:
        raise ValueError("нечего показывать: в выборке нет карт")

    columns = _columns(len(cards))
    side = 460 if len(cards) <= 12 else 340
    rows = (len(cards) + columns - 1) // columns

    width = MARGIN * 2 + columns * side + (columns - 1) * GAP
    height = MARGIN + rows * side + (rows - 1) * GAP + MARGIN

    alive = sum(1 for c in cards if c.is_active)
    subtitle = f"{len(cards)} карт, включено {alive}"
    sheet, head = _canvas(width, height, title, subtitle)

    for index, card in enumerate(cards):
        tile = _thumb(card, side)
        if not card.is_active:
            tile = _dim(tile)
        x = MARGIN + (index % columns) * (side + GAP)
        y = head + MARGIN + (index // columns) * (side + GAP)
        sheet.paste(tile, (x, y))

    return _encode(sheet)


def deal_board(
    views: list[AssignmentView],
    deal: Deal,
    book: Book | None,
    tz: ZoneInfo,
) -> bytes:
    """Постер раздачи: напротив каждого участника его карта.

    Раскрывает содержимое всех карт разом — отправлять только после встречи
    или тем, кому можно видеть весь расклад.
    """
    if not views:
        raise ValueError("в раздаче никого нет")

    columns = _columns(len(views))
    side = 420 if len(views) <= 9 else 330
    rows = (len(views) + columns - 1) // columns
    cell_h = side + NAME_STRIP

    width = MARGIN * 2 + columns * side + (columns - 1) * GAP
    height = MARGIN + rows * cell_h + (rows - 1) * GAP + MARGIN

    title = f"«{book.title}»" if book else "Раздача"
    parts = [PHASE_NAMES.get(deal.phase, deal.phase), f"{len(views)} участников"]
    if book and book.meeting_at:
        parts.append(f"встреча {fmt_dt(book.meeting_at, tz)}")
    sheet, head = _canvas(width, height, title, " · ".join(parts))
    draw = ImageDraw.Draw(sheet)

    for index, view in enumerate(views):
        x = MARGIN + (index % columns) * (side + GAP)
        y = head + MARGIN + (index // columns) * (cell_h + GAP)

        sheet.paste(_thumb(view.card, side), (x, y))

        name_font = _fit(draw, view.user.display_name, 30, side - 16)
        draw.text(
            (x + side / 2, y + side + NAME_STRIP / 2 - 4),
            view.user.display_name,
            font=name_font,
            fill=INK,
            anchor="mm",
        )

    return _encode(sheet)

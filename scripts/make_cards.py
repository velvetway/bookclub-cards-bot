#!/usr/bin/env python3
"""Наносит названия карт на сгенерированные картинки.

Зачем: Gemini рисует кириллицу криво и по-разному от карты к карте, а подпись
должна быть одинаковой во всей колоде. Поэтому картинки генерируются без текста,
с чистой полосой внизу, а название печатается здесь.

    python scripts/make_cards.py                  # data/cards/raw → data/cards
    python scripts/make_cards.py --only OPT-01    # одну карту
    python scripts/make_cards.py --font ~/f.ttf   # свой шрифт

Нужен Pillow:  pip install -r scripts/requirements.txt
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:  # pragma: no cover - подсказка вместо стектрейса
    sys.exit("Нужен Pillow: pip install -r scripts/requirements.txt")

BASE_DIR = Path(__file__).resolve().parent.parent
DECK = BASE_DIR / "data" / "deck.json"
RAW_DIR = BASE_DIR / "data" / "cards" / "raw"
OUT_DIR = BASE_DIR / "data" / "cards"

EXTENSIONS = (".png", ".jpg", ".jpeg", ".webp")

# шрифты с кириллицей, которые обычно уже стоят в системе
FONT_CANDIDATES = (
    "/System/Library/Fonts/Supplemental/Georgia Bold.ttf",
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
    "/System/Library/Fonts/Supplemental/Times New Roman Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf",
)

PLATE_HEIGHT = 0.22      # доля высоты картинки под затемнение снизу
TEXT_MARGIN = 0.08       # отступ от краёв по ширине
MAX_FONT = 0.11          # максимальный кегль как доля высоты картинки
MIN_FONT = 0.04
MAX_SIDE = 1280          # Telegram всё равно ужмёт, а репозиторий не пухнет


def find_font(explicit: str | None) -> Path:
    if explicit:
        path = Path(explicit).expanduser()
        if not path.exists():
            sys.exit(f"Шрифт не найден: {path}")
        return path
    for candidate in FONT_CANDIDATES:
        if Path(candidate).exists():
            return Path(candidate)
    sys.exit(
        "Не нашёл системный шрифт с кириллицей. Укажи свой: --font /путь/к/шрифту.ttf"
    )


def load_deck() -> dict[str, str]:
    deck = json.loads(DECK.read_text(encoding="utf-8"))
    return {item["code"]: item["title"] for item in deck}


def find_source(code: str, raw_dir: Path) -> Path | None:
    for extension in EXTENSIONS:
        candidate = raw_dir / f"{code}{extension}"
        if candidate.exists():
            return candidate
    return None


def fit_font(draw: ImageDraw.ImageDraw, text: str, font_path: Path, width: int, height: int):
    """Подбирает кегль так, чтобы название влезло в одну строку."""
    limit = width * (1 - 2 * TEXT_MARGIN)
    size = int(height * MAX_FONT)
    while size > int(height * MIN_FONT):
        font = ImageFont.truetype(str(font_path), size)
        if draw.textlength(text, font=font) <= limit:
            return font
        size -= 2
    return ImageFont.truetype(str(font_path), int(height * MIN_FONT))


def draw_plate(image: Image.Image) -> Image.Image:
    """Мягкое затемнение снизу, чтобы белый текст читался на любой картинке."""
    width, height = image.size
    plate_height = int(height * PLATE_HEIGHT)

    # градиент строим в один пиксель шириной и растягиваем — так быстрее попиксельного цикла
    column = Image.new("L", (1, plate_height))
    column.putdata([int(190 * (y / plate_height) ** 1.4) for y in range(plate_height)])
    mask = column.resize((width, plate_height))

    overlay = Image.new("RGB", (width, plate_height), (12, 8, 4))
    image.paste(overlay, (0, height - plate_height), mask)
    return image


def render(source: Path, title: str, out_path: Path, font_path: Path) -> None:
    image = Image.open(source).convert("RGB")
    image = draw_plate(image)

    draw = ImageDraw.Draw(image)
    width, height = image.size
    font = fit_font(draw, title, font_path, width, height)

    text_width = draw.textlength(title, font=font)
    x = (width - text_width) / 2
    y = height - int(height * PLATE_HEIGHT * 0.62)

    draw.text((x + 2, y + 2), title, font=font, fill=(0, 0, 0))
    draw.text((x, y), title, font=font, fill=(255, 248, 235))

    out_path.parent.mkdir(parents=True, exist_ok=True)
    if image.width > MAX_SIDE:
        image.thumbnail((MAX_SIDE, MAX_SIDE), Image.LANCZOS)
    image.save(out_path, "JPEG", quality=90, optimize=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="Подписывает картинки карточек")
    parser.add_argument("--raw", type=Path, default=RAW_DIR, help="папка с исходниками")
    parser.add_argument("--out", type=Path, default=OUT_DIR, help="куда класть готовые")
    parser.add_argument("--font", help="путь к ttf-шрифту с кириллицей")
    parser.add_argument("--only", help="обработать только одну карту, например OPT-01")
    args = parser.parse_args()

    if not args.raw.exists():
        sys.exit(
            f"Нет папки с исходниками: {args.raw}\n"
            "Сложи туда картинки из Gemini под именами OPT-01.png, INS-07.png и так далее."
        )

    font_path = find_font(args.font)
    deck = load_deck()
    codes = [args.only] if args.only else list(deck)

    done, missing = 0, []
    for code in codes:
        title = deck.get(code)
        if title is None:
            sys.exit(f"Кода {code} нет в колоде")
        source = find_source(code, args.raw)
        if source is None:
            missing.append(code)
            continue
        render(source, title, args.out / f"{code}.jpg", font_path)
        done += 1
        print(f"✓ {code} — {title}")

    print(f"\nГотово: {done}. Шрифт: {font_path.name}")
    if missing:
        print(f"Нет исходников для {len(missing)}: {', '.join(missing)}")


if __name__ == "__main__":
    main()

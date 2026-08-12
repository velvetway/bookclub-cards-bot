#!/usr/bin/env python3
"""Собирает промпты карточек из файла сцен.

Источник — prompts/scenes*.json (общий стиль плюс кот и сцена под смысл каждой
карты). Отсюда получаются два файла:
  <имя>_prompts.md   — читать и копировать в Gemini руками
  <имя>_prompts.json — если генерить пачкой через API

    python scripts/build_prompts.py                     # основная колода
    python scripts/build_prompts.py --scenes prompts/scenes_ack.json
    python scripts/build_prompts.py --all               # все колоды сразу

Книжная колода может не описывать стиль, а сослаться на основную через
"style_from" — тогда манера рисунка гарантированно одна на все колоды.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
PROMPTS_DIR = BASE_DIR / "prompts"
DEFAULT_SCENES = PROMPTS_DIR / "scenes.json"

TYPE_BY_PREFIX = {
    "OPT": "Оптика",
    "INS": "Врезка",
    "RAT": "К оценке",
    "ACK": "Врезка · под книгу",
    "DECK": "Обложки",
}

DEFAULT_TITLE = "Промпты для карточек"
DEFAULT_LEAD = (
    "31 карта: у каждой свой кот и своя локация, общая — только манера рисунка."
)

HEADER = """# {title}

{lead}

Сгенерировано скриптом `scripts/build_prompts.py` из `{source}` —
правь котов и сцены там, а не здесь.

## Как пользоваться

1. Генерируешь картинку по промпту карты. Формат квадратный, 1:1.
2. Кладёшь результат в `data/cards/raw/` под именем кода: `OPT-01.png`, `ACK-07.png`.
3. `python scripts/make_cards.py` — скрипт впечатает название карты в нижнюю
   полосу и сложит готовое в `data/cards/`. Бот сам подхватит файлы по коду.

Название печатается кодом, а не моделью: кириллицу генераторы пишут криво и
по-разному от карты к карте, а подпись должна быть одинаковой во всей колоде.
Поэтому в промптах прямо запрещён любой текст, а низ кадра просят оставить
спокойным — туда ляжет подпись.
{extra}
## Что различается, а что нет

Различается: герой (окрас, порода, возраст, характер — под смысл карты),
локация, палитра, время суток, погода.

Совпадает: манера рисунка. Тёплая живописная иллюстрация со сказочным
реализмом, мягкий свет, боке, пылинки в воздухе, проработанная шерсть,
приглушённая винтажная цветокоррекция. Эта часть вклеена в каждый промпт
дословно — её лучше не переписывать от карты к карте.

## Если колода всё же расползается по стилю

- Генерируй всё в одном чате одной моделью, не меняя формулировку стиля.
- Возьми одну удачную карту как референс и проси «та же манера рисунка,
  другой герой и другое место» — модели держат стиль лучше, чем персонажа.
- Проверяй низ кадра: если туда попало что-то важное, перегенерируй, иначе
  подпись ляжет поверх.

## Общая часть стиля

Она уже вклеена в каждый промпт ниже:

```
{style}
```

Негативная часть:

```
{negative}
```
"""


def load_style(data: dict, source: Path) -> dict:
    """Стиль берётся из самого файла либо из того, на который он ссылается."""
    if "style" in data:
        return data["style"]
    reference = data.get("style_from")
    if not reference:
        raise SystemExit(f"{source.name}: нет ни style, ни style_from")
    parent = json.loads((source.parent / reference).read_text(encoding="utf-8"))
    return parent["style"]


def build(source: Path) -> int:
    data = json.loads(source.read_text(encoding="utf-8"))
    style = load_style(data, source)
    doc = data.get("doc", {})
    common = f"{style['look']}. {style['variation']}. {style['frame']}"

    extra = doc.get("extra", "")
    lines = [
        HEADER.format(
            title=doc.get("title", DEFAULT_TITLE),
            lead=doc.get("lead", DEFAULT_LEAD),
            source=f"prompts/{source.name}",
            extra=f"\n{extra}\n" if extra else "",
            style=common,
            negative=style["negative"],
        ),
        "",
        "---",
        "",
    ]

    bundle = []
    current_type = None

    for card in data["cards"]:
        card_type = TYPE_BY_PREFIX.get(card["code"].split("-")[0], "")
        if card_type != current_type:
            lines.append(f"## {card_type}")
            lines.append("")
            current_type = card_type

        prompt = f"{card['cat']}, {card['scene']}. {common}. {style['negative']}"
        bundle.append({**card, "prompt": prompt})

        lines.append(f"### {card['code']} · {card['title']}")
        lines.append("")
        lines.append("```")
        lines.append(prompt)
        lines.append("```")
        lines.append("")

    stem = "card" if source.stem == "scenes" else source.stem.removeprefix("scenes_")
    out_md = PROMPTS_DIR / f"{stem}_prompts.md"
    out_json = PROMPTS_DIR / f"{stem}_prompts.json"
    out_md.write_text("\n".join(lines), encoding="utf-8")
    out_json.write_text(json.dumps(bundle, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"{source.name}: {len(bundle)} промптов → {out_md.name}, {out_json.name}")
    return len(bundle)


def main() -> None:
    parser = argparse.ArgumentParser(description="Собирает промпты карточек")
    parser.add_argument("--scenes", type=Path, default=DEFAULT_SCENES, help="файл сцен")
    parser.add_argument("--all", action="store_true", help="все файлы prompts/scenes*.json")
    args = parser.parse_args()

    sources = sorted(PROMPTS_DIR.glob("scenes*.json")) if args.all else [args.scenes]
    total = sum(build(source) for source in sources)
    if len(sources) > 1:
        print(f"Всего: {total}")


if __name__ == "__main__":
    main()

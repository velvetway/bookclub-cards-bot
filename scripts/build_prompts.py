#!/usr/bin/env python3
"""Собирает промпты карточек из prompts/scenes.json.

Источник один — scenes.json (общий стиль плюс сцена под смысл каждой карты).
Отсюда получаются два файла:
  prompts/card_prompts.md   — читать и копировать в Gemini руками
  prompts/card_prompts.json — если генерить пачкой через API

    python scripts/build_prompts.py
"""

from __future__ import annotations

import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
SCENES = BASE_DIR / "prompts" / "scenes.json"
OUT_MD = BASE_DIR / "prompts" / "card_prompts.md"
OUT_JSON = BASE_DIR / "prompts" / "card_prompts.json"

TYPE_BY_PREFIX = {"OPT": "Оптика", "INS": "Врезка", "RAT": "К оценке"}

HEADER = """# Промпты для карточек

31 карта: у каждой свой кот и своя локация, общая — только манера рисунка.
Сгенерировано скриптом `scripts/build_prompts.py` из `prompts/scenes.json` —
правь коты и сцены там, а не здесь.

## Как пользоваться

1. Генерируешь картинку по промпту карты. Формат квадратный, 1:1.
2. Кладёшь результат в `data/cards/raw/` под именем кода: `OPT-01.png`, `INS-07.png`.
3. `python scripts/make_cards.py` — скрипт впечатает название карты в нижнюю
   полосу и сложит готовое в `data/cards/`. Бот сам подхватит файлы по коду.

Название печатается кодом, а не моделью: кириллицу генераторы пишут криво и
по-разному от карты к карте, а подпись должна быть одинаковой во всей колоде.
Поэтому в промптах прямо запрещён любой текст, а низ кадра просят оставить
спокойным — туда ляжет подпись.

## Что различается, а что нет

Различается: кот (окрас, порода, возраст, характер — под смысл карты),
локация, палитра, время суток, погода. Чёрный прокурор в холодном зале суда и
рыжий подросток в летнем саду — это нормально и так задумано.

Совпадает: манера рисунка. Тёплая живописная иллюстрация со сказочным
реализмом, мягкий свет, боке, пылинки в воздухе, проработанная шерсть,
приглушённая винтажная цветокоррекция. Эта часть вклеена в каждый промпт
дословно — её лучше не переписывать от карты к карте.

## Если колода всё же расползается по стилю

- Генерируй всё в одном чате одной моделью, не меняя формулировку стиля.
- Возьми одну удачную карту как референс и проси «та же манера рисунка,
  другой кот и другое место» — модели держат стиль лучше, чем персонажа.
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


def main() -> None:
    data = json.loads(SCENES.read_text(encoding="utf-8"))
    style = data["style"]
    common = f"{style['look']}. {style['variation']}. {style['frame']}"

    lines = [
        HEADER.format(style=common, negative=style["negative"]),
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

    OUT_MD.write_text("\n".join(lines), encoding="utf-8")
    OUT_JSON.write_text(
        json.dumps(bundle, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"Готово: {len(bundle)} промптов → {OUT_MD.name}, {OUT_JSON.name}")


if __name__ == "__main__":
    main()

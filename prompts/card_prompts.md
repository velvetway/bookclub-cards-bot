# Промпты для карточек

31 карта, один котёнок-маскот на всех, единый стиль. Сгенерировано скриптом
`scripts/build_prompts.py` из `prompts/scenes.json` — правь сцены там, а не здесь.

## Как пользоваться

1. Генерируешь картинку по промпту карты. Формат квадратный, 1:1.
2. Кладёшь результат в `data/cards/raw/` под именем кода: `OPT-01.png`, `INS-07.png`.
3. `python scripts/make_cards.py` — скрипт впечатает название карты в нижнюю
   полосу и сложит готовое в `data/cards/`. Бот сам подхватит файлы по коду.

Название печатается кодом, а не моделью: кириллицу генераторы пишут криво и
по-разному от карты к карте, а подпись должна быть одинаковой во всей колоде.
Поэтому в промптах прямо запрещён любой текст, а низ кадра просят оставить
спокойным — туда ляжет подпись.

## Чтобы колода выглядела одной колодой

- Генерируй все карты в одном чате одной моделью, не меняя формулировку стиля.
- Если модель умеет держать персонажа (референс или seed) — покажи ей первую
  удачную картинку и проси «тот же котёнок» для остальных.
- Проверяй низ кадра: если туда попало что-то важное, перегенерируй, иначе
  подпись ляжет поверх.

## Стиль

Общая часть, она уже вклеена в каждый промпт ниже:

```
the same recurring mascot in every card: a small brown mackerel tabby kitten with big round green eyes, a white chest and white paws, soft plush fur, gentle and endearing rather than wild. warm painterly digital illustration, cozy storybook realism, soft golden light, shallow depth of field with creamy bokeh, floating dust motes and tiny sparkles, finely detailed fur, muted vintage palette of amber, honey, deep green and worn paper, antique books and candle or lamp glow. square 1:1 composition, the kitten centered in the upper two thirds, the bottom fifth of the frame kept calm, darker and uncluttered so a caption can be placed there later
```

Негативная часть:

```
no text, no letters, no words, no numbers, no watermark, no signature, no logo, no frame border, no people, not photorealistic, no harsh contrast, no neon colors
```


---

## Оптика

### OPT-01 · Адвокат

```
the kitten stands behind a small wooden lectern in a tiny lawyer's robe with a white lace jabot, one paw raised in an earnest defending gesture, an open book in front of it, warm library light behind. the same recurring mascot in every card: a small brown mackerel tabby kitten with big round green eyes, a white chest and white paws, soft plush fur, gentle and endearing rather than wild. warm painterly digital illustration, cozy storybook realism, soft golden light, shallow depth of field with creamy bokeh, floating dust motes and tiny sparkles, finely detailed fur, muted vintage palette of amber, honey, deep green and worn paper, antique books and candle or lamp glow. square 1:1 composition, the kitten centered in the upper two thirds, the bottom fifth of the frame kept calm, darker and uncluttered so a caption can be placed there later. no text, no letters, no words, no numbers, no watermark, no signature, no logo, no frame border, no people, not photorealistic, no harsh contrast, no neon colors
```

### OPT-02 · Прокурор

```
the kitten sits very straight in a dark robe, one paw pointing accusingly at a thick open book lying before it, a small brass bell and a rolled scroll nearby, dramatic side light. the same recurring mascot in every card: a small brown mackerel tabby kitten with big round green eyes, a white chest and white paws, soft plush fur, gentle and endearing rather than wild. warm painterly digital illustration, cozy storybook realism, soft golden light, shallow depth of field with creamy bokeh, floating dust motes and tiny sparkles, finely detailed fur, muted vintage palette of amber, honey, deep green and worn paper, antique books and candle or lamp glow. square 1:1 composition, the kitten centered in the upper two thirds, the bottom fifth of the frame kept calm, darker and uncluttered so a caption can be placed there later. no text, no letters, no words, no numbers, no watermark, no signature, no logo, no frame border, no people, not photorealistic, no harsh contrast, no neon colors
```

### OPT-03 · Только мир

```
the kitten sits on an open book and gazes out at a wide landscape of hills and mist that rises out of the pages like a diorama, air and space, the story itself out of focus. the same recurring mascot in every card: a small brown mackerel tabby kitten with big round green eyes, a white chest and white paws, soft plush fur, gentle and endearing rather than wild. warm painterly digital illustration, cozy storybook realism, soft golden light, shallow depth of field with creamy bokeh, floating dust motes and tiny sparkles, finely detailed fur, muted vintage palette of amber, honey, deep green and worn paper, antique books and candle or lamp glow. square 1:1 composition, the kitten centered in the upper two thirds, the bottom fifth of the frame kept calm, darker and uncluttered so a caption can be placed there later. no text, no letters, no words, no numbers, no watermark, no signature, no logo, no frame border, no people, not photorealistic, no harsh contrast, no neon colors
```

### OPT-04 · Только сборка

```
the kitten as a tiny watchmaker with a jeweller's loupe over one eye, taking apart a book that is built like a clockwork mechanism, brass gears and springs laid out neatly on the desk. the same recurring mascot in every card: a small brown mackerel tabby kitten with big round green eyes, a white chest and white paws, soft plush fur, gentle and endearing rather than wild. warm painterly digital illustration, cozy storybook realism, soft golden light, shallow depth of field with creamy bokeh, floating dust motes and tiny sparkles, finely detailed fur, muted vintage palette of amber, honey, deep green and worn paper, antique books and candle or lamp glow. square 1:1 composition, the kitten centered in the upper two thirds, the bottom fifth of the frame kept calm, darker and uncluttered so a caption can be placed there later. no text, no letters, no words, no numbers, no watermark, no signature, no logo, no frame border, no people, not photorealistic, no harsh contrast, no neon colors
```

### OPT-05 · Одна сцена

```
the kitten holds a small lantern over one single page, a narrow warm beam lighting one paragraph while the rest of the room falls into soft darkness. the same recurring mascot in every card: a small brown mackerel tabby kitten with big round green eyes, a white chest and white paws, soft plush fur, gentle and endearing rather than wild. warm painterly digital illustration, cozy storybook realism, soft golden light, shallow depth of field with creamy bokeh, floating dust motes and tiny sparkles, finely detailed fur, muted vintage palette of amber, honey, deep green and worn paper, antique books and candle or lamp glow. square 1:1 composition, the kitten centered in the upper two thirds, the bottom fifth of the frame kept calm, darker and uncluttered so a caption can be placed there later. no text, no letters, no words, no numbers, no watermark, no signature, no logo, no frame border, no people, not photorealistic, no harsh contrast, no neon colors
```

### OPT-06 · Через другую книгу

```
the kitten sits between two open books turned toward each other, glancing from one to the other, a thin glowing thread arcs between the two volumes like a bridge. the same recurring mascot in every card: a small brown mackerel tabby kitten with big round green eyes, a white chest and white paws, soft plush fur, gentle and endearing rather than wild. warm painterly digital illustration, cozy storybook realism, soft golden light, shallow depth of field with creamy bokeh, floating dust motes and tiny sparkles, finely detailed fur, muted vintage palette of amber, honey, deep green and worn paper, antique books and candle or lamp glow. square 1:1 composition, the kitten centered in the upper two thirds, the bottom fifth of the frame kept calm, darker and uncluttered so a caption can be placed there later. no text, no letters, no words, no numbers, no watermark, no signature, no logo, no frame border, no people, not photorealistic, no harsh contrast, no neon colors
```

## Врезка

### INS-01 · Своя сцена

```
the kitten sits inside a small glowing stage that grows out of an open book, tiny paper scenery and curtains around it, one scene kept alive after the story ended. the same recurring mascot in every card: a small brown mackerel tabby kitten with big round green eyes, a white chest and white paws, soft plush fur, gentle and endearing rather than wild. warm painterly digital illustration, cozy storybook realism, soft golden light, shallow depth of field with creamy bokeh, floating dust motes and tiny sparkles, finely detailed fur, muted vintage palette of amber, honey, deep green and worn paper, antique books and candle or lamp glow. square 1:1 composition, the kitten centered in the upper two thirds, the bottom fifth of the frame kept calm, darker and uncluttered so a caption can be placed there later. no text, no letters, no words, no numbers, no watermark, no signature, no logo, no frame border, no people, not photorealistic, no harsh contrast, no neon colors
```

### INS-02 · Выделенное

```
the kitten holds up an open book with one line marked by a bright silk ribbon bookmark, mouth slightly open as if reading that line aloud, warm candlelight. the same recurring mascot in every card: a small brown mackerel tabby kitten with big round green eyes, a white chest and white paws, soft plush fur, gentle and endearing rather than wild. warm painterly digital illustration, cozy storybook realism, soft golden light, shallow depth of field with creamy bokeh, floating dust motes and tiny sparkles, finely detailed fur, muted vintage palette of amber, honey, deep green and worn paper, antique books and candle or lamp glow. square 1:1 composition, the kitten centered in the upper two thirds, the bottom fifth of the frame kept calm, darker and uncluttered so a caption can be placed there later. no text, no letters, no words, no numbers, no watermark, no signature, no logo, no frame border, no people, not photorealistic, no harsh contrast, no neon colors
```

### INS-03 · Точка входа

```
the kitten steps through a page that has opened like a door, forepaws already inside the glowing doorway, the rest of the library dim behind it. the same recurring mascot in every card: a small brown mackerel tabby kitten with big round green eyes, a white chest and white paws, soft plush fur, gentle and endearing rather than wild. warm painterly digital illustration, cozy storybook realism, soft golden light, shallow depth of field with creamy bokeh, floating dust motes and tiny sparkles, finely detailed fur, muted vintage palette of amber, honey, deep green and worn paper, antique books and candle or lamp glow. square 1:1 composition, the kitten centered in the upper two thirds, the bottom fifth of the frame kept calm, darker and uncluttered so a caption can be placed there later. no text, no letters, no words, no numbers, no watermark, no signature, no logo, no frame border, no people, not photorealistic, no harsh contrast, no neon colors
```

### INS-04 · Тяжёлое место

```
the kitten climbs a steep page that rises like a paper mountain, claws dug into the paper, ears back with effort, cold blue light at the summit and warm light below. the same recurring mascot in every card: a small brown mackerel tabby kitten with big round green eyes, a white chest and white paws, soft plush fur, gentle and endearing rather than wild. warm painterly digital illustration, cozy storybook realism, soft golden light, shallow depth of field with creamy bokeh, floating dust motes and tiny sparkles, finely detailed fur, muted vintage palette of amber, honey, deep green and worn paper, antique books and candle or lamp glow. square 1:1 composition, the kitten centered in the upper two thirds, the bottom fifth of the frame kept calm, darker and uncluttered so a caption can be placed there later. no text, no letters, no words, no numbers, no watermark, no signature, no logo, no frame border, no people, not photorealistic, no harsh contrast, no neon colors
```

### INS-05 · Свой человек

```
the kitten leans its cheek against a small figure that steps out of the book, both in the same warm light, quiet recognition, soft golden glow around the pair. the same recurring mascot in every card: a small brown mackerel tabby kitten with big round green eyes, a white chest and white paws, soft plush fur, gentle and endearing rather than wild. warm painterly digital illustration, cozy storybook realism, soft golden light, shallow depth of field with creamy bokeh, floating dust motes and tiny sparkles, finely detailed fur, muted vintage palette of amber, honey, deep green and worn paper, antique books and candle or lamp glow. square 1:1 composition, the kitten centered in the upper two thirds, the bottom fifth of the frame kept calm, darker and uncluttered so a caption can be placed there later. no text, no letters, no words, no numbers, no watermark, no signature, no logo, no frame border, no people, not photorealistic, no harsh contrast, no neon colors
```

### INS-06 · Чужой

```
the kitten turns away with flattened ears and a puffed tail from a tall shadowy figure rising out of the open pages, cold light on the figure, warm light on the kitten. the same recurring mascot in every card: a small brown mackerel tabby kitten with big round green eyes, a white chest and white paws, soft plush fur, gentle and endearing rather than wild. warm painterly digital illustration, cozy storybook realism, soft golden light, shallow depth of field with creamy bokeh, floating dust motes and tiny sparkles, finely detailed fur, muted vintage palette of amber, honey, deep green and worn paper, antique books and candle or lamp glow. square 1:1 composition, the kitten centered in the upper two thirds, the bottom fifth of the frame kept calm, darker and uncluttered so a caption can be placed there later. no text, no letters, no words, no numbers, no watermark, no signature, no logo, no frame border, no people, not photorealistic, no harsh contrast, no neon colors
```

### INS-07 · Второстепенный

```
the kitten peers closely at a tiny mouse character standing at the very edge of the page margin, the big main characters blurred in the background, magnifying glass in one paw. the same recurring mascot in every card: a small brown mackerel tabby kitten with big round green eyes, a white chest and white paws, soft plush fur, gentle and endearing rather than wild. warm painterly digital illustration, cozy storybook realism, soft golden light, shallow depth of field with creamy bokeh, floating dust motes and tiny sparkles, finely detailed fur, muted vintage palette of amber, honey, deep green and worn paper, antique books and candle or lamp glow. square 1:1 composition, the kitten centered in the upper two thirds, the bottom fifth of the frame kept calm, darker and uncluttered so a caption can be placed there later. no text, no letters, no words, no numbers, no watermark, no signature, no logo, no frame border, no people, not photorealistic, no harsh contrast, no neon colors
```

### INS-08 · Где перестал верить

```
the kitten squints skeptically with one eyebrow raised at a page whose lines have started to ripple and come loose, a few paper fragments floating up. the same recurring mascot in every card: a small brown mackerel tabby kitten with big round green eyes, a white chest and white paws, soft plush fur, gentle and endearing rather than wild. warm painterly digital illustration, cozy storybook realism, soft golden light, shallow depth of field with creamy bokeh, floating dust motes and tiny sparkles, finely detailed fur, muted vintage palette of amber, honey, deep green and worn paper, antique books and candle or lamp glow. square 1:1 composition, the kitten centered in the upper two thirds, the bottom fifth of the frame kept calm, darker and uncluttered so a caption can be placed there later. no text, no letters, no words, no numbers, no watermark, no signature, no logo, no frame border, no people, not photorealistic, no harsh contrast, no neon colors
```

### INS-09 · Ножницы

```
the kitten holds a pair of small brass scissors and carefully cuts a piece out of a page, paper cutouts scattered on the desk around it. the same recurring mascot in every card: a small brown mackerel tabby kitten with big round green eyes, a white chest and white paws, soft plush fur, gentle and endearing rather than wild. warm painterly digital illustration, cozy storybook realism, soft golden light, shallow depth of field with creamy bokeh, floating dust motes and tiny sparkles, finely detailed fur, muted vintage palette of amber, honey, deep green and worn paper, antique books and candle or lamp glow. square 1:1 composition, the kitten centered in the upper two thirds, the bottom fifth of the frame kept calm, darker and uncluttered so a caption can be placed there later. no text, no letters, no words, no numbers, no watermark, no signature, no logo, no frame border, no people, not photorealistic, no harsh contrast, no neon colors
```

### INS-10 · Дыра

```
the kitten leans over a round hole burned through the middle of an open book, warm light pouring up out of the hole onto its curious face. the same recurring mascot in every card: a small brown mackerel tabby kitten with big round green eyes, a white chest and white paws, soft plush fur, gentle and endearing rather than wild. warm painterly digital illustration, cozy storybook realism, soft golden light, shallow depth of field with creamy bokeh, floating dust motes and tiny sparkles, finely detailed fur, muted vintage palette of amber, honey, deep green and worn paper, antique books and candle or lamp glow. square 1:1 composition, the kitten centered in the upper two thirds, the bottom fifth of the frame kept calm, darker and uncluttered so a caption can be placed there later. no text, no letters, no words, no numbers, no watermark, no signature, no logo, no frame border, no people, not photorealistic, no harsh contrast, no neon colors
```

### INS-11 · Лишний

```
the kitten lifts one small paper figure out of a crowded pop-up book and sets it aside on the desk, the scene behind now calmer and more balanced. the same recurring mascot in every card: a small brown mackerel tabby kitten with big round green eyes, a white chest and white paws, soft plush fur, gentle and endearing rather than wild. warm painterly digital illustration, cozy storybook realism, soft golden light, shallow depth of field with creamy bokeh, floating dust motes and tiny sparkles, finely detailed fur, muted vintage palette of amber, honey, deep green and worn paper, antique books and candle or lamp glow. square 1:1 composition, the kitten centered in the upper two thirds, the bottom fifth of the frame kept calm, darker and uncluttered so a caption can be placed there later. no text, no letters, no words, no numbers, no watermark, no signature, no logo, no frame border, no people, not photorealistic, no harsh contrast, no neon colors
```

### INS-12 · Другой финал

```
the kitten writes on a fresh last page with a long quill pen, two or three alternative paper endings pinned above like laundry on a line. the same recurring mascot in every card: a small brown mackerel tabby kitten with big round green eyes, a white chest and white paws, soft plush fur, gentle and endearing rather than wild. warm painterly digital illustration, cozy storybook realism, soft golden light, shallow depth of field with creamy bokeh, floating dust motes and tiny sparkles, finely detailed fur, muted vintage palette of amber, honey, deep green and worn paper, antique books and candle or lamp glow. square 1:1 composition, the kitten centered in the upper two thirds, the bottom fifth of the frame kept calm, darker and uncluttered so a caption can be placed there later. no text, no letters, no words, no numbers, no watermark, no signature, no logo, no frame border, no people, not photorealistic, no harsh contrast, no neon colors
```

### INS-13 · Мотив

```
the kitten holds a magnifying glass over a small figure's chest where a warm glowing clockwork heart is visible, everything else in soft shadow. the same recurring mascot in every card: a small brown mackerel tabby kitten with big round green eyes, a white chest and white paws, soft plush fur, gentle and endearing rather than wild. warm painterly digital illustration, cozy storybook realism, soft golden light, shallow depth of field with creamy bokeh, floating dust motes and tiny sparkles, finely detailed fur, muted vintage palette of amber, honey, deep green and worn paper, antique books and candle or lamp glow. square 1:1 composition, the kitten centered in the upper two thirds, the bottom fifth of the frame kept calm, darker and uncluttered so a caption can be placed there later. no text, no letters, no words, no numbers, no watermark, no signature, no logo, no frame border, no people, not photorealistic, no harsh contrast, no neon colors
```

### INS-14 · Виноват

```
the kitten as a small detective with a lantern, following a trail of inky paw prints across an open page, deerstalker cap slightly too big. the same recurring mascot in every card: a small brown mackerel tabby kitten with big round green eyes, a white chest and white paws, soft plush fur, gentle and endearing rather than wild. warm painterly digital illustration, cozy storybook realism, soft golden light, shallow depth of field with creamy bokeh, floating dust motes and tiny sparkles, finely detailed fur, muted vintage palette of amber, honey, deep green and worn paper, antique books and candle or lamp glow. square 1:1 composition, the kitten centered in the upper two thirds, the bottom fifth of the frame kept calm, darker and uncluttered so a caption can be placed there later. no text, no letters, no words, no numbers, no watermark, no signature, no logo, no frame border, no people, not photorealistic, no harsh contrast, no neon colors
```

### INS-15 · После финала

```
the kitten sits on a closed book by a window, looking into the distance at dusk, one last warm ray across its face, the story already over. the same recurring mascot in every card: a small brown mackerel tabby kitten with big round green eyes, a white chest and white paws, soft plush fur, gentle and endearing rather than wild. warm painterly digital illustration, cozy storybook realism, soft golden light, shallow depth of field with creamy bokeh, floating dust motes and tiny sparkles, finely detailed fur, muted vintage palette of amber, honey, deep green and worn paper, antique books and candle or lamp glow. square 1:1 composition, the kitten centered in the upper two thirds, the bottom fifth of the frame kept calm, darker and uncluttered so a caption can be placed there later. no text, no letters, no words, no numbers, no watermark, no signature, no logo, no frame border, no people, not photorealistic, no harsh contrast, no neon colors
```

### INS-16 · Кому дал бы прочитать

```
the kitten pushes a book across a table toward another sleepy kitten, both paws on the cover, a warm and generous gesture. the same recurring mascot in every card: a small brown mackerel tabby kitten with big round green eyes, a white chest and white paws, soft plush fur, gentle and endearing rather than wild. warm painterly digital illustration, cozy storybook realism, soft golden light, shallow depth of field with creamy bokeh, floating dust motes and tiny sparkles, finely detailed fur, muted vintage palette of amber, honey, deep green and worn paper, antique books and candle or lamp glow. square 1:1 composition, the kitten centered in the upper two thirds, the bottom fifth of the frame kept calm, darker and uncluttered so a caption can be placed there later. no text, no letters, no words, no numbers, no watermark, no signature, no logo, no frame border, no people, not photorealistic, no harsh contrast, no neon colors
```

### INS-17 · Название

```
the kitten tilts its head at a standing book cover that carries only an empty ornate blank plate where a title would be, curious and slightly doubtful. the same recurring mascot in every card: a small brown mackerel tabby kitten with big round green eyes, a white chest and white paws, soft plush fur, gentle and endearing rather than wild. warm painterly digital illustration, cozy storybook realism, soft golden light, shallow depth of field with creamy bokeh, floating dust motes and tiny sparkles, finely detailed fur, muted vintage palette of amber, honey, deep green and worn paper, antique books and candle or lamp glow. square 1:1 composition, the kitten centered in the upper two thirds, the bottom fifth of the frame kept calm, darker and uncluttered so a caption can be placed there later. no text, no letters, no words, no numbers, no watermark, no signature, no logo, no frame border, no people, not photorealistic, no harsh contrast, no neon colors
```

### INS-18 · На чём держится

```
the kitten stands on a small structure built of four stacked book columns holding up a floating open volume, testing one column with a careful paw. the same recurring mascot in every card: a small brown mackerel tabby kitten with big round green eyes, a white chest and white paws, soft plush fur, gentle and endearing rather than wild. warm painterly digital illustration, cozy storybook realism, soft golden light, shallow depth of field with creamy bokeh, floating dust motes and tiny sparkles, finely detailed fur, muted vintage palette of amber, honey, deep green and worn paper, antique books and candle or lamp glow. square 1:1 composition, the kitten centered in the upper two thirds, the bottom fifth of the frame kept calm, darker and uncluttered so a caption can be placed there later. no text, no letters, no words, no numbers, no watermark, no signature, no logo, no frame border, no people, not photorealistic, no harsh contrast, no neon colors
```

### INS-19 · Одна эмоция

```
the kitten hugs a book that glows with one single warm color, the whole room lit by that one hue, the kitten's face carrying that one feeling. the same recurring mascot in every card: a small brown mackerel tabby kitten with big round green eyes, a white chest and white paws, soft plush fur, gentle and endearing rather than wild. warm painterly digital illustration, cozy storybook realism, soft golden light, shallow depth of field with creamy bokeh, floating dust motes and tiny sparkles, finely detailed fur, muted vintage palette of amber, honey, deep green and worn paper, antique books and candle or lamp glow. square 1:1 composition, the kitten centered in the upper two thirds, the bottom fifth of the frame kept calm, darker and uncluttered so a caption can be placed there later. no text, no letters, no words, no numbers, no watermark, no signature, no logo, no frame border, no people, not photorealistic, no harsh contrast, no neon colors
```

### INS-20 · Разговор

```
two kittens of the same breed sit facing each other across an open book on a table, small soft speech clouds of warm steam rising between them. the same recurring mascot in every card: a small brown mackerel tabby kitten with big round green eyes, a white chest and white paws, soft plush fur, gentle and endearing rather than wild. warm painterly digital illustration, cozy storybook realism, soft golden light, shallow depth of field with creamy bokeh, floating dust motes and tiny sparkles, finely detailed fur, muted vintage palette of amber, honey, deep green and worn paper, antique books and candle or lamp glow. square 1:1 composition, the kitten centered in the upper two thirds, the bottom fifth of the frame kept calm, darker and uncluttered so a caption can be placed there later. no text, no letters, no words, no numbers, no watermark, no signature, no logo, no frame border, no people, not photorealistic, no harsh contrast, no neon colors
```

## К оценке

### RAT-01 · Цена балла

```
the kitten watches a small brass balance scale, one pan holding a single gold coin, the other holding a thin book, weighing them with a serious little face. the same recurring mascot in every card: a small brown mackerel tabby kitten with big round green eyes, a white chest and white paws, soft plush fur, gentle and endearing rather than wild. warm painterly digital illustration, cozy storybook realism, soft golden light, shallow depth of field with creamy bokeh, floating dust motes and tiny sparkles, finely detailed fur, muted vintage palette of amber, honey, deep green and worn paper, antique books and candle or lamp glow. square 1:1 composition, the kitten centered in the upper two thirds, the bottom fifth of the frame kept calm, darker and uncluttered so a caption can be placed there later. no text, no letters, no words, no numbers, no watermark, no signature, no logo, no frame border, no people, not photorealistic, no harsh contrast, no neon colors
```

### RAT-02 · Порог

```
the kitten stretches one paw up toward the next stone step of a warm-lit staircase made of stacked books, almost reaching it. the same recurring mascot in every card: a small brown mackerel tabby kitten with big round green eyes, a white chest and white paws, soft plush fur, gentle and endearing rather than wild. warm painterly digital illustration, cozy storybook realism, soft golden light, shallow depth of field with creamy bokeh, floating dust motes and tiny sparkles, finely detailed fur, muted vintage palette of amber, honey, deep green and worn paper, antique books and candle or lamp glow. square 1:1 composition, the kitten centered in the upper two thirds, the bottom fifth of the frame kept calm, darker and uncluttered so a caption can be placed there later. no text, no letters, no words, no numbers, no watermark, no signature, no logo, no frame border, no people, not photorealistic, no harsh contrast, no neon colors
```

### RAT-03 · Не моё

```
the kitten tries on a pair of round spectacles that are far too large, sliding off its nose, setting them aside with a polite and slightly rueful expression. the same recurring mascot in every card: a small brown mackerel tabby kitten with big round green eyes, a white chest and white paws, soft plush fur, gentle and endearing rather than wild. warm painterly digital illustration, cozy storybook realism, soft golden light, shallow depth of field with creamy bokeh, floating dust motes and tiny sparkles, finely detailed fur, muted vintage palette of amber, honey, deep green and worn paper, antique books and candle or lamp glow. square 1:1 composition, the kitten centered in the upper two thirds, the bottom fifth of the frame kept calm, darker and uncluttered so a caption can be placed there later. no text, no letters, no words, no numbers, no watermark, no signature, no logo, no frame border, no people, not photorealistic, no harsh contrast, no neon colors
```

### RAT-04 · Через год

```
the kitten sits beside a large hourglass, its warm reflection in the glass shown as a grown cat, an open book between them, sand falling slowly. the same recurring mascot in every card: a small brown mackerel tabby kitten with big round green eyes, a white chest and white paws, soft plush fur, gentle and endearing rather than wild. warm painterly digital illustration, cozy storybook realism, soft golden light, shallow depth of field with creamy bokeh, floating dust motes and tiny sparkles, finely detailed fur, muted vintage palette of amber, honey, deep green and worn paper, antique books and candle or lamp glow. square 1:1 composition, the kitten centered in the upper two thirds, the bottom fifth of the frame kept calm, darker and uncluttered so a caption can be placed there later. no text, no letters, no words, no numbers, no watermark, no signature, no logo, no frame border, no people, not photorealistic, no harsh contrast, no neon colors
```

### RAT-05 · Накинутое

```
the kitten quietly places one extra golden star on top of a small stack of stars beside a book, glancing aside a little guiltily. the same recurring mascot in every card: a small brown mackerel tabby kitten with big round green eyes, a white chest and white paws, soft plush fur, gentle and endearing rather than wild. warm painterly digital illustration, cozy storybook realism, soft golden light, shallow depth of field with creamy bokeh, floating dust motes and tiny sparkles, finely detailed fur, muted vintage palette of amber, honey, deep green and worn paper, antique books and candle or lamp glow. square 1:1 composition, the kitten centered in the upper two thirds, the bottom fifth of the frame kept calm, darker and uncluttered so a caption can be placed there later. no text, no letters, no words, no numbers, no watermark, no signature, no logo, no frame border, no people, not photorealistic, no harsh contrast, no neon colors
```

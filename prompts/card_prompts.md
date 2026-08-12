# Промпты для карточек

31 карта: у каждой свой кот и своя локация, общая — только манера рисунка.

Сгенерировано скриптом `scripts/build_prompts.py` из `prompts/scenes.json` —
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
consistent rendering across the whole deck: warm painterly digital illustration with storybook realism, soft natural light, shallow depth of field with creamy bokeh, floating dust motes and faint sparkles, finely detailed fur, gentle vintage color grading, visible painterly brushwork. palette, location and time of day change from card to card; only the painting technique, level of detail and the cosy mood stay the same. square 1:1 composition, the cat in the upper two thirds, the bottom fifth of the frame kept calm, darker and uncluttered so a caption can be placed there later
```

Негативная часть:

```
no text, no letters, no words, no numbers, no watermark, no signature, no logo, no frame border, no people, not photorealistic, no harsh contrast, no neon colors
```


---

## Оптика

### OPT-01 · Адвокат

```
a dignified middle-aged blue British shorthair with round amber eyes and a serious, kind face, wearing a small black robe with a white lace jabot, standing behind a wooden lectern in a panelled courtroom, one paw raised in an earnest defending gesture, an open book in front of it, warm brass lamps and deep oak tones. consistent rendering across the whole deck: warm painterly digital illustration with storybook realism, soft natural light, shallow depth of field with creamy bokeh, floating dust motes and faint sparkles, finely detailed fur, gentle vintage color grading, visible painterly brushwork. palette, location and time of day change from card to card; only the painting technique, level of detail and the cosy mood stay the same. square 1:1 composition, the cat in the upper two thirds, the bottom fifth of the frame kept calm, darker and uncluttered so a caption can be placed there later. no text, no letters, no words, no numbers, no watermark, no signature, no logo, no frame border, no people, not photorealistic, no harsh contrast, no neon colors
```

### OPT-02 · Прокурор

```
a lean black cat with sharp yellow eyes and a stern narrow face, in a dark severe robe, sitting bolt upright at a cold marble table in a high stone courtroom, one paw pointing accusingly at a thick open book, pale grey daylight from a tall window, cool blue-grey palette. consistent rendering across the whole deck: warm painterly digital illustration with storybook realism, soft natural light, shallow depth of field with creamy bokeh, floating dust motes and faint sparkles, finely detailed fur, gentle vintage color grading, visible painterly brushwork. palette, location and time of day change from card to card; only the painting technique, level of detail and the cosy mood stay the same. square 1:1 composition, the cat in the upper two thirds, the bottom fifth of the frame kept calm, darker and uncluttered so a caption can be placed there later. no text, no letters, no words, no numbers, no watermark, no signature, no logo, no frame border, no people, not photorealistic, no harsh contrast, no neon colors
```

### OPT-03 · Только мир

```
a fluffy white long-haired cat with pale blue eyes and a dreamy, faraway expression, sitting in the lantern room of a lighthouse, gazing out at a wide misty coastline of cliffs and sea, an open book forgotten under its paws, silver and seafoam palette, cool morning air. consistent rendering across the whole deck: warm painterly digital illustration with storybook realism, soft natural light, shallow depth of field with creamy bokeh, floating dust motes and faint sparkles, finely detailed fur, gentle vintage color grading, visible painterly brushwork. palette, location and time of day change from card to card; only the painting technique, level of detail and the cosy mood stay the same. square 1:1 composition, the cat in the upper two thirds, the bottom fifth of the frame kept calm, darker and uncluttered so a caption can be placed there later. no text, no letters, no words, no numbers, no watermark, no signature, no logo, no frame border, no people, not photorealistic, no harsh contrast, no neon colors
```

### OPT-04 · Только сборка

```
a ginger tabby tom in tiny round spectacles, focused and methodical, fur slightly untidy, in a watchmaker's workshop, taking apart a book built like clockwork, brass gears and springs laid out on green felt, jeweller's loupe, warm amber lamplight and glinting metal. consistent rendering across the whole deck: warm painterly digital illustration with storybook realism, soft natural light, shallow depth of field with creamy bokeh, floating dust motes and faint sparkles, finely detailed fur, gentle vintage color grading, visible painterly brushwork. palette, location and time of day change from card to card; only the painting technique, level of detail and the cosy mood stay the same. square 1:1 composition, the cat in the upper two thirds, the bottom fifth of the frame kept calm, darker and uncluttered so a caption can be placed there later. no text, no letters, no words, no numbers, no watermark, no signature, no logo, no frame border, no people, not photorealistic, no harsh contrast, no neon colors
```

### OPT-05 · Одна сцена

```
a small tuxedo kitten, black with a white chest and white socks, wide-eyed and curious, alone in a dark dusty attic, holding a small lantern over one single page, one narrow warm beam from the skylight, everything else deep shadow and silhouettes of old furniture. consistent rendering across the whole deck: warm painterly digital illustration with storybook realism, soft natural light, shallow depth of field with creamy bokeh, floating dust motes and faint sparkles, finely detailed fur, gentle vintage color grading, visible painterly brushwork. palette, location and time of day change from card to card; only the painting technique, level of detail and the cosy mood stay the same. square 1:1 composition, the cat in the upper two thirds, the bottom fifth of the frame kept calm, darker and uncluttered so a caption can be placed there later. no text, no letters, no words, no numbers, no watermark, no signature, no logo, no frame border, no people, not photorealistic, no harsh contrast, no neon colors
```

### OPT-06 · Через другую книгу

```
a clever tortoiseshell cat with mismatched patches and a thoughtful tilt of the head, in the aisle of an old bookshop between two tall shelves, two open books turned toward each other, a thin glowing thread arcing between them like a bridge, dusty green and burgundy spines. consistent rendering across the whole deck: warm painterly digital illustration with storybook realism, soft natural light, shallow depth of field with creamy bokeh, floating dust motes and faint sparkles, finely detailed fur, gentle vintage color grading, visible painterly brushwork. palette, location and time of day change from card to card; only the painting technique, level of detail and the cosy mood stay the same. square 1:1 composition, the cat in the upper two thirds, the bottom fifth of the frame kept calm, darker and uncluttered so a caption can be placed there later. no text, no letters, no words, no numbers, no watermark, no signature, no logo, no frame border, no people, not photorealistic, no harsh contrast, no neon colors
```

## Врезка

### INS-01 · Своя сцена

```
a cream-coloured fluffy kitten with big hopeful eyes, sitting inside a small paper toy theatre that grows out of an open book in a child's room, tiny cut-out scenery and velvet curtains, warm pink and honey evening light. consistent rendering across the whole deck: warm painterly digital illustration with storybook realism, soft natural light, shallow depth of field with creamy bokeh, floating dust motes and faint sparkles, finely detailed fur, gentle vintage color grading, visible painterly brushwork. palette, location and time of day change from card to card; only the painting technique, level of detail and the cosy mood stay the same. square 1:1 composition, the cat in the upper two thirds, the bottom fifth of the frame kept calm, darker and uncluttered so a caption can be placed there later. no text, no letters, no words, no numbers, no watermark, no signature, no logo, no frame border, no people, not photorealistic, no harsh contrast, no neon colors
```

### INS-02 · Выделенное

```
an elegant seal-point siamese with deep blue eyes and a solemn, formal manner, in a cosy drawing room by candlelight, holding up an open book with one line marked by a bright silk ribbon, mouth slightly open as if reading that line aloud, chestnut and candle-gold palette. consistent rendering across the whole deck: warm painterly digital illustration with storybook realism, soft natural light, shallow depth of field with creamy bokeh, floating dust motes and faint sparkles, finely detailed fur, gentle vintage color grading, visible painterly brushwork. palette, location and time of day change from card to card; only the painting technique, level of detail and the cosy mood stay the same. square 1:1 composition, the cat in the upper two thirds, the bottom fifth of the frame kept calm, darker and uncluttered so a caption can be placed there later. no text, no letters, no words, no numbers, no watermark, no signature, no logo, no frame border, no people, not photorealistic, no harsh contrast, no neon colors
```

### INS-03 · Точка входа

```
a lanky ginger adolescent cat, all legs and curiosity, in a summer garden, stepping through a page that has swung open like a green door in a hedge, forepaws already in the glowing doorway, fresh leaf-green and sunlit yellow. consistent rendering across the whole deck: warm painterly digital illustration with storybook realism, soft natural light, shallow depth of field with creamy bokeh, floating dust motes and faint sparkles, finely detailed fur, gentle vintage color grading, visible painterly brushwork. palette, location and time of day change from card to card; only the painting technique, level of detail and the cosy mood stay the same. square 1:1 composition, the cat in the upper two thirds, the bottom fifth of the frame kept calm, darker and uncluttered so a caption can be placed there later. no text, no letters, no words, no numbers, no watermark, no signature, no logo, no frame border, no people, not photorealistic, no harsh contrast, no neon colors
```

### INS-04 · Тяжёлое место

```
a sturdy grey norwegian forest cat with a thick winter ruff, determined and tired, climbing a steep mountainside made of folded paper pages, claws dug in, wind and thin snow, cold slate blue and white with one warm patch of light far below. consistent rendering across the whole deck: warm painterly digital illustration with storybook realism, soft natural light, shallow depth of field with creamy bokeh, floating dust motes and faint sparkles, finely detailed fur, gentle vintage color grading, visible painterly brushwork. palette, location and time of day change from card to card; only the painting technique, level of detail and the cosy mood stay the same. square 1:1 composition, the cat in the upper two thirds, the bottom fifth of the frame kept calm, darker and uncluttered so a caption can be placed there later. no text, no letters, no words, no numbers, no watermark, no signature, no logo, no frame border, no people, not photorealistic, no harsh contrast, no neon colors
```

### INS-05 · Свой человек

```
a soft calico cat with a warm, quietly happy face, curled by a fireplace under a woollen blanket, leaning its cheek against a small figure that has stepped out of the book, deep red and firelight orange, everything warm and close. consistent rendering across the whole deck: warm painterly digital illustration with storybook realism, soft natural light, shallow depth of field with creamy bokeh, floating dust motes and faint sparkles, finely detailed fur, gentle vintage color grading, visible painterly brushwork. palette, location and time of day change from card to card; only the painting technique, level of detail and the cosy mood stay the same. square 1:1 composition, the cat in the upper two thirds, the bottom fifth of the frame kept calm, darker and uncluttered so a caption can be placed there later. no text, no letters, no words, no numbers, no watermark, no signature, no logo, no frame border, no people, not photorealistic, no harsh contrast, no neon colors
```

### INS-06 · Чужой

```
a smoke-grey cat with flattened ears and a puffed tail, wary and tense, in a narrow dark corridor, backing away from a tall shadowy figure rising out of an open book through a half-open door, cold moonlight on the figure, one warm lamp behind the cat. consistent rendering across the whole deck: warm painterly digital illustration with storybook realism, soft natural light, shallow depth of field with creamy bokeh, floating dust motes and faint sparkles, finely detailed fur, gentle vintage color grading, visible painterly brushwork. palette, location and time of day change from card to card; only the painting technique, level of detail and the cosy mood stay the same. square 1:1 composition, the cat in the upper two thirds, the bottom fifth of the frame kept calm, darker and uncluttered so a caption can be placed there later. no text, no letters, no words, no numbers, no watermark, no signature, no logo, no frame border, no people, not photorealistic, no harsh contrast, no neon colors
```

### INS-07 · Второстепенный

```
a tiny abyssinian kitten with enormous ears, entirely absorbed, lying in tall summer meadow grass among daisies and dandelion clocks, peering through a magnifying glass at a very small mouse character standing at the edge of the page margin, bright green and sunlit gold, blurred wildflowers. consistent rendering across the whole deck: warm painterly digital illustration with storybook realism, soft natural light, shallow depth of field with creamy bokeh, floating dust motes and faint sparkles, finely detailed fur, gentle vintage color grading, visible painterly brushwork. palette, location and time of day change from card to card; only the painting technique, level of detail and the cosy mood stay the same. square 1:1 composition, the cat in the upper two thirds, the bottom fifth of the frame kept calm, darker and uncluttered so a caption can be placed there later. no text, no letters, no words, no numbers, no watermark, no signature, no logo, no frame border, no people, not photorealistic, no harsh contrast, no neon colors
```

### INS-08 · Где перестал верить

```
a grey mackerel tabby with one eyebrow raised and a distinctly skeptical squint, at a kitchen table with a cup of tea gone cold, looking at a page whose lines have started to ripple and come loose, a few paper fragments floating up, muted olive and cream, flat afternoon light. consistent rendering across the whole deck: warm painterly digital illustration with storybook realism, soft natural light, shallow depth of field with creamy bokeh, floating dust motes and faint sparkles, finely detailed fur, gentle vintage color grading, visible painterly brushwork. palette, location and time of day change from card to card; only the painting technique, level of detail and the cosy mood stay the same. square 1:1 composition, the cat in the upper two thirds, the bottom fifth of the frame kept calm, darker and uncluttered so a caption can be placed there later. no text, no letters, no words, no numbers, no watermark, no signature, no logo, no frame border, no people, not photorealistic, no harsh contrast, no neon colors
```

### INS-09 · Ножницы

```
a neat white cat with ginger patches, precise and slightly prim, in a tailor's workshop, holding small brass scissors and carefully cutting a piece out of a page, paper scraps and pinned patterns all around, dusty rose and pale wood. consistent rendering across the whole deck: warm painterly digital illustration with storybook realism, soft natural light, shallow depth of field with creamy bokeh, floating dust motes and faint sparkles, finely detailed fur, gentle vintage color grading, visible painterly brushwork. palette, location and time of day change from card to card; only the painting technique, level of detail and the cosy mood stay the same. square 1:1 composition, the cat in the upper two thirds, the bottom fifth of the frame kept calm, darker and uncluttered so a caption can be placed there later. no text, no letters, no words, no numbers, no watermark, no signature, no logo, no frame border, no people, not photorealistic, no harsh contrast, no neon colors
```

### INS-10 · Дыра

```
a curious young black cat with bright green eyes, in a dim cellar, leaning over a round hole burned clean through an open book, strong warm golden light pouring up out of the hole onto its face, everything else deep brown shadow. consistent rendering across the whole deck: warm painterly digital illustration with storybook realism, soft natural light, shallow depth of field with creamy bokeh, floating dust motes and faint sparkles, finely detailed fur, gentle vintage color grading, visible painterly brushwork. palette, location and time of day change from card to card; only the painting technique, level of detail and the cosy mood stay the same. square 1:1 composition, the cat in the upper two thirds, the bottom fifth of the frame kept calm, darker and uncluttered so a caption can be placed there later. no text, no letters, no words, no numbers, no watermark, no signature, no logo, no frame border, no people, not photorealistic, no harsh contrast, no neon colors
```

### INS-11 · Лишний

```
a calm brown tabby of middle age, unhurried and sure, at an evening desk, lifting one small paper figure out of a crowded pop-up book and setting it aside, the remaining scene visibly calmer, warm lamp circle in a dark room. consistent rendering across the whole deck: warm painterly digital illustration with storybook realism, soft natural light, shallow depth of field with creamy bokeh, floating dust motes and faint sparkles, finely detailed fur, gentle vintage color grading, visible painterly brushwork. palette, location and time of day change from card to card; only the painting technique, level of detail and the cosy mood stay the same. square 1:1 composition, the cat in the upper two thirds, the bottom fifth of the frame kept calm, darker and uncluttered so a caption can be placed there later. no text, no letters, no words, no numbers, no watermark, no signature, no logo, no frame border, no people, not photorealistic, no harsh contrast, no neon colors
```

### INS-12 · Другой финал

```
a ginger and white kitten with ink on its paws, pleased with itself, in an attic study, writing on a fresh last page with a long quill, two or three alternative paper endings pegged on a string above like laundry, ink bottle, warm dusk through a round window. consistent rendering across the whole deck: warm painterly digital illustration with storybook realism, soft natural light, shallow depth of field with creamy bokeh, floating dust motes and faint sparkles, finely detailed fur, gentle vintage color grading, visible painterly brushwork. palette, location and time of day change from card to card; only the painting technique, level of detail and the cosy mood stay the same. square 1:1 composition, the cat in the upper two thirds, the bottom fifth of the frame kept calm, darker and uncluttered so a caption can be placed there later. no text, no letters, no words, no numbers, no watermark, no signature, no logo, no frame border, no people, not photorealistic, no harsh contrast, no neon colors
```

### INS-13 · Мотив

```
a serious dark grey cat with a steady, searching gaze, in a dark study under a green banker's lamp, holding a magnifying glass over a small figure's chest where a warm clockwork heart glows, brass, leather and bottle-green. consistent rendering across the whole deck: warm painterly digital illustration with storybook realism, soft natural light, shallow depth of field with creamy bokeh, floating dust motes and faint sparkles, finely detailed fur, gentle vintage color grading, visible painterly brushwork. palette, location and time of day change from card to card; only the painting technique, level of detail and the cosy mood stay the same. square 1:1 composition, the cat in the upper two thirds, the bottom fifth of the frame kept calm, darker and uncluttered so a caption can be placed there later. no text, no letters, no words, no numbers, no watermark, no signature, no logo, no frame border, no people, not photorealistic, no harsh contrast, no neon colors
```

### INS-14 · Виноват

```
a brown tabby in a deerstalker cap that is slightly too big, deadly serious about it, on a rainy cobbled street under a gas lamp, following a trail of inky paw prints across an open page, wet reflections, blue-black night with warm lamp glow. consistent rendering across the whole deck: warm painterly digital illustration with storybook realism, soft natural light, shallow depth of field with creamy bokeh, floating dust motes and faint sparkles, finely detailed fur, gentle vintage color grading, visible painterly brushwork. palette, location and time of day change from card to card; only the painting technique, level of detail and the cosy mood stay the same. square 1:1 composition, the cat in the upper two thirds, the bottom fifth of the frame kept calm, darker and uncluttered so a caption can be placed there later. no text, no letters, no words, no numbers, no watermark, no signature, no logo, no frame border, no people, not photorealistic, no harsh contrast, no neon colors
```

### INS-15 · После финала

```
an old ginger tom with grey around the muzzle and calm half-closed eyes, sitting on a closed book on a wide windowsill at dusk, looking into the distance, one last warm ray across the face, faded rose and dusty blue. consistent rendering across the whole deck: warm painterly digital illustration with storybook realism, soft natural light, shallow depth of field with creamy bokeh, floating dust motes and faint sparkles, finely detailed fur, gentle vintage color grading, visible painterly brushwork. palette, location and time of day change from card to card; only the painting technique, level of detail and the cosy mood stay the same. square 1:1 composition, the cat in the upper two thirds, the bottom fifth of the frame kept calm, darker and uncluttered so a caption can be placed there later. no text, no letters, no words, no numbers, no watermark, no signature, no logo, no frame border, no people, not photorealistic, no harsh contrast, no neon colors
```

### INS-16 · Кому дал бы прочитать

```
a big good-natured round grey cat and, opposite it, a sleepy small kitten, at a morning kitchen table, the big cat pushing a book across the table toward the little one with both paws, milk jug and crumbs, pale yellow morning light. consistent rendering across the whole deck: warm painterly digital illustration with storybook realism, soft natural light, shallow depth of field with creamy bokeh, floating dust motes and faint sparkles, finely detailed fur, gentle vintage color grading, visible painterly brushwork. palette, location and time of day change from card to card; only the painting technique, level of detail and the cosy mood stay the same. square 1:1 composition, the cat in the upper two thirds, the bottom fifth of the frame kept calm, darker and uncluttered so a caption can be placed there later. no text, no letters, no words, no numbers, no watermark, no signature, no logo, no frame border, no people, not photorealistic, no harsh contrast, no neon colors
```

### INS-17 · Название

```
a curious white cat with odd eyes, one blue one amber, head tilted, in a bookshop window display at night, examining a standing book cover that carries only an empty ornate blank plate where a title would be, street light through glass, teal and warm gold. consistent rendering across the whole deck: warm painterly digital illustration with storybook realism, soft natural light, shallow depth of field with creamy bokeh, floating dust motes and faint sparkles, finely detailed fur, gentle vintage color grading, visible painterly brushwork. palette, location and time of day change from card to card; only the painting technique, level of detail and the cosy mood stay the same. square 1:1 composition, the cat in the upper two thirds, the bottom fifth of the frame kept calm, darker and uncluttered so a caption can be placed there later. no text, no letters, no words, no numbers, no watermark, no signature, no logo, no frame border, no people, not photorealistic, no harsh contrast, no neon colors
```

### INS-18 · На чём держится

```
a light-footed young tabby, an acrobat, balanced and alert, in a tall library, standing on a small structure of four stacked book columns holding up a floating open volume, testing one column with a careful paw, honey wood and long shafts of dusty light. consistent rendering across the whole deck: warm painterly digital illustration with storybook realism, soft natural light, shallow depth of field with creamy bokeh, floating dust motes and faint sparkles, finely detailed fur, gentle vintage color grading, visible painterly brushwork. palette, location and time of day change from card to card; only the painting technique, level of detail and the cosy mood stay the same. square 1:1 composition, the cat in the upper two thirds, the bottom fifth of the frame kept calm, darker and uncluttered so a caption can be placed there later. no text, no letters, no words, no numbers, no watermark, no signature, no logo, no frame border, no people, not photorealistic, no harsh contrast, no neon colors
```

### INS-19 · Одна эмоция

```
a plush persian with a wide open, unguarded face, in a bare room flooded by one single colour of light coming from a glowing book it is hugging, the whole scene in that one hue, everything else simplified. consistent rendering across the whole deck: warm painterly digital illustration with storybook realism, soft natural light, shallow depth of field with creamy bokeh, floating dust motes and faint sparkles, finely detailed fur, gentle vintage color grading, visible painterly brushwork. palette, location and time of day change from card to card; only the painting technique, level of detail and the cosy mood stay the same. square 1:1 composition, the cat in the upper two thirds, the bottom fifth of the frame kept calm, darker and uncluttered so a caption can be placed there later. no text, no letters, no words, no numbers, no watermark, no signature, no logo, no frame border, no people, not photorealistic, no harsh contrast, no neon colors
```

### INS-20 · Разговор

```
two cats facing each other, one glossy black, one soft white, both mid-conversation, at a small tea table in a steamy tea house, an open book between them, warm curls of steam rising like speech, amber lanterns and misted windows. consistent rendering across the whole deck: warm painterly digital illustration with storybook realism, soft natural light, shallow depth of field with creamy bokeh, floating dust motes and faint sparkles, finely detailed fur, gentle vintage color grading, visible painterly brushwork. palette, location and time of day change from card to card; only the painting technique, level of detail and the cosy mood stay the same. square 1:1 composition, the cat in the upper two thirds, the bottom fifth of the frame kept calm, darker and uncluttered so a caption can be placed there later. no text, no letters, no words, no numbers, no watermark, no signature, no logo, no frame border, no people, not photorealistic, no harsh contrast, no neon colors
```

## К оценке

### RAT-01 · Цена балла

```
a silver tabby with a precise, businesslike expression, behind the counter of an old shop, watching a brass balance scale with a single gold coin in one pan and a thin book in the other, weights and ledgers around, pewter and warm brass. consistent rendering across the whole deck: warm painterly digital illustration with storybook realism, soft natural light, shallow depth of field with creamy bokeh, floating dust motes and faint sparkles, finely detailed fur, gentle vintage color grading, visible painterly brushwork. palette, location and time of day change from card to card; only the painting technique, level of detail and the cosy mood stay the same. square 1:1 composition, the cat in the upper two thirds, the bottom fifth of the frame kept calm, darker and uncluttered so a caption can be placed there later. no text, no letters, no words, no numbers, no watermark, no signature, no logo, no frame border, no people, not photorealistic, no harsh contrast, no neon colors
```

### RAT-02 · Порог

```
a slender bengal adolescent, stretched out and straining, on a staircase built of stacked books, reaching one paw up toward the next step, strong warm light coming from above, cool shadow below. consistent rendering across the whole deck: warm painterly digital illustration with storybook realism, soft natural light, shallow depth of field with creamy bokeh, floating dust motes and faint sparkles, finely detailed fur, gentle vintage color grading, visible painterly brushwork. palette, location and time of day change from card to card; only the painting technique, level of detail and the cosy mood stay the same. square 1:1 composition, the cat in the upper two thirds, the bottom fifth of the frame kept calm, darker and uncluttered so a caption can be placed there later. no text, no letters, no words, no numbers, no watermark, no signature, no logo, no frame border, no people, not photorealistic, no harsh contrast, no neon colors
```

### RAT-03 · Не моё

```
a round scottish fold with a comically polite, apologetic face, in a fitting room with a mirror, trying on a pair of round spectacles far too large that slide off its nose, setting them aside, powder blue and soft grey. consistent rendering across the whole deck: warm painterly digital illustration with storybook realism, soft natural light, shallow depth of field with creamy bokeh, floating dust motes and faint sparkles, finely detailed fur, gentle vintage color grading, visible painterly brushwork. palette, location and time of day change from card to card; only the painting technique, level of detail and the cosy mood stay the same. square 1:1 composition, the cat in the upper two thirds, the bottom fifth of the frame kept calm, darker and uncluttered so a caption can be placed there later. no text, no letters, no words, no numbers, no watermark, no signature, no logo, no frame border, no people, not photorealistic, no harsh contrast, no neon colors
```

### RAT-04 · Через год

```
a small striped kitten whose reflection in the glass is a grown, composed cat of the same markings, beside a large hourglass by a window, an open book between kitten and reflection, sand falling slowly, pale winter light and long shadows. consistent rendering across the whole deck: warm painterly digital illustration with storybook realism, soft natural light, shallow depth of field with creamy bokeh, floating dust motes and faint sparkles, finely detailed fur, gentle vintage color grading, visible painterly brushwork. palette, location and time of day change from card to card; only the painting technique, level of detail and the cosy mood stay the same. square 1:1 composition, the cat in the upper two thirds, the bottom fifth of the frame kept calm, darker and uncluttered so a caption can be placed there later. no text, no letters, no words, no numbers, no watermark, no signature, no logo, no frame border, no people, not photorealistic, no harsh contrast, no neon colors
```

### RAT-05 · Накинутое

```
a plump ginger cat glancing aside with a faintly guilty look, at a market stall counter, quietly placing one extra golden star on top of a small stack of stars beside a book, warm evening lanterns, red and gold fabric. consistent rendering across the whole deck: warm painterly digital illustration with storybook realism, soft natural light, shallow depth of field with creamy bokeh, floating dust motes and faint sparkles, finely detailed fur, gentle vintage color grading, visible painterly brushwork. palette, location and time of day change from card to card; only the painting technique, level of detail and the cosy mood stay the same. square 1:1 composition, the cat in the upper two thirds, the bottom fifth of the frame kept calm, darker and uncluttered so a caption can be placed there later. no text, no letters, no words, no numbers, no watermark, no signature, no logo, no frame border, no people, not photorealistic, no harsh contrast, no neon colors
```

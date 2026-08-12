# Промпты для карточек «Убийство Роджера Экройда»

10 карт книжной колоды ACK. Манера рисунка та же, что у основной колоды —
она подтягивается из `prompts/scenes.json`, чтобы книжные карты не выбивались
из общей стопки. Место действия у всех одно: английская деревня двадцатых.
Местами вместо кота работает мышь.

Сгенерировано скриптом `scripts/build_prompts.py` из `prompts/scenes_ack.json` —
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

## Осторожно, финал

Карты этой колоды раскрывают развязку. Картинки — нет: ни одна сцена не
показывает, кто и как. Их можно спокойно генерировать и показывать до встречи,
а вот текст карт открывать только дочитавшим.

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

## Врезка · под книгу

### ACK-01 · Рассказчик

```
a tidy middle-aged grey tabby country doctor in a tweed waistcoat and pince-nez, pleasant and helpful, the sort everyone in the village trusts, writing his own account by lamplight at a mahogany desk in a 1920s English study, medical bag on the chair beside him; on the wall behind, his shadow sits in a subtly different posture than he does, warm brown and lamp-gold. consistent rendering across the whole deck: warm painterly digital illustration with storybook realism, soft natural light, shallow depth of field with creamy bokeh, floating dust motes and faint sparkles, finely detailed fur, gentle vintage color grading, visible painterly brushwork. palette, location and time of day change from card to card; only the painting technique, level of detail and the cosy mood stay the same. square 1:1 composition, the cat in the upper two thirds, the bottom fifth of the frame kept calm, darker and uncluttered so a caption can be placed there later. no text, no letters, no words, no numbers, no watermark, no signature, no logo, no frame border, no people, not photorealistic, no harsh contrast, no neon colors
```

### ACK-02 · Умолчание

```
a small bespectacled mouse archivist with careful paws and an unhurried, exacting manner, standing on an open page under a large magnifying glass, studying one printed line where a few words have fallen into deep shadow while the rest stay lit, the sentence still perfectly intact and unbroken, night library table, ink-blue and warm lamplight. consistent rendering across the whole deck: warm painterly digital illustration with storybook realism, soft natural light, shallow depth of field with creamy bokeh, floating dust motes and faint sparkles, finely detailed fur, gentle vintage color grading, visible painterly brushwork. palette, location and time of day change from card to card; only the painting technique, level of detail and the cosy mood stay the same. square 1:1 composition, the cat in the upper two thirds, the bottom fifth of the frame kept calm, darker and uncluttered so a caption can be placed there later. no text, no letters, no words, no numbers, no watermark, no signature, no logo, no frame border, no people, not photorealistic, no harsh contrast, no neon colors
```

### ACK-03 · Честная игра

```
two players facing each other: a sceptical brown tabby reader and a composed elderly lady cat in a 1920s cloche hat and pearls, both perfectly polite, at a green baize card table in a drawing room, one single card lying face down between them, all paws resting openly on the table where both can see them, a small rulebook open at the edge of the table, amber lamplight and a haze of smoke. consistent rendering across the whole deck: warm painterly digital illustration with storybook realism, soft natural light, shallow depth of field with creamy bokeh, floating dust motes and faint sparkles, finely detailed fur, gentle vintage color grading, visible painterly brushwork. palette, location and time of day change from card to card; only the painting technique, level of detail and the cosy mood stay the same. square 1:1 composition, the cat in the upper two thirds, the bottom fifth of the frame kept calm, darker and uncluttered so a caption can be placed there later. no text, no letters, no words, no numbers, no watermark, no signature, no logo, no frame border, no people, not photorealistic, no harsh contrast, no neon colors
```

### ACK-04 · Второй заход

```
a quiet cream-and-grey cat rereading with a slowly deepening frown, sitting in a wing armchair with the same book open for a second time; the tall mirror behind shows that very same room, but the furniture, the door and the light in it are subtly rearranged, twilight, dove grey and cold rose. consistent rendering across the whole deck: warm painterly digital illustration with storybook realism, soft natural light, shallow depth of field with creamy bokeh, floating dust motes and faint sparkles, finely detailed fur, gentle vintage color grading, visible painterly brushwork. palette, location and time of day change from card to card; only the painting technique, level of detail and the cosy mood stay the same. square 1:1 composition, the cat in the upper two thirds, the bottom fifth of the frame kept calm, darker and uncluttered so a caption can be placed there later. no text, no letters, no words, no numbers, no watermark, no signature, no logo, no frame border, no people, not photorealistic, no harsh contrast, no neon colors
```

### ACK-05 · Ватсон

```
a diligent mouse assistant in a knitted waistcoat with a notebook and pencil in its paws, sharply in focus in the foreground; far behind it, thrown out of focus, the small dapper silhouette of a cat detective, in a cluttered study, the assistant writing down every word while the blurred detective gestures at a map on the wall, the composition deliberately handing the whole foreground to the assistant, sepia and moss green. consistent rendering across the whole deck: warm painterly digital illustration with storybook realism, soft natural light, shallow depth of field with creamy bokeh, floating dust motes and faint sparkles, finely detailed fur, gentle vintage color grading, visible painterly brushwork. palette, location and time of day change from card to card; only the painting technique, level of detail and the cosy mood stay the same. square 1:1 composition, the cat in the upper two thirds, the bottom fifth of the frame kept calm, darker and uncluttered so a caption can be placed there later. no text, no letters, no words, no numbers, no watermark, no signature, no logo, no frame border, no people, not photorealistic, no harsh contrast, no neon colors
```

### ACK-06 · Кэролайн

```
a sharp-eyed calico lady cat with knitting needles, spectacles and the air of someone who knows everything first, at a lace-curtained village window, knitting a yarn that runs out through the window and threads on from house to house along the lane like telephone wire, neighbours' windows lighting up one after another in the dusk, warm rose and garden green. consistent rendering across the whole deck: warm painterly digital illustration with storybook realism, soft natural light, shallow depth of field with creamy bokeh, floating dust motes and faint sparkles, finely detailed fur, gentle vintage color grading, visible painterly brushwork. palette, location and time of day change from card to card; only the painting technique, level of detail and the cosy mood stay the same. square 1:1 composition, the cat in the upper two thirds, the bottom fifth of the frame kept calm, darker and uncluttered so a caption can be placed there later. no text, no letters, no words, no numbers, no watermark, no signature, no logo, no frame border, no people, not photorealistic, no harsh contrast, no neon colors
```

### ACK-07 · Последняя глава

```
an old theatrical black cat in evening dress, holding the final chapter like a script, standing on a small theatre stage in a single warm spotlight facing an empty auditorium, while the other half of the frame is a plain clerk's desk with a typed report and a rubber stamp under flat cold light, the two halves lit in openly different ways, crimson velvet against grey. consistent rendering across the whole deck: warm painterly digital illustration with storybook realism, soft natural light, shallow depth of field with creamy bokeh, floating dust motes and faint sparkles, finely detailed fur, gentle vintage color grading, visible painterly brushwork. palette, location and time of day change from card to card; only the painting technique, level of detail and the cosy mood stay the same. square 1:1 composition, the cat in the upper two thirds, the bottom fifth of the frame kept calm, darker and uncluttered so a caption can be placed there later. no text, no letters, no words, no numbers, no watermark, no signature, no logo, no frame border, no people, not photorealistic, no harsh contrast, no neon colors
```

### ACK-08 · Пуаро

```
a very small dapper cat with an immaculately waxed moustache, patent shoes and an egg-shaped head, retired and thoroughly pleased about it, in a sunny cottage kitchen garden among enormous vegetable marrows, watering can in paw, an unopened letter of invitation lying on the garden bench behind him and pointedly ignored, bright green and clay red. consistent rendering across the whole deck: warm painterly digital illustration with storybook realism, soft natural light, shallow depth of field with creamy bokeh, floating dust motes and faint sparkles, finely detailed fur, gentle vintage color grading, visible painterly brushwork. palette, location and time of day change from card to card; only the painting technique, level of detail and the cosy mood stay the same. square 1:1 composition, the cat in the upper two thirds, the bottom fifth of the frame kept calm, darker and uncluttered so a caption can be placed there later. no text, no letters, no words, no numbers, no watermark, no signature, no logo, no frame border, no people, not photorealistic, no harsh contrast, no neon colors
```

### ACK-09 · Кингс-Эббот

```
a row of village mice and cats at their garden gates, whiskers turned toward one another, one piece of news travelling down the lane from mouth to mouth, an English village street of thatched cottages at midday, a folded note passing paw to paw along the fence line, curtains twitching in every window it has already passed, the post office at the far end of the lane, sunlit green and cream. consistent rendering across the whole deck: warm painterly digital illustration with storybook realism, soft natural light, shallow depth of field with creamy bokeh, floating dust motes and faint sparkles, finely detailed fur, gentle vintage color grading, visible painterly brushwork. palette, location and time of day change from card to card; only the painting technique, level of detail and the cosy mood stay the same. square 1:1 composition, the cat in the upper two thirds, the bottom fifth of the frame kept calm, darker and uncluttered so a caption can be placed there later. no text, no letters, no words, no numbers, no watermark, no signature, no logo, no frame border, no people, not photorealistic, no harsh contrast, no neon colors
```

### ACK-10 · Финал

```
a solemn old mouse in mourning grey, quietly closing a heavy book with both paws, in a dark study after everyone has left: an empty armchair still holding the shape of whoever sat in it, a lamp turned down low, a clock showing a late hour, one unsent letter squared up on the desk, deep brown and ash, nothing violent anywhere in the frame. consistent rendering across the whole deck: warm painterly digital illustration with storybook realism, soft natural light, shallow depth of field with creamy bokeh, floating dust motes and faint sparkles, finely detailed fur, gentle vintage color grading, visible painterly brushwork. palette, location and time of day change from card to card; only the painting technique, level of detail and the cosy mood stay the same. square 1:1 composition, the cat in the upper two thirds, the bottom fifth of the frame kept calm, darker and uncluttered so a caption can be placed there later. no text, no letters, no words, no numbers, no watermark, no signature, no logo, no frame border, no people, not photorealistic, no harsh contrast, no neon colors
```

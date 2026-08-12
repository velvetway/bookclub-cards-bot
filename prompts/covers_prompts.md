# Промпты для обложек колод

Рубашка колоды — то, что можно показать, не раскрывая содержимого карт.
Манера рисунка та же, что у карточек, но кадр другой: не сцена с героем,
а предметный натюрморт, который читается с одного взгляда и в маленьком виде.

Сгенерировано скриптом `scripts/build_prompts.py` из `prompts/scenes_covers.json` —
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

## Чем обложка отличается от карточки

На карточке — герой в действии. На обложке героя нет или он уведён в силуэт:
обложка должна работать как рубашка, а не как ещё одна карта. Композиция
симметричнее, деталей меньше, крупные пятна вместо мелкой проработки —
иначе в ленте Telegram она превратится в кашу.

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

## Обложки

### DECK-MAIN · Бархатный Путь

```
no character in the foreground, only the shadow of a sleeping cat curled against the spine of the book, half dissolved into the dark, a deck cover still life, viewed straight on: an old leather-bound book lying open on deep velvet cloth, a fan of blank unmarked cards rising out of its pages like moths taking off, dandelion seeds and dust motes drifting through a single warm shaft of light, a brass reading lamp far out of focus behind, symmetrical and calm composition, deep plum velvet, honey gold and worn leather brown. consistent rendering across the whole deck: warm painterly digital illustration with storybook realism, soft natural light, shallow depth of field with creamy bokeh, floating dust motes and faint sparkles, finely detailed fur, gentle vintage color grading, visible painterly brushwork. palette, location and time of day change from card to card; only the painting technique, level of detail and the cosy mood stay the same. square 1:1 composition, the cat in the upper two thirds, the bottom fifth of the frame kept calm, darker and uncluttered so a caption can be placed there later. no text, no letters, no words, no numbers, no watermark, no signature, no logo, no frame border, no people, not photorealistic, no harsh contrast, no neon colors
```

### DECK-ACK · Убийство Роджера Экройда

```
no character in the foreground, only the tall silhouette of a cat in a homburg hat thrown across the wall by lamplight, unmistakable and unreadable, a detective deck cover still life, viewed straight on: a 1920s desk with a green banker's lamp, a magnifying glass resting on a folded newspaper, an envelope with a broken red wax seal, a single blank card face down beside it, fog pressing against the dark window behind, symmetrical and calm composition, art deco restraint, bottle green, oxblood red and brass. consistent rendering across the whole deck: warm painterly digital illustration with storybook realism, soft natural light, shallow depth of field with creamy bokeh, floating dust motes and faint sparkles, finely detailed fur, gentle vintage color grading, visible painterly brushwork. palette, location and time of day change from card to card; only the painting technique, level of detail and the cosy mood stay the same. square 1:1 composition, the cat in the upper two thirds, the bottom fifth of the frame kept calm, darker and uncluttered so a caption can be placed there later. no text, no letters, no words, no numbers, no watermark, no signature, no logo, no frame border, no people, not photorealistic, no harsh contrast, no neon colors
```

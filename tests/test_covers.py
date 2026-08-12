"""Обложки колод: подбор рубашки по кодам карт книги."""

from __future__ import annotations

from bot import images


def test_обложки_описаны_и_лежат_на_диске():
    covers = images.load_covers()
    codes = {c.code for c in covers}

    assert codes == {"DECK-MAIN", "DECK-ACK"}
    assert all(c.path.exists() for c in covers)


def test_книжной_колоде_достаётся_её_обложка():
    cover = images.cover_for_codes(["ACK-01", "ACK-07"])
    assert cover is not None and cover.code == "DECK-ACK"


def test_книге_без_своей_колоды_достаётся_общая():
    cover = images.cover_for_codes([])
    assert cover is not None and cover.is_main

    cover = images.cover_for_codes(["INS-03", "OPT-01"])
    assert cover is not None and cover.code == "DECK-MAIN"


def test_обложка_не_путается_с_картами():
    """Обложки лежат в своей папке: бот не должен раздать рубашку как карту."""
    card_files = {p.stem for p in images.CARDS_DIR.glob("*.jpg")}
    assert not any(name.startswith("DECK-") for name in card_files)


def test_фильтры_колод_упаковываются_в_callback_data():
    """Двоеточие — служебный разделитель aiogram: ключ колоды не должен его содержать."""
    from bot.callbacks import CardCB
    from bot.keyboards import DECK_FILTER

    for key in ("main", "ACK"):
        packed = CardCB(action="list", value=f"{DECK_FILTER}{key}").pack()
        assert CardCB.unpack(packed).value == f"{DECK_FILTER}{key}"


def test_кнопки_колод_в_списке_карт_собираются():
    from types import SimpleNamespace

    from bot import keyboards

    decks = [
        SimpleNamespace(key="main", title="Базовая колода", count=31, active=31),
        SimpleNamespace(key="ACK", title="Убийство Роджера Экройда", count=10, active=4),
    ]
    markup = keyboards.cards_list([], 0, "deck.ACK", decks)
    labels = [button.text for row in markup.inline_keyboard for button in row]

    assert any("Базовая колода (31)" in text for text in labels)
    assert any(
        text.startswith("· 🗂 Убийство Роджера Экройда") for text in labels
    ), "активный фильтр отмечен"
    assert any("вкл 4" in text for text in labels), "видно, что колода погашена не полностью"


def test_кнопки_массового_включения_появляются_только_у_колоды():
    from types import SimpleNamespace

    from bot import keyboards

    cards = [
        SimpleNamespace(id=1, code="ACK-01", title="Раз", is_active=True),
        SimpleNamespace(id=2, code="ACK-02", title="Два", is_active=False),
    ]
    decks = [
        SimpleNamespace(key="main", title="Базовая колода", count=31, active=31),
        SimpleNamespace(key="ACK", title="Экройд", count=2, active=1),
    ]

    with_deck = [
        b.text for row in keyboards.cards_list(cards, 0, "deck.ACK", decks).inline_keyboard for b in row
    ]
    assert any("Выключить все (1)" in t for t in with_deck)
    assert any("Включить все (1)" in t for t in with_deck)

    by_type = [
        b.text for row in keyboards.cards_list(cards, 0, "insert", decks).inline_keyboard for b in row
    ]
    assert not any("Выключить все" in t for t in by_type), "по типу карт массово не гасим"

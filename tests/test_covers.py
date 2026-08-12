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

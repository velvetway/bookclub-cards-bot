"""Сборка листа колоды и постера раздачи."""

from __future__ import annotations

import io
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

import pytest
from conftest import make_card
from PIL import Image

from bot import render
from bot.models import INSERT, Assignment, Book, Deal, User
from bot.storage.deals import AssignmentView

TZ = ZoneInfo("Europe/Moscow")


def _view(index: int, name: str) -> AssignmentView:
    return AssignmentView(
        assignment=Assignment(
            id=index,
            deal_id=1,
            user_id=index,
            card_id=index,
            status="sent",
            error=None,
            sent_at=None,
            reroll_count=0,
            manual=False,
        ),
        user=User(
            id=index,
            username=None,
            display_name=name,
            is_active=True,
            is_admin=False,
            started_at=datetime.now(timezone.utc),
        ),
        card=make_card(index, f"INS-{index:02d}"),
    )


def _deal() -> Deal:
    return Deal(
        id=1,
        book_id=1,
        phase=INSERT,
        pool_mode="all",
        pool_codes=None,
        status="draft",
        created_at=None,
        sent_at=None,
    )


def _size(data: bytes) -> tuple[int, int]:
    return Image.open(io.BytesIO(data)).size


def test_лист_колоды_собирается_без_картинок_на_диске():
    """У карт нет файлов — вместо них плашки с кодом, лист всё равно должен собраться."""
    cards = [make_card(i, f"INS-{i:02d}") for i in range(1, 32)]
    data = render.deck_sheet(cards, "Тестовая колода")

    width, height = _size(data)
    assert width > 500 and height > 500
    assert len(data) < 10 * 1024 * 1024, "Telegram не примет фото тяжелее 10 МБ"


def test_лист_растёт_вместе_с_числом_карт():
    small = _size(render.deck_sheet([make_card(1, "INS-01")], "Одна"))
    big = _size(render.deck_sheet([make_card(i, f"INS-{i:02d}") for i in range(1, 32)], "Много"))

    assert big[1] > small[1]


def test_пустая_выборка_не_даёт_пустую_картинку():
    with pytest.raises(ValueError):
        render.deck_sheet([], "Пусто")


def test_постер_раздачи_собирается():
    views = [_view(i, name) for i, name in enumerate(["Сергей", "БП", "Аня"], start=1)]
    book = Book(
        id=1,
        title="К югу от границы",
        author="Мураками",
        weeks=1,
        started_at=None,
        meeting_at=datetime.now(timezone.utc),
        status="current",
    )

    data = render.deal_board(views, _deal(), book, TZ)
    width, height = _size(data)

    assert width > 500 and height > 500
    assert len(data) < 10 * 1024 * 1024


def test_постер_без_участников_не_собирается():
    with pytest.raises(ValueError):
        render.deal_board([], _deal(), None, TZ)


def test_огромная_колода_не_выходит_за_лимиты_телеграма():
    cards = [make_card(i, f"C-{i:03d}") for i in range(1, 121)]
    data = render.deck_sheet(cards, "Сто двадцать карт")
    width, height = _size(data)

    assert max(width, height) <= render.MAX_SIDE
    assert len(data) < 10 * 1024 * 1024

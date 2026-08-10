from __future__ import annotations

import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from bot.models import INSERT, Card  # noqa: E402


def make_card(
    card_id: int,
    code: str,
    card_type: str = INSERT,
    *,
    is_active: bool = True,
    book_id: int | None = None,
) -> Card:
    return Card(
        id=card_id,
        code=code,
        type=card_type,
        title=f"Карта {code}",
        hint=None,
        is_active=is_active,
        book_id=book_id,
        created_at=None,
    )


def deck(n: int, card_type: str = INSERT, start: int = 1) -> list[Card]:
    return [make_card(i, f"C-{i:02d}", card_type) for i in range(start, start + n)]


def days_ago(n: int) -> datetime:
    return datetime.now(timezone.utc) - timedelta(days=n)


@pytest.fixture
def cards() -> list[Card]:
    return deck(20)

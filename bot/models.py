"""Типы предметной области. Значения статусов совпадают с тем, что лежит в базе."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

# типы карт
OPTICS = "optics"
INSERT = "insert"
RATING = "rating"
CARD_TYPES = (OPTICS, INSERT, RATING)

CARD_TYPE_NAMES = {
    OPTICS: "оптика",
    INSERT: "врезка",
    RATING: "к оценке",
}

# фазы раздачи
PHASE_MIXED = "mixed"
PHASES = (OPTICS, INSERT, RATING, PHASE_MIXED)

PHASE_NAMES = {
    OPTICS: "оптика",
    INSERT: "врезка",
    RATING: "к оценке",
    PHASE_MIXED: "смешанная",
}

# режимы пула
POOL_ALL = "all"
POOL_BY_TYPE = "by_type"
POOL_CUSTOM = "custom"
POOL_DECK = "deck"  # одна колода целиком: базовая или написанная под книгу

DECK_MAIN = "main"  # ключ базовой колоды, у книжных ключ — префикс кода (ACK)

# статусы раздачи
DEAL_DRAFT = "draft"
DEAL_SENT = "sent"
DEAL_PARTIAL = "partial"
DEAL_CANCELLED = "cancelled"

# статусы назначения
ASSIGN_PENDING = "pending"
ASSIGN_SENT = "sent"
ASSIGN_FAILED = "failed"
ASSIGN_SKIPPED = "skipped"

# статусы книги
BOOK_PLANNED = "planned"
BOOK_CURRENT = "current"
BOOK_DONE = "done"

# веса типов при pool_mode = all и фазе mixed
TYPE_WEIGHTS = {OPTICS: 0.20, INSERT: 0.65, RATING: 0.15}

# во сколько раз карта, написанная под конкретную книгу, вероятнее прочих
BOOK_CARD_BONUS = 3.0


@dataclass(frozen=True)
class User:
    id: int
    username: str | None
    display_name: str
    is_active: bool
    is_admin: bool
    started_at: datetime | None

    @property
    def reachable(self) -> bool:
        """Боту можно писать первым только тем, кто сам нажал /start."""
        return self.started_at is not None


@dataclass(frozen=True)
class Book:
    id: int
    title: str
    author: str | None
    weeks: int | None
    started_at: str | None
    meeting_at: datetime | None
    status: str


@dataclass(frozen=True)
class Card:
    id: int
    code: str
    type: str
    title: str
    hint: str | None
    is_active: bool
    book_id: int | None
    created_at: datetime | None
    image_path: str | None = None
    image_file_id: str | None = None
    image_sig: str | None = None

    @property
    def label(self) -> str:
        return f"{self.code} {self.title}"


@dataclass(frozen=True)
class Deal:
    id: int
    book_id: int
    phase: str
    pool_mode: str
    pool_codes: list[str] | None
    status: str
    created_at: datetime | None
    sent_at: datetime | None


@dataclass(frozen=True)
class Assignment:
    id: int
    deal_id: int
    user_id: int
    card_id: int
    status: str
    error: str | None
    sent_at: datetime | None
    reroll_count: int
    manual: bool
    repeat_of: datetime | None = None

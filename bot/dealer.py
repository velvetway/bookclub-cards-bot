"""Алгоритм раздачи (ТЗ, раздел 7).

Чистая логика без базы: на вход участники, пул и история, на выход назначения.
Так её можно прогонять тестами и не поднимать бота.

Порядок ограничений для каждого участника, от жёсткого к мягкому:
  1. карта не занята кем-то другим в этой же раздаче — не ослабляется никогда;
  2. оптика не выпадает, если участник получал её в последних OPTICS_COOLDOWN раздачах;
  3. карта не попадает в окно неповторения.
Если под всеми тремя ничего не осталось, ослабляем сначала (3), затем (2).
Ослабление (3) помечает назначение как повтор — в превью видно, от какой даты.
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from datetime import datetime, timezone

from bot.models import BOOK_CARD_BONUS, OPTICS, TYPE_WEIGHTS, Card

_EPOCH = datetime.min.replace(tzinfo=timezone.utc)


class NotEnoughCards(Exception):
    """Карт в пуле меньше, чем участников."""

    def __init__(self, needed: int, available: int) -> None:
        self.needed = needed
        self.available = available
        self.missing = needed - available
        super().__init__(f"не хватает карт: нужно {needed}, в пуле {available}")


@dataclass(frozen=True)
class UserHistory:
    """Что известно про участника на момент раздачи."""

    recent_card_ids: frozenset[int] = frozenset()
    had_optics_recently: bool = False
    last_dealt: dict[int, datetime] | None = None

    def last_time(self, card_id: int) -> datetime:
        if not self.last_dealt:
            return _EPOCH
        return self.last_dealt.get(card_id, _EPOCH)


@dataclass(frozen=True)
class Choice:
    user_id: int
    card_id: int
    repeat_of: datetime | None = None


def _weight(card: Card, candidates: list[Card], weighted: bool, book_id: int | None) -> float:
    """Вес карты при случайном выборе.

    При weighted доля типа фиксирована (20/65/15) независимо от того, сколько
    карт этого типа лежит в пуле: внутри типа карты равновероятны.
    Карта, написанная под текущую книгу, весит больше — при прочих равных выпадет первой.
    """
    if weighted:
        same_type = sum(1 for c in candidates if c.type == card.type)
        base = TYPE_WEIGHTS.get(card.type, 0.0) / same_type if same_type else 0.0
        if base <= 0:
            base = 1e-9  # тип без заданного веса всё равно должен иметь шанс
    else:
        base = 1.0

    if book_id is not None and card.book_id == book_id:
        base *= BOOK_CARD_BONUS
    return base


def _pick_weighted(
    candidates: list[Card], weighted: bool, book_id: int | None, rng: random.Random
) -> Card:
    weights = [_weight(c, candidates, weighted, book_id) for c in candidates]
    if sum(weights) <= 0:
        return rng.choice(candidates)
    return rng.choices(candidates, weights=weights, k=1)[0]


def _pick_oldest(candidates: list[Card], history: UserHistory, rng: random.Random) -> Card:
    """Окно ослаблено: берём карту, которую этот участник получал давнее всех."""
    shuffled = list(candidates)
    rng.shuffle(shuffled)  # чтобы одинаковые даты не разрешались порядком в пуле
    return min(shuffled, key=lambda c: history.last_time(c.id))


def choose_card(
    history: UserHistory,
    pool: list[Card],
    taken: set[int],
    *,
    weighted: bool,
    book_id: int | None = None,
    apply_optics_cooldown: bool = True,
    rng: random.Random | None = None,
) -> tuple[Card, datetime | None]:
    """Подбирает одну карту участнику. Возвращает карту и дату прошлой выдачи, если это повтор."""
    rng = rng or random.Random()

    free = [c for c in pool if c.id not in taken]
    if not free:
        raise NotEnoughCards(needed=len(taken) + 1, available=len(pool))

    without_optics = free
    if apply_optics_cooldown and history.had_optics_recently:
        without_optics = [c for c in free if c.type != OPTICS]

    fresh = [c for c in without_optics if c.id not in history.recent_card_ids]
    if fresh:
        return _pick_weighted(fresh, weighted, book_id, rng), None

    if without_optics:
        # все карты пула у этого участника уже были — ослабляем окно неповторения
        card = _pick_oldest(without_optics, history, rng)
        return card, history.last_time(card.id)

    # остались только карты-оптика, а у участника кулдаун — ослабляем и его
    fresh_optics = [c for c in free if c.id not in history.recent_card_ids]
    if fresh_optics:
        return _pick_weighted(fresh_optics, weighted, book_id, rng), None

    card = _pick_oldest(free, history, rng)
    return card, history.last_time(card.id)


def deal(
    user_ids: list[int],
    pool: list[Card],
    history: dict[int, UserHistory],
    *,
    weighted: bool = True,
    book_id: int | None = None,
    rng: random.Random | None = None,
) -> list[Choice]:
    """Раздаёт карты участникам. Порядок участников перемешивается."""
    rng = rng or random.Random()

    active_pool = [c for c in pool if c.is_active]
    if len(active_pool) < len(user_ids):
        raise NotEnoughCards(needed=len(user_ids), available=len(active_pool))

    # если в пуле нет ничего, кроме оптики, кулдаун применять нельзя —
    # иначе раздача оптики становится невозможной
    apply_cooldown = any(c.type != OPTICS for c in active_pool)

    order = list(user_ids)
    rng.shuffle(order)

    taken: set[int] = set()
    picked: dict[int, Choice] = {}
    for user_id in order:
        card, repeat_of = choose_card(
            history.get(user_id, UserHistory()),
            active_pool,
            taken,
            weighted=weighted,
            book_id=book_id,
            apply_optics_cooldown=apply_cooldown,
            rng=rng,
        )
        taken.add(card.id)
        picked[user_id] = Choice(user_id=user_id, card_id=card.id, repeat_of=repeat_of)

    # наружу отдаём в порядке, в котором админ выбирал состав
    return [picked[uid] for uid in user_ids]

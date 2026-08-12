"""Связка алгоритма раздачи с базой: сбор истории, генерация черновика, реролл."""

from __future__ import annotations

import logging
import random

import aiosqlite

from bot.dealer import Choice, NotEnoughCards, UserHistory, choose_card, deal as run_deal
from bot.models import (
    DECK_MAIN,
    POOL_ALL,
    POOL_BY_TYPE,
    POOL_CUSTOM,
    POOL_DECK,
    Assignment,
    Card,
    Deal,
)
from bot.storage import cards as cards_repo
from bot.storage import deals as deals_repo
from bot.storage.settings import Settings

log = logging.getLogger(__name__)


async def build_history(
    conn: aiosqlite.Connection, user_ids: list[int], settings: Settings
) -> dict[int, UserHistory]:
    history: dict[int, UserHistory] = {}
    for user_id in user_ids:
        recent = await deals_repo.recent_card_ids(conn, user_id, settings.no_repeat_window)
        history[user_id] = UserHistory(
            recent_card_ids=frozenset(recent),
            had_optics_recently=await deals_repo.had_optics_recently(
                conn, user_id, settings.optics_cooldown
            ),
            last_dealt=await deals_repo.last_dealt_map(conn, user_id),
        )
    return history


async def resolve_pool(conn: aiosqlite.Connection, deal: Deal) -> list[Card]:
    """Пул карт раздачи по её режиму."""
    if deal.pool_mode == POOL_BY_TYPE:
        return await cards_repo.list_all(conn, card_type=deal.phase, only_active=True)
    if deal.pool_mode == POOL_CUSTOM:
        codes = deal.pool_codes or []
        return await cards_repo.list_all(conn, codes=codes, only_active=True)
    if deal.pool_mode == POOL_DECK:
        key = (deal.pool_codes or [DECK_MAIN])[0]
        return await cards_repo.list_by_deck(conn, key)
    return await cards_repo.list_all(conn, only_active=True)


def is_weighted(deal: Deal) -> bool:
    """Веса типов работают, когда в пуле лежит целая колода (ТЗ, раздел 7).

    При выборе конкретной колоды это тоже так: если в ней карты одного типа,
    веса ничего не меняют, а в базовой дают привычные 20/65/15.
    """
    return deal.pool_mode in (POOL_ALL, POOL_DECK)


async def generate(
    conn: aiosqlite.Connection,
    deal: Deal,
    user_ids: list[int],
    settings: Settings,
    rng: random.Random | None = None,
) -> list[Choice]:
    """Генерирует состав черновика и сохраняет его. Бросает NotEnoughCards."""
    pool = await resolve_pool(conn, deal)
    history = await build_history(conn, user_ids, settings)

    choices = run_deal(
        user_ids,
        pool,
        history,
        weighted=is_weighted(deal),
        book_id=deal.book_id,
        rng=rng,
    )
    await deals_repo.replace_assignments(
        conn, deal.id, [(c.user_id, c.card_id, c.repeat_of) for c in choices]
    )
    log.info("раздача %s: сгенерировано назначений %s", deal.id, len(choices))
    return choices


async def reroll(
    conn: aiosqlite.Connection,
    deal: Deal,
    assignment: Assignment,
    settings: Settings,
    rng: random.Random | None = None,
) -> Card:
    """Меняет карту одному участнику. Карты остальных не трогает."""
    pool = await resolve_pool(conn, deal)
    others = await deals_repo.assignments(conn, deal.id)

    taken = {a.card_id for a in others if a.id != assignment.id}
    taken.add(assignment.card_id)  # ту же карту второй раз не выдаём

    if len([c for c in pool if c.id not in taken]) == 0:
        raise NotEnoughCards(needed=len(taken) + 1, available=len(pool))

    history = await build_history(conn, [assignment.user_id], settings)
    apply_cooldown = any(c.type != "optics" for c in pool)

    card, repeat_of = choose_card(
        history[assignment.user_id],
        pool,
        taken,
        weighted=is_weighted(deal),
        book_id=deal.book_id,
        apply_optics_cooldown=apply_cooldown,
        rng=rng,
    )
    await deals_repo.set_card(
        conn, assignment.id, card.id, bump_reroll=True, repeat_of=repeat_of
    )
    log.info(
        "реролл: раздача %s, участник %s, карта %s → %s",
        deal.id,
        assignment.user_id,
        assignment.card_id,
        card.id,
    )
    return card


async def set_card_manually(
    conn: aiosqlite.Connection, deal: Deal, assignment: Assignment, card_id: int
) -> str:
    """Ручная замена. Если карта уже у кого-то в этой раздаче — участники меняются картами."""
    others = await deals_repo.assignments(conn, deal.id)
    holder = next(
        (a for a in others if a.card_id == card_id and a.id != assignment.id), None
    )

    if holder is not None:
        await deals_repo.swap_cards(conn, assignment.id, holder.id)
        return "swapped"

    await deals_repo.set_card(conn, assignment.id, card_id, manual=True)
    return "set"

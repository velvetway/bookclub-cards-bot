"""Команды участника: своя карта, история, реролл."""

from __future__ import annotations

import logging
from html import escape

import aiosqlite
from aiogram import Bot, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from bot import delivery, keyboards, service, texts
from bot.callbacks import RerollCB
from bot.config import Config
from bot.dealer import NotEnoughCards
from bot.filters import IsPrivate
from bot.models import CARD_TYPE_NAMES, DEAL_PARTIAL, DEAL_SENT
from bot.storage import books as books_repo
from bot.storage import deals as deals_repo
from bot.storage import settings as settings_repo
from bot.timeutil import fmt_date_short

log = logging.getLogger(__name__)

router = Router(name="member")
router.message.filter(IsPrivate())


async def _view_for(conn: aiosqlite.Connection, assignment_id: int, deal_id: int):
    views = await deals_repo.views(conn, deal_id)
    return next((v for v in views if v.assignment.id == assignment_id), None)


@router.message(Command("me"))
async def cmd_me(
    message: Message, conn: aiosqlite.Connection, config: Config, bot: Bot
) -> None:
    current = await deals_repo.current_assignment(conn, message.from_user.id)
    if current is None:
        await message.answer("Карты пока нет. Придёт перед встречей.")
        return

    assignment, _card, deal = current
    settings = await settings_repo.effective(conn, config)
    book = await books_repo.get(conn, deal.book_id)
    view = await _view_for(conn, assignment.id, deal.id)
    if view is None:
        await message.answer("Карты пока нет. Придёт перед встречей.")
        return

    await delivery.send_card(bot, conn, view, book, settings, config.tz)


@router.message(Command("history"))
async def cmd_history(message: Message, conn: aiosqlite.Connection, config: Config) -> None:
    rows = await deals_repo.user_history(conn, message.from_user.id, limit=20)
    if not rows:
        await message.answer("Пока пусто — ни одной карты ещё не приходило.")
        return

    lines = ["<b>Твои карты</b>", ""]
    for card, deal, book in rows:
        when = fmt_date_short(deal.sent_at, config.tz)
        title = f"«{escape(book.title)}»" if book else "—"
        lines.append(
            f"{when} · {title}\n"
            f"   {card.code} <b>{escape(card.title)}</b> "
            f"<i>({CARD_TYPE_NAMES.get(card.type, card.type)})</i>"
        )
    await message.answer("\n".join(lines))


@router.callback_query(RerollCB.filter())
async def do_reroll(
    callback: CallbackQuery,
    callback_data: RerollCB,
    conn: aiosqlite.Connection,
    config: Config,
    bot: Bot,
) -> None:
    assignment = await deals_repo.get_assignment(conn, callback_data.assignment_id)
    if assignment is None or assignment.user_id != callback.from_user.id:
        await callback.answer("Эта карта не твоя", show_alert=True)
        return

    settings = await settings_repo.effective(conn, config)
    if settings.rerolls_per_deal <= 0:
        await callback.answer("Рероллы выключены", show_alert=True)
        return
    if assignment.reroll_count >= settings.rerolls_per_deal:
        await callback.answer("Реролл уже использован", show_alert=True)
        return

    deal = await deals_repo.get(conn, assignment.deal_id)
    if deal is None or deal.status not in (DEAL_SENT, DEAL_PARTIAL):
        await callback.answer("Раздача ещё не отправлена", show_alert=True)
        return

    try:
        await service.reroll(conn, deal, assignment, settings)
    except NotEnoughCards:
        await callback.answer("Свободных карт не осталось", show_alert=True)
        return

    # старую карточку не редактируем: у неё своя картинка. Гасим кнопку и шлём новую.
    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except TelegramBadRequest:
        pass

    book = await books_repo.get(conn, deal.book_id)
    view = await _view_for(conn, assignment.id, deal.id)
    if view is not None:
        await delivery.send_card(bot, conn, view, book, settings, config.tz)

    await callback.answer("Готово, карта другая")
    log.info("участник %s сделал реролл в раздаче %s", callback.from_user.id, deal.id)

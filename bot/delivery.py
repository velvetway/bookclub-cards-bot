"""Рассылка карт в личные сообщения."""

from __future__ import annotations

import asyncio
import logging
from zoneinfo import ZoneInfo

import aiosqlite
from aiogram import Bot
from aiogram.exceptions import TelegramAPIError, TelegramForbiddenError, TelegramRetryAfter
from aiogram.types import FSInputFile

from bot import images, keyboards, texts
from bot.models import (
    ASSIGN_FAILED,
    ASSIGN_SENT,
    DEAL_PARTIAL,
    DEAL_SENT,
    Book,
    Deal,
)
from bot.storage import books as books_repo
from bot.storage import cards as cards_repo
from bot.storage import deals as deals_repo
from bot.storage import users as users_repo
from bot.storage.deals import AssignmentView
from bot.storage.settings import Settings

log = logging.getLogger(__name__)

SEND_PAUSE = 0.05  # запас по лимитам Telegram

ERR_NOT_STARTED = "не нажимал /start — бот не может написать первым"
ERR_BLOCKED = "заблокировал бота"


async def deliver(
    bot: Bot,
    conn: aiosqlite.Connection,
    deal: Deal,
    settings: Settings,
    tz: ZoneInfo,
    *,
    only_failed: bool = False,
) -> list[AssignmentView]:
    """Отправляет карты участникам раздачи.

    only_failed — повторная попытка для тех, у кого статус failed.
    Карты при этом не перевыбираются: человек получит ровно то, что ему выпало.
    """
    book = await books_repo.get(conn, deal.book_id)
    views = await deals_repo.views(conn, deal.id)
    targets = [v for v in views if v.assignment.status == ASSIGN_FAILED] if only_failed else views

    for view in targets:
        await _send_one(bot, conn, view, book, settings, tz)
        await asyncio.sleep(SEND_PAUSE)

    views = await deals_repo.views(conn, deal.id)
    failed = sum(1 for v in views if v.assignment.status != ASSIGN_SENT)
    await deals_repo.mark_sent(conn, deal.id, DEAL_PARTIAL if failed else DEAL_SENT)
    log.info(
        "раздача %s разослана: успешно %s, с ошибкой %s",
        deal.id,
        len(views) - failed,
        failed,
    )
    return views


async def send_card(
    bot: Bot,
    conn: aiosqlite.Connection,
    view: AssignmentView,
    book: Book | None,
    settings: Settings,
    tz: ZoneInfo,
) -> None:
    """Картинка карточки, следом — пояснение отдельным сообщением.

    На картинке из текста только название карты. Если картинки нет,
    уходит одно текстовое сообщение.
    """
    user_id = view.user.id
    image = images.find_image(view.card)

    if image is not None:
        file_id = images.cached_file_id(view.card, image)
        message = await bot.send_photo(user_id, file_id or FSInputFile(image))
        if file_id is None:
            uploaded = _extract_file_id(message)
            if uploaded:
                await cards_repo.set_image_cache(
                    conn, view.card.id, uploaded, images.signature(image)
                )

    text = texts.render_card_message(settings.template, book, view.card, tz)
    rerolls_left = max(0, settings.rerolls_per_deal - view.assignment.reroll_count)
    await bot.send_message(
        user_id,
        text,
        reply_markup=keyboards.member_card(view.assignment.id, rerolls_left=rerolls_left),
    )


def _extract_file_id(message) -> str | None:
    photo = getattr(message, "photo", None)
    if not photo:
        return None
    return photo[-1].file_id


async def _send_one(
    bot: Bot,
    conn: aiosqlite.Connection,
    view: AssignmentView,
    book: Book | None,
    settings: Settings,
    tz: ZoneInfo,
) -> None:
    user = view.user
    if not user.reachable:
        await deals_repo.mark_delivery(conn, view.assignment.id, ASSIGN_FAILED, ERR_NOT_STARTED)
        log.warning("не отправлено %s: %s", user.id, ERR_NOT_STARTED)
        return

    try:
        await send_card(bot, conn, view, book, settings, tz)
    except TelegramRetryAfter as exc:
        log.warning("лимит Telegram, ждём %s с", exc.retry_after)
        await asyncio.sleep(exc.retry_after + 1)
        try:
            await send_card(bot, conn, view, book, settings, tz)
        except TelegramAPIError as retry_exc:
            await _fail(conn, view, str(retry_exc))
            return
    except TelegramForbiddenError:
        await users_repo.set_active(conn, user.id, False)
        await _fail(conn, view, ERR_BLOCKED)
        return
    except TelegramAPIError as exc:
        await _fail(conn, view, str(exc))
        return

    await deals_repo.mark_delivery(conn, view.assignment.id, ASSIGN_SENT)
    log.info("карта %s отправлена участнику %s", view.card.code, user.id)


async def _fail(conn: aiosqlite.Connection, view: AssignmentView, error: str) -> None:
    await deals_repo.mark_delivery(conn, view.assignment.id, ASSIGN_FAILED, error[:300])
    log.warning("ошибка отправки участнику %s: %s", view.user.id, error)


async def announce(
    bot: Bot,
    conn: aiosqlite.Connection,
    deal: Deal,
    settings: Settings,
    tz: ZoneInfo,
    delivered: int,
) -> bool:
    """Объявление в группу — только факт и состав, без содержимого карт."""
    if not settings.announce_in_group or settings.group_chat_id is None:
        return False

    book = await books_repo.get(conn, deal.book_id)
    try:
        await bot.send_message(
            settings.group_chat_id, texts.group_announcement(delivered, book, tz)
        )
    except TelegramAPIError as exc:
        log.warning("не удалось опубликовать объявление в группе: %s", exc)
        return False
    return True

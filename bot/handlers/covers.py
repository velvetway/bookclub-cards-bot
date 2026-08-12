"""Обложка колоды: посмотреть и отправить в группу.

Обложка ничего не раскрывает, поэтому её можно публиковать сразу после
объявления книги — задолго до самой раздачи. Отправка ручная: бот сам в группу
не пишет.
"""

from __future__ import annotations

import logging
from html import escape

import aiosqlite
from aiogram import Bot, F, Router
from aiogram.exceptions import TelegramAPIError
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, FSInputFile, Message

from bot import images, keyboards
from bot.callbacks import CoverCB, MenuCB
from bot.config import Config
from bot.filters import IsAdmin, IsPrivate
from bot.images import Cover
from bot.storage import books as books_repo
from bot.storage import cards as cards_repo
from bot.storage import settings as settings_repo
from bot.timeutil import fmt_dt

log = logging.getLogger(__name__)

router = Router(name="covers")
router.message.filter(IsPrivate(), IsAdmin())
router.callback_query.filter(IsAdmin())

NO_COVERS = (
    "Обложек пока нет.\n\n"
    "Сгенерируй их по <code>prompts/covers_prompts.md</code>, положи в "
    "<code>data/cards/raw/</code> как <code>DECK-MAIN.png</code> и "
    "<code>DECK-ACK.png</code>, потом <code>python scripts/make_cards.py</code>."
)


async def suggest_cover(conn: aiosqlite.Connection) -> Cover | None:
    """Обложка под текущую книгу: если у неё своя колода — её, иначе общая."""
    book = await books_repo.current(conn)
    codes: list[str] = []
    if book is not None:
        codes = [c.code for c in await cards_repo.list_all(conn) if c.book_id == book.id]
    return images.cover_for_codes(codes)


async def caption_for(conn: aiosqlite.Connection, config: Config) -> str:
    """Подпись к посту: книга и дата встречи, ничего про карты."""
    book = await books_repo.current(conn)
    if book is None:
        return "Новая колода."

    author = f" — {escape(book.author)}" if book.author else ""
    lines = [f"Читаем: «{escape(book.title)}»{author}"]
    if book.meeting_at:
        lines.append(f"Встреча: {fmt_dt(book.meeting_at, config.tz)}")
    return "\n".join(lines)


async def _show(
    target: Message | CallbackQuery,
    conn: aiosqlite.Connection,
    config: Config,
    cover: Cover | None,
) -> None:
    if cover is None:
        markup = keyboards.back_to_menu()
        if isinstance(target, CallbackQuery):
            await target.message.edit_text(NO_COVERS, reply_markup=markup)
            await target.answer()
        else:
            await target.answer(NO_COVERS, reply_markup=markup)
        return

    settings = await settings_repo.effective(conn, config)
    caption = await caption_for(conn, config)
    others = [c for c in images.load_covers() if c.code != cover.code]

    text = (
        f"<b>Обложка: {escape(cover.title)}</b>\n\n"
        "В группу уйдёт так:\n\n"
        f"{caption}"
    )
    if settings.group_chat_id is None:
        text += "\n\n⚠️ Группа не задана — укажи чат в /settings."

    photo = FSInputFile(cover.path)
    markup = keyboards.cover_actions(cover, others, can_send=settings.group_chat_id is not None)

    message = target.message if isinstance(target, CallbackQuery) else target
    await message.answer_photo(photo, caption=text, reply_markup=markup)
    if isinstance(target, CallbackQuery):
        await target.answer()


@router.message(Command("cover"))
async def cmd_cover(
    message: Message, conn: aiosqlite.Connection, config: Config, state: FSMContext
) -> None:
    await state.clear()
    await _show(message, conn, config, await suggest_cover(conn))


@router.callback_query(MenuCB.filter(F.action == "cover"))
async def menu_cover(
    callback: CallbackQuery, conn: aiosqlite.Connection, config: Config, state: FSMContext
) -> None:
    await state.clear()
    await _show(callback, conn, config, await suggest_cover(conn))


@router.callback_query(CoverCB.filter(F.action == "show"))
async def show_other(
    callback: CallbackQuery, callback_data: CoverCB, conn: aiosqlite.Connection, config: Config
) -> None:
    cover = next((c for c in images.load_covers() if c.code == callback_data.code), None)
    if cover is None:
        await callback.answer("Обложка не найдена", show_alert=True)
        return
    await _show(callback, conn, config, cover)


@router.callback_query(CoverCB.filter(F.action == "send"))
async def send_to_group(
    callback: CallbackQuery,
    callback_data: CoverCB,
    conn: aiosqlite.Connection,
    config: Config,
    bot: Bot,
) -> None:
    cover = next((c for c in images.load_covers() if c.code == callback_data.code), None)
    if cover is None:
        await callback.answer("Обложка не найдена", show_alert=True)
        return

    settings = await settings_repo.effective(conn, config)
    if settings.group_chat_id is None:
        await callback.answer("Сначала задай чат в /settings", show_alert=True)
        return

    try:
        await bot.send_photo(
            settings.group_chat_id,
            FSInputFile(cover.path),
            caption=await caption_for(conn, config),
        )
    except TelegramAPIError as exc:
        log.warning("не удалось отправить обложку в группу: %s", exc)
        await callback.answer(f"Не ушло: {exc}"[:180], show_alert=True)
        return

    log.info("обложка %s отправлена в группу %s", cover.code, settings.group_chat_id)
    await callback.answer("Отправлено в группу")
    await callback.message.edit_reply_markup(reply_markup=keyboards.back_to_menu())

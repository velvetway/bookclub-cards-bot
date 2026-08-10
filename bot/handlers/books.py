"""Книги: создать, сделать текущей, закрыть, назначить встречу."""

from __future__ import annotations

import logging
from html import escape

import aiosqlite
from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message

from bot import keyboards
from bot.callbacks import BookCB, MenuCB
from bot.config import Config
from bot.filters import IsAdmin, IsPrivate
from bot.models import BOOK_CURRENT, BOOK_DONE, BOOK_PLANNED
from bot.storage import books as books_repo
from bot.storage import deals as deals_repo
from bot.timeutil import fmt_dt, parse_user_datetime

log = logging.getLogger(__name__)

router = Router(name="books")
router.message.filter(IsPrivate(), IsAdmin())
router.callback_query.filter(IsAdmin())

STATUS_LABEL = {BOOK_CURRENT: "текущая", BOOK_DONE: "закрыта", BOOK_PLANNED: "запланирована"}


class BookForm(StatesGroup):
    title = State()
    meeting = State()


async def _show_list(target: Message | CallbackQuery, conn: aiosqlite.Connection) -> None:
    books = await books_repo.list_all(conn)
    text = "<b>Книги</b>" if books else "<b>Книги</b>\n\nПока ни одной."
    markup = keyboards.books_list(books)

    if isinstance(target, CallbackQuery):
        await target.message.edit_text(text, reply_markup=markup)
        await target.answer()
    else:
        await target.answer(text, reply_markup=markup)


@router.message(Command("book"))
async def cmd_book(message: Message, conn: aiosqlite.Connection, state: FSMContext) -> None:
    await state.clear()
    await _show_list(message, conn)


@router.callback_query(MenuCB.filter(F.action == "books"))
async def menu_books(
    callback: CallbackQuery, conn: aiosqlite.Connection, state: FSMContext
) -> None:
    await state.clear()
    await _show_list(callback, conn)


@router.callback_query(BookCB.filter(F.action == "list"))
async def books_list(
    callback: CallbackQuery, conn: aiosqlite.Connection, state: FSMContext
) -> None:
    await state.clear()
    await _show_list(callback, conn)


async def _render_book(
    callback: CallbackQuery, conn: aiosqlite.Connection, book_id: int, config: Config
) -> bool:
    book = await books_repo.get(conn, book_id)
    if book is None:
        return False

    deals = await deals_repo.list_for_book(conn, book.id)
    author = f"\n{escape(book.author)}" if book.author else ""
    text = (
        f"<b>«{escape(book.title)}»</b>{author}\n\n"
        f"Статус: {STATUS_LABEL.get(book.status, book.status)}\n"
        f"Встреча: {fmt_dt(book.meeting_at, config.tz)}\n"
        f"Раздач: {len(deals)}"
    )
    await callback.message.edit_text(text, reply_markup=keyboards.book_actions(book))
    return True


@router.callback_query(BookCB.filter(F.action == "open"))
async def open_book(
    callback: CallbackQuery, callback_data: BookCB, conn: aiosqlite.Connection, config: Config
) -> None:
    if not await _render_book(callback, conn, callback_data.book_id, config):
        await callback.answer("Книга не найдена", show_alert=True)
        return
    await callback.answer()


@router.callback_query(BookCB.filter(F.action == "make_current"))
async def make_current(
    callback: CallbackQuery, callback_data: BookCB, conn: aiosqlite.Connection, config: Config
) -> None:
    await books_repo.make_current(conn, callback_data.book_id)
    log.info("книга %s стала текущей", callback_data.book_id)
    await callback.answer("Теперь это текущая книга")
    await _render_book(callback, conn, callback_data.book_id, config)


@router.callback_query(BookCB.filter(F.action == "close"))
async def close_book(
    callback: CallbackQuery, callback_data: BookCB, conn: aiosqlite.Connection, config: Config
) -> None:
    await books_repo.set_status(conn, callback_data.book_id, BOOK_DONE)
    log.info("книга %s закрыта", callback_data.book_id)
    await callback.answer("Книга закрыта")
    await _render_book(callback, conn, callback_data.book_id, config)


@router.callback_query(BookCB.filter(F.action == "new"))
async def new_book(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(BookForm.title)
    await callback.message.edit_text(
        "Название книги. Можно так: <code>Автор — Название</code>"
    )
    await callback.answer()


@router.message(BookForm.title)
async def new_book_title(
    message: Message, conn: aiosqlite.Connection, state: FSMContext
) -> None:
    raw = (message.text or "").strip()
    if not raw:
        await message.answer("Пустое название. Попробуй ещё раз.")
        return

    author = None
    title = raw
    for sep in (" — ", " - ", " – "):
        if sep in raw:
            author, title = (part.strip() for part in raw.split(sep, 1))
            break

    book = await books_repo.create(conn, title=title, author=author)
    await state.update_data(book_id=book.id)
    await state.set_state(BookForm.meeting)
    log.info("создана книга %s: %s", book.id, book.title)
    await message.answer(
        f"Добавил «{escape(book.title)}».\n\n"
        "Когда встреча? <code>25.12.2026</code> или <code>25.12.2026 19:30</code>.\n"
        "Пропустить — <code>-</code>."
    )


@router.callback_query(BookCB.filter(F.action == "meeting"))
async def ask_meeting(
    callback: CallbackQuery, callback_data: BookCB, state: FSMContext
) -> None:
    await state.update_data(book_id=callback_data.book_id)
    await state.set_state(BookForm.meeting)
    await callback.message.edit_text(
        "Дата встречи: <code>25.12.2026</code> или <code>25.12.2026 19:30</code>.\n"
        "Убрать дату — <code>-</code>."
    )
    await callback.answer()


@router.message(BookForm.meeting)
async def save_meeting(
    message: Message, conn: aiosqlite.Connection, state: FSMContext, config: Config
) -> None:
    raw = (message.text or "").strip()
    data = await state.get_data()
    book_id = data["book_id"]

    if raw in ("-", "—", "нет", "пропустить"):
        await books_repo.set_meeting(conn, book_id, None)
    else:
        moment = parse_user_datetime(raw, config.tz)
        if moment is None:
            await message.answer("Не разобрал дату. Пример: <code>25.12.2026 19:30</code>")
            return
        await books_repo.set_meeting(conn, book_id, moment)

    await state.clear()
    book = await books_repo.get(conn, book_id)
    await message.answer(
        f"Встреча: {fmt_dt(book.meeting_at, config.tz)}" if book else "Готово"
    )
    await _show_list(message, conn)

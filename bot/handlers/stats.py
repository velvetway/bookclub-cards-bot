"""Кто что получил и статистика."""

from __future__ import annotations

from html import escape

import aiosqlite
from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot import keyboards, texts
from bot.callbacks import BookCB, MenuCB
from bot.config import Config
from bot.filters import IsAdmin, IsPrivate
from bot.models import ASSIGN_FAILED, ASSIGN_SENT, DEAL_DRAFT
from bot.storage import books as books_repo
from bot.storage import deals as deals_repo
from bot.storage import users as users_repo

router = Router(name="stats")
router.message.filter(IsPrivate(), IsAdmin())
router.callback_query.filter(IsAdmin())

MAX_MESSAGE = 3500  # с запасом до лимита Telegram в 4096 символов


async def _who_text(conn: aiosqlite.Connection, book_id: int, config: Config) -> str:
    book = await books_repo.get(conn, book_id)
    if book is None:
        return "Книга не найдена."

    picture = await deals_repo.book_picture(conn, book.id)
    lines = [f"<b>{texts.book_line(book)}</b>"]
    if book.meeting_at:
        from bot.timeutil import fmt_dt

        lines.append(f"Встреча: {fmt_dt(book.meeting_at, config.tz)}")

    if not picture:
        lines.append("")
        lines.append("По этой книге раздач ещё не было.")
        return "\n".join(lines)

    for deal, views in picture:
        lines.append("")
        lines.append(texts.deal_status_line(deal, config.tz))
        if not views:
            lines.append("   <i>состав пуст</i>")
            continue
        for view in views:
            mark = ""
            if view.assignment.status == ASSIGN_FAILED:
                mark = " ⚠️ не доставлено"
            elif deal.status != DEAL_DRAFT and view.assignment.status != ASSIGN_SENT:
                mark = " · ожидает"
            lines.append(
                f"   {escape(view.user.display_name)} — "
                f"{view.card.code} {escape(view.card.title)}{mark}"
            )

    text = "\n".join(lines)
    if len(text) > MAX_MESSAGE:
        text = text[:MAX_MESSAGE] + "\n\n<i>…список обрезан</i>"
    return text


@router.message(Command("who"))
async def cmd_who(
    message: Message, conn: aiosqlite.Connection, config: Config, state: FSMContext
) -> None:
    await state.clear()
    book = await books_repo.current(conn)
    if book is None:
        books = await books_repo.list_all(conn)
        if not books:
            await message.answer("Книг ещё нет.", reply_markup=keyboards.back_to_menu())
            return
        await message.answer("Какая книга?", reply_markup=keyboards.who_books(books))
        return
    await message.answer(
        await _who_text(conn, book.id, config), reply_markup=keyboards.who_back(book.id)
    )


@router.callback_query(MenuCB.filter(F.action == "who"))
async def menu_who(
    callback: CallbackQuery, conn: aiosqlite.Connection, config: Config, state: FSMContext
) -> None:
    await state.clear()
    books = await books_repo.list_all(conn)
    if not books:
        await callback.message.edit_text("Книг ещё нет.", reply_markup=keyboards.back_to_menu())
        await callback.answer()
        return

    current = await books_repo.current(conn)
    await callback.message.edit_text(
        "История выдач. Какая книга?",
        reply_markup=keyboards.who_books(books, current.id if current else None),
    )
    await callback.answer()


@router.callback_query(BookCB.filter(F.action == "who"))
async def book_who(
    callback: CallbackQuery, callback_data: BookCB, conn: aiosqlite.Connection, config: Config
) -> None:
    await callback.message.edit_text(
        await _who_text(conn, callback_data.book_id, config),
        reply_markup=keyboards.who_back(callback_data.book_id),
    )
    await callback.answer()


@router.message(Command("stats"))
async def cmd_stats(
    message: Message, conn: aiosqlite.Connection, state: FSMContext
) -> None:
    await state.clear()
    await message.answer(await _stats_text(conn), reply_markup=keyboards.back_to_menu())


@router.callback_query(MenuCB.filter(F.action == "stats"))
async def menu_stats(
    callback: CallbackQuery, conn: aiosqlite.Connection, state: FSMContext
) -> None:
    await state.clear()
    await callback.message.edit_text(
        await _stats_text(conn), reply_markup=keyboards.back_to_menu()
    )
    await callback.answer()


async def _stats_text(conn: aiosqlite.Connection) -> str:
    distribution = await deals_repo.user_distribution(conn)
    frequency = await deals_repo.card_frequency(conn)
    dealt = [row for row in frequency if row[2] > 0]

    lines = ["<b>Статистика</b>", "", "<b>По участникам</b>"]
    if not distribution:
        lines.append("пока пусто")
    for name, total, optics in distribution:
        if total == 0:
            continue
        lines.append(f"• {escape(name)} — {total}, оптики {optics}")

    lines.append("")
    lines.append("<b>Частые карты</b>")
    if not dealt:
        lines.append("ни одна карта ещё не выдавалась")
    for code, title, count in dealt[:10]:
        lines.append(f"• {code} {escape(title)} — {count}")

    never = [row for row in frequency if row[2] == 0]
    if never:
        lines.append("")
        lines.append(f"<b>Ни разу не выпадали:</b> {len(never)}")
        lines.append(", ".join(code for code, _, _ in never[:20]))

    return "\n".join(lines)

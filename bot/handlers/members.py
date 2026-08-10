"""Участники: список, статус, имя, права, приглашение."""

from __future__ import annotations

import logging
from html import escape

import aiosqlite
from aiogram import Bot, F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message

from bot import keyboards, texts
from bot.callbacks import MemberCB, MenuCB
from bot.config import Config
from bot.filters import IsAdmin, IsPrivate
from bot.models import CARD_TYPE_NAMES
from bot.storage import deals as deals_repo
from bot.storage import users as users_repo
from bot.timeutil import fmt_date_short

log = logging.getLogger(__name__)

router = Router(name="members")
router.message.filter(IsPrivate(), IsAdmin())
router.callback_query.filter(IsAdmin())


class MemberForm(StatesGroup):
    rename = State()


async def _list_text(conn: aiosqlite.Connection) -> str:
    users = await users_repo.list_all(conn)
    active = [u for u in users if u.is_active]
    joined = [u for u in active if u.reachable]

    lines = ["<b>Участники</b>", ""]
    for user in users:
        lines.append("• " + texts.member_line(user))
    lines.append("")
    lines.append(f"Активных {len(active)}, из них подключились {len(joined)}.")
    if len(joined) < len(active):
        lines.append("Кто без /start — тому бот написать не может, нужна ссылка-приглашение.")
    return "\n".join(lines)


async def _show_list(
    target: Message | CallbackQuery, conn: aiosqlite.Connection, page: int = 0
) -> None:
    users = await users_repo.list_all(conn)
    text = await _list_text(conn)
    markup = keyboards.members_list(users, page)

    if isinstance(target, CallbackQuery):
        await target.message.edit_text(text, reply_markup=markup)
        await target.answer()
    else:
        await target.answer(text, reply_markup=markup)


@router.message(Command("members"))
async def cmd_members(message: Message, conn: aiosqlite.Connection, state: FSMContext) -> None:
    await state.clear()
    await _show_list(message, conn)


@router.callback_query(MenuCB.filter(F.action == "members"))
async def menu_members(
    callback: CallbackQuery, conn: aiosqlite.Connection, state: FSMContext
) -> None:
    await state.clear()
    await _show_list(callback, conn)


@router.callback_query(MemberCB.filter(F.action == "list"))
async def members_page(
    callback: CallbackQuery, callback_data: MemberCB, conn: aiosqlite.Connection, state: FSMContext
) -> None:
    await state.clear()
    await _show_list(callback, conn, callback_data.page)


async def _render_member(
    callback: CallbackQuery, conn: aiosqlite.Connection, user_id: int, page: int
) -> bool:
    user = await users_repo.get(conn, user_id)
    if user is None:
        return False

    history = await deals_repo.user_history(conn, user_id, limit=3)
    last = ""
    if history:
        card, deal, _ = history[0]
        last = f"\n\nПоследняя карта: {card.code} {escape(card.title)}"

    text = texts.member_line(user) + last
    await callback.message.edit_text(text, reply_markup=keyboards.member_actions(user, page))
    return True


@router.callback_query(MemberCB.filter(F.action == "open"))
async def open_member(
    callback: CallbackQuery, callback_data: MemberCB, conn: aiosqlite.Connection
) -> None:
    if not await _render_member(callback, conn, callback_data.user_id, callback_data.page):
        await callback.answer("Участник не найден", show_alert=True)
        return
    await callback.answer()


@router.callback_query(MemberCB.filter(F.action == "toggle"))
async def toggle_member(
    callback: CallbackQuery, callback_data: MemberCB, conn: aiosqlite.Connection
) -> None:
    user = await users_repo.get(conn, callback_data.user_id)
    if user is None:
        await callback.answer("Участник не найден", show_alert=True)
        return
    await users_repo.set_active(conn, user.id, not user.is_active)
    log.info("участник %s: активность → %s", user.id, not user.is_active)
    await callback.answer("Активирован" if not user.is_active else "Деактивирован")
    await _render_member(callback, conn, user.id, callback_data.page)


@router.callback_query(MemberCB.filter(F.action == "admin"))
async def toggle_admin(
    callback: CallbackQuery, callback_data: MemberCB, conn: aiosqlite.Connection, bot: Bot
) -> None:
    user = await users_repo.get(conn, callback_data.user_id)
    if user is None:
        await callback.answer("Участник не найден", show_alert=True)
        return

    if user.is_admin and await users_repo.count_admins(conn) <= 1:
        await callback.answer("Это последний админ, права снять нельзя", show_alert=True)
        return

    await users_repo.set_admin(conn, user.id, not user.is_admin)
    log.info("участник %s: админ → %s", user.id, not user.is_admin)

    from bot.handlers.common import sync_commands

    await sync_commands(bot, conn)
    await callback.answer("Теперь админ" if not user.is_admin else "Права сняты")
    await _render_member(callback, conn, user.id, callback_data.page)


@router.callback_query(MemberCB.filter(F.action == "rename"))
async def ask_rename(
    callback: CallbackQuery, callback_data: MemberCB, state: FSMContext
) -> None:
    await state.update_data(user_id=callback_data.user_id, page=callback_data.page)
    await state.set_state(MemberForm.rename)
    await callback.message.edit_text("Как показывать этого участника в списках?")
    await callback.answer()


@router.message(MemberForm.rename)
async def save_rename(message: Message, conn: aiosqlite.Connection, state: FSMContext) -> None:
    name = (message.text or "").strip()
    if not name:
        await message.answer("Пустое имя. Попробуй ещё раз.")
        return
    data = await state.get_data()
    await users_repo.set_display_name(conn, data["user_id"], name)
    await state.clear()
    await message.answer(f"Теперь это {escape(name)}.")
    await _show_list(message, conn, data.get("page", 0))


@router.callback_query(MemberCB.filter(F.action == "history"))
async def member_history(
    callback: CallbackQuery, callback_data: MemberCB, conn: aiosqlite.Connection, config: Config
) -> None:
    user = await users_repo.get(conn, callback_data.user_id)
    if user is None:
        await callback.answer("Участник не найден", show_alert=True)
        return

    rows = await deals_repo.user_history(conn, user.id, limit=25)
    lines = [f"<b>{escape(user.display_name)}</b>", ""]
    if not rows:
        lines.append("Карт ещё не получал.")
    for card, deal, book in rows:
        title = f"«{escape(book.title)}»" if book else "—"
        lines.append(
            f"{fmt_date_short(deal.sent_at, config.tz)} · {title}\n"
            f"   {card.code} {escape(card.title)} "
            f"<i>({CARD_TYPE_NAMES.get(card.type, card.type)})</i>"
        )

    await callback.message.edit_text(
        "\n".join(lines), reply_markup=keyboards.member_actions(user, callback_data.page)
    )
    await callback.answer()


@router.callback_query(MemberCB.filter(F.action == "invite"))
async def invite(callback: CallbackQuery, bot: Bot) -> None:
    me = await bot.get_me()
    link = f"https://t.me/{me.username}?start=join"
    text = (
        "<b>Приглашение в клуб</b>\n\n"
        "Кинь эту ссылку в общий чат. Каждый, кто перейдёт и нажмёт «Старт», "
        "появится в списке участников — после этого бот сможет писать ему в личку.\n\n"
        f"{link}"
    )
    await callback.message.edit_text(
        text, reply_markup=keyboards.members_back(), disable_web_page_preview=True
    )
    await callback.answer()

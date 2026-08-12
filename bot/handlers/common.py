"""Онбординг, главное меню, служебные команды."""

from __future__ import annotations

import logging

import aiosqlite
from aiogram import Bot, F, Router
from aiogram.filters import Command, CommandObject, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    BotCommand,
    BotCommandScopeChat,
    BotCommandScopeDefault,
    CallbackQuery,
    Message,
)

from bot import keyboards
from bot.callbacks import MenuCB
from bot.config import Config
from bot.filters import IsPrivate
from bot.storage import books as books_repo
from bot.storage import cards as cards_repo
from bot.storage import users as users_repo
from bot.texts import book_line, members_word

log = logging.getLogger(__name__)

router = Router(name="common")
router.message.filter(IsPrivate())

MEMBER_COMMANDS = [
    BotCommand(command="me", description="моя текущая карта"),
    BotCommand(command="history", description="мои прошлые карты"),
]

ADMIN_COMMANDS = MEMBER_COMMANDS + [
    BotCommand(command="menu", description="панель админа"),
    BotCommand(command="deal", description="мастер раздачи"),
    BotCommand(command="cards", description="колода"),
    BotCommand(command="book", description="книги"),
    BotCommand(command="members", description="участники"),
    BotCommand(command="who", description="кто что получил"),
    BotCommand(command="cover", description="обложка колоды в группу"),
    BotCommand(command="stats", description="статистика"),
    BotCommand(command="settings", description="настройки"),
]

WELCOME_MEMBER = (
    "Ты в клубе.\n\n"
    "Перед встречей я пришлю тебе карту — угол или обязательный элемент, "
    "который нужно встроить в свой разбор книги.\n\n"
    "Чужие карты неизвестны до встречи, это часть игры.\n\n"
    "/me — текущая карта, /history — прошлые."
)


async def sync_commands(bot: Bot, conn: aiosqlite.Connection) -> None:
    """Участникам — короткий список команд, админам — полный."""
    await bot.set_my_commands(MEMBER_COMMANDS, scope=BotCommandScopeDefault())
    for user in await users_repo.list_all(conn):
        if not user.is_admin or not user.reachable:
            continue
        try:
            await bot.set_my_commands(ADMIN_COMMANDS, scope=BotCommandScopeChat(chat_id=user.id))
        except Exception as exc:  # чат мог быть удалён — это не повод падать на старте
            log.warning("не удалось задать команды админу %s: %s", user.id, exc)


@router.message(CommandStart())
async def cmd_start(
    message: Message,
    command: CommandObject,
    conn: aiosqlite.Connection,
    config: Config,
    bot: Bot,
    state: FSMContext,
) -> None:
    await state.clear()
    tg_user = message.from_user
    if tg_user is None:
        return

    display = tg_user.full_name or tg_user.username or str(tg_user.id)
    user = await users_repo.register(conn, tg_user.id, tg_user.username, display)

    # первый пришедший при пустой базе админов забирает права себе
    if not user.is_admin:
        if tg_user.id in config.admin_ids or await users_repo.count_admins(conn) == 0:
            await users_repo.set_admin(conn, tg_user.id, True)
            user = await users_repo.get(conn, tg_user.id) or user
            log.info("пользователь %s стал администратором", tg_user.id)

    payload = (command.args or "").strip()
    log.info("start: %s (%s), payload=%r", tg_user.id, display, payload)

    if user.is_admin:
        await sync_commands(bot, conn)
        await message.answer(await menu_text(conn), reply_markup=keyboards.main_menu())
        return

    await message.answer(WELCOME_MEMBER)


async def menu_text(conn: aiosqlite.Connection) -> str:
    book = await books_repo.current(conn)
    all_cards = await cards_repo.list_all(conn)
    active_cards = [c for c in all_cards if c.is_active]
    users = await users_repo.list_all(conn)
    active_users = [u for u in users if u.is_active]
    reachable = [u for u in active_users if u.reachable]

    lines = [
        "<b>Панель клуба</b>",
        "",
        f"Книга: {book_line(book)}" if book else "Книга: не выбрана",
        f"Колода: {len(all_cards)} карт, активных {len(active_cards)}",
        f"Участники: {members_word(len(active_users))}, подключились {len(reachable)}",
    ]
    if len(reachable) < len(active_users):
        lines.append("")
        lines.append("🚫 — не нажал /start, такому участнику бот написать не может.")
    return "\n".join(lines)


@router.message(Command("menu"))
async def cmd_menu(message: Message, conn: aiosqlite.Connection, state: FSMContext) -> None:
    if not await users_repo.is_admin(conn, message.from_user.id):
        await message.answer("Эта команда только для админов. Твоя карта — /me.")
        return
    await state.clear()
    await message.answer(await menu_text(conn), reply_markup=keyboards.main_menu())


@router.callback_query(MenuCB.filter(F.action == "root"))
async def open_menu(
    callback: CallbackQuery, conn: aiosqlite.Connection, state: FSMContext
) -> None:
    if not await users_repo.is_admin(conn, callback.from_user.id):
        await callback.answer("Только для админов", show_alert=True)
        return
    await state.clear()
    await callback.message.edit_text(await menu_text(conn), reply_markup=keyboards.main_menu())
    await callback.answer()

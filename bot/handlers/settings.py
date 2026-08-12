"""Настройки: окно неповторения, кулдаун оптики, рероллы, группа, шаблон."""

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
from bot.callbacks import MenuCB, SettingsCB
from bot.config import Config
from bot.filters import IsAdmin, IsPrivate
from bot.storage import settings as settings_repo
from bot.storage.settings import (
    DEFAULT_TEMPLATE,
    KEY_ANNOUNCE,
    KEY_BOARD_CHAT,
    KEY_GROUP_CHAT,
    KEY_NO_REPEAT,
    KEY_OPTICS_COOLDOWN,
    KEY_REROLLS,
    KEY_TEMPLATE,
)

log = logging.getLogger(__name__)

router = Router(name="settings")
router.message.filter(IsPrivate(), IsAdmin())
router.callback_query.filter(IsAdmin())

PLACEHOLDERS = (
    "{book} {author} {meeting} {card_title} {card_hint} {card_code} {card_type}"
)


class SettingsForm(StatesGroup):
    no_repeat = State()
    board = State()
    optics = State()
    rerolls = State()
    group = State()
    template = State()


async def _settings_text(conn: aiosqlite.Connection, config: Config) -> str:
    current = await settings_repo.effective(conn, config)
    group = current.group_chat_id if current.group_chat_id is not None else "не задана"
    announce = "да" if current.announce_in_group else "нет"
    rerolls = current.rerolls_per_deal or "выключены"
    board = current.board_chat_id if current.board_chat_id is not None else "не задан"
    if current.board_chat_id is not None and current.board_chat_id == current.group_chat_id:
        board = f"{board} (та же группа)"

    return (
        "<b>Настройки</b>\n\n"
        f"Окно неповторения: {current.no_repeat_window} последних выдач\n"
        f"Кулдаун оптики: {current.optics_cooldown} раздач\n"
        f"Рероллов на участника: {rerolls}\n"
        f"Группа для объявлений: {group} (постить: {announce})\n"
        f"Чат для постеров: {board}\n"
        f"Шаблон сообщения: {'свой' if current.template != DEFAULT_TEMPLATE else 'стандартный'}"
    )


async def _show(
    target: Message | CallbackQuery, conn: aiosqlite.Connection, config: Config
) -> None:
    text = await _settings_text(conn, config)
    markup = keyboards.settings_menu()
    if isinstance(target, CallbackQuery):
        await target.message.edit_text(text, reply_markup=markup)
        await target.answer()
    else:
        await target.answer(text, reply_markup=markup)


@router.message(Command("settings"))
async def cmd_settings(
    message: Message, conn: aiosqlite.Connection, config: Config, state: FSMContext
) -> None:
    await state.clear()
    await _show(message, conn, config)


@router.callback_query(MenuCB.filter(F.action == "settings"))
async def menu_settings(
    callback: CallbackQuery, conn: aiosqlite.Connection, config: Config, state: FSMContext
) -> None:
    await state.clear()
    await _show(callback, conn, config)


@router.callback_query(SettingsCB.filter(F.action == "root"))
async def settings_root(
    callback: CallbackQuery, conn: aiosqlite.Connection, config: Config, state: FSMContext
) -> None:
    await state.clear()
    await _show(callback, conn, config)


@router.callback_query(SettingsCB.filter(F.action == "no_repeat"))
async def ask_no_repeat(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(SettingsForm.no_repeat)
    await callback.message.edit_text(
        "Сколько последних выдач участнику блокируют повтор карты?\n"
        "Число от 0 до 100. По умолчанию 10.",
        reply_markup=keyboards.settings_back(),
    )
    await callback.answer()


@router.message(SettingsForm.no_repeat)
async def save_no_repeat(
    message: Message, conn: aiosqlite.Connection, config: Config, state: FSMContext
) -> None:
    value = _read_int(message.text, low=0, high=100)
    if value is None:
        await message.answer("Нужно целое число от 0 до 100.")
        return
    await settings_repo.set_value(conn, KEY_NO_REPEAT, value)
    await state.clear()
    log.info("окно неповторения → %s", value)
    await _show(message, conn, config)


@router.callback_query(SettingsCB.filter(F.action == "optics"))
async def ask_optics(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(SettingsForm.optics)
    await callback.message.edit_text(
        "Через сколько раздач участнику снова может выпасть оптика?\n"
        "Число от 0 до 20. По умолчанию 3.",
        reply_markup=keyboards.settings_back(),
    )
    await callback.answer()


@router.message(SettingsForm.optics)
async def save_optics(
    message: Message, conn: aiosqlite.Connection, config: Config, state: FSMContext
) -> None:
    value = _read_int(message.text, low=0, high=20)
    if value is None:
        await message.answer("Нужно целое число от 0 до 20.")
        return
    await settings_repo.set_value(conn, KEY_OPTICS_COOLDOWN, value)
    await state.clear()
    log.info("кулдаун оптики → %s", value)
    await _show(message, conn, config)


@router.callback_query(SettingsCB.filter(F.action == "rerolls"))
async def ask_rerolls(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(SettingsForm.rerolls)
    await callback.message.edit_text(
        "Сколько рероллов даём участнику в одной раздаче?\n"
        "0 — реролл выключен. По умолчанию 1.",
        reply_markup=keyboards.settings_back(),
    )
    await callback.answer()


@router.message(SettingsForm.rerolls)
async def save_rerolls(
    message: Message, conn: aiosqlite.Connection, config: Config, state: FSMContext
) -> None:
    value = _read_int(message.text, low=0, high=5)
    if value is None:
        await message.answer("Нужно целое число от 0 до 5.")
        return
    await settings_repo.set_value(conn, KEY_REROLLS, value)
    await state.clear()
    log.info("рероллы → %s", value)
    await _show(message, conn, config)


@router.callback_query(SettingsCB.filter(F.action == "group"))
async def group_menu(
    callback: CallbackQuery, conn: aiosqlite.Connection, config: Config
) -> None:
    current = await settings_repo.effective(conn, config)
    chat = current.group_chat_id if current.group_chat_id is not None else "не задана"
    await callback.message.edit_text(
        f"<b>Группа для объявлений</b>\n\nЧат: {chat}\n\n"
        "После раздачи бот может опубликовать в группе только факт: "
        "сколько человек получили карты и когда встреча. Содержимое карт не раскрывается.",
        reply_markup=keyboards.announce_toggle(current.announce_in_group),
    )
    await callback.answer()


@router.callback_query(SettingsCB.filter(F.action == "announce_toggle"))
async def toggle_announce(
    callback: CallbackQuery, conn: aiosqlite.Connection, config: Config
) -> None:
    current = await settings_repo.effective(conn, config)
    if current.group_chat_id is None and not current.announce_in_group:
        await callback.answer("Сначала задай чат", show_alert=True)
        return
    await settings_repo.set_value(conn, KEY_ANNOUNCE, "0" if current.announce_in_group else "1")
    await group_menu(callback, conn, config)


@router.callback_query(SettingsCB.filter(F.action == "group_set"))
async def ask_group(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(SettingsForm.group)
    await callback.message.edit_text(
        "Пришли ID чата. У супергрупп он начинается на <code>-100</code>.\n\n"
        "Где взять: добавь бота в группу, перешли оттуда любое сообщение "
        "боту @userinfobot — он покажет ID чата.\n\n"
        "Убрать группу — пришли <code>-</code>.",
        reply_markup=keyboards.settings_back(),
    )
    await callback.answer()


@router.message(SettingsForm.group)
async def save_group(
    message: Message, conn: aiosqlite.Connection, config: Config, state: FSMContext
) -> None:
    raw = (message.text or "").strip()
    if raw in ("-", "—"):
        await settings_repo.set_value(conn, KEY_GROUP_CHAT, "")
        await settings_repo.set_value(conn, KEY_ANNOUNCE, "0")
    else:
        try:
            chat_id = int(raw)
        except ValueError:
            await message.answer("Это не похоже на ID чата. Нужно число, например -1001234567890.")
            return
        await settings_repo.set_value(conn, KEY_GROUP_CHAT, chat_id)
        await settings_repo.set_value(conn, KEY_ANNOUNCE, "1")
        log.info("группа для объявлений → %s", chat_id)

    await state.clear()
    await _show(message, conn, config)


@router.callback_query(SettingsCB.filter(F.action == "template"))
async def ask_template(
    callback: CallbackQuery, conn: aiosqlite.Connection, config: Config, state: FSMContext
) -> None:
    current = await settings_repo.effective(conn, config)
    await state.set_state(SettingsForm.template)
    await callback.message.edit_text(
        "<b>Шаблон сообщения с картой</b>\n\n"
        f"<code>{escape(current.template)}</code>\n\n"
        f"Доступные подстановки:\n<code>{PLACEHOLDERS}</code>\n\n"
        "Пришли новый текст шаблона.",
        reply_markup=keyboards.template_actions(),
    )
    await callback.answer()


@router.message(SettingsForm.template)
async def save_template(
    message: Message, conn: aiosqlite.Connection, config: Config, state: FSMContext
) -> None:
    text = (message.text or "").strip()
    if not text:
        await message.answer("Пустой шаблон не пойдёт.")
        return
    await settings_repo.set_value(conn, KEY_TEMPLATE, text)
    await state.clear()
    log.info("шаблон сообщения изменён")
    await _show(message, conn, config)


@router.callback_query(SettingsCB.filter(F.action == "template_reset"))
async def reset_template(
    callback: CallbackQuery, conn: aiosqlite.Connection, config: Config, state: FSMContext
) -> None:
    await settings_repo.set_value(conn, KEY_TEMPLATE, None)
    await state.clear()
    await callback.answer("Вернул стандартный шаблон")
    await _show(callback, conn, config)


def _read_int(raw: str | None, *, low: int, high: int) -> int | None:
    try:
        value = int((raw or "").strip())
    except ValueError:
        return None
    return value if low <= value <= high else None


@router.callback_query(SettingsCB.filter(F.action == "board"))
async def ask_board(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(SettingsForm.board)
    await callback.message.edit_text(
        "Куда отправлять постеры раскладов?\n\n"
        "Пришли ID чата или канала. У супергрупп и каналов он начинается на "
        "<code>-100</code>, бот должен быть там администратором.\n\n"
        "Постер показывает карты всех участников разом — это не то, что стоит "
        "публиковать до встречи.\n\n"
        "Вернуть к группе объявлений — пришли <code>-</code>.",
        reply_markup=keyboards.settings_back(),
    )
    await callback.answer()


@router.message(SettingsForm.board)
async def save_board(
    message: Message, conn: aiosqlite.Connection, config: Config, state: FSMContext
) -> None:
    raw = (message.text or "").strip()
    if raw in ("-", "—"):
        await settings_repo.set_value(conn, KEY_BOARD_CHAT, None)
    else:
        try:
            chat_id = int(raw)
        except ValueError:
            await message.answer("Это не похоже на ID чата. Нужно число, например -1001234567890.")
            return
        await settings_repo.set_value(conn, KEY_BOARD_CHAT, chat_id)
        log.info("чат для постеров → %s", chat_id)

    await state.clear()
    await _show(message, conn, config)

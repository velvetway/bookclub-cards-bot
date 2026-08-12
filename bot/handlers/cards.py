"""Колода: список, добавление, правка, включение и выключение карт."""

from __future__ import annotations

import logging

import aiosqlite
from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message

from bot import keyboards, texts
from bot.callbacks import CardCB, MenuCB
from bot.filters import IsAdmin, IsPrivate
from bot.models import CARD_TYPE_NAMES, DECK_MAIN
from bot.storage import cards as cards_repo

log = logging.getLogger(__name__)

router = Router(name="cards")
router.message.filter(IsPrivate(), IsAdmin())
router.callback_query.filter(IsAdmin())


class CardForm(StatesGroup):
    new_title = State()
    new_hint = State()
    edit_title = State()
    edit_hint = State()


async def _select(
    conn: aiosqlite.Connection, active: str
) -> tuple[list, str]:
    """Карты под текущий фильтр и подпись к нему."""
    if active.startswith(keyboards.DECK_FILTER):
        key = active[len(keyboards.DECK_FILTER) :]
        deck = next((d for d in await cards_repo.decks(conn) if d.key == key), None)
        # list_by_deck отдаёт только активные, а в колоде надо видеть и выключенные
        cards = [
            c
            for c in await cards_repo.list_all(conn)
            if (c.book_id is None if key == DECK_MAIN else c.code.startswith(f"{key}-"))
        ]
        return cards, f" · {deck.title}" if deck else ""

    if active in CARD_TYPE_NAMES:
        return await cards_repo.list_all(conn, card_type=active), f" · {CARD_TYPE_NAMES[active]}"

    return await cards_repo.list_all(conn), ""


async def _show_list(
    target: Message | CallbackQuery,
    conn: aiosqlite.Connection,
    page: int = 0,
    active: str | None = None,
) -> None:
    active = active or ""
    cards, label = await _select(conn, active)
    alive = sum(1 for c in cards if c.is_active)

    text = f"<b>Колода{label}</b>\nВсего {len(cards)}, активных {alive}."
    markup = keyboards.cards_list(cards, page, active, await cards_repo.decks(conn))

    if isinstance(target, CallbackQuery):
        await target.message.edit_text(text, reply_markup=markup)
        await target.answer()
    else:
        await target.answer(text, reply_markup=markup)


@router.message(Command("cards"))
async def cmd_cards(message: Message, conn: aiosqlite.Connection, state: FSMContext) -> None:
    await state.clear()
    await _show_list(message, conn)


@router.callback_query(MenuCB.filter(F.action == "cards"))
async def menu_cards(
    callback: CallbackQuery, conn: aiosqlite.Connection, state: FSMContext
) -> None:
    await state.clear()
    await _show_list(callback, conn)


@router.callback_query(CardCB.filter(F.action == "list"))
async def cards_page(
    callback: CallbackQuery, callback_data: CardCB, conn: aiosqlite.Connection, state: FSMContext
) -> None:
    await state.clear()
    await _show_list(callback, conn, callback_data.page, callback_data.value)


@router.callback_query(CardCB.filter(F.action == "noop"))
async def noop(callback: CallbackQuery) -> None:
    await callback.answer()


async def _render_card(
    callback: CallbackQuery, conn: aiosqlite.Connection, card_id: int, page: int
) -> bool:
    card = await cards_repo.get(conn, card_id)
    if card is None:
        return False
    text = f"{texts.card_line(card)}\n\nТип: {CARD_TYPE_NAMES.get(card.type, card.type)}"
    await callback.message.edit_text(text, reply_markup=keyboards.card_actions(card, page))
    return True


@router.callback_query(CardCB.filter(F.action == "open"))
async def open_card(
    callback: CallbackQuery, callback_data: CardCB, conn: aiosqlite.Connection
) -> None:
    if not await _render_card(callback, conn, callback_data.card_id, callback_data.page):
        await callback.answer("Карта не найдена", show_alert=True)
        return
    await callback.answer()


@router.callback_query(CardCB.filter(F.action == "toggle"))
async def toggle_card(
    callback: CallbackQuery, callback_data: CardCB, conn: aiosqlite.Connection
) -> None:
    active = await cards_repo.toggle_active(conn, callback_data.card_id)
    card = await cards_repo.get(conn, callback_data.card_id)
    log.info(
        "карта %s теперь %s",
        card.code if card else callback_data.card_id,
        "активна" if active else "выключена",
    )
    await callback.answer("Включена" if active else "Выключена")
    await _render_card(callback, conn, callback_data.card_id, callback_data.page)


# ------------------------------------------------------------- новая карта


@router.callback_query(CardCB.filter(F.action == "new"))
async def new_card(callback: CallbackQuery) -> None:
    await callback.message.edit_text(
        "Какого типа карта?", reply_markup=keyboards.pick_card_type()
    )
    await callback.answer()


@router.callback_query(CardCB.filter(F.action == "new_type"))
async def new_card_type(
    callback: CallbackQuery, callback_data: CardCB, state: FSMContext
) -> None:
    await state.update_data(card_type=callback_data.value)
    await state.set_state(CardForm.new_title)
    await callback.message.edit_text(
        f"Тип: {CARD_TYPE_NAMES[callback_data.value]}.\n\nПришли название карты."
    )
    await callback.answer()


@router.message(CardForm.new_title)
async def new_card_title(message: Message, state: FSMContext) -> None:
    title = (message.text or "").strip()
    if not title:
        await message.answer("Пустое название. Попробуй ещё раз.")
        return
    await state.update_data(title=title)
    await state.set_state(CardForm.new_hint)
    await message.answer(
        "Теперь пояснение — строка под названием.\nЕсли не нужно, пришли <code>-</code>."
    )


@router.message(CardForm.new_hint)
async def new_card_hint(
    message: Message, conn: aiosqlite.Connection, state: FSMContext
) -> None:
    hint = (message.text or "").strip()
    hint = None if hint in ("-", "—") else hint
    data = await state.get_data()

    card = await cards_repo.create(conn, data["card_type"], data["title"], hint)
    await state.clear()
    log.info("добавлена карта %s %s", card.code, card.title)
    await message.answer(f"Готово: {texts.card_line(card)}")
    await _show_list(message, conn)


# ----------------------------------------------------------------- правка


@router.callback_query(CardCB.filter(F.action == "edit_title"))
async def edit_title(
    callback: CallbackQuery, callback_data: CardCB, state: FSMContext
) -> None:
    await state.update_data(card_id=callback_data.card_id, page=callback_data.page)
    await state.set_state(CardForm.edit_title)
    await callback.message.edit_text("Пришли новое название карты.")
    await callback.answer()


@router.message(CardForm.edit_title)
async def save_title(message: Message, conn: aiosqlite.Connection, state: FSMContext) -> None:
    title = (message.text or "").strip()
    if not title:
        await message.answer("Пустое название. Попробуй ещё раз.")
        return
    data = await state.get_data()
    await cards_repo.update_fields(conn, data["card_id"], title=title)
    await state.clear()
    card = await cards_repo.get(conn, data["card_id"])
    await message.answer(f"Готово: {texts.card_line(card)}" if card else "Готово")
    await _show_list(message, conn, data.get("page", 0))


@router.callback_query(CardCB.filter(F.action == "edit_hint"))
async def edit_hint(
    callback: CallbackQuery, callback_data: CardCB, state: FSMContext
) -> None:
    await state.update_data(card_id=callback_data.card_id, page=callback_data.page)
    await state.set_state(CardForm.edit_hint)
    await callback.message.edit_text(
        "Пришли новое пояснение.\nЧтобы убрать пояснение, пришли <code>-</code>."
    )
    await callback.answer()


@router.message(CardForm.edit_hint)
async def save_hint(message: Message, conn: aiosqlite.Connection, state: FSMContext) -> None:
    hint = (message.text or "").strip()
    data = await state.get_data()
    await cards_repo.update_fields(conn, data["card_id"], hint="" if hint in ("-", "—") else hint)
    await state.clear()
    card = await cards_repo.get(conn, data["card_id"])
    await message.answer(f"Готово: {texts.card_line(card)}" if card else "Готово")
    await _show_list(message, conn, data.get("page", 0))

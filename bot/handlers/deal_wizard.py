"""Мастер раздачи: книга → тип → состав → пул → превью → правка → отправка."""

from __future__ import annotations

import asyncio
import logging
from html import escape

import aiosqlite
from aiogram import Bot, F, Router
from aiogram.exceptions import TelegramAPIError
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import BufferedInputFile, CallbackQuery, Message

from bot import delivery, keyboards, render, service, texts
from bot.callbacks import AssignCB, DealCB, MenuCB, WizardCB
from bot.config import Config
from bot.dealer import NotEnoughCards
from bot.filters import IsAdmin, IsPrivate
from bot.models import (
    BOOK_CURRENT,
    DEAL_CANCELLED,
    DEAL_DRAFT,
    DEAL_PARTIAL,
    DEAL_SENT,
    PHASE_MIXED,
    PHASE_NAMES,
    DECK_MAIN,
    POOL_ALL,
    POOL_BY_TYPE,
    POOL_CUSTOM,
    POOL_DECK,
)
from bot.storage import books as books_repo
from bot.storage import cards as cards_repo
from bot.storage import deals as deals_repo
from bot.storage import settings as settings_repo
from bot.storage import users as users_repo
from bot.timeutil import parse_user_datetime

log = logging.getLogger(__name__)

router = Router(name="deal")
router.message.filter(IsPrivate(), IsAdmin())
router.callback_query.filter(IsAdmin())


class Wizard(StatesGroup):
    book = State()
    new_book_title = State()
    new_book_meeting = State()
    phase = State()
    members = State()
    pool = State()
    custom_pool = State()
    pool_codes = State()


# ------------------------------------------------------------- вспомогательное


async def _show(target: Message | CallbackQuery, text: str, markup=None) -> None:
    """Одинаково отвечает и на команду, и на нажатие кнопки."""
    if isinstance(target, CallbackQuery):
        if target.message is not None:
            try:
                await target.message.edit_text(text, reply_markup=markup)
            except Exception:  # сообщение могло быть с фото или не измениться
                await target.message.answer(text, reply_markup=markup)
        await target.answer()
    else:
        await target.answer(text, reply_markup=markup)


async def _deck_title(conn: aiosqlite.Connection, deal) -> str | None:
    if deal.pool_mode != POOL_DECK:
        return None
    key = (deal.pool_codes or [DECK_MAIN])[0]
    deck = next((d for d in await cards_repo.decks(conn) if d.key == key), None)
    return deck.title if deck else key


async def _preview_text(conn: aiosqlite.Connection, deal, config: Config) -> str:
    book = await books_repo.get(conn, deal.book_id)
    views = await deals_repo.views(conn, deal.id)
    head = texts.preview(
        deal, book, views, config.tz, deck_title=await _deck_title(conn, deal)
    )
    if deal.status == DEAL_DRAFT:
        return head + "\n\n<i>Черновик. Участникам ещё ничего не ушло.</i>"
    return head + f"\n\n<i>{texts.STATUS_NAMES.get(deal.status, deal.status)}</i>"


async def show_preview(
    target: Message | CallbackQuery, conn: aiosqlite.Connection, deal, config: Config
) -> None:
    await _show(target, await _preview_text(conn, deal, config), keyboards.preview_actions(deal))


# --------------------------------------------------------------- вход в мастер


@router.message(Command("deal"))
async def cmd_deal(
    message: Message, conn: aiosqlite.Connection, state: FSMContext, config: Config
) -> None:
    await _enter_wizard(message, conn, state, config)


@router.callback_query(MenuCB.filter(F.action == "deal"))
async def menu_deal(
    callback: CallbackQuery, conn: aiosqlite.Connection, state: FSMContext, config: Config
) -> None:
    await _enter_wizard(callback, conn, state, config)


async def _enter_wizard(
    target: Message | CallbackQuery,
    conn: aiosqlite.Connection,
    state: FSMContext,
    config: Config,
) -> None:
    await state.clear()
    draft = await deals_repo.latest_draft(conn)
    if draft is not None:
        book = await books_repo.get(conn, draft.book_id)
        count = len(await deals_repo.assignments(conn, draft.id))
        text = (
            f"Есть незаконченный черновик №{draft.id}.\n\n"
            f"Книга: {texts.book_line(book)}\n"
            f"Тип: {PHASE_NAMES.get(draft.phase, draft.phase)} · {texts.members_word(count)}"
        )
        await _show(target, text, keyboards.draft_found(draft))
        return
    await _ask_book(target, conn, state)


async def _ask_book(
    target: Message | CallbackQuery, conn: aiosqlite.Connection, state: FSMContext
) -> None:
    await state.set_state(Wizard.book)
    books = await books_repo.list_all(conn)
    if not books:
        await state.set_state(Wizard.new_book_title)
        await _show(target, "Книг пока нет. Пришли название книги одним сообщением.")
        return
    await _show(target, "Какая книга?", keyboards.pick_book(books))


@router.callback_query(DealCB.filter(F.action == "open"))
async def open_draft(
    callback: CallbackQuery, callback_data: DealCB, conn: aiosqlite.Connection, config: Config
) -> None:
    deal = await deals_repo.get(conn, callback_data.deal_id)
    if deal is None:
        await callback.answer("Черновик не найден", show_alert=True)
        return
    await show_preview(callback, conn, deal, config)


@router.callback_query(DealCB.filter(F.action == "drop"))
async def drop_draft(
    callback: CallbackQuery,
    callback_data: DealCB,
    conn: aiosqlite.Connection,
    state: FSMContext,
) -> None:
    await deals_repo.delete_draft(conn, callback_data.deal_id)
    log.info("черновик %s выброшен", callback_data.deal_id)
    await _ask_book(callback, conn, state)


# ------------------------------------------------------------------- шаг книги


@router.callback_query(WizardCB.filter(F.action == "book"))
async def picked_book(
    callback: CallbackQuery, callback_data: WizardCB, conn: aiosqlite.Connection, state: FSMContext
) -> None:
    await state.update_data(book_id=int(callback_data.value))
    await _ask_phase(callback, state)


@router.callback_query(WizardCB.filter(F.action == "newbook"))
async def new_book(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(Wizard.new_book_title)
    await _show(callback, "Название книги. Можно так: <code>Автор — Название</code>")


@router.message(Wizard.new_book_title)
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

    book = await books_repo.create(conn, title=title, author=author, status=BOOK_CURRENT)
    await books_repo.make_current(conn, book.id)
    await state.update_data(book_id=book.id)
    await state.set_state(Wizard.new_book_meeting)
    log.info("создана книга %s: %s", book.id, book.title)
    await message.answer(
        f"Книга «{escape(book.title)}» стала текущей.\n\n"
        "Когда встреча? Формат <code>25.12.2026</code> или <code>25.12.2026 19:30</code>.\n"
        "Можно пропустить — напиши <code>-</code>."
    )


@router.message(Wizard.new_book_meeting)
async def new_book_meeting(
    message: Message, conn: aiosqlite.Connection, state: FSMContext, config: Config
) -> None:
    raw = (message.text or "").strip()
    if raw not in ("-", "—", "нет", "пропустить"):
        moment = parse_user_datetime(raw, config.tz)
        if moment is None:
            await message.answer("Не разобрал дату. Пример: <code>25.12.2026 19:30</code>")
            return
        data = await state.get_data()
        await books_repo.set_meeting(conn, data["book_id"], moment)

    await _ask_phase(message, state)


# -------------------------------------------------------------------- шаг типа


async def _ask_phase(target: Message | CallbackQuery, state: FSMContext) -> None:
    await state.set_state(Wizard.phase)
    await _show(target, "Что раздаём?", keyboards.pick_phase())


@router.callback_query(WizardCB.filter(F.action == "back_book"))
async def back_to_book(
    callback: CallbackQuery, conn: aiosqlite.Connection, state: FSMContext
) -> None:
    await _ask_book(callback, conn, state)


@router.callback_query(WizardCB.filter(F.action == "phase"))
async def picked_phase(
    callback: CallbackQuery, callback_data: WizardCB, conn: aiosqlite.Connection, state: FSMContext
) -> None:
    await state.update_data(phase=callback_data.value)
    users = await users_repo.list_all(conn, only_active=True)
    default = {u.id for u in users if u.reachable}
    await state.update_data(members=sorted(default))
    await _ask_members(callback, conn, state)


# ------------------------------------------------------------------ шаг состава


async def _ask_members(
    target: Message | CallbackQuery,
    conn: aiosqlite.Connection,
    state: FSMContext,
    page: int = 0,
) -> None:
    await state.set_state(Wizard.members)
    data = await state.get_data()
    selected = set(data.get("members", []))
    users = await users_repo.list_all(conn, only_active=True)

    unreachable = [u for u in users if not u.reachable]
    text = [
        f"Кто читает? Выбрано: {len(selected)}.",
    ]
    if unreachable:
        text.append("")
        text.append("🚫 — не нажимал /start, такому бот написать не может.")
    await _show(target, "\n".join(text), keyboards.pick_members(users, selected, page))


@router.callback_query(WizardCB.filter(F.action == "back_phase"))
async def back_to_phase(callback: CallbackQuery, state: FSMContext) -> None:
    await _ask_phase(callback, state)


@router.callback_query(WizardCB.filter(F.action == "members_page"))
async def members_page(
    callback: CallbackQuery, callback_data: WizardCB, conn: aiosqlite.Connection, state: FSMContext
) -> None:
    await _ask_members(callback, conn, state, callback_data.page)


@router.callback_query(WizardCB.filter(F.action == "toggle"))
async def toggle_member(
    callback: CallbackQuery, callback_data: WizardCB, conn: aiosqlite.Connection, state: FSMContext
) -> None:
    user_id = int(callback_data.value)
    data = await state.get_data()
    selected = set(data.get("members", []))

    warning = None
    if user_id in selected:
        selected.discard(user_id)
    else:
        selected.add(user_id)
        user = await users_repo.get(conn, user_id)
        if user and not user.reachable:
            warning = f"{user.display_name} не нажимал /start — сообщение не дойдёт"

    await state.update_data(members=sorted(selected))
    if warning:
        await callback.answer(warning, show_alert=True)
    await _ask_members(callback, conn, state, callback_data.page)


@router.callback_query(WizardCB.filter(F.action == "all_members"))
async def all_members(
    callback: CallbackQuery, conn: aiosqlite.Connection, state: FSMContext
) -> None:
    users = await users_repo.list_all(conn, only_active=True)
    await state.update_data(members=sorted(u.id for u in users if u.reachable))
    await _ask_members(callback, conn, state)


@router.callback_query(WizardCB.filter(F.action == "no_members"))
async def no_members(
    callback: CallbackQuery, conn: aiosqlite.Connection, state: FSMContext
) -> None:
    await state.update_data(members=[])
    await _ask_members(callback, conn, state)


@router.callback_query(WizardCB.filter(F.action == "members_done"))
async def members_done(
    callback: CallbackQuery, conn: aiosqlite.Connection, state: FSMContext
) -> None:
    data = await state.get_data()
    if not data.get("members"):
        await callback.answer("Никто не выбран", show_alert=True)
        return
    await _ask_pool(callback, state, conn)


# --------------------------------------------------------------------- шаг пула


async def _ask_pool(
    target: Message | CallbackQuery, state: FSMContext, conn: aiosqlite.Connection
) -> None:
    await state.set_state(Wizard.pool)
    data = await state.get_data()
    phase = data.get("phase", PHASE_MIXED)
    decks = [d for d in await cards_repo.decks(conn) if d.active]

    text = "Из чего раздаём?"
    if len(decks) > 1:
        text += "\n\n<i>Колода целиком — карты только из неё. «Все карты сразу» — общий котёл.</i>"
    await _show(target, text, keyboards.pick_pool(phase, decks))


@router.callback_query(WizardCB.filter(F.action == "back_members"))
async def back_to_members(
    callback: CallbackQuery, conn: aiosqlite.Connection, state: FSMContext
) -> None:
    await _ask_members(callback, conn, state)


@router.callback_query(WizardCB.filter(F.action == "deck"))
async def picked_deck(
    callback: CallbackQuery,
    callback_data: WizardCB,
    conn: aiosqlite.Connection,
    state: FSMContext,
    config: Config,
) -> None:
    """Колода целиком: пул — только её карты."""
    await state.update_data(pool_mode=POOL_DECK, deck_key=callback_data.value)
    await _create_draft(callback, conn, state, config)


@router.callback_query(WizardCB.filter(F.action == "pool"))
async def picked_pool(
    callback: CallbackQuery,
    callback_data: WizardCB,
    conn: aiosqlite.Connection,
    state: FSMContext,
    config: Config,
) -> None:
    mode = callback_data.value
    await state.update_data(pool_mode=mode)

    if mode == POOL_CUSTOM:
        await state.update_data(pool_ids=[])
        await _ask_custom_pool(callback, conn, state)
        return

    await _create_draft(callback, conn, state, config)


async def _ask_custom_pool(
    target: Message | CallbackQuery,
    conn: aiosqlite.Connection,
    state: FSMContext,
    page: int = 0,
) -> None:
    await state.set_state(Wizard.custom_pool)
    data = await state.get_data()
    selected = set(data.get("pool_ids", []))
    cards = await cards_repo.list_all(conn, only_active=True)
    need = len(data.get("members", []))

    text = (
        f"Отметь карты. Выбрано: {len(selected)}, участников: {need}.\n\n"
        "Можно ввести кодами строкой: <code>INS-03 INS-07 OPT-02</code>"
    )
    await _show(target, text, keyboards.pick_custom_pool(cards, selected, page))


@router.callback_query(WizardCB.filter(F.action == "back_pool"))
async def back_to_pool(
    callback: CallbackQuery, state: FSMContext, conn: aiosqlite.Connection
) -> None:
    await _ask_pool(callback, state, conn)


@router.callback_query(WizardCB.filter(F.action == "pool_page"))
async def pool_page(
    callback: CallbackQuery, callback_data: WizardCB, conn: aiosqlite.Connection, state: FSMContext
) -> None:
    await _ask_custom_pool(callback, conn, state, callback_data.page)


@router.callback_query(WizardCB.filter(F.action == "pool_toggle"))
async def pool_toggle(
    callback: CallbackQuery, callback_data: WizardCB, conn: aiosqlite.Connection, state: FSMContext
) -> None:
    card_id = int(callback_data.value)
    data = await state.get_data()
    selected = set(data.get("pool_ids", []))
    selected.symmetric_difference_update({card_id})
    await state.update_data(pool_ids=sorted(selected))
    await _ask_custom_pool(callback, conn, state, callback_data.page)


@router.callback_query(WizardCB.filter(F.action == "pool_clear"))
async def pool_clear(
    callback: CallbackQuery, conn: aiosqlite.Connection, state: FSMContext
) -> None:
    await state.update_data(pool_ids=[])
    await _ask_custom_pool(callback, conn, state)


@router.callback_query(WizardCB.filter(F.action == "pool_codes"))
async def pool_codes_prompt(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(Wizard.pool_codes)
    await _show(
        callback,
        "Пришли коды карт одной строкой:\n<code>INS-03 INS-07 OPT-02</code>\n\n"
        "Они добавятся к уже отмеченным.",
    )


@router.message(Wizard.pool_codes)
async def pool_codes_input(
    message: Message, conn: aiosqlite.Connection, state: FSMContext
) -> None:
    raw = (message.text or "").replace(",", " ").split()
    data = await state.get_data()
    selected = set(data.get("pool_ids", []))

    unknown = []
    for code in raw:
        card = await cards_repo.get_by_code(conn, code)
        if card is None:
            unknown.append(code)
        else:
            selected.add(card.id)

    await state.update_data(pool_ids=sorted(selected))
    if unknown:
        await message.answer("Не нашёл коды: " + ", ".join(escape(c) for c in unknown))
    await _ask_custom_pool(message, conn, state)


@router.callback_query(WizardCB.filter(F.action == "pool_done"))
async def pool_done(
    callback: CallbackQuery, conn: aiosqlite.Connection, state: FSMContext, config: Config
) -> None:
    data = await state.get_data()
    if not data.get("pool_ids"):
        await callback.answer("Не выбрано ни одной карты", show_alert=True)
        return
    await _create_draft(callback, conn, state, config)


@router.callback_query(WizardCB.filter(F.action == "noop"))
async def noop(callback: CallbackQuery) -> None:
    await callback.answer()


# ------------------------------------------------------------ создание черновика


async def _create_draft(
    target: Message | CallbackQuery,
    conn: aiosqlite.Connection,
    state: FSMContext,
    config: Config,
) -> None:
    data = await state.get_data()
    members = list(data.get("members", []))
    pool_mode = data.get("pool_mode", POOL_ALL)

    pool_codes = None
    if pool_mode == POOL_DECK:
        pool_codes = [data.get("deck_key", DECK_MAIN)]
    elif pool_mode == POOL_CUSTOM:
        chosen = await cards_repo.get_many(conn, list(data.get("pool_ids", [])))
        pool_codes = [c.code for c in chosen.values()]

    deal = await deals_repo.create(
        conn,
        book_id=data["book_id"],
        phase=data.get("phase", PHASE_MIXED),
        pool_mode=pool_mode,
        pool_codes=pool_codes,
    )
    settings = await settings_repo.effective(conn, config)

    try:
        await service.generate(conn, deal, members, settings)
    except NotEnoughCards as exc:
        await deals_repo.delete_draft(conn, deal.id)
        word = texts.plural(exc.missing, "карты", "карт", "карт")
        await _show(
            target,
            f"Не хватает {exc.missing} {word}: участников {exc.needed}, "
            f"в пуле {exc.available}.\n\nДобавь карт в пул или убери участников.",
            keyboards.pick_pool(data.get("phase", PHASE_MIXED), await cards_repo.decks(conn)),
        )
        return

    await state.clear()
    await show_preview(target, conn, deal, config)


# ------------------------------------------------------------------ превью


@router.callback_query(DealCB.filter(F.action == "preview"))
async def back_to_preview(
    callback: CallbackQuery, callback_data: DealCB, conn: aiosqlite.Connection, config: Config
) -> None:
    deal = await deals_repo.get(conn, callback_data.deal_id)
    if deal is None:
        await callback.answer("Раздача не найдена", show_alert=True)
        return
    await show_preview(callback, conn, deal, config)


@router.callback_query(DealCB.filter(F.action == "regen"))
async def regenerate(
    callback: CallbackQuery, callback_data: DealCB, conn: aiosqlite.Connection, config: Config
) -> None:
    deal = await deals_repo.get(conn, callback_data.deal_id)
    if deal is None or deal.status != DEAL_DRAFT:
        await callback.answer("Перегенерировать можно только черновик", show_alert=True)
        return

    members = [a.user_id for a in await deals_repo.assignments(conn, deal.id)]
    settings = await settings_repo.effective(conn, config)
    try:
        await service.generate(conn, deal, members, settings)
    except NotEnoughCards as exc:
        await callback.answer(f"Не хватает карт: {exc.missing}", show_alert=True)
        return
    await show_preview(callback, conn, deal, config)


@router.callback_query(DealCB.filter(F.action == "cancel"))
async def cancel_deal(
    callback: CallbackQuery, callback_data: DealCB, conn: aiosqlite.Connection, state: FSMContext
) -> None:
    deal = await deals_repo.get(conn, callback_data.deal_id)
    if deal is None:
        await callback.answer("Раздача не найдена", show_alert=True)
        return
    if deal.status == DEAL_DRAFT:
        await deals_repo.delete_draft(conn, deal.id)
    else:
        await deals_repo.set_status(conn, deal.id, DEAL_CANCELLED)
    await state.clear()
    log.info("раздача %s отменена", deal.id)

    from bot.handlers.common import menu_text

    await _show(callback, await menu_text(conn), keyboards.main_menu())


# ------------------------------------------------------------------- правка


@router.callback_query(DealCB.filter(F.action == "edit"))
async def edit_list(
    callback: CallbackQuery, callback_data: DealCB, conn: aiosqlite.Connection, config: Config
) -> None:
    deal = await deals_repo.get(conn, callback_data.deal_id)
    if deal is None:
        await callback.answer("Раздача не найдена", show_alert=True)
        return
    views = await deals_repo.views(conn, deal.id)
    await _show(callback, "Кого правим?", keyboards.edit_rows(views, deal))


async def _open_row(
    callback: CallbackQuery, conn: aiosqlite.Connection, assignment_id: int, config: Config
) -> None:
    assignment = await deals_repo.get_assignment(conn, assignment_id)
    if assignment is None:
        await callback.answer("Строка не найдена", show_alert=True)
        return

    views = await deals_repo.views(conn, assignment.deal_id)
    view = next((v for v in views if v.assignment.id == assignment_id), None)
    deal = await deals_repo.get(conn, assignment.deal_id)
    if view is None or deal is None:
        await callback.answer("Строка не найдена", show_alert=True)
        return

    hint = f"\n<i>{escape(view.card.hint)}</i>" if view.card.hint else ""
    text = (
        f"<b>{escape(view.user.display_name)}</b>\n"
        f"{view.card.code} {escape(view.card.title)}{hint}"
    )
    await _show(callback, text, keyboards.row_actions(view, deal))


@router.callback_query(AssignCB.filter(F.action == "open"))
async def open_row(
    callback: CallbackQuery, callback_data: AssignCB, conn: aiosqlite.Connection, config: Config
) -> None:
    await _open_row(callback, conn, callback_data.assignment_id, config)


@router.callback_query(AssignCB.filter(F.action == "reroll"))
async def reroll_row(
    callback: CallbackQuery, callback_data: AssignCB, conn: aiosqlite.Connection, config: Config
) -> None:
    assignment = await deals_repo.get_assignment(conn, callback_data.assignment_id)
    if assignment is None:
        await callback.answer("Строка не найдена", show_alert=True)
        return
    deal = await deals_repo.get(conn, assignment.deal_id)
    settings = await settings_repo.effective(conn, config)

    try:
        await service.reroll(conn, deal, assignment, settings)
    except NotEnoughCards:
        await callback.answer("Свободных карт в пуле нет", show_alert=True)
        return
    await _open_row(callback, conn, assignment.id, config)


@router.callback_query(AssignCB.filter(F.action == "manual"))
async def manual_pick(
    callback: CallbackQuery, callback_data: AssignCB, conn: aiosqlite.Connection
) -> None:
    assignment = await deals_repo.get_assignment(conn, callback_data.assignment_id)
    if assignment is None:
        await callback.answer("Строка не найдена", show_alert=True)
        return
    deal = await deals_repo.get(conn, assignment.deal_id)
    pool = await service.resolve_pool(conn, deal)
    taken = {a.card_id for a in await deals_repo.assignments(conn, deal.id)}

    await _show(
        callback,
        "Какую карту поставить? Занятая карта обменяется с тем, у кого она сейчас.",
        keyboards.pick_manual_card(pool, assignment.id, callback_data.page, taken),
    )


@router.callback_query(AssignCB.filter(F.action == "manual_set"))
async def manual_set(
    callback: CallbackQuery, callback_data: AssignCB, conn: aiosqlite.Connection, config: Config
) -> None:
    assignment = await deals_repo.get_assignment(conn, callback_data.assignment_id)
    if assignment is None:
        await callback.answer("Строка не найдена", show_alert=True)
        return
    deal = await deals_repo.get(conn, assignment.deal_id)
    result = await service.set_card_manually(conn, deal, assignment, callback_data.value)
    await callback.answer("Обменялись картами" if result == "swapped" else "Готово")
    await _open_row(callback, conn, assignment.id, config)


@router.callback_query(AssignCB.filter(F.action == "swap"))
async def swap_pick(
    callback: CallbackQuery, callback_data: AssignCB, conn: aiosqlite.Connection
) -> None:
    assignment = await deals_repo.get_assignment(conn, callback_data.assignment_id)
    if assignment is None:
        await callback.answer("Строка не найдена", show_alert=True)
        return
    deal = await deals_repo.get(conn, assignment.deal_id)
    views = await deals_repo.views(conn, deal.id)
    await _show(callback, "С кем меняемся?", keyboards.pick_swap_target(views, assignment.id, deal))


@router.callback_query(AssignCB.filter(F.action == "swap_with"))
async def swap_with(
    callback: CallbackQuery, callback_data: AssignCB, conn: aiosqlite.Connection, config: Config
) -> None:
    await deals_repo.swap_cards(conn, callback_data.assignment_id, callback_data.value)
    await callback.answer("Обменялись")
    await _open_row(callback, conn, callback_data.assignment_id, config)


@router.callback_query(AssignCB.filter(F.action == "drop"))
async def drop_row(
    callback: CallbackQuery, callback_data: AssignCB, conn: aiosqlite.Connection, config: Config
) -> None:
    assignment = await deals_repo.get_assignment(conn, callback_data.assignment_id)
    if assignment is None:
        await callback.answer("Строка не найдена", show_alert=True)
        return
    deal = await deals_repo.get(conn, assignment.deal_id)
    await deals_repo.remove_assignment(conn, assignment.id)
    await callback.answer("Участник убран из раздачи")
    await show_preview(callback, conn, deal, config)


# ----------------------------------------------------------------- отправка


@router.callback_query(DealCB.filter(F.action == "send"))
async def ask_send(
    callback: CallbackQuery, callback_data: DealCB, conn: aiosqlite.Connection, config: Config
) -> None:
    deal = await deals_repo.get(conn, callback_data.deal_id)
    if deal is None:
        await callback.answer("Раздача не найдена", show_alert=True)
        return

    if deal.status in (DEAL_SENT, DEAL_PARTIAL):
        await _show(
            callback,
            "Эта раздача уже отправлена. Отправить всем ещё раз?",
            keyboards.confirm_send(deal, resend=True),
        )
        return

    views = await deals_repo.views(conn, deal.id)
    unreachable = [v for v in views if not v.user.reachable]
    warning = ""
    if unreachable:
        names = ", ".join(escape(v.user.display_name) for v in unreachable)
        warning = f"\n\n🚫 Не дойдёт до: {names}"

    await _show(
        callback,
        f"Отправить карты? Получателей: {len(views)}.{warning}",
        keyboards.confirm_send(deal),
    )


@router.callback_query(DealCB.filter(F.action.in_({"send_confirm", "resend_confirm", "retry"})))
async def do_send(
    callback: CallbackQuery,
    callback_data: DealCB,
    conn: aiosqlite.Connection,
    config: Config,
    bot: Bot,
) -> None:
    deal = await deals_repo.get(conn, callback_data.deal_id)
    if deal is None:
        await callback.answer("Раздача не найдена", show_alert=True)
        return

    only_failed = callback_data.action == "retry"
    settings = await settings_repo.effective(conn, config)

    await callback.answer("Отправляю…")
    if callback.message:
        await callback.message.edit_text("Отправляю карты…")

    views = await delivery.deliver(bot, conn, deal, settings, config.tz, only_failed=only_failed)
    deal = await deals_repo.get(conn, deal.id)

    delivered = sum(1 for v in views if v.assignment.status == "sent")
    posted = False
    if callback_data.action == "send_confirm" and delivered:
        posted = await delivery.announce(bot, conn, deal, settings, config.tz, delivered)

    report = texts.delivery_report(views, config.tz)
    if posted:
        report += "\n\nОбъявление в группе опубликовано."

    await _show(callback, report, keyboards.report_actions(deal, views))


BOARD_WARNING = (
    "На постере видны карты всех участников. До встречи в общий чат такое "
    "лучше не отправлять — интрига в том, что чужие карты неизвестны."
)


async def _build_board(conn: aiosqlite.Connection, deal, config: Config) -> bytes | None:
    views = await deals_repo.views(conn, deal.id)
    if not views:
        return None
    book = await books_repo.get(conn, deal.book_id)
    return await asyncio.to_thread(render.deal_board, views, deal, book, config.tz)


@router.callback_query(DealCB.filter(F.action == "board"))
async def show_board(
    callback: CallbackQuery,
    callback_data: DealCB,
    conn: aiosqlite.Connection,
    config: Config,
    bot: Bot,
) -> None:
    """Постер расклада — сначала только админу, чтобы было что посмотреть до отправки."""
    deal = await deals_repo.get(conn, callback_data.deal_id)
    if deal is None:
        await callback.answer("Раздача не найдена", show_alert=True)
        return

    await callback.answer("Собираю…")
    picture = await _build_board(conn, deal, config)
    if picture is None:
        await callback.answer("В раздаче никого нет", show_alert=True)
        return

    settings = await settings_repo.effective(conn, config)
    await bot.send_photo(
        callback.from_user.id,
        BufferedInputFile(picture, f"deal-{deal.id}.jpg"),
        caption=BOARD_WARNING,
        reply_markup=keyboards.board_actions(deal, can_send=settings.board_chat_id is not None),
    )


@router.callback_query(DealCB.filter(F.action == "board_chat"))
async def send_board(
    callback: CallbackQuery,
    callback_data: DealCB,
    conn: aiosqlite.Connection,
    config: Config,
    bot: Bot,
) -> None:
    deal = await deals_repo.get(conn, callback_data.deal_id)
    settings = await settings_repo.effective(conn, config)
    if deal is None:
        await callback.answer("Раздача не найдена", show_alert=True)
        return
    if settings.board_chat_id is None:
        await callback.answer("Сначала задай чат в /settings", show_alert=True)
        return

    await callback.answer("Отправляю…")
    picture = await _build_board(conn, deal, config)
    if picture is None:
        await callback.answer("В раздаче никого нет", show_alert=True)
        return

    book = await books_repo.get(conn, deal.book_id)
    caption = f"Расклад: {texts.book_line(book)} · {texts.members_word(len(await deals_repo.assignments(conn, deal.id)))}"
    try:
        await bot.send_photo(
            settings.board_chat_id, BufferedInputFile(picture, f"deal-{deal.id}.jpg"), caption=caption
        )
    except TelegramAPIError as exc:
        log.warning("не удалось отправить постер в чат: %s", exc)
        await callback.answer(f"Не ушло: {exc}"[:180], show_alert=True)
        return

    log.info("постер раздачи %s отправлен в чат %s", deal.id, settings.board_chat_id)
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.answer("Постер отправлен в чат.")


@router.callback_query(DealCB.filter(F.action == "resend"))
async def ask_resend(
    callback: CallbackQuery, callback_data: DealCB, conn: aiosqlite.Connection
) -> None:
    deal = await deals_repo.get(conn, callback_data.deal_id)
    if deal is None:
        await callback.answer("Раздача не найдена", show_alert=True)
        return
    await _show(
        callback,
        "Отправить те же карты ещё раз всем участникам?\n"
        "<i>Карты не перевыбираются — придёт ровно то же самое.</i>",
        keyboards.confirm_send(deal, resend=True),
    )

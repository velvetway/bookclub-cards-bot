"""Инлайн-клавиатуры. Всё управление — кнопками, с телефона."""

from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.callbacks import (
    AssignCB,
    BookCB,
    CardCB,
    CoverCB,
    DealCB,
    MemberCB,
    MenuCB,
    RerollCB,
    SettingsCB,
    WizardCB,
)
from bot.models import (
    ASSIGN_FAILED,
    CARD_TYPE_NAMES,
    CARD_TYPES,
    DEAL_DRAFT,
    INSERT,
    OPTICS,
    PHASE_MIXED,
    PHASE_NAMES,
    POOL_ALL,
    POOL_BY_TYPE,
    POOL_CUSTOM,
    RATING,
    Book,
    Card,
    Deal,
    User,
)
from bot.storage.deals import AssignmentView

CARDS_PER_PAGE = 8
MEMBERS_PER_PAGE = 10


def main_menu() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="🎴 Раздача", callback_data=MenuCB(action="deal"))
    kb.button(text="📚 Книги", callback_data=MenuCB(action="books"))
    kb.button(text="🗂 Колода", callback_data=MenuCB(action="cards"))
    kb.button(text="👥 Участники", callback_data=MenuCB(action="members"))
    kb.button(text="👀 Кто что получил", callback_data=MenuCB(action="who"))
    kb.button(text="📊 Статистика", callback_data=MenuCB(action="stats"))
    kb.button(text="🖼 Обложка в группу", callback_data=MenuCB(action="cover"))
    kb.button(text="⚙️ Настройки", callback_data=MenuCB(action="settings"))
    kb.adjust(1, 2, 2, 2, 1)
    return kb.as_markup()


def cover_actions(cover, others: list, *, can_send: bool) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    if can_send:
        kb.button(text="📣 Отправить в группу", callback_data=CoverCB(action="send", code=cover.code))
    for other in others:
        kb.button(text=f"🔄 {other.title}"[:60], callback_data=CoverCB(action="show", code=other.code))
    kb.button(text="‹ В меню", callback_data=MenuCB(action="root"))
    kb.adjust(1)
    return kb.as_markup()


def back_to_menu(text: str = "‹ В меню") -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text=text, callback_data=MenuCB(action="root"))
    return kb.as_markup()


# ------------------------------------------------------------ мастер раздачи


def draft_found(deal: Deal) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text=f"↩️ Продолжить черновик №{deal.id}", callback_data=DealCB(action="open", deal_id=deal.id))
    kb.button(text="🗑 Выбросить и начать заново", callback_data=DealCB(action="drop", deal_id=deal.id))
    kb.button(text="‹ В меню", callback_data=MenuCB(action="root"))
    kb.adjust(1)
    return kb.as_markup()


def pick_book(books: list[Book], *, allow_new: bool = True) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for book in books:
        mark = "▶️ " if book.status == "current" else ""
        kb.button(text=f"{mark}{book.title}"[:60], callback_data=WizardCB(action="book", value=str(book.id)))
    if allow_new:
        kb.button(text="➕ Новая книга", callback_data=WizardCB(action="newbook"))
    kb.button(text="‹ В меню", callback_data=MenuCB(action="root"))
    kb.adjust(1)
    return kb.as_markup()


def pick_phase() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for phase in (OPTICS, INSERT, RATING, PHASE_MIXED):
        kb.button(text=PHASE_NAMES[phase].capitalize(), callback_data=WizardCB(action="phase", value=phase))
    kb.button(text="‹ Назад", callback_data=WizardCB(action="back_book"))
    kb.adjust(2, 2, 1)
    return kb.as_markup()


def pick_members(
    users: list[User], selected: set[int], page: int = 0
) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    start = page * MEMBERS_PER_PAGE
    chunk = users[start : start + MEMBERS_PER_PAGE]

    for user in chunk:
        box = "✅" if user.id in selected else "⬜️"
        warn = "" if user.reachable else " 🚫"
        kb.button(
            text=f"{box} {user.display_name}{warn}"[:60],
            callback_data=WizardCB(action="toggle", value=str(user.id), page=page),
        )
    kb.adjust(1)

    nav = []
    if start > 0:
        nav.append(
            InlineKeyboardButton(
                text="‹", callback_data=WizardCB(action="members_page", page=page - 1).pack()
            )
        )
    if start + MEMBERS_PER_PAGE < len(users):
        nav.append(
            InlineKeyboardButton(
                text="›", callback_data=WizardCB(action="members_page", page=page + 1).pack()
            )
        )
    if nav:
        kb.row(*nav)

    kb.row(
        InlineKeyboardButton(text="Все активные", callback_data=WizardCB(action="all_members").pack()),
        InlineKeyboardButton(text="Снять всех", callback_data=WizardCB(action="no_members").pack()),
    )
    kb.row(InlineKeyboardButton(text="Далее ›", callback_data=WizardCB(action="members_done").pack()))
    kb.row(InlineKeyboardButton(text="‹ Назад", callback_data=WizardCB(action="back_phase").pack()))
    return kb.as_markup()


def pick_pool(phase: str) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="Вся колода", callback_data=WizardCB(action="pool", value=POOL_ALL))
    if phase != PHASE_MIXED:
        kb.button(
            text=f"Только {PHASE_NAMES.get(phase, phase)}",
            callback_data=WizardCB(action="pool", value=POOL_BY_TYPE),
        )
    kb.button(text="Произвольный набор", callback_data=WizardCB(action="pool", value=POOL_CUSTOM))
    kb.button(text="‹ Назад", callback_data=WizardCB(action="back_members"))
    kb.adjust(1)
    return kb.as_markup()


def pick_custom_pool(cards: list[Card], selected: set[int], page: int = 0) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    start = page * CARDS_PER_PAGE
    chunk = cards[start : start + CARDS_PER_PAGE]

    for card in chunk:
        box = "✅" if card.id in selected else "⬜️"
        kb.button(
            text=f"{box} {card.code} {card.title}"[:60],
            callback_data=WizardCB(action="pool_toggle", value=str(card.id), page=page),
        )
    kb.adjust(1)

    nav = []
    if start > 0:
        nav.append(
            InlineKeyboardButton(
                text="‹", callback_data=WizardCB(action="pool_page", page=page - 1).pack()
            )
        )
    nav.append(
        InlineKeyboardButton(
            text=f"{page + 1}/{max(1, (len(cards) + CARDS_PER_PAGE - 1) // CARDS_PER_PAGE)}",
            callback_data=WizardCB(action="noop").pack(),
        )
    )
    if start + CARDS_PER_PAGE < len(cards):
        nav.append(
            InlineKeyboardButton(
                text="›", callback_data=WizardCB(action="pool_page", page=page + 1).pack()
            )
        )
    kb.row(*nav)

    kb.row(
        InlineKeyboardButton(text="⌨️ Ввести кодами", callback_data=WizardCB(action="pool_codes").pack())
    )
    kb.row(
        InlineKeyboardButton(text="Готово ›", callback_data=WizardCB(action="pool_done").pack()),
        InlineKeyboardButton(text="Снять всё", callback_data=WizardCB(action="pool_clear").pack()),
    )
    kb.row(InlineKeyboardButton(text="‹ Назад", callback_data=WizardCB(action="back_pool").pack()))
    return kb.as_markup()


# ------------------------------------------------------------------ превью


def preview_actions(deal: Deal) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="🎲 Перегенерировать", callback_data=DealCB(action="regen", deal_id=deal.id))
    kb.button(text="✏️ Править", callback_data=DealCB(action="edit", deal_id=deal.id))
    kb.button(text="📨 Отправить", callback_data=DealCB(action="send", deal_id=deal.id))
    kb.button(text="🗑 Отменить раздачу", callback_data=DealCB(action="cancel", deal_id=deal.id))
    kb.button(text="‹ В меню", callback_data=MenuCB(action="root"))
    kb.adjust(2, 1, 1, 1)
    return kb.as_markup()


def edit_rows(views: list[AssignmentView], deal: Deal) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for index, view in enumerate(views, start=1):
        kb.button(
            text=f"{index}. {view.user.display_name} — {view.card.code}"[:60],
            callback_data=AssignCB(action="open", assignment_id=view.assignment.id),
        )
    kb.button(text="‹ К превью", callback_data=DealCB(action="preview", deal_id=deal.id))
    kb.adjust(1)
    return kb.as_markup()


def row_actions(view: AssignmentView, deal: Deal) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="🎲 Реролл", callback_data=AssignCB(action="reroll", assignment_id=view.assignment.id))
    kb.button(text="🗂 Заменить вручную", callback_data=AssignCB(action="manual", assignment_id=view.assignment.id))
    kb.button(text="🔁 Обменять с…", callback_data=AssignCB(action="swap", assignment_id=view.assignment.id))
    kb.button(text="🚫 Убрать участника", callback_data=AssignCB(action="drop", assignment_id=view.assignment.id))
    kb.button(text="‹ К списку", callback_data=DealCB(action="edit", deal_id=deal.id))
    kb.adjust(2, 1, 1, 1)
    return kb.as_markup()


def pick_swap_target(views: list[AssignmentView], source_id: int, deal: Deal) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for view in views:
        if view.assignment.id == source_id:
            continue
        kb.button(
            text=f"{view.user.display_name} — {view.card.code}"[:60],
            callback_data=AssignCB(action="swap_with", assignment_id=source_id, value=view.assignment.id),
        )
    kb.button(text="‹ Назад", callback_data=AssignCB(action="open", assignment_id=source_id))
    kb.adjust(1)
    return kb.as_markup()


def pick_manual_card(
    cards: list[Card], assignment_id: int, page: int = 0, taken: set[int] | None = None
) -> InlineKeyboardMarkup:
    taken = taken or set()
    kb = InlineKeyboardBuilder()
    start = page * CARDS_PER_PAGE
    chunk = cards[start : start + CARDS_PER_PAGE]

    for card in chunk:
        mark = "· занята " if card.id in taken else ""
        kb.button(
            text=f"{mark}{card.code} {card.title}"[:60],
            callback_data=AssignCB(
                action="manual_set", assignment_id=assignment_id, value=card.id, page=page
            ),
        )
    kb.adjust(1)

    nav = []
    if start > 0:
        nav.append(
            InlineKeyboardButton(
                text="‹",
                callback_data=AssignCB(action="manual", assignment_id=assignment_id, page=page - 1).pack(),
            )
        )
    if start + CARDS_PER_PAGE < len(cards):
        nav.append(
            InlineKeyboardButton(
                text="›",
                callback_data=AssignCB(action="manual", assignment_id=assignment_id, page=page + 1).pack(),
            )
        )
    if nav:
        kb.row(*nav)
    kb.row(
        InlineKeyboardButton(
            text="‹ Назад", callback_data=AssignCB(action="open", assignment_id=assignment_id).pack()
        )
    )
    return kb.as_markup()


def confirm_send(deal: Deal, *, resend: bool = False) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    action = "resend_confirm" if resend else "send_confirm"
    kb.button(text="✅ Да, отправить", callback_data=DealCB(action=action, deal_id=deal.id))
    kb.button(text="‹ Назад", callback_data=DealCB(action="preview", deal_id=deal.id))
    kb.adjust(1)
    return kb.as_markup()


def report_actions(deal: Deal, views: list[AssignmentView]) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    if any(v.assignment.status == ASSIGN_FAILED for v in views):
        kb.button(text="🔄 Повторить недоставленные", callback_data=DealCB(action="retry", deal_id=deal.id))
    kb.button(text="📨 Отправить заново всем", callback_data=DealCB(action="resend", deal_id=deal.id))
    kb.button(text="‹ В меню", callback_data=MenuCB(action="root"))
    kb.adjust(1)
    return kb.as_markup()


# ------------------------------------------------------------------- колода


def cards_list(cards: list[Card], page: int = 0, card_type: str | None = None) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    start = page * CARDS_PER_PAGE
    chunk = cards[start : start + CARDS_PER_PAGE]

    for card in chunk:
        state = "✅" if card.is_active else "⛔️"
        kb.button(
            text=f"{state} {card.code} {card.title}"[:60],
            callback_data=CardCB(action="open", card_id=card.id, page=page),
        )
    kb.adjust(1)

    nav = []
    if start > 0:
        nav.append(
            InlineKeyboardButton(
                text="‹", callback_data=CardCB(action="list", page=page - 1, value=card_type or "").pack()
            )
        )
    nav.append(
        InlineKeyboardButton(
            text=f"{page + 1}/{max(1, (len(cards) + CARDS_PER_PAGE - 1) // CARDS_PER_PAGE)}",
            callback_data=CardCB(action="noop").pack(),
        )
    )
    if start + CARDS_PER_PAGE < len(cards):
        nav.append(
            InlineKeyboardButton(
                text="›", callback_data=CardCB(action="list", page=page + 1, value=card_type or "").pack()
            )
        )
    kb.row(*nav)

    filters = [
        InlineKeyboardButton(text="Все", callback_data=CardCB(action="list", value="").pack())
    ]
    for type_code in CARD_TYPES:
        filters.append(
            InlineKeyboardButton(
                text=CARD_TYPE_NAMES[type_code].capitalize(),
                callback_data=CardCB(action="list", value=type_code).pack(),
            )
        )
    kb.row(*filters[:2])
    kb.row(*filters[2:])
    kb.row(InlineKeyboardButton(text="➕ Добавить карту", callback_data=CardCB(action="new").pack()))
    kb.row(InlineKeyboardButton(text="‹ В меню", callback_data=MenuCB(action="root").pack()))
    return kb.as_markup()


def card_actions(card: Card, page: int = 0) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(
        text="⛔️ Выключить" if card.is_active else "✅ Включить",
        callback_data=CardCB(action="toggle", card_id=card.id, page=page),
    )
    kb.button(text="✏️ Название", callback_data=CardCB(action="edit_title", card_id=card.id, page=page))
    kb.button(text="✏️ Пояснение", callback_data=CardCB(action="edit_hint", card_id=card.id, page=page))
    kb.button(text="‹ К колоде", callback_data=CardCB(action="list", page=page))
    kb.adjust(1, 2, 1)
    return kb.as_markup()


def pick_card_type(action: str = "new_type") -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for type_code in CARD_TYPES:
        kb.button(
            text=CARD_TYPE_NAMES[type_code].capitalize(),
            callback_data=CardCB(action=action, value=type_code),
        )
    kb.button(text="‹ Отмена", callback_data=CardCB(action="list"))
    kb.adjust(3, 1)
    return kb.as_markup()


# -------------------------------------------------------------------- книги


def books_list(books: list[Book]) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for book in books:
        mark = {"current": "▶️", "done": "✔️", "planned": "🕐"}.get(book.status, "")
        kb.button(text=f"{mark} {book.title}"[:60], callback_data=BookCB(action="open", book_id=book.id))
    kb.button(text="➕ Новая книга", callback_data=BookCB(action="new"))
    kb.button(text="‹ В меню", callback_data=MenuCB(action="root"))
    kb.adjust(1)
    return kb.as_markup()


def who_books(books: list[Book], current_id: int | None = None) -> InlineKeyboardMarkup:
    """Выбор книги для просмотра истории выдач."""
    kb = InlineKeyboardBuilder()
    for book in books:
        mark = "▶️ " if book.id == current_id else ""
        kb.button(text=f"{mark}{book.title}"[:60], callback_data=BookCB(action="who", book_id=book.id))
    kb.button(text="‹ В меню", callback_data=MenuCB(action="root"))
    kb.adjust(1)
    return kb.as_markup()


def who_back(book_id: int) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="📚 Другая книга", callback_data=MenuCB(action="who"))
    kb.button(text="‹ В меню", callback_data=MenuCB(action="root"))
    kb.adjust(1)
    return kb.as_markup()


def book_actions(book: Book) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    if book.status != "current":
        kb.button(text="▶️ Сделать текущей", callback_data=BookCB(action="make_current", book_id=book.id))
    if book.status != "done":
        kb.button(text="✔️ Закрыть книгу", callback_data=BookCB(action="close", book_id=book.id))
    kb.button(text="📅 Дата встречи", callback_data=BookCB(action="meeting", book_id=book.id))
    kb.button(text="👀 Кто что получил", callback_data=BookCB(action="who", book_id=book.id))
    kb.button(text="‹ К книгам", callback_data=BookCB(action="list"))
    kb.adjust(1)
    return kb.as_markup()


# --------------------------------------------------------------- участники


def members_list(users: list[User], page: int = 0) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    start = page * MEMBERS_PER_PAGE
    chunk = users[start : start + MEMBERS_PER_PAGE]

    for user in chunk:
        state = "✅" if user.is_active else "⛔️"
        warn = "" if user.reachable else " 🚫"
        kb.button(
            text=f"{state} {user.display_name}{warn}"[:60],
            callback_data=MemberCB(action="open", user_id=user.id, page=page),
        )
    kb.adjust(1)

    nav = []
    if start > 0:
        nav.append(
            InlineKeyboardButton(text="‹", callback_data=MemberCB(action="list", page=page - 1).pack())
        )
    if start + MEMBERS_PER_PAGE < len(users):
        nav.append(
            InlineKeyboardButton(text="›", callback_data=MemberCB(action="list", page=page + 1).pack())
        )
    if nav:
        kb.row(*nav)

    kb.row(InlineKeyboardButton(text="🔗 Пригласить", callback_data=MemberCB(action="invite").pack()))
    kb.row(InlineKeyboardButton(text="‹ В меню", callback_data=MenuCB(action="root").pack()))
    return kb.as_markup()


def members_back(page: int = 0) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="‹ К участникам", callback_data=MemberCB(action="list", page=page))
    return kb.as_markup()


def member_actions(user: User, page: int = 0) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(
        text="⛔️ Деактивировать" if user.is_active else "✅ Активировать",
        callback_data=MemberCB(action="toggle", user_id=user.id, page=page),
    )
    kb.button(text="✏️ Имя в списках", callback_data=MemberCB(action="rename", user_id=user.id, page=page))
    kb.button(
        text="👑 Снять админа" if user.is_admin else "👑 Сделать админом",
        callback_data=MemberCB(action="admin", user_id=user.id, page=page),
    )
    kb.button(text="🗂 История карт", callback_data=MemberCB(action="history", user_id=user.id, page=page))
    kb.button(text="‹ К участникам", callback_data=MemberCB(action="list", page=page))
    kb.adjust(1)
    return kb.as_markup()


# --------------------------------------------------------------- настройки


def settings_menu() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="🔁 Окно неповторения", callback_data=SettingsCB(action="no_repeat"))
    kb.button(text="🔭 Кулдаун оптики", callback_data=SettingsCB(action="optics"))
    kb.button(text="🎲 Рероллы", callback_data=SettingsCB(action="rerolls"))
    kb.button(text="💬 Группа для объявлений", callback_data=SettingsCB(action="group"))
    kb.button(text="📝 Шаблон сообщения", callback_data=SettingsCB(action="template"))
    kb.button(text="‹ В меню", callback_data=MenuCB(action="root"))
    kb.adjust(1)
    return kb.as_markup()


def settings_back() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="‹ К настройкам", callback_data=SettingsCB(action="root"))
    return kb.as_markup()


def template_actions() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="↩️ Вернуть стандартный", callback_data=SettingsCB(action="template_reset"))
    kb.button(text="‹ К настройкам", callback_data=SettingsCB(action="root"))
    kb.adjust(1)
    return kb.as_markup()


def announce_toggle(enabled: bool) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(
        text="🔕 Не постить в группу" if enabled else "🔔 Постить в группу",
        callback_data=SettingsCB(action="announce_toggle"),
    )
    kb.button(text="✏️ Сменить чат", callback_data=SettingsCB(action="group_set"))
    kb.button(text="‹ К настройкам", callback_data=SettingsCB(action="root"))
    kb.adjust(1)
    return kb.as_markup()


# ------------------------------------------------------------------ участник


def member_card(assignment_id: int, *, rerolls_left: int) -> InlineKeyboardMarkup | None:
    if rerolls_left <= 0:
        return None
    kb = InlineKeyboardBuilder()
    kb.button(text="🎲 Другую карту", callback_data=RerollCB(assignment_id=assignment_id))
    return kb.as_markup()


def cancel_input(callback_data: str) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.row(InlineKeyboardButton(text="‹ Отмена", callback_data=callback_data))
    return kb.as_markup()

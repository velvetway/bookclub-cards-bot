"""Фабрики callback_data. Префиксы короткие: у Telegram лимит 64 байта."""

from __future__ import annotations

from aiogram.filters.callback_data import CallbackData


class MenuCB(CallbackData, prefix="m"):
    action: str


class WizardCB(CallbackData, prefix="w"):
    """Шаги мастера до того, как черновик записан в базу."""

    action: str
    value: str = ""
    page: int = 0


class DealCB(CallbackData, prefix="d"):
    """Действия над черновиком или отправленной раздачей."""

    action: str
    deal_id: int
    value: int = 0


class AssignCB(CallbackData, prefix="a"):
    """Действия над строкой превью."""

    action: str
    assignment_id: int
    value: int = 0
    page: int = 0


class CardCB(CallbackData, prefix="c"):
    action: str
    card_id: int = 0
    page: int = 0
    value: str = ""


class BookCB(CallbackData, prefix="b"):
    action: str
    book_id: int = 0


class MemberCB(CallbackData, prefix="u"):
    action: str
    user_id: int = 0
    page: int = 0


class SettingsCB(CallbackData, prefix="s"):
    action: str
    value: str = ""


class RerollCB(CallbackData, prefix="r"):
    """Кнопка реролла под картой у участника."""

    assignment_id: int


class CoverCB(CallbackData, prefix="cv"):
    """Обложка колоды: показать другую, отправить в группу."""

    action: str
    code: str = ""

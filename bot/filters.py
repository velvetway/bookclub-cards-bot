"""Фильтры доступа."""

from __future__ import annotations

import aiosqlite
from aiogram.filters import BaseFilter
from aiogram.types import CallbackQuery, Message, TelegramObject

from bot.storage import users as users_repo


class IsAdmin(BaseFilter):
    """Пропускает только администраторов клуба."""

    async def __call__(self, event: TelegramObject, conn: aiosqlite.Connection) -> bool:
        user = getattr(event, "from_user", None)
        if user is None:
            return False
        return await users_repo.is_admin(conn, user.id)


class IsPrivate(BaseFilter):
    """Личные сообщения: в группе бот не работает."""

    async def __call__(self, event: TelegramObject) -> bool:
        if isinstance(event, Message):
            return event.chat.type == "private"
        if isinstance(event, CallbackQuery) and event.message:
            return event.message.chat.type == "private"
        return False

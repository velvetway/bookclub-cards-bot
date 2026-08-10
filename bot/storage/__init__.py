"""Слой доступа к данным. Каждый модуль отвечает за свою таблицу."""

from bot.storage import books, cards, deals, settings, users

__all__ = ["books", "cards", "deals", "settings", "users"]

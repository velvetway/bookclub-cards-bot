"""Роутеры бота. Порядок подключения важен: общий — последним."""

from aiogram import Router

from bot.handlers import (
    books,
    cards,
    common,
    covers,
    deal_wizard,
    member,
    members,
    settings,
    stats,
)


def build_router() -> Router:
    root = Router(name="root")
    root.include_router(deal_wizard.router)
    root.include_router(cards.router)
    root.include_router(books.router)
    root.include_router(members.router)
    root.include_router(stats.router)
    root.include_router(covers.router)
    root.include_router(settings.router)
    root.include_router(member.router)
    root.include_router(common.router)
    return root

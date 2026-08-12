"""Точка входа: поднимает базу, роутеры и long polling."""

from __future__ import annotations

import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import ErrorEvent

from bot import db, logs
from bot.config import BASE_DIR, load_config
from bot.handlers import build_router
from bot.handlers.common import sync_commands
from bot.storage import cards as cards_repo
from bot.storage import users as users_repo

log = logging.getLogger(__name__)

DECK_FILE = BASE_DIR / "data" / "deck.json"


async def run() -> None:
    config = load_config()
    logs.setup(config.log_dir)
    log.info("запуск бота, база %s", config.db_path)

    conn = await db.connect(config.db_path)
    await db.init_db(conn)
    await users_repo.ensure_admins(conn, config.admin_ids)

    # смотрим только на общие карты: книжную колоду могли залить скриптом раньше,
    # и это не повод считать, что основная уже на месте
    if await cards_repo.count(conn, general_only=True) == 0:
        added = await cards_repo.seed_from_file(conn, DECK_FILE)
        log.info("колода загружена из файла: %s карт", added)

    bot = Bot(
        token=config.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dispatcher = Dispatcher(conn=conn, config=config)
    dispatcher.include_router(build_router())

    @dispatcher.errors()
    async def on_error(event: ErrorEvent) -> bool:
        log.exception("необработанная ошибка: %s", event.exception)
        return True

    await sync_commands(bot, conn)

    try:
        await bot.delete_webhook(drop_pending_updates=False)
        await dispatcher.start_polling(bot)
    finally:
        await conn.close()
        await bot.session.close()
        log.info("бот остановлен")


def main() -> None:
    try:
        asyncio.run(run())
    except (KeyboardInterrupt, SystemExit):
        log.info("выход по сигналу")


if __name__ == "__main__":
    main()

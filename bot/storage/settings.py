"""Настройки: ключ-значение в базе поверх значений из .env.

В .env лежат значения по умолчанию, в базе — то, что админ поменял через /settings.
База всегда главнее.
"""

from __future__ import annotations

from dataclasses import dataclass

import aiosqlite

from bot.config import Config

KEY_NO_REPEAT = "no_repeat_window"
KEY_OPTICS_COOLDOWN = "optics_cooldown"
KEY_REROLLS = "rerolls_per_deal"
KEY_GROUP_CHAT = "group_chat_id"
KEY_TEMPLATE = "message_template"
KEY_ANNOUNCE = "announce_in_group"
KEY_BOARD_CHAT = "board_chat_id"

DEFAULT_TEMPLATE = (
    "Книга: «{book}»\n"
    "Встреча: {meeting}\n"
    "\n"
    "{card_title}\n"
    "{card_hint}\n"
    "\n"
    "Эту карту нужно встроить в свой разбор.\n"
    "Чужие карты неизвестны — не обсуждайте до встречи."
)

OPTICS_NOTE = "Это оптика: карта задаёт угол всего рассказа, а не отдельный кусок."


@dataclass(frozen=True)
class Settings:
    no_repeat_window: int
    optics_cooldown: int
    rerolls_per_deal: int
    group_chat_id: int | None
    board_chat_id: int | None  # куда уходят постеры раскладов, по умолчанию — группа
    template: str
    announce_in_group: bool


async def get(conn: aiosqlite.Connection, key: str) -> str | None:
    async with conn.execute("SELECT value FROM settings WHERE key = ?", (key,)) as cur:
        row = await cur.fetchone()
    return row["value"] if row else None


async def set_value(conn: aiosqlite.Connection, key: str, value: str | int | None) -> None:
    if value is None:
        await conn.execute("DELETE FROM settings WHERE key = ?", (key,))
    else:
        await conn.execute(
            """INSERT INTO settings (key, value) VALUES (?, ?)
               ON CONFLICT(key) DO UPDATE SET value = excluded.value""",
            (key, str(value)),
        )
    await conn.commit()


async def _int(conn: aiosqlite.Connection, key: str, fallback: int) -> int:
    raw = await get(conn, key)
    if raw is None or not raw.strip():
        return fallback
    try:
        return int(raw)
    except ValueError:
        return fallback


async def effective(conn: aiosqlite.Connection, config: Config) -> Settings:
    group_raw = await get(conn, KEY_GROUP_CHAT)
    group_id: int | None = config.group_chat_id
    if group_raw is not None:
        group_id = int(group_raw) if group_raw.strip() else None

    announce_raw = await get(conn, KEY_ANNOUNCE)
    announce = group_id is not None if announce_raw is None else announce_raw == "1"

    board_raw = await get(conn, KEY_BOARD_CHAT)
    board_id = int(board_raw) if board_raw and board_raw.strip() else group_id

    return Settings(
        no_repeat_window=await _int(conn, KEY_NO_REPEAT, config.no_repeat_window),
        optics_cooldown=await _int(conn, KEY_OPTICS_COOLDOWN, config.optics_cooldown),
        rerolls_per_deal=await _int(conn, KEY_REROLLS, config.rerolls_per_deal),
        group_chat_id=group_id,
        board_chat_id=board_id,
        template=await get(conn, KEY_TEMPLATE) or DEFAULT_TEMPLATE,
        announce_in_group=announce,
    )

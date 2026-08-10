"""Подключение к SQLite и схема.

Схема из ТЗ (раздел 6) плюс одна служебная колонка:
  assignments.repeat_of — дата прошлой выдачи этой карты участнику, если окно
                          неповторения пришлось ослабить (нужно для пометки в превью).

Оценки встреч (этап 3) лягут отдельной таблицей со ссылкой на deal_id и user_id,
менять существующие таблицы для этого не придётся.
"""

from __future__ import annotations

import logging
from pathlib import Path

import aiosqlite

log = logging.getLogger(__name__)

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id            INTEGER PRIMARY KEY,
    username      TEXT,
    display_name  TEXT NOT NULL,
    is_active     INTEGER NOT NULL DEFAULT 1,
    is_admin      INTEGER NOT NULL DEFAULT 0,
    started_at    TIMESTAMP
);

CREATE TABLE IF NOT EXISTS books (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    title         TEXT NOT NULL,
    author        TEXT,
    weeks         INTEGER,
    started_at    DATE,
    meeting_at    TIMESTAMP,
    status        TEXT NOT NULL DEFAULT 'planned'
);

CREATE TABLE IF NOT EXISTS cards (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    code          TEXT NOT NULL UNIQUE,
    type          TEXT NOT NULL,
    title         TEXT NOT NULL,
    hint          TEXT,
    is_active     INTEGER NOT NULL DEFAULT 1,
    book_id       INTEGER REFERENCES books(id) ON DELETE SET NULL,
    created_at    TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    image_path    TEXT,          -- если картинка лежит не по умолчанию data/cards/<code>.png
    image_file_id TEXT,          -- кеш Telegram: повторно файл не загружаем
    image_sig     TEXT           -- отпечаток файла, чтобы заметить подмену картинки
);

CREATE TABLE IF NOT EXISTS deals (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    book_id       INTEGER NOT NULL REFERENCES books(id) ON DELETE CASCADE,
    phase         TEXT NOT NULL,
    pool_mode     TEXT NOT NULL,
    pool_codes    TEXT,
    status        TEXT NOT NULL DEFAULT 'draft',
    created_at    TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    sent_at       TIMESTAMP
);

CREATE TABLE IF NOT EXISTS assignments (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    deal_id       INTEGER NOT NULL REFERENCES deals(id) ON DELETE CASCADE,
    user_id       INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    card_id       INTEGER NOT NULL REFERENCES cards(id) ON DELETE CASCADE,
    status        TEXT NOT NULL DEFAULT 'pending',
    error         TEXT,
    sent_at       TIMESTAMP,
    reroll_count  INTEGER NOT NULL DEFAULT 0,
    manual        INTEGER NOT NULL DEFAULT 0,
    repeat_of     TIMESTAMP,
    UNIQUE (deal_id, user_id)
);

CREATE TABLE IF NOT EXISTS settings (
    key           TEXT PRIMARY KEY,
    value         TEXT
);

CREATE INDEX IF NOT EXISTS idx_assignments_user_card ON assignments(user_id, card_id);
CREATE INDEX IF NOT EXISTS idx_assignments_deal ON assignments(deal_id);
CREATE INDEX IF NOT EXISTS idx_cards_type_active ON cards(type, is_active);
CREATE INDEX IF NOT EXISTS idx_deals_book ON deals(book_id);
"""


async def connect(db_path: Path) -> aiosqlite.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = await aiosqlite.connect(db_path)
    conn.row_factory = aiosqlite.Row
    await conn.execute("PRAGMA foreign_keys = ON")
    await conn.execute("PRAGMA journal_mode = WAL")
    return conn


# колонки, добавленные после первого релиза: базы, созданные раньше, догоняются на старте
LATE_COLUMNS = {
    "cards": {
        "image_path": "TEXT",
        "image_file_id": "TEXT",
        "image_sig": "TEXT",
    },
    "assignments": {
        "repeat_of": "TIMESTAMP",
    },
}


async def _migrate(conn: aiosqlite.Connection) -> None:
    for table, columns in LATE_COLUMNS.items():
        async with conn.execute(f"PRAGMA table_info({table})") as cur:
            existing = {row["name"] for row in await cur.fetchall()}
        for name, sql_type in columns.items():
            if name not in existing:
                await conn.execute(f"ALTER TABLE {table} ADD COLUMN {name} {sql_type}")
                log.info("миграция: в %s добавлена колонка %s", table, name)
    await conn.commit()


async def init_db(conn: aiosqlite.Connection) -> None:
    await conn.executescript(SCHEMA)
    await conn.commit()
    await _migrate(conn)
    log.info("схема базы готова")

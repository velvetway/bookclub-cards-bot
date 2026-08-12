"""Колода."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import json
import logging
from pathlib import Path

import aiosqlite

from dataclasses import dataclass

from bot.models import DECK_MAIN, Card
from bot.timeutil import parse_dt, utcnow_iso

log = logging.getLogger(__name__)

CODE_PREFIX = {"optics": "OPT", "insert": "INS", "rating": "RAT"}


def _get(row: Mapping[str, Any], key: str) -> Any:
    """aiosqlite.Row не умеет .get, а колонки картинок есть не во всех выборках."""
    try:
        return row[key]
    except (KeyError, IndexError):
        return None


def _row(row: Mapping[str, Any]) -> Card:
    return Card(
        id=row["id"],
        code=row["code"],
        type=row["type"],
        title=row["title"],
        hint=row["hint"],
        is_active=bool(row["is_active"]),
        book_id=row["book_id"],
        created_at=parse_dt(row["created_at"]),
        image_path=_get(row, "image_path"),
        image_file_id=_get(row, "image_file_id"),
        image_sig=_get(row, "image_sig"),
    )


async def get(conn: aiosqlite.Connection, card_id: int) -> Card | None:
    async with conn.execute("SELECT * FROM cards WHERE id = ?", (card_id,)) as cur:
        row = await cur.fetchone()
    return _row(row) if row else None


async def get_by_code(conn: aiosqlite.Connection, code: str) -> Card | None:
    async with conn.execute(
        "SELECT * FROM cards WHERE code = ? COLLATE NOCASE", (code.strip(),)
    ) as cur:
        row = await cur.fetchone()
    return _row(row) if row else None


async def list_all(
    conn: aiosqlite.Connection,
    *,
    card_type: str | None = None,
    only_active: bool = False,
    codes: list[str] | None = None,
) -> list[Card]:
    sql = "SELECT * FROM cards"
    where, params = [], []
    if card_type:
        where.append("type = ?")
        params.append(card_type)
    if only_active:
        where.append("is_active = 1")
    if codes is not None:
        if not codes:
            return []
        where.append(f"code IN ({','.join('?' * len(codes))})")
        params.extend(codes)
    if where:
        sql += " WHERE " + " AND ".join(where)
    sql += " ORDER BY type, code"
    async with conn.execute(sql, params) as cur:
        rows = await cur.fetchall()
    return [_row(r) for r in rows]


async def get_many(conn: aiosqlite.Connection, ids: list[int]) -> dict[int, Card]:
    if not ids:
        return {}
    marks = ",".join("?" * len(ids))
    async with conn.execute(f"SELECT * FROM cards WHERE id IN ({marks})", ids) as cur:
        rows = await cur.fetchall()
    return {r["id"]: _row(r) for r in rows}


@dataclass(frozen=True)
class Deck:
    """Колода как её видит админ при выборе пула."""

    key: str  # "main" или префикс кодов книжной колоды
    title: str
    count: int

    @property
    def is_main(self) -> bool:
        return self.key == DECK_MAIN


async def decks(conn: aiosqlite.Connection) -> list[Deck]:
    """Какие колоды есть в базе: общая плюс по одной на каждую книгу с картами."""
    async with conn.execute(
        """SELECT c.book_id, b.title AS book_title, COUNT(*) AS n, MIN(c.code) AS sample
             FROM cards c
             LEFT JOIN books b ON b.id = c.book_id
            WHERE c.is_active = 1
            GROUP BY c.book_id
            ORDER BY (c.book_id IS NOT NULL), c.book_id"""
    ) as cur:
        rows = await cur.fetchall()

    out = []
    for row in rows:
        if row["book_id"] is None:
            out.append(Deck(key=DECK_MAIN, title="Базовая колода", count=int(row["n"])))
        else:
            out.append(
                Deck(
                    key=row["sample"].split("-")[0],
                    title=row["book_title"] or "Книжная колода",
                    count=int(row["n"]),
                )
            )
    return out


async def list_by_deck(conn: aiosqlite.Connection, key: str) -> list[Card]:
    """Карты одной колоды: базовой (без книги) или книжной (по префиксу кода)."""
    if key == DECK_MAIN:
        sql = "SELECT * FROM cards WHERE is_active = 1 AND book_id IS NULL ORDER BY type, code"
        params: tuple = ()
    else:
        sql = "SELECT * FROM cards WHERE is_active = 1 AND code LIKE ? ORDER BY type, code"
        params = (f"{key}-%",)

    async with conn.execute(sql, params) as cur:
        rows = await cur.fetchall()
    return [_row(r) for r in rows]


async def next_code(conn: aiosqlite.Connection, card_type: str) -> str:
    prefix = CODE_PREFIX.get(card_type, "CRD")
    async with conn.execute(
        "SELECT code FROM cards WHERE code LIKE ? ORDER BY code DESC LIMIT 1", (f"{prefix}-%",)
    ) as cur:
        row = await cur.fetchone()
    number = 1
    if row:
        tail = row["code"].split("-", 1)[-1]
        if tail.isdigit():
            number = int(tail) + 1
    return f"{prefix}-{number:02d}"


async def create(
    conn: aiosqlite.Connection,
    card_type: str,
    title: str,
    hint: str | None = None,
    code: str | None = None,
    book_id: int | None = None,
) -> Card:
    code = code or await next_code(conn, card_type)
    cur = await conn.execute(
        """INSERT INTO cards (code, type, title, hint, is_active, book_id, created_at)
           VALUES (?, ?, ?, ?, 1, ?, ?)""",
        (code, card_type, title, hint, book_id, utcnow_iso()),
    )
    await conn.commit()
    card = await get(conn, cur.lastrowid)
    assert card is not None
    return card


async def update_fields(
    conn: aiosqlite.Connection,
    card_id: int,
    *,
    title: str | None = None,
    hint: str | None = None,
    card_type: str | None = None,
    book_id: int | None = None,
    reset_book: bool = False,
) -> None:
    sets, params = [], []
    if title is not None:
        sets.append("title = ?")
        params.append(title)
    if hint is not None:
        sets.append("hint = ?")
        params.append(hint)
    if card_type is not None:
        sets.append("type = ?")
        params.append(card_type)
    if reset_book:
        sets.append("book_id = NULL")
    elif book_id is not None:
        sets.append("book_id = ?")
        params.append(book_id)
    if not sets:
        return
    params.append(card_id)
    await conn.execute(f"UPDATE cards SET {', '.join(sets)} WHERE id = ?", params)
    await conn.commit()


async def set_image_cache(
    conn: aiosqlite.Connection, card_id: int, file_id: str | None, sig: str | None
) -> None:
    """Запоминает file_id загруженной картинки, чтобы не слать файл каждый раз."""
    await conn.execute(
        "UPDATE cards SET image_file_id = ?, image_sig = ? WHERE id = ?",
        (file_id, sig, card_id),
    )
    await conn.commit()


async def set_image_path(conn: aiosqlite.Connection, card_id: int, path: str | None) -> None:
    await conn.execute(
        "UPDATE cards SET image_path = ?, image_file_id = NULL, image_sig = NULL WHERE id = ?",
        (path, card_id),
    )
    await conn.commit()


async def toggle_active(conn: aiosqlite.Connection, card_id: int) -> bool:
    await conn.execute("UPDATE cards SET is_active = 1 - is_active WHERE id = ?", (card_id,))
    await conn.commit()
    card = await get(conn, card_id)
    return bool(card and card.is_active)


async def count(conn: aiosqlite.Connection, *, general_only: bool = False) -> int:
    """general_only — считать только карты общей колоды, без написанных под книгу."""
    sql = "SELECT COUNT(*) AS n FROM cards"
    if general_only:
        sql += " WHERE book_id IS NULL"
    async with conn.execute(sql) as cur:
        row = await cur.fetchone()
    return int(row["n"]) if row else 0


async def seed_from_file(conn: aiosqlite.Connection, path: Path) -> int:
    """Заливает колоду из JSON. Существующие коды не трогает — правки в боте важнее файла."""
    if not path.exists():
        log.warning("файл колоды не найден: %s", path)
        return 0
    deck = json.loads(path.read_text(encoding="utf-8"))
    added = 0
    for item in deck:
        async with conn.execute("SELECT 1 FROM cards WHERE code = ?", (item["code"],)) as cur:
            if await cur.fetchone():
                continue
        await conn.execute(
            """INSERT INTO cards (code, type, title, hint, is_active, created_at)
               VALUES (?, ?, ?, ?, 1, ?)""",
            (item["code"], item["type"], item["title"], item.get("hint"), utcnow_iso()),
        )
        added += 1
    await conn.commit()
    if added:
        log.info("в колоду добавлено карт: %s", added)
    return added

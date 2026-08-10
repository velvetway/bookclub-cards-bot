"""Книги — циклы чтения."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from datetime import datetime

import aiosqlite

from bot.models import BOOK_CURRENT, BOOK_DONE, Book
from bot.timeutil import parse_dt


def _row(row: Mapping[str, Any]) -> Book:
    return Book(
        id=row["id"],
        title=row["title"],
        author=row["author"],
        weeks=row["weeks"],
        started_at=row["started_at"],
        meeting_at=parse_dt(row["meeting_at"]),
        status=row["status"],
    )


async def get(conn: aiosqlite.Connection, book_id: int) -> Book | None:
    async with conn.execute("SELECT * FROM books WHERE id = ?", (book_id,)) as cur:
        row = await cur.fetchone()
    return _row(row) if row else None


async def current(conn: aiosqlite.Connection) -> Book | None:
    async with conn.execute(
        "SELECT * FROM books WHERE status = ? ORDER BY id DESC LIMIT 1", (BOOK_CURRENT,)
    ) as cur:
        row = await cur.fetchone()
    return _row(row) if row else None


async def list_all(conn: aiosqlite.Connection, limit: int = 30) -> list[Book]:
    async with conn.execute(
        "SELECT * FROM books ORDER BY (status = 'current') DESC, id DESC LIMIT ?", (limit,)
    ) as cur:
        rows = await cur.fetchall()
    return [_row(r) for r in rows]


async def create(
    conn: aiosqlite.Connection,
    title: str,
    author: str | None = None,
    weeks: int | None = None,
    started_at: str | None = None,
    meeting_at: datetime | None = None,
    status: str = "planned",
) -> Book:
    cur = await conn.execute(
        """INSERT INTO books (title, author, weeks, started_at, meeting_at, status)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (
            title,
            author,
            weeks,
            started_at,
            meeting_at.isoformat(timespec="seconds") if meeting_at else None,
            status,
        ),
    )
    await conn.commit()
    book = await get(conn, cur.lastrowid)
    assert book is not None
    return book


async def make_current(conn: aiosqlite.Connection, book_id: int) -> None:
    """Текущая книга ровно одна: прежняя уходит в done."""
    await conn.execute(
        "UPDATE books SET status = ? WHERE status = ? AND id != ?",
        (BOOK_DONE, BOOK_CURRENT, book_id),
    )
    await conn.execute("UPDATE books SET status = ? WHERE id = ?", (BOOK_CURRENT, book_id))
    await conn.commit()


async def set_status(conn: aiosqlite.Connection, book_id: int, status: str) -> None:
    await conn.execute("UPDATE books SET status = ? WHERE id = ?", (status, book_id))
    await conn.commit()


async def set_meeting(conn: aiosqlite.Connection, book_id: int, meeting_at: datetime | None) -> None:
    await conn.execute(
        "UPDATE books SET meeting_at = ? WHERE id = ?",
        (meeting_at.isoformat(timespec="seconds") if meeting_at else None, book_id),
    )
    await conn.commit()


async def update_fields(
    conn: aiosqlite.Connection,
    book_id: int,
    *,
    title: str | None = None,
    author: str | None = None,
    weeks: int | None = None,
) -> None:
    sets, params = [], []
    if title is not None:
        sets.append("title = ?")
        params.append(title)
    if author is not None:
        sets.append("author = ?")
        params.append(author)
    if weeks is not None:
        sets.append("weeks = ?")
        params.append(weeks)
    if not sets:
        return
    params.append(book_id)
    await conn.execute(f"UPDATE books SET {', '.join(sets)} WHERE id = ?", params)
    await conn.commit()

"""Участники клуба."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import aiosqlite

from bot.models import User
from bot.timeutil import parse_dt, utcnow_iso


def _row(row: Mapping[str, Any]) -> User:
    return User(
        id=row["id"],
        username=row["username"],
        display_name=row["display_name"],
        is_active=bool(row["is_active"]),
        is_admin=bool(row["is_admin"]),
        started_at=parse_dt(row["started_at"]),
    )


async def get(conn: aiosqlite.Connection, user_id: int) -> User | None:
    async with conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)) as cur:
        row = await cur.fetchone()
    return _row(row) if row else None


async def list_all(
    conn: aiosqlite.Connection,
    *,
    only_active: bool = False,
    only_reachable: bool = False,
) -> list[User]:
    sql = "SELECT * FROM users"
    where = []
    if only_active:
        where.append("is_active = 1")
    if only_reachable:
        where.append("started_at IS NOT NULL")
    if where:
        sql += " WHERE " + " AND ".join(where)
    sql += " ORDER BY display_name COLLATE NOCASE"
    async with conn.execute(sql) as cur:
        rows = await cur.fetchall()
    return [_row(r) for r in rows]


async def get_many(conn: aiosqlite.Connection, ids: list[int]) -> dict[int, User]:
    if not ids:
        return {}
    marks = ",".join("?" * len(ids))
    async with conn.execute(f"SELECT * FROM users WHERE id IN ({marks})", ids) as cur:
        rows = await cur.fetchall()
    return {r["id"]: _row(r) for r in rows}


async def register(
    conn: aiosqlite.Connection,
    user_id: int,
    username: str | None,
    display_name: str,
    *,
    mark_started: bool = True,
) -> User:
    """Заводит участника или обновляет его данные при повторном /start.

    display_name, если админ его правил, не затирается автоматикой Telegram.
    """
    existing = await get(conn, user_id)
    now = utcnow_iso()
    if existing is None:
        await conn.execute(
            """INSERT INTO users (id, username, display_name, is_active, is_admin, started_at)
               VALUES (?, ?, ?, 1, 0, ?)""",
            (user_id, username, display_name, now if mark_started else None),
        )
    else:
        await conn.execute(
            """UPDATE users
                  SET username = ?,
                      is_active = 1,
                      started_at = COALESCE(started_at, ?)
                WHERE id = ?""",
            (username, now if mark_started else None, user_id),
        )
    await conn.commit()
    user = await get(conn, user_id)
    assert user is not None
    return user


async def set_active(conn: aiosqlite.Connection, user_id: int, active: bool) -> None:
    await conn.execute("UPDATE users SET is_active = ? WHERE id = ?", (int(active), user_id))
    await conn.commit()


async def set_admin(conn: aiosqlite.Connection, user_id: int, admin: bool) -> None:
    await conn.execute("UPDATE users SET is_admin = ? WHERE id = ?", (int(admin), user_id))
    await conn.commit()


async def set_display_name(conn: aiosqlite.Connection, user_id: int, name: str) -> None:
    await conn.execute("UPDATE users SET display_name = ? WHERE id = ?", (name, user_id))
    await conn.commit()


async def count_admins(conn: aiosqlite.Connection) -> int:
    async with conn.execute("SELECT COUNT(*) AS n FROM users WHERE is_admin = 1") as cur:
        row = await cur.fetchone()
    return int(row["n"]) if row else 0


async def ensure_admins(conn: aiosqlite.Connection, admin_ids: list[int]) -> None:
    """Проставляет флаг админа тем, кто перечислен в конфиге."""
    for admin_id in admin_ids:
        await conn.execute(
            """INSERT INTO users (id, username, display_name, is_admin)
               VALUES (?, NULL, ?, 1)
               ON CONFLICT(id) DO UPDATE SET is_admin = 1""",
            (admin_id, f"admin {admin_id}"),
        )
    await conn.commit()


async def is_admin(conn: aiosqlite.Connection, user_id: int) -> bool:
    user = await get(conn, user_id)
    return bool(user and user.is_admin)

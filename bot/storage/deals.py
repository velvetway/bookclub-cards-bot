"""Раздачи и назначения."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import json
from dataclasses import dataclass
from datetime import datetime

import aiosqlite

from bot.models import (
    ASSIGN_FAILED,
    ASSIGN_PENDING,
    ASSIGN_SENT,
    DEAL_DRAFT,
    Assignment,
    Card,
    Deal,
    User,
)
from bot.storage.books import _row as _book_row
from bot.storage.cards import _row as _card_row
from bot.storage.users import _row as _user_row
from bot.timeutil import parse_dt, utcnow_iso


@dataclass(frozen=True)
class AssignmentView:
    """Назначение вместе с участником и картой — то, что показывается в превью и отчёте."""

    assignment: Assignment
    user: User
    card: Card


def _deal_row(row: Mapping[str, Any]) -> Deal:
    codes = row["pool_codes"]
    return Deal(
        id=row["id"],
        book_id=row["book_id"],
        phase=row["phase"],
        pool_mode=row["pool_mode"],
        pool_codes=json.loads(codes) if codes else None,
        status=row["status"],
        created_at=parse_dt(row["created_at"]),
        sent_at=parse_dt(row["sent_at"]),
    )


def _assignment_row(row: Mapping[str, Any]) -> Assignment:
    return Assignment(
        id=row["id"],
        deal_id=row["deal_id"],
        user_id=row["user_id"],
        card_id=row["card_id"],
        status=row["status"],
        error=row["error"],
        sent_at=parse_dt(row["sent_at"]),
        reroll_count=row["reroll_count"],
        manual=bool(row["manual"]),
        repeat_of=parse_dt(row["repeat_of"]),
    )


# ---------------------------------------------------------------- раздачи


async def create(
    conn: aiosqlite.Connection,
    book_id: int,
    phase: str,
    pool_mode: str,
    pool_codes: list[str] | None = None,
) -> Deal:
    cur = await conn.execute(
        """INSERT INTO deals (book_id, phase, pool_mode, pool_codes, status, created_at)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (
            book_id,
            phase,
            pool_mode,
            json.dumps(pool_codes, ensure_ascii=False) if pool_codes else None,
            DEAL_DRAFT,
            utcnow_iso(),
        ),
    )
    await conn.commit()
    deal = await get(conn, cur.lastrowid)
    assert deal is not None
    return deal


async def get(conn: aiosqlite.Connection, deal_id: int) -> Deal | None:
    async with conn.execute("SELECT * FROM deals WHERE id = ?", (deal_id,)) as cur:
        row = await cur.fetchone()
    return _deal_row(row) if row else None


async def latest_draft(conn: aiosqlite.Connection) -> Deal | None:
    """Незавершённый черновик — то, к чему админ возвращается после выхода из мастера."""
    async with conn.execute(
        "SELECT * FROM deals WHERE status = ? ORDER BY id DESC LIMIT 1", (DEAL_DRAFT,)
    ) as cur:
        row = await cur.fetchone()
    return _deal_row(row) if row else None


async def list_for_book(conn: aiosqlite.Connection, book_id: int) -> list[Deal]:
    async with conn.execute(
        "SELECT * FROM deals WHERE book_id = ? ORDER BY id", (book_id,)
    ) as cur:
        rows = await cur.fetchall()
    return [_deal_row(r) for r in rows]


async def set_status(conn: aiosqlite.Connection, deal_id: int, status: str) -> None:
    await conn.execute("UPDATE deals SET status = ? WHERE id = ?", (status, deal_id))
    await conn.commit()


async def mark_sent(conn: aiosqlite.Connection, deal_id: int, status: str) -> None:
    await conn.execute(
        "UPDATE deals SET status = ?, sent_at = COALESCE(sent_at, ?) WHERE id = ?",
        (status, utcnow_iso(), deal_id),
    )
    await conn.commit()


async def delete_draft(conn: aiosqlite.Connection, deal_id: int) -> None:
    await conn.execute("DELETE FROM deals WHERE id = ? AND status = ?", (deal_id, DEAL_DRAFT))
    await conn.commit()


# ------------------------------------------------------------- назначения


async def replace_assignments(
    conn: aiosqlite.Connection,
    deal_id: int,
    items: list[tuple[int, int, datetime | None]],
) -> None:
    """Перезаписывает состав черновика: (user_id, card_id, repeat_of)."""
    await conn.execute("DELETE FROM assignments WHERE deal_id = ?", (deal_id,))
    await conn.executemany(
        """INSERT INTO assignments (deal_id, user_id, card_id, status, repeat_of)
           VALUES (?, ?, ?, ?, ?)""",
        [
            (deal_id, uid, cid, ASSIGN_PENDING, repeat.isoformat(timespec="seconds") if repeat else None)
            for uid, cid, repeat in items
        ],
    )
    await conn.commit()


async def assignments(conn: aiosqlite.Connection, deal_id: int) -> list[Assignment]:
    async with conn.execute(
        "SELECT * FROM assignments WHERE deal_id = ? ORDER BY id", (deal_id,)
    ) as cur:
        rows = await cur.fetchall()
    return [_assignment_row(r) for r in rows]


async def views(conn: aiosqlite.Connection, deal_id: int) -> list[AssignmentView]:
    async with conn.execute(
        """SELECT a.*,
                  u.id AS u_id, u.username AS u_username, u.display_name AS u_display_name,
                  u.is_active AS u_is_active, u.is_admin AS u_is_admin, u.started_at AS u_started_at,
                  c.id AS c_id, c.code AS c_code, c.type AS c_type, c.title AS c_title,
                  c.hint AS c_hint, c.is_active AS c_is_active, c.book_id AS c_book_id,
                  c.created_at AS c_created_at, c.image_path AS c_image_path,
                  c.image_file_id AS c_image_file_id, c.image_sig AS c_image_sig
             FROM assignments a
             JOIN users u ON u.id = a.user_id
             JOIN cards c ON c.id = a.card_id
            WHERE a.deal_id = ?
            ORDER BY a.id""",
        (deal_id,),
    ) as cur:
        rows = await cur.fetchall()

    out: list[AssignmentView] = []
    for row in rows:
        user = _user_row(
            {
                "id": row["u_id"],
                "username": row["u_username"],
                "display_name": row["u_display_name"],
                "is_active": row["u_is_active"],
                "is_admin": row["u_is_admin"],
                "started_at": row["u_started_at"],
            }
        )
        card = _card_row(
            {
                "id": row["c_id"],
                "code": row["c_code"],
                "type": row["c_type"],
                "title": row["c_title"],
                "hint": row["c_hint"],
                "is_active": row["c_is_active"],
                "book_id": row["c_book_id"],
                "created_at": row["c_created_at"],
                "image_path": row["c_image_path"],
                "image_file_id": row["c_image_file_id"],
                "image_sig": row["c_image_sig"],
            }
        )
        out.append(AssignmentView(assignment=_assignment_row(row), user=user, card=card))
    return out


async def get_assignment(conn: aiosqlite.Connection, assignment_id: int) -> Assignment | None:
    async with conn.execute("SELECT * FROM assignments WHERE id = ?", (assignment_id,)) as cur:
        row = await cur.fetchone()
    return _assignment_row(row) if row else None


async def set_card(
    conn: aiosqlite.Connection,
    assignment_id: int,
    card_id: int,
    *,
    manual: bool = False,
    bump_reroll: bool = False,
    repeat_of: datetime | None = None,
) -> None:
    await conn.execute(
        f"""UPDATE assignments
               SET card_id = ?,
                   manual = ?,
                   repeat_of = ?,
                   reroll_count = reroll_count {'+ 1' if bump_reroll else ''}
             WHERE id = ?""",
        (
            card_id,
            int(manual),
            repeat_of.isoformat(timespec="seconds") if repeat_of else None,
            assignment_id,
        ),
    )
    await conn.commit()


async def swap_cards(conn: aiosqlite.Connection, first_id: int, second_id: int) -> None:
    first = await get_assignment(conn, first_id)
    second = await get_assignment(conn, second_id)
    if not first or not second:
        return
    await conn.execute(
        "UPDATE assignments SET card_id = ?, manual = 1 WHERE id = ?", (second.card_id, first.id)
    )
    await conn.execute(
        "UPDATE assignments SET card_id = ?, manual = 1 WHERE id = ?", (first.card_id, second.id)
    )
    await conn.commit()


async def remove_assignment(conn: aiosqlite.Connection, assignment_id: int) -> None:
    await conn.execute("DELETE FROM assignments WHERE id = ?", (assignment_id,))
    await conn.commit()


async def mark_delivery(
    conn: aiosqlite.Connection,
    assignment_id: int,
    status: str,
    error: str | None = None,
) -> None:
    await conn.execute(
        "UPDATE assignments SET status = ?, error = ?, sent_at = ? WHERE id = ?",
        (status, error, utcnow_iso() if status == ASSIGN_SENT else None, assignment_id),
    )
    await conn.commit()


async def failed_views(conn: aiosqlite.Connection, deal_id: int) -> list[AssignmentView]:
    return [v for v in await views(conn, deal_id) if v.assignment.status == ASSIGN_FAILED]


# ---------------------------------------------------------------- история


async def recent_card_ids(conn: aiosqlite.Connection, user_id: int, window: int) -> list[int]:
    """Последние window карт, реально доставленных участнику."""
    if window <= 0:
        return []
    async with conn.execute(
        """SELECT a.card_id
             FROM assignments a
            WHERE a.user_id = ? AND a.status = ?
            ORDER BY a.id DESC
            LIMIT ?""",
        (user_id, ASSIGN_SENT, window),
    ) as cur:
        rows = await cur.fetchall()
    return [r["card_id"] for r in rows]


async def had_optics_recently(conn: aiosqlite.Connection, user_id: int, deals_back: int) -> bool:
    """Была ли оптика у участника в последних deals_back раздачах, где он участвовал."""
    if deals_back <= 0:
        return False
    async with conn.execute(
        """SELECT c.type
             FROM assignments a
             JOIN cards c ON c.id = a.card_id
            WHERE a.user_id = ? AND a.status = ?
            ORDER BY a.deal_id DESC
            LIMIT ?""",
        (user_id, ASSIGN_SENT, deals_back),
    ) as cur:
        rows = await cur.fetchall()
    return any(r["type"] == "optics" for r in rows)


async def last_dealt_at(
    conn: aiosqlite.Connection, user_id: int, card_id: int
) -> datetime | None:
    async with conn.execute(
        """SELECT sent_at FROM assignments
            WHERE user_id = ? AND card_id = ? AND status = ?
            ORDER BY id DESC LIMIT 1""",
        (user_id, card_id, ASSIGN_SENT),
    ) as cur:
        row = await cur.fetchone()
    return parse_dt(row["sent_at"]) if row else None


async def last_dealt_map(conn: aiosqlite.Connection, user_id: int) -> dict[int, datetime]:
    """card_id → когда карта в последний раз доставлялась этому участнику."""
    async with conn.execute(
        """SELECT card_id, MAX(sent_at) AS last_at
             FROM assignments
            WHERE user_id = ? AND status = ?
            GROUP BY card_id""",
        (user_id, ASSIGN_SENT),
    ) as cur:
        rows = await cur.fetchall()
    out: dict[int, datetime] = {}
    for row in rows:
        moment = parse_dt(row["last_at"])
        if moment:
            out[row["card_id"]] = moment
    return out


async def user_history(
    conn: aiosqlite.Connection, user_id: int, limit: int = 20
) -> list[tuple[Card, Deal, "Book | None"]]:
    """История выдач участника: карта, раздача, книга — от свежих к старым."""
    async with conn.execute(
        """SELECT c.id AS c_id, c.code AS c_code, c.type AS c_type, c.title AS c_title,
                  c.hint AS c_hint, c.is_active AS c_is_active, c.book_id AS c_book_id,
                  c.created_at AS c_created_at,
                  d.id AS d_id, d.book_id AS d_book_id, d.phase AS d_phase,
                  d.pool_mode AS d_pool_mode, d.pool_codes AS d_pool_codes,
                  d.status AS d_status, d.created_at AS d_created_at, d.sent_at AS d_sent_at,
                  b.id AS b_id, b.title AS b_title, b.author AS b_author, b.weeks AS b_weeks,
                  b.started_at AS b_started_at, b.meeting_at AS b_meeting_at, b.status AS b_status
             FROM assignments a
             JOIN cards c ON c.id = a.card_id
             JOIN deals d ON d.id = a.deal_id
             LEFT JOIN books b ON b.id = d.book_id
            WHERE a.user_id = ? AND a.status = ?
            ORDER BY a.id DESC
            LIMIT ?""",
        (user_id, ASSIGN_SENT, limit),
    ) as cur:
        rows = await cur.fetchall()

    out = []
    for row in rows:
        card = _card_row(
            {
                "id": row["c_id"], "code": row["c_code"], "type": row["c_type"],
                "title": row["c_title"], "hint": row["c_hint"], "is_active": row["c_is_active"],
                "book_id": row["c_book_id"], "created_at": row["c_created_at"],
            }
        )
        deal = _deal_row(
            {
                "id": row["d_id"], "book_id": row["d_book_id"], "phase": row["d_phase"],
                "pool_mode": row["d_pool_mode"], "pool_codes": row["d_pool_codes"],
                "status": row["d_status"], "created_at": row["d_created_at"],
                "sent_at": row["d_sent_at"],
            }
        )
        book = None
        if row["b_id"] is not None:
            book = _book_row(
                {
                    "id": row["b_id"], "title": row["b_title"], "author": row["b_author"],
                    "weeks": row["b_weeks"], "started_at": row["b_started_at"],
                    "meeting_at": row["b_meeting_at"], "status": row["b_status"],
                }
            )
        out.append((card, deal, book))
    return out


async def current_assignment(
    conn: aiosqlite.Connection, user_id: int
) -> tuple[Assignment, Card, Deal] | None:
    """Последняя доставленная участнику карта — это и есть его текущая."""
    async with conn.execute(
        """SELECT a.*, c.id AS c_id, c.code AS c_code, c.type AS c_type, c.title AS c_title,
                  c.hint AS c_hint, c.is_active AS c_is_active, c.book_id AS c_book_id,
                  c.created_at AS c_created_at, c.image_path AS c_image_path,
                  c.image_file_id AS c_image_file_id, c.image_sig AS c_image_sig,
                  d.id AS d_id, d.book_id AS d_book_id, d.phase AS d_phase,
                  d.pool_mode AS d_pool_mode, d.pool_codes AS d_pool_codes,
                  d.status AS d_status, d.created_at AS d_created_at, d.sent_at AS d_sent_at
             FROM assignments a
             JOIN cards c ON c.id = a.card_id
             JOIN deals d ON d.id = a.deal_id
            WHERE a.user_id = ? AND a.status = ?
            ORDER BY a.id DESC LIMIT 1""",
        (user_id, ASSIGN_SENT),
    ) as cur:
        row = await cur.fetchone()
    if not row:
        return None
    card = _card_row(
        {
            "id": row["c_id"], "code": row["c_code"], "type": row["c_type"],
            "title": row["c_title"], "hint": row["c_hint"], "is_active": row["c_is_active"],
            "book_id": row["c_book_id"], "created_at": row["c_created_at"],
            "image_path": row["c_image_path"], "image_file_id": row["c_image_file_id"],
            "image_sig": row["c_image_sig"],
        }
    )
    deal = _deal_row(
        {
            "id": row["d_id"], "book_id": row["d_book_id"], "phase": row["d_phase"],
            "pool_mode": row["d_pool_mode"], "pool_codes": row["d_pool_codes"],
            "status": row["d_status"], "created_at": row["d_created_at"],
            "sent_at": row["d_sent_at"],
        }
    )
    return _assignment_row(row), card, deal


async def book_picture(conn: aiosqlite.Connection, book_id: int) -> list[tuple[Deal, list[AssignmentView]]]:
    """Что кому ушло по книге — для /who."""
    out = []
    for deal in await list_for_book(conn, book_id):
        out.append((deal, await views(conn, deal.id)))
    return out


# ------------------------------------------------------------- статистика


async def card_frequency(conn: aiosqlite.Connection) -> list[tuple[str, str, int]]:
    async with conn.execute(
        """SELECT c.code, c.title, COUNT(a.id) AS n
             FROM cards c
             LEFT JOIN assignments a ON a.card_id = c.id AND a.status = ?
            GROUP BY c.id
            ORDER BY n DESC, c.code""",
        (ASSIGN_SENT,),
    ) as cur:
        rows = await cur.fetchall()
    return [(r["code"], r["title"], int(r["n"])) for r in rows]


async def user_distribution(conn: aiosqlite.Connection) -> list[tuple[str, int, int]]:
    """display_name, всего карт, из них оптики."""
    async with conn.execute(
        """SELECT u.display_name,
                  COUNT(a.id) AS total,
                  SUM(CASE WHEN c.type = 'optics' THEN 1 ELSE 0 END) AS optics
             FROM users u
             LEFT JOIN assignments a ON a.user_id = u.id AND a.status = ?
             LEFT JOIN cards c ON c.id = a.card_id
            GROUP BY u.id
            ORDER BY total DESC, u.display_name COLLATE NOCASE""",
        (ASSIGN_SENT,),
    ) as cur:
        rows = await cur.fetchall()
    return [(r["display_name"], int(r["total"]), int(r["optics"] or 0)) for r in rows]

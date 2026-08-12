#!/usr/bin/env python3
"""Заливает книжную колоду в базу и привязывает её карты к книге.

Карты с book_id участвуют в раздаче наравне с общими, но выпадают чаще —
алгоритм даёт им повышенный вес, когда раздача идёт по этой самой книге.

    python scripts/load_deck.py data/decks/ack.json
    python scripts/load_deck.py data/decks/ack.json --make-current
    python scripts/load_deck.py data/decks/ack.json --off   # завести выключенными

Повторный запуск ничего не ломает: существующие коды пропускаются.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from bot import db  # noqa: E402
from bot.models import BOOK_PLANNED  # noqa: E402
from bot.storage import books as books_repo  # noqa: E402
from bot.storage import cards as cards_repo  # noqa: E402
from bot.timeutil import utcnow_iso  # noqa: E402


def db_path() -> Path:
    raw = (os.getenv("DB_PATH") or "").strip()
    if not raw:
        env_file = BASE_DIR / ".env"
        if env_file.exists():
            for line in env_file.read_text(encoding="utf-8").splitlines():
                if line.strip().startswith("DB_PATH="):
                    raw = line.split("=", 1)[1].strip()
                    break
    path = Path(raw or "data/bot.db")
    return path if path.is_absolute() else BASE_DIR / path


async def find_book(conn, title: str):
    for book in await books_repo.list_all(conn, limit=500):
        if book.title.casefold() == title.casefold():
            return book
    return None


async def run(deck_file: Path, make_current: bool, active: bool) -> None:
    data = json.loads(deck_file.read_text(encoding="utf-8"))
    meta = data.get("book") or {}
    if not meta.get("title"):
        sys.exit(f"{deck_file.name}: в файле нет book.title — к какой книге привязывать карты?")

    conn = await db.connect(db_path())
    await db.init_db(conn)

    book = await find_book(conn, meta["title"])
    if book is None:
        book = await books_repo.create(
            conn,
            title=meta["title"],
            author=meta.get("author"),
            weeks=meta.get("weeks"),
            status=BOOK_PLANNED,
        )
        print(f"книга заведена: «{book.title}» (id {book.id})")
    else:
        print(f"книга найдена: «{book.title}» (id {book.id})")

    if make_current:
        await books_repo.make_current(conn, book.id)
        print("книга сделана текущей")

    added, skipped = 0, []
    for card in data["cards"]:
        if await cards_repo.get_by_code(conn, card["code"]):
            skipped.append(card["code"])
            continue
        await conn.execute(
            """INSERT INTO cards (code, type, title, hint, is_active, book_id, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                card["code"],
                card["type"],
                card["title"],
                card.get("hint"),
                int(active),
                book.id,
                utcnow_iso(),
            ),
        )
        added += 1
    await conn.commit()
    await conn.close()

    print(f"карт добавлено: {added}" + (" (выключенными)" if not active else ""))
    if skipped:
        print(f"уже были в колоде: {', '.join(skipped)}")

    if data.get("spoiler"):
        print(f"\n⚠️  {data['spoiler']}")
    conflicts = data.get("conflicts") or {}
    if conflicts:
        print("\nНе раздавать вместе:")
        for code, others in conflicts.items():
            print(f"  {code} перекрывает {', '.join(others)}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Загрузка книжной колоды")
    parser.add_argument("deck", type=Path, help="json колоды, например data/decks/ack.json")
    parser.add_argument("--make-current", action="store_true", help="сделать книгу текущей")
    parser.add_argument("--off", action="store_true", help="завести карты выключенными")
    args = parser.parse_args()

    if not args.deck.exists():
        sys.exit(f"Файл не найден: {args.deck}")
    asyncio.run(run(args.deck, args.make_current, active=not args.off))


if __name__ == "__main__":
    main()

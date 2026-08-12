"""Сквозные проверки по чек-листу приёмки: раздача, доставка, повтор, черновик."""

from __future__ import annotations

from pathlib import Path

import pytest
from aiogram.exceptions import TelegramForbiddenError

from bot import db, delivery, images, service
from bot.dealer import NotEnoughCards
from bot.config import Config
from bot.models import (
    ASSIGN_FAILED,
    ASSIGN_SENT,
    BOOK_CURRENT,
    DEAL_PARTIAL,
    DEAL_SENT,
    INSERT,
    OPTICS,
    POOL_ALL,
    POOL_BY_TYPE,
    POOL_CUSTOM,
    POOL_DECK,
)
from bot.storage import books as books_repo
from bot.storage import cards as cards_repo
from bot.storage import deals as deals_repo
from bot.storage import settings as settings_repo
from bot.storage import users as users_repo

DECK = Path(__file__).resolve().parent.parent / "data" / "deck.json"


class FakePhotoSize:
    def __init__(self, file_id: str) -> None:
        self.file_id = file_id


class FakeMessage:
    def __init__(self, file_id: str) -> None:
        self.photo = [FakePhotoSize(file_id)]


class FakeBot:
    """Подменяет Bot: копит отправленное, умеет изображать блокировку."""

    def __init__(self, blocked: set[int] | None = None) -> None:
        self.sent: list[tuple[int, str]] = []
        self.photos: list[tuple[int, object]] = []
        self.blocked = blocked or set()

    async def send_message(self, chat_id: int, text: str, reply_markup=None, **kwargs):
        if chat_id in self.blocked:
            raise TelegramForbiddenError(method=None, message="bot was blocked by the user")
        self.sent.append((chat_id, text))
        return None

    async def send_photo(self, chat_id: int, photo, **kwargs):
        if chat_id in self.blocked:
            raise TelegramForbiddenError(method=None, message="bot was blocked by the user")
        self.photos.append((chat_id, photo))
        return FakeMessage("cached-file-id")


@pytest.fixture
async def conn(tmp_path):
    connection = await db.connect(tmp_path / "test.db")
    await db.init_db(connection)
    await cards_repo.seed_from_file(connection, DECK)
    yield connection
    await connection.close()


@pytest.fixture
def config(tmp_path) -> Config:
    return Config(bot_token="test", db_path=tmp_path / "test.db", log_dir=tmp_path / "logs")


async def make_members(conn, count: int, *, unreachable: set[int] = frozenset()):
    ids = []
    for i in range(1, count + 1):
        user_id = 1000 + i
        await users_repo.register(
            conn, user_id, f"user{i}", f"Участник {i}", mark_started=user_id not in unreachable
        )
        ids.append(user_id)
    return ids


async def make_book(conn, title: str = "К югу от границы, на запад от солнца"):
    book = await books_repo.create(conn, title=title, author="Харуки Мураками")
    await books_repo.make_current(conn, book.id)
    return await books_repo.get(conn, book.id)


async def test_раздача_на_семерых_уходит_в_лс(conn, config):
    users = await make_members(conn, 7)
    book = await make_book(conn)
    settings = await settings_repo.effective(conn, config)

    deal = await deals_repo.create(conn, book.id, INSERT, POOL_BY_TYPE)
    await service.generate(conn, deal, users, settings)

    bot = FakeBot()
    views = await delivery.deliver(bot, conn, deal, settings, config.tz)

    assert len(bot.sent) == 7
    assert all(v.assignment.status == ASSIGN_SENT for v in views)

    deal = await deals_repo.get(conn, deal.id)
    assert deal.status == DEAL_SENT
    assert deal.sent_at is not None


async def test_заблокировавший_бота_даёт_статус_partial_и_повтор_без_дублей(conn, config):
    users = await make_members(conn, 7)
    book = await make_book(conn)
    settings = await settings_repo.effective(conn, config)

    deal = await deals_repo.create(conn, book.id, INSERT, POOL_BY_TYPE)
    await service.generate(conn, deal, users, settings)

    blocked = users[3]
    bot = FakeBot(blocked={blocked})
    views = await delivery.deliver(bot, conn, deal, settings, config.tz)

    deal = await deals_repo.get(conn, deal.id)
    assert deal.status == DEAL_PARTIAL
    assert len(bot.sent) == 6

    failed = [v for v in views if v.assignment.status == ASSIGN_FAILED]
    assert [v.user.id for v in failed] == [blocked]

    # заблокировавший помечен неактивным
    assert (await users_repo.get(conn, blocked)).is_active is False

    cards_before = {v.user.id: v.card.id for v in views}

    # повтор недоставленных: тому же участнику уходит та же карта, остальным ничего
    bot.blocked.clear()
    views_after = await delivery.deliver(bot, conn, deal, settings, config.tz, only_failed=True)

    assert len(bot.sent) == 7, "повтор отправил ровно одно новое сообщение"
    assert {v.user.id: v.card.id for v in views_after} == cards_before, "карты не перевыбирались"
    assert (await deals_repo.get(conn, deal.id)).status == DEAL_SENT


async def test_участник_без_старта_не_получает_и_не_ломает_раздачу(conn, config):
    users = await make_members(conn, 4, unreachable={1002})
    book = await make_book(conn)
    settings = await settings_repo.effective(conn, config)

    deal = await deals_repo.create(conn, book.id, INSERT, POOL_BY_TYPE)
    await service.generate(conn, deal, users, settings)

    bot = FakeBot()
    views = await delivery.deliver(bot, conn, deal, settings, config.tz)

    failed = [v for v in views if v.assignment.status == ASSIGN_FAILED]
    assert [v.user.id for v in failed] == [1002]
    assert "start" in failed[0].assignment.error
    assert len(bot.sent) == 3


async def test_карта_не_повторяется_в_пределах_окна_на_реальной_истории(conn, config):
    users = await make_members(conn, 2)
    book = await make_book(conn)
    settings = await settings_repo.effective(conn, config)

    seen: set[int] = set()
    for _ in range(4):
        deal = await deals_repo.create(conn, book.id, INSERT, POOL_BY_TYPE)
        await service.generate(conn, deal, users, settings)
        bot = FakeBot()
        views = await delivery.deliver(bot, conn, deal, settings, config.tz)

        for view in views:
            if view.user.id != users[0]:
                continue
            assert view.card.id not in seen, "карта повторилась внутри окна неповторения"
            seen.add(view.card.id)


async def test_оптика_не_приходит_два_цикла_подряд(conn, config):
    users = await make_members(conn, 3)
    book = await make_book(conn)
    settings = await settings_repo.effective(conn, config)

    got_optics: list[set[int]] = []
    for _ in range(4):
        deal = await deals_repo.create(conn, book.id, "mixed", POOL_ALL)
        await service.generate(conn, deal, users, settings)
        bot = FakeBot()
        views = await delivery.deliver(bot, conn, deal, settings, config.tz)
        got_optics.append({v.user.id for v in views if v.card.type == OPTICS})

    for previous, current in zip(got_optics, got_optics[1:]):
        assert not (previous & current), "оптика пришла одному человеку два цикла подряд"


async def test_произвольный_пул_из_пяти_карт(conn, config):
    settings = await settings_repo.effective(conn, config)
    book = await make_book(conn)
    codes = ["INS-01", "INS-02", "INS-03", "INS-04", "INS-05"]

    five = await make_members(conn, 5)
    deal = await deals_repo.create(conn, book.id, INSERT, POOL_CUSTOM, codes)
    await service.generate(conn, deal, five, settings)

    views = await deals_repo.views(conn, deal.id)
    assert {v.card.code for v in views} == set(codes)

    six = five + (await make_members(conn, 6))[5:]
    deal2 = await deals_repo.create(conn, book.id, INSERT, POOL_CUSTOM, codes)
    with pytest.raises(Exception) as exc:
        await service.generate(conn, deal2, six, settings)
    assert "не хватает карт" in str(exc.value)


async def test_черновик_переживает_выход_из_мастера(conn, config):
    users = await make_members(conn, 3)
    book = await make_book(conn)
    settings = await settings_repo.effective(conn, config)

    deal = await deals_repo.create(conn, book.id, INSERT, POOL_BY_TYPE)
    await service.generate(conn, deal, users, settings)

    # «перезапуск»: заново читаем из базы, ничего в памяти не держим
    draft = await deals_repo.latest_draft(conn)
    assert draft is not None and draft.id == deal.id

    views = await deals_repo.views(conn, draft.id)
    assert len(views) == 3


async def test_who_показывает_картину_по_книге(conn, config):
    users = await make_members(conn, 3)
    book = await make_book(conn)
    settings = await settings_repo.effective(conn, config)

    optics_deal = await deals_repo.create(conn, book.id, OPTICS, POOL_BY_TYPE)
    await service.generate(conn, optics_deal, users, settings)
    await delivery.deliver(FakeBot(), conn, optics_deal, settings, config.tz)

    insert_deal = await deals_repo.create(conn, book.id, INSERT, POOL_BY_TYPE)
    await service.generate(conn, insert_deal, users, settings)
    await delivery.deliver(FakeBot(), conn, insert_deal, settings, config.tz)

    picture = await deals_repo.book_picture(conn, book.id)
    assert [d.phase for d, _ in picture] == [OPTICS, INSERT]
    assert all(len(views) == 3 for _, views in picture)


async def test_повторная_отправка_не_меняет_карты(conn, config):
    users = await make_members(conn, 3)
    book = await make_book(conn)
    settings = await settings_repo.effective(conn, config)

    deal = await deals_repo.create(conn, book.id, INSERT, POOL_BY_TYPE)
    await service.generate(conn, deal, users, settings)

    bot = FakeBot()
    before = {v.user.id: v.card.id for v in await delivery.deliver(bot, conn, deal, settings, config.tz)}
    after = {v.user.id: v.card.id for v in await delivery.deliver(bot, conn, deal, settings, config.tz)}

    assert before == after
    assert len(bot.sent) == 6, "второй проход отправил те же карты ещё раз"


async def test_реролл_меняет_карту_и_считается(conn, config):
    users = await make_members(conn, 2)
    book = await make_book(conn)
    settings = await settings_repo.effective(conn, config)

    deal = await deals_repo.create(conn, book.id, INSERT, POOL_BY_TYPE)
    await service.generate(conn, deal, users, settings)

    assignment = (await deals_repo.assignments(conn, deal.id))[0]
    old_card = assignment.card_id

    card = await service.reroll(conn, deal, assignment, settings)
    updated = await deals_repo.get_assignment(conn, assignment.id)

    assert card.id != old_card
    assert updated.card_id == card.id
    assert updated.reroll_count == 1


async def test_карточка_уходит_картинкой_и_отдельным_пояснением(
    conn, config, tmp_path, monkeypatch
):
    monkeypatch.setattr(images, "CARDS_DIR", tmp_path)
    (tmp_path / "INS-01.png").write_bytes(b"fake png")

    users = await make_members(conn, 1)
    book = await make_book(conn)
    settings = await settings_repo.effective(conn, config)

    deal = await deals_repo.create(conn, book.id, INSERT, POOL_CUSTOM, ["INS-01"])
    await service.generate(conn, deal, users, settings)

    bot = FakeBot()
    await delivery.deliver(bot, conn, deal, settings, config.tz)

    assert len(bot.photos) == 1, "картинка ушла отдельным сообщением"
    assert len(bot.sent) == 1, "пояснение ушло вторым сообщением"
    assert "Эту карту нужно встроить" in bot.sent[0][1]

    card = await cards_repo.get_by_code(conn, "INS-01")
    assert card.image_file_id == "cached-file-id", "file_id закеширован"

    # второй раз файл не загружаем, отправляем по file_id
    await delivery.deliver(bot, conn, deal, settings, config.tz)
    assert bot.photos[1][1] == "cached-file-id"


async def test_без_картинки_карта_уходит_одним_сообщением(conn, config, tmp_path, monkeypatch):
    monkeypatch.setattr(images, "CARDS_DIR", tmp_path)

    users = await make_members(conn, 1)
    book = await make_book(conn)
    settings = await settings_repo.effective(conn, config)

    deal = await deals_repo.create(conn, book.id, INSERT, POOL_BY_TYPE)
    await service.generate(conn, deal, users, settings)

    bot = FakeBot()
    await delivery.deliver(bot, conn, deal, settings, config.tz)

    assert bot.photos == []
    assert len(bot.sent) == 1


async def test_ручная_замена_на_занятую_карту_меняет_участников_местами(conn, config):
    users = await make_members(conn, 2)
    book = await make_book(conn)
    settings = await settings_repo.effective(conn, config)

    deal = await deals_repo.create(conn, book.id, INSERT, POOL_BY_TYPE)
    await service.generate(conn, deal, users, settings)

    first, second = await deals_repo.assignments(conn, deal.id)
    result = await service.set_card_manually(conn, deal, first, second.card_id)

    assert result == "swapped"
    first_after = await deals_repo.get_assignment(conn, first.id)
    second_after = await deals_repo.get_assignment(conn, second.id)
    assert first_after.card_id == second.card_id
    assert second_after.card_id == first.card_id


async def test_основная_колода_доливается_если_первой_залили_книжную(tmp_path):
    """Книжную колоду можно залить скриптом до первого запуска бота.

    Тогда карты в базе уже есть, и проверка «колода пуста» пропустила бы
    основную колоду навсегда — поэтому считаем только карты без book_id.
    """
    connection = await db.connect(tmp_path / "fresh.db")
    await db.init_db(connection)

    book = await books_repo.create(connection, title="Убийство Роджера Экройда")
    await cards_repo.create(
        connection, INSERT, "Рассказчик", code="ACK-01", book_id=book.id
    )

    assert await cards_repo.count(connection) == 1
    assert await cards_repo.count(connection, general_only=True) == 0

    added = await cards_repo.seed_from_file(connection, DECK)
    assert added == 31
    assert await cards_repo.count(connection) == 32

    await connection.close()


async def make_book_deck(conn, book_id: int, count: int = 6):
    """Книжная колода: карты с book_id и своим префиксом кода."""
    for i in range(1, count + 1):
        await cards_repo.create(
            conn, INSERT, f"Книжная {i}", code=f"ACK-{i:02d}", book_id=book_id
        )


async def test_колоды_видны_отдельно(conn, config):
    book = await make_book(conn)
    await make_book_deck(conn, book.id)

    decks = {d.key: d for d in await cards_repo.decks(conn)}

    assert set(decks) == {"main", "ACK"}
    assert decks["main"].count == 31
    assert decks["ACK"].count == 6
    assert decks["ACK"].title == book.title


async def test_раздача_из_книжной_колоды_берёт_только_её_карты(conn, config):
    book = await make_book(conn)
    await make_book_deck(conn, book.id)
    users = await make_members(conn, 4)
    settings = await settings_repo.effective(conn, config)

    deal = await deals_repo.create(conn, book.id, INSERT, POOL_DECK, ["ACK"])
    await service.generate(conn, deal, users, settings)

    views = await deals_repo.views(conn, deal.id)
    assert len(views) == 4
    assert all(v.card.code.startswith("ACK-") for v in views)


async def test_раздача_из_базовой_колоды_не_трогает_книжные_карты(conn, config):
    book = await make_book(conn)
    await make_book_deck(conn, book.id)
    users = await make_members(conn, 5)
    settings = await settings_repo.effective(conn, config)

    deal = await deals_repo.create(conn, book.id, "mixed", POOL_DECK, ["main"])
    await service.generate(conn, deal, users, settings)

    views = await deals_repo.views(conn, deal.id)
    assert len(views) == 5
    assert not any(v.card.code.startswith("ACK-") for v in views)


async def test_книжная_колода_меньше_состава_даёт_понятную_ошибку(conn, config):
    book = await make_book(conn)
    await make_book_deck(conn, book.id, count=3)
    users = await make_members(conn, 4)
    settings = await settings_repo.effective(conn, config)

    deal = await deals_repo.create(conn, book.id, INSERT, POOL_DECK, ["ACK"])
    with pytest.raises(NotEnoughCards) as exc:
        await service.generate(conn, deal, users, settings)

    assert exc.value.missing == 1

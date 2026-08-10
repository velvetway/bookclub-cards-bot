"""Тесты алгоритма раздачи. Пункты приёмки 4, 5, 6 из ТЗ."""

from __future__ import annotations

import random

import pytest
from conftest import days_ago, deck, make_card

from bot.dealer import NotEnoughCards, UserHistory, choose_card, deal
from bot.models import INSERT, OPTICS, RATING


def rng() -> random.Random:
    return random.Random(20260810)


def test_каждый_участник_получает_свою_карту():
    users = [1, 2, 3, 4, 5, 6, 7]
    result = deal(users, deck(20), {}, rng=rng())

    assert [c.user_id for c in result] == users
    assert len({c.card_id for c in result}) == len(users)


def test_пул_из_пяти_карт_раздаётся_пятерым():
    result = deal([1, 2, 3, 4, 5], deck(5), {}, weighted=False, rng=rng())
    assert len(result) == 5
    assert len({c.card_id for c in result}) == 5


def test_пул_из_пяти_карт_падает_на_шести_участниках():
    with pytest.raises(NotEnoughCards) as exc:
        deal([1, 2, 3, 4, 5, 6], deck(5), {}, weighted=False, rng=rng())

    assert exc.value.missing == 1
    assert exc.value.available == 5


def test_неактивные_карты_в_раздачу_не_идут():
    pool = deck(4) + [make_card(99, "OFF-01", is_active=False)]
    result = deal([1, 2, 3, 4], pool, {}, weighted=False, rng=rng())
    assert 99 not in {c.card_id for c in result}


def test_карта_не_повторяется_в_пределах_окна():
    pool = deck(10)
    seen = frozenset({1, 2, 3, 4, 5})
    history = {7: UserHistory(recent_card_ids=seen)}

    for _ in range(50):
        result = deal([7], pool, history, weighted=False, rng=random.Random())
        assert result[0].card_id not in seen
        assert result[0].repeat_of is None


def test_окно_ослабляется_когда_свежих_карт_не_осталось():
    pool = deck(3)
    history = {
        7: UserHistory(
            recent_card_ids=frozenset({1, 2, 3}),
            last_dealt={1: days_ago(5), 2: days_ago(40), 3: days_ago(12)},
        )
    }

    result = deal([7], pool, history, weighted=False, rng=rng())

    assert result[0].card_id == 2, "берём карту с самой старой выдачей"
    assert result[0].repeat_of is not None, "назначение помечено как повтор"


def test_оптика_не_выпадает_после_недавней_оптики():
    pool = deck(5, INSERT) + [make_card(50, "OPT-01", OPTICS), make_card(51, "OPT-02", OPTICS)]
    history = {7: UserHistory(had_optics_recently=True)}

    for _ in range(100):
        result = deal([7], pool, history, rng=random.Random())
        assert result[0].card_id not in (50, 51)


def test_кулдаун_оптики_не_блокирует_раздачу_чистой_оптики():
    """Фаза «оптика»: пул целиком из оптики, иначе раздать было бы нечего."""
    pool = [make_card(50, "OPT-01", OPTICS), make_card(51, "OPT-02", OPTICS)]
    history = {7: UserHistory(had_optics_recently=True), 8: UserHistory()}

    result = deal([7, 8], pool, history, weighted=False, rng=rng())

    assert {c.card_id for c in result} == {50, 51}


def test_кулдаун_ослабляется_если_свободна_только_оптика():
    pool = [make_card(1, "INS-01", INSERT), make_card(50, "OPT-01", OPTICS)]
    history = {7: UserHistory(), 8: UserHistory(had_optics_recently=True)}

    result = deal([7, 8], pool, history, weighted=False, rng=rng())

    assert len({c.card_id for c in result}) == 2, "оба участника получили карты"


def test_веса_типов_дают_примерно_20_65_15():
    pool = (
        [make_card(i, f"OPT-{i:02d}", OPTICS) for i in range(1, 7)]
        + [make_card(20 + i, f"INS-{i:02d}", INSERT) for i in range(1, 21)]
        + [make_card(60 + i, f"RAT-{i:02d}", RATING) for i in range(1, 6)]
    )
    by_id = {c.id: c for c in pool}
    counts = {OPTICS: 0, INSERT: 0, RATING: 0}

    runs = 3000
    generator = random.Random(1)
    for _ in range(runs):
        card, _ = choose_card(UserHistory(), pool, set(), weighted=True, rng=generator)
        counts[by_id[card.id].type] += 1

    assert 0.14 < counts[OPTICS] / runs < 0.27
    assert 0.57 < counts[INSERT] / runs < 0.73
    assert 0.10 < counts[RATING] / runs < 0.21


def test_равномерный_выбор_без_весов():
    """При произвольном пуле веса типов не применяются: 6 карт оптики против 1 врезки."""
    pool = [make_card(i, f"OPT-{i:02d}", OPTICS) for i in range(1, 7)]
    pool.append(make_card(9, "INS-01", INSERT))
    counts = {OPTICS: 0, INSERT: 0}
    by_id = {c.id: c for c in pool}

    generator = random.Random(2)
    runs = 2000
    for _ in range(runs):
        card, _ = choose_card(UserHistory(), pool, set(), weighted=False, rng=generator)
        counts[by_id[card.id].type] += 1

    assert 0.10 < counts[INSERT] / runs < 0.19, "≈1/7 при равномерном выборе"


def test_карта_под_книгу_выпадает_чаще():
    pool = deck(4) + [make_card(77, "BOOK-01", INSERT, book_id=3)]
    hits = 0
    generator = random.Random(3)
    runs = 2000
    for _ in range(runs):
        card, _ = choose_card(UserHistory(), pool, set(), weighted=False, book_id=3, rng=generator)
        hits += card.id == 77

    assert hits / runs > 0.30, "книжная карта весит втрое против обычной (ожидание ≈3/7)"


def test_порядок_участников_перемешивается():
    """Порядок обхода не должен давать преимущества, но ответ приходит в исходном порядке."""
    users = list(range(1, 8))
    pool = deck(7)

    first_cards = set()
    for seed in range(30):
        result = deal(users, pool, {}, weighted=False, rng=random.Random(seed))
        assert [c.user_id for c in result] == users
        first_cards.add(result[0].card_id)

    assert len(first_cards) > 1, "первому участнику не достаётся всегда одна и та же карта"

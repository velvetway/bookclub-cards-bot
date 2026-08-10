"""Сборка текстов сообщений. Разметка везде HTML."""

from __future__ import annotations

from html import escape
from zoneinfo import ZoneInfo

from bot.models import (
    ASSIGN_FAILED,
    ASSIGN_SENT,
    CARD_TYPE_NAMES,
    DEAL_PARTIAL,
    DEAL_SENT,
    OPTICS,
    PHASE_NAMES,
    Book,
    Card,
    Deal,
    User,
)
from bot.storage.deals import AssignmentView
from bot.storage.settings import OPTICS_NOTE
from bot.timeutil import fmt_date_short, fmt_dt

STATUS_NAMES = {
    "draft": "черновик",
    "sent": "отправлена",
    "partial": "частично доставлена",
    "cancelled": "отменена",
}


def plural(n: int, one: str, few: str, many: str) -> str:
    if n % 10 == 1 and n % 100 != 11:
        return one
    if 2 <= n % 10 <= 4 and not 12 <= n % 100 <= 14:
        return few
    return many


def members_word(n: int) -> str:
    return f"{n} {plural(n, 'участник', 'участника', 'участников')}"


def book_line(book: Book | None) -> str:
    if book is None:
        return "Книга не выбрана"
    author = f" — {escape(book.author)}" if book.author else ""
    return f"«{escape(book.title)}»{author}"


class _SafeDict(dict):
    """Неизвестный плейсхолдер в шаблоне не должен ронять рассылку."""

    def __missing__(self, key: str) -> str:
        return "{" + key + "}"


def card_fields(book: Book | None, card: Card, tz: ZoneInfo) -> dict[str, str]:
    return {
        "book": escape(book.title) if book else "—",
        "author": escape(book.author) if book and book.author else "",
        "meeting": fmt_dt(book.meeting_at, tz) if book else "не назначена",
        "card_title": f"<b>{escape(card.title)}</b>",
        "card_hint": escape(card.hint or ""),
        "card_code": card.code,
        "card_type": CARD_TYPE_NAMES.get(card.type, card.type),
    }


def render_card_message(
    template: str,
    book: Book | None,
    card: Card,
    tz: ZoneInfo,
) -> str:
    """Личное сообщение участнику с его картой."""
    fields = _SafeDict(card_fields(book, card, tz))
    try:
        text = template.format_map(fields)
    except (IndexError, ValueError):
        # шаблон сломан — отдаём его как есть, чтобы админ увидел проблему в отчёте
        text = template
    if card.type == OPTICS:
        text += f"\n\n{OPTICS_NOTE}"
    return text


def preview(
    deal: Deal,
    book: Book | None,
    views: list[AssignmentView],
    tz: ZoneInfo,
    *,
    numbered: bool = True,
) -> str:
    head = [
        f"Книга: {book_line(book)}",
        f"Тип: {PHASE_NAMES.get(deal.phase, deal.phase)} · {members_word(len(views))}",
    ]
    if book and book.meeting_at:
        head.append(f"Встреча: {fmt_dt(book.meeting_at, tz)}")

    lines = []
    for index, view in enumerate(views, start=1):
        marks = []
        if view.assignment.repeat_of:
            marks.append(f"повтор от {fmt_date_short(view.assignment.repeat_of, tz)}")
        if view.assignment.manual:
            marks.append("вручную")
        if view.assignment.reroll_count:
            marks.append(f"реролл ×{view.assignment.reroll_count}")
        suffix = f"  <i>({', '.join(marks)})</i>" if marks else ""
        prefix = f"{index}. " if numbered else "• "
        lines.append(
            f"{prefix}{escape(view.user.display_name)} — "
            f"{view.card.code} {escape(view.card.title)}{suffix}"
        )

    body = "\n".join(lines) if lines else "<i>состав пуст</i>"
    return "\n".join(head) + "\n\n" + body


def delivery_report(views: list[AssignmentView], tz: ZoneInfo) -> str:
    sent = [v for v in views if v.assignment.status == ASSIGN_SENT]
    failed = [v for v in views if v.assignment.status == ASSIGN_FAILED]

    lines = [f"Доставлено: {len(sent)} из {len(views)}"]
    if failed:
        lines.append("")
        lines.append("Не дошло:")
        for view in failed:
            reason = view.assignment.error or "неизвестная ошибка"
            lines.append(f"• {escape(view.user.display_name)} — {escape(reason)}")
        lines.append("")
        lines.append("Карты у этих участников сохранены: повтор отправит те же самые.")
    return "\n".join(lines)


def group_announcement(count: int, book: Book | None, tz: ZoneInfo) -> str:
    meeting = ""
    if book and book.meeting_at:
        meeting = f" Встреча {fmt_dt(book.meeting_at, tz)}."
    return f"Карты розданы: {members_word(count)}.{meeting}"


def member_line(user: User) -> str:
    marks = []
    if not user.reachable:
        marks.append("не нажал /start")
    if not user.is_active:
        marks.append("неактивен")
    if user.is_admin:
        marks.append("админ")
    suffix = f" <i>({', '.join(marks)})</i>" if marks else ""
    handle = f" @{escape(user.username)}" if user.username else ""
    return f"{escape(user.display_name)}{handle}{suffix}"


def card_line(card: Card) -> str:
    state = "" if card.is_active else " <i>(выключена)</i>"
    hint = f"\n   <i>{escape(card.hint)}</i>" if card.hint else ""
    return f"{card.code} <b>{escape(card.title)}</b>{state}{hint}"


def deal_status_line(deal: Deal, tz: ZoneInfo) -> str:
    status = STATUS_NAMES.get(deal.status, deal.status)
    when = ""
    if deal.status in (DEAL_SENT, DEAL_PARTIAL) and deal.sent_at:
        when = f" · {fmt_date_short(deal.sent_at, tz)}"
    return f"Раздача №{deal.id} · {PHASE_NAMES.get(deal.phase, deal.phase)} · {status}{when}"

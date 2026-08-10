"""Работа со временем: в базе всё в UTC, пользователю показываем в локальной зоне."""

from __future__ import annotations

import re
from datetime import date, datetime, timezone
from zoneinfo import ZoneInfo

MONTHS_RU = (
    "января", "февраля", "марта", "апреля", "мая", "июня",
    "июля", "августа", "сентября", "октября", "ноября", "декабря",
)

_DATE_PATTERNS = (
    "%d.%m.%Y %H:%M",
    "%d.%m.%Y",
    "%d.%m.%y %H:%M",
    "%d.%m.%y",
    "%Y-%m-%d %H:%M",
    "%Y-%m-%d",
)


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def utcnow_iso() -> str:
    return utcnow().isoformat(timespec="seconds")


def parse_dt(raw: str | None) -> datetime | None:
    """Читает то, что лежит в базе: ISO-строку либо формат SQLite CURRENT_TIMESTAMP."""
    if not raw:
        return None
    if isinstance(raw, datetime):
        return raw if raw.tzinfo else raw.replace(tzinfo=timezone.utc)
    text = str(raw).strip()
    try:
        dt = datetime.fromisoformat(text)
    except ValueError:
        try:
            dt = datetime.strptime(text, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            return None
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def parse_user_datetime(text: str, tz: ZoneInfo) -> datetime | None:
    """Разбирает дату встречи, введённую человеком. Без времени — 19:00."""
    text = text.strip()
    for pattern in _DATE_PATTERNS:
        try:
            naive = datetime.strptime(text, pattern)
        except ValueError:
            continue
        if "%H" not in pattern:
            naive = naive.replace(hour=19, minute=0)
        return naive.replace(tzinfo=tz).astimezone(timezone.utc)
    return None


def fmt_dt(dt: datetime | None, tz: ZoneInfo, with_time: bool = True) -> str:
    if dt is None:
        return "не назначена"
    local = dt.astimezone(tz)
    head = f"{local.day} {MONTHS_RU[local.month - 1]}"
    if local.year != datetime.now(tz).year:
        head += f" {local.year}"
    return f"{head}, {local:%H:%M}" if with_time else head


def fmt_date_short(dt: datetime | None, tz: ZoneInfo) -> str:
    if dt is None:
        return "—"
    return dt.astimezone(tz).strftime("%d.%m.%Y")


def today_iso(tz: ZoneInfo) -> str:
    return datetime.now(tz).date().isoformat()


def parse_date_only(raw: str | None) -> date | None:
    if not raw:
        return None
    match = re.match(r"(\d{4})-(\d{2})-(\d{2})", str(raw))
    if not match:
        return None
    return date(int(match.group(1)), int(match.group(2)), int(match.group(3)))

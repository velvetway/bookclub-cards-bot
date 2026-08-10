"""Конфигурация из переменных окружения."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent


def _int_list(raw: str | None) -> list[int]:
    if not raw:
        return []
    out: list[int] = []
    for chunk in raw.replace(";", ",").split(","):
        chunk = chunk.strip()
        if chunk:
            out.append(int(chunk))
    return out


def _int(raw: str | None, default: int) -> int:
    if raw is None or not raw.strip():
        return default
    return int(raw.strip())


@dataclass(frozen=True)
class Config:
    bot_token: str
    admin_ids: list[int] = field(default_factory=list)
    group_chat_id: int | None = None
    db_path: Path = BASE_DIR / "data" / "bot.db"
    tz_name: str = "Europe/Moscow"
    no_repeat_window: int = 10
    optics_cooldown: int = 3
    rerolls_per_deal: int = 1
    log_dir: Path = BASE_DIR / "logs"

    @property
    def tz(self) -> ZoneInfo:
        try:
            return ZoneInfo(self.tz_name)
        except ZoneInfoNotFoundError:
            return ZoneInfo("UTC")


def load_config(env_file: str | os.PathLike[str] | None = None) -> Config:
    load_dotenv(env_file or BASE_DIR / ".env")

    token = (os.getenv("BOT_TOKEN") or "").strip()
    if not token:
        raise RuntimeError(
            "BOT_TOKEN не задан. Скопируйте .env.example в .env и впишите токен от @BotFather."
        )

    group_raw = (os.getenv("GROUP_CHAT_ID") or "").strip()
    db_raw = (os.getenv("DB_PATH") or "data/bot.db").strip()
    db_path = Path(db_raw)
    if not db_path.is_absolute():
        db_path = BASE_DIR / db_path

    log_raw = (os.getenv("LOG_DIR") or "logs").strip()
    log_dir = Path(log_raw)
    if not log_dir.is_absolute():
        log_dir = BASE_DIR / log_dir

    return Config(
        bot_token=token,
        admin_ids=_int_list(os.getenv("ADMIN_IDS")),
        group_chat_id=int(group_raw) if group_raw else None,
        db_path=db_path,
        tz_name=(os.getenv("TZ") or "Europe/Moscow").strip(),
        no_repeat_window=_int(os.getenv("NO_REPEAT_WINDOW"), 10),
        optics_cooldown=_int(os.getenv("OPTICS_COOLDOWN"), 3),
        rerolls_per_deal=_int(os.getenv("REROLLS_PER_DEAL"), 1),
        log_dir=log_dir,
    )

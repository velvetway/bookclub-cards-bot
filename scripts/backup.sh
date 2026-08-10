#!/usr/bin/env bash
# Ежедневная копия базы. Хранит 30 дней, старое удаляет.
#
# Копия снимается через `sqlite3 .backup` — это безопасно на работающем боте,
# простой `cp` при включённом WAL может дать битый файл.
#
# Ставится в cron:
#   0 4 * * * /opt/bookclub-cards-bot/scripts/backup.sh >> /var/log/bookclub-backup.log 2>&1

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DB="${1:-$ROOT/data/bot.db}"
BACKUP_DIR="${BACKUP_DIR:-$ROOT/backups}"
KEEP_DAYS="${KEEP_DAYS:-30}"

if [[ ! -f "$DB" ]]; then
  echo "базы нет: $DB" >&2
  exit 1
fi

mkdir -p "$BACKUP_DIR"
STAMP="$(date +%Y-%m-%d)"
TARGET="$BACKUP_DIR/bot-$STAMP.db"

sqlite3 "$DB" ".backup '$TARGET'"
gzip -f "$TARGET"

find "$BACKUP_DIR" -name 'bot-*.db.gz' -type f -mtime "+$KEEP_DAYS" -delete

echo "$(date '+%Y-%m-%d %H:%M:%S') бэкап готов: $TARGET.gz"

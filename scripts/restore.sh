#!/usr/bin/env bash
# 從備份檔還原 PostgreSQL
# 使用方式：bash scripts/restore.sh backups/db_20260624_120000.sql.gz
set -euo pipefail

FILE="${1:?請提供備份檔路徑，例如：bash scripts/restore.sh backups/db_20260624_120000.sql.gz}"

if [[ ! -f "$FILE" ]]; then
  echo "錯誤：找不到檔案 $FILE" >&2
  exit 1
fi

echo "⚠ 即將還原 ${POSTGRES_DB:-portfolio_db} 從 $FILE"
echo "   這會覆蓋現有資料！按 Enter 繼續，Ctrl+C 取消..."
read -r

echo "▶ 還原中..."
gunzip -c "$FILE" | docker compose exec -T db psql \
  -U "${POSTGRES_USER:-portfolio}" \
  "${POSTGRES_DB:-portfolio_db}"

echo "✓ 還原完成"

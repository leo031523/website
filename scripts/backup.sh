#!/usr/bin/env bash
# 手動備份 PostgreSQL（自動備份由 docker-compose.prod.yml backup 服務處理）
set -euo pipefail

BACKUP_DIR="./backups"
DATE=$(date +%Y%m%d_%H%M%S)
FILE="${BACKUP_DIR}/db_${DATE}.sql.gz"

mkdir -p "$BACKUP_DIR"

echo "▶ 備份中..."
docker compose exec -T db pg_dump \
  -U "${POSTGRES_USER:-portfolio}" \
  "${POSTGRES_DB:-portfolio_db}" \
  | gzip > "$FILE"

echo "✓ 備份完成：$FILE ($(du -sh "$FILE" | cut -f1))"

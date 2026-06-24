#!/usr/bin/env bash
# 初次取得 Let's Encrypt 憑證
# 使用方式：bash scripts/init-certbot.sh <domain> <email>
# 範例：    bash scripts/init-certbot.sh example.com admin@example.com
set -euo pipefail

DOMAIN="${1:?請提供 domain，例如：bash scripts/init-certbot.sh example.com your@email.com}"
EMAIL="${2:?請提供 email，例如：bash scripts/init-certbot.sh example.com your@email.com}"

echo "▶ 替換 nginx.prod.conf 中的 YOUR_DOMAIN → $DOMAIN"
sed -i.bak "s/YOUR_DOMAIN/$DOMAIN/g" nginx/nginx.prod.conf && rm -f nginx/nginx.prod.conf.bak

echo "▶ 先以 HTTP-only 模式啟動 nginx（讓 ACME challenge 通過）"
# 暫時用開發版 nginx.conf（只有 port 80，不需要 SSL 憑證）
docker compose up -d nginx

sleep 3

echo "▶ 申請憑證（webroot）"
docker compose -f docker-compose.yml -f docker-compose.prod.yml run --rm certbot \
  certbot certonly \
  --webroot \
  --webroot-path=/var/www/certbot \
  --email "$EMAIL" \
  --agree-tos \
  --no-eff-email \
  -d "$DOMAIN"

echo "▶ 切換到完整 production 模式（HTTPS）"
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d

echo "✓ 完成！網站現在應可透過 https://$DOMAIN 訪問"

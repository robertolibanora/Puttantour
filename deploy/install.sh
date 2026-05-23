#!/usr/bin/env bash
set -euo pipefail

ROOT="/var/www/Puttantour"

echo "==> Install systemd service"
install -m 644 "$ROOT/deploy/puttantour.service" /etc/systemd/system/puttantour.service

echo "==> Update Caddyfile (skip if block already present)"
if ! grep -q 'puttantour.online' /etc/caddy/Caddyfile; then
  cat "$ROOT/deploy/caddy-puttantour.conf" >> /etc/caddy/Caddyfile
fi

echo "==> Reload services"
systemctl daemon-reload
systemctl enable puttantour.service
systemctl restart puttantour.service
caddy validate --config /etc/caddy/Caddyfile
systemctl reload caddy

echo "==> Status"
systemctl --no-pager status puttantour.service
echo "OK: https://puttantour.online -> 127.0.0.1:8999"

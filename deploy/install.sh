#!/usr/bin/env bash
set -euo pipefail

ROOT="/var/www/AlbaShore"

echo "==> Install systemd service"
install -m 644 "$ROOT/deploy/albashore.service" /etc/systemd/system/albashore.service

echo "==> Update Caddyfile (skip if block already present)"
if ! grep -q 'alba.puttantour.online' /etc/caddy/Caddyfile; then
  cat "$ROOT/deploy/caddy-albashore.conf" >> /etc/caddy/Caddyfile
fi

echo "==> Reload services"
systemctl daemon-reload
systemctl enable albashore.service
systemctl restart albashore.service
caddy validate --config /etc/caddy/Caddyfile
systemctl reload caddy

echo "==> Status"
systemctl --no-pager status albashore.service
echo "OK: https://alba.puttantour.online -> 127.0.0.1:8998"

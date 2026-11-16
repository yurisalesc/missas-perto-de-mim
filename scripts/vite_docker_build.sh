#!/usr/bin/env bash
set -euo pipefail

npm install --no-fund --no-audit qrcode@1.5.4 >&2
test -f node_modules/qrcode/package.json
npx --yes vite build >&2

if ! grep -R -E --include='*.js' 'window\.__API_BASE__\|\|[`"]/api[`"]' dist >/dev/null; then
  echo "[deploy] Built web assets missing production API_BASE=/api" >&2
  grep -R -n --include='*.js' -E 'window\.__API_BASE__|127\.0\.0\.1:8000|/api' dist >&2 || true
  exit 1
fi

tar -C dist -cf - .

#!/usr/bin/env bash
# Runs inside the node Docker image during production deploy.
# Reads a web source tar from stdin and writes the dist tar to stdout.
set -euo pipefail

mkdir -p /app
tar -xf - -C /app
cd /app

npm install --no-fund --no-audit qrcode@1.5.4 >&2
test -f node_modules/qrcode/package.json
npx --yes vite build >&2

# Fail the deploy if the public bundle did not bake the production API base.
if ! grep -R -E --include='*.js' 'window\.__API_BASE__\|\|[`"]/api[`"]' /app/dist >/dev/null; then
  echo "[deploy] Built web assets missing production API_BASE=/api" >&2
  grep -R -n --include='*.js' -E 'window\.__API_BASE__|127\.0\.0\.1:8000|/api' /app/dist >&2 || true
  exit 1
fi

tar -C /app/dist -cf - .

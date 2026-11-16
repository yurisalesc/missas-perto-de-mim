#!/usr/bin/env bash
# Runs inside the node Docker image during production deploy.
# Expects the web project already extracted into the current directory.
# Writes the dist tar to stdout.
set -euo pipefail

npm install --no-fund --no-audit qrcode@1.5.4 >&2
test -f node_modules/qrcode/package.json
npx --yes vite build >&2

# Fail the deploy if the public bundle did not bake the production API base.
if ! grep -R -E --include='*.js' 'window\.__API_BASE__\|\|[`"]/api[`"]' dist >/dev/null; then
  echo "[deploy] Built web assets missing production API_BASE=/api" >&2
  grep -R -n --include='*.js' -E 'window\.__API_BASE__|127\.0\.0\.1:8000|/api' dist >&2 || true
  exit 1
fi

tar -C dist -cf - .

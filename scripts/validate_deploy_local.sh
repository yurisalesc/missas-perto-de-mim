#!/usr/bin/env bash
set -Eeuo pipefail

echo "[validate] 1/5 bash syntax"
bash -n scripts/deploy_production.sh

echo "[validate] 2/5 workflow file exists"
test -f .github/workflows/deploy.yml

echo "[validate] 3/5 compose production config"
docker compose -p missas -f docker-compose.prod.yml config >/dev/null

echo "[validate] 4/5 frontend syntax"
node --check apps/web/src/main.js
node --check apps/web/src/admin.js

echo "[validate] 5/5 local tree status"
git status --short

cat <<'EOF'
[validate] OK
Before push, still run these on VPS when possible:
  - docker ps --filter publish=8000
  - curl -fsS http://127.0.0.1:8000/health || true
EOF

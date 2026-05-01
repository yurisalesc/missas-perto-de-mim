#!/usr/bin/env bash
set -Eeuo pipefail

trap 'echo "FAILED: line=${LINENO} cmd=${BASH_COMMAND}" >&2' ERR

APP_DIR="${APP_DIR:-/opt/missas-perto-de-mim}"
COMPOSE_ARGS="-p missas -f docker-compose.prod.yml"
DB_NAME="${POSTGRES_DB:-missa_perto}"
DB_USER="${POSTGRES_USER:-missa_user}"
BACKUP_DIR="${BACKUP_DIR:-/var/backups/missas-perto-de-mim}"
TIMESTAMP="$(date +%Y%m%d-%H%M%S)"
BACKUP_FILE="${BACKUP_DIR}/db-${TIMESTAMP}.sql.gz"
WEB_TMP_DIR="/var/www/missas_tmp_${TIMESTAMP}"

echo "[deploy] Step 1/7: update source"
cd "$APP_DIR"
git pull --ff-only origin main

echo "[deploy] Step 2/7: database safety backup"
mkdir -p "$BACKUP_DIR"
EXISTING_DB_CONTAINER="$(docker compose $COMPOSE_ARGS ps -q db || true)"
if [ -n "$EXISTING_DB_CONTAINER" ] && [ "$(docker inspect -f '{{.State.Running}}' "$EXISTING_DB_CONTAINER" 2>/dev/null || echo false)" = "true" ]; then
  echo "[deploy] Creating backup at $BACKUP_FILE"
  docker exec "$EXISTING_DB_CONTAINER" pg_dump -U "$DB_USER" "$DB_NAME" | gzip > "$BACKUP_FILE"
  shopt -s nullglob
  backup_files=("$BACKUP_DIR"/db-*.sql.gz)
  if [ "${#backup_files[@]}" -gt 14 ]; then
    printf '%s\n' "${backup_files[@]}" | sort -r | tail -n +15 | xargs -r rm -f
  fi
  shopt -u nullglob
else
  echo "[deploy] No running DB container found, skipping backup"
fi

echo "[deploy] Step 3/7: restart api only (db volume untouched)"
docker compose $COMPOSE_ARGS up -d db
docker compose $COMPOSE_ARGS up -d --build --no-deps api

echo "[deploy] Step 4/7: wait api health"
for _ in $(seq 1 60); do
  if curl -fsS http://127.0.0.1:8000/health >/dev/null; then
    echo "[deploy] API is healthy"
    break
  fi
  sleep 2
done
curl -fsS http://127.0.0.1:8000/health >/dev/null

echo "[deploy] Step 5/7: build web"
mkdir -p /var/www/missas "$WEB_TMP_DIR"
tar -C "$APP_DIR/apps/web" -cf - . \
  | docker run --rm -i -w /app node:22-bookworm bash -lc "set -euo pipefail; mkdir -p /app; tar -xf - -C /app; npx --yes vite build >&2; tar -C /app/dist -cf - ." \
  | tar -C "$WEB_TMP_DIR" -xf -
mkdir -p "$WEB_TMP_DIR/src"
cp "$APP_DIR/apps/web/admin.html" "$WEB_TMP_DIR/admin.html"
cp -r "$APP_DIR/apps/web/src/"* "$WEB_TMP_DIR/src/"
sed -i 's|http://127.0.0.1:8000|/api|g' "$WEB_TMP_DIR/src/config.js"

echo "[deploy] Step 6/7: publish web files"
if command -v rsync >/dev/null 2>&1; then
  rsync -a --delete "$WEB_TMP_DIR"/ /var/www/missas/
else
  cp -a "$WEB_TMP_DIR"/. /var/www/missas/
fi
rm -rf "$WEB_TMP_DIR"
chown -R www-data:www-data /var/www/missas || true
chmod -R 755 /var/www/missas

echo "[deploy] Step 7/7: reload nginx"
nginx -t
systemctl reload nginx
echo "[deploy] Done"

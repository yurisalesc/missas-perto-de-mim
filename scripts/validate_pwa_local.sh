#!/usr/bin/env bash
set -Eeuo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WEB_DIR="$ROOT_DIR/apps/web"
DIST_DIR="$WEB_DIR/dist"
PORT="${PWA_PREVIEW_PORT:-4173}"
cd "$ROOT_DIR"

echo "[pwa-validate] 1/6 syntax checks"
node --check "$WEB_DIR/src/main.js"
node --check "$WEB_DIR/public/sw.js"
python3 -m json.tool "$WEB_DIR/public/manifest.webmanifest" >/dev/null

echo "[pwa-validate] 2/6 required source assets"
required=(
  "$WEB_DIR/public/manifest.webmanifest"
  "$WEB_DIR/public/sw.js"
  "$WEB_DIR/public/icons/icon-180.png"
  "$WEB_DIR/public/icons/icon-192.png"
  "$WEB_DIR/public/icons/icon-512.png"
  "$WEB_DIR/public/icons/icon-192-maskable.png"
  "$WEB_DIR/public/icons/icon-512-maskable.png"
)
for path in "${required[@]}"; do
  test -f "$path" || { echo "Missing: $path" >&2; exit 1; }
done

echo "[pwa-validate] 3/6 vite build"
(
  cd "$WEB_DIR"
  npx --yes vite build >/tmp/missas-pwa-vite-build.log 2>&1
)

echo "[pwa-validate] 4/6 dist contents"
dist_required=(
  "$DIST_DIR/manifest.webmanifest"
  "$DIST_DIR/sw.js"
  "$DIST_DIR/icons/icon-180.png"
  "$DIST_DIR/icons/icon-192.png"
  "$DIST_DIR/icons/icon-512.png"
  "$DIST_DIR/icons/icon-192-maskable.png"
  "$DIST_DIR/icons/icon-512-maskable.png"
  "$DIST_DIR/index.html"
)
for path in "${dist_required[@]}"; do
  test -f "$path" || { echo "Missing in dist: $path" >&2; exit 1; }
done

grep -q 'rel="manifest"' "$DIST_DIR/index.html"
grep -q '/manifest.webmanifest' "$DIST_DIR/index.html"
grep -q 'serviceWorker.register("/sw.js")' "$WEB_DIR/src/main.js"
grep -q 'missas-perto-v3' "$DIST_DIR/sw.js"
grep -q '/api/' "$DIST_DIR/sw.js"

python3 - <<PY
import json
from pathlib import Path
manifest = json.loads(Path(r"$DIST_DIR/manifest.webmanifest").read_text())
assert manifest["display"] == "standalone"
assert manifest["start_url"] == "/"
purposes = {(icon["src"], icon["purpose"]) for icon in manifest["icons"]}
needed = {
    ("/icons/icon-192.png", "any"),
    ("/icons/icon-512.png", "any"),
    ("/icons/icon-192-maskable.png", "maskable"),
    ("/icons/icon-512-maskable.png", "maskable"),
}
missing = needed - purposes
assert not missing, f"Missing icon purposes: {missing}"
print("[pwa-validate] manifest OK")
PY

echo "[pwa-validate] 5/6 HTTP preview + endpoints"
preview_log="/tmp/missas-pwa-preview.log"
(
  cd "$WEB_DIR"
  npx --yes vite preview --host 127.0.0.1 --port "$PORT" --strictPort
) >"$preview_log" 2>&1 &
PREVIEW_PID=$!
cleanup() {
  kill "$PREVIEW_PID" 2>/dev/null || true
  wait "$PREVIEW_PID" 2>/dev/null || true
}
trap cleanup EXIT

for _ in $(seq 1 60); do
  if curl -fsS "http://127.0.0.1:${PORT}/" >/dev/null 2>&1; then
    break
  fi
  sleep 0.25
done

curl -fsS "http://127.0.0.1:${PORT}/" >/dev/null
curl -fsS "http://127.0.0.1:${PORT}/manifest.webmanifest" >/dev/null
curl -fsS "http://127.0.0.1:${PORT}/sw.js" >/dev/null
curl -fsS "http://127.0.0.1:${PORT}/icons/icon-512.png" >/dev/null
curl -fsS "http://127.0.0.1:${PORT}/icons/icon-512-maskable.png" >/dev/null
echo "[pwa-validate] HTTP endpoints OK"

echo "[pwa-validate] 6/6 service worker registration (Playwright)"
PLAYWRIGHT_DIR="$(mktemp -d /tmp/missas-pwa-playwright-XXXXXX)"
cleanup_playwright() {
  rm -rf "$PLAYWRIGHT_DIR"
}
trap 'cleanup; cleanup_playwright' EXIT
cp "$ROOT_DIR/scripts/pwa_sw_smoke.mjs" "$PLAYWRIGHT_DIR/pwa_sw_smoke.mjs"
npm install --silent --prefix "$PLAYWRIGHT_DIR" playwright >/tmp/missas-pwa-playwright-install.log 2>&1
(
  cd "$PLAYWRIGHT_DIR"
  # Reuses ~/.cache/ms-playwright when already present.
  npx --yes playwright install chromium >/tmp/missas-pwa-playwright-browser.log 2>&1
  PWA_PREVIEW_PORT="$PORT" node ./pwa_sw_smoke.mjs
)

echo "[pwa-validate] OK"

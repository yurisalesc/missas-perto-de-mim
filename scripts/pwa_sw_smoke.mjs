import { chromium } from "playwright";

const port = Number(process.env.PWA_PREVIEW_PORT || 4173);
const url = `http://127.0.0.1:${port}/`;

const browser = await chromium.launch({ headless: true });
const page = await browser.newPage();
await page.goto(url, { waitUntil: "networkidle" });

const result = await page.evaluate(async () => {
  if (!("serviceWorker" in navigator)) {
    return { ok: false, reason: "no-sw-api" };
  }
  const reg = await navigator.serviceWorker.register("/sw.js");
  await navigator.serviceWorker.ready;
  const active = reg.active || (await navigator.serviceWorker.getRegistration())?.active;
  const manifestLink = document.querySelector('link[rel="manifest"]');
  let manifestStatus = null;
  try {
    const res = await fetch("/manifest.webmanifest");
    manifestStatus = res.status;
    await res.json();
  } catch (error) {
    return { ok: false, reason: `manifest-fetch:${error.message}` };
  }
  return {
    ok: Boolean(active || reg.installing || reg.waiting),
    scope: reg.scope || null,
    scriptURL:
      active?.scriptURL ||
      reg.installing?.scriptURL ||
      reg.waiting?.scriptURL ||
      null,
    manifestHref: manifestLink?.getAttribute("href") || null,
    manifestStatus,
  };
});

await browser.close();

if (!result.ok) {
  console.error("[pwa-validate] SW registration failed:", result);
  process.exit(1);
}
if (result.manifestHref !== "/manifest.webmanifest" || result.manifestStatus !== 200) {
  console.error("[pwa-validate] manifest check failed:", result);
  process.exit(1);
}
console.log("[pwa-validate] SW registered:", result.scriptURL, "scope:", result.scope);

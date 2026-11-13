const CACHE_NAME = "missas-perto-v6";
const APP_SHELL_URLS = [
  "/",
  "/index.html",
  "/doar.html",
  "/manifest.webmanifest",
  "/icons/icon-192.png",
  "/icons/icon-512.png",
  "/icons/icon-180.png",
  "/icons/icon-192-maskable.png",
  "/icons/icon-512-maskable.png",
];

function isApiRequest(url) {
  return url.pathname === "/api" || url.pathname.startsWith("/api/");
}

function isNavigationPath(pathname) {
  return pathname === "/" || pathname === "/index.html" || pathname === "/doar.html";
}

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches
      .open(CACHE_NAME)
      .then((cache) => cache.addAll(APP_SHELL_URLS))
      .then(() => self.skipWaiting())
  );
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches
      .keys()
      .then((keys) => Promise.all(keys.filter((key) => key !== CACHE_NAME).map((key) => caches.delete(key))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener("fetch", (event) => {
  if (event.request.method !== "GET") return;

  const requestUrl = new URL(event.request.url);
  if (requestUrl.origin !== self.location.origin) return;
  if (isApiRequest(requestUrl)) return;

  if (event.request.mode === "navigate") {
    event.respondWith(
      fetch(event.request)
        .then((response) => {
          if (response && response.ok && isNavigationPath(requestUrl.pathname)) {
            const cacheKey = requestUrl.pathname === "/" ? "/index.html" : requestUrl.pathname;
            const responseClone = response.clone();
            caches.open(CACHE_NAME).then((cache) => cache.put(cacheKey, responseClone));
          }
          return response;
        })
        .catch(() => {
          if (requestUrl.pathname === "/doar.html") {
            return caches.match("/doar.html").then((cached) => cached || caches.match("/index.html"));
          }
          return caches.match("/index.html");
        })
    );
    return;
  }

  if (
    requestUrl.pathname.startsWith("/src/") ||
    requestUrl.pathname.startsWith("/assets/") ||
    requestUrl.pathname.includes("/node_modules/")
  ) {
    event.respondWith(
      fetch(event.request)
        .then((response) => {
          if (response && response.status === 200 && response.type === "basic") {
            const responseClone = response.clone();
            caches.open(CACHE_NAME).then((cache) => cache.put(event.request, responseClone));
          }
          return response;
        })
        .catch(() => caches.match(event.request))
    );
    return;
  }

  event.respondWith(
    caches.match(event.request).then((cachedResponse) => {
      if (cachedResponse) return cachedResponse;

      return fetch(event.request).then((response) => {
        if (!response || response.status !== 200 || response.type !== "basic") {
          return response;
        }
        const responseClone = response.clone();
        caches.open(CACHE_NAME).then((cache) => cache.put(event.request, responseClone));
        return response;
      });
    })
  );
});

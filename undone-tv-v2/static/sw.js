// Service worker de Undone TV.
// Objetivo unico: permitir que el sitio se pueda "instalar" en el celular.
// A proposito NO guarda en cache la pagina principal ni /api/*, porque
// la programacion es en vivo y sincronizada para todos los espectadores;
// si se cacheara, el reloj del canal se desincronizaria.

const CACHE_NAME = "undone-tv-shell-v1";
const SHELL_ASSETS = [
  "/static/manifest.json",
  "/static/icon-192.png",
  "/static/icon-512.png"
];

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll(SHELL_ASSETS))
  );
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((k) => k !== CACHE_NAME).map((k) => caches.delete(k)))
    )
  );
  self.clients.claim();
});

self.addEventListener("fetch", (event) => {
  const url = new URL(event.request.url);

  // La pagina principal y la API siempre van a la red: el canal es en vivo.
  if (url.pathname === "/" || url.pathname.startsWith("/api/")) {
    event.respondWith(fetch(event.request));
    return;
  }

  // El resto (iconos, manifest) puede servirse desde cache si no hay red.
  event.respondWith(
    caches.match(event.request).then((cached) => cached || fetch(event.request))
  );
});

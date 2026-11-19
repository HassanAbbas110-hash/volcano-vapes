// Offline support: pages and stock list network-first (fresh when online), everything else cache-first.
const CACHE = "volcano-v4";
const CORE = ["./", "index.html", "shop.html", "visit.html", "help.html", "about.html", "fit.html", "product.html", "assets/site.css", "assets/volcano.css", "assets/site.js", "assets/fits.js", "assets/img/logo.webp", "assets/img/logo-sm.webp", "assets/img/icon.png"];
self.addEventListener("install", (e) => { e.waitUntil(caches.open(CACHE).then((c) => c.addAll(CORE)).then(() => self.skipWaiting())); });
self.addEventListener("activate", (e) => { e.waitUntil(caches.keys().then((ks) => Promise.all(ks.filter((k) => k !== CACHE).map((k) => caches.delete(k)))).then(() => self.clients.claim())); });
self.addEventListener("fetch", (e) => {
  const req = e.request, url = new URL(req.url);
  if (req.method !== "GET" || url.origin !== location.origin) return; // product photos and maps load straight from the web
  const fresh = req.mode === "navigate" || url.pathname.endsWith(".json") || url.pathname.endsWith(".js") || url.pathname.endsWith(".css");
  const save = (res) => { if (res.ok) { const copy = res.clone(); caches.open(CACHE).then((c) => c.put(req, copy)); } return res; };
  e.respondWith(fresh
    ? fetch(req.url, { cache: "no-cache" }).then(save).catch(() => caches.match(req, { ignoreSearch: req.mode === "navigate" })) // always revalidate: never show an old version
    : caches.match(req).then((hit) => hit || fetch(req).then(save)));
});

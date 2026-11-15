// Keeps the tool page in the browser after the first visit, so a reload does not download it again.
// It checks the server with a small HEAD request and fetches a new copy only when the file has changed.
const C = 'tool-page-v1';
self.addEventListener('install', () => self.skipWaiting());
self.addEventListener('activate', (e) => e.waitUntil(self.clients.claim()));
async function refresh(cache, key, old) {
  try {
    const h = await fetch(key, { method: 'HEAD', cache: 'no-store' });
    const tag = h.headers.get('etag') || h.headers.get('last-modified') || '';
    const had = old ? (old.headers.get('etag') || old.headers.get('last-modified') || '') : null;
    if (old && tag && tag === had) return;
    const r = await fetch(key, { cache: 'no-cache' });
    if (r.ok) await cache.put(key, r.clone());
  } catch (_) {}
}
self.addEventListener('fetch', (e) => {
  const u = new URL(e.request.url);
  if (e.request.method !== 'GET' || u.origin !== location.origin || !/\/app\/(index\.html)?$/.test(u.pathname)) return;
  const key = u.origin + u.pathname.replace(/index\.html$/, '');
  e.respondWith((async () => {
    const cache = await caches.open(C), hit = await cache.match(key);
    if (hit) { e.waitUntil(refresh(cache, key, hit)); return hit; }
    const r = await fetch(key);
    if (r.ok) e.waitUntil(cache.put(key, r.clone()));
    return r;
  })());
});

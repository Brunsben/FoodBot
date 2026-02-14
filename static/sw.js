const CACHE_VERSION = 2;
const CACHE_NAME = `foodbot-v${CACHE_VERSION}`;
const STATIC_ASSETS = [
    '/static/css/base.css',
    '/static/css/components.css',
    '/static/css/layouts.css',
    '/static/css/pages/mobile.css',
    '/static/icons/icon-192.png',
    '/static/icons/icon-512.png'
];

// Install: Cache static assets
self.addEventListener('install', event => {
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then(cache => cache.addAll(STATIC_ASSETS))
            .then(() => self.skipWaiting())
    );
});

// Activate: Clean old caches
self.addEventListener('activate', event => {
    event.waitUntil(
        caches.keys().then(keys =>
            Promise.all(
                keys.filter(k => k !== CACHE_NAME).map(k => caches.delete(k))
            )
        ).then(() => self.clients.claim())
    );
});

// Fetch: Network-first for HTML, cache-first for static assets, no cache for API
self.addEventListener('fetch', event => {
    const url = new URL(event.request.url);

    // API-Anfragen: Nie cachen (sensible Daten)
    if (url.pathname.startsWith('/api/') || url.pathname === '/rfid_scan' || url.pathname.startsWith('/kitchen/data') || url.pathname.startsWith('/menu/data')) {
        event.respondWith(fetch(event.request));
        return;
    }

    // Static assets: cache-first
    if (url.pathname.startsWith('/static/')) {
        event.respondWith(
            caches.match(event.request)
                .then(cached => cached || fetch(event.request).then(resp => {
                    const clone = resp.clone();
                    caches.open(CACHE_NAME).then(c => c.put(event.request, clone));
                    return resp;
                }))
        );
        return;
    }

    // HTML: network-first with offline fallback
    event.respondWith(
        fetch(event.request)
            .then(resp => {
                if (event.request.method === 'GET' && resp.status === 200) {
                    const clone = resp.clone();
                    caches.open(CACHE_NAME).then(c => c.put(event.request, clone));
                }
                return resp;
            })
            .catch(() => caches.match(event.request))
    );
});

const CACHE_NAME = 'persona-chat-v3';
const ASSETS_TO_CACHE = [
  '/',
  '/index.html',
  '/app.js',
  '/style.css',
  '/manifest.json',
  '/src/logo3.png',
  // ES 모듈 파일들
  '/modules/ui/modals.js',
  '/modules/ui/screens.js',
  '/modules/routing/router.js'
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll(ASSETS_TO_CACHE.map((p) => new Request(p, { cache: 'no-cache' })));
    })
  );
  // skipWaiting()은 클라이언트 요청 시에만 호출 (사용자가 토스트 클릭할 때)
});

// 클라이언트에서 SKIP_WAITING 메시지를 받으면 활성화
self.addEventListener('message', (event) => {
  if (event.data && event.data.type === 'SKIP_WAITING') {
    self.skipWaiting();
  }
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) => Promise.all(
      keys.filter(k => k !== CACHE_NAME).map(k => caches.delete(k))
    ))
  );
  self.clients.claim();
});

self.addEventListener('fetch', (event) => {
  const req = event.request;
  // API requests: network-first (if fails, fallback to cache)
  if (req.url.includes('/api/')) {
    event.respondWith(
      fetch(req).then((res) => {
        return res;
      }).catch(() => caches.match(req))
    );
    return;
  }

  // For navigation requests and static assets: cache-first, then network
  event.respondWith(
    caches.match(req).then((cached) => {
      if (cached) {
        // Also update cache in background
        fetch(req).then((res) => {
          if (res && res.ok && res.type !== 'opaque') {
            // Clone before any async operation to avoid "already used" error
            const cloned = res.clone();
            caches.open(CACHE_NAME).then((cache) => cache.put(req, cloned));
          }
        }).catch(() => {});
        return cached;
      }
      return fetch(req).then((res) => {
        // save static responses
        if (res && res.ok && res.type !== 'opaque') {
          // Clone immediately before any async operation
          const cloned = res.clone();
          caches.open(CACHE_NAME).then((cache) => cache.put(req, cloned));
        }
        return res;
      }).catch(() => {
        // fallback to offline page or cached index
        return caches.match('/index.html');
      });
    })
  );
});

/* Minimal offline support: cache core assets on install, cache pages as they are visited. */
var VERSION = 'lop48-__VERSION__';
var CORE = [
  './', './laws/', './offline.html', './manifest.webmanifest',
  './assets/css/main.css?v=__VERSION__', './assets/js/app.js?v=__VERSION__', './assets/js/reader.js?v=__VERSION__', './assets/js/pages.js?v=__VERSION__',
  './assets/fonts/noto-serif-bengali-bengali-400-normal.woff2', './assets/fonts/noto-serif-bengali-bengali-700-normal.woff2',
  './assets/icons/favicon.svg'
];
self.addEventListener('install', function (e) {
  e.waitUntil(caches.open(VERSION).then(function (c) { return c.addAll(CORE); }).then(function () { return self.skipWaiting(); }));
});
self.addEventListener('activate', function (e) {
  e.waitUntil(caches.keys().then(function (keys) {
    return Promise.all(keys.filter(function (k) { return k.indexOf('lop48-') === 0 && k !== VERSION; }).map(function (k) { return caches.delete(k); }));
  }).then(function () { return self.clients.claim(); }));
});
self.addEventListener('fetch', function (e) {
  var req = e.request;
  if (req.method !== 'GET' || new URL(req.url).origin !== location.origin) return;
  if (req.mode === 'navigate') {
    // network first for pages, fall back to cache, then offline page
    e.respondWith(fetch(req).then(function (res) {
      var copy = res.clone(); caches.open(VERSION).then(function (c) { c.put(req, copy); }); return res;
    }).catch(function () {
      return caches.match(req).then(function (r) { return r || caches.match('./offline.html'); });
    }));
    return;
  }
  // cache first for static assets
  e.respondWith(caches.match(req).then(function (r) {
    return r || fetch(req).then(function (res) {
      if (res.ok) { var copy = res.clone(); caches.open(VERSION).then(function (c) { c.put(req, copy); }); }
      return res;
    });
  }));
});

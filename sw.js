// Réseau d'abord (les mises à jour arrivent toutes seules), cache si pas de réseau à la salle.
const V = 'muscu-v14';
const FICHIERS = ['./', 'index.html', 'manifest.json', 'carnet.js', 'course.js', 'icon-haltere-180.png', 'icon-haltere-512.png'];
self.addEventListener('install', e => e.waitUntil(caches.open(V).then(c => c.addAll(FICHIERS)).then(() => self.skipWaiting())));
self.addEventListener('activate', e => e.waitUntil(caches.keys().then(k => Promise.all(k.filter(x => x !== V).map(x => caches.delete(x)))).then(() => self.clients.claim())));
self.addEventListener('fetch', e => {
  if (e.request.method !== 'GET') return;
  e.respondWith(fetch(e.request).then(r => {
    const copie = r.clone(); caches.open(V).then(c => c.put(e.request, copie)); return r;
  }).catch(() => caches.match(e.request)));
});

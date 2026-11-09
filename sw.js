// Garde l'app en cache pour qu'elle s'ouvre sans réseau à la salle.
// Après une modif de index.html, changer V pour forcer la mise à jour.
const V = 'muscu-v1';
const FICHIERS = ['./', 'index.html', 'manifest.json', 'icon-180.png', 'icon-512.png'];
self.addEventListener('install', e => e.waitUntil(caches.open(V).then(c => c.addAll(FICHIERS)).then(() => self.skipWaiting())));
self.addEventListener('activate', e => e.waitUntil(caches.keys().then(k => Promise.all(k.filter(x => x !== V).map(x => caches.delete(x))))));
self.addEventListener('fetch', e => e.respondWith(caches.match(e.request).then(r => r || fetch(e.request))));

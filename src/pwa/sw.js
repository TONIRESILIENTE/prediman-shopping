// sw.js — Service Worker para funcionamento offline
const CACHE_NAME = 'prediman-v1';
const ASSETS = [
  '/pwa/index.html',
  '/pwa/app.js',
  '/pwa/style.css',
  '/pwa/manifest.json',
];

// Instalação: cache dos arquivos essenciais
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll(ASSETS))
  );
});

// Ativação: limpa caches antigos
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) => {
      return Promise.all(
        keys.filter((key) => key !== CACHE_NAME).map((key) => caches.delete(key))
      );
    })
  );
});

// Estratégia: Network First (tenta rede, fallback para cache)
self.addEventListener('fetch', (event) => {
  event.respondWith(
    fetch(event.request)
      .then((response) => {
        // Atualiza cache com resposta fresca
        const clone = response.clone();
        caches.open(CACHE_NAME).then((cache) => cache.put(event.request, clone));
        return response;
      })
      .catch(() => {
        // Offline: serve do cache
        return caches.match(event.request);
      })
  );
});
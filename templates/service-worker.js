
{% load static %}

// templates/service-worker.js

const CACHE_NAME = 'ebd-app-cache-v1';
// Lista de arquivos e URLs essenciais para o funcionamento offline.
const urlsToCache = [
  '/', // A página inicial (roteador de login)
  '/offline/', // Nossa página de fallback
  '{% static "css/custom.css" %}',
  '{% static "js/main.js" %}',
  // Adicione aqui outros arquivos estáticos críticos, se houver.
  'https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css',
  'https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.min.css'
];

// Evento de Instalação: Ocorre quando o service worker é registrado pela primeira vez.
self.addEventListener('install', event => {
  // Espera até que o cache seja aberto e todos os arquivos essenciais sejam adicionados.
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => {
        console.log('Cache aberto');
        return cache.addAll(urlsToCache);
      })
  );
});

// Evento Fetch: Ocorre toda vez que o app faz uma requisição de rede (ex: carregar uma página, imagem, etc.).
self.addEventListener('fetch', event => {
  event.respondWith(
    // 1. Tenta encontrar a resposta no cache.
    caches.match(event.request)
      .then(response => {
        // Se encontrou no cache, retorna a resposta do cache.
        if (response) {
          return response;
        }
        // 2. Se não encontrou no cache, tenta buscar na rede.
        return fetch(event.request)
          .catch(() => {
            // 3. Se a busca na rede falhar (está offline), retorna a página de fallback.
            return caches.match('/offline/');
          });
      })
  );
});
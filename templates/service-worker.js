
{% load static %}

// templates/service-worker.js

const CACHE_NAME = 'ebd-app-cache-v1';
// Lista de arquivos e URLs essenciais para o funcionamento offline.
const urlsToCache = [
  
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
// templates/service-worker.js
// ... (depois do addEventListener('install', ...)) ...

self.addEventListener('fetch', event => {
  // Verifica se é uma requisição de navegação (acessar uma página HTML)
  if (event.request.mode === 'navigate') {
    // Estratégia: Tenta a Rede Primeiro para páginas HTML
    event.respondWith(
      fetch(event.request)
        .then(response => {
          // Se a resposta da rede for válida, retorna ela
          // (Importante: NÃO cacheamos respostas de navegação aqui para evitar problemas com redirects)
          return response;
        })
        .catch(error => {
          // Se a rede falhar, tenta pegar do cache (se já tiver sido cacheada antes)
          console.log('Fetch failed; returning offline page instead.', error);
          return caches.match('/offline/'); // Mostra a página offline
        })
    );
  } else {
    // Para outros tipos de requisição (CSS, JS, imagens), usa Cache First
    event.respondWith(
      caches.match(event.request)
        .then(response => {
          // Retorna do cache se encontrar, senão busca na rede
          // (Opcional: Poderíamos adicionar o item ao cache aqui se não encontrado,
          // mas vamos manter simples por enquanto)
          return response || fetch(event.request);
        })
        .catch(() => {
          // Se TUDO falhar (cache miss E network error), pode opcionalmente
          // retornar um placeholder genérico, mas para assets geralmente não é necessário.
          // Para simplificar, não faremos nada aqui.
        })
    );
  }
});

// Opcional, mas recomendado: Adicionar um listener 'activate' para limpar caches antigos
self.addEventListener('activate', event => {
  console.log('Service Worker ativando.');
  // Remove caches antigos que não sejam o atual
  event.waitUntil(
    caches.keys().then(cacheNames => {
      return Promise.all(
        cacheNames.filter(cacheName => {
          // Retorna true se você quiser deletar este cache antigo
          return cacheName.startsWith('ebd-app-cache-') && cacheName !== CACHE_NAME;
        }).map(cacheName => {
          return caches.delete(cacheName);
        })
      );
    })
  );
  // Garante que o SW ativo controle a página imediatamente em futuras visitas
  return self.clients.claim();
});
const CACHE_NAME = 'ilac-takip-v2';
const urlsToCache = [
  '/',
  '/static/manifest.json',
  '/static/icon-192.png',
  '/static/icon-512.png',
  'https://cdn.jsdelivr.net/npm/bootstrap@5.3.1/dist/css/bootstrap.min.css',
  'https://cdn.jsdelivr.net/npm/bootstrap@5.3.1/dist/js/bootstrap.bundle.min.js',
  'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css'
];

// Install event - Cache dosyaları
self.addEventListener('install', event => {
  console.log('Service Worker: Installing...');
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => {
        console.log('Service Worker: Caching app shell and content');
        return cache.addAll(urlsToCache);
      })
      .then(() => self.skipWaiting())
  );
});

// Activate event - Eski cache'leri temizle
self.addEventListener('activate', event => {
  console.log('Service Worker: Activating...');
  event.waitUntil(
    caches.keys().then(cacheNames => {
      return Promise.all(
        cacheNames.map(cacheName => {
          if (cacheName !== CACHE_NAME) {
            console.log('Service Worker: Deleting old cache', cacheName);
            return caches.delete(cacheName);
          }
        })
      );
    }).then(() => self.clients.claim())
  );
});

// Fetch event - Offline destek
self.addEventListener('fetch', event => {
  event.respondWith(
    caches.match(event.request)
      .then(response => {
        // Cache'de varsa döndür
        if (response) {
          return response;
        }

        // Cache'de yoksa network'den al
        return fetch(event.request).then(response => {
          // Sadece başarılı GET request'leri cache'le
          if (!response || response.status !== 200 || response.type !== 'basic' ||
              event.request.method !== 'GET') {
            return response;
          }

          const responseToCache = response.clone();

          caches.open(CACHE_NAME)
            .then(cache => {
              cache.put(event.request, responseToCache);
            });

          return response;
        }).catch(error => {
          console.log('Network request failed:', error);
          // Offline fallback sayfası olabilir
          return caches.match('/offline.html');
        });
      })
  );
});

// Background sync - Offline verileri senkronize et
self.addEventListener('sync', event => {
  if (event.tag === 'background-sync') {
    event.waitUntil(doBackgroundSync());
  }
});

function doBackgroundSync() {
  return new Promise((resolve, reject) => {
    // Offline veri kontrolü ve backend'e gönderme
    console.log('Background sync çalışıyor...');
    resolve();
  });
}

// Push notifications - Web Push API
self.addEventListener('push', event => {
  console.log('Push notification received:', event);

  let data = {};
  if (event.data) {
    data = event.data.json();
  }

  const options = {
    body: data.body || 'İlaç zamanınız geldi!',
    icon: '/static/icon-192.png',
    badge: '/static/icon-192.png',
    vibrate: [200, 100, 200, 100, 200],
    requireInteraction: true,
    data: data,
    actions: [
      {
        action: 'take',
        title: '✅ Aldım',
        icon: '/static/check-icon.png'
      },
      {
        action: 'snooze',
        title: '⏰ 15 Dakika',
        icon: '/static/snooze-icon.png'
      }
    ]
  };

  event.waitUntil(
    self.registration.showNotification(data.title || '💊 İlaç Takip', options)
  );
});

// Notification click handling
self.addEventListener('notificationclick', event => {
  console.log('Notification clicked:', event.action);

  event.notification.close();

  if (event.action === 'take') {
    // İlaç alımını işaretle
    event.waitUntil(
      clients.openWindow('/?action=take&medication=' + (event.notification.data.id || ''))
    );
  } else if (event.action === 'snooze') {
    // 15 dakika ertele
    event.waitUntil(
      clients.openWindow('/?action=snooze&medication=' + (event.notification.data.id || ''))
    );
  } else {
    // Normal açılış
    event.waitUntil(
      clients.openWindow('/')
    );
  }
});

// Message event - Frontend'den mesajlar
self.addEventListener('message', event => {
  console.log('Message received:', event.data);

  if (event.data && event.data.type === 'SKIP_WAITING') {
    self.skipWaiting();
  }
});

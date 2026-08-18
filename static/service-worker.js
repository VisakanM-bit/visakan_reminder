const CACHE_NAME = "bday-reminder-v1";

const APP_SHELL = [
    "/",
    "/static/css/style.css",
    "/static/js/app.js",
    "/static/js/chat.js",
    "/static/js/pwa.js"
];

self.addEventListener("install", function (event) {
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then(function (cache) {
                return cache.addAll(APP_SHELL);
            })
            .then(function () {
                return self.skipWaiting();
            })
    );
});

self.addEventListener("activate", function (event) {
    event.waitUntil(
        caches.keys()
            .then(function (cacheNames) {
                return Promise.all(
                    cacheNames
                        .filter(function (name) {
                            return name !== CACHE_NAME;
                        })
                        .map(function (name) {
                            return caches.delete(name);
                        })
                );
            })
            .then(function () {
                return self.clients.claim();
            })
    );
});

self.addEventListener("fetch", function (event) {
    if (event.request.method !== "GET") {
        return;
    }

    event.respondWith(
        fetch(event.request)
            .then(function (response) {
                if (response && response.status === 200) {
                    const responseClone = response.clone();

                    caches.open(CACHE_NAME).then(function (cache) {
                        cache.put(event.request, responseClone);
                    });
                }

                return response;
            })
            .catch(function () {
                return caches.match(event.request)
                    .then(function (cachedResponse) {
                        return cachedResponse || new Response(
                            "Offline",
                            {
                                status: 503,
                                headers: {
                                    "Content-Type": "text/plain"
                                }
                            }
                        );
                    });
            })
    );
});
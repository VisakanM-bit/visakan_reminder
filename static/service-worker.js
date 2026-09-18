// ============================================================
// BDAY REMINDER
// SERVICE WORKER
// ============================================================

const CACHE_NAME = "bday-reminder-v2";

const APP_SHELL = [
    "/",
    "/static/css/style.css",
    "/static/js/app.js",
    "/static/js/chat.js",
    "/static/js/pwa.js"
];


// ============================================================
// INSTALL
// ============================================================

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


// ============================================================
// ACTIVATE
// ============================================================

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


// ============================================================
// FETCH
// ============================================================

self.addEventListener("fetch", function (event) {

    if (event.request.method !== "GET") {

        return;

    }

    event.respondWith(

        fetch(event.request)

            .then(function (response) {

                if (
                    response &&
                    response.status === 200
                ) {

                    const responseClone =
                        response.clone();

                    caches.open(CACHE_NAME)
                        .then(function (cache) {

                            cache.put(
                                event.request,
                                responseClone
                            );

                        });

                }

                return response;

            })

            .catch(function () {

                return caches.match(
                    event.request
                )

                    .then(function (cachedResponse) {

                        return cachedResponse ||
                            new Response(
                                "Offline",
                                {
                                    status: 503,
                                    headers: {
                                        "Content-Type":
                                            "text/plain"
                                    }
                                }
                            );

                    });

            })

    );

});


// ============================================================
// PUSH NOTIFICATION
// ============================================================
// This receives the notification from the Flask server even
// when the PWA/page is not open.
// ============================================================

self.addEventListener(
    "push",
    function (event) {

        let data = {};

        try {

            if (event.data) {

                data = event.data.json();

            }

        } catch (error) {

            console.error(
                "Push notification data error:",
                error
            );

            data = {
                title: "Birthday Reminder",
                body: "You have a reminder."
            };

        }


        const title =
            data.title ||
            "Birthday Reminder";

        const options = {

            body:
                data.body ||
                "You have a reminder.",

            icon:
                "/static/icons/icon-192.png",

            badge:
                "/static/icons/icon-192.png",

            tag:
                data.alarm_id
                    ? `bday-reminder-${data.alarm_id}`
                    : "bday-reminder",

            renotify: true,

            requireInteraction: true,

            data: {

                url:
                    data.url ||
                    "/",

                alarm_id:
                    data.alarm_id ||
                    null,

                type:
                    data.type ||
                    null,

                source_id:
                    data.source_id ||
                    null

            }

        };


        event.waitUntil(

            self.registration.showNotification(
                title,
                options
            )

        );

    }
);


// ============================================================
// NOTIFICATION CLICK
// ============================================================

self.addEventListener(
    "notificationclick",
    function (event) {

        event.notification.close();


        const notificationData =
            event.notification.data || {};

        const targetUrl =
            notificationData.url || "/";


        event.waitUntil(

            clients.matchAll({

                type: "window",
                includeUncontrolled: true

            })

                .then(function (clientList) {

                    // ------------------------------------------------
                    // If the PWA is already open, focus it.
                    // ------------------------------------------------

                    for (
                        const client of clientList
                    ) {

                        if (
                            "focus" in client &&
                            client.url.includes(
                                self.location.origin
                            )
                        ) {

                            return client.focus();

                        }

                    }


                    // ------------------------------------------------
                    // Otherwise open the PWA.
                    // ------------------------------------------------

                    if (
                        clients.openWindow
                    ) {

                        return clients.openWindow(
                            targetUrl
                        );

                    }

                })

        );

    }
);

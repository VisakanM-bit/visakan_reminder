// ============================================================
// BDAY REMINDER
// PWA + WEB PUSH REGISTRATION
// ============================================================

(function () {

    "use strict";


    // ========================================================
    // CHECK SUPPORT
    // ========================================================

    if (!("serviceWorker" in navigator)) {

        console.log(
            "PWA: Service workers are not supported."
        );

        return;
    }


    // ========================================================
    // CONVERT VAPID PUBLIC KEY
    // ========================================================

    function urlBase64ToUint8Array(
        base64String
    ) {

        const padding =
            "=".repeat(
                (4 - base64String.length % 4) % 4
            );

        const base64 =
            (
                base64String +
                padding
            )
                .replace(/-/g, "+")
                .replace(/_/g, "/");

        const rawData =
            window.atob(base64);

        const outputArray =
            new Uint8Array(
                rawData.length
            );

        for (
            let i = 0;
            i < rawData.length;
            ++i
        ) {

            outputArray[i] =
                rawData.charCodeAt(i);

        }

        return outputArray;
    }


    // ========================================================
    // GET VAPID PUBLIC KEY
    // ========================================================

    async function getVapidPublicKey() {

        const response =
            await fetch(
                "/api/push/vapid-public-key"
            );

        if (!response.ok) {

            throw new Error(
                "Unable to get VAPID public key."
            );

        }

        const data =
            await response.json();

        if (
            !data.success ||
            !data.publicKey
        ) {

            throw new Error(
                "VAPID public key is not configured."
            );

        }

        return data.publicKey;
    }


    // ========================================================
    // SAVE PUSH SUBSCRIPTION
    // ========================================================

    async function savePushSubscription(
        subscription
    ) {

        const subscriptionJson =
            subscription.toJSON();

        const response =
            await fetch(
                "/api/push/subscribe",
                {
                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body:
                        JSON.stringify(
                            subscriptionJson
                        )
                }
            );

        if (!response.ok) {

            throw new Error(
                "Unable to save push subscription."
            );

        }

        const data =
            await response.json();

        if (!data.success) {

            throw new Error(
                data.error ||
                "Push subscription failed."
            );

        }

        console.log(
            "PWA: Push subscription saved successfully."
        );
    }


    // ========================================================
    // ENABLE WEB PUSH
    // ========================================================

    async function enablePushNotifications(
        registration
    ) {

        // ----------------------------------------------------
        // Browser notification support
        // ----------------------------------------------------

        if (!("Notification" in window)) {

            console.log(
                "PWA: Browser notifications are not supported."
            );

            return;
        }


        // ----------------------------------------------------
        // Request permission
        // ----------------------------------------------------

        let permission =
            Notification.permission;


        if (permission === "default") {

            permission =
                await Notification.requestPermission();

        }


        if (permission !== "granted") {

            console.log(
                "PWA: Notification permission:",
                permission
            );

            return;
        }


        // ----------------------------------------------------
        // Check Push API
        // ----------------------------------------------------

        if (
            !registration.pushManager
        ) {

            console.log(
                "PWA: Push API is not supported."
            );

            return;
        }


        // ----------------------------------------------------
        // Get VAPID public key
        // ----------------------------------------------------

        const publicKey =
            await getVapidPublicKey();


        // ----------------------------------------------------
        // Check existing subscription
        // ----------------------------------------------------

        let subscription =
            await registration.pushManager.getSubscription();


        // ----------------------------------------------------
        // Create subscription if needed
        // ----------------------------------------------------

        if (!subscription) {

            subscription =
                await registration.pushManager.subscribe({

                    userVisibleOnly: true,

                    applicationServerKey:
                        urlBase64ToUint8Array(
                            publicKey
                        )

                });

        }


        // ----------------------------------------------------
        // Send subscription to Flask
        // ----------------------------------------------------

        await savePushSubscription(
            subscription
        );

    }


    // ========================================================
    // REGISTER SERVICE WORKER
    // ========================================================

    window.addEventListener(
        "load",
        async function () {

            try {

                const registration =
                    await navigator.serviceWorker.register(
                        "/static/service-worker.js",
                        {
                            scope: "/"
                        }
                    );


                console.log(
                    "PWA: Service worker registered successfully.",
                    registration.scope
                );


                // ------------------------------------------------
                // Wait until service worker is ready
                // ------------------------------------------------

                const readyRegistration =
                    await navigator.serviceWorker.ready;


                console.log(
                    "PWA: Service worker is ready."
                );


                // ------------------------------------------------
                // Enable Web Push
                // ------------------------------------------------

                await enablePushNotifications(
                    readyRegistration
                );


            } catch (error) {

                console.error(
                    "PWA: Service worker / push registration failed:",
                    error
                );

            }

        }
    );

})();

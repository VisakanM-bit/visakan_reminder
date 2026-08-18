(function () {
    "use strict";

    if (!("serviceWorker" in navigator)) {
        console.log("PWA: Service workers are not supported.");
        return;
    }

    window.addEventListener("load", function () {
        navigator.serviceWorker
            .register("/static/service-worker.js", {
                scope: "/"
            })
            .then(function (registration) {
                console.log(
                    "PWA: Service worker registered successfully.",
                    registration.scope
                );
            })
            .catch(function (error) {
                console.error(
                    "PWA: Service worker registration failed:",
                    error
                );
            });
    });
})();
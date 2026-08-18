"use strict";

/*
=============================================================
BDAY REMINDER
PERSISTENT NOTIFICATION / ALARM ENGINE

FLOW:

DATABASE
   ↓
/api/notifications/due
   ↓
BACKEND DECIDES DUE / 5-MINUTE REPEAT
   ↓
APP.JS
   ↓
IN-APP ALARM
   ↓
BROWSER NOTIFICATION
   ↓
SOUND
   ↓
STOP
   ↓
DATABASE

IMPORTANT:

The frontend polling interval is NOT the alarm interval.

Frontend:
    polls every 20 seconds

Backend:
    decides whether another notification
    is allowed after 5 minutes.
=============================================================
*/


(function () {

    const POLL_INTERVAL =
        20 * 1000;


    let pollingTimer =
        null;


    let audioContext =
        null;


    let audioUnlocked =
        false;


    const countdownShown =
        new Set();


    /* =========================================================
       NOTIFICATION CONTAINER
    ========================================================= */

    function createNotificationContainer() {

        let container =
            document.getElementById(
                "reminder-notification-container"
            );


        if (!container) {

            container =
                document.createElement(
                    "div"
                );


            container.id =
                "reminder-notification-container";


            document.body.appendChild(
                container
            );

        }


        return container;

    }


    /* =========================================================
       HTML SAFETY
    ========================================================= */

    function escapeHtml(
        value
    ) {

        const div =
            document.createElement(
                "div"
            );


        div.textContent =
            value == null
                ? ""
                : String(value);


        return div.innerHTML;

    }


    /* =========================================================
       REMOVE
    ========================================================= */

    function removeNotification(
        notification
    ) {

        if (!notification) {

            return;

        }


        notification.classList.remove(
            "show"
        );


        window.setTimeout(
            function () {

                if (
                    notification.parentElement
                ) {

                    notification.remove();

                }

            },
            300
        );

    }


    /* =========================================================
       BROWSER PERMISSION
    ========================================================= */

    async function requestBrowserPermission() {

        if (
            !("Notification" in window)
        ) {

            return;

        }


        if (
            Notification.permission !==
            "default"
        ) {

            return;

        }


        try {

            await Notification.requestPermission();

        }

        catch (error) {

            console.warn(
                "Browser notification permission failed:",
                error
            );

        }

    }


    /* =========================================================
       AUDIO INITIALIZATION
    ========================================================= */

    function unlockAudio() {

        if (audioUnlocked) {

            return;

        }


        const AudioContextClass =
            window.AudioContext ||
            window.webkitAudioContext;


        if (!AudioContextClass) {

            return;

        }


        try {

            audioContext =
                audioContext ||
                new AudioContextClass();


            if (
                audioContext.state ===
                "suspended"
            ) {

                audioContext
                    .resume()
                    .catch(
                        function () {}
                    );

            }


            audioUnlocked =
                true;

        }

        catch (error) {

            console.warn(
                "Audio initialization failed:",
                error
            );

        }

    }


    /* =========================================================
       ALARM SOUND
    ========================================================= */

    function playAlarmSound() {

        if (
            !audioContext ||
            !audioUnlocked
        ) {

            return;

        }


        try {

            const now =
                audioContext.currentTime;


            const oscillator =
                audioContext.createOscillator();


            const gain =
                audioContext.createGain();


            oscillator.type =
                "sine";


            oscillator.frequency.setValueAtTime(
                880,
                now
            );


            oscillator.frequency.setValueAtTime(
                660,
                now + 0.12
            );


            gain.gain.setValueAtTime(
                0.0001,
                now
            );


            gain.gain.exponentialRampToValueAtTime(
                0.18,
                now + 0.02
            );


            gain.gain.exponentialRampToValueAtTime(
                0.0001,
                now + 0.55
            );


            oscillator.connect(
                gain
            );


            gain.connect(
                audioContext.destination
            );


            oscillator.start(
                now
            );


            oscillator.stop(
                now + 0.6
            );

        }

        catch (error) {

            console.warn(
                "Alarm sound blocked:",
                error
            );

        }

    }


    /* =========================================================
       FORMAT TIME
    ========================================================= */

    function formatTime(
        value
    ) {

        if (!value) {

            return "";

        }


        const parts =
            String(value).split(":");


        let hour =
            parseInt(
                parts[0],
                10
            );


        const minute =
            parts[1] || "00";


        if (
            Number.isNaN(hour)
        ) {

            return String(value);

        }


        const period =
            hour >= 12
                ? "PM"
                : "AM";


        hour =
            hour % 12 || 12;


        return (
            hour +
            ":" +
            minute +
            " " +
            period
        );

    }


    /* =========================================================
       BROWSER NOTIFICATION
    ========================================================= */

    function showBrowserNotification(
        item
    ) {

        if (
            !("Notification" in window)
        ) {

            return;

        }


        if (
            Notification.permission !==
            "granted"
        ) {

            return;

        }


        const isBirthday =
            item.type ===
            "birthday";


        const title =
            isBirthday
                ? "🎂 Birthday Today"
                : "🔔 Reminder Due";


        const body =
            isBirthday
                ? item.message
                : (
                    `${item.title} — ` +
                    `Scheduled: ` +
                    `${formatTime(item.time)}`
                );


        try {

            new Notification(
                title,
                {
                    body:
                        body,

                    tag:
                        `bday-reminder-${item.id}`
                }
            );

        }

        catch (error) {

            console.warn(
                "Browser notification failed:",
                error
            );

        }

    }


    /* =========================================================
       STOP BACKEND ALARM
    ========================================================= */

    async function stopAlarm(
        alarmId,
        notification
    ) {

        const button =
            notification.querySelector(
                ".floating-reminder-done"
            );


        if (button) {

            button.disabled =
                true;


            button.textContent =
                "Stopping...";

        }


        try {

            const response =
                await fetch(
                    `/api/notifications/${alarmId}/stop`,
                    {
                        method:
                            "POST",

                        headers: {

                            "Accept":
                                "application/json",

                            "Content-Type":
                                "application/json"

                        },

                        credentials:
                            "same-origin"

                    }
                );


            if (
                response.status ===
                401
            ) {

                window.location.href =
                    "/login";

                return;

            }


            const data =
                await response.json();


            if (
                !response.ok ||
                !data.success
            ) {

                throw new Error(
                    data.error ||
                    "Unable to stop alarm."
                );

            }


            removeNotification(
                notification
            );

        }

        catch (error) {

            console.error(
                "Stop alarm failed:",
                error
            );


            if (button) {

                button.disabled =
                    false;


                button.textContent =
                    "⛔ STOP";

            }

        }

    }


    /* =========================================================
       SHOW ACTIVE ALARM
    ========================================================= */

    function showAlarm(
        item
    ) {

        const container =
            createNotificationContainer();


        const notification =
            document.createElement(
                "div"
            );


        notification.className =
            "floating-reminder";


        const isBirthday =
            item.type ===
            "birthday";


        const title =
            isBirthday
                ? "🎂 Birthday Today"
                : "🔔 Reminder Due";


        const name =
            isBirthday
                ? item.name
                : item.title;


        const message =
            item.message;


        let schedule;


        if (isBirthday) {

            schedule =
                `
                    📅
                    ${escapeHtml(
                        item.birthday
                    )}
                `;

        }

        else {

            schedule =
                `
                    📅
                    ${escapeHtml(
                        item.date
                    )}

                    <br>

                    🕐
                    ${escapeHtml(
                        formatTime(
                            item.time
                        )
                    )}

                    ${
                        item.place
                            ?
                            `
                                <br>
                                📍
                                ${escapeHtml(
                                    item.place
                                )}
                            `
                            :
                            ""
                    }
                `;

        }


        notification.innerHTML =
            `

            <div
                class="floating-reminder-header"
            >

                <div
                    class="floating-reminder-title"
                >
                    ${title}
                </div>


                <button
                    type="button"
                    class="floating-reminder-close"
                    aria-label="Close notification"
                >
                    ×
                </button>

            </div>


            <div
                class="floating-reminder-content"
            >

                <h3>
                    ${escapeHtml(
                        name
                    )}
                </h3>


                <p>
                    ${escapeHtml(
                        message
                    )}
                </p>


                <div
                    class="floating-reminder-time"
                >
                    ${schedule}
                </div>

            </div>


            <div
                class="floating-reminder-actions"
            >

                <button
                    type="button"
                    class="floating-reminder-done"
                >
                    ⛔ STOP
                </button>

            </div>

            `;


        container.appendChild(
            notification
        );


        /* -----------------------------------------------------
           CLOSE
        ----------------------------------------------------- */

        const closeButton =
            notification.querySelector(
                ".floating-reminder-close"
            );


        if (closeButton) {

            closeButton.addEventListener(
                "click",
                function () {

                    removeNotification(
                        notification
                    );

                }
            );

        }


        /* -----------------------------------------------------
           STOP
        ----------------------------------------------------- */

        const stopButton =
            notification.querySelector(
                ".floating-reminder-done"
            );


        if (stopButton) {

            stopButton.addEventListener(
                "click",
                function () {

                    stopAlarm(
                        item.id,
                        notification
                    );

                }
            );

        }


        window.setTimeout(
            function () {

                notification.classList.add(
                    "show"
                );

            },
            50
        );


        playAlarmSound();


        showBrowserNotification(
            item
        );

    }


    /* =========================================================
       CHECK PERSISTENT ALARMS
    ========================================================= */

    async function checkNotifications() {

        try {

            const response =
                await fetch(
                    "/api/notifications/due",
                    {
                        method:
                            "GET",

                        headers: {

                            "Accept":
                                "application/json"

                        },

                        credentials:
                            "same-origin",

                        cache:
                            "no-store"

                    }
                );


            if (
                response.status ===
                401
            ) {

                return;

            }


            if (!response.ok) {

                return;

            }


            const data =
                await response.json();


            if (
                !data.success ||
                !Array.isArray(
                    data.notifications
                )
            ) {

                return;

            }


            data.notifications.forEach(
                function (item) {

                    showAlarm(
                        item
                    );

                }
            );

        }

        catch (error) {

            console.error(
                "Notification check failed:",
                error
            );

        }

    }


    /* =========================================================
       BIRTHDAY COUNTDOWN
       
       Preserves the existing:
       5 days → 4 → 3 → 2 → 1 → today
       
       This is NOT the persistent alarm.
    ========================================================= */

    async function checkBirthdayCountdown() {

        try {

            const response =
                await fetch(
                    "/api/upcoming-birthdays",
                    {
                        method:
                            "GET",

                        headers: {

                            "Accept":
                                "application/json"

                        },

                        credentials:
                            "same-origin",

                        cache:
                            "no-store"

                    }
                );


            if (
                response.status ===
                401 ||
                !response.ok
            ) {

                return;

            }


            const data =
                await response.json();


            if (
                !data.success ||
                !Array.isArray(
                    data.birthdays
                )
            ) {

                return;

            }


            const countdownItems =
                data.birthdays.filter(
                    function (birthday) {

                        const days =
                            Number(
                                birthday.days_remaining
                            );


                        return (
                            days >= 1 &&
                            days <= 5
                        );

                    }
                );


            if (
                !countdownItems.length
            ) {

                return;

            }


            const container =
                createNotificationContainer();


            countdownItems.forEach(
                function (birthday) {

                    const key =
                        `birthday-countdown-` +
                        `${birthday.id}-` +
                        `${birthday.date}`;


                    if (
                        countdownShown.has(
                            key
                        )
                    ) {

                        return;

                    }


                    countdownShown.add(
                        key
                    );


                    const notification =
                        document.createElement(
                            "div"
                        );


                    notification.className =
                        "floating-reminder";


                    notification.innerHTML =
                        `

                        <div
                            class="floating-reminder-header"
                        >

                            <div
                                class="floating-reminder-title"
                            >
                                🎂 Birthday Reminder
                            </div>


                            <button
                                type="button"
                                class="floating-reminder-close"
                                aria-label="Close birthday reminder"
                            >
                                ×
                            </button>

                        </div>


                        <div
                            class="floating-reminder-content"
                        >

                            <h3>
                                🎉
                                ${escapeHtml(
                                    birthday.name
                                )}
                            </h3>


                            <p>
                                ${escapeHtml(
                                    birthday.message
                                )}
                            </p>

                        </div>

                        `;


                    container.appendChild(
                        notification
                    );


                    const closeButton =
                        notification.querySelector(
                            ".floating-reminder-close"
                        );


                    if (closeButton) {

                        closeButton.addEventListener(
                            "click",
                            function () {

                                removeNotification(
                                    notification
                                );

                            }
                        );

                    }


                    window.setTimeout(
                        function () {

                            notification.classList.add(
                                "show"
                            );

                        },
                        50
                    );

                }
            );

        }

        catch (error) {

            console.error(
                "Birthday countdown failed:",
                error
            );

        }

    }


    /* =========================================================
       INITIALIZE
    ========================================================= */

    function initialize() {

        if (pollingTimer) {

            return;

        }


        /* -----------------------------------------------------
           Browser interaction
        ----------------------------------------------------- */

        function firstInteraction() {

            unlockAudio();

            requestBrowserPermission();

        }


        document.addEventListener(
            "pointerdown",
            firstInteraction,
            {
                once:
                    true
            }
        );


        document.addEventListener(
            "keydown",
            firstInteraction,
            {
                once:
                    true
            }
        );


        /* -----------------------------------------------------
           Immediate checks
        ----------------------------------------------------- */

        checkNotifications();

        checkBirthdayCountdown();


        /* -----------------------------------------------------
           Persistent alarm polling
           
           20 seconds is only for responsiveness.
           The backend controls the 5-minute repeat.
        ----------------------------------------------------- */

        pollingTimer =
            window.setInterval(
                checkNotifications,
                POLL_INTERVAL
            );


        /* -----------------------------------------------------
           Birthday countdown
        ----------------------------------------------------- */

        window.setInterval(
            checkBirthdayCountdown,
            60000
        );

    }


    document.addEventListener(
        "DOMContentLoaded",
        initialize,
        {
            once:
                true
        }
    );

})();
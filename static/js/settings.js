"use strict";

/*
===========================================================
BDAY REMINDER
SETTINGS ENGINE
===========================================================
*/


document.addEventListener(
    "DOMContentLoaded",
    function () {


        /* =================================================
           STORAGE
        ================================================= */

        const STORAGE_PREFIX =
            "bday-reminder-setting-";


        function saveSetting(
            key,
            value
        ) {

            localStorage.setItem(
                STORAGE_PREFIX + key,
                JSON.stringify(value)
            );

        }


        function getSetting(
            key,
            defaultValue
        ) {

            const value =
                localStorage.getItem(
                    STORAGE_PREFIX + key
                );


            if (
                value === null
            ) {

                return defaultValue;

            }


            try {

                return JSON.parse(
                    value
                );

            }

            catch {

                return defaultValue;

            }

        }


        /* =================================================
           SECTIONS
        ================================================= */

        const sections =
            document.querySelectorAll(
                ".settings-section"
            );


        sections.forEach(
            function (section) {

                const header =
                    section.querySelector(
                        ".settings-section-header"
                    );


                if (!header) {
                    return;
                }


                header.addEventListener(
                    "click",
                    function () {

                        section.classList.toggle(
                            "open"
                        );

                    }
                );

            }
        );


        /* =================================================
           ELEMENTS
        ================================================= */

        const reminderNotifications =
            document.getElementById(
                "reminder-notifications"
            );


        const birthdayNotifications =
            document.getElementById(
                "birthday-notifications"
            );


        const browserNotifications =
            document.getElementById(
                "browser-notifications"
            );


        const birthdayAlertDays =
            document.getElementById(
                "birthday-alert-days"
            );


        const birthdayDayAlert =
            document.getElementById(
                "birthday-day-alert"
            );


        const showCompleted =
            document.getElementById(
                "show-completed"
            );


        const autoComplete =
            document.getElementById(
                "auto-complete"
            );


        const appearanceTheme =
            document.getElementById(
                "appearance-theme"
            );


        const autoBackground =
            document.getElementById(
                "auto-background"
            );


        const assistantEnabled =
            document.getElementById(
                "assistant-enabled"
            );


        const assistantConfirmation =
            document.getElementById(
                "assistant-confirmation"
            );


        /* =================================================
           LOAD SETTINGS
        ================================================= */

        function loadSettings() {


            if (reminderNotifications) {

                reminderNotifications.checked =
                    getSetting(
                        "reminderNotifications",
                        true
                    );

            }


            if (birthdayNotifications) {

                birthdayNotifications.checked =
                    getSetting(
                        "birthdayNotifications",
                        true
                    );

            }


            if (browserNotifications) {

                browserNotifications.checked =
                    getSetting(
                        "browserNotifications",
                        true
                    );

            }


            if (birthdayAlertDays) {

                birthdayAlertDays.value =
                    String(
                        getSetting(
                            "birthdayAlertDays",
                            5
                        )
                    );

            }


            if (birthdayDayAlert) {

                birthdayDayAlert.checked =
                    getSetting(
                        "birthdayDayAlert",
                        true
                    );

            }


            if (showCompleted) {

                showCompleted.checked =
                    getSetting(
                        "showCompleted",
                        false
                    );

            }


            if (autoComplete) {

                autoComplete.checked =
                    getSetting(
                        "autoComplete",
                        false
                    );

            }


            if (appearanceTheme) {

                appearanceTheme.value =
                    getSetting(
                        "appearanceTheme",
                        "light"
                    );

            }


            if (autoBackground) {

                autoBackground.checked =
                    getSetting(
                        "autoBackground",
                        true
                    );

            }


            if (assistantEnabled) {

                assistantEnabled.checked =
                    getSetting(
                        "assistantEnabled",
                        true
                    );

            }


            if (assistantConfirmation) {

                assistantConfirmation.checked =
                    getSetting(
                        "assistantConfirmation",
                        true
                    );

            }

        }


        loadSettings();


        /* =================================================
           SAVE CHECKBOX
        ================================================= */

        function bindCheckbox(
            element,
            key
        ) {

            if (!element) {
                return;
            }


            element.addEventListener(
                "change",
                function () {

                    saveSetting(
                        key,
                        element.checked
                    );


                    showSavedMessage();

                }
            );

        }


        bindCheckbox(
            reminderNotifications,
            "reminderNotifications"
        );


        bindCheckbox(
            birthdayNotifications,
            "birthdayNotifications"
        );


        bindCheckbox(
            browserNotifications,
            "browserNotifications"
        );


        bindCheckbox(
            birthdayDayAlert,
            "birthdayDayAlert"
        );


        bindCheckbox(
            showCompleted,
            "showCompleted"
        );


        bindCheckbox(
            autoComplete,
            "autoComplete"
        );


        bindCheckbox(
            autoBackground,
            "autoBackground"
        );


        bindCheckbox(
            assistantEnabled,
            "assistantEnabled"
        );


        bindCheckbox(
            assistantConfirmation,
            "assistantConfirmation"
        );


        /* =================================================
           BIRTHDAY DAYS
        ================================================= */

        if (
            birthdayAlertDays
        ) {

            birthdayAlertDays.addEventListener(
                "change",
                function () {

                    saveSetting(
                        "birthdayAlertDays",
                        Number(
                            birthdayAlertDays.value
                        )
                    );


                    showSavedMessage();

                }
            );

        }


        /* =================================================
           THEME
        ================================================= */

        if (
            appearanceTheme
        ) {

            appearanceTheme.addEventListener(
                "change",
                function () {

                    const theme =
                        appearanceTheme.value;


                    saveSetting(
                        "appearanceTheme",
                        theme
                    );


                    if (
                        theme === "dark"
                    ) {

                        document.body.classList.add(
                            "dark"
                        );

                        localStorage.setItem(
                            "bday-reminder-theme",
                            "dark"
                        );

                    }

                    else {

                        document.body.classList.remove(
                            "dark"
                        );

                        localStorage.setItem(
                            "bday-reminder-theme",
                            "light"
                        );

                    }


                    const themeButton =
                        document.getElementById(
                            "theme-toggle"
                        );


                    if (themeButton) {

                        themeButton.textContent =
                            theme === "dark"
                                ? "☀️"
                                : "🌙";

                    }


                    showSavedMessage();

                }
            );

        }


        /* =================================================
           THEME BUTTON
        ================================================= */

        const themeToggle =
            document.getElementById(
                "theme-toggle"
            );


        if (themeToggle) {

            themeToggle.addEventListener(
                "click",
                function () {

                    document.body.classList.toggle(
                        "dark"
                    );


                    const isDark =
                        document.body.classList.contains(
                            "dark"
                        );


                    const theme =
                        isDark
                            ? "dark"
                            : "light";


                    localStorage.setItem(
                        "bday-reminder-theme",
                        theme
                    );


                    saveSetting(
                        "appearanceTheme",
                        theme
                    );


                    if (
                        appearanceTheme
                    ) {

                        appearanceTheme.value =
                            theme;

                    }


                    themeToggle.textContent =
                        isDark
                            ? "☀️"
                            : "🌙";

                }
            );

        }


        /* =================================================
           CLEAR COMPLETED
        ================================================= */

        const clearCompleted =
            document.getElementById(
                "clear-completed"
            );


        if (clearCompleted) {

            clearCompleted.addEventListener(
                "click",
                async function () {

                    const confirmed =
                        confirm(
                            "Clear all completed reminders?"
                        );


                    if (!confirmed) {

                        return;

                    }


                    try {

                        const response =
                            await fetch(
                                "/api/reminders/clear-completed",
                                {

                                    method:
                                        "POST",

                                    headers: {

                                        "Content-Type":
                                            "application/json"

                                    },

                                    credentials:
                                        "same-origin"

                                }
                            );


                        if (
                            response.ok
                        ) {

                            showSavedMessage(
                                "Completed reminders cleared."
                            );

                        }

                        else {

                            alert(
                                "Unable to clear completed reminders."
                            );

                        }

                    }

                    catch (error) {

                        console.error(
                            error
                        );

                        alert(
                            "Unable to connect to the server."
                        );

                    }

                }
            );

        }


        /* =================================================
           SAVED MESSAGE
        ================================================= */

        function showSavedMessage(
            text = "Settings saved"
        ) {

            let message =
                document.getElementById(
                    "settings-saved-message"
                );


            if (!message) {

                message =
                    document.createElement(
                        "div"
                    );

                message.id =
                    "settings-saved-message";

                message.className =
                    "settings-saved-message";


                document.body.appendChild(
                    message
                );

            }


            message.textContent =
                "✓ " + text;


            message.classList.add(
                "show"
            );


            clearTimeout(
                window.settingsSavedTimer
            );


            window.settingsSavedTimer =
                setTimeout(
                    function () {

                        message.classList.remove(
                            "show"
                        );

                    },
                    1800
                );

        }


    }
);
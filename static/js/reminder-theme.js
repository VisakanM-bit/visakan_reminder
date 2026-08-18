/* =========================================================
   BDAY REMINDER
   UNIVERSAL THEME + TIME BACKGROUND ENGINE
   ========================================================= */

"use strict";

document.addEventListener("DOMContentLoaded", function () {

    /* =====================================================
       ELEMENTS
    ===================================================== */

    const background =
        document.querySelector(".background") ||
        document.getElementById("time-background");

    const themeToggle =
        document.getElementById("theme-toggle");

    const periodButtons =
        document.querySelectorAll(
            ".period-button, .time-option"
        );


    /* =====================================================
       STORAGE
    ===================================================== */

    const THEME_KEY =
        "bday-reminder-theme";

    const PERIOD_KEY =
        "bday-reminder-period";


    /* =====================================================
       THEME
    ===================================================== */

    function applyTheme(theme) {

        const dark =
            theme === "dark";

        document.body.classList.toggle(
            "dark",
            dark
        );

        if (themeToggle) {

            themeToggle.textContent =
                dark ? "☀️" : "🌙";

            themeToggle.setAttribute(
                "aria-label",
                dark
                    ? "Switch to light theme"
                    : "Switch to dark theme"
            );

            themeToggle.setAttribute(
                "title",
                dark
                    ? "Switch to light theme"
                    : "Switch to dark theme"
            );

        }

    }


    function loadTheme() {

        const savedTheme =
            localStorage.getItem(
                THEME_KEY
            );

        if (
            savedTheme === "dark"
        ) {

            applyTheme("dark");

        }

        else {

            applyTheme("light");

        }

    }


    if (themeToggle) {

        themeToggle.addEventListener(
            "click",
            function () {

                const isDark =
                    document.body.classList.toggle(
                        "dark"
                    );


                const newTheme =
                    isDark
                        ? "dark"
                        : "light";


                localStorage.setItem(
                    THEME_KEY,
                    newTheme
                );


                applyTheme(
                    newTheme
                );

            }
        );

    }


    /* =====================================================
       TIME PERIOD
       
       05:00 - 11:59  MORNING
       12:00 - 17:59  AFTERNOON
       18:00 - 20:59  EVENING
       21:00 - 04:59  NIGHT
    ===================================================== */

    function getAutomaticPeriod() {

        const hour =
            new Date().getHours();


        if (
            hour >= 5 &&
            hour < 12
        ) {

            return "morning";

        }


        if (
            hour >= 12 &&
            hour < 18
        ) {

            return "afternoon";

        }


        if (
            hour >= 18 &&
            hour < 21
        ) {

            return "evening";

        }


        return "night";

    }


    /* =====================================================
       APPLY PERIOD
    ===================================================== */

    function applyPeriod(period) {

        if (!background) {

            console.warn(
                "Reminder theme: background element not found."
            );

            return;

        }


        const periods = [
            "morning",
            "afternoon",
            "evening",
            "night"
        ];


        /* Remove old classes */

        periods.forEach(
            function (item) {

                document.body.classList.remove(
                    "period-" + item
                );

                background.classList.remove(
                    item
                );

            }
        );


        /* Auto */

        let actualPeriod =
            period;


        if (
            !period ||
            period === "auto"
        ) {

            actualPeriod =
                getAutomaticPeriod();

        }


        /* Safety */

        if (
            !periods.includes(
                actualPeriod
            )
        ) {

            actualPeriod =
                getAutomaticPeriod();

        }


        /* Apply to BODY */

        document.body.classList.add(
            "period-" +
            actualPeriod
        );


        /*
           Also apply directly to
           background for compatibility
           with older CSS.
        */

        background.classList.add(
            actualPeriod
        );


        /* Update buttons */

        periodButtons.forEach(
            function (button) {

                const buttonPeriod =
                    button.dataset.period;


                button.classList.toggle(
                    "active",
                    buttonPeriod ===
                    period
                );

            }
        );

    }


    /* =====================================================
       LOAD SAVED PERIOD
    ===================================================== */

    function loadPeriod() {

        const savedPeriod =
            localStorage.getItem(
                PERIOD_KEY
            );


        const validPeriods = [
            "auto",
            "morning",
            "afternoon",
            "evening",
            "night"
        ];


        if (
            savedPeriod &&
            validPeriods.includes(
                savedPeriod
            )
        ) {

            applyPeriod(
                savedPeriod
            );

        }

        else {

            localStorage.setItem(
                PERIOD_KEY,
                "auto"
            );


            applyPeriod(
                "auto"
            );

        }

    }


    /* =====================================================
       PERIOD BUTTONS
    ===================================================== */

    periodButtons.forEach(
        function (button) {

            button.addEventListener(
                "click",
                function () {

                    const selectedPeriod =
                        button.dataset.period;


                    if (
                        !selectedPeriod
                    ) {

                        return;

                    }


                    localStorage.setItem(
                        PERIOD_KEY,
                        selectedPeriod
                    );


                    applyPeriod(
                        selectedPeriod
                    );

                }
            );

        }
    );


    /* =====================================================
       AUTO REFRESH
    ===================================================== */

    setInterval(
        function () {

            const savedPeriod =
                localStorage.getItem(
                    PERIOD_KEY
                );


            if (
                !savedPeriod ||
                savedPeriod === "auto"
            ) {

                applyPeriod(
                    "auto"
                );

            }

        },
        60 * 1000
    );


    /* =====================================================
       RANDOM CRICKET BALLS
    ===================================================== */

    function createBall() {

        if (!background) {
            return;
        }


        const ball =
            document.createElement(
                "div"
            );


        ball.className =
            "cricket-ball";


        const size =
            Math.floor(
                Math.random() * 17
            ) + 13;


        ball.style.width =
            size + "px";


        ball.style.height =
            size + "px";


        ball.style.top =
            Math.random() * 85 + "%";


        const duration =
            Math.floor(
                Math.random() * 5
            ) + 6;


        ball.style.animation =
            `ballFlyRandom ${duration}s linear forwards`;


        background.appendChild(
            ball
        );


        setTimeout(
            function () {

                ball.remove();

            },
            duration * 1000 + 500
        );

    }


    /* =====================================================
       BALL ANIMATION
    ===================================================== */

    if (
        !document.getElementById(
            "reminder-theme-animations"
        )
    ) {

        const style =
            document.createElement(
                "style"
            );


        style.id =
            "reminder-theme-animations";


        style.textContent = `

        @keyframes ballFlyRandom {

            0% {

                transform:
                    translate(-100px,80px)
                    rotate(0deg);

                opacity: 0;

            }

            10% {
                opacity: .8;
            }

            50% {

                transform:
                    translate(55vw,-120px)
                    rotate(720deg);

            }

            100% {

                transform:
                    translate(115vw,100px)
                    rotate(1440deg);

                opacity: 0;

            }

        }


        @keyframes balloonFloat {

            0% {

                transform:
                    translateY(0)
                    rotate(-5deg);

                opacity: 0;

            }

            10% {
                opacity: .45;
            }

            50% {

                transform:
                    translateY(-60vh)
                    translateX(25px)
                    rotate(7deg);

            }

            100% {

                transform:
                    translateY(-120vh)
                    translateX(-20px)
                    rotate(-5deg);

                opacity: 0;

            }

        }

        `;


        document.head.appendChild(
            style
        );

    }


    /* =====================================================
       RANDOM BALLOONS
    ===================================================== */

    function createBalloon() {

        if (!background) {
            return;
        }


        const balloon =
            document.createElement(
                "div"
            );


        balloon.className =
            "balloon";


        const colors = [

            "#818cf8",
            "#f472b6",
            "#38bdf8",
            "#34d399",
            "#fbbf24",
            "#fb7185"

        ];


        balloon.style.background =
            colors[
                Math.floor(
                    Math.random() *
                    colors.length
                )
            ];


        balloon.style.left =
            Math.random() * 94 + "%";


        const duration =
            Math.floor(
                Math.random() * 8
            ) + 14;


        balloon.style.animation =
            `balloonFloat ${duration}s linear forwards`;


        background.appendChild(
            balloon
        );


        setTimeout(
            function () {

                balloon.remove();

            },
            duration * 1000 + 500
        );

    }


    /* =====================================================
       START ANIMATIONS
    ===================================================== */

    /*
       Create a few immediately
       so the background isn't empty.
    */

    createBall();
    createBall();
    createBall();

    createBalloon();
    createBalloon();


    setInterval(
        createBall,
        1800
    );


    setInterval(
        createBalloon,
        3500
    );


    /* =====================================================
       INITIALIZE
    ===================================================== */

    loadTheme();

    loadPeriod();

});
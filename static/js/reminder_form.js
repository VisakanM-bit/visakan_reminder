/* =========================================================
   BDAY REMINDER
   REMINDERS CALENDAR ENGINE
   ========================================================= */

"use strict";


/* =========================================================
   DATA
   ========================================================= */

const reminderData =
    Array.isArray(window.REMINDERS_DATA)
        ? window.REMINDERS_DATA
        : [];


/* =========================================================
   DOM
   ========================================================= */

const calendarMonth =
    document.getElementById(
        "calendar-month"
    );


const calendarDays =
    document.getElementById(
        "calendar-days"
    );


const previousMonthButton =
    document.getElementById(
        "previous-month"
    );


const nextMonthButton =
    document.getElementById(
        "next-month"
    );


const todayButton =
    document.getElementById(
        "today-button"
    );


const selectedDateTitle =
    document.getElementById(
        "selected-date-title"
    );


const selectedCount =
    document.getElementById(
        "selected-count"
    );


const reminderList =
    document.getElementById(
        "reminder-list"
    );


const emptyState =
    document.getElementById(
        "empty-state"
    );


/* =========================================================
   DATE
   ========================================================= */

const now =
    new Date();


let currentMonth =
    now.getMonth();


let currentYear =
    now.getFullYear();


let selectedDate =
    new Date(
        now.getFullYear(),
        now.getMonth(),
        now.getDate()
    );


/* =========================================================
   HELPERS
   ========================================================= */

function pad(value) {

    return String(value)
        .padStart(2, "0");

}


function formatDateKey(date) {

    return (
        date.getFullYear()
        + "-"
        + pad(date.getMonth() + 1)
        + "-"
        + pad(date.getDate())
    );

}


function parseDateKey(value) {

    if (!value) {
        return null;
    }


    const parts =
        value.split("-");


    if (
        parts.length !== 3
    ) {
        return null;
    }


    return new Date(
        Number(parts[0]),
        Number(parts[1]) - 1,
        Number(parts[2])
    );

}


function formatLongDate(date) {

    return date.toLocaleDateString(
        "en-IN",
        {
            weekday: "long",
            day: "numeric",
            month: "long",
            year: "numeric"
        }
    );

}


function formatMonthYear(
    year,
    month
) {

    return new Date(
        year,
        month,
        1
    ).toLocaleDateString(
        "en-IN",
        {
            month: "long",
            year: "numeric"
        }
    );

}


function escapeHTML(value) {

    const div =
        document.createElement(
            "div"
        );

    div.textContent =
        value ?? "";

    return div.innerHTML;

}


/* =========================================================
   TODAY
   ========================================================= */

function getTodayKey() {

    return formatDateKey(
        new Date()
    );

}


/* =========================================================
   REMINDER DATE
   ========================================================= */

function getReminderDate(
    reminder
) {

    return (
        reminder.reminder_date
        ||
        reminder.date
        ||
        ""
    );

}


/* =========================================================
   RENDER CALENDAR
   ========================================================= */

function renderCalendar() {

    if (!calendarDays) {
        return;
    }


    calendarMonth.textContent =
        formatMonthYear(
            currentYear,
            currentMonth
        );


    calendarDays.innerHTML =
        "";


    const firstDay =
        new Date(
            currentYear,
            currentMonth,
            1
        );


    const lastDay =
        new Date(
            currentYear,
            currentMonth + 1,
            0
        );


    const firstWeekday =
        firstDay.getDay();


    const daysInMonth =
        lastDay.getDate();


    /*
       Empty cells before
       first day.
    */

    for (
        let i = 0;
        i < firstWeekday;
        i++
    ) {

        const empty =
            document.createElement(
                "div"
            );

        empty.className =
            "calendar-day empty";

        calendarDays.appendChild(
            empty
        );

    }


    /*
       Actual days.
    */

    for (
        let day = 1;
        day <= daysInMonth;
        day++
    ) {

        const date =
            new Date(
                currentYear,
                currentMonth,
                day
            );


        const dateKey =
            formatDateKey(
                date
            );


        const cell =
            document.createElement(
                "button"
            );


        cell.type =
            "button";


        cell.className =
            "calendar-day";


        /*
           Today.
        */

        if (
            dateKey ===
            getTodayKey()
        ) {

            cell.classList.add(
                "today"
            );

        }


        /*
           Selected date.
        */

        if (
            dateKey ===
            formatDateKey(
                selectedDate
            )
        ) {

            cell.classList.add(
                "selected"
            );

        }


        /*
           Does this date have
           reminders?
        */

        const hasReminder =
            reminderData.some(
                function(reminder) {

                    return (
                        getReminderDate(
                            reminder
                        )
                        ===
                        dateKey
                    );

                }
            );


        if (hasReminder) {

            cell.classList.add(
                "has-reminders"
            );

        }


        cell.innerHTML =
            `
                <span class="day-number">
                    ${day}
                </span>
            `;


        cell.addEventListener(
            "click",
            function() {

                selectedDate =
                    new Date(
                        currentYear,
                        currentMonth,
                        day
                    );

                renderCalendar();

                renderSelectedDate();

            }
        );


        calendarDays.appendChild(
            cell
        );

    }

}


/* =========================================================
   SELECTED DATE
   ========================================================= */

function renderSelectedDate() {

    if (!selectedDateTitle) {
        return;
    }


    selectedDateTitle.textContent =
        formatLongDate(
            selectedDate
        );


    const selectedKey =
        formatDateKey(
            selectedDate
        );


    const selectedReminders =
        reminderData.filter(
            function(reminder) {

                return (
                    getReminderDate(
                        reminder
                    )
                    ===
                    selectedKey
                );

            }
        );


    if (selectedCount) {

        selectedCount.textContent =
            selectedReminders.length;

    }


    renderReminderList(
        selectedReminders
    );

}


/* =========================================================
   FORMAT TIME
   ========================================================= */

function formatReminderTime(
    reminder
) {

    const value =
        reminder.reminder_time
        ||
        reminder.time
        ||
        "";


    if (!value) {
        return "--:--";
    }


    const parts =
        value.split(":");


    if (
        parts.length < 2
    ) {

        return value;

    }


    let hours =
        Number(parts[0]);


    const minutes =
        parts[1];


    const suffix =
        hours >= 12
            ? "PM"
            : "AM";


    hours =
        hours % 12;


    if (hours === 0) {
        hours = 12;
    }


    return (
        hours
        + ":"
        + minutes
        + " "
        + suffix
    );

}


/* =========================================================
   RENDER REMINDERS
   ========================================================= */

function renderReminderList(
    reminders
) {

    if (!reminderList) {
        return;
    }


    reminderList.innerHTML =
        "";


    if (
        !reminders.length
    ) {

        if (emptyState) {

            emptyState.style.display =
                "block";

        }

        return;

    }


    if (emptyState) {

        emptyState.style.display =
            "none";

    }


    /*
       Sort by time.
    */

    const sorted =
        [...reminders].sort(
            function(a, b) {

                return (
                    (
                        a.reminder_time
                        ||
                        ""
                    )
                    .localeCompare(
                        b.reminder_time
                        ||
                        ""
                    )
                );

            }
        );


    sorted.forEach(
        function(reminder) {

            const card =
                document.createElement(
                    "article"
                );


            card.className =
                "reminder-card";


            const title =
                escapeHTML(
                    reminder.title
                    ||
                    "Untitled reminder"
                );


            const description =
                escapeHTML(
                    reminder.description
                    ||
                    ""
                );


            const status =
                escapeHTML(
                    reminder.status
                    ||
                    "pending"
                );


            card.innerHTML =
                `
                    <div class="reminder-time">
                        ${formatReminderTime(reminder)}
                    </div>

                    <div class="reminder-main">

                        <h3>
                            ${title}
                        </h3>

                        ${
                            description
                                ? `
                                    <p class="reminder-description">
                                        ${description}
                                    </p>
                                  `
                                : ""
                        }

                        <span class="reminder-status">
                            ${status}
                        </span>

                    </div>

                    <div class="reminder-actions">

                        <a
                            class="reminder-action edit"
                            href="/reminders/edit/${reminder.id}"
                            aria-label="Edit reminder"
                        >
                            ✏️
                        </a>

                        <form
                            method="POST"
                            action="/reminders/delete/${reminder.id}"
                            onsubmit="
                                return confirm(
                                    'Are you sure you want to delete this reminder?'
                                );
                            "
                        >

                            <button
                                type="submit"
                                class="reminder-action delete"
                                aria-label="Delete reminder"
                            >
                                🗑️
                            </button>

                        </form>

                    </div>
                `;


            reminderList.appendChild(
                card
            );

        }
    );

}


/* =========================================================
   PREVIOUS MONTH
   ========================================================= */

if (previousMonthButton) {

    previousMonthButton.addEventListener(
        "click",
        function() {

            currentMonth--;

            if (
                currentMonth < 0
            ) {

                currentMonth = 11;

                currentYear--;

            }


            renderCalendar();

        }
    );

}


/* =========================================================
   NEXT MONTH
   ========================================================= */

if (nextMonthButton) {

    nextMonthButton.addEventListener(
        "click",
        function() {

            currentMonth++;

            if (
                currentMonth > 11
            ) {

                currentMonth = 0;

                currentYear++;

            }


            renderCalendar();

        }
    );

}


/* =========================================================
   TODAY
   ========================================================= */

if (todayButton) {

    todayButton.addEventListener(
        "click",
        function() {

            const today =
                new Date();


            currentMonth =
                today.getMonth();


            currentYear =
                today.getFullYear();


            selectedDate =
                new Date(
                    today.getFullYear(),
                    today.getMonth(),
                    today.getDate()
                );


            renderCalendar();

            renderSelectedDate();

        }
    );

}


/* =========================================================
   INITIALIZE
   ========================================================= */

function initializeRemindersPage() {

    renderCalendar();

    renderSelectedDate();

}


if (
    document.readyState ===
    "loading"
) {

    document.addEventListener(
        "DOMContentLoaded",
        initializeRemindersPage
    );

}

else {

    initializeRemindersPage();

}
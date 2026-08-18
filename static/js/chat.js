"use strict";

/*
=============================================================
BDAY REMINDER - CHAT ASSISTANT
=============================================================

TIME EVENT
    ↓
Flexible natural-language text
    ↓
Flask
    ↓
Reminder database
    ↓
Reminders page

BIRTHDAY
    ↓
Flexible natural-language text
    ↓
Birthday database
    ↓
Annual Reminder database
    ↓
5-day birthday notification
=============================================================
*/


document.addEventListener(
    "DOMContentLoaded",
    function () {

        const form =
            document.getElementById(
                "chat-form"
            );


        const input =
            document.getElementById(
                "chat-message"
            ) ||
            document.getElementById(
                "message-input"
            );


        const messages =
            document.getElementById(
                "chat-messages"
            );


        const sendButton =
            document.getElementById(
                "chat-send"
            ) ||
            document.getElementById(
                "send-button"
            );


        const modeLabel =
            document.getElementById(
                "selected-mode"
            );


        const typeCards =
            document.querySelectorAll(
                ".type-card"
            );


        if (
            !form ||
            !input ||
            !messages
        ) {

            console.error(
                "Chat elements not found."
            );

            return;

        }


        let currentMode =
            "reminder";


        let isSending =
            false;


        /* =====================================================
           MODE
        ===================================================== */

        function updateMode(
            mode
        ) {

            currentMode =

                mode === "birthday"

                    ? "birthday"

                    : "reminder";


            typeCards.forEach(
                function (card) {

                    card.classList.toggle(

                        "active",

                        card.dataset.mode
                        ===
                        currentMode

                    );

                }
            );


            if (!modeLabel) {

                return;

            }


            if (
                currentMode
                ===
                "birthday"
            ) {

                modeLabel.textContent =
                    "🎂 Birthday Reminder";


                input.placeholder =
                    "Example: Arun's birthday is August 25";

            }

            else {

                modeLabel.textContent =
                    "⏰ Time Event Reminder";


                input.placeholder =
                    "Example: Meeting tomorrow at 7 PM";

            }

        }


        typeCards.forEach(
            function (card) {

                card.addEventListener(
                    "click",
                    function () {

                        updateMode(

                            card.dataset.mode
                            ||
                            "reminder"

                        );


                        input.focus();

                    }
                );

            }
        );


        /* =====================================================
           TIME
        ===================================================== */

        function getTime() {

            return new Date()
                .toLocaleTimeString(
                    [],
                    {
                        hour:
                            "2-digit",

                        minute:
                            "2-digit"
                    }
                );

        }


        /* =====================================================
           HTML SAFETY
        ===================================================== */

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


        /* =====================================================
           FORMAT TIME
        ===================================================== */

        function formatTime(
            value
        ) {

            if (!value) {

                return "";

            }


            const parts =
                String(
                    value
                ).split(":");


            if (
                parts.length < 2
            ) {

                return String(
                    value
                );

            }


            let hour =
                parseInt(
                    parts[0],
                    10
                );


            const minute =
                parts[1];


            const period =
                hour >= 12
                    ? "PM"
                    : "AM";


            hour =
                hour % 12 || 12;


            return (

                hour
                +
                ":"
                +
                minute
                +
                " "
                +
                period

            );

        }


        /* =====================================================
           ADD MESSAGE
        ===================================================== */

        function addMessage(
            text,
            sender,
            data
        ) {

            const row =
                document.createElement(
                    "div"
                );


            row.className =
                "message "
                +
                sender;


            const avatar =
                document.createElement(
                    "div"
                );


            avatar.className =
                "message-avatar";


            avatar.textContent =

                sender === "user"

                    ? "👤"

                    : "🤖";


            const content =
                document.createElement(
                    "div"
                );


            content.className =
                "message-content";


            const bubble =
                document.createElement(
                    "div"
                );


            bubble.className =
                "message-bubble";


            bubble.innerHTML =
                escapeHtml(
                    text
                ).replace(
                    /\n/g,
                    "<br>"
                );


            /* =================================================
               CREATED REMINDER CARD
            ================================================= */

            if (
                data
                &&
                data.created
            ) {

                const card =
                    document.createElement(
                        "div"
                    );


                card.className =
                    "created-card";


                if (
                    data.type
                    ===
                    "reminder"
                    &&
                    data.reminder
                ) {

                    card.innerHTML = `

                        <div class="created-icon">
                            ⏰
                        </div>

                        <div>

                            <strong>
                                Reminder Added
                            </strong>

                            <span>
                                ${escapeHtml(
                                    data.reminder.title
                                )}
                            </span>

                            <small>

                                📅
                                ${escapeHtml(
                                    data.reminder.date
                                )}

                                <br>

                                🕐
                                ${escapeHtml(
                                    formatTime(
                                        data.reminder.time
                                    )
                                )}

                            </small>

                        </div>

                    `;

                }


                if (
                    data.type
                    ===
                    "birthday"
                    &&
                    data.birthday
                ) {

                    card.innerHTML = `

                        <div class="created-icon">
                            🎂
                        </div>

                        <div>

                            <strong>
                                Birthday Added
                            </strong>

                            <span>
                                ${escapeHtml(
                                    data.birthday.name
                                )}
                            </span>

                            <small>

                                📅
                                ${escapeHtml(
                                    data.birthday.date
                                )}

                                <br>

                                🔁 Every year

                            </small>

                        </div>

                    `;

                }


                bubble.appendChild(
                    card
                );

            }


            const timeElement =
                document.createElement(
                    "span"
                );


            timeElement.className =
                "message-time";


            timeElement.textContent =
                getTime();


            content.appendChild(
                bubble
            );


            content.appendChild(
                timeElement
            );


            row.appendChild(
                avatar
            );


            row.appendChild(
                content
            );


            messages.appendChild(
                row
            );


            messages.scrollTop =
                messages.scrollHeight;

        }


        /* =====================================================
           TYPING
        ===================================================== */

        function showTyping() {

            removeTyping();


            const row =
                document.createElement(
                    "div"
                );


            row.id =
                "typing-message";


            row.className =
                "message assistant";


            row.innerHTML = `

                <div class="message-avatar">
                    🤖
                </div>

                <div class="message-content">

                    <div class="typing-bubble">

                        <span></span>
                        <span></span>
                        <span></span>

                    </div>

                </div>

            `;


            messages.appendChild(
                row
            );


            messages.scrollTop =
                messages.scrollHeight;

        }


        function removeTyping() {

            const typing =
                document.getElementById(
                    "typing-message"
                );


            if (typing) {

                typing.remove();

            }

        }


        /* =====================================================
           SEND MESSAGE
        ===================================================== */

        async function sendMessage(
            event
        ) {

            if (event) {

                event.preventDefault();

            }


            if (isSending) {

                return;

            }


            const message =
                input.value.trim();


            if (!message) {

                input.focus();

                return;

            }


            addMessage(
                message,
                "user"
            );


            input.value =
                "";


            isSending =
                true;


            input.style.height =
                "auto";


            if (sendButton) {

                sendButton.disabled =
                    true;

            }


            showTyping();


            try {

                const response =
                    await fetch(

                        "/api/chat-agent",

                        {

                            method:
                                "POST",

                            headers: {

                                "Content-Type":
                                    "application/json",

                                "Accept":
                                    "application/json"

                            },

                            credentials:
                                "same-origin",

                            body:
                                JSON.stringify({

                                    message:
                                        message,

                                    mode:
                                        currentMode

                                })

                        }

                    );


                let data = {};


                try {

                    data =
                        await response.json();

                }

                catch (jsonError) {

                    console.error(
                        "Invalid JSON:",
                        jsonError
                    );

                }


                removeTyping();


                if (
                    response.status
                    ===
                    401
                ) {

                    addMessage(

                        "🔐 Your session has expired. Please log in again.",

                        "assistant"

                    );


                    return;

                }


                if (
                    !response.ok
                    ||
                    !data.success
                    ||
                    !data.verified
                ) {

                    addMessage(

                        data.reply
                        ||
                        "❌ I could not save that.",

                        "assistant"

                    );


                    return;

                }


                addMessage(

                    data.reply
                    ||
                    "✅ Received and saved successfully.",

                    "assistant",

                    data

                );


            }

            catch (error) {

                console.error(
                    "Chat error:",
                    error
                );


                removeTyping();


                addMessage(

                    "❌ Connection problem. Please make sure Flask is running.",

                    "assistant"

                );

            }

            finally {

                isSending =
                    false;

                if (sendButton) {

                    sendButton.disabled =
                        false;

                }


                input.focus();

            }

        }


        /* =====================================================
           ENTER
        ===================================================== */

        input.addEventListener(

            "keydown",

            function (event) {

                if (

                    event.key
                    ===
                    "Enter"

                    &&

                    !event.shiftKey

                ) {

                    event.preventDefault();


                    form.requestSubmit();

                }

            }

        );


        /* =====================================================
           AUTO RESIZE
        ===================================================== */

        input.addEventListener(

            "input",

            function () {

                input.style.height =
                    "auto";


                input.style.height =

                    Math.min(

                        input.scrollHeight,

                        120

                    )
                    +
                    "px";

            }

        );


        /* =====================================================
           SUBMIT
        ===================================================== */

        form.addEventListener(

            "submit",

            sendMessage

        );


        /* =====================================================
           INITIAL
        ===================================================== */

        updateMode(
            "reminder"
        );

    }
);

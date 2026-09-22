# ============================================================
# BDAY REMINDER
# EMAIL SERVICE
# SMTP / GMAIL
# ============================================================

import os
import smtplib

from email.message import EmailMessage


# ============================================================
# SMTP CONFIGURATION
# ============================================================

SMTP_SERVER = os.environ.get(
    "SMTP_SERVER",
    "smtp.gmail.com"
)

SMTP_PORT = int(
    os.environ.get(
        "SMTP_PORT",
        "587"
    )
)

SMTP_USERNAME = os.environ.get(
    "SMTP_USERNAME",
    ""
)

SMTP_PASSWORD = os.environ.get(
    "SMTP_PASSWORD",
    ""
)

SMTP_FROM_EMAIL = os.environ.get(
    "SMTP_FROM_EMAIL",
    SMTP_USERNAME
)

SMTP_FROM_NAME = os.environ.get(
    "SMTP_FROM_NAME",
    "Bday Reminder"
)


# ============================================================
# DEFAULT RECIPIENT
# ============================================================
#
# All reminder emails will currently be sent to:
#
# visakanreminder@gmail.com
#
# Later, if you want different users to receive emails at
# different addresses, we can move this into the database.
#
# ============================================================

DEFAULT_RECIPIENT_EMAIL = os.environ.get(
    "REMINDER_EMAIL",
    "visakanreminder@gmail.com"
)


# ============================================================
# SMTP CONFIGURATION CHECK
# ============================================================

def smtp_configuration_ready():
    """
    Check whether the required SMTP credentials are available.

    Returns:
        bool: True when SMTP username and password are available.
    """

    return bool(
        SMTP_SERVER
        and SMTP_PORT
        and SMTP_USERNAME
        and SMTP_PASSWORD
        and SMTP_FROM_EMAIL
    )


# ============================================================
# BUILD REMINDER EMAIL
# ============================================================

def build_reminder_email(
    title,
    body,
    recipient=None,
    date_text=None,
    time_text=None,
    place=None
):
    """
    Build a reminder email using the same information shown
    by the application's notification system.

    Args:
        title: Reminder title.
        body: Main notification message.
        recipient: Email recipient.
        date_text: Optional reminder date.
        time_text: Optional reminder time.
        place: Optional reminder location.

    Returns:
        EmailMessage
    """

    recipient = (
        recipient
        or DEFAULT_RECIPIENT_EMAIL
    )

    message = EmailMessage()

    # --------------------------------------------------------
    # EMAIL HEADERS
    # --------------------------------------------------------

    message["From"] = (
        f"{SMTP_FROM_NAME} <{SMTP_FROM_EMAIL}>"
    )

    message["To"] = recipient

    message["Subject"] = (
        f"🔔 Reminder: {title}"
    )

    # --------------------------------------------------------
    # EMAIL BODY
    # --------------------------------------------------------

    email_lines = [
        "🔔 BDAY REMINDER",
        "",
        f"Reminder: {title}",
        "",
        body.strip() if body else "Your reminder is due now."
    ]

    if date_text:
        email_lines.extend([
            "",
            f"📅 Date: {date_text}"
        ])

    if time_text:
        email_lines.append(
            f"🕐 Time: {time_text}"
        )

    if place:
        email_lines.append(
            f"📍 Place: {place}"
        )

    email_lines.extend([
        "",
        "This reminder is due now.",
        "",
        "— Bday Reminder"
    ])

    message.set_content(
        "\n".join(email_lines)
    )

    return message


# ============================================================
# SEND EMAIL
# ============================================================

def send_reminder_email(
    title,
    body,
    recipient=None,
    date_text=None,
    time_text=None,
    place=None
):
    """
    Send a reminder email through Gmail SMTP.

    Returns:
        True  -> Email sent successfully.
        False -> Email could not be sent.
    """

    recipient = (
        recipient
        or DEFAULT_RECIPIENT_EMAIL
    )

    # --------------------------------------------------------
    # CHECK SMTP CONFIGURATION
    # --------------------------------------------------------

    if not smtp_configuration_ready():

        print(
            "⚠️ SMTP configuration is incomplete."
        )

        return False

    # --------------------------------------------------------
    # BUILD EMAIL
    # --------------------------------------------------------

    message = build_reminder_email(
        title=title,
        body=body,
        recipient=recipient,
        date_text=date_text,
        time_text=time_text,
        place=place
    )

    # --------------------------------------------------------
    # CONNECT TO GMAIL SMTP
    # --------------------------------------------------------

    try:

        print(
            f"📧 Connecting to SMTP server: "
            f"{SMTP_SERVER}:{SMTP_PORT}"
        )

        with smtplib.SMTP(
            SMTP_SERVER,
            SMTP_PORT,
            timeout=30
        ) as smtp:

            # ------------------------------------------------
            # START TLS ENCRYPTION
            # ------------------------------------------------

            smtp.ehlo()

            smtp.starttls()

            smtp.ehlo()

            # ------------------------------------------------
            # LOGIN
            # ------------------------------------------------

            smtp.login(
                SMTP_USERNAME,
                SMTP_PASSWORD
            )

            # ------------------------------------------------
            # SEND EMAIL
            # ------------------------------------------------

            smtp.send_message(
                message
            )

        print(
            f"✅ Reminder email sent successfully "
            f"to {recipient}"
        )

        return True

    except smtplib.SMTPAuthenticationError:

        print(
            "❌ SMTP authentication failed."
        )

        print(
            "Check the Gmail App Password and "
            "SMTP username in Render."
        )

        return False

    except smtplib.SMTPConnectError:

        print(
            "❌ Could not connect to the SMTP server."
        )

        return False

    except smtplib.SMTPException as error:

        print(
            f"❌ SMTP error while sending email: {error}"
        )

        return False

    except Exception as error:

        print(
            f"❌ Unexpected email error: {error}"
        )

        return False


# ============================================================
# SIMPLE TEST FUNCTION
# ============================================================

def send_test_email(
    recipient=None
):
    """
    Send a simple test email.

    This function is useful for testing SMTP separately
    before connecting the email service to the scheduler.
    """

    return send_reminder_email(
        title="Test Notification",
        body=(
            "This is a test notification from "
            "your Bday Reminder application."
        ),
        recipient=(
            recipient
            or DEFAULT_RECIPIENT_EMAIL
        ),
        date_text=None,
        time_text=None,
        place=None
    )

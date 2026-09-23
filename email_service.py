# ============================================================
# BDAY REMINDER
# RELIABLE EMAIL NOTIFICATION SERVICE
# ============================================================
#
# Purpose:
#
# 1. Works with the EXISTING scheduler.py.
# 2. Keeps the existing function name:
#       send_due_email_notifications()
# 3. Checks the same due-notification source used by
#    notification_service.py.
# 4. Runs safely every 30 seconds through scheduler.py.
# 5. Retries failed email delivery on the next 30-second cycle.
# 6. Prevents duplicate emails after successful delivery.
# 7. Uses a short SMTP timeout so a slow SMTP connection cannot
#    block the scheduler for a long time.
# 8. Keeps reminder and birthday email formatting.
#
# IMPORTANT:
# Replace the existing email_service.py with this file.
# Do NOT change app.py, notification_service.py, database models,
# PWA files, chat files, or reminder creation files for this step.
#
# ============================================================

import os
import smtplib
import time

from datetime import datetime

from email.message import EmailMessage

from sqlalchemy.exc import OperationalError, SQLAlchemyError

from database import db

from notification_service import get_due_push_items


# ============================================================
# CONFIGURATION
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

DEFAULT_RECIPIENT_EMAIL = os.environ.get(
    "REMINDER_EMAIL",
    "visakanreminder@gmail.com"
)


# ============================================================
# RELIABILITY SETTINGS
# ============================================================

# scheduler.py checks every 30 seconds.
EMAIL_CHECK_INTERVAL_SECONDS = 30

# Maximum time allowed for one SMTP connection/send attempt.
# Keeping this below the scheduler interval prevents a slow SMTP
# connection from occupying the scheduler for the entire cycle.
SMTP_TIMEOUT_SECONDS = 10

# Retry database reads a small number of times inside one cycle.
DATABASE_READ_RETRIES = 2

# Small pause between database retry attempts.
DATABASE_RETRY_DELAY_SECONDS = 1


# ============================================================
# EMAIL DELIVERY TRACKING
# ============================================================

class EmailDelivery(db.Model):

    __tablename__ = "notification_email_deliveries"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    # NotificationAlarm ID.
    # Intentionally NOT a foreign key so email tracking cannot
    # interfere with existing notification alarm operations.
    alarm_id = db.Column(
        db.Integer,
        nullable=False,
        unique=True,
        index=True
    )

    # Set ONLY after an email has actually been sent successfully.
    last_sent_at = db.Column(
        db.DateTime,
        nullable=True
    )

    created_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow
    )


# ============================================================
# SMTP CONFIGURATION
# ============================================================

def smtp_configuration_ready():

    return bool(
        SMTP_SERVER
        and SMTP_PORT
        and SMTP_USERNAME
        and SMTP_PASSWORD
        and SMTP_FROM_EMAIL
        and DEFAULT_RECIPIENT_EMAIL
    )


# ============================================================
# GET DELIVERY RECORD
# ============================================================

def get_email_delivery(alarm_id):

    return (
        EmailDelivery.query
        .filter_by(
            alarm_id=alarm_id
        )
        .first()
    )


# ============================================================
# CREATE DELIVERY RECORD
# ============================================================

def get_or_create_email_delivery(alarm_id):

    delivery = get_email_delivery(
        alarm_id
    )

    if delivery:
        return delivery

    delivery = EmailDelivery(
        alarm_id=alarm_id,
        last_sent_at=None
    )

    db.session.add(
        delivery
    )

    try:

        db.session.flush()

        return delivery

    except Exception:

        db.session.rollback()

        # Another scheduler cycle/process may have created it.
        return get_email_delivery(
            alarm_id
        )


# ============================================================
# DATE / TIME FORMATTING
# ============================================================

def format_email_date(value):

    if not value:
        return ""

    try:

        parsed = datetime.strptime(
            str(value),
            "%Y-%m-%d"
        )

        return parsed.strftime(
            "%d %B %Y"
        )

    except Exception:

        return str(value)


def format_email_time(value):

    if not value:
        return ""

    try:

        parsed = datetime.strptime(
            str(value),
            "%H:%M"
        )

        return parsed.strftime(
            "%I:%M %p"
        )

    except Exception:

        return str(value)


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

    recipient = (
        recipient
        or DEFAULT_RECIPIENT_EMAIL
    )

    message = EmailMessage()

    message["From"] = (
        f"{SMTP_FROM_NAME} "
        f"<{SMTP_FROM_EMAIL}>"
    )

    message["To"] = recipient

    message["Subject"] = (
        f"🔔 Reminder: {title}"
    )

    lines = [
        "🔔 BDAY REMINDER",
        "",
        f"Reminder: {title}",
        ""
    ]

    if body:

        lines.append(
            body.strip()
        )

    else:

        lines.append(
            "Your reminder is due now."
        )

    if date_text:

        lines.extend([
            "",
            f"📅 Date: {date_text}"
        ])

    if time_text:

        lines.append(
            f"🕐 Time: {time_text}"
        )

    if place:

        lines.append(
            f"📍 Place: {place}"
        )

    lines.extend([
        "",
        "This reminder is due now.",
        "",
        "— Bday Reminder"
    ])

    message.set_content(
        "\n".join(lines)
    )

    return message


# ============================================================
# BUILD BIRTHDAY EMAIL
# ============================================================

def build_birthday_email(
    name,
    body,
    recipient=None,
    date_text=None,
    time_text=None
):

    recipient = (
        recipient
        or DEFAULT_RECIPIENT_EMAIL
    )

    message = EmailMessage()

    message["From"] = (
        f"{SMTP_FROM_NAME} "
        f"<{SMTP_FROM_EMAIL}>"
    )

    message["To"] = recipient

    message["Subject"] = (
        f"🎂 Birthday Reminder: {name}"
    )

    lines = [
        "🎂 BIRTHDAY REMINDER",
        "",
        f"Today is {name}'s birthday!",
        ""
    ]

    if body:

        lines.append(
            body.strip()
        )

    else:

        lines.append(
            f"Today is {name}'s birthday!"
        )

    if date_text:

        lines.extend([
            "",
            f"📅 Date: {date_text}"
        ])

    if time_text:

        lines.append(
            f"🕐 Notification Time: {time_text}"
        )

    lines.extend([
        "",
        "Don't forget to wish them!",
        "",
        "— Bday Reminder"
    ])

    message.set_content(
        "\n".join(lines)
    )

    return message


# ============================================================
# SEND ONE EMAIL
# ============================================================

def send_email(message):

    if not smtp_configuration_ready():

        print(
            "❌ SMTP configuration is incomplete."
        )

        return False

    try:

        print(
            "📧 Connecting to Gmail SMTP..."
        )

        print(
            f"   SMTP: {SMTP_SERVER}:{SMTP_PORT}"
        )

        print(
            f"   From: {SMTP_FROM_EMAIL}"
        )

        print(
            f"   To: {message['To']}"
        )

        print(
            f"   Subject: {message['Subject']}"
        )

        with smtplib.SMTP(
            SMTP_SERVER,
            SMTP_PORT,
            timeout=SMTP_TIMEOUT_SECONDS
        ) as smtp:

            smtp.ehlo()

            smtp.starttls()

            smtp.ehlo()

            smtp.login(
                SMTP_USERNAME,
                SMTP_PASSWORD
            )

            smtp.send_message(
                message
            )

        print(
            f"✅ Email sent successfully to "
            f"{message['To']}"
        )

        return True

    except smtplib.SMTPAuthenticationError:

        print(
            "❌ Gmail SMTP authentication failed."
        )

        print(
            "Check SMTP_USERNAME and the Gmail "
            "App Password in Render."
        )

        return False

    except smtplib.SMTPConnectError:

        print(
            "❌ Could not connect to Gmail SMTP."
        )

        return False

    except (TimeoutError, OSError):

        print(
            "❌ Gmail SMTP connection timed out "
            "or was interrupted."
        )

        return False

    except smtplib.SMTPException as error:

        print(
            f"❌ SMTP error: {error}"
        )

        return False

    except Exception as error:

        print(
            f"❌ Email sending error: {error}"
        )

        return False


# ============================================================
# SEND REMINDER EMAIL
# ============================================================

def send_reminder_email(
    title,
    body,
    recipient=None,
    date_text=None,
    time_text=None,
    place=None
):

    message = build_reminder_email(
        title=title,
        body=body,
        recipient=recipient,
        date_text=date_text,
        time_text=time_text,
        place=place
    )

    return send_email(
        message
    )


# ============================================================
# SEND BIRTHDAY EMAIL
# ============================================================

def send_birthday_email(
    name,
    body,
    recipient=None,
    date_text=None,
    time_text=None
):

    message = build_birthday_email(
        name=name,
        body=body,
        recipient=recipient,
        date_text=date_text,
        time_text=time_text
    )

    return send_email(
        message
    )


# ============================================================
# GET DUE ITEMS SAFELY
# ============================================================

def get_due_items_safely():

    for attempt in range(
        1,
        DATABASE_READ_RETRIES + 1
    ):

        try:

            return get_due_push_items()

        except OperationalError as error:

            db.session.rollback()

            print(
                f"⚠️ Database read attempt "
                f"{attempt}/{DATABASE_READ_RETRIES} failed."
            )

            print(
                f"   {error}"
            )

            if attempt < DATABASE_READ_RETRIES:

                time.sleep(
                    DATABASE_RETRY_DELAY_SECONDS
                )

        except SQLAlchemyError as error:

            db.session.rollback()

            print(
                f"⚠️ Database error while checking "
                f"email notifications: {error}"
            )

            if attempt < DATABASE_READ_RETRIES:

                time.sleep(
                    DATABASE_RETRY_DELAY_SECONDS
                )

        except Exception as error:

            db.session.rollback()

            print(
                f"❌ Unexpected error while getting "
                f"due email notifications: {error}"
            )

            break

    return []


# ============================================================
# SEND DUE EMAIL NOTIFICATIONS
# ============================================================
#
# scheduler.py calls this function every 30 seconds.
#
# Flow:
#
# Reminder becomes due
#       ↓
# scheduler checks
#       ↓
# this function gets the same due item used by push
#       ↓
# email is attempted immediately
#       ↓
# SUCCESS → record delivery → never send duplicate
# FAILURE → do NOT record success
#       ↓
# next 30-second scheduler cycle retries
#
# This gives the email path repeated opportunities to deliver
# instead of losing the notification after one failed attempt.
#
# A normal successful SMTP delivery should therefore happen
# during the first available 30-second check. The retry mechanism
# continues beyond five minutes if an external service is
# temporarily unavailable; we do not deliberately discard an
# unsent reminder after five minutes.
#
# ============================================================

def send_due_email_notifications():

    print(
        "📧 Checking due email notifications..."
    )

    if not smtp_configuration_ready():

        print(
            "⚠️ SMTP is not configured."
        )

        return

    items = get_due_items_safely()

    if not items:

        print(
            "📧 No due email notifications."
        )

        return

    print(
        f"📧 Due notification items found: "
        f"{len(items)}"
    )

    for alarm, user_id, payload in items:

        alarm_id = payload.get(
            "id"
        )

        if not alarm_id:

            continue

        try:

            # ------------------------------------------------
            # DUPLICATE PROTECTION
            # ------------------------------------------------

            delivery = get_email_delivery(
                alarm_id
            )

            if delivery and delivery.last_sent_at:

                print(
                    f"📧 Email already sent for "
                    f"alarm {alarm_id}."
                )

                continue

            notification_type = payload.get(
                "type"
            )

            # ------------------------------------------------
            # REMINDER
            # ------------------------------------------------

            if notification_type == "reminder":

                title = payload.get(
                    "title",
                    "Reminder"
                )

                body = payload.get(
                    "message",
                    f"{title} is due."
                )

                date_value = payload.get(
                    "date"
                )

                time_value = payload.get(
                    "time"
                )

                place = payload.get(
                    "place"
                )

                date_text = (
                    format_email_date(
                        date_value
                    )
                    if date_value
                    else None
                )

                time_text = (
                    format_email_time(
                        time_value
                    )
                    if time_value
                    else None
                )

                success = send_reminder_email(
                    title=title,
                    body=body,
                    recipient=DEFAULT_RECIPIENT_EMAIL,
                    date_text=date_text,
                    time_text=time_text,
                    place=place
                )

            # ------------------------------------------------
            # BIRTHDAY
            # ------------------------------------------------

            elif notification_type == "birthday":

                name = payload.get(
                    "name",
                    "Birthday"
                )

                body = payload.get(
                    "message",
                    f"Today is {name}'s birthday!"
                )

                date_value = payload.get(
                    "date"
                )

                time_value = payload.get(
                    "time"
                )

                date_text = (
                    format_email_date(
                        date_value
                    )
                    if date_value
                    else None
                )

                time_text = (
                    format_email_time(
                        time_value
                    )
                    if time_value
                    else None
                )

                success = send_birthday_email(
                    name=name,
                    body=body,
                    recipient=DEFAULT_RECIPIENT_EMAIL,
                    date_text=date_text,
                    time_text=time_text
                )

            else:

                print(
                    f"⚠️ Unknown notification type: "
                    f"{notification_type}"
                )

                continue

            # ------------------------------------------------
            # SUCCESS
            # ------------------------------------------------

            if success:

                delivery = get_or_create_email_delivery(
                    alarm_id
                )

                if delivery:

                    delivery.last_sent_at = (
                        datetime.utcnow()
                    )

                    db.session.commit()

                    print(
                        f"📧 Email delivery recorded "
                        f"for alarm {alarm_id}."
                    )

                else:

                    # The email was already sent successfully.
                    # Do not send it a second time just because
                    # the tracking record could not be created.
                    print(
                        f"⚠️ Email was sent for alarm "
                        f"{alarm_id}, but delivery tracking "
                        f"could not be created."
                    )

            # ------------------------------------------------
            # FAILURE → RETRY NEXT 30-SECOND CYCLE
            # ------------------------------------------------

            else:

                db.session.rollback()

                print(
                    f"⚠️ Email failed for alarm "
                    f"{alarm_id}. "
                    f"Will retry on the next 30-second check."
                )

        except Exception as error:

            db.session.rollback()

            print(
                f"❌ Email processing error for "
                f"alarm {alarm_id}: {error}"
            )

            print(
                "   The next 30-second scheduler cycle "
                "will retry."
            )


# ============================================================
# MANUAL TEST EMAIL
# ============================================================

def send_test_email(
    recipient=None
):

    recipient = (
        recipient
        or DEFAULT_RECIPIENT_EMAIL
    )

    message = EmailMessage()

    message["From"] = (
        f"{SMTP_FROM_NAME} "
        f"<{SMTP_FROM_EMAIL}>"
    )

    message["To"] = recipient

    message["Subject"] = (
        "✅ Bday Reminder SMTP Test"
    )

    message.set_content(
        "\n".join([
            "BDAY REMINDER SMTP TEST",
            "",
            "This is a test email from your",
            "Bday Reminder application.",
            "",
            "Gmail SMTP configuration is working.",
            "",
            "— Bday Reminder"
        ])
    )

    return send_email(
        message
    )

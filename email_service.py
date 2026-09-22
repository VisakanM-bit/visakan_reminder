# ============================================================
# BDAY REMINDER
# EMAIL NOTIFICATION SERVICE
# ============================================================
#
# This service:
#
# 1. Sends reminder emails through Gmail SMTP.
# 2. Sends birthday notification emails.
# 3. Uses the same notification information as the
#    existing notification_service.py.
# 4. Prevents duplicate emails.
# 5. Retries automatically if an email fails.
#
# SMTP credentials are read ONLY from environment variables.
#
# ============================================================


import os
import smtplib

from datetime import datetime

from email.message import EmailMessage

from database import db

from database.models import (
    Reminder,
    Birthday
)

from notification_service import (
    get_due_push_items
)


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
# EMAIL RECIPIENT
# ============================================================
#
# Current project requirement:
#
# Send notification emails to:
#
# visakanreminder@gmail.com
#
# This can later be changed to a user-specific email
# stored in the database.
#
# ============================================================

DEFAULT_RECIPIENT_EMAIL = os.environ.get(
    "REMINDER_EMAIL",
    "visakanreminder@gmail.com"
)


# ============================================================
# EMAIL DELIVERY TRACKING
# ============================================================
#
# The scheduler runs every 30 seconds.
#
# Therefore, we MUST remember which notification has already
# received an email.
#
# IMPORTANT:
# We intentionally do NOT create a foreign-key relationship
# with notification_alarms.
#
# This prevents email tracking records from blocking the
# existing alarm deletion/reset functions.
#
# ============================================================


class EmailDelivery(db.Model):

    __tablename__ = "notification_email_deliveries"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    # NotificationAlarm ID.
    #
    # This is intentionally an Integer without a foreign key.
    #
    alarm_id = db.Column(
        db.Integer,
        nullable=False,
        unique=True,
        index=True
    )

    # Time at which the email was successfully sent.
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
# SMTP CONFIGURATION CHECK
# ============================================================


def smtp_configuration_ready():

    return bool(
        SMTP_SERVER
        and SMTP_PORT
        and SMTP_USERNAME
        and SMTP_PASSWORD
        and SMTP_FROM_EMAIL
    )


# ============================================================
# GET EMAIL DELIVERY RECORD
# ============================================================


def get_email_delivery(
    alarm_id
):

    return (
        EmailDelivery.query
        .filter_by(
            alarm_id=alarm_id
        )
        .first()
    )


# ============================================================
# GET / CREATE EMAIL DELIVERY RECORD
# ============================================================


def get_or_create_email_delivery(
    alarm_id
):

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

        return get_email_delivery(
            alarm_id
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

    recipient = (
        recipient
        or DEFAULT_RECIPIENT_EMAIL
    )

    message = EmailMessage()

    # --------------------------------------------------------
    # EMAIL HEADERS
    # --------------------------------------------------------

    message["From"] = (
        f"{SMTP_FROM_NAME} "
        f"<{SMTP_FROM_EMAIL}>"
    )

    message["To"] = recipient

    message["Subject"] = (
        f"🔔 Reminder: {title}"
    )

    # --------------------------------------------------------
    # EMAIL BODY
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # EMAIL HEADERS
    # --------------------------------------------------------

    message["From"] = (
        f"{SMTP_FROM_NAME} "
        f"<{SMTP_FROM_EMAIL}>"
    )

    message["To"] = recipient

    message["Subject"] = (
        f"🎂 Birthday Reminder: {name}"
    )

    # --------------------------------------------------------
    # EMAIL BODY
    # --------------------------------------------------------

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
# SEND EMAIL THROUGH GMAIL SMTP
# ============================================================


def send_email(
    message
):

    if not smtp_configuration_ready():

        print(
            "⚠️ SMTP configuration is incomplete."
        )

        return False

    try:

        print(
            "📧 Connecting to Gmail SMTP..."
        )

        with smtplib.SMTP(
            SMTP_SERVER,
            SMTP_PORT,
            timeout=30
        ) as smtp:

            # ------------------------------------------------
            # START TLS
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
            # SEND MESSAGE
            # ------------------------------------------------

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
# SEND DUE EMAIL NOTIFICATIONS
# ============================================================
#
# This function is called by scheduler.py every 30 seconds.
#
# It uses get_due_push_items() from notification_service.py
# so the email notification is based on the SAME due
# notification data used by the push notification system.
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

    try:

        # ----------------------------------------------------
        # Get the same due notification items used by
        # the existing push notification system.
        # ----------------------------------------------------

        items = get_due_push_items()

        if not items:

            print(
                "📧 No due email notifications."
            )

            return

        # ----------------------------------------------------
        # Process every due notification.
        # ----------------------------------------------------

        for alarm, user_id, payload in items:

            alarm_id = payload.get(
                "id"
            )

            if not alarm_id:

                continue

            # ------------------------------------------------
            # Check whether this notification already sent
            # an email.
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

            # =================================================
            # REMINDER EMAIL
            # =================================================

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

            # =================================================
            # BIRTHDAY EMAIL
            # =================================================

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
            # RECORD SUCCESSFUL EMAIL DELIVERY
            # ------------------------------------------------

            if success:

                delivery = (
                    get_or_create_email_delivery(
                        alarm_id
                    )
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

                # ------------------------------------------------
                # IMPORTANT:
                #
                # We do NOT create a successful delivery record
                # when sending fails.
                #
                # The next scheduler cycle can therefore retry.
                # ------------------------------------------------

                db.session.rollback()

                print(
                    f"⚠️ Email failed for alarm "
                    f"{alarm_id}. Will retry."
                )

    except Exception as error:

        print(
            "❌ Email scheduler error:"
        )

        print(
            f"   {error}"
        )

        db.session.rollback()


# ============================================================
# FORMAT DATE FOR EMAIL
# ============================================================


def format_email_date(
    value
):

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


# ============================================================
# FORMAT TIME FOR EMAIL
# ============================================================


def format_email_time(
    value
):

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
# MANUAL TEST EMAIL
# ============================================================
#
# This function is NOT automatically executed.
#
# It can be used later if we want a dedicated SMTP
# test endpoint.
#
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

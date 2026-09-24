"""
Resend Email Service
====================

Separate email delivery service for Bday Reminder.

IMPORTANT:
- Does NOT modify or replace Gmail SMTP.
- Uses Resend HTTPS API.
- Uses the same due notification data as notification_service.py.
- Has its own delivery tracking table.
- Retries automatically on the next scheduler cycle if sending fails.
"""

import os
import requests
from datetime import datetime

from database import db


# ============================================================
# RESEND CONFIGURATION
# ============================================================

RESEND_API_URL = "https://api.resend.com/emails"

RESEND_API_KEY = os.environ.get("RESEND_API_KEY", "").strip()

RESEND_FROM_EMAIL = os.environ.get(
    "RESEND_FROM_EMAIL",
    "onboarding@resend.dev"
).strip()

RESEND_FROM_NAME = os.environ.get(
    "RESEND_FROM_NAME",
    "Bday Reminder"
).strip()

RESEND_RECIPIENT_EMAIL = os.environ.get(
    "REMINDER_EMAIL",
    "visakanreminder@gmail.com"
).strip()


# ============================================================
# DELIVERY MODEL
# ============================================================

class ResendEmailDelivery(db.Model):
    """
    Keeps Resend delivery tracking separate from Gmail SMTP.

    This is intentional.

    Gmail SMTP and Resend are two independent delivery channels,
    so one channel being successful must NOT prevent the other
    channel from attempting delivery.
    """

    __tablename__ = "notification_resend_deliveries"

    id = db.Column(db.Integer, primary_key=True)

    alarm_id = db.Column(
        db.Integer,
        nullable=False,
        unique=True,
        index=True
    )

    resend_message_id = db.Column(
        db.String(255),
        nullable=True
    )

    last_sent_at = db.Column(
        db.DateTime,
        nullable=True
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False
    )


# ============================================================
# CONFIGURATION CHECK
# ============================================================

def resend_configuration_ready():
    """
    Check whether Resend has been configured correctly.
    """

    if not RESEND_API_KEY:
        print("⚠️ RESEND_API_KEY is not configured.")
        return False

    if not RESEND_FROM_EMAIL:
        print("⚠️ RESEND_FROM_EMAIL is not configured.")
        return False

    if not RESEND_RECIPIENT_EMAIL:
        print("⚠️ RESEND recipient email is not configured.")
        return False

    return True


# ============================================================
# DELIVERY RECORD
# ============================================================

def get_resend_delivery(alarm_id):
    """
    Get the Resend delivery record for an alarm.
    """

    return ResendEmailDelivery.query.filter_by(
        alarm_id=alarm_id
    ).first()


def get_or_create_resend_delivery(alarm_id):
    """
    Get an existing delivery record or create one.
    """

    delivery = get_resend_delivery(alarm_id)

    if delivery:
        return delivery

    delivery = ResendEmailDelivery(
        alarm_id=alarm_id
    )

    db.session.add(delivery)
    db.session.flush()

    return delivery


# ============================================================
# EMAIL HTML
# ============================================================

def build_reminder_email(item):
    """
    Build the same reminder email content from the
    notification payload.
    """

    title = item.get("title") or "Reminder"
    description = item.get("description") or ""
    place = item.get("place") or ""
    date_value = item.get("date") or ""
    time_value = item.get("time") or ""

    subject = f"🔔 Reminder: {title}"

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport"
              content="width=device-width, initial-scale=1.0">

        <title>{title}</title>
    </head>

    <body style="
        margin:0;
        padding:0;
        background:#f4f7fb;
        font-family:Arial,Helvetica,sans-serif;
    ">

        <div style="
            max-width:600px;
            margin:30px auto;
            background:white;
            border-radius:16px;
            overflow:hidden;
            box-shadow:0 4px 20px rgba(0,0,0,0.08);
        ">

            <div style="
                background:linear-gradient(135deg,#667eea,#764ba2);
                padding:25px;
                color:white;
                text-align:center;
            ">
                <h1 style="
                    margin:0;
                    font-size:26px;
                ">
                    🔔 Reminder
                </h1>
            </div>

            <div style="padding:30px;">

                <h2 style="
                    margin-top:0;
                    color:#222;
                ">
                    {title}
                </h2>

                <p style="
                    color:#555;
                    font-size:16px;
                    line-height:1.6;
                ">
                    Your reminder is due now.
                </p>

                <div style="
                    background:#f7f8fc;
                    border-radius:12px;
                    padding:20px;
                    margin-top:20px;
                ">

                    <p>
                        <strong>📅 Date:</strong>
                        {date_value}
                    </p>

                    <p>
                        <strong>⏰ Time:</strong>
                        {time_value}
                    </p>

                    {
                        f'''
                        <p>
                            <strong>📍 Place:</strong>
                            {place}
                        </p>
                        '''
                        if place else ""
                    }

                    {
                        f'''
                        <p>
                            <strong>📝 Description:</strong>
                            {description}
                        </p>
                        '''
                        if description else ""
                    }

                </div>

                <p style="
                    margin-top:30px;
                    color:#777;
                    font-size:13px;
                    text-align:center;
                ">
                    Visakan Reminder
                </p>

            </div>

        </div>

    </body>
    </html>
    """

    return subject, html


def build_birthday_email(item):
    """
    Build birthday email content.
    """

    name = item.get("name") or "Someone"
    birthday = item.get("birthday") or ""
    date_value = item.get("date") or ""
    time_value = item.get("time") or ""

    subject = f"🎂 Birthday Reminder: {name}"

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport"
              content="width=device-width, initial-scale=1.0">

        <title>Birthday Reminder</title>
    </head>

    <body style="
        margin:0;
        padding:0;
        background:#f4f7fb;
        font-family:Arial,Helvetica,sans-serif;
    ">

        <div style="
            max-width:600px;
            margin:30px auto;
            background:white;
            border-radius:16px;
            overflow:hidden;
            box-shadow:0 4px 20px rgba(0,0,0,0.08);
        ">

            <div style="
                background:linear-gradient(135deg,#ff758c,#ff7eb3);
                padding:25px;
                color:white;
                text-align:center;
            ">
                <h1 style="
                    margin:0;
                    font-size:28px;
                ">
                    🎂 Birthday Reminder
                </h1>
            </div>

            <div style="padding:30px;text-align:center;">

                <h2 style="
                    color:#222;
                    font-size:25px;
                ">
                    Today is {name}'s Birthday! 🎉
                </h2>

                <p style="
                    color:#555;
                    font-size:17px;
                ">
                    Don't forget to wish <strong>{name}</strong>
                    a happy birthday!
                </p>

                <div style="
                    background:#fff5f7;
                    border-radius:12px;
                    padding:20px;
                    margin-top:25px;
                ">

                    <p>
                        <strong>🎂 Birthday:</strong>
                        {birthday}
                    </p>

                    <p>
                        <strong>📅 Date:</strong>
                        {date_value}
                    </p>

                    <p>
                        <strong>⏰ Reminder Time:</strong>
                        {time_value}
                    </p>

                </div>

                <p style="
                    margin-top:30px;
                    color:#777;
                    font-size:13px;
                ">
                    Visakan Reminder
                </p>

            </div>

        </div>

    </body>
    </html>
    """

    return subject, html


# ============================================================
# SEND THROUGH RESEND
# ============================================================

def send_resend_email(subject, html):
    """
    Send one email through the Resend HTTPS API.

    Returns:
        (success, message_id)
    """

    if not resend_configuration_ready():
        return False, None

    payload = {
        "from": f"{RESEND_FROM_NAME} <{RESEND_FROM_EMAIL}>",
        "to": [RESEND_RECIPIENT_EMAIL],
        "subject": subject,
        "html": html
    }

    headers = {
        "Authorization": f"Bearer {RESEND_API_KEY}",
        "Content-Type": "application/json"
    }

    try:

        print("📨 Sending email through Resend...")
        print(f"   To: {RESEND_RECIPIENT_EMAIL}")
        print(f"   From: {RESEND_FROM_EMAIL}")

        response = requests.post(
            RESEND_API_URL,
            headers=headers,
            json=payload,
            timeout=15
        )

        if response.status_code >= 200 and response.status_code < 300:

            try:
                response_data = response.json()
            except Exception:
                response_data = {}

            message_id = response_data.get("id")

            print("✅ Resend email sent successfully.")

            if message_id:
                print(f"   Resend ID: {message_id}")

            return True, message_id

        print("❌ Resend email failed.")
        print(f"   HTTP Status: {response.status_code}")
        print(f"   Response: {response.text[:1000]}")

        return False, None

    except requests.Timeout:
        print("❌ Resend request timed out.")
        return False, None

    except requests.RequestException as error:
        print("❌ Resend connection error:")
        print(f"   {error}")
        return False, None

    except Exception as error:
        print("❌ Unexpected Resend error:")
        print(f"   {error}")
        return False, None


# ============================================================
# SEND DUE EMAIL NOTIFICATIONS
# ============================================================

def send_due_resend_notifications():
    """
    Check the same due notification queue used by
    the existing notification system.

    Resend has its own delivery tracking, so Gmail SMTP
    and Resend operate independently.
    """

    print("📨 Checking due Resend email notifications...")

    if not resend_configuration_ready():
        print("⚠️ Resend is not configured.")
        return

    try:
        from notification_service import get_due_push_items

        items = get_due_push_items()

        if not items:
            print("📭 No due Resend email notifications.")
            return

        print(
            f"📬 Found {len(items)} due "
            f"notification(s) for Resend."
        )

        # IMPORTANT:
        # get_due_push_items() returns:
        # (alarm, user_id, payload)

        for alarm, user_id, payload in items:

            alarm_id = payload.get("id")
            notification_type = payload.get("type")

            if not alarm_id:
                print("⚠️ Skipping notification without alarm ID.")
                continue

            try:

                # ------------------------------------------------
                # CHECK RESEND DELIVERY ONLY
                # ------------------------------------------------

                delivery = get_resend_delivery(alarm_id)

                if delivery and delivery.last_sent_at:
                    print(
                        f"📨 Resend email already sent "
                        f"for alarm {alarm_id}."
                    )
                    continue

                # ------------------------------------------------
                # BUILD EMAIL
                # ------------------------------------------------

                if notification_type == "reminder":

                    subject, html = build_reminder_email(
                        payload
                    )

                elif notification_type == "birthday":

                    subject, html = build_birthday_email(
                        payload
                    )

                else:

                    print(
                        f"⚠️ Unknown notification type: "
                        f"{notification_type}"
                    )
                    continue

                # ------------------------------------------------
                # SEND THROUGH RESEND
                # ------------------------------------------------

                success, message_id = send_resend_email(
                    subject,
                    html
                )

                if success:

                    delivery = get_or_create_resend_delivery(
                        alarm_id
                    )

                    if delivery:

                        delivery.resend_message_id = message_id
                        delivery.last_sent_at = datetime.utcnow()

                        db.session.commit()

                        print(
                            f"✅ Resend delivery recorded "
                            f"for alarm {alarm_id}."
                        )

                else:

                    db.session.rollback()

                    print(
                        f"🔁 Resend will retry alarm "
                        f"{alarm_id} on the next check."
                    )

            except Exception as error:

                db.session.rollback()

                print(
                    f"❌ Error processing Resend alarm "
                    f"{alarm_id}:"
                )
                print(f"   {error}")

    except Exception as error:

        db.session.rollback()

        print("❌ Resend notification check failed:")
        print(f"   {error}")
# ============================================================
# TEST EMAIL
# ============================================================

def send_test_resend_email():
    """
    Send a manual test email through Resend.
    """

    subject = "✅ Visakan Reminder - Resend Test"

    html = """
    <!DOCTYPE html>
    <html>

    <body style="
        font-family:Arial,Helvetica,sans-serif;
        padding:30px;
    ">

        <h2>✅ Resend is working!</h2>

        <p>
            This is a test email from
            <strong>Visakan Reminder</strong>.
        </p>

        <p>
            Resend HTTPS email delivery is configured
            successfully.
        </p>

    </body>

    </html>
    """

    return send_resend_email(
        subject,
        html
    )

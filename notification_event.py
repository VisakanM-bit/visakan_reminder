# ============================================================
# BDAY REMINDER
# NOTIFICATION EVENT
# ============================================================
#
# Central notification event layer.
#
# One NotificationEvent represents ONE reminder/birthday event.
#
# The same event can later be delivered independently through:
#
#   1. Browser Web Push
#   2. Gmail SMTP
#   3. Resend
#
# Each delivery channel has its own status so that a failure
# in one channel does not affect the others.
#
# IMPORTANT:
# This file does NOT replace the existing notification system.
# It provides the central event record that we will connect to
# the existing notification services in the next step.
# ============================================================


from datetime import datetime

from database import db


# ============================================================
# NOTIFICATION EVENT MODEL
# ============================================================

class NotificationEvent(db.Model):

    __tablename__ = "notification_events"

    # --------------------------------------------------------
    # PRIMARY KEY
    # --------------------------------------------------------

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    # --------------------------------------------------------
    # USER
    # --------------------------------------------------------
    #
    # The user who owns this notification.
    # --------------------------------------------------------

    user_id = db.Column(
        db.Integer,
        nullable=False,
        index=True
    )

    # --------------------------------------------------------
    # ALARM
    # --------------------------------------------------------
    #
    # Links this event to the NotificationAlarm created by
    # notification_service.py.
    #
    # One alarm should produce one notification event.
    # --------------------------------------------------------

    alarm_id = db.Column(
        db.Integer,
        nullable=False,
        unique=True,
        index=True
    )

    # --------------------------------------------------------
    # NOTIFICATION TYPE
    # --------------------------------------------------------
    #
    # Examples:
    #
    #   reminder
    #   birthday
    # --------------------------------------------------------

    notification_type = db.Column(
        db.String(50),
        nullable=False,
        index=True
    )

    # --------------------------------------------------------
    # SOURCE ID
    # --------------------------------------------------------
    #
    # Original Reminder.id or Birthday.id.
    # --------------------------------------------------------

    source_id = db.Column(
        db.Integer,
        nullable=False,
        index=True
    )

    # --------------------------------------------------------
    # TITLE
    # --------------------------------------------------------

    title = db.Column(
        db.String(255),
        nullable=True
    )

    # --------------------------------------------------------
    # MESSAGE
    # --------------------------------------------------------

    message = db.Column(
        db.Text,
        nullable=True
    )

    # --------------------------------------------------------
    # DESCRIPTION
    # --------------------------------------------------------

    description = db.Column(
        db.Text,
        nullable=True
    )

    # --------------------------------------------------------
    # PLACE
    # --------------------------------------------------------

    place = db.Column(
        db.String(255),
        nullable=True
    )

    # --------------------------------------------------------
    # EVENT DATE
    # --------------------------------------------------------

    event_date = db.Column(
        db.String(20),
        nullable=True
    )

    # --------------------------------------------------------
    # EVENT TIME
    # --------------------------------------------------------

    event_time = db.Column(
        db.String(20),
        nullable=True
    )

    # --------------------------------------------------------
    # BIRTHDAY DISPLAY DATE
    # --------------------------------------------------------
    #
    # Used only for birthday notifications.
    #
    # Example:
    #   "08 October"
    # --------------------------------------------------------

    birthday = db.Column(
        db.String(50),
        nullable=True
    )

    # --------------------------------------------------------
    # COMPLETE PAYLOAD
    # --------------------------------------------------------
    #
    # Stores the original notification information.
    #
    # This gives us a permanent copy of exactly what was
    # supposed to be delivered.
    # --------------------------------------------------------

    payload = db.Column(
        db.JSON,
        nullable=True
    )

    # ========================================================
    # DELIVERY STATUS - BROWSER PUSH
    # ========================================================

    push_status = db.Column(
        db.String(20),
        nullable=False,
        default="PENDING"
    )

    push_attempts = db.Column(
        db.Integer,
        nullable=False,
        default=0
    )

    push_sent_at = db.Column(
        db.DateTime,
        nullable=True
    )

    push_error = db.Column(
        db.Text,
        nullable=True
    )

    # ========================================================
    # DELIVERY STATUS - GMAIL SMTP
    # ========================================================

    gmail_status = db.Column(
        db.String(20),
        nullable=False,
        default="PENDING"
    )

    gmail_attempts = db.Column(
        db.Integer,
        nullable=False,
        default=0
    )

    gmail_sent_at = db.Column(
        db.DateTime,
        nullable=True
    )

    gmail_error = db.Column(
        db.Text,
        nullable=True
    )

    # ========================================================
    # DELIVERY STATUS - RESEND
    # ========================================================

    resend_status = db.Column(
        db.String(20),
        nullable=False,
        default="PENDING"
    )

    resend_attempts = db.Column(
        db.Integer,
        nullable=False,
        default=0
    )

    resend_sent_at = db.Column(
        db.DateTime,
        nullable=True
    )

    resend_error = db.Column(
        db.Text,
        nullable=True
    )

    # --------------------------------------------------------
    # CREATED TIME
    # --------------------------------------------------------

    created_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
        index=True
    )

    # --------------------------------------------------------
    # UPDATED TIME
    # --------------------------------------------------------

    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    # ========================================================
    # REPRESENTATION
    # ========================================================

    def __repr__(self):

        return (
            f"<NotificationEvent "
            f"id={self.id} "
            f"type={self.notification_type} "
            f"alarm={self.alarm_id}>"
        )


# ============================================================
# CREATE NOTIFICATION EVENT
# ============================================================

def create_notification_event(
    alarm,
    user_id,
    payload
):
    """
    Create one central NotificationEvent for an alarm.

    If the event already exists, the existing event is returned.

    This makes the function safe when multiple scheduler jobs
    check the same notification.
    """

    if alarm is None:

        return None

    if not payload:

        return None

    # --------------------------------------------------------
    # CHECK WHETHER EVENT ALREADY EXISTS
    # --------------------------------------------------------

    existing_event = (

        NotificationEvent.query

        .filter_by(
            alarm_id=alarm.id
        )

        .first()

    )

    if existing_event:

        return existing_event

    # --------------------------------------------------------
    # READ PAYLOAD
    # --------------------------------------------------------

    notification_type = (
        payload.get("type")
        or "reminder"
    )

    source_id = payload.get(
        "source_id"
    )

    title = payload.get(
        "title"
    )

    message = payload.get(
        "message"
    )

    description = payload.get(
        "description"
    )

    place = payload.get(
        "place"
    )

    event_date = payload.get(
        "date"
    )

    event_time = payload.get(
        "time"
    )

    birthday = payload.get(
        "birthday"
    )

    # --------------------------------------------------------
    # CREATE EVENT
    # --------------------------------------------------------

    event = NotificationEvent(

        user_id=user_id,

        alarm_id=alarm.id,

        notification_type=notification_type,

        source_id=source_id,

        title=title,

        message=message,

        description=description,

        place=place,

        event_date=event_date,

        event_time=event_time,

        birthday=birthday,

        payload=payload,

        push_status="PENDING",

        gmail_status="PENDING",

        resend_status="PENDING"

    )

    # --------------------------------------------------------
    # SAVE
    # --------------------------------------------------------

    try:

        db.session.add(
            event
        )

        db.session.commit()

        return event

    except Exception:

        db.session.rollback()

        # ----------------------------------------------------
        # RACE CONDITION PROTECTION
        # ----------------------------------------------------
        #
        # Another scheduler/process may have created the
        # same event at exactly the same time.
        # ----------------------------------------------------

        existing_event = (

            NotificationEvent.query

            .filter_by(
                alarm_id=alarm.id
            )

            .first()

        )

        if existing_event:

            return existing_event

        raise


# ============================================================
# GET EVENT BY ALARM
# ============================================================

def get_notification_event(
    alarm_id
):
    """
    Get the central notification event using its alarm ID.
    """

    if not alarm_id:

        return None

    return (

        NotificationEvent.query

        .filter_by(
            alarm_id=alarm_id
        )

        .first()

    )


# ============================================================
# MARK PUSH AS SENT
# ============================================================

def mark_push_sent(
    event
):

    if not event:

        return

    event.push_status = "SENT"

    event.push_attempts = (
        (event.push_attempts or 0)
        + 1
    )

    event.push_sent_at = datetime.utcnow()

    event.push_error = None

    db.session.commit()


# ============================================================
# MARK PUSH AS FAILED
# ============================================================

def mark_push_failed(
    event,
    error_message
):

    if not event:

        return

    event.push_status = "FAILED"

    event.push_attempts = (
        (event.push_attempts or 0)
        + 1
    )

    event.push_error = str(
        error_message
    )[:5000]

    db.session.commit()


# ============================================================
# MARK GMAIL AS SENT
# ============================================================

def mark_gmail_sent(
    event
):

    if not event:

        return

    event.gmail_status = "SENT"

    event.gmail_attempts = (
        (event.gmail_attempts or 0)
        + 1
    )

    event.gmail_sent_at = datetime.utcnow()

    event.gmail_error = None

    db.session.commit()


# ============================================================
# MARK GMAIL AS FAILED
# ============================================================

def mark_gmail_failed(
    event,
    error_message
):

    if not event:

        return

    event.gmail_status = "FAILED"

    event.gmail_attempts = (
        (event.gmail_attempts or 0)
        + 1
    )

    event.gmail_error = str(
        error_message
    )[:5000]

    db.session.commit()


# ============================================================
# MARK RESEND AS SENT
# ============================================================

def mark_resend_sent(
    event
):

    if not event:

        return

    event.resend_status = "SENT"

    event.resend_attempts = (
        (event.resend_attempts or 0)
        + 1
    )

    event.resend_sent_at = datetime.utcnow()

    event.resend_error = None

    db.session.commit()


# ============================================================
# MARK RESEND AS FAILED
# ============================================================

def mark_resend_failed(
    event,
    error_message
):

    if not event:

        return

    event.resend_status = "FAILED"

    event.resend_attempts = (
        (event.resend_attempts or 0)
        + 1
    )

    event.resend_error = str(
        error_message
    )[:5000]

    db.session.commit()


# ============================================================
# GET PENDING EVENTS
# ============================================================

def get_pending_notification_events(
    limit=100
):
    """
    Return notification events where at least one delivery
    channel is still pending or failed.

    This will be used later by the independent delivery
    workers.
    """

    return (

        NotificationEvent.query

        .filter(

            db.or_(

                NotificationEvent.push_status.in_(
                    ["PENDING", "FAILED"]
                ),

                NotificationEvent.gmail_status.in_(
                    ["PENDING", "FAILED"]
                ),

                NotificationEvent.resend_status.in_(
                    ["PENDING", "FAILED"]
                )

            )

        )

        .order_by(
            NotificationEvent.created_at.asc()
        )

        .limit(limit)

        .all()

    )


# ============================================================
# CHECK WHETHER ALL CHANNELS ARE COMPLETE
# ============================================================

def notification_event_completed(
    event
):
    """
    Returns True only when all three delivery channels
    have completed successfully.
    """

    if not event:

        return False

    return (

        event.push_status == "SENT"

        and

        event.gmail_status == "SENT"

        and

        event.resend_status == "SENT"

    )

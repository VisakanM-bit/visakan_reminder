# ============================================================
# BDAY REMINDER
# PERSISTENT NOTIFICATION / ALARM SERVICE
# ============================================================

import json
import os

from datetime import datetime, date, time, timedelta
from zoneinfo import ZoneInfo

from flask import Blueprint, jsonify, request
from flask_login import current_user, login_required
from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError

from pywebpush import webpush, WebPushException

from database import db
from database.models import (
    Birthday,
    Reminder,
    PushSubscription
)


# ============================================================
# BLUEPRINT
# ============================================================

notification_bp = Blueprint(
    "notifications",
    __name__
)


# ============================================================
# SETTINGS
# ============================================================

IST = ZoneInfo("Asia/Kolkata")

# Birthday model has no time field.
# Birthday notification starts at 09:00 AM.
BIRTHDAY_NOTIFICATION_TIME = time(
    9,
    0
)

# Backend repeat interval.
REPEAT_MINUTES = 5


# ============================================================
# VAPID SETTINGS
# ============================================================

VAPID_PUBLIC_KEY = os.environ.get(
    "VAPID_PUBLIC_KEY",
    ""
)

VAPID_PRIVATE_KEY = os.environ.get(
    "VAPID_PRIVATE_KEY",
    ""
)

VAPID_CLAIM_EMAIL = os.environ.get(
    "VAPID_CLAIM_EMAIL",
    ""
)


# ============================================================
# PERSISTENT ALARM MODEL
# ============================================================

class NotificationAlarm(db.Model):

    __tablename__ = "notification_alarms"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False,
        index=True
    )

    # reminder / birthday
    kind = db.Column(
        db.String(20),
        nullable=False
    )

    # ID of Reminder or Birthday
    source_id = db.Column(
        db.Integer,
        nullable=False
    )

    # Identifies one occurrence.
    #
    # Reminder:
    # reminder:12:2026-08-18:19:00:00
    #
    # Birthday:
    # birthday:5:2026-08-18
    occurrence_key = db.Column(
        db.String(150),
        nullable=False
    )

    # Alarm lifecycle
    active = db.Column(
        db.Boolean,
        nullable=False,
        default=False
    )

    stopped = db.Column(
        db.Boolean,
        nullable=False,
        default=False
    )

    # Backend notification timing
    last_notified_at = db.Column(
        db.DateTime,
        nullable=True
    )

    started_at = db.Column(
        db.DateTime,
        nullable=True
    )

    created_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow
    )

    __table_args__ = (
        db.UniqueConstraint(
            "user_id",
            "kind",
            "source_id",
            "occurrence_key",
            name="uq_notification_alarm_occurrence"
        ),
    )


# ============================================================
# PUSH DELIVERY TRACKING
# ============================================================
# Separate table so we do NOT need to modify the existing
# notification_alarms table.
#
# This prevents the scheduler from interfering with the
# existing in-page notification timing.
# ============================================================

class PushDelivery(db.Model):

    __tablename__ = "notification_push_deliveries"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    alarm_id = db.Column(
        db.Integer,
        db.ForeignKey("notification_alarms.id"),
        nullable=False,
        unique=True,
        index=True
    )

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
# INDIA TIME
# ============================================================

def get_india_now():

    return (
        datetime
        .now(IST)
        .replace(
            tzinfo=None
        )
    )


# ============================================================
# GET / CREATE ALARM
# ============================================================

def get_or_create_alarm(
    user_id,
    kind,
    source_id,
    occurrence_key
):

    alarm = (
        NotificationAlarm.query
        .filter_by(
            user_id=user_id,
            kind=kind,
            source_id=source_id,
            occurrence_key=occurrence_key
        )
        .first()
    )

    if alarm:
        return alarm

    alarm = NotificationAlarm(
        user_id=user_id,
        kind=kind,
        source_id=source_id,
        occurrence_key=occurrence_key,
        active=False,
        stopped=False
    )

    db.session.add(alarm)

    try:

        # Use a SAVEPOINT so a concurrent insert does not
        # roll back the whole request transaction.
        with db.session.begin_nested():
            db.session.flush()

        return alarm

    except IntegrityError:

        # Another request/scheduler worker may have created
        # this exact alarm at the same time.
        return (
            NotificationAlarm.query
            .filter_by(
                user_id=user_id,
                kind=kind,
                source_id=source_id,
                occurrence_key=occurrence_key
            )
            .first()
        )


# ============================================================
# CLAIM NOTIFICATION
#
# This controls the existing in-page notification system.
# ============================================================

def claim_notification(
    alarm_id,
    now
):

    alarm = db.session.get(
        NotificationAlarm,
        alarm_id
    )

    if not alarm:
        return None

    if alarm.stopped:
        return None

    cutoff = (
        now -
        timedelta(
            minutes=REPEAT_MINUTES
        )
    )

    # --------------------------------------------------------
    # FIRST NOTIFICATION
    # --------------------------------------------------------

    if not alarm.active:

        updated = (
            NotificationAlarm.query
            .filter(
                NotificationAlarm.id == alarm_id,
                NotificationAlarm.stopped.is_(False),
                NotificationAlarm.active.is_(False)
            )
            .update(
                {
                    "active": True,
                    "started_at": now,
                    "last_notified_at": now
                },
                synchronize_session=False
            )
        )

    # --------------------------------------------------------
    # REPEAT NOTIFICATION
    # --------------------------------------------------------

    else:

        updated = (
            NotificationAlarm.query
            .filter(
                NotificationAlarm.id == alarm_id,
                NotificationAlarm.stopped.is_(False),
                NotificationAlarm.active.is_(True),
                or_(
                    NotificationAlarm.last_notified_at.is_(None),
                    NotificationAlarm.last_notified_at <= cutoff
                )
            )
            .update(
                {
                    "last_notified_at": now
                },
                synchronize_session=False
            )
        )

    if not updated:

        db.session.expire_all()

        return None

    return db.session.get(
        NotificationAlarm,
        alarm_id
    )


# ============================================================
# NEXT BIRTHDAY
# ============================================================

def get_next_birthday_date(
    birthday,
    today
):

    month = birthday.birthday.month
    day = birthday.birthday.day

    try:

        occurrence = date(
            today.year,
            month,
            day
        )

    except ValueError:

        # Handle February 29 safely.
        if (
            month == 2
            and day == 29
        ):

            occurrence = date(
                today.year,
                2,
                28
            )

        else:

            return None

    if occurrence < today:

        try:

            occurrence = date(
                today.year + 1,
                month,
                day
            )

        except ValueError:

            if (
                month == 2
                and day == 29
            ):

                occurrence = date(
                    today.year + 1,
                    2,
                    28
                )

            else:

                return None

    return occurrence


# ============================================================
# REMINDER PAYLOAD
# ============================================================

def reminder_payload(
    alarm,
    reminder
):

    return {

        "id":
            alarm.id,

        "type":
            "reminder",

        "source_id":
            reminder.id,

        "title":
            reminder.title or "Reminder",

        "description":
            reminder.description or "",

        "place":
            reminder.place or "",

        "date":
            reminder.reminder_date.isoformat(),

        "time":
            reminder.reminder_time.strftime(
                "%H:%M"
            ),

        "message":
            (
                f"{reminder.title or 'Reminder'} "
                "is due."
            ),

        "alarm_active":
            True

    }


# ============================================================
# BIRTHDAY PAYLOAD
# ============================================================

def birthday_payload(
    alarm,
    birthday,
    occurrence
):

    return {

        "id":
            alarm.id,

        "type":
            "birthday",

        "source_id":
            birthday.id,

        "name":
            birthday.name,

        "date":
            occurrence.isoformat(),

        "time":
            BIRTHDAY_NOTIFICATION_TIME.strftime(
                "%H:%M"
            ),

        "birthday":
            birthday.birthday.strftime(
                "%d %B"
            ),

        "message":
            (
                f"Today is "
                f"{birthday.name}'s birthday!"
            ),

        "alarm_active":
            True

    }


# ============================================================
# PUSH DELIVERY CHECK
# ============================================================

def push_is_due(
    alarm,
    now
):

    delivery = (
        PushDelivery.query
        .filter_by(
            alarm_id=alarm.id
        )
        .first()
    )

    if not delivery:

        return True, None

    if not delivery.last_sent_at:

        return True, delivery

    cutoff = (
        now -
        timedelta(
            minutes=REPEAT_MINUTES
        )
    )

    if delivery.last_sent_at <= cutoff:

        return True, delivery

    return False, delivery


# ============================================================
# CREATE / GET PUSH DELIVERY
# ============================================================

def get_or_create_push_delivery(
    alarm_id
):

    delivery = (
        PushDelivery.query
        .filter_by(
            alarm_id=alarm_id
        )
        .first()
    )

    if delivery:

        return delivery

    delivery = PushDelivery(
        alarm_id=alarm_id,
        last_sent_at=None
    )

    db.session.add(
        delivery
    )

    try:

        with db.session.begin_nested():
            db.session.flush()

        return delivery

    except IntegrityError:

        return (
            PushDelivery.query
            .filter_by(
                alarm_id=alarm_id
            )
            .first()
        )


# ============================================================
# GET DUE ALARMS FOR PUSH
# ============================================================

def get_due_push_items():

    now = get_india_now()

    items = []

    # ========================================================
    # REMINDERS
    # ========================================================

    reminders = (
        Reminder.query
        .filter_by(
            status="pending"
        )
        .filter(
            Reminder.reminder_date <= now.date()
        )
        .all()
    )

    for reminder in reminders:

        if (
            not reminder.reminder_date
            or not reminder.reminder_time
        ):

            continue

        scheduled = datetime.combine(
            reminder.reminder_date,
            reminder.reminder_time
        )

        if now < scheduled:

            continue

        occurrence_key = (
            "reminder:"
            f"{reminder.id}:"
            f"{reminder.reminder_date.isoformat()}:"
            f"{reminder.reminder_time.strftime('%H:%M:%S')}"
        )

        alarm = get_or_create_alarm(
            reminder.user_id,
            "reminder",
            reminder.id,
            occurrence_key
        )

        if not alarm:

            continue

        if alarm.stopped:

            continue

        payload = reminder_payload(
            alarm,
            reminder
        )

        items.append(
            (
                alarm,
                reminder.user_id,
                payload
            )
        )

    # ========================================================
    # BIRTHDAYS
    # ========================================================

    birthdays = (
        Birthday.query
        .all()
    )

    for birthday in birthdays:

        if not birthday.birthday:

            continue

        occurrence = get_next_birthday_date(
            birthday,
            now.date()
        )

        if occurrence != now.date():

            continue

        scheduled = datetime.combine(
            occurrence,
            BIRTHDAY_NOTIFICATION_TIME
        )

        if now < scheduled:

            continue

        occurrence_key = (
            "birthday:"
            f"{birthday.id}:"
            f"{occurrence.isoformat()}"
        )

        alarm = get_or_create_alarm(
            birthday.user_id,
            "birthday",
            birthday.id,
            occurrence_key
        )

        if not alarm:

            continue

        if alarm.stopped:

            continue

        payload = birthday_payload(
            alarm,
            birthday,
            occurrence
        )

        items.append(
            (
                alarm,
                birthday.user_id,
                payload
            )
        )

    return items


# ============================================================
# SEND DUE PUSH NOTIFICATIONS
#
# Called by scheduler.py.
#
# IMPORTANT:
# This does NOT claim the normal notification alarm.
#
# Therefore:
#
# 1. Existing page notification continues working.
# 2. Push notification works when app is closed.
# ============================================================

def send_due_push_notifications():

    now = get_india_now()

    try:

        items = get_due_push_items()

        for alarm, user_id, payload in items:

            should_send, delivery = push_is_due(
                alarm,
                now
            )

            if not should_send:

                continue

            subscriptions = (
                PushSubscription.query
                .filter_by(
                    user_id=user_id,
                    active=True
                )
                .all()
            )

            if not subscriptions:

                continue

            sent_any = False

            for subscription in subscriptions:

                success = send_web_push(
                    subscription,
                    {
                        "title":
                            payload.get(
                                "title",
                                "Birthday Reminder"
                            )
                        if payload.get("type") == "reminder"
                        else "Birthday Reminder",

                        "body":
                            payload.get(
                                "message",
                                "You have a reminder."
                            ),

                        "type":
                            payload.get(
                                "type"
                            ),

                        "alarm_id":
                            payload.get(
                                "id"
                            ),

                        "source_id":
                            payload.get(
                                "source_id"
                            ),

                        "url":
                            "/"
                    }
                )

                if success:

                    sent_any = True

            if sent_any:

                if not delivery:

                    delivery = get_or_create_push_delivery(
                        alarm.id
                    )

                if delivery:

                    delivery.last_sent_at = now

        db.session.commit()

    except Exception as error:

        print(
            "❌ Push scheduler error:",
            error
        )

        db.session.rollback()


# ============================================================
# DUE NOTIFICATIONS
# ============================================================

@notification_bp.get(
    "/api/notifications/due"
)
@login_required
def due_notifications():

    now = get_india_now()

    notifications = []

    # ========================================================
    # TIME REMINDERS
    # ========================================================

    reminders = (
        Reminder.query
        .filter_by(
            user_id=current_user.id,
            status="pending"
        )
        .filter(
            Reminder.reminder_date <= now.date()
        )
        .all()
    )

    for reminder in reminders:

        if (
            not reminder.reminder_date
            or not reminder.reminder_time
        ):

            continue

        scheduled = datetime.combine(
            reminder.reminder_date,
            reminder.reminder_time
        )

        # Not due yet
        if now < scheduled:

            continue

        occurrence_key = (
            "reminder:"
            f"{reminder.id}:"
            f"{reminder.reminder_date.isoformat()}:"
            f"{reminder.reminder_time.strftime('%H:%M:%S')}"
        )

        alarm = get_or_create_alarm(
            current_user.id,
            "reminder",
            reminder.id,
            occurrence_key
        )

        if not alarm:

            continue

        claimed = claim_notification(
            alarm.id,
            now
        )

        if claimed:

            notifications.append(
                reminder_payload(
                    claimed,
                    reminder
                )
            )

    # ========================================================
    # BIRTHDAYS
    # ========================================================

    birthdays = (
        Birthday.query
        .filter_by(
            user_id=current_user.id
        )
        .all()
    )

    for birthday in birthdays:

        if not birthday.birthday:

            continue

        occurrence = get_next_birthday_date(
            birthday,
            now.date()
        )

        if occurrence != now.date():

            continue

        scheduled = datetime.combine(
            occurrence,
            BIRTHDAY_NOTIFICATION_TIME
        )

        # Birthday alarm starts at 09:00 AM.
        if now < scheduled:

            continue

        occurrence_key = (
            "birthday:"
            f"{birthday.id}:"
            f"{occurrence.isoformat()}"
        )

        alarm = get_or_create_alarm(
            current_user.id,
            "birthday",
            birthday.id,
            occurrence_key
        )

        if not alarm:

            continue

        claimed = claim_notification(
            alarm.id,
            now
        )

        if claimed:

            notifications.append(
                birthday_payload(
                    claimed,
                    birthday,
                    occurrence
                )
            )

    # ========================================================
    # SAVE BACKEND STATE
    # ========================================================

    db.session.commit()

    return jsonify({
        "success":
            True,

        "notifications":
            notifications
    })


# ============================================================
# STOP
# ============================================================

@notification_bp.post(
    "/api/notifications/<int:alarm_id>/stop"
)
@login_required
def stop_notification(
    alarm_id
):

    alarm = (
        NotificationAlarm.query
        .filter_by(
            id=alarm_id,
            user_id=current_user.id
        )
        .first_or_404()
    )

    alarm.stopped = True
    alarm.active = False

    db.session.commit()

    return jsonify({
        "success":
            True,

        "id":
            alarm.id,

        "stopped":
            True
    })


# ============================================================
# STOP ACTIVE REMINDER ALARMS
# ============================================================

def stop_active_alarms_for_reminder(
    reminder_id,
    user_id
):

    alarms = (
        NotificationAlarm.query
        .filter_by(
            source_id=reminder_id,
            user_id=user_id,
            kind="reminder",
            active=True
        )
        .all()
    )

    for alarm in alarms:

        alarm.stopped = True
        alarm.active = False


# ============================================================
# RESET REMINDER ALARMS
#
# Used when a reminder is edited.
# The new date/time becomes a fresh schedule.
# ============================================================

def reset_alarms_for_reminder(
    reminder_id,
    user_id
):

    alarm_ids = (
        db.session.query(NotificationAlarm.id)
        .filter_by(
            source_id=reminder_id,
            user_id=user_id,
            kind="reminder"
        )
        .subquery()
    )

    (
        PushDelivery.query
        .filter(
            PushDelivery.alarm_id.in_(alarm_ids)
        )
        .delete(
            synchronize_session=False
        )
    )

    (
        NotificationAlarm.query
        .filter_by(
            source_id=reminder_id,
            user_id=user_id,
            kind="reminder"
        )
        .delete(
            synchronize_session=False
        )
    )


# ============================================================
# RESET BIRTHDAY ALARMS
#
# Used when birthday details/date are edited.
# ============================================================

def reset_alarms_for_birthday(
    birthday_id,
    user_id
):

    (
        NotificationAlarm.query
        .filter_by(
            source_id=birthday_id,
            user_id=user_id,
            kind="birthday"
        )
        .delete(
            synchronize_session=False
        )
    )

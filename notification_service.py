# ============================================================
# BDAY REMINDER
# PERSISTENT NOTIFICATION / ALARM SERVICE
# ============================================================

from datetime import datetime, date, time, timedelta
from zoneinfo import ZoneInfo

from flask import Blueprint, jsonify
from flask_login import current_user, login_required
from sqlalchemy import or_

from database import db
from database.models import Birthday, Reminder


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
# Per the agreed specification, use 09:00 AM.
BIRTHDAY_NOTIFICATION_TIME = time(
    9,
    0
)

# Backend controls the repeat interval.
REPEAT_MINUTES = 5


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


    db.session.add(
        alarm
    )


    try:

        db.session.flush()

        return alarm


    except Exception:

        db.session.rollback()


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
# IMPORTANT:
# The database decides whether a notification is allowed.
#
# Frontend polling frequency does NOT control the 5-minute
# repeat interval.
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
                NotificationAlarm.id
                == alarm_id,

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

                NotificationAlarm.id
                == alarm_id,

                NotificationAlarm.stopped.is_(False),

                NotificationAlarm.active.is_(True),

                or_(

                    NotificationAlarm
                    .last_notified_at
                    .is_(None),

                    NotificationAlarm
                    .last_notified_at
                    <= cutoff

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

        # Handle Feb 29 safely

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

            Reminder.reminder_date
            <= now.date()

        )

        .all()

    )


    for reminder in reminders:


        if (
            not reminder.reminder_date
            or
            not reminder.reminder_time
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
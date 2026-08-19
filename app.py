# ============================================================
# BDAY REMINDER
# COMPLETE APPLICATION
#
# Database:
# - Render + TiDB Cloud through DATABASE_URL
# - Local SQLite fallback
#
# Existing functionality:
# - Login
# - Register
# - Logout
# - Dashboard
# - Birthdays
# - Add Birthday
# - Edit Birthday
# - Delete Birthday
# - Reminders
# - Add Reminder
# - Edit Reminder
# - Delete Reminder
# - Complete Reminder
# - Chat Assistant
# - History
# - Settings
# - Upcoming Birthday API
#
# Notifications:
# - Persistent notification alarm system
# - 5-minute repeat notification
# - STOP support
# - Chat → Reminder integration
# - Chat → Birthday integration
# - Alarm reset when reminder is edited
# - Alarm cleanup when reminder is deleted/completed
# ============================================================


# ============================================================
# IMPORTS
# ============================================================

import os
import re

from datetime import (
    datetime,
    date,
    timedelta,
    time
)

from zoneinfo import ZoneInfo


from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    jsonify
)


from flask_bcrypt import Bcrypt


from flask_login import (
    LoginManager,
    login_user,
    logout_user,
    login_required,
    current_user
)


from config import Config

from database import db

from database.models import (
    User,
    Birthday,
    Reminder
)


# ============================================================
# NOTIFICATION SERVICE
# ============================================================

from notification_service import (
    notification_bp,
    stop_active_alarms_for_reminder,
    reset_alarms_for_reminder,
    reset_alarms_for_birthday
)


# ============================================================
# APP SETUP
# ============================================================

app = Flask(__name__)

app.config.from_object(Config)


# ============================================================
# DATABASE CONFIGURATION
#
# config.py is now responsible for selecting:
#
# 1. Render DATABASE_URL
# 2. Local SQLite fallback
#
# We intentionally do NOT overwrite the database URI here.
# ============================================================

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_pre_ping": True
}


# ============================================================
# BCRYPT
# ============================================================

bcrypt = Bcrypt(app)


# ============================================================
# DATABASE
# ============================================================

db.init_app(app)


# ============================================================
# NOTIFICATION BLUEPRINT
# ============================================================

app.register_blueprint(notification_bp)


# ============================================================
# TIMEZONE
# ============================================================

INDIA_TZ = ZoneInfo("Asia/Kolkata")


def india_now():
    """
    Return current India local time
    as a naive datetime.

    Database stores Date and Time separately,
    so a naive datetime is used for comparisons.
    """

    return (
        datetime
        .now(INDIA_TZ)
        .replace(tzinfo=None)
    )


def india_today():
    """
    Return today's date in India.
    """

    return india_now().date()


# ============================================================
# LOGIN MANAGER
# ============================================================

login_manager = LoginManager(app)

login_manager.login_view = "login"


@login_manager.user_loader
def load_user(user_id):

    try:

        return db.session.get(
            User,
            int(user_id)
        )

    except (
        ValueError,
        TypeError
    ):

        return None


# ============================================================
# DASHBOARD
# ============================================================

@app.route("/")
@login_required
def home():

    today = india_today()

    birthdays = (
        Birthday.query
        .filter_by(
            user_id=current_user.id
        )
        .order_by(
            Birthday.birthday.asc()
        )
        .all()
    )

    all_reminders = (
        Reminder.query
        .filter_by(
            user_id=current_user.id
        )
        .order_by(
            Reminder.reminder_date.asc(),
            Reminder.reminder_time.asc()
        )
        .all()
    )

    reminders = [
        r
        for r in all_reminders
        if (
            r.status or "pending"
        ).lower() == "pending"
    ]

    completed_count = sum(
        1
        for r in all_reminders
        if (
            r.status or ""
        ).lower() == "completed"
    )

    cancelled_count = sum(
        1
        for r in all_reminders
        if (
            r.status or ""
        ).lower() == "cancelled"
    )

    today_reminders = [
        r
        for r in all_reminders
        if r.reminder_date == today
    ]

    today_birthdays = [
        b
        for b in birthdays
        if (
            b.birthday
            and
            b.birthday.month == today.month
            and
            b.birthday.day == today.day
        )
    ]

    upcoming_reminders = [
        r
        for r in reminders
        if (
            r.reminder_date
            and
            r.reminder_date >= today
        )
    ]

    return render_template(
        "dashboard.html",

        user=current_user,

        birthdays=birthdays,

        reminders=reminders,

        all_reminders=all_reminders,

        completed_count=completed_count,

        cancelled_count=cancelled_count,

        today_reminders=today_reminders,

        today_birthdays=today_birthdays,

        today_events_count=(
            len(today_reminders)
            +
            len(today_birthdays)
        ),

        upcoming_reminders=upcoming_reminders,

        upcoming_birthdays=birthdays
    )


# ============================================================
# REGISTER
# ============================================================

@app.route(
    "/register",
    methods=["GET", "POST"]
)
def register():

    if current_user.is_authenticated:

        return redirect(
            url_for("home")
        )

    if request.method == "POST":

        name = request.form.get(
            "name",
            ""
        ).strip()

        email = request.form.get(
            "email",
            ""
        ).strip().lower()

        password = request.form.get(
            "password",
            ""
        )

        if (
            not name
            or
            not email
            or
            not password
        ):

            flash(
                "All fields are required.",
                "error"
            )

            return redirect(
                url_for("register")
            )

        existing = (
            User.query
            .filter_by(
                email=email
            )
            .first()
        )

        if existing:

            flash(
                "Email already registered.",
                "error"
            )

            return redirect(
                url_for("register")
            )

        password_hash = (
            bcrypt
            .generate_password_hash(
                password
            )
            .decode("utf-8")
        )

        user = User(
            name=name,
            email=email,
            password_hash=password_hash
        )

        try:

            db.session.add(user)

            db.session.commit()

        except Exception:

            db.session.rollback()

            flash(
                "Unable to create the account right now.",
                "error"
            )

            return redirect(
                url_for("register")
            )

        login_user(user)

        flash(
            "Account created successfully!",
            "success"
        )

        return redirect(
            url_for("home")
        )

    return render_template(
        "register.html"
    )


# ============================================================
# LOGIN
# ============================================================

@app.route(
    "/login",
    methods=["GET", "POST"]
)
def login():

    if current_user.is_authenticated:

        return redirect(
            url_for("home")
        )

    if request.method == "POST":

        email = request.form.get(
            "email",
            ""
        ).strip().lower()

        password = request.form.get(
            "password",
            ""
        )

        user = (
            User.query
            .filter_by(
                email=email
            )
            .first()
        )

        if (
            user
            and
            bcrypt.check_password_hash(
                user.password_hash,
                password
            )
        ):

            login_user(user)

            next_page = request.args.get(
                "next"
            )

            # Prevent open redirects.
            if (
                next_page
                and
                next_page.startswith("/")
                and
                not next_page.startswith("//")
            ):

                return redirect(next_page)

            return redirect(
                url_for("home")
            )

        flash(
            "Invalid email or password.",
            "error"
        )

    return render_template(
        "login.html"
    )


# ============================================================
# LOGOUT
# ============================================================

@app.route("/logout")
@login_required
def logout():

    logout_user()

    flash(
        "You have been logged out.",
        "success"
    )

    return redirect(
        url_for("login")
    )


# ============================================================
# BIRTHDAYS
# ============================================================

@app.route("/birthdays")
@login_required
def birthdays():

    birthday_list = (
        Birthday.query
        .filter_by(
            user_id=current_user.id
        )
        .order_by(
            Birthday.birthday.asc()
        )
        .all()
    )

    return render_template(
        "birthdays.html",
        birthdays=birthday_list
    )


# ============================================================
# ADD BIRTHDAY
# ============================================================

@app.route(
    "/birthdays/add",
    methods=["GET", "POST"]
)
@login_required
def add_birthday():

    if request.method == "POST":

        name = request.form.get(
            "name",
            ""
        ).strip()

        birthday_value = request.form.get(
            "birthday",
            ""
        ).strip()

        phone = request.form.get(
            "phone",
            ""
        ).strip()

        relationship = request.form.get(
            "relationship",
            ""
        ).strip()

        notes = request.form.get(
            "notes",
            ""
        ).strip()

        if (
            not name
            or
            not birthday_value
        ):

            flash(
                "Name and birthday are required.",
                "error"
            )

            return redirect(
                url_for("add_birthday")
            )

        try:

            birthday_date = datetime.strptime(
                birthday_value,
                "%Y-%m-%d"
            ).date()

        except ValueError:

            flash(
                "Invalid birthday date.",
                "error"
            )

            return redirect(
                url_for("add_birthday")
            )

        birthday = Birthday(
            user_id=current_user.id,
            name=name,
            birthday=birthday_date,
            phone=phone or None,
            relationship=relationship or None,
            notes=notes or None
        )

        try:

            db.session.add(birthday)

            db.session.commit()

        except Exception:

            db.session.rollback()

            flash(
                "Unable to save birthday.",
                "error"
            )

            return redirect(
                url_for("add_birthday")
            )

        flash(
            f"{name}'s birthday was added!",
            "success"
        )

        return redirect(
            url_for("birthdays")
        )

    return render_template(
        "add_birthday.html"
    )


# ============================================================
# EDIT BIRTHDAY
# ============================================================

@app.route(
    "/birthdays/edit/<int:birthday_id>",
    methods=["GET", "POST"]
)
@login_required
def edit_birthday(birthday_id):

    birthday = (
        Birthday.query
        .filter_by(
            id=birthday_id,
            user_id=current_user.id
        )
        .first_or_404()
    )

    if request.method == "POST":

        name = request.form.get(
            "name",
            ""
        ).strip()

        birthday_value = request.form.get(
            "birthday",
            ""
        ).strip()

        phone = request.form.get(
            "phone",
            ""
        ).strip()

        relationship = request.form.get(
            "relationship",
            ""
        ).strip()

        notes = request.form.get(
            "notes",
            ""
        ).strip()

        if (
            not name
            or
            not birthday_value
        ):

            flash(
                "Name and birthday are required.",
                "error"
            )

            return redirect(
                url_for(
                    "edit_birthday",
                    birthday_id=birthday.id
                )
            )

        try:

            birthday_date = datetime.strptime(
                birthday_value,
                "%Y-%m-%d"
            ).date()

        except ValueError:

            flash(
                "Invalid birthday date.",
                "error"
            )

            return redirect(
                url_for(
                    "edit_birthday",
                    birthday_id=birthday.id
                )
            )

        birthday.name = name

        birthday.birthday = birthday_date

        birthday.phone = phone or None

        birthday.relationship = (
            relationship or None
        )

        birthday.notes = notes or None

        try:

            reset_alarms_for_birthday(
                birthday.id,
                current_user.id
            )

            db.session.commit()

        except Exception:

            db.session.rollback()

            flash(
                "Unable to update birthday.",
                "error"
            )

            return redirect(
                url_for(
                    "edit_birthday",
                    birthday_id=birthday.id
                )
            )

        flash(
            "Birthday updated successfully!",
            "success"
        )

        return redirect(
            url_for("birthdays")
        )

    return render_template(
        "edit_birthday.html",
        birthday=birthday
    )


# ============================================================
# DELETE BIRTHDAY
# ============================================================

@app.route(
    "/birthdays/delete/<int:birthday_id>",
    methods=["POST"]
)
@login_required
def delete_birthday(birthday_id):

    birthday = (
        Birthday.query
        .filter_by(
            id=birthday_id,
            user_id=current_user.id
        )
        .first_or_404()
    )

    try:

        reset_alarms_for_birthday(
            birthday.id,
            current_user.id
        )

        db.session.delete(birthday)

        db.session.commit()

    except Exception:

        db.session.rollback()

        flash(
            "Unable to delete birthday.",
            "error"
        )

        return redirect(
            url_for("birthdays")
        )

    flash(
        "Birthday deleted.",
        "success"
    )

    return redirect(
        url_for("birthdays")
    )


# ============================================================
# REMINDERS
# ============================================================

@app.route("/reminders")
@login_required
def reminders():

    reminder_list = (
        Reminder.query
        .filter_by(
            user_id=current_user.id
        )
        .order_by(
            Reminder.reminder_date.asc(),
            Reminder.reminder_time.asc()
        )
        .all()
    )

    reminders_json = []

    for reminder in reminder_list:

        reminder_date_value = (
            reminder.reminder_date.strftime(
                "%Y-%m-%d"
            )
            if reminder.reminder_date
            else ""
        )

        reminder_time_value = (
            reminder.reminder_time.strftime(
                "%H:%M"
            )
            if reminder.reminder_time
            else ""
        )

        reminders_json.append({

            "id":
                reminder.id,

            "title":
                reminder.title or "",

            "description":
                reminder.description or "",

            "place":
                reminder.place or "",

            "reminder_date":
                reminder_date_value,

            "reminder_time":
                reminder_time_value,

            "date":
                reminder_date_value,

            "time":
                reminder_time_value,

            "status":
                reminder.status or "pending",

            "reminder_type":
                reminder.reminder_type or "custom",

            "type":
                reminder.reminder_type or "custom"
        })

    return render_template(
        "reminder.html",
        reminders=reminder_list,
        reminders_json=reminders_json
    )


# ============================================================
# ADD REMINDER
# ============================================================

@app.route(
    "/reminders/add",
    methods=["GET", "POST"]
)
@login_required
def add_reminder():

    if request.method == "POST":

        title = request.form.get(
            "title",
            ""
        ).strip()

        description = request.form.get(
            "description",
            ""
        ).strip()

        place = request.form.get(
            "place",
            ""
        ).strip()

        date_value = request.form.get(
            "reminder_date",
            ""
        ).strip()

        time_value = request.form.get(
            "reminder_time",
            ""
        ).strip()

        if (
            not title
            or
            not date_value
            or
            not time_value
        ):

            flash(
                "Title, date and time are required.",
                "error"
            )

            return redirect(
                url_for("add_reminder")
            )

        try:

            reminder_date = datetime.strptime(
                date_value,
                "%Y-%m-%d"
            ).date()

            reminder_time = datetime.strptime(
                time_value,
                "%H:%M"
            ).time()

        except ValueError:

            flash(
                "Invalid date or time.",
                "error"
            )

            return redirect(
                url_for("add_reminder")
            )

        reminder = Reminder(
            user_id=current_user.id,
            title=title,
            description=description or None,
            place=place or None,
            reminder_date=reminder_date,
            reminder_time=reminder_time,
            status="pending",
            reminder_type="custom"
        )

        try:

            db.session.add(reminder)

            db.session.commit()

        except Exception:

            db.session.rollback()

            flash(
                "Unable to create reminder.",
                "error"
            )

            return redirect(
                url_for("add_reminder")
            )

        flash(
            "Reminder created successfully!",
            "success"
        )

        return redirect(
            url_for("reminders")
        )

    return render_template(
        "add_reminder.html"
    )


# ============================================================
# EDIT REMINDER
# ============================================================

@app.route(
    "/reminders/edit/<int:reminder_id>",
    methods=["GET", "POST"]
)
@login_required
def edit_reminder(reminder_id):

    reminder = (
        Reminder.query
        .filter_by(
            id=reminder_id,
            user_id=current_user.id
        )
        .first_or_404()
    )

    if request.method == "POST":

        title = request.form.get(
            "title",
            ""
        ).strip()

        description = request.form.get(
            "description",
            ""
        ).strip()

        place = request.form.get(
            "place",
            ""
        ).strip()

        date_value = request.form.get(
            "reminder_date",
            ""
        ).strip()

        time_value = request.form.get(
            "reminder_time",
            ""
        ).strip()

        if (
            not title
            or
            not date_value
            or
            not time_value
        ):

            flash(
                "Title, date and time are required.",
                "error"
            )

            return redirect(
                url_for(
                    "edit_reminder",
                    reminder_id=reminder.id
                )
            )

        try:

            reminder_date = datetime.strptime(
                date_value,
                "%Y-%m-%d"
            ).date()

            reminder_time = datetime.strptime(
                time_value,
                "%H:%M"
            ).time()

        except ValueError:

            flash(
                "Invalid date or time.",
                "error"
            )

            return redirect(
                url_for(
                    "edit_reminder",
                    reminder_id=reminder.id
                )
            )

        try:

            reset_alarms_for_reminder(
                reminder.id,
                current_user.id
            )

            reminder.title = title

            reminder.description = (
                description or None
            )

            reminder.place = (
                place or None
            )

            reminder.reminder_date = (
                reminder_date
            )

            reminder.reminder_time = (
                reminder_time
            )

            if (
                reminder.status or ""
            ).lower() == "completed":

                reminder.status = "pending"

            db.session.commit()

        except Exception:

            db.session.rollback()

            flash(
                "Unable to update reminder.",
                "error"
            )

            return redirect(
                url_for(
                    "edit_reminder",
                    reminder_id=reminder.id
                )
            )

        flash(
            "Reminder updated successfully!",
            "success"
        )

        return redirect(
            url_for("reminders")
        )

    return render_template(
        "edit_reminder.html",
        reminder=reminder
    )


# ============================================================
# DELETE REMINDER
# ============================================================

@app.route(
    "/reminders/delete/<int:reminder_id>",
    methods=["POST"]
)
@login_required
def delete_reminder(reminder_id):

    reminder = (
        Reminder.query
        .filter_by(
            id=reminder_id,
            user_id=current_user.id
        )
        .first_or_404()
    )

    try:

        reset_alarms_for_reminder(
            reminder.id,
            current_user.id
        )

        db.session.delete(reminder)

        db.session.commit()

    except Exception:

        db.session.rollback()

        flash(
            "Unable to delete reminder.",
            "error"
        )

        return redirect(
            url_for("reminders")
        )

    flash(
        "Reminder deleted.",
        "success"
    )

    return redirect(
        url_for("reminders")
    )


# ============================================================
# COMPLETE REMINDER — NORMAL PAGE
# ============================================================

@app.route(
    "/reminders/complete/<int:reminder_id>",
    methods=["POST"]
)
@login_required
def complete_reminder(reminder_id):

    reminder = (
        Reminder.query
        .filter_by(
            id=reminder_id,
            user_id=current_user.id
        )
        .first_or_404()
    )

    try:

        reminder.status = "completed"

        stop_active_alarms_for_reminder(
            reminder.id,
            current_user.id
        )

        db.session.commit()

    except Exception:

        db.session.rollback()

        flash(
            "Unable to complete reminder.",
            "error"
        )

        return redirect(
            url_for("reminders")
        )

    flash(
        "Reminder completed!",
        "success"
    )

    return redirect(
        url_for("reminders")
    )


# ============================================================
# COMPLETE REMINDER — API
# ============================================================

@app.route(
    "/api/reminders/<int:reminder_id>/complete",
    methods=["POST"]
)
@login_required
def complete_reminder_api(reminder_id):

    reminder = (
        Reminder.query
        .filter_by(
            id=reminder_id,
            user_id=current_user.id
        )
        .first_or_404()
    )

    try:

        reminder.status = "completed"

        stop_active_alarms_for_reminder(
            reminder.id,
            current_user.id
        )

        db.session.commit()

    except Exception:

        db.session.rollback()

        return jsonify({
            "success": False,
            "message": "Unable to complete reminder."
        }), 500

    return jsonify({

        "success": True,

        "id": reminder.id,

        "status": reminder.status

    })


# ============================================================
# CHAT PAGE
# ============================================================

@app.route("/chat")
@login_required
def chat_page():

    return render_template(
        "chat.html"
    )


# ============================================================
# CHAT HELPERS
# ============================================================

MONTHS = {

    "january": 1,
    "jan": 1,

    "february": 2,
    "feb": 2,

    "march": 3,
    "mar": 3,

    "april": 4,
    "apr": 4,

    "may": 5,

    "june": 6,
    "jun": 6,

    "july": 7,
    "jul": 7,

    "august": 8,
    "aug": 8,

    "september": 9,
    "sep": 9,
    "sept": 9,

    "october": 10,
    "oct": 10,

    "november": 11,
    "nov": 11,

    "december": 12,
    "dec": 12
}


# ============================================================
# EXTRACT TIME
# ============================================================

def extract_time(text):

    lower = text.lower()

    match = re.search(
        r"\b"
        r"(1[0-2]|[1-9])"
        r"(?:[:.]([0-5]\d))?"
        r"\s*"
        r"(am|pm)"
        r"\b",
        lower
    )

    if match:

        hour = int(match.group(1))

        minute = int(
            match.group(2) or 0
        )

        period = match.group(3)

        if period == "pm" and hour != 12:
            hour += 12

        if period == "am" and hour == 12:
            hour = 0

        return time(hour, minute)

    match = re.search(
        r"\b"
        r"([01]\d|2[0-3])"
        r":"
        r"([0-5]\d)"
        r"\b",
        lower
    )

    if match:

        return time(
            int(match.group(1)),
            int(match.group(2))
        )

    match = re.search(
        r"\b"
        r"(1[0-2]|[1-9])"
        r"\s*"
        r"o"
        r"\s*"
        r"(?:'|’)?"
        r"\s*"
        r"clock"
        r"\s*"
        r"(am|pm)?"
        r"\b",
        lower
    )

    if match:

        hour = int(match.group(1))

        period = match.group(2)

        if period == "pm":

            if hour != 12:
                hour += 12

        elif period == "am":

            if hour == 12:
                hour = 0

        else:

            if re.search(
                r"\b(night|tonight|evening)\b",
                lower
            ):

                if hour < 12:
                    hour += 12

            elif re.search(
                r"\b(afternoon)\b",
                lower
            ):

                if hour < 12:
                    hour += 12

        return time(hour, 0)

    if re.search(
        r"\bnoon\b",
        lower
    ):

        return time(12, 0)

    if re.search(
        r"\bmidnight\b",
        lower
    ):

        return time(0, 0)

    return None


# ============================================================
# EXTRACT DATE
# ============================================================

def extract_date(text):

    lower = text.lower()

    today = india_today()

    if re.search(
        r"\bday\s+after\s+tomorrow\b",
        lower
    ):

        return today + timedelta(days=2)

    if re.search(
        r"\btomorrow\b",
        lower
    ):

        return today + timedelta(days=1)

    if re.search(
        r"\btoday\b",
        lower
    ):

        return today

    weekdays = {

        "monday": 0,
        "tuesday": 1,
        "wednesday": 2,
        "thursday": 3,
        "friday": 4,
        "saturday": 5,
        "sunday": 6
    }

    for (
        weekday_name,
        weekday_number
    ) in weekdays.items():

        if re.search(
            rf"\b{weekday_name}\b",
            lower
        ):

            days_ahead = (
                weekday_number
                -
                today.weekday()
            ) % 7

            if days_ahead == 0:
                days_ahead = 7

            return today + timedelta(
                days=days_ahead
            )

    month_names = "|".join(
        re.escape(value)
        for value in MONTHS.keys()
    )

    match = re.search(
        r"\b("
        + month_names
        + r")\s+"
        r"(\d{1,2})"
        r"(?:st|nd|rd|th)?"
        r"(?:\s+(\d{4}))?"
        r"\b",
        lower
    )

    if match:

        month = MONTHS[
            match.group(1)
        ]

        day = int(
            match.group(2)
        )

        supplied_year = match.group(3)

        year = (
            int(supplied_year)
            if supplied_year
            else today.year
        )

        try:

            result = date(
                year,
                month,
                day
            )

            if (
                not supplied_year
                and
                result < today
            ):

                result = date(
                    year + 1,
                    month,
                    day
                )

            return result

        except ValueError:

            return None

    return None


# ============================================================
# EXTRACT BIRTHDAY NAME
# ============================================================

def extract_birthday_name(text):

    patterns = [

        r"\b(.+?)['’]s\s+"
        r"(?:birthday|bday)\b",

        r"^\s*(?:add|create|save|set)?\s*"
        r"(.+?)\s+"
        r"(?:birthday|bday)\b",

        r"\b(?:birthday|bday)"
        r"\s+of\s+"
        r"(.+?)"
        r"(?:\s+is|\s+on|\s*$)",

        r"\b(?:birthday|bday)"
        r"\s+(?:for|of)\s+"
        r"(.+?)"
        r"(?:\s+is|\s+on|\s*$)"
    ]

    for pattern in patterns:

        match = re.search(
            pattern,
            text,
            re.IGNORECASE
        )

        if match:

            name = (
                match.group(1)
                .strip()
            )

            name = re.sub(
                r"^(add|create|save|set)\s+",
                "",
                name,
                flags=re.IGNORECASE
            )

            name = re.sub(
                r"\s+(?:is|on)\s+.*$",
                "",
                name,
                flags=re.IGNORECASE
            )

            name = name.strip(
                " .,!?-"
            )

            if name:
                return name

    return ""


# ============================================================
# EXTRACT REMINDER TITLE
# ============================================================

def extract_reminder_title(text):

    title = text.strip()

    title = re.sub(
        r"^\s*"
        r"(please\s+)?"
        r"remind\s+me"
        r"(\s+to)?\s*",
        "",
        title,
        flags=re.IGNORECASE
    )

    title = re.sub(
        r"^\s*"
        r"(please\s+)?"
        r"(add|create|set)"
        r"\s+(a\s+)?"
        r"reminder"
        r"\s*(to\s+)?",
        "",
        title,
        flags=re.IGNORECASE
    )

    title = re.sub(
        r"\b"
        r"(1[0-2]|[1-9])"
        r"(?:[:.]([0-5]\d))?"
        r"\s*"
        r"(am|pm)"
        r"\b",
        "",
        title,
        flags=re.IGNORECASE
    )

    title = re.sub(
        r"\b"
        r"(1[0-2]|[1-9])"
        r"\s*"
        r"o"
        r"\s*"
        r"(?:'|’)?"
        r"\s*"
        r"clock"
        r"\s*"
        r"(am|pm)?"
        r"\b",
        "",
        title,
        flags=re.IGNORECASE
    )

    title = re.sub(
        r"\b("
        r"today|"
        r"tomorrow|"
        r"day\s+after\s+tomorrow|"
        r"tonight|"
        r"morning|"
        r"afternoon|"
        r"evening"
        r")\b",
        "",
        title,
        flags=re.IGNORECASE
    )

    month_names = "|".join(
        re.escape(value)
        for value in MONTHS.keys()
    )

    title = re.sub(
        r"\b("
        + month_names
        + r")\s+"
        r"\d{1,2}"
        r"(?:st|nd|rd|th)?"
        r"(?:\s+\d{4})?\b",
        "",
        title,
        flags=re.IGNORECASE
    )

    title = re.sub(
        r"\s{2,}",
        " ",
        title
    ).strip(
        " .,!?-"
    )

    if not title:
        title = "Reminder"

    return (
        title[:1].upper()
        +
        title[1:]
    )


# ============================================================
# CHAT API
# ============================================================

@app.route(
    "/api/chat",
    methods=["POST"]
)
@app.route(
    "/api/chat-agent",
    methods=["POST"]
)
@login_required
def chat():

    data = request.get_json(
        silent=True
    ) or {}

    message = str(
        data.get(
            "message",
            ""
        )
    ).strip()

    mode = str(
        data.get(
            "mode",
            ""
        )
    ).strip().lower()

    if not message:

        return jsonify({

            "success": False,

            "created": False,

            "reply":
                "Please type a message."

        }), 400

    try:

        lower = message.lower()

        # ====================================================
        # BIRTHDAY
        # ====================================================

        is_birthday = (
            mode == "birthday"
            or
            bool(
                re.search(
                    r"\b(birthday|bday)\b",
                    lower
                )
            )
        )

        if is_birthday:

            name = extract_birthday_name(
                message
            )

            birthday_date = extract_date(
                message
            )

            if not name:

                return jsonify({

                    "success": False,

                    "created": False,

                    "type": "birthday",

                    "reply":
                        (
                            "🎂 Please include "
                            "the person's name.\n\n"
                            "Example:\n"
                            "Arun's birthday is "
                            "August 25"
                        )

                })

            if not birthday_date:

                return jsonify({

                    "success": False,

                    "created": False,

                    "type": "birthday",

                    "reply":
                        (
                            f"🎂 I found {name}, "
                            "but I need the "
                            "birthday date.\n\n"
                            "Example:\n"
                            "Arun's birthday is "
                            "August 25"
                        )

                })

            birthday = (
                Birthday.query
                .filter_by(
                    user_id=current_user.id,
                    name=name
                )
                .first()
            )

            if birthday:

                reset_alarms_for_birthday(
                    birthday.id,
                    current_user.id
                )

                birthday.birthday = (
                    birthday_date
                )

                action = "updated"

            else:

                birthday = Birthday(
                    user_id=current_user.id,
                    name=name,
                    birthday=birthday_date,
                    phone=None,
                    relationship=None,
                    notes="Created through chat."
                )

                db.session.add(
                    birthday
                )

                action = "added"

            db.session.commit()

            return jsonify({

                "success": True,

                "created": True,

                "type": "birthday",

                "birthday": {

                    "id":
                        birthday.id,

                    "name":
                        birthday.name,

                    "date":
                        birthday.birthday.isoformat()
                },

                "reply":
                    (
                        "✅ Yes! Received and "
                        f"{action} successfully.\n\n"
                        f"🎂 {name}'s Birthday\n"
                        f"📅 "
                        f"{birthday_date.strftime('%d %B %Y')}"
                    )
            })

        # ====================================================
        # TIME REMINDER
        # ====================================================

        reminder_mode = (
            mode == "reminder"
            or
            bool(
                re.search(
                    r"\b("
                    r"remind|"
                    r"reminder|"
                    r"event|"
                    r"schedule|"
                    r"remember"
                    r")\b",
                    lower
                )
            )
            or
            extract_time(message) is not None
        )

        if reminder_mode:

            reminder_time = extract_time(
                message
            )

            if not reminder_time:

                return jsonify({

                    "success": False,

                    "created": False,

                    "type": "reminder",

                    "reply":
                        (
                            "⏰ I need a "
                            "time for the "
                            "reminder.\n\n"
                            "Example:\n"
                            "Remind me to "
                            "study at 7 PM"
                        )

                })

            reminder_date = extract_date(
                message
            )

            if not reminder_date:

                reminder_date = india_today()

                now = india_now()

                scheduled = datetime.combine(
                    reminder_date,
                    reminder_time
                )

                if scheduled <= now:

                    reminder_date += (
                        timedelta(days=1)
                    )

            title = extract_reminder_title(
                message
            )

            reminder = Reminder(
                user_id=current_user.id,
                title=title,
                description="Created through chat.",
                place=None,
                reminder_date=reminder_date,
                reminder_time=reminder_time,
                status="pending",
                reminder_type="chat"
            )

            db.session.add(
                reminder
            )

            db.session.commit()

            return jsonify({

                "success": True,

                "created": True,

                "type": "reminder",

                "reminder": {

                    "id":
                        reminder.id,

                    "title":
                        reminder.title,

                    "date":
                        reminder.reminder_date.isoformat(),

                    "time":
                        reminder.reminder_time.strftime(
                            "%H:%M"
                        )
                },

                "reply":
                    (
                        "✅ Yes! Received and "
                        "added successfully.\n\n"
                        f"⏰ {title}\n"
                        f"📅 "
                        f"{reminder_date.strftime('%d %B %Y')}\n"
                        f"🕐 "
                        f"{reminder_time.strftime('%I:%M %p')}"
                    )
            })

        # ====================================================
        # UNKNOWN
        # ====================================================

        return jsonify({

            "success": True,

            "created": False,

            "type": "unknown",

            "reply":
                (
                    "👋 I received your message.\n\n"
                    "Try:\n"
                    "⏰ Remind me to study "
                    "at 7 PM\n"
                    "🎂 Arun's birthday is "
                    "August 25"
                )
        })

    except Exception as error:

        db.session.rollback()

        print(
            "CHAT ERROR:",
            repr(error)
        )

        return jsonify({

            "success": False,

            "created": False,

            "reply":
                (
                    "❌ I couldn't save "
                    "that right now."
                )

        }), 500


# ============================================================
# OLD DUE REMINDERS API
#
# Kept for backward compatibility.
# ============================================================

@app.route("/api/due-reminders")
@login_required
def due_reminders():

    now = india_now()

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

    due = []

    for reminder in reminders:

        if not reminder.reminder_date:
            continue

        if not reminder.reminder_time:
            continue

        scheduled = datetime.combine(
            reminder.reminder_date,
            reminder.reminder_time
        )

        if scheduled <= now:

            due.append({

                "id":
                    reminder.id,

                "title":
                    reminder.title,

                "description":
                    reminder.description or "",

                "date":
                    reminder.reminder_date.strftime(
                        "%d %B %Y"
                    ),

                "time":
                    reminder.reminder_time.strftime(
                        "%I:%M %p"
                    )
            })

    return jsonify({

        "success": True,

        "reminders": due
    })


# ============================================================
# UPCOMING BIRTHDAYS
# ============================================================

@app.route("/api/upcoming-birthdays")
@login_required
def upcoming_birthdays():

    today = india_today()

    birthday_list = (
        Birthday.query
        .filter_by(
            user_id=current_user.id
        )
        .all()
    )

    result = []

    for birthday in birthday_list:

        if not birthday.birthday:
            continue

        month = birthday.birthday.month

        day = birthday.birthday.day

        try:

            next_birthday = date(
                today.year,
                month,
                day
            )

        except ValueError:

            if (
                month == 2
                and
                day == 29
            ):

                next_birthday = date(
                    today.year,
                    2,
                    28
                )

            else:

                continue

        if next_birthday < today:

            try:

                next_birthday = date(
                    today.year + 1,
                    month,
                    day
                )

            except ValueError:

                if (
                    month == 2
                    and
                    day == 29
                ):

                    next_birthday = date(
                        today.year + 1,
                        2,
                        28
                    )

                else:

                    continue

        days = (
            next_birthday
            -
            today
        ).days

        if 0 <= days <= 5:

            if days == 0:

                message = (
                    f"🎉 Today is "
                    f"{birthday.name}'s birthday!"
                )

            elif days == 1:

                message = (
                    f"🎂 {birthday.name}'s "
                    "birthday is tomorrow!"
                )

            else:

                message = (
                    f"🎂 {birthday.name}'s "
                    f"birthday is in {days} days!"
                )

            result.append({

                "id":
                    birthday.id,

                "name":
                    birthday.name,

                "birthday":
                    birthday.birthday.strftime(
                        "%d %B"
                    ),

                "date":
                    next_birthday.isoformat(),

                "days_remaining":
                    days,

                "message":
                    message
            })

    result.sort(
        key=lambda x:
        x["days_remaining"]
    )

    return jsonify({

        "success": True,

        "birthdays": result
    })


# ============================================================
# HISTORY
# ============================================================

@app.route("/history")
@login_required
def history():

    reminders_history = (
        Reminder.query
        .filter_by(
            user_id=current_user.id
        )
        .order_by(
            Reminder.reminder_date.desc(),
            Reminder.reminder_time.desc()
        )
        .all()
    )

    birthdays_history = (
        Birthday.query
        .filter_by(
            user_id=current_user.id
        )
        .order_by(
            Birthday.birthday.desc()
        )
        .all()
    )

    return render_template(
        "history.html",
        reminders=reminders_history,
        birthdays=birthdays_history
    )


# ============================================================
# SETTINGS
# ============================================================

@app.route("/settings")
@login_required
def settings():

    return render_template(
        "settings.html",
        user=current_user
    )


# ============================================================
# DATABASE INITIALIZATION
# ============================================================
#
# This is safe for both:
#
# Local SQLite
# and
# TiDB Cloud
#
# Existing tables/data are NOT deleted.
# ============================================================

with app.app_context():

    try:

        db.create_all()

    except Exception as error:

        print(
            "DATABASE INITIALIZATION ERROR:",
            repr(error)
        )


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":

    port = int(
        os.environ.get(
            "PORT",
            5000
        )
    )

    app.run(
        host="0.0.0.0",
        port=port,
        debug=True,
        use_reloader=False
    )
"""Self-contained natural-language chat agent for Bday Reminder.

This module deliberately uses the application's existing SQLAlchemy session and
models.  It does not render HTML or maintain any client-side reminder store.
"""

import logging
import re
from datetime import date, datetime, time, timedelta

from sqlalchemy import func

from database import db
from database.models import Birthday, Reminder


logger = logging.getLogger(__name__)

MONTHS = {
    "january": 1, "jan": 1, "february": 2, "feb": 2,
    "march": 3, "mar": 3, "april": 4, "apr": 4, "may": 5,
    "june": 6, "jun": 6, "july": 7, "jul": 7, "august": 8,
    "aug": 8, "september": 9, "sep": 9, "sept": 9,
    "october": 10, "oct": 10, "november": 11, "nov": 11,
    "december": 12, "dec": 12,
}
WEEKDAYS = {"monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3,
            "friday": 4, "saturday": 5, "sunday": 6}


def _safe_date(year, month, day):
    try:
        return date(year, month, day)
    except ValueError:
        return None


def _next_year_if_past(value, explicit_year):
    if value and not explicit_year and value < date.today():
        return _safe_date(value.year + 1, value.month, value.day)
    return value


def extract_date(message):
    """Return a date from common Indian and natural-language date formats."""
    text = message.lower()
    today = date.today()
    if re.search(r"\bday\s+after\s+tomorrow\b", text):
        return today + timedelta(days=2)
    if re.search(r"\btomorrow\b", text):
        return today + timedelta(days=1)
    if re.search(r"\btoday\b", text):
        return today
    relative = re.search(r"\b(?:in|after)\s+(\d+)\s+days?\b", text)
    if relative:
        return today + timedelta(days=int(relative.group(1)))

    weekday_names = "|".join(WEEKDAYS)
    weekday = re.search(r"\b(?:(next|this|on)\s+)?(" + weekday_names + r")\b", text)
    if weekday:
        modifier, name = weekday.groups()
        delta = WEEKDAYS[name] - today.weekday()
        if modifier == "next":
            if delta <= 0:
                delta += 7
        elif delta < 0:
            delta += 7
        return today + timedelta(days=delta)

    numeric = re.search(r"\b(\d{1,2})[/.\-](\d{1,2})(?:[/.\-](\d{4}))?\b", text)
    if numeric:
        first, second, year_text = numeric.groups()
        year = int(year_text) if year_text else today.year
        value = _safe_date(year, int(second), int(first))  # DD/MM preferred
        if value is None:
            value = _safe_date(year, int(first), int(second))
        return _next_year_if_past(value, bool(year_text))

    names = "|".join(MONTHS)
    patterns = (
        r"\b(" + names + r")\s+(\d{1,2})(?:st|nd|rd|th)?(?:,?\s+(\d{4}))?\b",
        r"\b(\d{1,2})(?:st|nd|rd|th)?\s+(" + names + r")(?:,?\s+(\d{4}))?\b",
    )
    for index, pattern in enumerate(patterns):
        match = re.search(pattern, text)
        if not match:
            continue
        first, second, year_text = match.groups()
        month, day = (MONTHS[first], int(second)) if index == 0 else (MONTHS[second], int(first))
        year = int(year_text) if year_text else today.year
        return _next_year_if_past(_safe_date(year, month, day), bool(year_text))
    return None


def extract_time(message):
    """Extract an explicit or contextual time without falling back to 09:00."""
    text = message.lower()
    match = re.search(r"\b(1[0-2]|[1-9])(?:[:.]([0-5]\d))?\s*(am|pm)\b", text)
    if match:
        hour, minute, period = int(match.group(1)), int(match.group(2) or 0), match.group(3)
        hour = hour % 12 + (12 if period == "pm" else 0)
        result = time(hour, minute)
        logger.info("CHAT AGENT TIME raw=%r period=%s final=%s", match.group(0), period, result)
        return result
    match = re.search(r"\b([01]\d|2[0-3]):([0-5]\d)\b", text)
    if match:
        result = time(int(match.group(1)), int(match.group(2)))
        logger.info("CHAT AGENT TIME raw=%r period=24-hour final=%s", match.group(0), result)
        return result

    # Keep this before a bare ``at 5`` match.  Otherwise ``at/by 5 o'clock``
    # is incorrectly consumed as 05:00 with no chance to use its context.
    match = re.search(r"\b(?:at|by)\s*(\d{1,2})\s*(?:o\s*'?clock|clock)\b|\b(\d{1,2})\s*(?:o\s*'?clock|clock)\b", text)
    if match:
        hour = int(match.group(1) or match.group(2))
        if 1 <= hour <= 12:
            result, period = _contextual_clock_time(hour, text)
            logger.info("CHAT AGENT TIME raw=%r period=%s final=%s", match.group(0), period, result)
            return result

    # Accept a plain "at/by 5" too, while still respecting morning/evening.
    match = re.search(r"\b(?:at|by)\s+([0-9]{1,2})\b", text)
    if match and int(match.group(1)) <= 23:
        hour = int(match.group(1))
        if 1 <= hour <= 12:
            result, period = _contextual_clock_time(hour, text)
        else:
            result, period = time(hour, 0), "24-hour"
        logger.info("CHAT AGENT TIME raw=%r period=%s final=%s", match.group(0), period, result)
        return result
    for pattern, value in ((r"\bmidnight\b", time(0, 0)), (r"\bnoon\b", time(12, 0)),
                           (r"\b(morning|breakfast)\b", time(9, 0)),
                           (r"\b(afternoon|lunch)\b", time(13, 0)),
                           (r"\b(evening|dinner)\b", time(18, 0)),
                           (r"\b(night|tonight)\b", time(20, 0))):
        if re.search(pattern, text):
            logger.info("CHAT AGENT TIME raw=%r period=context final=%s", pattern, value)
            return value
    return None


def _contextual_clock_time(hour, text):
    """Resolve an AM/PM-less clock hour using the surrounding language."""
    if re.search(r"\b(morning|breakfast)\b", text):
        return time(hour % 12, 0), "AM (morning)"
    if re.search(r"\b(afternoon|evening|night|tonight|dinner)\b", text):
        return time(hour % 12 + 12, 0), "PM (context)"

    # A deadline/request at 1–7 is generally an afternoon/evening time;
    # 8–11 is generally daytime. This is used only when there is no period.
    if 1 <= hour <= 7:
        return time(hour + 12, 0), "PM (inferred)"
    return time(hour % 12, 0), "AM (inferred)"


def extract_reminder_title(message):
    title = message.strip()
    title = re.sub(r"^\s*(?:please\s+)?(?:remind\s+me|reminder\s+to|set\s+(?:a\s+)?reminder|add\s+(?:a\s+)?reminder|create\s+(?:a\s+)?reminder)\s*(?:to\s+)?", "", title, flags=re.I)
    title = re.sub(r"^\s*(?:i\s+(?:need|have)\s+(?:to\s+)?|i'm\s+going\s+to\s+)", "", title, flags=re.I)
    title = re.sub(r"\b(1[0-2]|[1-9])(?:[:.]([0-5]\d))?\s*(am|pm)\b", "", title, flags=re.I)
    title = re.sub(r"\b(?:at|by)\s*\d{1,2}\s*(?:o\s*'?clock|clock)\b|\b\d{1,2}\s*(?:o\s*'?clock|clock)\b", "", title, flags=re.I)
    title = re.sub(r"\b([01]\d|2[0-3]):([0-5]\d)\b|\bat\s+\d{1,2}\b", "", title, flags=re.I)
    title = re.sub(r"\b(day\s+after\s+tomorrow|today|tomorrow|(?:in|after)\s+\d+\s+days?)\b", "", title, flags=re.I)
    title = re.sub(r"\b(?:next\s+|this\s+|on\s+)?(?:" + "|".join(WEEKDAYS) + r")\b", "", title, flags=re.I)
    title = re.sub(r"\b\d{1,2}[/.\-]\d{1,2}(?:[/.\-]\d{4})?\b", "", title)
    months = "|".join(MONTHS)
    title = re.sub(r"\b(?:" + months + r")\s+\d{1,2}(?:st|nd|rd|th)?(?:,?\s+\d{4})?\b", "", title, flags=re.I)
    title = re.sub(r"\b\d{1,2}(?:st|nd|rd|th)?\s+(?:" + months + r")(?:,?\s+\d{4})?\b", "", title, flags=re.I)
    title = re.sub(r"\b(morning|afternoon|evening|night|tonight|noon|midnight)\b", "", title, flags=re.I)
    title = re.sub(r"\s+\b(?:at|by|on|in)\b\s*$", "", title, flags=re.I)
    title = re.sub(r"\s+", " ", title).strip(" .,!?-")
    return (title or "Reminder")[:1].upper() + (title or "Reminder")[1:]


def extract_birthday_name(message):
    text = message.strip()
    patterns = (
        r"(.+?)[’']s\s+(?:birthday|bday)\b",
        r"(?:birthday|bday)\s+(?:of|for)\s+(.+?)(?:\s+(?:is|on)\b|$)",
        r"^(.+?)\s+(?:birthday|bday)\b",
    )
    for pattern in patterns:
        match = re.search(pattern, text, re.I)
        if match:
            name = re.sub(r"^(?:please\s+)?(?:add|create|save|set|remember)\s+", "", match.group(1).strip(), flags=re.I)
            name = re.sub(r"^(?:it'?s|my|the)\s+", "", name, flags=re.I).strip(" .,!?-")
            if name:
                return name
    return None


def parse_reminder_text(message):
    reminder_date, reminder_time = extract_date(message), extract_time(message)
    logger.info("CHAT AGENT PARSE original=%r extracted_date=%s extracted_time=%s", message, reminder_date, reminder_time)
    if reminder_date and not reminder_time:
        reminder_time = time(9, 0)
    elif reminder_time and not reminder_date:
        reminder_date = date.today()
        if datetime.combine(reminder_date, reminder_time) <= datetime.now():
            reminder_date += timedelta(days=1)
    elif not reminder_date and not reminder_time:
        reminder_date, reminder_time = date.today() + timedelta(days=1), time(9, 0)
    return {"title": extract_reminder_title(message), "date": reminder_date, "time": reminder_time}


def _sync_birthday_reminder(birthday):
    today = date.today()
    occurrence = _safe_date(today.year, birthday.birthday.month, birthday.birthday.day)
    if occurrence is None and birthday.birthday.month == 2 and birthday.birthday.day == 29:
        occurrence = date(today.year, 2, 28)
    if occurrence < today:
        occurrence = _safe_date(today.year + 1, birthday.birthday.month, birthday.birthday.day)
    title = f"🎂 {birthday.name}'s Birthday"
    reminder = Reminder.query.filter_by(user_id=birthday.user_id, reminder_type="birthday", title=title).first()
    if not reminder:
        reminder = Reminder(user_id=birthday.user_id, title=title, description="Annual birthday reminder.", place=None,
                            reminder_date=occurrence, reminder_time=time(9, 0), status="pending", reminder_type="birthday")
        db.session.add(reminder)
    else:
        reminder.reminder_date, reminder.reminder_time, reminder.status = occurrence, time(9, 0), "pending"
    return reminder


def _serialize_reminder(record):
    return {"id": record.id, "title": record.title, "date": record.reminder_date.isoformat(),
            "time": record.reminder_time.strftime("%H:%M"), "status": record.status, "type": record.reminder_type}


def process_message(message, mode, user_id):
    """Parse, persist, re-query, and return a JSON-safe response dictionary."""
    message, mode = str(message or "").strip(), str(mode or "reminder").lower().strip()
    logger.info("CHAT AGENT REQUEST mode=%s message=%r", mode, message)
    if not user_id:
        return {"success": False, "created": False, "verified": False, "error": "LOGIN_REQUIRED", "reply": "🔐 Please log in before creating a reminder."}
    if not message:
        return {"success": False, "created": False, "verified": False, "reply": "⚠️ Please type a reminder first."}
    if mode not in {"reminder", "birthday"}:
        return {"success": False, "created": False, "verified": False, "reply": "⚠️ Please select Time Event or Birthday."}
    try:
        if mode == "birthday":
            name, birthday_date = extract_birthday_name(message), extract_date(message)
            logger.info("CHAT AGENT PARSED name=%r date=%s", name, birthday_date)
            if not name or not birthday_date:
                return {"success": False, "created": False, "verified": False, "reply": "⚠️ Please include the person's name and birthday date."}
            birthday = Birthday.query.filter(Birthday.user_id == user_id, func.lower(Birthday.name) == name.lower()).first()
            if birthday:
                birthday.birthday = birthday_date
            else:
                birthday = Birthday(user_id=user_id, name=name, birthday=birthday_date, phone=None, relationship=None, notes="Created through Chat Agent.")
                db.session.add(birthday)
            db.session.flush()
            annual_reminder = _sync_birthday_reminder(birthday)
            logger.info("CHAT AGENT DB INSERT birthday name=%r", name)
            db.session.commit()
            saved = Birthday.query.filter_by(id=birthday.id, user_id=user_id).first()
            if not saved:
                return {"success": False, "created": False, "verified": False, "reply": "❌ I could not verify the birthday. Nothing was confirmed."}
            logger.info("CHAT AGENT DB VERIFIED birthday id=%s", saved.id)
            return {"success": True, "created": True, "verified": True, "type": "birthday",
                    "birthday": {"id": saved.id, "name": saved.name, "date": saved.birthday.isoformat()},
                    "reminder": _serialize_reminder(annual_reminder),
                    "reply": f"🎂 Yes! {saved.name}'s birthday was added successfully."}

        parsed = parse_reminder_text(message)
        logger.info("CHAT AGENT PARSED title=%r date=%s time=%s", parsed["title"], parsed["date"], parsed["time"])
        record = Reminder(user_id=user_id, title=parsed["title"], description=f"Created through Chat Agent: {message}",
                          place=None, reminder_date=parsed["date"], reminder_time=parsed["time"], status="pending", reminder_type="chat")
        logger.info("CHAT AGENT DB INSERT reminder title=%r", record.title)
        db.session.add(record)
        db.session.commit()
        logger.info("CHAT AGENT DB COMMIT id=%s", record.id)
        saved = Reminder.query.filter_by(id=record.id, user_id=user_id).first()
        if not saved:
            return {"success": False, "created": False, "verified": False, "reply": "❌ I could not verify the reminder. Nothing was confirmed."}
        logger.info("CHAT AGENT DB VERIFIED id=%s", saved.id)
        return {"success": True, "created": True, "verified": True, "type": "reminder", "reminder": _serialize_reminder(saved), "reply": "✅ Yes! Reminder added successfully."}
    except Exception:
        db.session.rollback()
        logger.exception("CHAT AGENT ERROR")
        return {"success": False, "created": False, "verified": False, "reply": "❌ I could not save the reminder. Nothing was added."}

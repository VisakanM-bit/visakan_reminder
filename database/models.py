# ============================================================
# BDAY REMINDER
# DATABASE MODELS
# ============================================================

from flask_login import UserMixin

from database import db


# ============================================================
# USER MODEL
# ============================================================

class User(UserMixin, db.Model):

    __tablename__ = "users"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    name = db.Column(
        db.String(100),
        nullable=False
    )

    email = db.Column(
        db.String(150),
        unique=True,
        nullable=False
    )

    password_hash = db.Column(
        db.String(255),
        nullable=False
    )

    # --------------------------------------------------------
    # RELATIONSHIPS
    # --------------------------------------------------------

    birthdays = db.relationship(
        "Birthday",
        backref="user",
        lazy=True,
        cascade="all, delete-orphan"
    )

    reminders = db.relationship(
        "Reminder",
        backref="user",
        lazy=True,
        cascade="all, delete-orphan"
    )


# ============================================================
# BIRTHDAY MODEL
# ============================================================

class Birthday(db.Model):

    __tablename__ = "birthdays"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    name = db.Column(
        db.String(100),
        nullable=False
    )

    birthday = db.Column(
        db.Date,
        nullable=False
    )

    phone = db.Column(
        db.String(30),
        nullable=True
    )

    relationship = db.Column(
        db.String(100),
        nullable=True
    )

    notes = db.Column(
        db.Text,
        nullable=True
    )


# ============================================================
# REMINDER MODEL
# ============================================================

class Reminder(db.Model):

    __tablename__ = "reminders"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    # --------------------------------------------------------
    # WHAT
    # --------------------------------------------------------

    title = db.Column(
        db.String(200),
        nullable=False
    )

    # --------------------------------------------------------
    # DESCRIPTION
    # --------------------------------------------------------

    description = db.Column(
        db.Text,
        nullable=True
    )

    # --------------------------------------------------------
    # WHERE
    # --------------------------------------------------------

    place = db.Column(
        db.String(255),
        nullable=True
    )

    # --------------------------------------------------------
    # DATE
    # --------------------------------------------------------

    reminder_date = db.Column(
        db.Date,
        nullable=False
    )

    # --------------------------------------------------------
    # TIME
    # --------------------------------------------------------

    reminder_time = db.Column(
        db.Time,
        nullable=False
    )

    # --------------------------------------------------------
    # STATUS
    # --------------------------------------------------------

    status = db.Column(
        db.String(20),
        nullable=False,
        default="pending"
    )

    # --------------------------------------------------------
    # TYPE
    # --------------------------------------------------------

    reminder_type = db.Column(
        db.String(50),
        nullable=False,
        default="custom"
    )

    def __repr__(self):

        return (
            f"<Reminder "
            f"{self.id}: "
            f"{self.title}>"
        )
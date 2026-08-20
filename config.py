import os

from pathlib import Path


# ============================================================
# PROJECT BASE DIRECTORY
# ============================================================

BASE_DIR = Path(__file__).resolve().parent


# ============================================================
# CONFIGURATION
# ============================================================

class Config:

    # --------------------------------------------------------
    # SECRET KEY
    # --------------------------------------------------------

    SECRET_KEY = os.environ.get(
        "SECRET_KEY",
        "bday-reminder-development-secret-key"
    )


    # --------------------------------------------------------
    # DATABASE
    # --------------------------------------------------------
    #
    # Render:
    #   DATABASE_URL → Supabase PostgreSQL
    #
    # Local:
    #   SQLite fallback
    #
    # --------------------------------------------------------

    DATABASE_URL = os.environ.get(
        "DATABASE_URL"
    )


    if DATABASE_URL:

        if DATABASE_URL.startswith(
            "postgresql://"
        ):

            DATABASE_URL = DATABASE_URL.replace(
                "postgresql://",
                "postgresql+psycopg2://",
                1
            )


        SQLALCHEMY_DATABASE_URI = (
            DATABASE_URL
        )


    else:

        SQLALCHEMY_DATABASE_URI = (
            f"sqlite:///{BASE_DIR / 'bday_reminder.db'}"
        )


    # --------------------------------------------------------
    # SQLALCHEMY
    # --------------------------------------------------------

    SQLALCHEMY_TRACK_MODIFICATIONS = False


    SQLALCHEMY_ENGINE_OPTIONS = {

        "pool_pre_ping": True

    }


    # --------------------------------------------------------
    # JSON
    # --------------------------------------------------------

    JSON_SORT_KEYS = False


    # --------------------------------------------------------
    # SESSION
    # --------------------------------------------------------

    SESSION_COOKIE_HTTPONLY = True

    SESSION_COOKIE_SAMESITE = "Lax"


    # --------------------------------------------------------
    # RENDER / HTTPS
    # --------------------------------------------------------

    SESSION_COOKIE_SECURE = (

        os.environ.get(
            "SESSION_COOKIE_SECURE",
            "0"
        ).lower()

        in (
            "1",
            "true",
            "yes"
        )

    )


    # --------------------------------------------------------
    # APPLICATION TIMEZONE
    # --------------------------------------------------------

    TIMEZONE = os.environ.get(
        "APP_TIMEZONE",
        "Asia/Kolkata"
    )
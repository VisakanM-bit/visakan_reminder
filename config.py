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
    #
    # Render:
    #   DATABASE_URL environment variable
    #
    # Local:
    #   SQLite fallback
    # --------------------------------------------------------

    SQLALCHEMY_DATABASE_URI = (
        os.environ.get("DATABASE_URL")
        or
        f"sqlite:///{BASE_DIR / 'bday_reminder.db'}"
    )


    SQLALCHEMY_TRACK_MODIFICATIONS = False


    # --------------------------------------------------------
    # SQLALCHEMY ENGINE OPTIONS
    # --------------------------------------------------------

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
    #
    # Local development remains normal HTTP.
    # Production HTTPS can be enabled by environment.
    # --------------------------------------------------------

    SESSION_COOKIE_SECURE = (
        os.environ.get(
            "SESSION_COOKIE_SECURE",
            "0"
        ).lower()
        in ("1", "true", "yes")
    )


    # --------------------------------------------------------
    # APPLICATION TIMEZONE
    # --------------------------------------------------------

    TIMEZONE = os.environ.get(
        "APP_TIMEZONE",
        "Asia/Kolkata"
    )
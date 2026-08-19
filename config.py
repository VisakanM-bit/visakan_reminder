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
    # PRODUCTION / RENDER:
    #   Uses DATABASE_URL from Render Environment Variables
    #
    # LOCAL:
    #   Falls back to SQLite
    #
    # For TiDB Cloud Starter, DATABASE_URL should contain:
    #
    # mysql+pymysql://USERNAME:PASSWORD@HOST:4000/DATABASE
    # ?ssl_verify_cert=true&ssl_verify_identity=true
    # --------------------------------------------------------

    DATABASE_URL = os.environ.get("DATABASE_URL")


    if DATABASE_URL:

        # ----------------------------------------------------
        # TiDB Cloud Starter TLS
        #
        # TiDB requires TLS for public connections.
        # Add the required SSL parameters automatically
        # if they are not already present.
        # ----------------------------------------------------

        if DATABASE_URL.startswith(
            "mysql+pymysql://"
        ):

            if "ssl_verify_cert=" not in DATABASE_URL:

                separator = (
                    "&"
                    if "?" in DATABASE_URL
                    else "?"
                )

                DATABASE_URL += (
                    separator
                    + "ssl_verify_cert=true"
                    + "&ssl_verify_identity=true"
                )


        SQLALCHEMY_DATABASE_URI = DATABASE_URL


    else:

        # ----------------------------------------------------
        # LOCAL DEVELOPMENT
        # ----------------------------------------------------

        SQLALCHEMY_DATABASE_URI = (
            f"sqlite:///{BASE_DIR / 'bday_reminder.db'}"
        )


    # --------------------------------------------------------
    # SQLALCHEMY
    # --------------------------------------------------------

    SQLALCHEMY_TRACK_MODIFICATIONS = False


    # --------------------------------------------------------
    # SQLALCHEMY ENGINE OPTIONS
    # --------------------------------------------------------

    SQLALCHEMY_ENGINE_OPTIONS = {

        "pool_pre_ping": True,

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
    # SESSION COOKIE SECURITY
    #
    # Local:
    #   HTTP is allowed
    #
    # Render:
    #   Set SESSION_COOKIE_SECURE=1
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
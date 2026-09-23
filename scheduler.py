from apscheduler.schedulers.background import BackgroundScheduler
import time

from notification_service import send_due_push_notifications
from email_service import send_due_email_notifications


# ============================================================
# PUSH NOTIFICATION CHECK
# ============================================================

def check_push_notifications(app):
    """
    Check and send all due Web Push / Android notifications.

    This job is independent from email so a slow email operation
    cannot block push notification processing.
    """
    with app.app_context():
        start_time = time.time()

        print("⏰ Checking push notifications...")

        try:
            send_due_push_notifications()

            duration = time.time() - start_time

            print(
                f"✅ Push notification check completed "
                f"in {duration:.2f}s."
            )

        except Exception as error:
            duration = time.time() - start_time

            print("❌ Push notification error:")
            print(f"   {error}")
            print(
                f"   Push check stopped after "
                f"{duration:.2f}s."
            )


# ============================================================
# EMAIL NOTIFICATION CHECK
# ============================================================

def check_email_notifications(app):
    """
    Check and send all due email notifications.

    This job is independent from push so a slow SMTP operation
    cannot block Android/Web Push notifications.
    """
    with app.app_context():
        start_time = time.time()

        print("📧 Checking email notifications...")

        try:
            send_due_email_notifications()

            duration = time.time() - start_time

            print(
                f"✅ Email notification check completed "
                f"in {duration:.2f}s."
            )

        except Exception as error:
            duration = time.time() - start_time

            print("❌ Email notification error:")
            print(f"   {error}")
            print(
                f"   Email check stopped after "
                f"{duration:.2f}s."
            )


# ============================================================
# START BACKGROUND SCHEDULER
# ============================================================

def start_scheduler(app):
    """
    Start independent notification jobs.

    PUSH:
        Runs every 30 seconds.
        max_instances=1 prevents overlapping push checks.

    EMAIL:
        Runs every 30 seconds.
        max_instances=1 prevents overlapping email checks.

    The two jobs are completely independent. A slow or blocked
    email operation cannot stop the push notification job.
    """

    scheduler = BackgroundScheduler(
        timezone="Asia/Kolkata"
    )

    # --------------------------------------------------------
    # PUSH NOTIFICATION JOB
    # --------------------------------------------------------

    scheduler.add_job(
        func=check_push_notifications,
        args=[app],
        trigger="interval",
        seconds=30,
        id="push_notification_checker",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
        misfire_grace_time=120
    )

    # --------------------------------------------------------
    # EMAIL NOTIFICATION JOB
    # --------------------------------------------------------

    scheduler.add_job(
        func=check_email_notifications,
        args=[app],
        trigger="interval",
        seconds=30,
        id="email_notification_checker",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
        misfire_grace_time=120
    )

    # --------------------------------------------------------
    # START SCHEDULER
    # --------------------------------------------------------

    scheduler.start()

    print("⏰ Reminder scheduler started.")
    print("📱 Web Push background notifications enabled.")
    print("📧 Email notification scheduler enabled.")
    print(
        "🔄 Push and email checks run independently "
        "every 30 seconds."
    )

    return scheduler

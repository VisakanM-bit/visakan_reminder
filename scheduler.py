from apscheduler.schedulers.background import BackgroundScheduler
import time

from notification_service import send_due_push_notifications
from email_service import send_due_email_notifications


# ============================================================
# PUSH NOTIFICATION CHECK
# ============================================================

def check_push_notifications(app):
    with app.app_context():
        print("⏰ Checking push notifications...")

        start_time = time.time()

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
    with app.app_context():
        print("📧 Checking email notifications...")

        start_time = time.time()

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
    scheduler = BackgroundScheduler(
        timezone="Asia/Kolkata"
    )

    # --------------------------------------------------------
    # PUSH JOB
    # --------------------------------------------------------
    # Runs independently from email.
    # A slow email connection cannot block push notifications.
    # max_instances=1 prevents duplicate overlapping push jobs.
    # coalesce=True prevents a backlog of missed executions.
    # misfire_grace_time allows a delayed scheduler run to still
    # execute if it was only briefly missed.
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
    # EMAIL JOB
    # --------------------------------------------------------
    # Runs independently from push.
    # A slow SMTP/email operation cannot block push checks.
    # max_instances=1 prevents duplicate overlapping emails.
    # coalesce=True prevents a backlog of old checks.
    # misfire_grace_time allows a delayed scheduler run to still
    # execute if it was only briefly missed.
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

    scheduler.start()

    print("⏰ Reminder scheduler started.")
    print("📱 Web Push background notifications enabled.")
    print("📧 Email notification scheduler enabled.")
    print("🔄 Push and email checks run independently every 30 seconds.")

    return scheduler

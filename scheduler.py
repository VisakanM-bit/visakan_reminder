from apscheduler.schedulers.background import BackgroundScheduler
import time

from notification_service import (
    send_due_push_notifications
)

from email_service import (
    send_due_email_notifications
)

from resend_email_service import (
    send_due_resend_notifications
)


# ============================================================
# PUSH NOTIFICATION JOB
# ============================================================

def check_push_notifications(app):
    with app.app_context():

        print("📱 Checking push notifications...")

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
# GMAIL SMTP EMAIL JOB
# ============================================================

def check_smtp_email_notifications(app):
    with app.app_context():

        print("📧 Checking Gmail SMTP email notifications...")

        start_time = time.time()

        try:
            send_due_email_notifications()

            duration = time.time() - start_time

            print(
                f"✅ Gmail SMTP email check completed "
                f"in {duration:.2f}s."
            )

        except Exception as error:

            duration = time.time() - start_time

            print("❌ Gmail SMTP email error:")
            print(f"   {error}")
            print(
                f"   Gmail SMTP check stopped after "
                f"{duration:.2f}s."
            )


# ============================================================
# RESEND EMAIL JOB
# ============================================================

def check_resend_email_notifications(app):
    with app.app_context():

        print("📨 Checking Resend email notifications...")

        start_time = time.time()

        try:
            send_due_resend_notifications()

            duration = time.time() - start_time

            print(
                f"✅ Resend email check completed "
                f"in {duration:.2f}s."
            )

        except Exception as error:

            duration = time.time() - start_time

            print("❌ Resend email error:")
            print(f"   {error}")
            print(
                f"   Resend check stopped after "
                f"{duration:.2f}s."
            )


# ============================================================
# START SCHEDULER
# ============================================================

def start_scheduler(app):

    scheduler = BackgroundScheduler(
        timezone="Asia/Kolkata"
    )

    # --------------------------------------------------------
    # PUSH JOB
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
    # GMAIL SMTP JOB
    # --------------------------------------------------------

    scheduler.add_job(
        func=check_smtp_email_notifications,
        args=[app],
        trigger="interval",
        seconds=30,
        id="smtp_email_checker",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
        misfire_grace_time=120
    )

    # --------------------------------------------------------
    # RESEND JOB
    # --------------------------------------------------------

    scheduler.add_job(
        func=check_resend_email_notifications,
        args=[app],
        trigger="interval",
        seconds=30,
        id="resend_email_checker",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
        misfire_grace_time=120
    )

    # --------------------------------------------------------
    # START
    # --------------------------------------------------------

    scheduler.start()

    print("⏰ Reminder scheduler started.")
    print("📱 Web Push background notifications enabled.")
    print("📧 Gmail SMTP email scheduler enabled.")
    print("📨 Resend HTTPS email scheduler enabled.")

    return scheduler

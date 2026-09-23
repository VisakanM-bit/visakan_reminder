from apscheduler.schedulers.background import BackgroundScheduler
import time

from notification_service import (
    send_due_push_notifications
)

from email_service import (
    send_due_email_notifications
)


def check_reminders(app):
    with app.app_context():
        print("⏰ Checking reminders...")

        # --------------------------------------------------------
        # PUSH NOTIFICATION CHECK
        # --------------------------------------------------------
        push_start = time.time()

        try:
            send_due_push_notifications()

            push_duration = time.time() - push_start

            print(
                f"✅ Push notification check completed "
                f"in {push_duration:.2f}s."
            )

        except Exception as error:
            push_duration = time.time() - push_start

            print("❌ Push notification error:")
            print(f"   {error}")
            print(
                f"   Push check stopped after "
                f"{push_duration:.2f}s."
            )

        # --------------------------------------------------------
        # EMAIL / SMTP NOTIFICATION CHECK
        # --------------------------------------------------------
        email_start = time.time()

        try:
            send_due_email_notifications()

            email_duration = time.time() - email_start

            print(
                f"📧 Email notification check completed "
                f"in {email_duration:.2f}s."
            )

        except Exception as error:
            email_duration = time.time() - email_start

            print("❌ Email notification error:")
            print(f"   {error}")
            print(
                f"   Email check stopped after "
                f"{email_duration:.2f}s."
            )

        # --------------------------------------------------------
        # TOTAL SCHEDULER EXECUTION TIME
        # --------------------------------------------------------
        total_duration = time.time() - push_start

        print(
            f"⏱️ Total reminder check completed "
            f"in {total_duration:.2f}s."
        )


def start_scheduler(app):
    scheduler = BackgroundScheduler(
        timezone="Asia/Kolkata"
    )

    scheduler.add_job(
        func=check_reminders,
        args=[app],
        trigger="interval",
        seconds=30,
        id="reminder_checker",
        replace_existing=True,
        max_instances=1,
        coalesce=True
    )

    scheduler.start()

    print("⏰ Reminder scheduler started.")
    print("📱 Web Push background notifications enabled.")
    print("📧 SMTP email notification scheduler enabled.")

    return scheduler

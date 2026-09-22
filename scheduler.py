# ============================================================
# BDAY REMINDER
# BACKGROUND REMINDER SCHEDULER
# ============================================================

from apscheduler.schedulers.background import BackgroundScheduler

from notification_service import (
    send_due_push_notifications
)

from email_service import (
    send_due_email_notifications
)


# ============================================================
# CHECK REMINDERS
# ============================================================
#
# Runs every 30 seconds.
#
# It checks two independent notification channels:
#
# 1. Web Push / Android notification
# 2. Email through Gmail SMTP
#
# A failure in one channel does not stop the other channel.
#
# ============================================================

def check_reminders(app):

    with app.app_context():

        print(
            "⏰ Checking reminders..."
        )

        # ====================================================
        # WEB PUSH
        # ====================================================

        try:

            send_due_push_notifications()

            print(
                "✅ Push notification check completed."
            )

        except Exception as error:

            print(
                "❌ Push notification error:"
            )

            print(
                f"   {error}"
            )

        # ====================================================
        # EMAIL
        # ====================================================

        try:

            send_due_email_notifications()

            print(
                "📧 Email notification check completed."
            )

        except Exception as error:

            print(
                "❌ Email notification error:"
            )

            print(
                f"   {error}"
            )


# ============================================================
# START SCHEDULER
# ============================================================

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

    print(
        "⏰ Reminder scheduler started."
    )

    print(
        "📱 Web Push background notifications enabled."
    )

    print(
        "📧 SMTP email notification scheduler enabled."
    )

    return scheduler

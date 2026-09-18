# ============================================================
# BDAY REMINDER
# BACKGROUND REMINDER SCHEDULER
# ============================================================

from apscheduler.schedulers.background import BackgroundScheduler

from notification_service import send_due_push_notifications


# ============================================================
# CHECK REMINDERS / SEND WEB PUSH
# ============================================================

def check_reminders(app):

    with app.app_context():

        print(
            "⏰ Checking reminders and push notifications..."
        )

        try:

            # ------------------------------------------------
            # Send Web Push notifications
            #
            # This works independently of whether the PWA
            # is currently open.
            # ------------------------------------------------

            send_due_push_notifications()

            print(
                "✅ Push notification check completed."
            )

        except Exception as error:

            print(
                "❌ Scheduler error:"
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

    return scheduler

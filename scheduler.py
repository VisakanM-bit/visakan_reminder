from datetime import datetime

from apscheduler.schedulers.background import BackgroundScheduler

from database import db
from database.models import Reminder


# ============================================================
# CHECK REMINDERS
# ============================================================

def check_reminders(app):

    with app.app_context():

        now = datetime.now()

        reminders = Reminder.query.filter(
            Reminder.status == "pending",
            Reminder.reminder_date <= now.date()
        ).all()


        for reminder in reminders:

            reminder_datetime = datetime.combine(
                reminder.reminder_date,
                reminder.reminder_time
            )


            if reminder_datetime <= now:

                print(
                    "🔔 DUE REMINDER"
                )

                print(
                    f"   ID: {reminder.id}"
                )

                print(
                    f"   Title: {reminder.title}"
                )

                print(
                    f"   Date: {reminder.reminder_date}"
                )

                print(
                    f"   Time: {reminder.reminder_time}"
                )

                # IMPORTANT:
                #
                # We do NOT mark it completed here.
                #
                # The browser notification appears first.
                #
                # User clicks "Done"
                #       ↓
                # /api/reminders/<id>/complete
                #       ↓
                # MySQL status = completed


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


    return scheduler
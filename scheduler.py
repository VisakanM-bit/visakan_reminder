from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
from zoneinfo import ZoneInfo
import time

from notification_service import send_due_push_notifications
from email_service import send_due_email_notifications
from resend_email_service import send_due_resend_notifications


IST = ZoneInfo("Asia/Kolkata")


# ============================================================
# PUSH
# ============================================================

def check_push_notifications(app):
    with app.app_context():
        print("📱 Checking push notifications...", flush=True)

        start = time.time()

        try:
            send_due_push_notifications()

            print(
                f"✅ Push check completed in "
                f"{time.time() - start:.2f}s.",
                flush=True
            )

        except Exception as error:
            print("❌ Push notification error:", flush=True)
            print(f"   {error}", flush=True)


# ============================================================
# GMAIL SMTP
# ============================================================

def check_smtp_email_notifications(app):
    with app.app_context():
        print("📧 Checking Gmail SMTP email notifications...", flush=True)

        start = time.time()

        try:
            send_due_email_notifications()

            print(
                f"✅ Gmail SMTP check completed in "
                f"{time.time() - start:.2f}s.",
                flush=True
            )

        except Exception as error:
            print("❌ Gmail SMTP email error:", flush=True)
            print(f"   {error}", flush=True)


# ============================================================
# RESEND
# ============================================================

def check_resend_email_notifications(app):
    with app.app_context():
        print("📨 Checking Resend email notifications...", flush=True)

        start = time.time()

        try:
            send_due_resend_notifications()

            print(
                f"✅ Resend email check completed in "
                f"{time.time() - start:.2f}s.",
                flush=True
            )

        except Exception as error:
            print("❌ Resend email error:", flush=True)
            print(f"   {error}", flush=True)


# ============================================================
# START SCHEDULER
# ============================================================

def start_scheduler(app):

    scheduler = BackgroundScheduler(
        timezone=IST,
        daemon=True
    )

    # --------------------------------------------------------
    # PUSH
    # --------------------------------------------------------

    scheduler.add_job(
        check_push_notifications,
        args=[app],
        trigger="interval",
        seconds=30,
        id="push_notification_checker",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
        misfire_grace_time=120,
        next_run_time=datetime.now(IST)
    )

    # --------------------------------------------------------
    # GMAIL SMTP
    # --------------------------------------------------------

    scheduler.add_job(
        check_smtp_email_notifications,
        args=[app],
        trigger="interval",
        seconds=30,
        id="smtp_email_checker",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
        misfire_grace_time=120,
        next_run_time=datetime.now(IST)
    )

    # --------------------------------------------------------
    # RESEND
    # --------------------------------------------------------

    scheduler.add_job(
        check_resend_email_notifications,
        args=[app],
        trigger="interval",
        seconds=30,
        id="resend_email_checker",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
        misfire_grace_time=120,
        next_run_time=datetime.now(IST)
    )

    scheduler.start()

    print("⏰ Reminder scheduler started.", flush=True)
    print("📱 Web Push background notifications enabled.", flush=True)
    print("📧 Gmail SMTP email scheduler enabled.", flush=True)
    print("📨 Resend HTTPS email scheduler enabled.", flush=True)

    # --------------------------------------------------------
    # VERIFY SCHEDULED JOBS
    # --------------------------------------------------------

    print("🔎 Scheduled jobs:", flush=True)

    for job in scheduler.get_jobs():
        print(
            f"   {job.id} → next run: {job.next_run_time}",
            flush=True
        )

    return scheduler

# ============================================================
# BDAY REMINDER
# CENTRAL WEB PUSH SERVICE
# ============================================================

import json
import os

from datetime import datetime

from flask import Blueprint, jsonify, request
from flask_login import current_user, login_required

from pywebpush import webpush, WebPushException

from database import db
from database.models import PushSubscription


# ============================================================
# BLUEPRINT
# ============================================================

push_bp = Blueprint(
    "push",
    __name__
)


# ============================================================
# VAPID CONFIGURATION
# ============================================================

VAPID_PUBLIC_KEY = os.environ.get(
    "VAPID_PUBLIC_KEY",
    ""
)

VAPID_PRIVATE_KEY = os.environ.get(
    "VAPID_PRIVATE_KEY",
    ""
)

VAPID_CLAIM_EMAIL = os.environ.get(
    "VAPID_CLAIM_EMAIL",
    ""
)


# ============================================================
# CONFIGURATION CHECK
# ============================================================

def push_configuration_ready():

    return bool(
        VAPID_PUBLIC_KEY
        and VAPID_PRIVATE_KEY
        and VAPID_CLAIM_EMAIL
    )


# ============================================================
# GET VAPID PUBLIC KEY
# ============================================================

@push_bp.get(
    "/api/push/vapid-public-key"
)
@login_required
def get_vapid_public_key():

    if not VAPID_PUBLIC_KEY:

        return jsonify({
            "success": False,
            "error":
                "VAPID public key is not configured."
        }), 500

    return jsonify({
        "success": True,
        "publicKey":
            VAPID_PUBLIC_KEY
    })


# ============================================================
# SAVE / UPDATE PUSH SUBSCRIPTION
# ============================================================

@push_bp.post(
    "/api/push/subscribe"
)
@login_required
def subscribe():

    data = request.get_json(
        silent=True
    ) or {}

    endpoint = data.get(
        "endpoint"
    )

    keys = data.get(
        "keys"
    ) or {}

    p256dh = keys.get(
        "p256dh"
    )

    auth = keys.get(
        "auth"
    )


    # --------------------------------------------------------
    # Validate subscription
    # --------------------------------------------------------

    if not endpoint:

        return jsonify({
            "success": False,
            "error":
                "Push endpoint is missing."
        }), 400


    if not p256dh:

        return jsonify({
            "success": False,
            "error":
                "Push p256dh key is missing."
        }), 400


    if not auth:

        return jsonify({
            "success": False,
            "error":
                "Push auth key is missing."
        }), 400


    # --------------------------------------------------------
    # Find existing subscription
    # --------------------------------------------------------

    subscription = (
        PushSubscription.query
        .filter_by(
            endpoint=endpoint
        )
        .first()
    )


    # --------------------------------------------------------
    # Update existing subscription
    # --------------------------------------------------------

    if subscription:

        subscription.user_id = (
            current_user.id
        )

        subscription.p256dh = (
            p256dh
        )

        subscription.auth = (
            auth
        )

        subscription.active = True

        subscription.updated_at = (
            datetime.utcnow()
        )


    # --------------------------------------------------------
    # Create new subscription
    # --------------------------------------------------------

    else:

        subscription = PushSubscription(

            user_id=current_user.id,

            endpoint=endpoint,

            p256dh=p256dh,

            auth=auth,

            active=True

        )

        db.session.add(
            subscription
        )


    # --------------------------------------------------------
    # Save
    # --------------------------------------------------------

    try:

        db.session.commit()

    except Exception as error:

        db.session.rollback()

        print(
            "❌ Failed to save push subscription:",
            error
        )

        return jsonify({
            "success": False,
            "error":
                "Unable to save push subscription."
        }), 500


    print(
        "✅ Push subscription saved."
    )

    print(
        f"   User ID: {current_user.id}"
    )

    print(
        f"   Subscription ID: {subscription.id}"
    )


    return jsonify({

        "success":
            True,

        "message":
            "Push subscription saved.",

        "subscription_id":
            subscription.id

    })


# ============================================================
# UNSUBSCRIBE
# ============================================================

@push_bp.post(
    "/api/push/unsubscribe"
)
@login_required
def unsubscribe():

    data = request.get_json(
        silent=True
    ) or {}

    endpoint = data.get(
        "endpoint"
    )


    if not endpoint:

        return jsonify({
            "success": False,
            "error":
                "Push endpoint is missing."
        }), 400


    subscription = (
        PushSubscription.query
        .filter_by(
            endpoint=endpoint,
            user_id=current_user.id
        )
        .first()
    )


    if subscription:

        subscription.active = False

        subscription.updated_at = (
            datetime.utcnow()
        )

        db.session.commit()


    return jsonify({
        "success": True
    })


# ============================================================
# GET ACTIVE SUBSCRIPTIONS FOR USER
# ============================================================

def get_user_subscriptions(
    user_id
):

    return (
        PushSubscription.query
        .filter_by(
            user_id=user_id,
            active=True
        )
        .all()
    )


# ============================================================
# SEND PUSH TO ONE SUBSCRIPTION
# ============================================================

def send_push_to_subscription(
    subscription,
    payload
):

    if not push_configuration_ready():

        print(
            "❌ Web Push configuration is incomplete."
        )

        return False


    subscription_info = {

        "endpoint":
            subscription.endpoint,

        "keys": {

            "p256dh":
                subscription.p256dh,

            "auth":
                subscription.auth

        }

    }


    try:

        webpush(

            subscription_info=
                subscription_info,

            data=json.dumps(
                payload
            ),

            vapid_private_key=
                VAPID_PRIVATE_KEY,

            vapid_claims={

                "sub":
                    VAPID_CLAIM_EMAIL

            }

        )


        print(
            "📱 Web Push sent successfully."
        )

        print(
            f"   Subscription ID: "
            f"{subscription.id}"
        )


        return True


    except WebPushException as error:

        print(
            "❌ Web Push failed:"
        )

        print(
            f"   {error}"
        )


        response = getattr(
            error,
            "response",
            None
        )

        status_code = getattr(
            response,
            "status_code",
            None
        )


        # ----------------------------------------------------
        # Expired / invalid browser subscription
        # ----------------------------------------------------

        if status_code in (
            404,
            410
        ):

            print(
                "🗑️ Push subscription expired."
            )

            subscription.active = False

            try:

                db.session.commit()

            except Exception:

                db.session.rollback()


        return False


    except Exception as error:

        print(
            "❌ Unexpected Web Push error:"
        )

        print(
            f"   {error}"
        )

        return False


# ============================================================
# SEND PUSH TO USER
# ============================================================

def send_push_to_user(
    user_id,
    title,
    body,
    notification_type="reminder",
    alarm_id=None,
    source_id=None,
    url="/"
):

    subscriptions = (
        get_user_subscriptions(
            user_id
        )
    )


    if not subscriptions:

        print(
            "ℹ️ No active push subscriptions."
        )

        print(
            f"   User ID: {user_id}"
        )

        return False


    payload = {

        "title":
            title,

        "body":
            body,

        "type":
            notification_type,

        "alarm_id":
            alarm_id,

        "source_id":
            source_id,

        "url":
            url

    }


    sent_any = False


    for subscription in subscriptions:

        success = (
            send_push_to_subscription(
                subscription,
                payload
            )
        )

        if success:

            sent_any = True


    return sent_any


# ============================================================
# PUSH SERVICE STATUS
# ============================================================

def get_push_status():

    return {

        "configured":
            push_configuration_ready(),

        "public_key":
            bool(
                VAPID_PUBLIC_KEY
            ),

        "private_key":
            bool(
                VAPID_PRIVATE_KEY
            ),

        "claim_email":
            bool(
                VAPID_CLAIM_EMAIL
            )

    }

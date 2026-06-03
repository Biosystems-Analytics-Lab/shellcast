import logging
import os
from datetime import date, datetime, timezone

import requests
from core.notifications.inbound import handle_stop_start

# Removed unused imports to fix F401
from firebase_admin import auth
from flask import Blueprint, jsonify, request
from models import db
from models.CMUProbability import CMUProbability
from models.Lease import Lease
from models.User import User
from models.UserLease import UserLease
from routes.authentication import user_required
from routes.validators.profile_info_validator import ProfileInfoValidator
from sqlalchemy.exc import IntegrityError

api = Blueprint("api", __name__)

# State identifier for FL
STATE = "FL"


def _construct_user_info_response(user_obj):
    user_info_dict = {
        "email": user_obj.email,
        "email_pref": user_obj.email_pref,
        "text_pref": user_obj.text_pref,
        "prob_pref": user_obj.prob_pref,
        "text_consent": user_obj.text_consent,
        "phone_verified": getattr(user_obj, "phone_verified", False),
        "phone_verified_at": getattr(user_obj, "phone_verified_at", None),
        "phone_verif_count": getattr(user_obj, "phone_verif_count", None),
        "phone_verif_count_date": getattr(user_obj, "phone_verif_count_date", None),
    }
    if user_obj.phone_number is not None:
        user_info_dict["phone_number"] = user_obj.phone_number
    return user_info_dict


@api.route("/user-info", methods=["GET", "POST"])
@user_required
def user_info(user):
    """
    Returns the user's info if a GET request.  Updates the user's info if a POST request.
    """

    if request.method == "GET":
        return _construct_user_info_response(user)
    else:  # request.method == 'POST'
        # validate the uploaded info
        validator = ProfileInfoValidator(request.json)
        if validator.validate():
            now = datetime.now(timezone.utc)
            prev_email_pref = user.email_pref
            if validator.email_pref:
                user.email = validator.email or ""
            user.phone_number = validator.phone_number
            user.email_pref = validator.email_pref
            user.text_pref = validator.text_pref
            user.prob_pref = validator.prob_pref
            user.text_consent = validator.text_consent
            if validator.email_pref != prev_email_pref:
                if validator.email_pref:
                    user.email_opt_in_date = now
                    user.email_opt_out_date = None
                else:
                    user.email_opt_out_date = now
            user.touch_updated(now)
            db.session.add(user)
            db.session.commit()
            return _construct_user_info_response(user)
        return {"errors": validator.errors}, 400


@api.route("/verify-phone/send", methods=["POST"])
@user_required
def send_phone_verification(user):
    """
    Send a one-time SMS to verify the user's phone number for text alerts.

    Preconditions (effective values):
    - User is not deleted.
    - Effective phone_number is present.
    - Effective text_pref and text_consent are enabled.
    """
    if user.deleted:
        return {"errors": ["User account is deleted."]}, 400

    payload = request.get_json(silent=True) or {}
    phone_number = (payload.get("phone_number") or user.phone_number or "").strip()

    if "text_pref" in payload:
        text_pref = bool(payload.get("text_pref"))
    else:
        text_pref = user.text_pref

    if "text_consent" in payload:
        text_consent = bool(payload.get("text_consent"))
    else:
        text_consent = user.text_consent

    if not phone_number:
        return {"errors": ["Phone number is required to send verification SMS."]}, 400

    if not text_pref or not text_consent:
        return {
            "errors": [
                "Text notifications and consent must be enabled before sending verification SMS."
            ]
        }, 400

    # Enforce a maximum of 3 successful verification sends per day per user.
    now = datetime.utcnow()
    today = now.date()
    last_dt = getattr(user, "phone_verif_count_date", None)
    if isinstance(last_dt, date) and not isinstance(last_dt, datetime):
        last_date = last_dt
    elif last_dt:
        last_date = last_dt.date()
    else:
        last_date = None
    current_count = getattr(user, "phone_verif_count", 0) or 0

    if last_date == today and current_count >= 3:
        return {
            "errors": [
                "You have reached the maximum number of phone verification attempts for today. Please try again tomorrow."
            ]
        }, 429

    from routes.cron import _send_bandwidth_message_single

    verification_text = (
        f"ShellCast-{STATE}: Your phone number is confirmed for closure alerts. "
        "Reply STOP to unsubscribe."
    )

    try:
        response = _send_bandwidth_message_single(phone_number, verification_text)
    except Exception as e:  # pragma: no cover - defensive logging
        logging.error(f"Failed to send phone verification SMS for user {user.id}: {e}")
        return {"errors": ["Failed to send verification SMS."]}, 500

    if not response:
        return {"errors": ["Failed to send verification SMS."]}, 500

    # Persist effective values and bump verification counters
    user.phone_number = phone_number
    user.text_pref = text_pref
    user.text_consent = text_consent
    if last_date == today:
        user.phone_verif_count = current_count + 1
        user.phone_verif_count_date = last_dt
    else:
        user.phone_verif_count = 1
        user.phone_verif_count_date = now
    user.phone_verified = True
    user.phone_verified_at = now
    user.touch_updated(now)
    db.session.add(user)
    db.session.commit()

    _log_sms_to_nc(
        state=STATE,
        user_id=user.id,
        phone_number=user.phone_number,
        direction="outbound",
        message_id=response.id if getattr(response, "id", None) else None,
        template_name="sms_verification",
        send_success=True,
    )

    return _construct_user_info_response(user), 200


@api.route("/delete-account")
@user_required
def delete_account(user):
    """
    Soft-delete: remove Firebase user, clear PII, set users.deleted=True.
    Does not DELETE the users row (see docs/DATABASE_STORED_PROCEDURES.md).
    """
    try:
        # delete the user from Firebase
        auth.delete_user(user.firebase_uid)

        # clear PII
        user.firebase_uid = None
        user.email = None
        user.phone_number = None

        # clear preferences
        user.email_pref = User.DEFAULT_email_pref
        user.text_pref = User.DEFAULT_text_pref
        user.prob_pref = User.DEFAULT_prob_pref
        user.text_consent = User.DEFAULT_text_consent

        # mark user record as deleted
        user.deleted = True
        user.touch_updated()

        db.session.add(user)
        db.session.commit()
    except Exception as err:
        print(err)
        return {"errors": ["Could not delete user."]}, 400
    return "Success"


@api.route("/lease-probs")
@user_required
def get_lease_closure_probabilities(user):
    """
    Returns the user's lease closure probabilities.
    """
    leases = db.session.query(UserLease).filter_by(user_id=user.id, deleted=False).all()

    def get_lease_prob_for_lease(lease):
        prob_dict = {
            "lease_id": lease.lease_id,
            "cmu_id": lease.leases.cmu_id,
            "sh_id": lease.leases.cmus.sh_id,
            "sh_name": lease.leases.cmus.sh_name,
            "latitude": lease.leases.latitude,
            "longitude": lease.leases.longitude,
        }
        lease_prob = lease.getLatestProbability()
        if lease_prob:
            prob_dict["prob_1d_perc"] = lease_prob.prob_1d_perc
        return prob_dict

    lease_list = list(map(get_lease_prob_for_lease, leases))
    return jsonify(lease_list)


@api.route("/growing-unit-probs")
def get_growing_unit_probabilities():
    """
    Returns the most recent closure probabilities for each growing unit.
    """
    # If no probabilities, return empty dict.
    growing_unit_probs = (
        db.session.query(CMUProbability).order_by(CMUProbability.id.desc()).all()
    )
    if not growing_unit_probs:
        return jsonify({})

    growing_unit_probs_as_dicts = {}
    # Iterate newest-first; keep the first (latest) record per cmu_id.
    for unit in growing_unit_probs:
        if unit.cmu_id not in growing_unit_probs_as_dicts:
            growing_unit_probs_as_dicts[unit.cmu_id] = unit.as_dict()

    return jsonify(growing_unit_probs_as_dicts)


@api.route("/leases", methods=["GET", "POST", "DELETE"])
@user_required
def user_leases(user):
    """
    Returns the user's leases if a GET request.  Adds a new lease or updates
    an existing one if a POST request.  Deletes a lease if a DELETE request.
    """

    def lease_to_dict(lease):
        return {
            "lease_id": lease.lease_id,
            "cmu_id": lease.leases.cmu_id,
            "parcel_name": lease.leases.parcel_name,
            "waterbody": lease.leases.waterbody,
            "grow_area_type": lease.leases.grow_area_type,
            "rainfall_desc": lease.leases.cmus.rainfall_desc,
            "sh_id": lease.leases.cmus.sh_id,
            "sh_name": lease.leases.cmus.sh_name,
            "latitude": lease.leases.latitude,
            "longitude": lease.leases.longitude,
        }

    if request.method == "GET":
        leases = (
            db.session.query(UserLease).filter_by(user_id=user.id, deleted=False).all()
        )
        return jsonify(list(map(lease_to_dict, leases)))
    elif request.method == "POST":
        client_data = request.json
        lease_id = client_data.get("lease_id")
        # find the lease record
        lease = db.session.query(Lease).filter_by(lease_id=lease_id).first()
        if lease:
            # assertion: at this point we know that the given ncdmf_lease_id is valid
            # now we need to check if this lease already exists for the current user
            user_lease = (
                db.session.query(UserLease)
                .filter_by(user_id=user.id, lease_id=lease_id)
                .first()
            )
            if user_lease:
                # mark the lease as not deleted
                user_lease.deleted = False
            else:
                # create a new lease record
                # new_user_lease = {'lease_id': lease_id}
                user_lease = UserLease(user_id=user.id, lease_id=lease_id)
            try:
                db.session.add(user_lease)
                db.session.commit()
            except IntegrityError:
                return {
                    "errors": ["Cannot add/update lease due to constraint violations."]
                }, 400
            return lease_to_dict(user_lease)
        return {"errors": ["The given lease ID does not exist."]}, 400
    else:  # request.method == 'DELETE'
        client_data = request.json
        lease_id = client_data.get("lease_id")
        # find the lease with the given lease id and belongs to the current user
        user_lease = (
            db.session.query(UserLease)
            .filter_by(user_id=user.id, lease_id=lease_id)
            .first()
        )
        if user_lease:
            # set the deleted field
            user_lease.deleted = True
            db.session.add(user_lease)
            db.session.commit()
            return {"message": "Success"}, 200
        else:
            return {
                "errors": ["A lease with the given ID does not exist for this user."]
            }, 400


@api.route("/search-leases", methods=["POST"])
@user_required
def search_leases(user):
    """
    Returns leases based on a search term.
    """
    search_term = str(request.json.get("search"))
    user_lease_ids = (
        db.session.query(UserLease.lease_id)
        .filter_by(user_id=user.id, deleted=False)
        .all()
    )
    ncdmf_lease_ids = (
        db.session.query(Lease.lease_id)
        .filter(
            Lease.lease_id.like("%%" + search_term + "%%"),
            ~Lease.lease_id.in_(list(map(lambda x: x[0], user_lease_ids))),
        )
        .all()
    )
    return jsonify(list(map(lambda x: x[0], ncdmf_lease_ids)))


# =============================================================================
# Bandwidth SMS Callback Handler (Internal - receives forwarded callbacks from NC)
# =============================================================================


@api.route("/api/bandwidth/callback/internal", methods=["POST"])
def bandwidth_callback_internal():
    """
    Internal endpoint for Bandwidth callbacks forwarded from NC service.
    NC is the default service and routes FL callbacks here.

    Purpose: Handle opt-out (STOP) commands to update FL's users table.
    Note: Notification logging is centralized in NC's notification_events table.

    Callback types handled:
    - message-received: Incoming SMS from user (STOP/HELP commands)
    """
    # Verify it came from NC service
    forwarded_by = request.headers.get("X-Forwarded-By")
    if forwarded_by != "nc-callback-router":
        logging.warning("Callback received without proper forwarding header")

    try:
        callback_data = request.json

        if not callback_data:
            logging.warning("Received empty callback")
            return "", 200

        for event in callback_data:
            event_type = event.get("type")
            tag = (
                (event.get("tag") or event.get("message", {}).get("tag") or "")
                .strip()
                .upper()
            )
            message_id = event.get("message", {}).get("id")
            from_number = event.get("message", {}).get("from")
            text = event.get("message", {}).get("text", "")

            logging.info(f"FL Bandwidth callback - Type: {event_type}, Tag: {tag!r}")

            # Handle inbound when tag is FL or when tag is empty (NC forwarded; we process if we have this user)
            if event_type == "message-received" and (tag == "FL" or not tag):
                _handle_inbound_message_fl(from_number, text, message_id)
            elif event_type == "message-received" and tag:
                logging.info(f"FL ignoring message-received for tag={tag!r} (not FL)")

        return "", 200

    except Exception as e:
        logging.error(f"Error processing Bandwidth callback: {e}")
        return "", 200


# Template name for NC notification_events (must match NC's NotificationEvent)
TEMPLATE_SMS_CLOSURE_ALERT = "sms_closure_alert"


def _log_sms_to_nc(
    state,
    user_id,
    phone_number,
    direction,
    message_id=None,
    template_name=None,
    send_success=True,
):
    """Log an SMS event to NC's notification_events (centralized logging)."""
    url = os.getenv("NC_LOG_URL")
    secret = os.getenv("NC_LOG_SECRET")
    if not url or not secret:
        logging.warning("NC_LOG_URL or NC_LOG_SECRET not set, skipping log to NC")
        return
    endpoint = url.rstrip("/") + "/api/bandwidth/log-event"
    payload = {
        "state": state,
        "user_id": user_id,
        "phone_number": phone_number,
        "message_id": message_id,
        "direction": direction,
        "send_success": send_success,
    }
    if direction == "outbound":
        payload["template_name"] = template_name or TEMPLATE_SMS_CLOSURE_ALERT
    try:
        r = requests.post(
            endpoint,
            json=payload,
            headers={"Content-Type": "application/json", "X-NC-Log-Secret": secret},
            timeout=10,
        )
        if r.status_code != 200:
            logging.warning(f"NC log-event returned {r.status_code}")
    except Exception as e:
        logging.error(f"Failed to log SMS to NC: {e}")


def _handle_inbound_message_fl(from_number, text, message_id):
    """Handle incoming SMS from user (STOP, START, HELP) for FL."""
    from routes.cron import _send_bandwidth_message_single

    def _log_inbound_fl(state: str, user_id: int, phone_number: str, msg_id: str):
        _log_sms_to_nc(
            state=state,
            user_id=user_id,
            phone_number=phone_number,
            direction="inbound",
            message_id=msg_id,
        )

    handled = handle_stop_start(
        state="FL",
        db_session=db.session,
        user_model=User,
        from_number=from_number,
        text=text,
        message_id=message_id,
        log_inbound_fn=_log_inbound_fl,
        send_opt_out_fn=lambda to: _send_bandwidth_message_single(
            to,
            "ShellCast-FL: You've been unsubscribed and will no longer receive alerts. Reply START to resubscribe.",
        ),
        send_opt_in_fn=lambda to: _send_bandwidth_message_single(
            to,
            "ShellCast-FL: You've been resubscribed to closure alerts. Reply STOP to unsubscribe.",
        ),
    )

    if handled:
        return

    # HELP keyword - send help message
    text_upper = text.strip().upper()
    if text_upper == "HELP":
        logging.info(f"Sending help message to {from_number}")
        help_message = (
            "Thank you for reaching out to ShellCast. For support, please email us at "
            "shellcastapp@ncsu.edu. Reply STOP to opt out."
        )
        try:
            _send_bandwidth_message_single(from_number, help_message)
            logging.info("Help message sent successfully")
        except Exception as e:
            logging.error(f"Failed to send help message: {e}")

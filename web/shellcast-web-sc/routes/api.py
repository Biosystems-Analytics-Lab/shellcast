import logging
import os

import requests
from core.notifications.inbound import handle_stop_start
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

# State identifier for SC
STATE = "SC"

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


# Help message for HELP command
HELP_MESSAGE = (
    "Thank you for reaching out to ShellCast. For support, please email us at "
    "shellcastapp@ncsu.edu. Reply STOP to opt out."
)


@api.route("/user-info", methods=["GET", "POST"])
@user_required
def user_info(user):
    """
    Returns the user's info if a GET request.  Updates the user's info if a POST request.
    """

    def construct_response(user_obj):
        user_info_dict = {
            "email": user.email,
            "email_pref": user.email_pref,
            "text_pref": user.text_pref,
            "prob_pref": user.prob_pref,
            "email_consent": user.email_consent,
            "text_consent": user.text_consent,
        }
        if user.phone_number is not None:
            user_info_dict["phone_number"] = user.phone_number
        return user_info_dict

    if request.method == "GET":
        return construct_response(user)
    else:  # request.method == 'POST'
        # validate the uploaded info
        validator = ProfileInfoValidator(request.json)
        if validator.validate():
            if validator.email_pref:
                user.email = validator.email or ""
            user.phone_number = validator.phone_number
            user.email_pref = validator.email_pref
            user.text_pref = validator.text_pref
            user.prob_pref = validator.prob_pref
            user.text_consent = validator.text_consent
            db.session.add(user)
            db.session.commit()
            return construct_response(user)
        return {"errors": validator.errors}, 400


@api.route("/delete-account")
@user_required
def delete_account(user):
    """
    Deletes the user's account.
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
        user.email_consent = User.DEFAULT_email_consent
        user.text_consent = User.DEFAULT_text_consent

        # mark user record as deleted
        user.deleted = True

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
            "latitude": lease.leases.latitude,
            "longitude": lease.leases.longitude,
        }
        lease_prob = lease.get_latest_probability()
        if lease_prob:
            prob_dict["prob_1d_perc"] = lease_prob.prob_1d_perc
            prob_dict["prob_2d_perc"] = lease_prob.prob_2d_perc
            prob_dict["prob_3d_perc"] = lease_prob.prob_3d_perc
        return prob_dict

    lease_list = list(map(get_lease_prob_for_lease, leases))
    return jsonify(lease_list)


@api.route("/growing-unit-probs")
def get_growing_unit_probabilities():
    """
    Returns the most recent closure probabilities for each growing unit.
    """
    # TODO make sure this returns one (and only one) closure probability for each growing unit
    num_growing_units = db.session.query(Lease).count()
    growing_unit_probs = (
        db.session.query(CMUProbability)
        .order_by(CMUProbability.id.desc())
        .limit(num_growing_units)
    )
    growing_unit_probs_as_dicts = {}
    for unit in growing_unit_probs:
        lease_id = unit.lease_id
        growing_unit_probs_as_dicts[lease_id] = unit.as_dict()

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
            "grow_area_name": lease.leases.grow_area_name,
            "grow_area_desc": lease.leases.grow_area_desc,
            "cmu_name": lease.leases.cmu_name,
            "rainfall_thresh_in": lease.leases.rainfall_thresh_in,
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
                new_user_lease = {"lease_id": lease_id}
                user_lease = UserLease(user_id=user.id, **new_user_lease)
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
    NC is the default service and routes SC callbacks here.

    Purpose: Handle opt-out (STOP) commands to update SC's users table.
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
            message_id = event.get("message", {}).get("id")
            from_number = event.get("message", {}).get("from")
            text = event.get("message", {}).get("text", "")

            logging.info(f"SC Bandwidth callback - Type: {event_type}")

            # Only handle inbound messages (STOP/HELP) - delivery status logged in NC
            if event_type == "message-received":
                _handle_inbound_message_sc(from_number, text, message_id)

        return "", 200

    except Exception as e:
        logging.error(f"Error processing Bandwidth callback: {e}")
        return "", 200


def _handle_inbound_message_sc(from_number, text, message_id):
    """Handle incoming SMS from user (STOP, START, HELP) for SC."""
    from routes.cron import _send_bandwidth_message_single

    def _log_inbound_sc(state: str, user_id: int, phone_number: str, msg_id: str):
        _log_sms_to_nc(
            state=state,
            user_id=user_id,
            phone_number=phone_number,
            direction="inbound",
            message_id=msg_id,
        )

    handled = handle_stop_start(
        state="SC",
        db_session=db.session,
        user_model=User,
        from_number=from_number,
        text=text,
        message_id=message_id,
        log_inbound_fn=_log_inbound_sc,
        send_opt_out_fn=lambda to: _send_bandwidth_message_single(
            to,
            f"ShellCast-{STATE}: You've been unsubscribed and will no longer receive alerts. Reply START to resubscribe.",
        ),
        send_opt_in_fn=lambda to: _send_bandwidth_message_single(
            to,
            f"ShellCast-{STATE}: You've been resubscribed to closure alerts. Reply STOP to unsubscribe.",
        ),
    )

    if handled:
        return

    # HELP keyword - send help message
    text_upper = text.strip().upper()
    if text_upper == "HELP":
        logging.info(f"Sending help message to {from_number}")
        try:
            _send_bandwidth_message_single(from_number, HELP_MESSAGE)
            logging.info("Help message sent successfully")
        except Exception as e:
            logging.error(f"Failed to send help message: {e}")

import logging
import os
from datetime import date, datetime, timezone

import requests
from core.notifications.inbound import handle_stop_start
from core.notifications.phone_utils import clean_inbound_phone
from firebase_admin import auth
from flask import Blueprint, jsonify, request
from models import db
from models.CMU import CMU
from models.CMUProbability import CMUProbability
from models.Lease import Lease
from models.NotificationEvent import NotificationEvent
from models.User import User
from models.UserLease import UserLease
from routes.authentication import user_required
from routes.validators.profile_info_validator import ProfileInfoValidator
from sqlalchemy.exc import IntegrityError

api = Blueprint("api", __name__)

# State identifier for NC
STATE = "NC"

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
            "email": user_obj.email,
            "email_pref": user_obj.email_pref,
            "text_pref": user_obj.text_pref,
            "text_consent": user_obj.text_consent,
            "prob_pref": user_obj.prob_pref,
            "phone_verified": getattr(user_obj, "phone_verified", False),
        }
        if user_obj.phone_number is not None:
            user_info_dict["phone_number"] = user_obj.phone_number
        return user_info_dict

    if request.method == "GET":
        return construct_response(user)
    else:  # request.method == 'POST'
        if request.json is None:
            return {"errors": ["Request body must be JSON."]}, 400
        # validate the uploaded info
        validator = ProfileInfoValidator(request.json)
        if validator.validate():
            now = datetime.now(timezone.utc)
            prev_email_pref = user.email_pref
            prev_text_consent = user.text_consent
            # Persist preferences and contact info
            user.phone_number = validator.phone_number
            user.email_pref = validator.email_pref
            user.text_pref = validator.text_pref
            user.text_consent = validator.text_consent
            user.prob_pref = validator.prob_pref
            # Only update email when email_pref is on; when off, preserve existing email
            if validator.email_pref:
                user.email = validator.email or ""
            # Opt-in/opt-out timestamps: only set when email preference actually changed
            if validator.email_pref != prev_email_pref:
                if validator.email_pref:
                    user.email_opt_in_date = now
                    user.email_opt_out_date = None
                else:
                    user.email_opt_out_date = now
            # Opt-in/opt-out timestamps: only set when text consent actually changed
            if validator.text_consent != prev_text_consent:
                if validator.text_consent:
                    user.text_opt_in_date = now
                    user.text_opt_out_date = None
                else:
                    user.text_opt_out_date = now
            user.touch_updated(now)
            db.session.add(user)
            db.session.commit()
            return construct_response(user)
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

    # Allow frontend to pass current form values so the user can verify
    # a new number before saving preferences.
    payload = request.get_json(silent=True) or {}
    phone_number = (payload.get("phone_number") or user.phone_number or "").strip()

    # Prefer explicit values from payload when provided; otherwise fall back to DB.
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

    # Persist effective values and mark phone as verified, updating attempt counters.
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

    event = NotificationEvent.log_sms_outbound(
        state=STATE,
        user_id=user.id,
        phone_number=user.phone_number,
        template_name="sms_verification",
        message_id=response.id if getattr(response, "id", None) else None,
        send_success=True,
    )
    db.session.add(event)
    db.session.commit()

    return {"ok": True}, 200


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
        user.text_consent = User.DEFAULT_text_consent
        user.prob_pref = User.DEFAULT_prob_pref

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
            "lease_id": lease.leases.lease_id,
            "latitude": lease.leases.latitude,
            "longitude": lease.leases.longitude,
        }
        lease_prob = lease.getLatestProbability()
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
    Returns the most recent closure probabilties for each growing unit.
    """
    # TODO make sure this returns one (and only one) closure probability for each growing unit
    num_growing_units = db.session.query(CMU).count()
    growing_unit_probs = (
        db.session.query(CMUProbability)
        .order_by(CMUProbability.id.desc())
        .limit(num_growing_units)
    )
    growing_unit_probs_as_dicts = {}
    for unit in growing_unit_probs:
        cmu_name = unit.cmu_name
        growing_unit_probs_as_dicts[cmu_name] = unit.as_dict()

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
        # find the NCDMF lease record
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
# Bandwidth SMS Callback Handler (NC is the default service)
# =============================================================================


@api.route("/api/bandwidth/callback", methods=["POST"])
def bandwidth_callback():
    """
    Handle callbacks from Bandwidth for SMS delivery status and incoming messages.
    NC is the default service, so it receives all callbacks and routes to appropriate state.

    Callback types:
    - message-delivered: SMS was successfully delivered
    - message-failed: SMS delivery failed
    - message-received: Incoming SMS from user (e.g., STOP/START commands)

    Important testing note:
    - STOP/START are processed per phone number using the last state (NC, SC, FL)
      that sent an SMS to that number. In local or test environments, if you
      register the same phone for multiple states, sending STOP will unsubscribe
      whichever state most recently sent a text to that phone. In production,
      users normally subscribe to a single state, so this mainly affects
      developers who reuse one test phone across NC/SC/FL.
    """
    try:
        callback_data = request.json

        if not callback_data:
            logging.warning("Received empty callback from Bandwidth")
            return "", 200

        for event in callback_data:
            event_type = event.get("type")
            # Tag can be at event level or inside event.message (Bandwidth may put it in message for inbound)
            tag = (
                (event.get("tag") or event.get("message", {}).get("tag") or "")
                .strip()
                .upper()
            )
            message_id = event.get("message", {}).get("id")
            to_number = event.get("message", {}).get("to", [None])[0]
            from_number = event.get("message", {}).get("from")
            text = event.get("message", {}).get("text", "")

            logging.info(
                f"Bandwidth callback - Type: {event_type}, Tag: {tag}, Message ID: {message_id}"
            )

            # Delivery status: update NC's NotificationEvent for all states (NC, FL, SC)
            if event_type == "message-delivered":
                _handle_delivery_success(message_id, to_number)
            elif event_type == "message-failed":
                error_code = event.get("errorCode")
                description = event.get("description")
                _handle_delivery_failure(message_id, to_number, error_code, description)

            # Route delivery events to state service for their internal handling
            if (
                event_type in ("message-delivered", "message-failed")
                and tag
                and tag != STATE
            ):
                _route_callback_to_state(tag, [event])
                continue

            # Inbound: route by tag when present; when tag is missing, infer state from last outbound to this phone.
            if event_type == "message-received":
                if tag == "NC":
                    _handle_inbound_message(from_number, text, message_id)
                elif tag in ("SC", "FL"):
                    _route_callback_to_state(tag, [event])
                elif not tag:
                    state_for_phone = _get_last_state_that_sent_to_phone(from_number)
                    if state_for_phone == "NC":
                        _handle_inbound_message(from_number, text, message_id)
                    elif state_for_phone in ("SC", "FL"):
                        _route_callback_to_state(state_for_phone, [event])
                    else:
                        _route_callback_to_state("SC", [event])
                        _route_callback_to_state("FL", [event])
                else:
                    logging.warning(f"Unknown inbound tag: {tag!r}, skipping")
            elif event_type not in ("message-delivered", "message-failed"):
                logging.warning(f"Unknown event type received: {event_type}")

        return "", 200

    except Exception as e:
        logging.error(f"Error processing Bandwidth callback: {e}")
        return "", 200


def _get_last_state_that_sent_to_phone(phone_number: str):
    """
    Return which state (NC, SC, FL) last sent an outbound SMS to this phone,
    using NC's notification_events. Used when inbound callback has no tag.
    Returns "NC", "SC", "FL", or None if no record.
    """
    if not phone_number:
        return None
    clean = clean_inbound_phone(phone_number)
    if not clean or len(clean) < 10:
        return None
    digits = "".join(c for c in clean if c.isdigit())
    if len(digits) >= 10:
        lookup = digits[-10:]
    else:
        lookup = digits
    event = (
        NotificationEvent.query.filter_by(
            phone_number=lookup,
            message_direction="outbound",
        )
        .order_by(NotificationEvent.created.desc())
        .first()
    )
    if event and event.state in ("NC", "SC", "FL"):
        return event.state
    return None


def _route_callback_to_state(state, events):
    """
    Route callback events to the appropriate state service.
    """
    project_id = os.getenv("GOOGLE_CLOUD_PROJECT", "ncsu-shellcast")

    state_urls = {
        "SC": f"https://shellcast-sc-dot-{project_id}.appspot.com/api/bandwidth/callback/internal",
        "FL": f"https://shellcast-fl-dot-{project_id}.appspot.com/api/bandwidth/callback/internal",
    }

    if state not in state_urls:
        logging.warning(f"Unknown state tag: {state}, cannot route callback")
        return

    try:
        response = requests.post(
            state_urls[state],
            json=events,
            headers={
                "Content-Type": "application/json",
                "X-Forwarded-By": "nc-callback-router",
            },
            timeout=10,
        )
        logging.info(
            f"Routed callback to {state} service, status: {response.status_code}"
        )
    except Exception as e:
        logging.error(f"Failed to route callback to {state}: {e}")


# =============================================================================
# Centralized notification logging (for FL/SC to record in NC DB)
# =============================================================================


@api.route("/api/bandwidth/log-event", methods=["POST"])
def bandwidth_log_event():
    """
    Internal endpoint for FL and SC to log SMS events to NC's notification_events.
    Secured with X-NC-Log-Secret header. Used so all states log in one place.
    """
    secret = request.headers.get("X-NC-Log-Secret")
    expected = os.getenv("NC_LOG_SECRET")
    if not expected or secret != expected:
        logging.warning("bandwidth_log_event: missing or invalid X-NC-Log-Secret")
        return "", 403

    try:
        data = request.json or {}
        state = data.get("state")
        user_id = data.get("user_id")
        phone_number = data.get("phone_number")
        message_id = data.get("message_id")
        direction = data.get("direction")  # "outbound" | "inbound"
        template_name = data.get("template_name")
        send_success = data.get("send_success", True)

        if not state or state not in ("FL", "SC"):
            return "", 400
        if not user_id or not phone_number or not direction:
            return "", 400
        if direction == "outbound" and not template_name:
            return "", 400

        phone_number = clean_inbound_phone(str(phone_number or ""))
        if len(phone_number) > 10:
            phone_number = "".join(c for c in phone_number if c.isdigit())[-10:]

        if direction == "outbound":
            event = NotificationEvent.log_sms_outbound(
                state=state,
                user_id=int(user_id),
                phone_number=phone_number,
                template_name=template_name,
                message_id=message_id,
                send_success=send_success,
            )
        else:
            event = NotificationEvent.log_sms_inbound(
                state=state,
                user_id=int(user_id),
                phone_number=phone_number,
                message_id=message_id,
            )
        db.session.add(event)
        db.session.commit()
        return "", 200
    except Exception as e:
        logging.error(f"bandwidth_log_event: {e}")
        db.session.rollback()
        return "", 500


def _handle_delivery_success(message_id, to_number):
    """Handle successful SMS delivery callback."""
    logging.info(f"Message {message_id} delivered successfully to {to_number}")

    if message_id:
        event = NotificationEvent.query.filter_by(message_id=message_id).first()
        if event:
            event.update_delivery_status("DELIVERED")
            db.session.commit()


def _handle_delivery_failure(message_id, to_number, error_code, description):
    """Handle failed SMS delivery callback."""
    logging.error(
        f"Message {message_id} failed to {to_number}: {description} (Code: {error_code})"
    )

    if message_id:
        event = NotificationEvent.query.filter_by(message_id=message_id).first()
        if event:
            event.update_delivery_status("FAILED", error_code=error_code)
            db.session.commit()


def _handle_inbound_message(from_number, text, message_id):
    """Handle incoming SMS from user (STOP, START, HELP, etc.)."""
    from routes.cron import _send_bandwidth_message_single

    def _log_inbound_nc(state: str, user_id: int, phone_number: str, msg_id: str):
        event = NotificationEvent.log_sms_inbound(
            state=state,
            user_id=user_id,
            phone_number=phone_number,
            message_id=msg_id,
        )
        db.session.add(event)
        db.session.commit()

    handled = handle_stop_start(
        state=STATE,
        db_session=db.session,
        user_model=User,
        from_number=from_number,
        text=text,
        message_id=message_id,
        log_inbound_fn=_log_inbound_nc,
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

    # Handle HELP keyword
    text_upper = text.strip().upper()
    if text_upper == "HELP":
        logging.info(f"Sending help message to {from_number}")
        try:
            _send_bandwidth_message_single(from_number, HELP_MESSAGE)
            logging.info("Help message sent successfully")
        except Exception as e:
            logging.error(f"Failed to send help message: {e}")

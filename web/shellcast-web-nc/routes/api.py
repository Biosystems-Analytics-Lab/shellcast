import logging
import os
from datetime import datetime, timezone

import requests
from core.notifications.inbound import handle_stop_start
from firebase_admin import auth
from flask import Blueprint, current_app, jsonify, request
from models import db
from models.CMU import CMU
from models.CMUProbability import CMUProbability
from models.Lease import Lease
from models.NotificationEvent import NotificationEvent
from models.User import User
from models.UserLease import UserLease
from routes.authentication import userRequired
from routes.validators.ProfileInfoValidator import ProfileInfoValidator
from sqlalchemy.exc import IntegrityError

api = Blueprint("api", __name__)

# State identifier for NC
STATE = "NC"

# Help message for HELP command
HELP_MESSAGE = (
    "Thank you for reaching out to ShellCast. For support, please email us at "
    "shellcastapp@ncsu.edu. Reply STOP to opt out."
)


@api.route("/userInfo", methods=["GET", "POST"])
@userRequired
def userInfo(user):
    """
    Returns the user's info if a GET request.  Updates the user's info if a POST request.
    """

    def constructResponse(userObj):
        userInfo = {
            "email": userObj.email,
            "email_pref": userObj.email_pref,
            "text_pref": userObj.text_pref,
            "email_consent": userObj.email_consent,
            "text_consent": userObj.text_consent,
            "prob_pref": userObj.prob_pref,
        }
        if userObj.phone_number is not None:
            userInfo["phone_number"] = userObj.phone_number
        return userInfo

    if request.method == "GET":
        return constructResponse(user)
    else:  # request.method == 'POST'
        # validate the uploaded info
        validator = ProfileInfoValidator(request.json)
        if validator.validate():
            now = datetime.now(timezone.utc)
            prev_email_consent = user.email_consent
            prev_text_consent = user.text_consent
            # Persist preferences and contact info
            user.phone_number = validator.phone_number
            user.email_pref = validator.email_pref
            user.text_pref = validator.text_pref
            user.email_consent = validator.email_consent
            user.text_consent = validator.text_consent
            user.prob_pref = validator.prob_pref
            # Only clear email when explicitly opting out of email (email_pref False)
            if validator.email_pref:
                user.email = validator.email if validator.email else user.email
            else:
                user.email = validator.email
            # Opt-in/opt-out timestamps: only set when consent actually changed
            if validator.text_consent != prev_text_consent:
                if validator.text_consent:
                    user.text_opt_in_date = now
                    user.text_opt_out_date = None
                else:
                    user.text_opt_out_date = now
            if validator.email_consent != prev_email_consent:
                if validator.email_consent:
                    user.email_opt_in_date = now
                    user.email_opt_out_date = None
                else:
                    user.email_opt_out_date = now
            db.session.add(user)
            db.session.commit()
            return constructResponse(user)
        return {"errors": validator.errors}, 400


@api.route("/deleteAccount")
@userRequired
def deleteAccount(user):
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

        # mark user record as deleted
        user.deleted = True

        db.session.add(user)
        db.session.commit()
    except Exception as err:
        print(err)
        return {"errors": ["Could not delete user."]}, 400
    return "Success"


@api.route("/leaseProbs")
@userRequired
def getLeaseClosureProbabilities(user):
    """
    Returns the user's lease closure probabilities.
    """
    leases = db.session.query(UserLease).filter_by(user_id=user.id, deleted=False).all()

    def getLeaseProbForLease(lease):
        probDict = {
            "lease_id": lease.leases.lease_id,
            "latitude": lease.leases.latitude,
            "longitude": lease.leases.longitude,
        }
        leaseProb = lease.getLatestProbability()
        if leaseProb:
            probDict["prob_1d_perc"] = leaseProb.prob_1d_perc
            probDict["prob_2d_perc"] = leaseProb.prob_2d_perc
            probDict["prob_3d_perc"] = leaseProb.prob_3d_perc
        return probDict

    leaseList = list(map(getLeaseProbForLease, leases))
    return jsonify(leaseList)


@api.route("/growingUnitProbs")
def getGrowingUnitProbabilities():
    """
    Returns the most recent closure probabilties for each growing unit.
    """
    # TODO make sure this returns one (and only one) closure probability for each growing unit
    numGrowingUnits = db.session.query(CMU).count()
    growingUnitProbs = (
        db.session.query(CMUProbability)
        .order_by(CMUProbability.id.desc())
        .limit(numGrowingUnits)
    )
    growingUnitProbsAsDicts = {}
    for unit in growingUnitProbs:
        cmuName = unit.cmu_name
        growingUnitProbsAsDicts[cmuName] = unit.asDict()

    return jsonify(growingUnitProbsAsDicts)


@api.route("/leases", methods=["GET", "POST", "DELETE"])
@userRequired
def userLeases(user):
    """
    Returns the user's leases if a GET request.  Adds a new lease or updates
    an existing one if a POST request.  Deletes a lease if a DELETE request.
    """

    def leaseToDict(lease):
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
        return jsonify(list(map(leaseToDict, leases)))
    elif request.method == "POST":
        clientData = request.json
        leaseId = clientData.get("lease_id")
        # find the NCDMF lease record
        lease = db.session.query(Lease).filter_by(lease_id=leaseId).first()
        if lease:
            # assertion: at this point we know that the given ncdmf_lease_id is valid
            # now we need to check if this lease already exists for the current user
            userLease = (
                db.session.query(UserLease)
                .filter_by(user_id=user.id, lease_id=leaseId)
                .first()
            )
            if userLease:
                # mark the lease as not deleted
                userLease.deleted = False
            else:
                # create a new lease record
                new_user_lease = {"lease_id": leaseId}
                userLease = UserLease(user_id=user.id, **new_user_lease)
            try:
                db.session.add(userLease)
                db.session.commit()
            except IntegrityError:
                return {
                    "errors": ["Cannot add/update lease due to constraint violations."]
                }, 400
            return leaseToDict(userLease)
        return {"errors": ["The given lease ID does not exist."]}, 400
    else:  # request.method == 'DELETE'
        clientData = request.json
        leaseId = clientData.get("lease_id")
        # find the lease with the given lease id and belongs to the current user
        userLease = (
            db.session.query(UserLease)
            .filter_by(user_id=user.id, lease_id=leaseId)
            .first()
        )
        if userLease:
            # set the deleted field
            userLease.deleted = True
            db.session.add(userLease)
            db.session.commit()
            return {"message": "Success"}, 200
        else:
            return {
                "errors": ["A lease with the given ID does not exist for this user."]
            }, 400


@api.route("/searchLeases", methods=["POST"])
@userRequired
def searchLeases(user):
    """
    Returns leases based on a search term.
    """
    searchTerm = str(request.json.get("search"))
    userLeaseIds = (
        db.session.query(UserLease.lease_id)
        .filter_by(user_id=user.id, deleted=False)
        .all()
    )
    ncdmfLeaseIds = (
        db.session.query(Lease.lease_id)
        .filter(
            Lease.lease_id.like("%%" + searchTerm + "%%"),
            ~Lease.lease_id.in_(list(map(lambda x: x[0], userLeaseIds))),
        )
        .all()
    )
    return jsonify(list(map(lambda x: x[0], ncdmfLeaseIds)))


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
    """
    try:
        callback_data = request.json

        if not callback_data:
            logging.warning("Received empty callback from Bandwidth")
            return "", 200

        for event in callback_data:
            event_type = event.get("type")
            tag = event.get("tag", "")  # State tag from when message was sent
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

            # Inbound: handle NC, then forward to FL and SC so they can handle and log
            if event_type == "message-received":
                _handle_inbound_message(from_number, text, message_id)
                _route_callback_to_state("FL", [event])
                _route_callback_to_state("SC", [event])
            elif event_type not in ("message-delivered", "message-failed"):
                logging.warning(f"Unknown event type received: {event_type}")

        return "", 200

    except Exception as e:
        logging.error(f"Error processing Bandwidth callback: {e}")
        return "", 200


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
            "ShellCast: You've been unsubscribed and will no longer receive alerts. Reply START to resubscribe.",
        ),
        send_opt_in_fn=lambda to: _send_bandwidth_message_single(
            to,
            "ShellCast: You've been resubscribed to closure alerts. Reply STOP to unsubscribe.",
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

import logging
from datetime import datetime, timezone

from firebase_admin import auth
from flask import Blueprint, jsonify, request
from models import db
from models.CMUProbability import CMUProbability
from models.Lease import Lease
from models.User import User
from models.UserLease import UserLease
from routes.authentication import userRequired
from routes.validators.ProfileInfoValidator import ProfileInfoValidator
from sqlalchemy.exc import IntegrityError

api = Blueprint("api", __name__)


@api.route("/userInfo", methods=["GET", "POST"])
@userRequired
def userInfo(user):
    """
    Returns the user's info if a GET request.  Updates the user's info if a POST request.
    """

    def constructResponse(userObj):
        userInfo = {
            "email": user.email,
            "email_pref": user.email_pref,
            "text_pref": user.text_pref,
            "prob_pref": user.prob_pref,
            "email_consent": user.email_consent,
            "text_consent": user.text_consent,
        }
        if user.phone_number != None:
            userInfo["phone_number"] = user.phone_number
        return userInfo

    if request.method == "GET":
        return constructResponse(user)
    else:  # request.method == 'POST'
        # validate the uploaded info
        validator = ProfileInfoValidator(request.json)
        if validator.validate():
            user.email = validator.email
            user.phone_number = validator.phone_number
            user.email_pref = validator.email_pref
            user.text_pref = validator.text_pref
            user.prob_pref = validator.prob_pref
            user.email_consent = validator.email_consent
            user.text_consent = validator.text_consent
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


@api.route("/leaseProbs")
@userRequired
def getLeaseClosureProbabilities(user):
    """
    Returns the user's lease closure probabilities.
    """
    leases = db.session.query(UserLease).filter_by(user_id=user.id, deleted=False).all()

    def getLeaseProbForLease(lease):
        probDict = {
            "lease_id": lease.lease_id,
            "cmu_id": lease.leases.cmu_id,
            "sh_id": lease.leases.cmus.sh_id,
            "sh_name": lease.leases.cmus.sh_name,
            "latitude": lease.leases.latitude,
            "longitude": lease.leases.longitude,
        }
        leaseProb = lease.getLatestProbability()
        if leaseProb:
            probDict["prob_1d_perc"] = leaseProb.prob_1d_perc
        return probDict

    leaseList = list(map(getLeaseProbForLease, leases))
    return jsonify(leaseList)


@api.route("/growingUnitProbs")
def getGrowingUnitProbabilities():
    """
    Returns the most recent closure probabilities for each growing unit.
    """
    # TODO make sure this returns one (and only one) closure probability for each growing unit
    latestDate = (
        db.session.query(CMUProbability)
        .order_by(CMUProbability.created.desc())
        .first()
        .created
    )
    count = (
        db.session.query(CMUProbability)
        .filter(CMUProbability.created == latestDate)
        .count()
    )
    print(count)
    growingUnitProbs = (
        db.session.query(CMUProbability).order_by(CMUProbability.id.desc()).limit(count)
    )
    growingUnitProbsAsDicts = {}
    for unit in growingUnitProbs:
        growingUnitProbsAsDicts[unit.cmu_id] = unit.asDict()

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
        return jsonify(list(map(leaseToDict, leases)))
    elif request.method == "POST":
        clientData = request.json
        leaseId = clientData.get("lease_id")
        # find the lease record
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
                # new_user_lease = {'lease_id': leaseId}
                userLease = UserLease(user_id=user.id, lease_id=leaseId)
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
# Bandwidth SMS Callback Handler (Internal - receives forwarded callbacks from NC)
# =============================================================================


@api.route("/bandwidth/callback/internal", methods=["POST"])
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
            message_id = event.get("message", {}).get("id")
            from_number = event.get("message", {}).get("from")
            text = event.get("message", {}).get("text", "")

            logging.info(f"FL Bandwidth callback - Type: {event_type}")

            # Only handle inbound messages (STOP/HELP) - delivery status logged in NC
            if event_type == "message-received":
                _handle_inbound_message_fl(from_number, text, message_id)

        return "", 200

    except Exception as e:
        logging.error(f"Error processing Bandwidth callback: {e}")
        return "", 200


def _handle_inbound_message_fl(from_number, text, message_id):
    """
    Handle incoming SMS from user (STOP, HELP) for FL.
    Updates FL's users table for opt-out.
    """
    logging.info(f"Received SMS from {from_number}: {text}")

    text_upper = text.strip().upper()

    # Handle opt-out keywords - update FL users table
    if text_upper in ["STOP", "UNSUBSCRIBE", "CANCEL", "END", "QUIT"]:
        user = db.session.query(User).filter_by(phone_number=from_number).first()
        if user:
            user.text_pref = False
            user.text_consent = False
            user.text_opt_out_date = datetime.now(timezone.utc)
            db.session.commit()
            logging.info(f"FL User {user.id} opted out of SMS notifications")
        else:
            logging.warning(f"No FL user found with phone number {from_number}")

    # Handle HELP keyword - send help message
    elif text_upper == "HELP":
        from routes.cron import _send_bandwidth_message_single

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

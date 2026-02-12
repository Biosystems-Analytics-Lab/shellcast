import os
import secrets
from functools import wraps

from firebase_admin import auth
from firebase_admin.auth import ExpiredIdTokenError, InvalidIdTokenError
from flask import request
from models import db
from models.User import User


def ensureUserExists(fbUserInfo):
    """
    Checks if a user record already exists for the given Firebase user and
    adds one to the database if not.
    """
    # extract user info
    fbUid = fbUserInfo.get("uid")
    email = fbUserInfo.get("email")

    # check if the user with this Firebase UID already exists
    user = User.query.filter_by(firebase_uid=fbUid).first()
    if user != None:
        return user

    # otherwise we need to create a new user
    newUser = User(firebase_uid=fbUid, email=email)
    db.session.add(newUser)
    db.session.commit()

    return newUser


def userRequired(func):
    """
    A decorator function that verifies the Firebase JWT token in the
    Authorization header and ensures that a corresponding user record
    exists in the ShellCast database.  The user record is then injected
    into the arguments of the wrapped function as 'user'.
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        # check for a Firebase JWT in the Authorization header
        try:
            idToken = request.headers["Authorization"].split(" ").pop()
            fbUserInfo = auth.verify_id_token(idToken)
        except ExpiredIdTokenError:
            return {"message": "ID token is expired"}, 401
        except InvalidIdTokenError:
            return {"message": "ID token is invalid"}, 401

        user = ensureUserExists(fbUserInfo)
        return func(*args, **kwargs, user=user)

    return wrapper


def cronOnly(func):
    """
    Ensures the request is from GAE cron (X-Appengine-Cron) or from NC orchestrator
    (X-NC-Orchestrator-Secret). NC triggers FL/SC when cron runs only on NC.
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        # GAE cron sends this header
        if request.headers.get("X-Appengine-Cron"):
            return func(*args, **kwargs)
        # NC orchestrator sends this when triggering FL send
        secret = os.getenv("NC_ORCHESTRATOR_SECRET")
        if secret and request.headers.get("X-NC-Orchestrator-Secret"):
            if secrets.compare_digest(
                request.headers["X-NC-Orchestrator-Secret"], secret
            ):
                return func(*args, **kwargs)
        return {"message": "Request must be made by cron service"}, 401

    return wrapper

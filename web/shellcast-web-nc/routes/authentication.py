from functools import wraps

from firebase_admin import auth
from firebase_admin.auth import ExpiredIdTokenError, InvalidIdTokenError
from flask import request
from models import db
from models.User import User


def ensure_user_exists(fb_user_info):
    """
    Checks if a user record already exists for the given Firebase user and
    adds one to the database if not.
    """
    # extract user info
    fb_uid = fb_user_info.get("uid")
    email = fb_user_info.get("email")

    # check if the user with this Firebase UID already exists
    user = User.query.filter_by(firebase_uid=fb_uid).first()
    if user != None:
        return user

    # otherwise we need to create a new user
    new_user = User(firebase_uid=fb_uid, email=email)
    db.session.add(new_user)
    db.session.commit()

    return new_user


def user_required(func):
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
            id_token = request.headers["Authorization"].split(" ").pop()
            fb_user_info = auth.verify_id_token(id_token)
        except ExpiredIdTokenError:
            return {"message": "ID token is expired"}, 401
        except InvalidIdTokenError:
            return {"message": "ID token is invalid"}, 401

        user = ensure_user_exists(fb_user_info)
        return func(*args, **kwargs, user=user)

    return wrapper


def cron_only(func):
    """
    A decorator function that ensures that a request is made by the
    GCP App Engine cron service.
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        # check for X-Appengine-Cron header
        try:
            if not request.headers["X-Appengine-Cron"]:
                return {"message": "Request must be made by cron service"}, 401
        except KeyError:
            return {"message": "Request must be made by cron service"}, 401
        return func(*args, **kwargs)

    return wrapper

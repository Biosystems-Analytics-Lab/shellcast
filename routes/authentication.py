from functools import wraps

from flask import request

from firebase_admin import auth
from firebase_admin.auth import ExpiredIdTokenError, InvalidIdTokenError

from models import db
from models.User import User

def ensureUserExists(fbUserInfo):
  """
  Checks if a user record already exists for the given Firebase user and
  adds one to the database if not.
  """
  # extract user info
  fbUid = fbUserInfo.get('uid')
  email = fbUserInfo.get('email')
  phoneNum = fbUserInfo.get('phone_number')

  # check if the user with this Firebase UID already exists
  user = User.query.filter_by(firebase_uid=fbUid).first()
  if (user != None):
    return user

  # otherwise we need to create a new user
  newUser = User(firebase_uid=fbUid, email=email, phone_number=phoneNum)
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
      idToken = request.headers['Authorization'].split(' ').pop()
      fbUserInfo = auth.verify_id_token(idToken)
    except ExpiredIdTokenError:
      return {'message': 'ID token is expired'}, 401
    except InvalidIdTokenError:
      return {'message': 'ID token is invalid'}, 401
    
    user = ensureUserExists(fbUserInfo)
    return func(*args, **kwargs, user=user)
  return wrapper

def cronRequired(func):
  """
  A decorator function that ensures that a request is made by the
  GCP App Engine cron service.
  """
  @wraps(func)
  def wrapper(*args, **kwargs):
    # check for X-Appengine-Cron header
    try:
      if (not request.headers['X-Appengine-Cron']):
        return {'message': 'Request must be made by cron service'}, 401
    except KeyError:
      return {'message': 'Request must be made by cron service'}, 401
    return func(*args, **kwargs)
  return wrapper

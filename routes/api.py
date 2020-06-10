from flask import Blueprint, jsonify, request

from models import db
from models.User import User
from models.ClosureProbability import ClosureProbability
from models.LeaseInfo import LeaseInfo

import time

from firebase_admin import auth
from firebase_admin.auth import ExpiredIdTokenError, InvalidIdTokenError

api = Blueprint('api', __name__)

def getFirebaseUserInfo():
  idToken = request.headers['Authorization'].split(' ').pop()
  userInfo = auth.verify_id_token(idToken)
  return userInfo

def createNewUser(fbUserInfo):
  # extract user info
  fbUid = fbUserInfo.get('uid')
  email = fbUserInfo.get('email')
  phoneNum = fbUserInfo.get('phone_number')
  displayName = fbUserInfo.get('display_name')
  firstName = None
  lastName = None
  if (displayName != None):
    splitName = displayName.split(' ')
    if (len(splitName) >= 1):
      firstName = splitName[0]
    if (len(splitName) >= 2):
      lastName = splitName[1]

  # check if the user with this Firebase UID already exists
  res = User.query.filter_by(firebase_uid=fbUid).first()
  if (res != None):
    return False

  newUser = User(firebase_uid=fbUid, email=email, phone_number=phoneNum, first_name=firstName, last_name=lastName)
  db.session.add(newUser)
  db.session.commit()

  return True

@api.route('/newUser', methods=['POST'])
def newUser():
  try:
    fbUserInfo = getFirebaseUserInfo()
  except ExpiredIdTokenError:
    return {'message': 'ID token is expired'}, 401
  except InvalidIdTokenError:
    return {'message': 'ID token is invalid'}, 401

  if (createNewUser(fbUserInfo)):
    return {'message': 'User created'}
  return {'message': 'User already exists'}

def queryClosureProbabilities():
  results = db.session.query(ClosureProbability, LeaseInfo.grow_area_name).join(LeaseInfo).all()
  dictOfCPs = {}
  for r in results:
    sgaName = r[1]
    dictOfCPs[sgaName] = r[0].to_dict()
  return dictOfCPs

@api.route('/areaData')
def getAreaData():
  # t0 = time.perf_counter_ns()
  dictOfCPs = queryClosureProbabilities()
  # t1 = time.perf_counter_ns()
  # print('Total query time: {} ms'.format((t1 - t0) / 1000000))

  return jsonify(dictOfCPs)

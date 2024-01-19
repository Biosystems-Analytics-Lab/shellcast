import json
import sys

from flask import Blueprint, jsonify, request
from sqlalchemy.exc import IntegrityError

from firebase_admin import auth

from models import db
from models.User import User
# from models.CMU import CMU
from models.CMUProbability import CMUProbability
from models.UserLease import UserLease
from models.Lease import Lease

from routes.validators.ProfileInfoValidator import ProfileInfoValidator

from routes.authentication import userRequired

api = Blueprint('api', __name__)

@api.route('/userInfo', methods=['GET', 'POST'])
@userRequired
def userInfo(user):
  """
  Returns the user's info if a GET request.  Updates the user's info if a POST request.
  """
  def constructResponse(userObj):
    userInfo = {
      'email': user.email,
      'email_pref': user.email_pref,
      'text_pref': user.text_pref,
      'prob_pref': user.prob_pref
    }
    if (user.phone_number != None):
      userInfo['phone_number'] = user.phone_number
      userInfo['service_provider_id'] = user.service_provider_id
    return userInfo

  if (request.method == 'GET'):
    return constructResponse(user)
  else: # request.method == 'POST'
    # validate the uploaded info
    validator = ProfileInfoValidator(request.json)
    if (validator.validate()):
      user.email = validator.email
      user.phone_number = validator.phone_number
      user.service_provider_id = validator.service_provider_id
      user.email_pref = validator.email_pref
      user.text_pref = validator.text_pref
      user.prob_pref = validator.prob_pref
      db.session.add(user)
      db.session.commit()
      return constructResponse(user)
    return {'errors': validator.errors}, 400

@api.route('/deleteAccount')
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
    user.service_provider_id = None

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
    return {'errors': ['Could not delete user.']}, 400
  return 'Success'

@api.route('/leaseProbs')
@userRequired
def getLeaseClosureProbabilities(user):
  """
  Returns the user's lease closure probabilities.
  """
  leases = db.session.query(UserLease).filter_by(user_id=user.id, deleted=False).all()
  def getLeaseProbForLease(lease):
    probDict = {'lease_id': lease.lease_id, 'latitude': lease.leases.latitude, 'longitude': lease.leases.longitude}
    leaseProb = lease.getLatestProbability()
    if (leaseProb):
      probDict['prob_1d_perc'] = leaseProb.prob_1d_perc
    return probDict
  leaseList = list(map(getLeaseProbForLease, leases))
  return jsonify(leaseList)

@api.route('/growingUnitProbs')
def getGrowingUnitProbabilities():
  """
  Returns the most recent closure probabilities for each growing unit.
  """
  # TODO make sure this returns one (and only one) closure probability for each growing unit
  numGrowingUnits = db.session.query(Lease).count()
  growingUnitProbs = db.session.query(CMUProbability).order_by(CMUProbability.id.desc()).limit(numGrowingUnits)
  growingUnitProbsAsDicts = {}
  for unit in growingUnitProbs:
    leaseId = unit.lease_id
    growingUnitProbsAsDicts[leaseId] = unit.asDict()

  return jsonify(growingUnitProbsAsDicts)

@api.route('/leases', methods=['GET', 'POST', 'DELETE'])
@userRequired
def userLeases(user):
  """
  Returns the user's leases if a GET request.  Adds a new lease or updates
  an existing one if a POST request.  Deletes a lease if a DELETE request.
  """
  def leaseToDict(lease):
    return {
      'lease_id': lease.lease_id,
      'grow_area_name': lease.leases.grow_area_name,
      'rainfall_desc': lease.leases.grow_area_desc,
      'cmu_name': lease.leases.cmu_name,
    }
  if (request.method == 'GET'):
    leases = db.session.query(UserLease).filter_by(user_id=user.id, deleted=False).all()
    return jsonify(list(map(leaseToDict, leases)))
  elif (request.method == 'POST'):
    clientData = request.json
    leaseId = clientData.get('lease_id')
    # find the lease record
    lease = db.session.query(Lease).filter_by(lease_id=leaseId).first()
    if (lease):
      # assertion: at this point we know that the given ncdmf_lease_id is valid
      # now we need to check if this lease already exists for the current user
      userLease = db.session.query(UserLease).filter_by(user_id=user.id, lease_id=leaseId).first()
      if (userLease):
        # mark the lease as not deleted
        userLease.deleted = False
      else:
        # create a new lease record
        new_user_lease = {'lease_id': leaseId}
        userLease = UserLease(user_id=user.id, **new_user_lease)
      try:
        db.session.add(userLease)
        db.session.commit()
      except IntegrityError:
        return {'errors': ['Cannot add/update lease due to constraint violations.']}, 400
      return leaseToDict(userLease)
    return {'errors': ['The given lease ID does not exist.']}, 400
  else: # request.method == 'DELETE'
    clientData = request.json
    leaseId = clientData.get('lease_id')
    # find the lease with the given lease id and belongs to the current user
    userLease = db.session.query(UserLease).filter_by(user_id=user.id, lease_id=leaseId).first()
    if (userLease):
      # set the deleted field
      userLease.deleted = True
      db.session.add(userLease)
      db.session.commit()
      return {'message': 'Success'}, 200
    else:
      return {'errors': ['A lease with the given ID does not exist for this user.']}, 400

@api.route('/searchLeases', methods=['POST'])
@userRequired
def searchLeases(user):
  """
  Returns leases based on a search term.
  """
  searchTerm = str(request.json.get('search'))
  userLeaseIds = db.session.query(UserLease.lease_id).filter_by(user_id=user.id, deleted=False).all()
  ncdmfLeaseIds = db.session.query(Lease.lease_id).\
      filter(
        Lease.lease_id.like('%%' + searchTerm + '%%'),
        ~Lease.lease_id.in_(list(map(lambda x: x[0], userLeaseIds)))
      ).all()
  return jsonify(list(map(lambda x: x[0], ncdmfLeaseIds)))

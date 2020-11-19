from flask import Blueprint, jsonify, request
from sqlalchemy.exc import IntegrityError

from models import db
from models.ClosureProbability import ClosureProbability
from models.GrowArea import GrowArea
from models.SGAMinMaxProbability import SGAMinMaxProbability
from models.UserLease import UserLease
from models.NCDMFLease import NCDMFLease

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

@api.route('/leaseProbs')
@userRequired
def getLeaseClosureProbabilities(user):
  """
  Returns the user's lease closure probabilities.
  """
  leases = db.session.query(UserLease).filter_by(user_id=user.id, deleted=False).all()
  def getLeaseProbForLease(lease):
    probDict = {'ncdmf_lease_id': lease.ncdmf_lease_id, 'geometry': lease.geometry}
    if (len(lease.closureProbabilities) >= 1):
      # get the latest closure probability for the lease
      prob = lease.closureProbabilities[0]
      probDict['prob_1d_perc'] = prob.prob_1d_perc
      probDict['prob_2d_perc'] = prob.prob_2d_perc
      probDict['prob_3d_perc'] = prob.prob_3d_perc
    return probDict
  leaseList = list(map(getLeaseProbForLease, leases))
  return jsonify(leaseList)

@api.route('/growAreaProbs')
def getGrowAreaProbabilities():
  """
  Returns the min/max closure probabilties for each grow area.
  """
  # TODO make sure this returns one (and only one) closure probability for each grow area
  numberOfGrowAreas = db.session.query(GrowArea).count()
  growAreaProbs = db.session.query(SGAMinMaxProbability).order_by(SGAMinMaxProbability.id.desc()).limit(numberOfGrowAreas)
  growAreaProbsAsDicts = {}
  for area in growAreaProbs:
    sgaName = area.grow_area_name
    growAreaProbsAsDicts[sgaName] = area.asDict()

  return jsonify(growAreaProbsAsDicts)

@api.route('/leases', methods=['GET', 'POST', 'DELETE'])
@userRequired
def userLeases(user):
  """
  Returns the user's leases if a GET request.  Adds a new lease or updates
  an existing one if a POST request.  Deletes a lease if a DELETE request.
  """
  def leaseToDict(lease):
    return {
      'id': lease.id,
      'ncdmf_lease_id': lease.ncdmf_lease_id,
      'grow_area_name': lease.grow_area_name,
      'rainfall_thresh_in': lease.rainfall_thresh_in,
      'geometry': lease.geometry
    }
  if (request.method == 'GET'):
    leases = db.session.query(UserLease).filter_by(user_id=user.id, deleted=False).all()
    return jsonify(list(map(leaseToDict, leases)))
  elif (request.method == 'POST'):
    clientData = request.json
    ncdmfLeaseId = clientData.get('ncdmf_lease_id')
    # find the NCDMF lease record
    ncdmfLease = db.session.query(NCDMFLease).filter_by(ncdmf_lease_id=ncdmfLeaseId).first()
    if (ncdmfLease):
      # assertion: at this point we know that the given ncdmf_lease_id is valid
      # now we need to check if this lease already exists for the current user
      userLease = db.session.query(UserLease).filter_by(user_id=user.id, ncdmf_lease_id=ncdmfLeaseId).first()
      if (userLease):
        # mark the lease as not deleted
        userLease.deleted = False
      else:
        # create a new lease record
        userLease = UserLease(user_id=user.id, **ncdmfLease.asDict())
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
    userLease = db.session.query(UserLease).filter_by(user_id=user.id, id=leaseId).first()
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
  userLeaseIds = db.session.query(UserLease.ncdmf_lease_id).filter_by(user_id=user.id, deleted=False).all()
  ncdmfLeaseIds = db.session.query(NCDMFLease.ncdmf_lease_id).\
      filter(
        NCDMFLease.ncdmf_lease_id.like('%%' + searchTerm + '%%'),
        ~NCDMFLease.ncdmf_lease_id.in_(list(map(lambda x: x[0], userLeaseIds)))
      ).all()
  return jsonify(list(map(lambda x: x[0], ncdmfLeaseIds)))

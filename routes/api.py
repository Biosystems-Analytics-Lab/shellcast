from flask import Blueprint, jsonify, request

from models import db
from models.User import User
from models.ClosureProbability import ClosureProbability
from models.SGAMinMaxProbability import SGAMinMaxProbability
from models.Lease import Lease

from routes.forms.ProfileInfoForm import ProfileInfoForm

from routes.authentication import userRequired

# just a temporary filler for the Mike Griffin API
NCDMF_LEASES = [
  {'ncdmf_lease_id': '4-C-89', 'grow_area_name': 'A01', 'rainfall_thresh_in': 1.5},
  {'ncdmf_lease_id': '819401', 'grow_area_name': 'B02', 'rainfall_thresh_in': 2.5},
  {'ncdmf_lease_id': '82-389B', 'grow_area_name': 'C03', 'rainfall_thresh_in': 3.5},
  {'ncdmf_lease_id': '123456', 'grow_area_name': 'D04', 'rainfall_thresh_in': 4.5}
]

api = Blueprint('api', __name__)

@api.route('/userInfo', methods=['GET', 'POST'])
@userRequired
def userInfo(user):
  if (request.method == 'GET'):
    userInfo = {}
    if (user.email != None):
      userInfo['email'] = user.email
    if (user.phone_number != None):
      userInfo['phone_number'] = user.phone_number
    return userInfo
  else: # request.method == 'POST'
    form = ProfileInfoForm.from_json(request.json)
    if (form.validate()):
      user.email = form.email.data
      user.phone_number = form.phone_number.data
      db.session.add(user)
      db.session.commit()
      return {'message': 'Success'}, 200
    return {'message': 'Bad form input'}, 400


def queryLeaseClosureProbabilities(user):
  leases = db.session.query(Lease).filter_by(user_id=user.id).all()
  probs = []
  for lease in leases:
    closureProb = db.session.query(ClosureProbability).filter_by(lease_id=lease.id).first()
    probDict = closureProb.asDict()
    probDict['ncdmf_lease_id'] = lease.ncdmf_lease_id
    probDict['geo_boundary'] = lease.geo_boundary
    probs.append(probDict)
  return probs

@api.route('/leaseProbs')
@userRequired
def getLeaseClosureProbabilities(user):
  return jsonify(queryLeaseClosureProbabilities(user))

def queryGrowAreaProbabilities():
  results = db.session.query(SGAMinMaxProbability).all()
  dictOfCPs = {}
  for r in results:
    sgaName = r.grow_area_name
    dictOfCPs[sgaName] = r.asDict()
  return dictOfCPs

@api.route('/growAreaProbs')
def getAreaData():
  # t0 = time.perf_counter_ns()
  dictOfCPs = queryGrowAreaProbabilities()
  # t1 = time.perf_counter_ns()
  # print('Total query time: {} ms'.format((t1 - t0) / 1000000))

  return jsonify(dictOfCPs)

@api.route('/leases')
@userRequired
def getLeases(user):
  leases = db.session.query(Lease).filter_by(user_id=user.id).all()
  def leaseToDict(lease):
    return {
      'id': lease.id,
      'ncdmf_lease_id': lease.ncdmf_lease_id,
      'grow_area_name': lease.grow_area_name,
      'rainfall_thresh_in': lease.rainfall_thresh_in,
      'geo_boundary': lease.geo_boundary,
      'email_pref': lease.email_pref,
      'text_pref': lease.text_pref,
      'window_pref': lease.window_pref,
      'prob_pref': lease.prob_pref,
    }
  return jsonify(list(map(leaseToDict, leases)))

@api.route('/searchLeases', methods=['POST'])
@userRequired
def searchLeases(user):
  searchTerm = str(request.json.get('search'))
  # TODO return the pre-collected leases from the Griffin API with a fuzzy search on the ncdmf lease id
  print('TODO return leases from database with a fuzzy search on the ncdmf lease id')
  leases = NCDMF_LEASES
  filteredLeases = filter(lambda x: searchTerm in str(x['ncdmf_lease_id']), leases)
  leaseIdsOnly = map(lambda x: x['ncdmf_lease_id'], filteredLeases)
  return jsonify(list(leaseIdsOnly))

@api.route('/addLease', methods=['POST'])
@userRequired
def addLease(user):
  ncdmfLeaseId = request.json.get('ncdmf_lease_id')
  # find the NCDMF lease record
  ncdmfLease = {'ncdmf_lease_id': ncdmfLeaseId}
  for lease in NCDMF_LEASES:
    if (lease['ncdmf_lease_id'] == ncdmfLeaseId):
      ncdmfLease = lease
      break
  newLease = Lease(user_id=user.id, **ncdmfLease)
  db.session.add(newLease)
  db.session.commit()
  return {
    'id': newLease.id,
    'ncdmf_lease_id': newLease.ncdmf_lease_id,
    'grow_area_name': newLease.grow_area_name,
    'rainfall_thresh_in': newLease.rainfall_thresh_in,
    'email_pref': newLease.email_pref,
    'text_pref': newLease.text_pref,
    'window_pref': newLease.window_pref,
    'prob_pref': newLease.prob_pref,
  }

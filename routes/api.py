from flask import Blueprint, jsonify, request

from models import db
from models.User import User
from models.ClosureProbability import ClosureProbability
from models.SGAMinMaxProbability import SGAMinMaxProbability
from models.Lease import Lease

from routes.forms.ProfileInfoForm import ProfileInfoForm

from routes.authentication import userRequired

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

@api.route('/searchLeases', methods=['POST'])
@userRequired
def searchLeases(user):
  searchTerm = str(request.json.get('search'))
  # TODO return the pre-collected leases from the Griffin API with a fuzzy search on the ncdmf lease id
  print('TODO return leases from database with a fuzzy search on the ncdmf lease id')
  leases = ['4-C-89', '819401', '82-389B', '123456']
  def matchesSearchTerm(item):
    return searchTerm in str(item)
  return filter(matchesSearchTerm, leases)

@api.route('/addLease', methods=['POST'])
@userRequired
def addLease(user):
  newLease = Lease(ncdmf_lease_id=request.json.get('ncdmf_lease_id'), user_id=user.id)
  db.session.add(newLease)
  db.session.commit()
  return {'message': 'Success'}, 200

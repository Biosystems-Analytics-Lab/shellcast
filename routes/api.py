from flask import Blueprint, jsonify, request

from models import db
from models.User import User
from models.ClosureProbability import ClosureProbability
from models.SGAMinMaxProbability import SGAMinMaxProbability
from models.Lease import Lease

from routes.forms.ProfileInfoForm import ProfileInfoForm

from routes.authentication import userRequired

NUMBER_OF_GROW_AREAS = 73

# just a temporary filler for the Mike Griffin API
NCDMF_LEASES = [
  {'ncdmf_lease_id': '4-C-89', 'grow_area_name': 'A01', 'rainfall_thresh_in': 1.5, 'geometry': (36.303915, -75.864693)},
  {'ncdmf_lease_id': '819401', 'grow_area_name': 'B02', 'rainfall_thresh_in': 2.5, 'geometry': (36.164344, -75.927864)},
  {'ncdmf_lease_id': '82-389B', 'grow_area_name': 'C03', 'rainfall_thresh_in': 3.5, 'geometry': (35.868877, -75.754829)},
  {'ncdmf_lease_id': '123456', 'grow_area_name': 'D04', 'rainfall_thresh_in': 4.5, 'geometry': (34.404497, -77.567573)}
]

api = Blueprint('api', __name__)

@api.route('/userInfo', methods=['GET', 'POST'])
@userRequired
def userInfo(user):
  """
  Returns the user's info if a GET request.  Updates the user's info if a POST request.
  """
  if (request.method == 'GET'):
    userInfo = {}
    if (user.email != None):
      userInfo['email'] = user.email
    if (user.phone_number != None):
      userInfo['phone_number'] = user.phone_number
    return userInfo
  else: # request.method == 'POST'
    # validate the uploaded info
    form = ProfileInfoForm.from_json(request.json)
    if (form.validate()):
      user.email = form.email.data
      user.phone_number = form.phone_number.data
      db.session.add(user)
      db.session.commit()
      return {'message': 'Success'}, 200
    return {'message': 'Bad form input'}, 400

@api.route('/leaseProbs')
@userRequired
def getLeaseClosureProbabilities(user):
  """
  Returns the user's lease closure probabilities.
  """
  leases = db.session.query(Lease).filter_by(user_id=user.id).all()
  def getLeaseProbForLease(lease):
    probDict = {'ncdmf_lease_id': lease.ncdmf_lease_id, 'geometry': lease.geometry}
    closureProb = db.session.query(ClosureProbability).filter_by(lease_id=lease.id).first()
    if (closureProb):
      probDict['prob_1d_perc'] = closureProb.prob_1d_perc
      probDict['prob_2d_perc'] = closureProb.prob_2d_perc
      probDict['prob_3d_perc'] = closureProb.prob_3d_perc
    return probDict
  leaseList = list(map(getLeaseProbForLease, leases))
  return jsonify(leaseList)

@api.route('/growAreaProbs')
def getGrowAreaProbabilities():
  """
  Returns the min/max closure probabilties for each grow area.
  """
  # t0 = time.perf_counter_ns()
  # TODO make sure this returns one (and only one) closure probability for each grow area
  growAreaProbs = db.session.query(SGAMinMaxProbability).order_by(SGAMinMaxProbability.id.desc()).limit(NUMBER_OF_GROW_AREAS)
  growAreaProbsAsDicts = {}
  for area in growAreaProbs:
    sgaName = area.grow_area_name
    growAreaProbsAsDicts[sgaName] = area.asDict()
  # t1 = time.perf_counter_ns()
  # print('Total query time: {} ms'.format((t1 - t0) / 1000000))

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
      'geometry': lease.geometry,
      'email_pref': lease.email_pref,
      'text_pref': lease.text_pref,
      'prob_pref': lease.prob_pref
    }
  if (request.method == 'GET'):
    leases = db.session.query(Lease).filter_by(user_id=user.id).all()
    return jsonify(list(map(leaseToDict, leases)))
  elif (request.method == 'POST'):
    clientData = request.json
    # find the NCDMF lease record
    for lease in NCDMF_LEASES:
      if (lease['ncdmf_lease_id'] == clientData.get('ncdmf_lease_id')):
        # assertion: at this point we know that the given ncdmf_lease_id is valid
        # now we need to check if this lease already exists for the current user
        leaseRecord = db.session.query(Lease).filter_by(id=clientData.get('id'), user_id=user.id, ncdmf_lease_id=clientData.get('ncdmf_lease_id')).first()
        if (leaseRecord):
          # update the existing record
          # TODO need to add checks for invalid values
          leaseRecord.email_pref = request.json.get('email_pref')
          leaseRecord.text_pref = request.json.get('text_pref')
          leaseRecord.prob_pref = request.json.get('prob_pref')
        else:
          # create a new lease record
          leaseRecord = Lease(user_id=user.id, **lease)
        db.session.add(leaseRecord)
        db.session.commit()
        return leaseToDict(leaseRecord)
    return {'message': 'The given lease id does not exist.'}, 400
  else: # request.method == 'DELETE'
    print('TODO delete lease')
    return {'message': 'Success'}, 200

@api.route('/searchLeases', methods=['POST'])
@userRequired
def searchLeases(user):
  """
  Returns leases based on a search term.
  """
  searchTerm = str(request.json.get('search'))
  # TODO return the pre-collected leases from the Griffin API with a fuzzy search on the ncdmf lease id
  print('TODO return leases from database with a fuzzy search on the ncdmf lease id')
  leases = NCDMF_LEASES
  filteredLeases = filter(lambda x: searchTerm in str(x['ncdmf_lease_id']), leases)
  leaseIdsOnly = map(lambda x: x['ncdmf_lease_id'], filteredLeases)
  return jsonify(list(leaseIdsOnly))

import pytest

from main import createApp
from models import db as _db

from config import TestConfig

from firebase_admin import auth
from firebase_admin.auth import ExpiredIdTokenError, InvalidIdTokenError

import boto3

import random
import string

RNG_SEED = 8375

# will be run once at the beginning of the testing session
@pytest.fixture(scope='session')
def monkeyPatchBotoClient():
  class MockClient():
    def __init__(self, *args, **kwargs):
      pass
    def send_email(self, *args, **kwargs):
      return {'MessageId': 'bleh'}

  # replace the boto3.client definition
  realBotoClient = boto3.client
  boto3.client = MockClient

  yield MockClient

  # restore the true boto3 client
  boto3.client = realBotoClient

# will be run once at the beginning of the testing session
@pytest.fixture(scope='session')
def app():
  return createApp(TestConfig())

# will be run once at the beginning of the testing session
@pytest.fixture(scope='session')
def client(app):
  with app.test_client() as c:
    yield c

# will be run once at the beginning of the testing session
@pytest.fixture(scope='session')
def db(app):
  # setup
  _db.app = app
  _db.create_all()

  yield _db

  # teardown
  _db.drop_all()

# will be called before every test function automatically
@pytest.fixture(scope='function', autouse=True)
def dbSession(db):
  # setup
  connection = db.engine.connect()
  transaction = connection.begin()
  options = dict(bind=connection, binds={})
  session = db.create_scoped_session(options=options)
  db.session = session

  # keeps track of the tables that are used during this session
  tablesUsed = {}
  # override the session .add and .add_all functions with similar functions
  # that also record the tables that are used
  origAddFunc = session.add
  origAddAllFunc = session.add_all
  def mockAdd(model):
    tablesUsed[model.__tablename__] = True
    origAddFunc(model)
  session.add = mockAdd
  def mockAddAll(models):
    for model in models:
      tablesUsed[model.__tablename__] = True
    origAddAllFunc(models)
  session.add_all = mockAddAll

  yield session

  # teardown
  transaction.rollback() # rollback all database operations
  for table in tablesUsed: # reset the auto_increment fields for all tables that were used
    session.execute('ALTER TABLE {} AUTO_INCREMENT = 1;'.format(table))
  connection.close()
  session.remove()

@pytest.fixture(scope='function', autouse=True)
def addMockFbUser():
  """
  Monkey patches Firebase token verification and yields a function that can
  be used to create mock Firebase users and their ID tokens.
  """
  mockFirebaseUsers = {}

  def mockTokenVerification(token):
    if (token not in mockFirebaseUsers):
      raise InvalidIdTokenError('{} is not a valid token.'.format(token))
    user = mockFirebaseUsers[token]
    if (user['tokenExpired']):
      raise ExpiredIdTokenError('{} is expired.'.format(token), None)
    return user['userInfo']

  # replace the verify_id_token definition
  realTokenVerification = auth.verify_id_token
  auth.verify_id_token = mockTokenVerification

  def addUser(userInfo, token, tokenIsExpired=False):
    mockFirebaseUsers[token] = dict(tokenExpired=tokenIsExpired, userInfo=userInfo)

  yield addUser

  # restore true token verification
  auth.verify_id_token = realTokenVerification

@pytest.fixture(scope='function', autouse=True)
def genRandomString():
  random.seed(RNG_SEED)

  def generator(chars=string.printable, length=10):
    return ''.join(random.choice(chars) for _ in range(length))

  yield generator

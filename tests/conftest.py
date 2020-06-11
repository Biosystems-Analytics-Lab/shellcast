import pytest

from main import createApp
from models import db as _db

from config import TestConfig

from firebase_admin import auth
from firebase_admin.auth import ExpiredIdTokenError, InvalidIdTokenError

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

  yield session

  # teardown
  transaction.rollback()
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

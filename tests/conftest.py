import pytest

from main import createApp
from models import db as _db

from config import TestConfig

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

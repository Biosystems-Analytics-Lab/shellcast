import os
import random
import string

from dotenv import load_dotenv
from sqlalchemy.orm import scoped_session, sessionmaker

# Load local .env for development/testing, but allow explicit test defaults
# below to take precedence when they set a value.
_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_ENV_PATH = os.path.join(_BASE_DIR, ".env")
load_dotenv(dotenv_path=_ENV_PATH, override=False)

# Set test environment before main (and createApp) are loaded
os.environ.setdefault("HOST", "127.0.0.1")
os.environ.setdefault("PORT", "3361")
os.environ.setdefault("TESTING", "true")
os.environ.setdefault("SECRET_KEY", "test-secret-key")
os.environ.setdefault("EMAIL_SECRET_KEY", "test-email-secret-key")
os.environ.setdefault("DB_USER", "test")
os.environ.setdefault("DB_PASS", "test")
os.environ.setdefault("DB_NAME", "shellcast_nc")
os.environ.setdefault("DB_HOST", "127.0.0.1")
os.environ.setdefault("DB_PORT", "3306")
os.environ.setdefault("DB_UNIX_SOCKET_PATH_PREFIX", "./cloudsql/")
os.environ.setdefault("CLOUD_SQL_INSTANCE_NAME", "test:us-east1:test")
os.environ.setdefault("DB_POOL_SIZE", "5")
os.environ.setdefault("DB_MAX_OVERFLOW", "2")
os.environ.setdefault("DB_POOL_TIMEOUT", "30")
os.environ.setdefault("DB_POOL_RECYCLE", "1800")
os.environ.setdefault("SQLALCHEMY_DATABASE_URI", "sqlite:///test_shellcast.db")
os.environ.setdefault("NC_LOG_SECRET", "test-nc-log-secret")

import boto3
import pytest
from firebase_admin import auth
from firebase_admin.auth import (
    ExpiredIdTokenError,
    InvalidIdTokenError,
    UserNotFoundError,
)
from main import create_app
from models import db as _db

RNG_SEED = 8375


# will be run once at the beginning of the testing session
@pytest.fixture(scope="session")
def monkeypatch_boto_client():
    emailsSent = {}

    class MockClient:
        def __init__(self, *args, **kwargs):
            pass

        def send_email(self, *args, **kwargs):
            address = kwargs["Destination"]["ToAddresses"][0]
            subject = kwargs["Message"]["Subject"]["Data"]
            body = kwargs["Message"]["Body"]["Text"]["Data"]
            if emailsSent.get(address) is None:
                emailsSent[address] = [{"subject": subject, "body": body}]
            else:
                emailsSent[address].append({"subject": subject, "body": body})
            return {"MessageId": "abc123"}

    # replace the boto3.client definition
    realBotoClient = boto3.client
    boto3.client = MockClient

    yield lambda: emailsSent

    # restore the true boto3 client
    boto3.client = realBotoClient


# will be run once at the beginning of the testing session
@pytest.fixture(scope="session")
def app():
    app = create_app()
    ctx = app.app_context()
    ctx.push()
    try:
        yield app
    finally:
        ctx.pop()


# will be run once at the beginning of the testing session
@pytest.fixture(scope="session")
def client(app):
    with app.test_client() as c:
        yield c


# will be run once at the beginning of the testing session
@pytest.fixture(scope="session")
def db(app):
    # setup
    _db.app = app
    _db.create_all()

    yield _db

    # teardown
    _db.drop_all()


# will be called before every test function automatically
@pytest.fixture(scope="function", autouse=True)
def db_session(db):
    # setup
    connection = db.engine.connect()
    transaction = connection.begin()
    session_factory = sessionmaker(bind=connection)
    session = scoped_session(session_factory)
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
    transaction.rollback()  # rollback all database operations
    # Reset auto_increment only for MySQL (SQLite does not support this)
    if "sqlite" not in db.engine.url.drivername:
        for table in tablesUsed:
            session.execute("ALTER TABLE {} AUTO_INCREMENT = 1;".format(table))
    connection.close()
    session.remove()


@pytest.fixture(scope="function", autouse=True)
def add_mock_fb_user():
    """
    Monkey patches Firebase token verification and yields a function that can
    be used to create mock Firebase users and their ID tokens.
    """
    mockFirebaseUsers = {}

    def mockTokenVerification(token):
        if token not in mockFirebaseUsers:
            raise InvalidIdTokenError("{} is not a valid token.".format(token))
        user = mockFirebaseUsers[token]
        if user["tokenExpired"]:
            raise ExpiredIdTokenError("{} is expired.".format(token), None)
        return user["userInfo"]

    # replace the verify_id_token definition
    realTokenVerification = auth.verify_id_token
    auth.verify_id_token = mockTokenVerification

    def mockDeleteUser(firebaseUID):
        for token in mockFirebaseUsers:
            user = mockFirebaseUsers[token]
            if user["userInfo"]["uid"] == firebaseUID:
                del mockFirebaseUsers[token]
                return
        raise UserNotFoundError(
            "A user with the UID {} was not found.".format(firebaseUID)
        )

    # replace the delete_user definition
    realDeleteUser = auth.delete_user
    auth.delete_user = mockDeleteUser

    def addUser(userInfo, token, tokenIsExpired=False):
        mockFirebaseUsers[token] = dict(tokenExpired=tokenIsExpired, userInfo=userInfo)

    yield addUser

    # restore true token verification
    auth.verify_id_token = realTokenVerification
    # restore true delete_user
    auth.delete_user = realDeleteUser


@pytest.fixture(scope="function", autouse=True)
def gen_random_string():
    random.seed(RNG_SEED)

    def generator(chars=string.printable, length=10):
        return "".join(random.choice(chars) for _ in range(length))

    yield generator

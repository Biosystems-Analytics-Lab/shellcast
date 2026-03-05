"""
Clean pytest configuration for ShellCast SC application.
Uses SQLite in-memory database for testing.
"""

import pytest
from firebase_admin import auth
from firebase_admin.auth import (
    ExpiredIdTokenError,
    InvalidIdTokenError,
    UserNotFoundError,
)
from main import createApp
from models import db
from tests.test_config import get_test_config


@pytest.fixture(scope="function", autouse=True)
def add_mock_fb_user():
    """
    Monkey-patch Firebase token verification; yields addUser(user_info, token) for tests.
    """
    mock_users = {}

    def mock_verify_id_token(token):
        if token not in mock_users:
            raise InvalidIdTokenError(f"Invalid token: {token}")
        rec = mock_users[token]
        if rec.get("token_expired"):
            raise ExpiredIdTokenError("Token expired", None)
        return rec["user_info"]

    def mock_delete_user(firebase_uid):
        for t, rec in list(mock_users.items()):
            if rec["user_info"].get("uid") == firebase_uid:
                del mock_users[t]
                return
        raise UserNotFoundError(f"User {firebase_uid} not found")

    real_verify = auth.verify_id_token
    real_delete = auth.delete_user
    auth.verify_id_token = mock_verify_id_token
    auth.delete_user = mock_delete_user

    def add_user(user_info, token, token_expired=False):
        mock_users[token] = {"user_info": user_info, "token_expired": token_expired}

    yield add_user

    auth.verify_id_token = real_verify
    auth.delete_user = real_delete


@pytest.fixture(scope="function")
def app():
    """Create and configure a new app instance for each test."""
    config = get_test_config()
    app = createApp(config)

    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()


@pytest.fixture(scope="function")
def client(app):
    """A test client for the app."""
    return app.test_client()


@pytest.fixture(scope="function")
def db_session(app):
    """Database session for testing."""
    with app.app_context():
        yield db.session


# Database-specific fixtures for advanced testing
@pytest.fixture(scope="session")
def mysql_app():
    """Create app with MySQL configuration for integration tests."""
    from config import TestConfigMySQL

    app = createApp(TestConfigMySQL())

    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()


@pytest.fixture(scope="session")
def mysql_client(mysql_app):
    """Test client for MySQL-based tests."""
    return mysql_app.test_client()


@pytest.fixture(scope="session")
def mysql_session(mysql_app):
    """Database session for MySQL-based tests."""
    with mysql_app.app_context():
        yield db.session

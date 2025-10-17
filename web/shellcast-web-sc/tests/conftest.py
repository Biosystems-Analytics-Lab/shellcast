"""
Clean pytest configuration for ShellCast SC application.
Uses SQLite in-memory database for testing.
"""

import pytest
from main import createApp
from models import db
from tests.test_config import get_test_config


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


# Fixture factories for common test scenarios
@pytest.fixture
def user_fixtures():
    """Access to user fixtures."""
    from tests.fixtures import UserFixtures

    return UserFixtures


@pytest.fixture
def lease_fixtures():
    """Access to lease fixtures."""
    from tests.fixtures import LeaseFixtures

    return LeaseFixtures


@pytest.fixture
def notification_fixtures():
    """Access to notification fixtures."""
    from tests.fixtures import NotificationFixtures

    return NotificationFixtures


@pytest.fixture
def test_data():
    """Access to test data sets."""
    from tests.fixtures import TestDataSets

    return TestDataSets

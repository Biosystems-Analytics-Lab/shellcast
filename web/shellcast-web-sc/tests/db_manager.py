"""
Advanced database management for Flask testing (Django-style).
Provides database duplication, clearing, and transaction management.
"""

import os
import shutil
import tempfile
from contextlib import contextmanager

from models import db
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker


class TestDatabaseManager:
    """
    Manages test databases like Django's testing framework.
    Supports database duplication, clearing, and transaction rollback.
    """

    def __init__(self, app, config):
        self.app = app
        self.config = config
        # Handle both property and direct attribute cases
        if hasattr(config, "SQLALCHEMY_DATABASE_URI"):
            self.original_uri = config.SQLALCHEMY_DATABASE_URI
        else:
            # Fallback for property-based configs
            self.original_uri = getattr(
                config, "SQLALCHEMY_DATABASE_URI", "sqlite:///:memory:"
            )
        self.test_uri = None
        self.test_engine = None
        self.test_session_factory = None

    def create_test_database(self):
        """Create a fresh test database (like Django's TestCase)."""
        if "sqlite" in self.original_uri:
            # SQLite: Use in-memory with shared cache
            self.test_uri = "sqlite:///:memory:?cache=shared"
            self.test_engine = create_engine(self.test_uri)
        else:
            # MySQL/PostgreSQL: Create actual test database
            self._create_mysql_test_database()

        # Create all tables
        with self.app.app_context():
            db.create_all()

        return self.test_uri

    def _create_mysql_test_database(self):
        """Create a MySQL test database (like Django's TestCase)."""
        # Parse original URI to get connection details
        if "mysql" in self.original_uri:
            # Extract database name and create test version
            db_name = f"test_{self.config.DB_NAME}"

            # Connect to MySQL server (without specifying database)
            base_uri = f"mysql+pymysql://{self.config.DB_USER}:{self.config.DB_PASS}@{self.config.DB_HOST}:{self.config.DB_PORT}"
            base_engine = create_engine(base_uri)

            with base_engine.connect() as conn:
                # Drop test database if it exists
                conn.execute(text(f"DROP DATABASE IF EXISTS `{db_name}`"))
                # Create fresh test database
                conn.execute(
                    text(
                        f"CREATE DATABASE `{db_name}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
                    )
                )
                conn.commit()

            # Set test database URI
            self.test_uri = f"{base_uri}/{db_name}"
            self.test_engine = create_engine(self.test_uri)

    def destroy_test_database(self):
        """Destroy the test database (like Django's TestCase)."""
        if self.test_engine:
            self.test_engine.dispose()

        if "mysql" in self.test_uri:
            # Drop MySQL test database
            base_uri = self.test_uri.rsplit("/", 1)[0]
            base_engine = create_engine(base_uri)

            with base_engine.connect() as conn:
                db_name = self.test_uri.rsplit("/", 1)[1]
                conn.execute(text(f"DROP DATABASE IF EXISTS `{db_name}`"))
                conn.commit()

    @contextmanager
    def test_database(self):
        """Context manager for test database (like Django's TestCase)."""
        try:
            self.create_test_database()
            yield self.test_engine
        finally:
            self.destroy_test_database()

    def clear_database(self):
        """Clear all data from test database (like Django's TestCase)."""
        with self.app.app_context():
            # Get all tables
            inspector = db.inspect(db.engine)
            table_names = inspector.get_table_names()

            # Disable foreign key checks (MySQL)
            if "mysql" in self.test_uri:
                with db.engine.connect() as conn:
                    conn.execute(text("SET FOREIGN_KEY_CHECKS = 0"))

                    for table in table_names:
                        conn.execute(text(f"TRUNCATE TABLE `{table}`"))

                    conn.execute(text("SET FOREIGN_KEY_CHECKS = 1"))
                    conn.commit()
            else:
                # SQLite: Delete all data
                for table in table_names:
                    with db.engine.connect() as conn:
                        conn.execute(text(f"DELETE FROM {table}"))
                        conn.commit()

    def load_fixtures(self, fixtures_data):
        """Load test fixtures (like Django's fixtures)."""
        with self.app.app_context():
            for model_class, records in fixtures_data.items():
                for record_data in records:
                    instance = model_class(**record_data)
                    db.session.add(instance)
            db.session.commit()

    def get_test_session(self):
        """Get a test database session."""
        if not self.test_engine:
            self.create_test_database()

        Session = sessionmaker(bind=self.test_engine)
        return Session()


class TransactionTestCase:
    """
    Base class for tests that need transaction management (like Django's TransactionTestCase).
    Each test runs in its own transaction and gets rolled back.
    """

    def __init__(self, app, db_manager):
        self.app = app
        self.db_manager = db_manager
        self.session = None

    def setUp(self):
        """Set up test database and session."""
        self.session = self.db_manager.get_test_session()

    def tearDown(self):
        """Clean up after test."""
        if self.session:
            self.session.close()

    @contextmanager
    def transaction(self):
        """Context manager for database transaction."""
        try:
            yield self.session
            self.session.commit()
        except Exception:
            self.session.rollback()
            raise


class TestCase:
    """
    Base class for tests with automatic transaction rollback (like Django's TestCase).
    Each test runs in a transaction that gets rolled back automatically.
    """

    def __init__(self, app, db_manager):
        self.app = app
        self.db_manager = db_manager
        self.session = None

    def setUp(self):
        """Set up test database and session."""
        self.session = self.db_manager.get_test_session()
        # Start transaction
        self.session.begin()

    def tearDown(self):
        """Rollback transaction and clean up."""
        if self.session:
            self.session.rollback()
            self.session.close()

    def assertDatabaseHas(self, model_class, **filters):
        """Assert that database contains record (like Django's assertContains)."""
        record = self.session.query(model_class).filter_by(**filters).first()
        assert (
            record is not None
        ), f"No {model_class.__name__} found with filters: {filters}"

    def assertDatabaseCount(self, model_class, expected_count):
        """Assert database has expected number of records."""
        actual_count = self.session.query(model_class).count()
        assert (
            actual_count == expected_count
        ), f"Expected {expected_count} {model_class.__name__} records, got {actual_count}"

    def assertDatabaseEmpty(self, model_class):
        """Assert database has no records of given model."""
        count = self.session.query(model_class).count()
        assert count == 0, f"Expected 0 {model_class.__name__} records, got {count}"

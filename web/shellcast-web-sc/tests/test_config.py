"""
Test configuration management for different testing strategies.
This module helps ensure tests work in both SQLite and MySQL environments.
"""

import os

from config import TestConfig, TestConfigMySQL


def get_test_config():
    """
    Get the appropriate test configuration based on environment.

    Returns:
        TestConfig: Either SQLite (fast) or MySQL (production-like) config
    """
    # Check if we want to test against MySQL
    use_mysql = os.environ.get("TEST_MYSQL", "false").lower() == "true"

    if use_mysql:
        print("🧪 Using MySQL test configuration (production-like)")
        return TestConfigMySQL()
    else:
        print("🧪 Using SQLite test configuration (fast)")
        return TestConfig()


def get_test_database_url():
    """
    Get the test database URL for database setup scripts.

    Returns:
        str: Database URL for testing
    """
    config = get_test_config()
    return config.SQLALCHEMY_DATABASE_URI


# Test environment variables you can set:
#
# Fast testing (default):
#   export TEST_MYSQL=false  # or don't set it
#   python -m pytest tests/  # Uses SQLite
#
# Production-like testing:
#   export TEST_MYSQL=true
#   python -m pytest tests/  # Uses MySQL
#
# Run both:
#   python -m pytest tests/  # SQLite
#   TEST_MYSQL=true python -m pytest tests/  # MySQL

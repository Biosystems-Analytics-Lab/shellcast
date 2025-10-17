#!/usr/bin/env python3
"""
Unit tests for EmailNotification class email consent logic

This module tests the state-specific email consent behavior:
- SC and FL: Require both email_pref=1 AND email_consent=1 for email notifications
- NC: Only requires email_pref=1 (email_consent is ignored)

Usage:
# Run all tests
python -m pytest test_email_notification.py -v

# Run specific test class
python -m pytest test_email_notification.py::TestEmailConsentLogic -v

# Run specific test
python -m pytest test_email_notification.py::TestEmailConsentLogic::test_sc_with_both_pref_and_consent -v

# Run with unittest
python test_email_notification.py
"""

import logging
import os
import sys
import unittest
from datetime import datetime
from unittest.mock import Mock, patch

# Add the parent directory to the Python path to import from src
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from notifications import NotificationEmailContentGenerator, filter_users_by_preferences

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def create_test_data(state, user_id, user_email, email_pref=1, email_consent=1):
    """Create test data for specified state, user_id, and email"""
    # Mock data that would come from the database
    test_data = [
        {
            "user_id": user_id,
            "email": user_email,
            "phone": None,
            "prob_pref": 3,  # Moderate threshold
            "email_pref": email_pref,  # Email preference (0 or 1)
            "email_consent": email_consent,  # Email consent (0 or 1)
            "text_pref": 0,  # Text disabled
            "text_consent": 0,  # Text consent disabled
            "threshold": 4,
            "lease_id": f"TEST{user_id:03d}",
            "area_id": f"{state.upper()}001",
            "user_code": f"TEST_USER_{user_id}",
            "prob_1d_perc": 4,  # High probability today
            "prob_2d_perc": 3,  # Moderate probability tomorrow
            "prob_3d_perc": 2,  # Low probability in 2 days
        }
    ]
    return test_data


class TestEmailConsentLogic(unittest.TestCase):
    """Test cases for email consent logic in different states"""

    def test_sc_with_both_pref_and_consent(self):
        """Test SC with both email_pref=1 and email_consent=1 (should work)"""
        test_data = create_test_data(
            "SC", 1, "test@example.com", email_pref=1, email_consent=1
        )
        filtered_data = filter_users_by_preferences(
            test_data, prob_1d_only=False, state="SC"
        )

        self.assertEqual(len(filtered_data), 1)
        self.assertEqual(filtered_data[0]["email"], "test@example.com")

    def test_sc_with_pref_but_no_consent(self):
        """Test SC with email_pref=1 but email_consent=0 (should fail)"""
        test_data = create_test_data(
            "SC", 1, "test@example.com", email_pref=1, email_consent=0
        )
        filtered_data = filter_users_by_preferences(
            test_data, prob_1d_only=False, state="SC"
        )

        self.assertEqual(len(filtered_data), 0)

    def test_sc_with_consent_but_no_pref(self):
        """Test SC with email_pref=0 but email_consent=1 (should fail)"""
        test_data = create_test_data(
            "SC", 1, "test@example.com", email_pref=0, email_consent=1
        )
        filtered_data = filter_users_by_preferences(
            test_data, prob_1d_only=False, state="SC"
        )

        self.assertEqual(len(filtered_data), 0)

    def test_fl_with_both_pref_and_consent(self):
        """Test FL with both email_pref=1 and email_consent=1 (should work)"""
        test_data = create_test_data(
            "FL", 1, "test@example.com", email_pref=1, email_consent=1
        )
        filtered_data = filter_users_by_preferences(
            test_data, prob_1d_only=True, state="FL"
        )

        self.assertEqual(len(filtered_data), 1)
        self.assertEqual(filtered_data[0]["email"], "test@example.com")

    def test_fl_with_pref_but_no_consent(self):
        """Test FL with email_pref=1 but email_consent=0 (should fail)"""
        test_data = create_test_data(
            "FL", 1, "test@example.com", email_pref=1, email_consent=0
        )
        filtered_data = filter_users_by_preferences(
            test_data, prob_1d_only=True, state="FL"
        )

        self.assertEqual(len(filtered_data), 0)

    def test_nc_with_pref_only(self):
        """Test NC with email_pref=1 (should work - NC doesn't check consent)"""
        test_data = create_test_data(
            "NC", 1, "test@example.com", email_pref=1, email_consent=0
        )
        filtered_data = filter_users_by_preferences(
            test_data, prob_1d_only=False, state="NC"
        )

        self.assertEqual(len(filtered_data), 1)
        self.assertEqual(filtered_data[0]["email"], "test@example.com")

    def test_nc_with_pref_and_consent(self):
        """Test NC with both email_pref=1 and email_consent=1 (should work)"""
        test_data = create_test_data(
            "NC", 1, "test@example.com", email_pref=1, email_consent=1
        )
        filtered_data = filter_users_by_preferences(
            test_data, prob_1d_only=False, state="NC"
        )

        self.assertEqual(len(filtered_data), 1)
        self.assertEqual(filtered_data[0]["email"], "test@example.com")

    def test_nc_without_pref(self):
        """Test NC with email_pref=0 (should fail)"""
        test_data = create_test_data(
            "NC", 1, "test@example.com", email_pref=0, email_consent=1
        )
        filtered_data = filter_users_by_preferences(
            test_data, prob_1d_only=False, state="NC"
        )

        self.assertEqual(len(filtered_data), 0)

    def test_unknown_state_defaults_to_nc_behavior(self):
        """Test unknown state defaults to NC behavior (only check email_pref)"""
        test_data = create_test_data(
            "UNKNOWN", 1, "test@example.com", email_pref=1, email_consent=0
        )
        filtered_data = filter_users_by_preferences(
            test_data, prob_1d_only=False, state="UNKNOWN"
        )

        self.assertEqual(len(filtered_data), 1)
        self.assertEqual(filtered_data[0]["email"], "test@example.com")


class TestEmailContentGeneration(unittest.TestCase):
    """Test cases for email content generation with consent logic"""

    def setUp(self):
        """Set up test fixtures"""
        self.notification_config = Mock()
        self.notification_config.lease_template = "Test lease template"
        self.notification_config.lease_template_today_only = (
            "Test lease template today only"
        )
        self.notification_config.subject_template = "Test subject for {}"
        self.notification_config.notification_footer = "Test footer"
        self.notification_config.web_base_url = "https://test.example.com"
        self.notification_config.secret_key = "test_secret_key"

    def test_sc_content_generation_with_consent(self):
        """Test SC content generation with both pref and consent"""
        test_data = create_test_data(
            "SC", 1, "test@example.com", email_pref=1, email_consent=1
        )
        content_generator = NotificationEmailContentGenerator(
            self.notification_config, "SC", test_data
        )

        contents = content_generator()
        self.assertEqual(len(contents), 1)
        self.assertEqual(contents[0]["email"], "test@example.com")

    def test_sc_content_generation_without_consent(self):
        """Test SC content generation without consent (should generate no content)"""
        test_data = create_test_data(
            "SC", 1, "test@example.com", email_pref=1, email_consent=0
        )
        content_generator = NotificationEmailContentGenerator(
            self.notification_config, "SC", test_data
        )

        contents = content_generator()
        self.assertEqual(len(contents), 0)

    def test_fl_content_generation_with_consent(self):
        """Test FL content generation with both pref and consent"""
        test_data = create_test_data(
            "FL", 1, "test@example.com", email_pref=1, email_consent=1
        )
        content_generator = NotificationEmailContentGenerator(
            self.notification_config, "FL", test_data
        )

        contents = content_generator()
        self.assertEqual(len(contents), 1)
        self.assertEqual(contents[0]["email"], "test@example.com")

    def test_nc_content_generation_with_pref_only(self):
        """Test NC content generation with pref only (should work)"""
        test_data = create_test_data(
            "NC", 1, "test@example.com", email_pref=1, email_consent=0
        )
        content_generator = NotificationEmailContentGenerator(
            self.notification_config, "NC", test_data
        )

        contents = content_generator()
        self.assertEqual(len(contents), 1)
        self.assertEqual(contents[0]["email"], "test@example.com")


if __name__ == "__main__":
    # Run the tests
    unittest.main(verbosity=2)

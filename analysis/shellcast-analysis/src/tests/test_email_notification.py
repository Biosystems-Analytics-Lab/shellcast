#!/usr/bin/env python3
"""
Unit tests for email notification preference and unsubscribe content.

Usage:
    python -m pytest test_email_notification.py -v
"""

import logging
import os
import sys
import unittest
from unittest.mock import Mock

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from notifications import (  # noqa: E402
    NotificationEmailContentGenerator,
    filter_users_by_preferences,
    user_wants_email_notifications,
)

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def create_test_data(state, user_id, user_email, email_pref=1):
    """Create test row dict as returned by SelectUserLeaseProbsToday."""
    return [
        {
            "user_id": user_id,
            "email": user_email,
            "phone": None,
            "prob_pref": 3,
            "email_pref": email_pref,
            "threshold": 4,
            "lease_id": f"TEST{user_id:03d}",
            "area_id": f"{state.upper()}001",
            "user_code": f"TEST_USER_{user_id}",
            "prob_1d_perc": 4,
            "prob_2d_perc": 3,
            "prob_3d_perc": 2,
        }
    ]


class TestEmailPrefLogic(unittest.TestCase):
    """Email sends require email_pref and a non-empty email address."""

    def test_user_wants_email_notifications(self):
        self.assertTrue(
            user_wants_email_notifications({"email_pref": 1, "email": "a@b.com"})
        )
        self.assertFalse(user_wants_email_notifications({"email_pref": 1, "email": ""}))
        self.assertFalse(
            user_wants_email_notifications({"email_pref": 0, "email": "a@b.com"})
        )

    def test_all_states_with_pref_and_email(self):
        for state in ("NC", "SC", "FL"):
            test_data = create_test_data(state, 1, "test@example.com", email_pref=1)
            filtered = filter_users_by_preferences(
                test_data, prob_1d_only=(state == "FL"), state=state
            )
            self.assertEqual(len(filtered), 1, state)

    def test_without_pref(self):
        test_data = create_test_data("NC", 1, "test@example.com", email_pref=0)
        filtered = filter_users_by_preferences(test_data, state="NC")
        self.assertEqual(len(filtered), 0)

    def test_without_email_address(self):
        row = create_test_data("NC", 1, "", email_pref=1)[0]
        row["email"] = ""
        filtered = filter_users_by_preferences([row], state="NC")
        self.assertEqual(len(filtered), 0)


class TestEmailContentGeneration(unittest.TestCase):
    """Email bodies include an unsubscribe link for every state."""

    def setUp(self):
        self.notification_config = Mock()
        self.notification_config.lease_template = "Test lease template"
        self.notification_config.lease_template_today_only = (
            "Test lease template today only"
        )
        self.notification_config.subject_template = "{} ShellCast Forecasts for {}"
        self.notification_config.notification_footer = "Test footer"
        self.notification_config.web_base_url = "https://test.example.com"
        self.notification_config.secret_key = "test_secret_key"

    def _assert_has_unsubscribe(self, state, prob_1d_only=False, token_link=False):
        test_data = create_test_data(state, 1, "test@example.com", email_pref=1)
        generator = NotificationEmailContentGenerator(
            self.notification_config, state, test_data
        )
        contents = generator()
        self.assertEqual(len(contents), 1)
        self.assertIn("unsubscribe", contents[0]["content"].lower())
        self.assertIn("/preferences", contents[0]["content"])
        if token_link:
            self.assertIn("/u/", contents[0]["content"])

    def test_nc_includes_unsubscribe_link(self):
        self._assert_has_unsubscribe("NC", token_link=True)

    def test_sc_includes_unsubscribe_link(self):
        self._assert_has_unsubscribe("SC", token_link=True)

    def test_fl_includes_unsubscribe_link(self):
        self._assert_has_unsubscribe("FL", prob_1d_only=True, token_link=True)

    def test_no_content_without_email_pref(self):
        test_data = create_test_data("SC", 1, "test@example.com", email_pref=0)
        generator = NotificationEmailContentGenerator(
            self.notification_config, "SC", test_data
        )
        self.assertEqual(len(generator()), 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)

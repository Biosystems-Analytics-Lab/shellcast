"""Regression tests for users table schema and timestamp behavior."""

from datetime import datetime, timezone
from unittest.mock import MagicMock, patch


from models.User import User


class TestUserSchema:
    def test_email_consent_column_removed(self):
        column_names = {c.name for c in User.__table__.columns}
        assert "email_consent" not in column_names

    def test_audit_and_opt_columns_present(self):
        column_names = {c.name for c in User.__table__.columns}
        for name in (
            "email_opt_in_date",
            "email_opt_out_date",
            "text_opt_in_date",
            "text_opt_out_date",
            "created",
            "updated",
        ):
            assert name in column_names


class TestUserTouchUpdated:
    def test_touch_updated_sets_aware_utc(self):
        user = User()
        user.touch_updated()
        assert user.updated is not None
        assert user.updated.tzinfo is not None

    def test_touch_updated_accepts_explicit_time(self):
        user = User()
        fixed = datetime(2024, 6, 1, 12, 0, 0, tzinfo=timezone.utc)
        user.touch_updated(fixed)
        assert user.updated == fixed


class TestEnsureUserExists:
    @patch("routes.authentication.db")
    @patch("routes.authentication.User")
    def test_new_user_gets_created_and_updated_at_registration(
        self, mock_user_cls, mock_db
    ):
        from routes.authentication import ensure_user_exists

        mock_user_cls.query.filter_by.return_value.first.return_value = None
        created_user = MagicMock()
        mock_user_cls.return_value = created_user

        fb_info = {"uid": "firebase123456789012", "email": "grower@example.com"}
        result = ensure_user_exists(fb_info)

        assert result is created_user
        mock_user_cls.assert_called_once()
        kwargs = mock_user_cls.call_args.kwargs
        assert kwargs["firebase_uid"] == fb_info["uid"]
        assert kwargs["email"] == fb_info["email"]
        assert kwargs["created"] == kwargs["updated"]
        assert kwargs["created"].tzinfo is not None
        mock_db.session.add.assert_called_once_with(created_user)
        mock_db.session.commit.assert_called_once()

    @patch("routes.authentication.db")
    @patch("routes.authentication.User")
    def test_existing_user_not_recreated(self, mock_user_cls, mock_db):
        from routes.authentication import ensure_user_exists

        existing = MagicMock()
        mock_user_cls.query.filter_by.return_value.first.return_value = existing

        result = ensure_user_exists({"uid": "x", "email": "a@b.com"})

        assert result is existing
        mock_user_cls.assert_not_called()
        mock_db.session.add.assert_not_called()


def _apply_email_pref_timestamps(user, new_pref, prev_pref, now):
    """Mirror POST /user-info email_pref transition logic."""
    if new_pref != prev_pref:
        if new_pref:
            user.email_opt_in_date = now
            user.email_opt_out_date = None
        else:
            user.email_opt_out_date = now


class TestEmailPrefTimestamps:
    def test_opt_in_clears_opt_out_and_sets_in_date(self):
        user = User()
        user.email_pref = False
        now = datetime(2025, 1, 2, 3, 4, 5, tzinfo=timezone.utc)
        _apply_email_pref_timestamps(user, True, False, now)
        assert user.email_opt_in_date == now
        assert user.email_opt_out_date is None

    def test_opt_out_sets_out_date_only(self):
        user = User()
        user.email_pref = True
        now = datetime(2025, 1, 2, 3, 4, 5, tzinfo=timezone.utc)
        _apply_email_pref_timestamps(user, False, True, now)
        assert user.email_opt_out_date == now

    def test_unchanged_pref_leaves_dates(self):
        user = User()
        user.email_opt_in_date = datetime(2020, 1, 1, tzinfo=timezone.utc)
        _apply_email_pref_timestamps(user, True, True, datetime.now(timezone.utc))
        assert user.email_opt_in_date.year == 2020


class TestProfileInfoValidator:
    def test_valid_email_opt_in_payload(self):
        from routes.validators.profile_info_validator import ProfileInfoValidator

        data = {
            "email": "user@example.com",
            "phone_number": None,
            "email_pref": True,
            "text_pref": False,
            "text_consent": False,
            "prob_pref": 3,
        }
        v = ProfileInfoValidator(data)
        assert v.validate() is True
        assert v.errors == []

    def test_payload_without_service_provider_id(self):
        """Frontend no longer sends service_provider_id; must still validate."""
        from routes.validators.profile_info_validator import ProfileInfoValidator

        data = {
            "email": "user@example.com",
            "phone_number": "9195551234",
            "email_pref": True,
            "text_pref": True,
            "text_consent": True,
            "prob_pref": 4,
        }
        v = ProfileInfoValidator(data)
        assert v.validate() is True

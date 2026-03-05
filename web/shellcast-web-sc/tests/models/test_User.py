"""
Test the User model using pytest with SQLite.
Tests model creation, validation, relationships, and methods.
"""

from datetime import datetime, timezone

from models.User import User


class TestUserModel:
    """Test cases for the User model."""

    def test_user_creation(self, db_session):
        """Test basic user creation."""
        user = User(
            firebase_uid="test_uid_123",
            email="test@example.com",
            phone_number="1234567890",
        )

        db_session.add(user)
        db_session.commit()

        # Check user was created
        assert user.id is not None
        assert user.firebase_uid == "test_uid_123"
        assert user.email == "test@example.com"
        assert user.phone_number == "1234567890"

        # Check default values
        assert user.email_pref == User.DEFAULT_email_pref
        assert user.text_pref == User.DEFAULT_text_pref
        assert user.prob_pref == User.DEFAULT_prob_pref
        assert user.email_consent == User.DEFAULT_email_consent
        assert user.text_consent == User.DEFAULT_text_consent
        assert user.deleted is False

    def test_user_defaults(self, db_session):
        """Test that user defaults are set correctly."""
        user = User(firebase_uid="test_uid_456", email="test2@example.com")

        db_session.add(user)
        db_session.commit()

        # Verify defaults
        assert user.email_pref is False
        assert user.text_pref is False
        assert user.prob_pref == User.DEFAULT_prob_pref  # 75 for SC
        assert user.email_consent is False
        assert user.text_consent is False
        assert user.deleted is False
        assert user.email_opt_in_date is None
        assert user.text_opt_in_date is None
        assert user.email_opt_out_date is None
        assert user.text_opt_out_date is None

    def test_user_consent_management(self, db_session):
        """Test email consent management."""
        user = User(
            firebase_uid="test_uid_789",
            email="consent@example.com",
            email_consent=True,
            email_pref=True,
        )

        db_session.add(user)
        db_session.commit()

        # Test opt-in
        user.email_opt_in_date = datetime.now(timezone.utc)
        db_session.commit()

        assert user.email_consent is True
        assert user.email_pref is True
        assert user.email_opt_in_date is not None

        # Test opt-out
        user.email_consent = False
        user.email_pref = False
        user.email_opt_out_date = datetime.now(timezone.utc)
        db_session.commit()

        assert user.email_consent is False
        assert user.email_pref is False
        assert user.email_opt_out_date is not None

    def test_user_soft_delete(self, db_session):
        """Test soft delete functionality."""
        user = User(firebase_uid="test_uid_delete", email="delete@example.com")

        db_session.add(user)
        db_session.commit()

        user_id = user.id

        # Soft delete
        user.deleted = True
        db_session.commit()

        # User should still exist in database but marked as deleted
        deleted_user = db_session.query(User).filter_by(id=user_id).first()
        assert deleted_user is not None
        assert deleted_user.deleted is True

        # Query without deleted filter should not find the user
        active_user = (
            db_session.query(User).filter_by(deleted=False, id=user_id).first()
        )
        assert active_user is None

    def test_user_phone_number_validation(self, db_session):
        """Test phone number handling."""
        # Test with valid phone number
        user1 = User(
            firebase_uid="test_uid_phone1",
            email="phone1@example.com",
            phone_number="1234567890",
        )

        # Test with no phone number
        user2 = User(firebase_uid="test_uid_phone2", email="phone2@example.com")

        db_session.add_all([user1, user2])
        db_session.commit()

        assert user1.phone_number == "1234567890"
        assert user2.phone_number is None

    def test_user_probability_preference(self, db_session):
        """Test probability preference handling."""
        user = User(firebase_uid="test_uid_prob", email="prob@example.com", prob_pref=5)

        db_session.add(user)
        db_session.commit()

        assert user.prob_pref == 5

        # Test changing preference
        user.prob_pref = 4
        db_session.commit()

        updated_user = db_session.query(User).filter_by(id=user.id).first()
        assert updated_user.prob_pref == 4

    def test_user_timestamps(self, db_session):
        """Test that timestamps are set correctly."""
        user = User(firebase_uid="test_uid_time", email="time@example.com")

        db_session.add(user)
        db_session.commit()

        # Check created timestamp
        assert user.created is not None
        assert isinstance(user.created, datetime)

        # Check updated timestamp
        assert user.updated is not None
        assert isinstance(user.updated, datetime)

        # Update user and check updated timestamp changes
        original_updated = user.updated
        user.email = "updated@example.com"
        db_session.commit()

        # Refresh the user object to get updated timestamp
        db_session.refresh(user)
        assert user.updated >= original_updated

    def test_user_as_dict_method(self, db_session):
        """Test the asDict method."""
        user = User(
            firebase_uid="test_uid_dict",
            email="dict@example.com",
            phone_number="9876543210",
            email_pref=True,
            text_pref=False,
            prob_pref=4,
            email_consent=True,
            text_consent=False,
        )

        db_session.add(user)
        db_session.commit()

        user_dict = user.as_dict()

        # Check all expected fields
        assert user_dict["firebase_uid"] == "test_uid_dict"
        assert user_dict["email"] == "dict@example.com"
        assert user_dict["phone_number"] == "9876543210"
        assert user_dict["email_pref"] is True
        assert user_dict["text_pref"] is False
        assert user_dict["prob_pref"] == 4  # custom override
        assert user_dict["email_consent"] is True
        assert user_dict["text_consent"] is False
        assert user_dict["email_verification_sent"] is False
        assert user_dict["text_verification_sent"] is False

    def test_user_relationships(self, db_session):
        """Test that user relationships are set up correctly."""
        user = User(firebase_uid="test_uid_rel", email="rel@example.com")

        db_session.add(user)
        db_session.commit()

        # Check that relationships are accessible (even if empty)
        assert hasattr(user, "leases")
        assert len(user.leases) == 0

    def test_user_repr_method(self, db_session):
        """Test the __repr__ method."""
        user = User(firebase_uid="test_uid_repr", email="repr@example.com")

        db_session.add(user)
        db_session.commit()

        # Test string representation
        user_repr = repr(user)
        assert "User:" in user_repr
        assert "repr@example.com" in user_repr

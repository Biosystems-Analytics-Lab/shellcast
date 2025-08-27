"""
Test fixtures for ShellCast (Django-style).
Provides consistent test data across all tests.
"""

from datetime import datetime, timezone
from models.User import User
from models.Lease import Lease
from models.Notification import Notification


class UserFixtures:
    """Fixtures for User model testing."""
    
    @staticmethod
    def create_user(**overrides):
        """Create a user with default values (like Django's factories)."""
        defaults = {
            'firebase_uid': 'test_uid_123',
            'email': 'test@example.com',
            'phone_number': '1234567890',
            'email_consent': False,
            'email_pref': False,
            'text_consent': False,
            'text_pref': False,
            'prob_pref': 3,
            'deleted': False
        }
        defaults.update(overrides)
        return User(**defaults)
    
    @staticmethod
    def create_active_user(**overrides):
        """Create an active user with email consent."""
        return UserFixtures.create_user(
            email_consent=True,
            email_pref=True,
            **overrides
        )
    
    @staticmethod
    def create_deleted_user(**overrides):
        """Create a deleted user."""
        return UserFixtures.create_user(
            deleted=True,
            **overrides
        )
    
    @staticmethod
    def create_users_batch(count=5, **base_overrides):
        """Create multiple users (like Django's bulk_create)."""
        users = []
        for i in range(count):
            user_data = {
                'firebase_uid': f'test_uid_{i}',
                'email': f'test{i}@example.com',
                **base_overrides
            }
            users.append(UserFixtures.create_user(**user_data))
        return users


class LeaseFixtures:
    """Fixtures for Lease model testing."""
    
    @staticmethod
    def create_lease(**overrides):
        """Create a lease with default values."""
        defaults = {
            'lease_id': 'TEST-001',
            'grow_area_name': 'GA1',
            'grow_area_desc': 'Test Grow Area',
            'cmu_name': 'TEST-CMU',
            'rainfall_thresh_in': 2.5,
            'latitude': 35.0,
            'longitude': -80.0
        }
        defaults.update(overrides)
        return Lease(**defaults)
    
    @staticmethod
    def create_leases_batch(count=3, **base_overrides):
        """Create multiple leases."""
        leases = []
        for i in range(count):
            lease_data = {
                'lease_id': f'TEST-{i:03d}',
                'grow_area_name': f'GA{i}',
                'grow_area_desc': f'Test Grow Area {i}',
                'cmu_name': f'TEST-CMU-{i}',
                **base_overrides
            }
            leases.append(LeaseFixtures.create_lease(**lease_data))
        return leases


class NotificationFixtures:
    """Fixtures for Notification model testing."""
    
    @staticmethod
    def create_notification(**overrides):
        """Create a notification with default values."""
        defaults = {
            'user_id': 1,
            'address': 'test@example.com',
            'notification_text': 'Test notification message',
            'notification_type': 'email',
            'send_success': True
        }
        defaults.update(overrides)
        return Notification(**defaults)


class TestDataSets:
    """Complete test data sets for integration testing."""
    
    @staticmethod
    def basic_user_setup():
        """Basic setup with one user."""
        return {
            'users': [
                UserFixtures.create_user()
            ]
        }
    
    @staticmethod
    def multiple_users_setup():
        """Setup with multiple users."""
        return {
            'users': UserFixtures.create_users_batch(3)
        }
    
    @staticmethod
    def user_with_leases_setup():
        """Setup with user and associated leases."""
        user = UserFixtures.create_active_user()
        leases = LeaseFixtures.create_leases_batch(2)
        
        return {
            'users': [user],
            'leases': leases
        }
    
    @staticmethod
    def complex_setup():
        """Complex setup with users, leases, and notifications."""
        users = UserFixtures.create_users_batch(3)
        leases = LeaseFixtures.create_leases_batch(2)
        
        # Note: user_id will be set after users are committed to database
        # This is just a template - the actual user_id should be set in the test
        notifications = [
            NotificationFixtures.create_notification(user_id=1),  # Placeholder
            NotificationFixtures.create_notification(user_id=2)   # Placeholder
        ]
        
        return {
            'users': users,
            'leases': leases,
            'notifications': notifications
        }


# Convenience functions for common test scenarios
def create_test_user(**kwargs):
    """Quick way to create a test user."""
    return UserFixtures.create_user(**kwargs)


def create_test_users(count=3, **kwargs):
    """Quick way to create multiple test users."""
    return UserFixtures.create_users_batch(count, **kwargs)


def create_test_lease(**kwargs):
    """Quick way to create a test lease."""
    return LeaseFixtures.create_lease(**kwargs)


def create_test_notification(**kwargs):
    """Quick way to create a test notification."""
    return NotificationFixtures.create_notification(**kwargs)

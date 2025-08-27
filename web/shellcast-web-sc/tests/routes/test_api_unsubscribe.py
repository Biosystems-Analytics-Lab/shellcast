"""
Test the unsubscribe API endpoint using pytest.
Clean, modern testing approach with SQLite.
"""

import pytest
from datetime import datetime, timezone
from models.User import User


class TestUnsubscribeAPI:
    """Test cases for the unsubscribe API endpoint."""
    
    def test_unsubscribe_page_loads_with_valid_params(self, client):
        """Test that unsubscribe page loads with valid parameters."""
        response = client.get('/unsubscribe?email=test@example.com&token=test_token_123')
        
        assert response.status_code == 200
        assert b'Email Unsubscription' in response.data
        assert b'Are you sure you want to unsubscribe?' in response.data
    
    def test_unsubscribe_page_loads_with_invalid_params(self, client):
        """Test that unsubscribe page loads with default content for invalid parameters."""
        response = client.get('/unsubscribe')
        
        assert response.status_code == 200
        # Since JavaScript doesn't run in tests, the page shows default content
        # In a real browser, JavaScript would validate and show "Invalid Unsubscribe Link"
        assert b'Email Unsubscription' in response.data
        assert b'Are you sure you want to unsubscribe?' in response.data
    
    def test_unsubscribe_api_success(self, client, db_session):
        """Test successful unsubscription via API."""
        # Create a test user
        user = User(
            firebase_uid="test_uid_123",
            email="test@example.com",
            email_consent=True,
            email_pref=True,
            text_consent=False,
            text_pref=False,
            prob_pref=3
        )
        db_session.add(user)
        db_session.commit()
        
        # Test unsubscription
        response = client.post('/unsubscribe', 
                             json={'email': 'test@example.com', 'token': 'test_token_123'})
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'message' in data
        assert data['email'] == 'test@example.com'
        assert 'unsubscribed_at' in data
        
        # Verify database was updated
        updated_user = User.query.filter_by(email='test@example.com').first()
        assert updated_user.email_consent == False
        assert updated_user.email_pref == False
        assert updated_user.email_opt_out_date is not None
    
    def test_unsubscribe_api_missing_email(self, client):
        """Test API error when email is missing."""
        response = client.post('/unsubscribe', 
                             json={'token': 'test_token_123'})
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'errors' in data
        assert 'Email and token are required.' in data['errors']
    
    def test_unsubscribe_api_missing_token(self, client):
        """Test API error when token is missing."""
        response = client.post('/unsubscribe', 
                             json={'email': 'test@example.com'})
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'errors' in data
        assert 'Email and token are required.' in data['errors']
    
    def test_unsubscribe_api_user_not_found(self, client):
        """Test API error when user doesn't exist."""
        response = client.post('/unsubscribe', 
                             json={'email': 'nonexistent@example.com', 'token': 'test_token_123'})
        
        assert response.status_code == 404
        data = response.get_json()
        assert 'errors' in data
        assert 'User not found.' in data['errors']
    
    def test_unsubscribe_api_deleted_user(self, client, db_session):
        """Test API error when user is deleted."""
        # Create and mark user as deleted
        user = User(
            firebase_uid="test_uid_456",
            email="deleted@example.com",
            email_consent=True,
            email_pref=True,
            deleted=True
        )
        db_session.add(user)
        db_session.commit()
        
        response = client.post('/unsubscribe', 
                             json={'email': 'deleted@example.com', 'token': 'test_token_123'})
        
        assert response.status_code == 404
        data = response.get_json()
        assert 'errors' in data
        assert 'User not found.' in data['errors']
    
    def test_unsubscribe_api_updates_all_fields(self, client, db_session):
        """Test that all relevant fields are updated on unsubscription."""
        # Create test user
        user = User(
            firebase_uid="test_uid_789",
            email="test_fields@example.com",
            email_consent=True,
            email_pref=True,
            text_consent=False,
            text_pref=False,
            prob_pref=3
        )
        db_session.add(user)
        db_session.commit()
        
        # Verify initial state
        user = User.query.filter_by(email='test_fields@example.com').first()
        assert user.email_consent == True
        assert user.email_pref == True
        assert user.email_opt_out_date is None
        
        # Perform unsubscription
        response = client.post('/unsubscribe', 
                             json={'email': 'test_fields@example.com', 'token': 'test_token_123'})
        
        assert response.status_code == 200
        
        # Verify all fields were updated
        updated_user = User.query.filter_by(email='test_fields@example.com').first()
        assert updated_user.email_consent == False
        assert updated_user.email_pref == False
        assert updated_user.email_opt_out_date is not None
        
        # Check that opt_out_date is recent (within last minute)
        # Convert to timezone-aware datetime for comparison
        current_time = datetime.now(timezone.utc)
        if updated_user.email_opt_out_date.tzinfo is None:
            # If email_opt_out_date is naive, assume it's UTC
            opt_out_time = updated_user.email_opt_out_date.replace(tzinfo=timezone.utc)
        else:
            opt_out_time = updated_user.email_opt_out_date
            
        time_diff = current_time - opt_out_time
        assert time_diff.total_seconds() < 60

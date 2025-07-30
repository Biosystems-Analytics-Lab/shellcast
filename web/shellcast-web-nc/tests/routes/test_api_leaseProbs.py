import pytest

from models.User import User
from models.UserLease import UserLease
from models.Lease import Lease
from models.CMUProbability import CMUProbability

from firebase_admin import auth

def test_valid_lease_probs(client, dbSession, addMockFbUser):
    """
    Test the /leaseProbs route with valid data.
    This test demonstrates how to test Flask API routes:
    1. Set up test data in the database
    2. Make HTTP requests to the API
    3. Assert the response status and content
    """
    # Step 1: Set up authentication - add a mock Firebase user
    addMockFbUser(dict(uid='3sH9so5Y3DP72QA1XqbWw9J6I8o1', email='blah@gmail.com', phone_number='11234567890'), 'validUser1')

    # Step 2: Create a user in the database
    user = User(firebase_uid='3sH9so5Y3DP72QA1XqbWw9J6I8o1', email='blah@gmail.com', phone_number='11234567890')
    dbSession.add(user)
    dbSession.commit()

    # Step 3: Create Lease records (these are the actual lease definitions)
    leases = [
        Lease(
            lease_id='45678',
            grow_area_name='A01',
            grow_area_desc='Test Area 1',
            cmu_name='U001',
            rainfall_thresh_in=1.5,
            latitude=34.404497,
            longitude=-77.567573
        ),
        Lease(
            lease_id='12345',
            grow_area_name='B02',
            grow_area_desc='Test Area 2',
            cmu_name='U002',
            rainfall_thresh_in=2.5,
            latitude=35.207332,
            longitude=-76.523872
        ),
        Lease(
            lease_id='82945',
            grow_area_name='C01',
            grow_area_desc='Test Area 3',
            cmu_name='U003',
            rainfall_thresh_in=1.5,
            latitude=36.164344,
            longitude=-75.927864
        )
    ]
    dbSession.add_all(leases)
    dbSession.commit()

    # Step 4: Create UserLease records (these link users to leases)
    user_leases = [
        UserLease(user_id=user.id, lease_id='45678'),
        UserLease(user_id=user.id, lease_id='12345'),
        UserLease(user_id=user.id, lease_id='82945')
    ]
    dbSession.add_all(user_leases)
    dbSession.commit()

    # Step 5: Create CMUProbability records (these contain the probability data)
    probabilities = [
        CMUProbability(cmu_name='U001', prob_1d_perc=60, prob_2d_perc=70, prob_3d_perc=80),
        CMUProbability(cmu_name='U002', prob_1d_perc=45, prob_2d_perc=54, prob_3d_perc=57),
        CMUProbability(cmu_name='U003', prob_1d_perc=32, prob_2d_perc=33, prob_3d_perc=69)
    ]
    dbSession.add_all(probabilities)
    dbSession.commit()

    # Step 6: Make the API request
    # The 'client' is a Flask test client that simulates HTTP requests
    # 'headers={'Authorization': 'validUser1'}' simulates the authentication token
    res = client.get('/leaseProbs', headers={'Authorization': 'validUser1'})
    
    # Step 7: Assert the response
    assert res.status_code == 200  # Check that the request was successful

    # Step 8: Parse and validate the JSON response
    json = res.get_json()
    assert len(json) == 3  # Should return 3 lease probabilities

    # Step 9: Validate each lease probability entry
    # The API should return: lease_id, latitude, longitude, and probability fields
    assert json[0]['lease_id'] == '45678'
    assert json[0]['latitude'] == 34.404497
    assert json[0]['longitude'] == -77.567573
    assert json[0]['prob_1d_perc'] == 60
    assert json[0]['prob_2d_perc'] == 70
    assert json[0]['prob_3d_perc'] == 80

    assert json[1]['lease_id'] == '12345'
    assert json[1]['latitude'] == 35.207332
    assert json[1]['longitude'] == -76.523872
    assert json[1]['prob_1d_perc'] == 45
    assert json[1]['prob_2d_perc'] == 54
    assert json[1]['prob_3d_perc'] == 57

    assert json[2]['lease_id'] == '82945'
    assert json[2]['latitude'] == 36.164344
    assert json[2]['longitude'] == -75.927864
    assert json[2]['prob_1d_perc'] == 32
    assert json[2]['prob_2d_perc'] == 33
    assert json[2]['prob_3d_perc'] == 69

def test_no_probabilities(client, dbSession, addMockFbUser):
    """
    Test the /leaseProbs route when some leases don't have probability data.
    This tests the case where getLatestProbability() returns None.
    """
    # Set up authentication and user
    addMockFbUser(dict(uid='3sH9so5Y3DP72QA1XqbWw9J6I8o1', email='blah@gmail.com', phone_number='11234567890'), 'validUser1')
    user = User(firebase_uid='3sH9so5Y3DP72QA1XqbWw9J6I8o1', email='blah@gmail.com', phone_number='11234567890')
    dbSession.add(user)
    dbSession.commit()

    # Create leases
    leases = [
        Lease(
            lease_id='45678',
            grow_area_name='A01',
            grow_area_desc='Test Area 1',
            cmu_name='U001',
            rainfall_thresh_in=1.5,
            latitude=34.404497,
            longitude=-77.567573
        ),
        Lease(
            lease_id='12345',
            grow_area_name='B02',
            grow_area_desc='Test Area 2',
            cmu_name='U002',
            rainfall_thresh_in=2.5,
            latitude=35.207332,
            longitude=-76.523872
        ),
        Lease(
            lease_id='82945',
            grow_area_name='C01',
            grow_area_desc='Test Area 3',
            cmu_name='U003',
            rainfall_thresh_in=1.5,
            latitude=36.164344,
            longitude=-75.927864
        )
    ]
    dbSession.add_all(leases)
    dbSession.commit()

    # Create user leases
    user_leases = [
        UserLease(user_id=user.id, lease_id='45678'),
        UserLease(user_id=user.id, lease_id='12345'),
        UserLease(user_id=user.id, lease_id='82945')
    ]
    dbSession.add_all(user_leases)
    dbSession.commit()

    # Only add probability for one CMU (U002)
    lease1Prob = CMUProbability(cmu_name='U002', prob_1d_perc=45, prob_2d_perc=54, prob_3d_perc=57)
    dbSession.add(lease1Prob)
    dbSession.commit()

    # Make the API request
    res = client.get('/leaseProbs', headers={'Authorization': 'validUser1'})
    assert res.status_code == 200

    # Validate response
    json = res.get_json()
    assert len(json) == 3

    # First lease (U001) should have no probability data
    assert json[0]['lease_id'] == '45678'
    assert json[0]['latitude'] == 34.404497
    assert json[0]['longitude'] == -77.567573
    assert 'prob_1d_perc' not in json[0]  # No probability fields should be present
    assert 'prob_2d_perc' not in json[0]
    assert 'prob_3d_perc' not in json[0]

    # Second lease (U002) should have probability data
    assert json[1]['lease_id'] == '12345'
    assert json[1]['latitude'] == 35.207332
    assert json[1]['longitude'] == -76.523872
    assert json[1]['prob_1d_perc'] == 45
    assert json[1]['prob_2d_perc'] == 54
    assert json[1]['prob_3d_perc'] == 57

    # Third lease (U003) should have no probability data
    assert json[2]['lease_id'] == '82945'
    assert json[2]['latitude'] == 36.164344
    assert json[2]['longitude'] == -75.927864
    assert 'prob_1d_perc' not in json[2]
    assert 'prob_2d_perc' not in json[2]
    assert 'prob_3d_perc' not in json[2]

def test_no_leases(client, dbSession, addMockFbUser):
    """
    Test the /leaseProbs route when user has no leases.
    """
    # Set up authentication and user
    addMockFbUser(dict(uid='3sH9so5Y3DP72QA1XqbWw9J6I8o1', email='blah@gmail.com', phone_number='11234567890'), 'validUser1')
    user = User(firebase_uid='3sH9so5Y3DP72QA1XqbWw9J6I8o1', email='blah@gmail.com', phone_number='11234567890')
    dbSession.add(user)
    dbSession.commit()

    # Make the API request
    res = client.get('/leaseProbs', headers={'Authorization': 'validUser1'})
    assert res.status_code == 200

    # Validate response - should be empty list
    json = res.get_json()
    assert len(json) == 0

def test_unauthorized_access(client, dbSession):
    """
    Test the /leaseProbs route without authentication.
    This demonstrates testing error cases.
    """
    # Make the API request without authentication header
    res = client.get('/leaseProbs')
    
    # Should return 401 Unauthorized
    assert res.status_code == 401

def test_deleted_leases_not_returned(client, dbSession, addMockFbUser):
    """
    Test that deleted leases are not returned by the /leaseProbs route.
    """
    # Set up authentication and user
    addMockFbUser(dict(uid='3sH9so5Y3DP72QA1XqbWw9J6I8o1', email='blah@gmail.com', phone_number='11234567890'), 'validUser1')
    user = User(firebase_uid='3sH9so5Y3DP72QA1XqbWw9J6I8o1', email='blah@gmail.com', phone_number='11234567890')
    dbSession.add(user)
    dbSession.commit()

    # Create a lease
    lease = Lease(
        lease_id='45678',
        grow_area_name='A01',
        grow_area_desc='Test Area 1',
        cmu_name='U001',
        rainfall_thresh_in=1.5,
        latitude=34.404497,
        longitude=-77.567573
    )
    dbSession.add(lease)
    dbSession.commit()

    # Create a user lease that is marked as deleted
    user_lease = UserLease(user_id=user.id, lease_id='45678', deleted=True)
    dbSession.add(user_lease)
    dbSession.commit()

    # Make the API request
    res = client.get('/leaseProbs', headers={'Authorization': 'validUser1'})
    assert res.status_code == 200

    # Validate response - should be empty because the lease is deleted
    json = res.get_json()
    assert len(json) == 0

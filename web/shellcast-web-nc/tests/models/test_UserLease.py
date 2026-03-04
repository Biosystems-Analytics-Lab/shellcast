from models.CMUProbability import CMUProbability
from models.Lease import Lease
from models.User import User
from models.UserLease import UserLease


def test_valid(db_session):
    # add the user to the db
    user = User(firebase_uid="3sH9so5Y3DP72QA1XqbWw9J6I8o1", email="blah@gmail.com")
    db_session.add(user)
    db_session.commit()

    lease = Lease(
        lease_id="45678",
        grow_area_name="A01",
        grow_area_desc="Test area",
        cmu_name="U001",
        rainfall_thresh_in=1.5,
        latitude=35.803644,
        longitude=-75.985285,
    )
    db_session.add(lease)
    db_session.commit()

    validLease1 = UserLease(user_id=user.id, lease_id=lease.lease_id)

    db_session.add(validLease1)
    db_session.commit()

    res = UserLease.query.all()

    assert len(res) == 1
    assert res[0].lease_id == validLease1.lease_id
    assert res[0].leases.grow_area_name == lease.grow_area_name
    assert res[0].leases.grow_area_desc == lease.grow_area_desc
    assert res[0].leases.cmu_name == lease.cmu_name
    assert res[0].leases.rainfall_thresh_in == lease.rainfall_thresh_in
    assert res[0].leases.latitude == lease.latitude
    assert res[0].leases.longitude == lease.longitude
    assert res[0].deleted is False
    # do some checks to make sure that these are no longer stored by UserLease
    assert not hasattr(res[0], "email_pref")
    assert not hasattr(res[0], "text_pref")
    assert not hasattr(res[0], "prob_pref")


def test_getLatestProbability(db_session):
    # add a user and a lease to the db
    user = User(firebase_uid="3sH9so5Y3DP72QA1XqbWw9J6I8o1", email="blah@gmail.com")
    db_session.add(user)
    db_session.commit()

    base_lease = Lease(
        lease_id="45678",
        grow_area_name="A01",
        grow_area_desc="Test area",
        cmu_name="U001",
        rainfall_thresh_in=1.5,
        latitude=35.803644,
        longitude=-75.985285,
    )
    db_session.add(base_lease)
    db_session.commit()

    lease = UserLease(user_id=user.id, lease_id=base_lease.lease_id)
    db_session.add(lease)
    db_session.commit()

    # add a few probabilities for various CMUs
    probs = [
        CMUProbability(cmu_name="U001", prob_1d_perc=60),
        CMUProbability(cmu_name="U002", prob_1d_perc=70),
        CMUProbability(cmu_name="U003", prob_1d_perc=80),
        CMUProbability(cmu_name="U004", prob_1d_perc=90),
    ]
    db_session.add_all(probs)
    db_session.commit()

    # add more recent probabilities for the CMUs
    probs = [
        CMUProbability(cmu_name="U001", prob_1d_perc=1),
        CMUProbability(cmu_name="U002", prob_1d_perc=2),
        CMUProbability(cmu_name="U003", prob_1d_perc=3),
        CMUProbability(cmu_name="U004", prob_1d_perc=4),
    ]
    db_session.add_all(probs)
    db_session.commit()

    assert lease.getLatestProbability().prob_1d_perc == 1


def test_as_dict():
    base_lease = Lease(
        lease_id="45678",
        grow_area_name="A01",
        grow_area_desc="Test area",
        cmu_name="U001",
        rainfall_thresh_in=1.5,
        latitude=35.803644,
        longitude=-75.985285,
    )

    lease = UserLease(user_id=1, lease_id=base_lease.lease_id, deleted=False)
    lease.leases = base_lease

    dict_form = lease.as_dict()

    assert dict_form["lease_id"] == lease.lease_id
    assert dict_form["grow_area_name"] == base_lease.grow_area_name
    assert dict_form["grow_area_desc"] == base_lease.grow_area_desc
    assert dict_form["cmu_name"] == base_lease.cmu_name
    assert dict_form["rainfall_thresh_in"] == base_lease.rainfall_thresh_in
    assert dict_form["latitude"] == base_lease.latitude
    assert dict_form["longitude"] == base_lease.longitude
    assert dict_form["deleted"] is False
    # do some checks to make sure that these are no longer stored by UserLease
    assert dict_form.get("email_pref") is None
    assert dict_form.get("text_pref") is None
    assert dict_form.get("prob_pref") is None


def test_repr():
    base_lease = Lease(
        lease_id="45678",
        grow_area_name="A01",
        grow_area_desc="Test area",
        cmu_name="U001",
        rainfall_thresh_in=1.5,
        latitude=35.803644,
        longitude=-75.985285,
    )

    lease = UserLease(user_id=9, lease_id=base_lease.lease_id)
    lease.leases = base_lease

    string_form = repr(lease)

    assert "UserLease" in string_form
    assert str(lease.user_id) in string_form
    assert lease.lease_id in string_form
    assert base_lease.grow_area_name in string_form
    assert base_lease.grow_area_desc in string_form
    assert base_lease.cmu_name in string_form

"""Tests for /leases route (GET, POST, DELETE)."""

from models.Lease import Lease
from models.User import User
from models.UserLease import UserLease


def test_get_leases(client, db_session, add_mock_fb_user):
    """GET /leases returns user's non-deleted leases."""
    add_mock_fb_user(
        dict(uid="uid1", email="u1@example.com", phone_number="15551234567"),
        "token1",
    )
    user = User(
        firebase_uid="uid1",
        email="u1@example.com",
        phone_number="15551234567",
    )
    db_session.add(user)
    db_session.commit()

    lease1 = Lease(
        lease_id="L001",
        grow_area_name="A01",
        grow_area_desc="Area 1",
        cmu_name="U001",
        rainfall_thresh_in=1.5,
    )
    lease2 = Lease(
        lease_id="L002",
        grow_area_name="B02",
        grow_area_desc="Area 2",
        cmu_name="U002",
        rainfall_thresh_in=2.5,
    )
    db_session.add_all([lease1, lease2])
    db_session.commit()

    db_session.add_all(
        [
            UserLease(user_id=user.id, lease_id="L001"),
            UserLease(user_id=user.id, lease_id="L002"),
        ]
    )
    db_session.commit()

    res = client.get("/leases", headers={"Authorization": "token1"})
    assert res.status_code == 200
    data = res.get_json()
    assert len(data) == 2
    by_id = {d["lease_id"]: d for d in data}
    assert by_id["L001"]["grow_area_name"] == "A01"
    assert by_id["L001"]["grow_area_desc"] == "Area 1"
    assert by_id["L001"]["cmu_name"] == "U001"
    assert by_id["L001"]["rainfall_thresh_in"] == 1.5
    assert by_id["L002"]["grow_area_name"] == "B02"
    assert by_id["L002"]["rainfall_thresh_in"] == 2.5


def test_get_leases_empty(client, db_session, add_mock_fb_user):
    """GET /leases with no leases returns empty list."""
    add_mock_fb_user(dict(uid="uid1", email="u1@example.com"), "token1")
    user = User(firebase_uid="uid1", email="u1@example.com")
    db_session.add(user)
    db_session.commit()

    res = client.get("/leases", headers={"Authorization": "token1"})
    assert res.status_code == 200
    assert res.get_json() == []


def test_post_leases_add(client, db_session, add_mock_fb_user):
    """POST /leases with valid lease_id adds lease for user."""
    add_mock_fb_user(dict(uid="uid1", email="u1@example.com"), "token1")
    user = User(firebase_uid="uid1", email="u1@example.com")
    db_session.add(user)
    db_session.commit()

    lease = Lease(
        lease_id="L999",
        grow_area_name="X99",
        grow_area_desc="Test",
        cmu_name="U001",
        rainfall_thresh_in=1.0,
    )
    db_session.add(lease)
    db_session.commit()

    res = client.post(
        "/leases",
        headers={"Authorization": "token1"},
        json={"lease_id": "L999"},
    )
    assert res.status_code == 200
    data = res.get_json()
    assert data["lease_id"] == "L999"
    assert data["grow_area_name"] == "X99"
    assert data["cmu_name"] == "U001"

    res2 = client.get("/leases", headers={"Authorization": "token1"})
    assert len(res2.get_json()) == 1
    assert res2.get_json()[0]["lease_id"] == "L999"


def test_post_leases_invalid_lease_id(client, db_session, add_mock_fb_user):
    """POST /leases with nonexistent lease_id returns 400."""
    add_mock_fb_user(dict(uid="uid1", email="u1@example.com"), "token1")
    user = User(firebase_uid="uid1", email="u1@example.com")
    db_session.add(user)
    db_session.commit()

    res = client.post(
        "/leases",
        headers={"Authorization": "token1"},
        json={"lease_id": "NONEXISTENT"},
    )
    assert res.status_code == 400
    assert "errors" in res.get_json()


def test_delete_leases(client, db_session, add_mock_fb_user):
    """DELETE /leases soft-deletes user lease."""
    add_mock_fb_user(dict(uid="uid1", email="u1@example.com"), "token1")
    user = User(firebase_uid="uid1", email="u1@example.com")
    db_session.add(user)
    db_session.commit()
    lease = Lease(
        lease_id="L001",
        grow_area_name="A01",
        grow_area_desc="A",
        cmu_name="U001",
    )
    db_session.add(lease)
    db_session.commit()
    user_lease = UserLease(user_id=user.id, lease_id="L001")
    db_session.add(user_lease)
    db_session.commit()

    res = client.delete(
        "/leases",
        headers={"Authorization": "token1"},
        json={"lease_id": "L001"},
    )
    assert res.status_code == 200

    res2 = client.get("/leases", headers={"Authorization": "token1"})
    assert res2.get_json() == []


def test_delete_leases_nonexistent(client, db_session, add_mock_fb_user):
    """DELETE /leases for lease user does not have returns 400."""
    add_mock_fb_user(dict(uid="uid1", email="u1@example.com"), "token1")
    user = User(firebase_uid="uid1", email="u1@example.com")
    db_session.add(user)
    db_session.commit()

    res = client.delete(
        "/leases",
        headers={"Authorization": "token1"},
        json={"lease_id": "L999"},
    )
    assert res.status_code == 400
    assert "errors" in res.get_json()


def test_leases_unauthorized(client):
    """GET /leases with invalid auth returns 401."""
    res = client.get("/leases", headers={"Authorization": "invalid-token"})
    assert res.status_code == 401

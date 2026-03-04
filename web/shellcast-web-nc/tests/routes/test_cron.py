"""Tests for cron routes: send-bandwidth-message (SMS via Bandwidth).

NotificationEvent is used for logging; PhoneServiceProvider and AWS are removed.
Cron job calls POST /send-bandwidth-message (cron_only).
"""

from unittest.mock import MagicMock, patch

from models.CMUProbability import CMUProbability
from models.Lease import Lease
from models.NotificationEvent import NotificationEvent
from models.User import User
from models.UserLease import UserLease


def _cron_headers():
    """Headers that satisfy cron_only (X-Appengine-Cron)."""
    return {"X-Appengine-Cron": "true"}


def test_send_bandwidth_message_unauthorized_without_cron_header(client):
    """POST /send-bandwidth-message without X-Appengine-Cron returns 401."""
    res = client.post(
        "/send-bandwidth-message", headers={"Content-Type": "application/json"}
    )
    assert res.status_code == 401


def test_send_bandwidth_message_no_users(client, db_session):
    """POST /send-bandwidth-message with no eligible users returns 200 and NC: 0 sent."""
    with patch("routes.cron.requests.post", return_value=MagicMock(status_code=200)):
        res = client.post(
            "/send-bandwidth-message",
            headers=_cron_headers(),
        )
    assert res.status_code == 200
    data = res.get_data(as_text=True)
    assert "NC: 0 sent" in data or "0 sent" in data


def test_send_bandwidth_message_sends_sms_and_logs_event(client, db_session):
    """POST /send-bandwidth-message notifies eligible user and creates NotificationEvent."""
    # User with SMS opted in and phone number
    user = User(
        firebase_uid="uid-cron-1",
        email="shellcastapp@ncsu.edu",
        phone_number="5555555555",
        email_pref=False,
        text_pref=True,
        text_consent=True,
        prob_pref=User.DEFAULT_prob_pref,
    )
    db_session.add(user)
    db_session.commit()

    # Leases for that user
    for lease_id, grow_area, cmu in [
        ("45678", "A01", "U001"),
        ("12345", "B02", "U002"),
    ]:
        lease = Lease(
            lease_id=lease_id,
            grow_area_name=grow_area,
            grow_area_desc="Area",
            cmu_name=cmu,
            latitude=34.4,
            longitude=-77.5,
        )
        db_session.add(lease)
    db_session.commit()

    for lease_id in ("45678", "12345"):
        ul = UserLease(user_id=user.id, lease_id=lease_id, deleted=False)
        db_session.add(ul)
    db_session.commit()

    # Probabilities so at least one lease meets prob_pref
    for cmu, p1, p2, p3 in [("U001", 5, 4, 4), ("U002", 2, 2, 2)]:
        db_session.add(
            CMUProbability(
                cmu_name=cmu, prob_1d_perc=p1, prob_2d_perc=p2, prob_3d_perc=p3
            )
        )
    db_session.commit()

    mock_batch = [
        (user.id, "5555555555", True, "mock-msg-123"),
    ]
    with patch("routes.cron.requests.post", return_value=MagicMock(status_code=200)):
        with patch(
            "routes.cron.send_sms_batch",
            return_value=mock_batch,
        ):
            res = client.post(
                "/send-bandwidth-message",
                headers=_cron_headers(),
            )

    assert res.status_code == 200
    data = res.get_data(as_text=True)
    assert "NC:" in data and "1 sent" in data

    events = db_session.query(NotificationEvent).filter_by(state="NC").all()
    assert len(events) >= 1
    outbound = [e for e in events if e.message_direction == "outbound"]
    assert len(outbound) == 1
    assert outbound[0].user_id == user.id
    assert outbound[0].phone_number == "5555555555"
    assert (
        outbound[0].text_content_template
        == NotificationEvent.TEMPLATE_SMS_CLOSURE_ALERT
    )
    assert outbound[0].send_success is True


def test_send_bandwidth_message_triggers_fl_and_sc(client, db_session):
    """POST /send-bandwidth-message triggers FL and SC send-bandwidth-message URLs."""
    with patch(
        "routes.cron.requests.post", return_value=MagicMock(status_code=200)
    ) as mock_post:
        with patch("routes.cron.send_sms_batch", return_value=[]):
            with patch.dict(
                "os.environ", {"NC_ORCHESTRATOR_SECRET": "test-orchestrator-secret"}
            ):
                res = client.post(
                    "/send-bandwidth-message",
                    headers=_cron_headers(),
                )

    assert res.status_code == 200
    assert mock_post.call_count == 2
    urls = [c[0][0] for c in mock_post.call_args_list]
    assert any("shellcast-fl" in u and "send-bandwidth-message" in u for u in urls)
    assert any("shellcast-sc" in u and "send-bandwidth-message" in u for u in urls)
    for call in mock_post.call_args_list:
        assert call[1]["headers"].get("X-NC-Orchestrator-Secret") is not None


def test_send_bandwidth_message_deleted_users_excluded(client, db_session):
    """Only non-deleted users are considered for notifications."""
    active_user = User(
        firebase_uid="uid-active",
        email="active@ncsu.edu",
        phone_number="15551234567",
        text_pref=True,
        text_consent=True,
        prob_pref=User.DEFAULT_prob_pref,
        deleted=False,
    )
    deleted_user = User(
        firebase_uid="uid-deleted",
        email="deleted@ncsu.edu",
        phone_number="15559999999",
        text_pref=True,
        text_consent=True,
        prob_pref=User.DEFAULT_prob_pref,
        deleted=True,
    )
    db_session.add_all([active_user, deleted_user])
    db_session.commit()

    for lease_id, cmu in [("L001", "U001"), ("L002", "U002")]:
        db_session.add(
            Lease(
                lease_id=lease_id,
                grow_area_name="A01",
                grow_area_desc="Area",
                cmu_name=cmu,
                latitude=34.4,
                longitude=-77.5,
            )
        )
    db_session.commit()
    db_session.add(UserLease(user_id=active_user.id, lease_id="L001", deleted=False))
    db_session.add(UserLease(user_id=deleted_user.id, lease_id="L002", deleted=False))
    db_session.add(
        CMUProbability(cmu_name="U001", prob_1d_perc=5, prob_2d_perc=5, prob_3d_perc=5)
    )
    db_session.add(
        CMUProbability(cmu_name="U002", prob_1d_perc=5, prob_2d_perc=5, prob_3d_perc=5)
    )
    db_session.commit()

    with patch("routes.cron.requests.post", return_value=MagicMock(status_code=200)):
        with patch(
            "routes.cron.send_sms_batch",
            return_value=[(active_user.id, "15551234567", True, "msg-1")],
        ):
            res = client.post(
                "/send-bandwidth-message",
                headers=_cron_headers(),
            )

    assert res.status_code == 200
    events = db_session.query(NotificationEvent).filter_by(state="NC").all()
    assert len(events) == 1
    assert events[0].user_id == active_user.id
    assert events[0].phone_number == "15551234567"

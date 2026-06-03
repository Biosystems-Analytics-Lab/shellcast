"""Tests for SMS STOP/START inbound handling."""

from unittest.mock import MagicMock

from core.notifications.inbound import handle_stop_start


def test_stop_sets_opt_out_and_touch_updated():
    user = MagicMock()
    user.text_pref = True
    user.text_consent = True
    session = MagicMock()
    session.query.return_value.filter_by.return_value.first.return_value = user

    handled = handle_stop_start(
        state="NC",
        db_session=session,
        user_model=MagicMock,
        from_number="+19195551234",
        text="STOP",
        message_id="msg-1",
        log_inbound_fn=lambda *a, **k: None,
        send_opt_out_fn=lambda *a, **k: None,
        send_opt_in_fn=lambda *a, **k: None,
    )

    assert handled is True
    assert user.text_pref is False
    assert user.text_consent is False
    assert user.text_opt_out_date is not None
    user.touch_updated.assert_called_once()
    session.commit.assert_called_once()


def test_start_sets_opt_in_and_touch_updated():
    user = MagicMock()
    user.text_pref = False
    user.text_consent = False
    session = MagicMock()
    session.query.return_value.filter_by.return_value.first.return_value = user

    handled = handle_stop_start(
        state="NC",
        db_session=session,
        user_model=MagicMock,
        from_number="+19195551234",
        text="START",
        message_id="msg-2",
        log_inbound_fn=lambda *a, **k: None,
        send_opt_out_fn=lambda *a, **k: None,
        send_opt_in_fn=lambda *a, **k: None,
    )

    assert handled is True
    assert user.text_pref is True
    assert user.text_consent is True
    assert user.text_opt_in_date is not None
    user.touch_updated.assert_called_once()

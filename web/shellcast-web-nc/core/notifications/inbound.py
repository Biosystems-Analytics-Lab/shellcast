"""Shared STOP/START handling for inbound SMS."""

import logging
from datetime import datetime, timezone
from typing import Callable, Optional, Type

from .phone_utils import clean_inbound_phone, is_start_keyword, is_stop_keyword


def handle_stop_start(
    *,
    state: str,
    db_session,
    user_model: Type,
    from_number: str,
    text: str,
    message_id: Optional[str],
    log_inbound_fn: Callable[[str, int, str, Optional[str]], None],
    send_opt_out_fn: Callable[[str], None],
    send_opt_in_fn: Callable[[str], None],
) -> bool:
    """Handle STOP/START inbound messages in a shared way.

    Returns True if the message was handled as STOP or START, False otherwise.
    """
    logging.info(f"Received SMS from {from_number}: {text}")

    clean_number = clean_inbound_phone(from_number)
    text_upper = text.strip().upper()

    # STOP / opt-out
    if is_stop_keyword(text_upper):
        user = db_session.query(user_model).filter_by(phone_number=clean_number).first()
        if user:
            user.text_pref = False
            user.text_consent = False
            user.text_opt_out_date = datetime.now(timezone.utc)
            db_session.commit()

            log_inbound_fn(state, user.id, clean_number, message_id)
            logging.info(f"{state} User {user.id} opted out of SMS notifications")

            try:
                send_opt_out_fn(from_number)
            except Exception as e:  # pragma: no cover - defensive logging
                logging.error(f"{state}: Failed to send opt-out confirmation: {e}")
        else:
            logging.warning(
                f"{state}: No user found with phone number {clean_number} for opt-out"
            )
        return True

    # START / opt-in
    if is_start_keyword(text_upper):
        user = db_session.query(user_model).filter_by(phone_number=clean_number).first()
        if user:
            user.text_pref = True
            user.text_consent = True
            user.text_opt_in_date = datetime.now(timezone.utc)
            db_session.commit()

            log_inbound_fn(state, user.id, clean_number, message_id)
            logging.info(f"{state} User {user.id} opted in to SMS notifications")

            try:
                send_opt_in_fn(from_number)
            except Exception as e:  # pragma: no cover - defensive logging
                logging.error(f"{state}: Failed to send opt-in confirmation: {e}")
        else:
            logging.warning(
                f"{state}: No user found with phone number {clean_number} for opt-in"
            )
        return True

    # Not STOP or START
    return False

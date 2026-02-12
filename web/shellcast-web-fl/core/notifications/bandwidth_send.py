"""Shared helpers for sending SMS via Bandwidth.

This module focuses only on talking to Bandwidth and returning results.
Logging to NotificationEvent or NC is handled by the caller in each app.
"""

import os
import time
from typing import List, Optional, Sequence, Tuple

import bandwidth


def send_sms_single(
    to_number: str,
    text: str,
    state: str,
) -> Optional[object]:
    """Send one SMS via Bandwidth.

    Args:
        to_number: E.164 or US number to send to.
        text: Message body.
        state: Two-letter tag for callback routing (e.g. 'FL').

    Returns:
        Bandwidth API response on success, None on failure or missing config.
    """
    bw_username = os.getenv("BW_USERNAME")
    bw_password = os.getenv("BW_PASSWORD")
    bw_account_id = os.getenv("BW_ACCOUNT_ID")
    bw_application_id = os.getenv("BW_APPLICATION_ID")
    bw_from_number = os.getenv("BW_NUMBER")
    if not all(
        [bw_username, bw_password, bw_account_id, bw_application_id, bw_from_number]
    ):
        return None
    configuration = bandwidth.Configuration(username=bw_username, password=bw_password)
    with bandwidth.ApiClient(configuration) as api_client:
        messages_api = bandwidth.MessagesApi(api_client)
        message_request = bandwidth.MessageRequest(
            application_id=bw_application_id,
            to=[to_number],
            var_from=bw_from_number,
            text=text,
            tag=state,
        )
        return messages_api.create_message(bw_account_id, message_request)


def send_sms_batch(
    users_to_notify: Sequence[Tuple[int, str]],
    text: str,
    state: str,
    sleep_seconds: float = 0.1,
) -> List[Tuple[int, str, bool, str]]:
    """Send SMS messages to multiple recipients using Bandwidth.

    Args:
        users_to_notify: iterable of (user_id, phone_number) tuples.
        text: SMS body.
        state: two-letter state code used as Bandwidth tag (e.g. 'NC', 'FL', 'SC').
        sleep_seconds: optional delay between sends to avoid rate limiting.

    Returns:
        List of (user_id, phone_number, success, message_id) tuples.
    """
    if not users_to_notify:
        return []

    bw_username = os.getenv("BW_USERNAME")
    bw_password = os.getenv("BW_PASSWORD")
    bw_account_id = os.getenv("BW_ACCOUNT_ID")
    bw_application_id = os.getenv("BW_APPLICATION_ID")
    bw_from_number = os.getenv("BW_NUMBER")

    configuration = bandwidth.Configuration(username=bw_username, password=bw_password)
    results: List[Tuple[int, str, bool, str]] = []

    with bandwidth.ApiClient(configuration) as api_client:
        messages_api = bandwidth.MessagesApi(api_client)

        for user_id, phone_number in users_to_notify:
            try:
                message_request = bandwidth.MessageRequest(
                    application_id=bw_application_id,
                    to=[phone_number],
                    var_from=bw_from_number,
                    text=text,
                    tag=state,
                )
                response = messages_api.create_message(bw_account_id, message_request)
                message_id = response.id if response else None
                results.append((user_id, phone_number, True, message_id))
            except Exception:
                # Caller is responsible for logging the error details.
                results.append((user_id, phone_number, False, None))

            if sleep_seconds > 0:
                time.sleep(sleep_seconds)

    return results

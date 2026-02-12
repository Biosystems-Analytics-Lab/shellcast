"""Helpers for phone number normalization and keyword handling
for SMS notifications.

This module is intended to be identical across NC, FL, and SC apps and
can be copied into each app's ``core/notifications`` package.
"""

from typing import Tuple

# Keywords are uppercase; compare against text_upper
STOP_KEYWORDS: Tuple[str, ...] = ("STOP", "UNSUBSCRIBE", "CANCEL", "END", "QUIT")
START_KEYWORDS: Tuple[str, ...] = ("START", "UNSTOP", "SUBSCRIBE")


def clean_inbound_phone(from_number: str) -> str:
    """Normalize an inbound Bandwidth phone number for DB lookups.

    Current behavior: strip leading +1 (US country code) if present.
    """
    if not from_number:
        return ""
    if from_number.startswith("+1"):
        return from_number[2:]
    return from_number


def is_stop_keyword(text_upper: str) -> bool:
    """Return True if the uppercased inbound text is a STOP keyword."""
    return text_upper in STOP_KEYWORDS


def is_start_keyword(text_upper: str) -> bool:
    """Return True if the uppercased inbound text is a START keyword."""
    return text_upper in START_KEYWORDS

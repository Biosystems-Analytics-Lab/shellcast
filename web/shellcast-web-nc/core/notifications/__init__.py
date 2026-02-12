"""Shared notification utilities for the NC web app.

This package is designed to be copied as-is into FL and SC app roots so
they can import the same helpers with::

    from core.notifications.phone_utils import ...

Only code that is identical across states should live here.
"""

from .bandwidth_send import send_sms_batch  # noqa: F401
from .phone_utils import (  # noqa: F401
    START_KEYWORDS,
    STOP_KEYWORDS,
    clean_inbound_phone,
    is_start_keyword,
    is_stop_keyword,
)

__all__ = [
    "STOP_KEYWORDS",
    "START_KEYWORDS",
    "clean_inbound_phone",
    "is_stop_keyword",
    "is_start_keyword",
    "send_sms_batch",
]

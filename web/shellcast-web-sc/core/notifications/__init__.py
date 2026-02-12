"""Shared notification utilities for the SC web app.

This package is designed to mirror NC's core/notifications so that
all state apps can import the same helpers with::

    from core.notifications.phone_utils import ...
"""

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
]

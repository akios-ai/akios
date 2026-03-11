# Copyright (C) 2025-2026 AKIOUD AI, SAS <contact@akioud.ai>
# SPDX-License-Identifier: GPL-3.0-or-later

"""
Network utilities — single source of truth for connectivity checks.

Previously the same ``socket.create_connection("8.8.8.8", 53)`` pattern was
duplicated in engine.py, tracker.py, and cli/run.py.  Import from here instead.
"""

import socket
import logging

logger = logging.getLogger(__name__)

_DNS_HOST = "8.8.8.8"
_DNS_PORT = 53
_DEFAULT_TIMEOUT = 3  # seconds


def check_network_available(timeout: float = _DEFAULT_TIMEOUT) -> bool:
    """
    Return *True* if the host can reach the public internet.

    Uses a quick TCP SYN to Google Public DNS (8.8.8.8:53) as a lightweight
    reachability probe.  No data is sent — the connection is closed immediately.

    Args:
        timeout: Maximum seconds to wait for a connection.

    Returns:
        ``True`` if the probe succeeded, ``False`` otherwise.
    """
    try:
        conn = socket.create_connection((_DNS_HOST, _DNS_PORT), timeout=timeout)
        conn.close()
        return True
    except (socket.error, OSError):
        return False

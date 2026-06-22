"""
Utility modules for TaskForge
"""

from typing import Any

from .config import Config

AuthManager: Any
try:
    from .auth import AuthManager
except ImportError:
    AuthManager = None

NotificationManager: Any
try:
    from .notifications import NotificationManager
except ImportError:
    NotificationManager = None

__all__ = ["Config", "AuthManager", "NotificationManager"]

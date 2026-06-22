"""Storage package public exports."""

from typing import Any

from .base import StorageBackend

JSONStorage: Any
try:
    from .json_storage import JSONStorage
except ImportError:
    from .simple_json_storage import SimpleJSONStorage as JSONStorage

JsonStorage = JSONStorage

PostgreSQLStorage: Any
try:
    from .postgresql import PostgreSQLStorage
except ImportError:
    try:
        from .simple_postgresql_storage import (
            SimplePostgreSQLStorage as PostgreSQLStorage,
        )
    except ImportError:
        PostgreSQLStorage = None

__all__ = ["StorageBackend", "JSONStorage", "JsonStorage"]

if PostgreSQLStorage is not None:
    __all__.append("PostgreSQLStorage")

"""Storage package initialization"""

from .base import StorageBackend
from .json_storage import JSONStorage
from .json_storage import JSONStorage as JsonStorage

# Optional imports - only load if dependencies are available
try:
    from .postgresql import PostgreSQLStorage

    __all__ = ["StorageBackend", "JsonStorage", "PostgreSQLStorage"]
except ImportError:
    __all__ = ["StorageBackend", "JsonStorage"]

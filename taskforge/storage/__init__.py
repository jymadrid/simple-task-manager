"""Storage package initialization"""

from .base import StorageBackend

# Try to import optimized storage, fallback to simple version
try:
    from .json_storage import JSONStorage
    from .json_storage import JSONStorage as JsonStorage
except ImportError:
    from .simple_json_storage import SimpleJSONStorage as JSONStorage
    from .simple_json_storage import SimpleJSONStorage as JsonStorage

# Optional imports - only load if dependencies are available
try:
    from .postgresql import PostgreSQLStorage

    __all__ = ["StorageBackend", "JsonStorage", "PostgreSQLStorage", "JSONStorage"]
except ImportError:
    __all__ = ["StorageBackend", "JsonStorage", "JSONStorage"]

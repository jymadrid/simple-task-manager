"""Storage package initialization"""

from .base import StorageBackend

# Try to import optimized storage, fallback to simple version
try:
    from .json_storage import JSONStorage
    from .json_storage import JSONStorage as JsonStorage
except ImportError:
    from .simple_json_storage import SimpleJSONStorage as JSONStorage
    from .simple_json_storage import SimpleJSONStorage as JsonStorage

# Initialize __all__
__all__ = ["StorageBackend", "JsonStorage", "JSONStorage"]

# Optional imports - only load if dependencies are available
try:
    from .postgresql import PostgreSQLStorage
    __all__.extend(["PostgreSQLStorage"])
except ImportError:
    try:
        from .simple_postgresql_storage import SimplePostgreSQLStorage as PostgreSQLStorage
        __all__.extend(["PostgreSQLStorage"])
    except ImportError:
        pass

# Optional imports - only load if dependencies are available
__all__ = ["StorageBackend", "JsonStorage", "JSONStorage"]

try:
    from .postgresql import PostgreSQLStorage
    __all__.extend(["PostgreSQLStorage"])
except ImportError:
    try:
        from .simple_postgresql_storage import SimplePostgreSQLStorage as PostgreSQLStorage
        __all__.extend(["PostgreSQLStorage"])
    except ImportError:
        pass

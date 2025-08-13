"""
Configuration management for TaskForge
"""

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional


@dataclass
class DatabaseConfig:
    """Database configuration"""

    type: str = "json"  # json, postgresql, mysql
    url: str = ""
    host: str = "localhost"
    port: int = 5432
    database: str = "taskforge"
    username: str = ""
    password: str = ""
    pool_size: int = 10
    max_overflow: int = 20


@dataclass
class ServerConfig:
    """Server configuration"""

    host: str = "127.0.0.1"
    port: int = 8000
    debug: bool = False
    reload: bool = False
    workers: int = 1
    log_level: str = "info"


@dataclass
class SecurityConfig:
    """Security configuration"""

    secret_key: str = ""
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    password_min_length: int = 8
    max_login_attempts: int = 5
    lockout_duration_minutes: int = 15


@dataclass
class NotificationConfig:
    """Notification configuration"""

    enabled: bool = True
    email_backend: str = "smtp"  # smtp, sendgrid, mailgun
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    smtp_use_tls: bool = True
    from_email: str = ""


@dataclass
class PluginConfig:
    """Plugin configuration"""

    enabled: bool = True
    directories: list = field(
        default_factory=lambda: ["./plugins", "~/.taskforge/plugins"]
    )
    auto_load: list = field(default_factory=list)
    disabled: list = field(default_factory=list)


@dataclass
class Config:
    """Main configuration class"""

    # Basic settings
    debug: bool = False
    data_directory: str = "./data"
    log_level: str = "INFO"
    timezone: str = "UTC"

    # Component configurations
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    server: ServerConfig = field(default_factory=ServerConfig)
    security: SecurityConfig = field(default_factory=SecurityConfig)
    notifications: NotificationConfig = field(default_factory=NotificationConfig)
    plugins: PluginConfig = field(default_factory=PluginConfig)

    # Feature flags
    features: Dict[str, bool] = field(
        default_factory=lambda: {
            "web_interface": True,
            "cli_interface": True,
            "api_interface": True,
            "plugins": True,
            "notifications": True,
            "analytics": True,
            "export_import": True,
        }
    )

    # Custom settings
    custom: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def load(cls, config_file: Optional[str] = None) -> "Config":
        """Load configuration from file and environment variables"""
        config = cls()

        # Try to load from file
        if config_file:
            config_path = Path(config_file)
        else:
            # Look for config files in common locations
            possible_paths = [
                Path("./taskforge.json"),
                Path("./config.json"),
                Path.home() / ".taskforge" / "config.json",
                Path("/etc/taskforge/config.json"),
            ]
            config_path = None
            for path in possible_paths:
                if path.exists():
                    config_path = path
                    break

        if config_path and config_path.exists():
            try:
                with open(config_path, "r") as f:
                    file_config = json.load(f)
                    config._update_from_dict(file_config)
            except (json.JSONDecodeError, IOError) as e:
                print(f"Warning: Could not load config file {config_path}: {e}")

        # Override with environment variables
        config._load_from_env()

        # Validate configuration
        config._validate()

        return config

    def _update_from_dict(self, data: Dict[str, Any]):
        """Update configuration from dictionary"""
        for key, value in data.items():
            if hasattr(self, key):
                attr = getattr(self, key)
                if isinstance(
                    attr,
                    (
                        DatabaseConfig,
                        ServerConfig,
                        SecurityConfig,
                        NotificationConfig,
                        PluginConfig,
                    ),
                ):
                    # Update nested config objects
                    if isinstance(value, dict):
                        for nested_key, nested_value in value.items():
                            if hasattr(attr, nested_key):
                                setattr(attr, nested_key, nested_value)
                else:
                    setattr(self, key, value)

    def _load_from_env(self):
        """Load configuration from environment variables"""
        # Basic settings
        self.debug = os.getenv("TASKFORGE_DEBUG", "false").lower() == "true"
        self.data_directory = os.getenv("TASKFORGE_DATA_DIR", self.data_directory)
        self.log_level = os.getenv("TASKFORGE_LOG_LEVEL", self.log_level)
        self.timezone = os.getenv("TASKFORGE_TIMEZONE", self.timezone)

        # Database configuration
        if os.getenv("DATABASE_URL"):
            self.database.url = os.getenv("DATABASE_URL")
            # Parse database type from URL
            if self.database.url.startswith("postgresql://"):
                self.database.type = "postgresql"
            elif self.database.url.startswith("mysql://"):
                self.database.type = "mysql"

        self.database.type = os.getenv("TASKFORGE_DB_TYPE", self.database.type)
        self.database.host = os.getenv("TASKFORGE_DB_HOST", self.database.host)
        self.database.port = int(
            os.getenv("TASKFORGE_DB_PORT", str(self.database.port))
        )
        self.database.database = os.getenv("TASKFORGE_DB_NAME", self.database.database)
        self.database.username = os.getenv("TASKFORGE_DB_USER", self.database.username)
        self.database.password = os.getenv(
            "TASKFORGE_DB_PASSWORD", self.database.password
        )

        # Server configuration
        self.server.host = os.getenv("TASKFORGE_HOST", self.server.host)
        self.server.port = int(os.getenv("TASKFORGE_PORT", str(self.server.port)))
        self.server.debug = (
            os.getenv("TASKFORGE_SERVER_DEBUG", "false").lower() == "true"
        )
        self.server.workers = int(
            os.getenv("TASKFORGE_WORKERS", str(self.server.workers))
        )

        # Security configuration
        self.security.secret_key = os.getenv(
            "TASKFORGE_SECRET_KEY", self.security.secret_key
        )
        if not self.security.secret_key:
            # Generate a random secret key if not provided
            import secrets

            self.security.secret_key = secrets.token_urlsafe(32)

        # Notification configuration
        self.notifications.smtp_host = os.getenv(
            "SMTP_HOST", self.notifications.smtp_host
        )
        self.notifications.smtp_port = int(
            os.getenv("SMTP_PORT", str(self.notifications.smtp_port))
        )
        self.notifications.smtp_username = os.getenv(
            "SMTP_USERNAME", self.notifications.smtp_username
        )
        self.notifications.smtp_password = os.getenv(
            "SMTP_PASSWORD", self.notifications.smtp_password
        )
        self.notifications.from_email = os.getenv(
            "FROM_EMAIL", self.notifications.from_email
        )

    def _validate(self):
        """Validate configuration"""
        # Ensure data directory exists
        Path(self.data_directory).mkdir(parents=True, exist_ok=True)

        # Validate database configuration
        if self.database.type == "postgresql" and not self.database.url:
            if not all(
                [
                    self.database.host,
                    self.database.database,
                    self.database.username,
                    self.database.password,
                ]
            ):
                raise ValueError("PostgreSQL database configuration is incomplete")

        # Validate server configuration
        if not (1 <= self.server.port <= 65535):
            raise ValueError(f"Invalid server port: {self.server.port}")

        # Validate security configuration
        if len(self.security.secret_key) < 32:
            print("Warning: Secret key is shorter than recommended (32 characters)")

    def save(self, config_file: str):
        """Save configuration to file"""
        config_data = {
            "debug": self.debug,
            "data_directory": self.data_directory,
            "log_level": self.log_level,
            "timezone": self.timezone,
            "database": {
                "type": self.database.type,
                "url": (
                    self.database.url
                    if not any([self.database.username, self.database.password])
                    else ""
                ),  # Don't save credentials in URL
                "host": self.database.host,
                "port": self.database.port,
                "database": self.database.database,
                "pool_size": self.database.pool_size,
                "max_overflow": self.database.max_overflow,
            },
            "server": {
                "host": self.server.host,
                "port": self.server.port,
                "debug": self.server.debug,
                "reload": self.server.reload,
                "workers": self.server.workers,
                "log_level": self.server.log_level,
            },
            "security": {
                "algorithm": self.security.algorithm,
                "access_token_expire_minutes": self.security.access_token_expire_minutes,
                "refresh_token_expire_days": self.security.refresh_token_expire_days,
                "password_min_length": self.security.password_min_length,
                "max_login_attempts": self.security.max_login_attempts,
                "lockout_duration_minutes": self.security.lockout_duration_minutes,
            },
            "notifications": {
                "enabled": self.notifications.enabled,
                "email_backend": self.notifications.email_backend,
                "smtp_host": self.notifications.smtp_host,
                "smtp_port": self.notifications.smtp_port,
                "smtp_use_tls": self.notifications.smtp_use_tls,
                "from_email": self.notifications.from_email,
            },
            "plugins": {
                "enabled": self.plugins.enabled,
                "directories": self.plugins.directories,
                "auto_load": self.plugins.auto_load,
                "disabled": self.plugins.disabled,
            },
            "features": self.features,
            "custom": self.custom,
        }

        config_path = Path(config_file)
        config_path.parent.mkdir(parents=True, exist_ok=True)

        with open(config_path, "w") as f:
            json.dump(config_data, f, indent=2)

    def get_database_url(self) -> str:
        """Get database URL for SQLAlchemy"""
        if self.database.url:
            return self.database.url

        if self.database.type == "postgresql":
            return (
                f"postgresql+asyncpg://{self.database.username}:"
                f"{self.database.password}@{self.database.host}:"
                f"{self.database.port}/{self.database.database}"
            )
        elif self.database.type == "mysql":
            return (
                f"mysql+aiomysql://{self.database.username}:"
                f"{self.database.password}@{self.database.host}:"
                f"{self.database.port}/{self.database.database}"
            )
        else:
            return ""  # JSON storage doesn't need URL

    def is_feature_enabled(self, feature: str) -> bool:
        """Check if a feature is enabled"""
        return self.features.get(feature, False)

import os
from typing import Optional
from .exceptions import ConfigException


class Config:
    """Application configuration manager"""

    @classmethod
    def get(cls, key: str, default: Optional[str] = None) -> str:
        """Get environment variable with optional default"""
        value = os.getenv(key, default)
        if value is None:
            raise ConfigException(f"Required config key not found: {key}")
        return value

    @classmethod
    def get_optional(cls, key: str, default: Optional[str] = None) -> Optional[str]:
        """Get optional environment variable"""
        return os.getenv(key, default)

    @staticmethod
    def azure_storage_account() -> str:
        return os.getenv('AZURE_STORAGE_ACCOUNT', 'devstoreaccount1')

    @staticmethod
    def azure_storage_key() -> str:
        return os.getenv('AZURE_STORAGE_KEY', 'sharedsecretkey1')

    @staticmethod
    def azurite_endpoint() -> str:
        return os.getenv('AZURITE_ENDPOINT', 'http://azurite:10000')

    @staticmethod
    def database_url() -> str:
        return os.getenv('DATABASE_URL', 'postgresql://df_user:postgres@postgres:5432/data_factory')

    @staticmethod
    def spark_endpoint() -> str:
        return os.getenv('SPARK_ENDPOINT', 'http://spark:8888')

    @staticmethod
    def log_level() -> str:
        return os.getenv('LOG_LEVEL', 'INFO')

    @staticmethod
    def api_host() -> str:
        return os.getenv('API_HOST', '0.0.0.0')

    @staticmethod
    def api_port() -> int:
        return int(os.getenv('API_PORT', '5000'))

    @staticmethod
    def environment() -> str:
        return os.getenv('ENVIRONMENT', 'development')

    @staticmethod
    def is_development() -> bool:
        return Config.environment() == 'development'

    @staticmethod
    def is_production() -> bool:
        return Config.environment() == 'production'

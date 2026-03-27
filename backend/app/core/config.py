"""Application settings."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Settings loaded from environment variables."""

    app_name: str = "Missa Perto de Mim API"
    database_url: str = "sqlite:///./missa_perto.db"
    admin_username: str = "admin"
    admin_password_hash: str = "$2b$12$Jr2Yh3Smf8uJY.Bf8exSEut8Y8J9is5d1fQkeH8COjJfUATwaQAHm"
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()

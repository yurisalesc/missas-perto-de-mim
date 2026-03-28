"""Application settings."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Settings loaded from environment variables."""

    app_name: str = "Missa Perto de Mim API"
    app_env: str = "development"
    database_url: str = "sqlite:///./missa_perto.db"
    cors_allowed_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    admin_username: str = "admin"
    admin_password: str | None = None
    admin_password_hash: str | None = None
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    @property
    def cors_allowed_origins_list(self) -> list[str]:
        return [item.strip() for item in self.cors_allowed_origins.split(",") if item.strip()]


settings = Settings()

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import SecretStr


# Настройки приложения из .env и переменных окружения.
class Settings(BaseSettings):
    app_name: str = "Tutor Booking API"
    debug: bool = False
    database_url: SecretStr | None = None
    secret_key: SecretStr = SecretStr("dev-secret-key-change-in-production")
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 1440

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()

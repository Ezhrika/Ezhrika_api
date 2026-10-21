from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import AnyHttpUrl, Field, SecretStr


# Настройки приложения из .env и переменных окружения.
class Settings(BaseSettings):
    app_name: str = "Tutor Booking API"
    debug: bool = False
    database_url: SecretStr | None = None
    secret_key: SecretStr = SecretStr("dev-secret-key-change-in-production")
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 1440
    public_base_url: AnyHttpUrl = AnyHttpUrl("http://127.0.0.1:8000")
    guest_confirmation_minutes: int = Field(default=15, ge=1, le=1440)
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: SecretStr = SecretStr("")
    smtp_from: str = "noreply@tutor-booking.local"
    smtp_use_tls: bool = True
    max_notification_attempts: int = 3

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()

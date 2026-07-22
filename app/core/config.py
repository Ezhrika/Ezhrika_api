
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # Строка подключения к PostgreSQL.
    # Пример: postgresql://postgres:1234@localhost:5432/smartconsult
    database_url: str
    # Секрет для подписи токенов авторизации (понадобится позже).
    # Пока задан дефолт для запуска, но в .env его нужно переопределить.
    secret_key: str = "change-me-in-env"
    model_config = SettingsConfigDict(env_file=".env")


# Единственный экземпляр настроек, который импортируют остальные модули.
settings = Settings()
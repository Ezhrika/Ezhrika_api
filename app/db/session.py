from collections.abc import Generator
from functools import lru_cache

from sqlalchemy import Engine, create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session

from app.core.config import settings


# Подключение к PostgreSQL и управление сессиями работы с БД.
@lru_cache(maxsize=1)
def get_engine() -> Engine:
    if settings.database_url is None:
        raise RuntimeError("Set DATABASE_URL in .env to use the database.")

    url = make_url(settings.database_url.get_secret_value())
    if url.drivername != "postgresql+psycopg":
        raise ValueError("DATABASE_URL must use postgresql+psycopg.")

    return create_engine(url, pool_pre_ping=True, connect_args={"connect_timeout": 5})


def get_db() -> Generator[Session, None, None]:
    with Session(get_engine()) as session:
        yield session

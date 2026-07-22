"""Подключение к базе данных.

Здесь живёт engine (само соединение с БД) и get_db() — зависимость,
которую роутеры запрашивают через Depends(). Она выдаёт сессию на время
одного запроса и гарантированно закрывает её после, даже если внутри
произошла ошибка.

Какая именно база (SQLite для локальных тестов или PostgreSQL на сервере)
определяется строкой DATABASE_URL из окружения — код одинаков для обеих.
"""
from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings

# SQLite в многопоточном веб-сервере требует отключить проверку потока.
# PostgreSQL этот параметр не нужен — поэтому добавляем только для sqlite.
connect_args = {}
if settings.database_url.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

# Engine — низкоуровневое соединение с БД, создаётся один раз на всё приложение.
engine = create_engine(settings.database_url, connect_args=connect_args)

# Фабрика сессий. Каждый запрос получает свою свежую сессию.
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def get_db():
    """Зависимость FastAPI: открыть сессию -> отдать в эндпоинт -> закрыть."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
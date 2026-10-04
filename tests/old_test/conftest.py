"""Общая обвязка для тестов (pytest сам подхватывает файл с именем conftest.py).

Главная идея: тесты НЕ должны трогать твою рабочую базу. Поэтому здесь
поднимается отдельная тестовая БД (SQLite-файл), таблицы создаются с нуля
перед тестами и сносятся после. Приложению через dependency_overrides
подсовывается эта тестовая сессия вместо настоящей get_db.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app import models  # важно: импорт, чтобы все таблицы зарегистрировались


# Отдельная тестовая база — свой файл, не рабочий.
TEST_DB_URL = "sqlite:///./test.db"
engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


@pytest.fixture(scope="function")
def db_session():
    """Свежие таблицы на каждый тест: создать до, снести после.

    Так тесты не влияют друг на друга — каждый стартует на чистой базе.
    """
    Base.metadata.create_all(engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(engine)


@pytest.fixture(scope="function")
def client(db_session):
    """TestClient, у которого get_db заменён на тестовую сессию.

    dependency_overrides — штатный механизм FastAPI: подменить зависимость
    на время тестов. Приложение думает, что работает как обычно, но сессия
    приходит из тестовой базы.
    """
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()
def _create(client, url, json):
    resp = client.post(url, json=json)
    assert resp.status_code == 201, f"POST {url} -> {resp.status_code}: {resp.text}"
    return resp.json()["id"]
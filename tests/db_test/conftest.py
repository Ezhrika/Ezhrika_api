"""Общие фикстуры существующих тестов моделей, без подключения рабочей БД."""
import pytest

from app.models.tests.conftest import engine, populated_engine, session  # noqa: F401


@pytest.fixture
def db_session(session):
    return session


@pytest.fixture
def consultation(db_session):
    from app.models import Consultation

    return db_session.get(Consultation, 1)


@pytest.fixture
def group(db_session):
    from app.models import AcademicGroup

    obj = AcademicGroup(name="ТЕСТ-102", admission_year=2026)
    db_session.add(obj)
    db_session.commit()
    return obj

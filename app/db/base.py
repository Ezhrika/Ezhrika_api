"""Общий предок всех SQLAlchemy-моделей.

Каждая модель в models.py наследуется от Base. SQLAlchemy через него
собирает метаданные всех таблиц (для создания схемы, связей и т.д.).
"""
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass

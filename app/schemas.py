"""Pydantic-схемы — форма данных на входе и выходе API (то, что в JSON).

Это НЕ то же, что модели. Модели (models.py) описывают таблицы в БД.
Схемы описывают, что приходит от клиента и что уходит клиенту.

Разделение на *Create (вход) и *Out (выход) — не формальность:
именно оно не даёт лишним полям (например password_hash) утечь наружу,
потому что в *Out таких полей просто нет.
"""
from pydantic import BaseModel, ConfigDict
from app.models import UserRole


# ── Teacher ────────────────────────────────────────────────────────────────
class TeacherBase(BaseModel):
    """Общие поля, которые есть и на входе, и на выходе."""
    name: str
    faculty: int


class TeacherCreate(TeacherBase):
    """Что клиент присылает при создании преподавателя."""
    user_id: int


class TeacherOut(TeacherBase):
    """Что API отдаёт клиенту."""
    id: int
    user_id: int

    # Позволяет отдавать объект SQLAlchemy напрямую, без ручного перекладывания полей.
    model_config = ConfigDict(from_attributes=True)
# ── Student ────────────────────────────────────────────────────────────────
class StudentBase(BaseModel):
    """Общие поля, которые есть и на входе, и на выходе."""
    name: str
    student_group: int


class StudentCreate(StudentBase):
    """Что клиент присылает при создании преподавателя."""
    user_id: int


class StudentOut(StudentBase):
    """Что API отдаёт клиенту."""
    id: int
    user_id: int

    # Позволяет отдавать объект SQLAlchemy напрямую, без ручного перекладывания полей.
    model_config = ConfigDict(from_attributes=True)
# ── Account ────────────────────────────────────────────────────────────────
class AccountBase(BaseModel):
    """Общие поля, которые есть и на входе, и на выходе."""
    login: str
    role: UserRole

class AccountCreate(AccountBase):
    """Что клиент присылает при создании преподавателя."""
    password: str

class AccountOut(AccountBase):
    """Что API отдаёт клиенту."""
    id: int
    model_config = ConfigDict(from_attributes=True)
class AccountUpdate(BaseModel):
    login: str
    role: UserRole


class PasswordChange(BaseModel):
    old_password: str      # текущий — для подтверждения, что это владелец
    new_password: str      # новый
# ConsultCreate/ConsultOut, ClassroomOut и т.д. — по одной сущности за раз.

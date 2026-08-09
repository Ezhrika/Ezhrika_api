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
    """Основное поле Teacher"""
    name: str
    faculty: int


class TeacherCreate(TeacherBase):
    """Поля создания преподавателя"""
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

class FacultyBase(BaseModel):
    """Общие поля, факультета"""
    name: str

class FacultyCreate(FacultyBase):
    """заготовка под будущее"""
    pass
class FacultyOut(FacultyBase):
    """Что API отдаёт клиенту."""
    id: int
    model_config = ConfigDict(from_attributes=True)

class StudentGroupBase(BaseModel):
    """Общие поля, группы студентов"""
    name: str
class StudentGroupCreate(StudentGroupBase):
    """заготовка под будущее"""
    pass
class StudentGroupOut(StudentGroupBase):
    """Что API отдаёт клиенту."""
    id: int
    model_config = ConfigDict(from_attributes=True)


class CorpusBase(BaseModel):
    """Общие поля, корпуса"""
    name: str

class CorpusCreate(CorpusBase):
    """заготовка под будущее"""
    pass
class CorpusOut(CorpusBase):
    """Что API отдаёт клиенту."""
    id: int
    model_config = ConfigDict(from_attributes=True)

class ClassroomTypeBase(BaseModel):
    """Общие поля, типа корпуса"""
    name: str

class ClassroomTypeCreate(ClassroomTypeBase):
    """заготовка под будущее"""
    pass
class ClassroomTypeOut(ClassroomTypeBase):
    """Что API отдаёт клиенту."""
    id: int
    model_config = ConfigDict(from_attributes=True)

class SubjectBase(BaseModel):
    """Общие поля, типа предмет"""
    name: str
    faculty: int

class SubjectCreate(SubjectBase):
    """заготовка под будущее"""

    pass

class SubjectOut(SubjectBase):
    """Что API отдаёт клиенту."""
    id: int
    model_config = ConfigDict(from_attributes=True)
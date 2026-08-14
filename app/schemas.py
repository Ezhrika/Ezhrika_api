
from datetime import date,time
from pydantic import BaseModel, ConfigDict, Field, field_validator,model_validator
from app.models import UserRole, BoardType, ScreenType,TimetableKind

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


class ClassroomBase(BaseModel):
    name: str = Field(min_length=1, examples=["301а"])
    corpus: int
    capacity: int = Field(gt=0)
    type: int
    board: BoardType | None = None
    screen: ScreenType = ScreenType.none
    faculty: int | None = None
    info: str | None = None


class ClassroomCreate(ClassroomBase):
    pass


class ClassroomOut(ClassroomBase):
    id: int

    model_config = ConfigDict(from_attributes=True)
class SlotBase(BaseModel):
    number: int = Field(gt=0)
    start_time: time
    end_time: time

    @model_validator(mode="after")
    def end_after_start(self):
        if self.end_time <= self.start_time:
            raise ValueError("end_time должен быть позже start_time")
        return self


class SlotCreate(SlotBase):
    pass


class SlotOut(SlotBase):
    id: int

    model_config = ConfigDict(from_attributes=True)

class TimetableBase(BaseModel):
    day: date
    slot: int
    classroom: int
    teacher: int
    subject: int
    kind: TimetableKind
    groups: list[int] = []


class TimetableCreate(TimetableBase):
    pass


class TimetableOut(TimetableBase):
    id: int

    model_config = ConfigDict(from_attributes=True)

    @field_validator("groups", mode="before")
    @classmethod
    def groups_to_ids(cls, v):
        """Из модели приходят объекты StudentGroup — отдаём клиенту их id."""
        return [g.id if hasattr(g, "id") else g for g in v]
class ConsultBase(BaseModel):
    """Общие поля, типа консультаций"""
    name: str | None = None
    timetable: int
    max_students: int = Field(gt=0)

class ConsultCreate(ConsultBase):
    """заготовка под будущее"""
    pass
class ConsultOut(ConsultBase):
    """Что API отдаёт клиенту."""
    id: int
    model_config = ConfigDict(from_attributes=True)
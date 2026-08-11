"""SQLAlchemy-модели — таблицы базы данных.

Один файл на всю схему: сущностей немного, и так удобнее видеть их целиком
вместе со связями. Соответствует финальной DBML-схеме проекта.
Стиль SQLAlchemy 2.0: Mapped[...] + mapped_column().
"""
import datetime
import enum

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Text,
    Time,
    UniqueConstraint,
    func,
    Table,
Column
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


# ── Перечисления (enum) — фиксированные короткие списки значений ───────────
class UserRole(str, enum.Enum):
    student = "student"
    teacher = "teacher"
    admin = "admin"


class TimetableKind(str, enum.Enum):
    lecture = "lecture"
    practice = "practice"
    consultation = "consultation"
    exam = "exam"


class BoardType(str, enum.Enum):
    chalk = "chalk"
    marker = "marker"
    interactive = "interactive"


class ScreenType(str, enum.Enum):
    none = "none"
    projector = "projector"
    tv = "tv"
    interactive = "interactive"


# ── Учётные записи и люди ──────────────────────────────────────────────────
class Account(Base):
    __tablename__ = "account"

    id: Mapped[int] = mapped_column(primary_key=True)
    login: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(Text, nullable=False)
    role: Mapped[UserRole] = mapped_column(nullable=False)

    teacher: Mapped["Teacher"] = relationship(back_populates="account", uselist=False)
    student: Mapped["Student"] = relationship(back_populates="account", uselist=False)


class Faculty(Base):
    __tablename__ = "faculty"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)


class StudentGroup(Base):
    __tablename__ = "student_group"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)


class Teacher(Base):
    __tablename__ = "teacher"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("account.id"), unique=True, nullable=False
    )
    name: Mapped[str] = mapped_column(Text, nullable=False)
    faculty: Mapped[int] = mapped_column(ForeignKey("faculty.id"), nullable=False)

    account: Mapped["Account"] = relationship(back_populates="teacher")


class Student(Base):
    __tablename__ = "student"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("account.id"), unique=True, nullable=False
    )
    name: Mapped[str] = mapped_column(Text, nullable=False)
    student_group: Mapped[int] = mapped_column(
        ForeignKey("student_group.id"), nullable=False
    )

    account: Mapped["Account"] = relationship(back_populates="student")
    registrations: Mapped[list["ConsultRegistration"]] = relationship(
        back_populates="student"
    )


# ── Помещения ──────────────────────────────────────────────────────────────
class Corpus(Base):
    __tablename__ = "corpus"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)


class ClassroomType(Base):
    __tablename__ = "classroom_type"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)


class Classroom(Base):
    __tablename__ = "classroom"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    corpus: Mapped[int] = mapped_column(ForeignKey("corpus.id"), nullable=False)
    capacity: Mapped[int] = mapped_column(Integer, nullable=False)
    type: Mapped[int] = mapped_column(ForeignKey("classroom_type.id"), nullable=False)
    board: Mapped[BoardType | None] = mapped_column(nullable=True)
    screen: Mapped[ScreenType] = mapped_column(default=ScreenType.none, nullable=False)
    faculty: Mapped[int | None] = mapped_column(ForeignKey("faculty.id"), nullable=True)
    info: Mapped[str | None] = mapped_column(Text, nullable=True)


# ── Предметы и расписание ──────────────────────────────────────────────────
class Subject(Base):
    __tablename__ = "subject"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    faculty: Mapped[int] = mapped_column(ForeignKey("faculty.id"), nullable=False)


class Slot(Base):
    __tablename__ = "slot"

    id: Mapped[int] = mapped_column(primary_key=True)
    number: Mapped[int] = mapped_column(Integer, nullable=False)  # номер пары
    start_time: Mapped[datetime.time] = mapped_column(Time, nullable=False)
    end_time: Mapped[datetime.time] = mapped_column(Time, nullable=False)

class TimetableGroup(Base):
    __tablename__ = "timetable_groups"

    timetable_id: Mapped[int] = mapped_column(
        ForeignKey("timetable.id", ondelete="CASCADE"), primary_key=True
    )
    group_id: Mapped[int] = mapped_column(
        ForeignKey("student_group.id"), primary_key=True
    )

class Timetable(Base):
    __tablename__ = "timetable"
    __table_args__ = (
        # Кабинет занят одной строкой на слот — структурная блокировка кабинета.
        UniqueConstraint("classroom", "day", "slot", name="uq_classroom_day_slot"),
        # Преподаватель не может быть в двух местах одновременно.
        UniqueConstraint("teacher", "day", "slot", name="uq_teacher_day_slot"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    day: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    slot: Mapped[int] = mapped_column(ForeignKey("slot.id"), nullable=False)
    classroom: Mapped[int] = mapped_column(ForeignKey("classroom.id"), nullable=False)
    teacher: Mapped[int] = mapped_column(ForeignKey("teacher.id"), nullable=False)
    subject: Mapped[int] = mapped_column(ForeignKey("subject.id"), nullable=False)
    kind: Mapped[TimetableKind] = mapped_column(nullable=False)

    consult: Mapped["Consult"] = relationship(back_populates="timetable_row", uselist=False)

    groups = relationship("StudentGroup", secondary="timetable_groups")
# ── Консультации ───────────────────────────────────────────────────────────
class Consult(Base):
    __tablename__ = "consult"

    id: Mapped[int] = mapped_column(primary_key=True)
    # Ссылка на строку расписания (kind=consultation для свободного кабинета
    # или kind=practice, если консультация идёт поверх своей пары).
    # Время, кабинет и преподаватель берутся оттуда.
    timetable: Mapped[int] = mapped_column(
        ForeignKey("timetable.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    max_students: Mapped[int] = mapped_column(Integer, nullable=False)

    timetable_row: Mapped["Timetable"] = relationship(back_populates="consult")
    registrations: Mapped[list["ConsultRegistration"]] = relationship(
        back_populates="consult"
    )


class ConsultRegistration(Base):
    __tablename__ = "consult_registrations"

    consult_id: Mapped[int] = mapped_column(
        ForeignKey("consult.id"), primary_key=True
    )
    student_id: Mapped[int] = mapped_column(
        ForeignKey("student.id"), primary_key=True
    )
    registration_time: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    consult: Mapped["Consult"] = relationship(back_populates="registrations")
    student: Mapped["Student"] = relationship(back_populates="registrations")



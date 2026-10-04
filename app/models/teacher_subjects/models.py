"""TeacherSubject: таблица teacher_subjects целевой схемы consultations_v2."""
from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import (
    ForeignKey,
    Integer,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models import (
        Subject,
        Teacher,
    )


class TeacherSubject(Base):
    """
    Справочный список дисциплин преподавателя, не расписание и не список студентов.
    """
    __tablename__ = 'teacher_subjects'

    __table_args__ = (
        {"comment": 'Справочный список дисциплин преподавателя, не расписание и не список студентов.'},
    )

    teacher_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey('teachers.id', name='fk_teacher_subjects_teacher_id'),
        primary_key=True,
        autoincrement=False,
        nullable=False,
    )
    subject_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey('subjects.id', name='fk_teacher_subjects_subject_id'),
        primary_key=True,
        autoincrement=False,
        nullable=False,
    )

    teacher: Mapped[Teacher] = relationship(
        'Teacher',
        back_populates='subject_links',
        foreign_keys='[TeacherSubject.teacher_id]',
    )

    subject: Mapped[Subject] = relationship(
        'Subject',
        back_populates='teacher_links',
        foreign_keys='[TeacherSubject.subject_id]',
    )

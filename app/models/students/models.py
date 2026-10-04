"""Student: таблица students целевой схемы consultations_v2."""
from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import (
    ForeignKey,
    Integer,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models import (
        AcademicGroup,
        ConsultationRegistration,
        ConsultationRequest,
        Person,
    )


class Student(Base):
    """
    Одна текущая академическая группа. NULL означает, что группа пока не определена.
    """
    __tablename__ = 'students'

    __table_args__ = (
        UniqueConstraint('person_id', name='uq_students_person_id'),
        {"comment": 'Одна текущая академическая группа. NULL означает, что группа пока не определена.'},
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
        nullable=False,
    )
    person_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey('people.id', name='fk_students_person_id'),
        nullable=False,
    )
    group_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey('academic_groups.id', name='fk_students_group_id'),
        nullable=True,
    )

    person: Mapped[Person] = relationship(
        'Person',
        back_populates='student',
        foreign_keys='[Student.person_id]',
    )

    group: Mapped[AcademicGroup | None] = relationship(
        'AcademicGroup',
        back_populates='students',
        foreign_keys='[Student.group_id]',
    )

    registrations: Mapped[list[ConsultationRegistration]] = relationship(
        'ConsultationRegistration',
        back_populates='student',
        foreign_keys='[ConsultationRegistration.student_id]',
        passive_deletes="all",
    )

    consultation_requests: Mapped[list[ConsultationRequest]] = relationship(
        'ConsultationRequest',
        back_populates='student',
        foreign_keys='[ConsultationRequest.student_id]',
        passive_deletes="all",
    )

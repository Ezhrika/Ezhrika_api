"""Subject: таблица subjects целевой схемы consultations_v2."""
from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import (
    ForeignKey,
    Integer,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models import (
        Consultation,
        ConsultationRequest,
        Department,
        Teacher,
        TeacherSubject,
        TimetableEvent,
    )


class Subject(Base):
    __tablename__ = 'subjects'

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
        nullable=False,
    )
    name: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    department_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey('departments.id', name='fk_subjects_department_id'),
        nullable=True,
    )

    department: Mapped[Department | None] = relationship(
        'Department',
        back_populates='subjects',
        foreign_keys='[Subject.department_id]',
    )

    teacher_links: Mapped[list[TeacherSubject]] = relationship(
        'TeacherSubject',
        back_populates='subject',
        foreign_keys='[TeacherSubject.subject_id]',
        passive_deletes="all",
    )

    timetable_events: Mapped[list[TimetableEvent]] = relationship(
        'TimetableEvent',
        back_populates='subject',
        foreign_keys='[TimetableEvent.subject_id]',
        passive_deletes="all",
    )

    consultations: Mapped[list[Consultation]] = relationship(
        'Consultation',
        back_populates='subject',
        foreign_keys='[Consultation.subject_id]',
        passive_deletes="all",
    )

    consultation_requests: Mapped[list[ConsultationRequest]] = relationship(
        'ConsultationRequest',
        back_populates='subject',
        foreign_keys='[ConsultationRequest.subject_id]',
        passive_deletes="all",
    )

    teachers: Mapped[list[Teacher]] = relationship(
        'Teacher',
        secondary='teacher_subjects',
        viewonly=True,
    )

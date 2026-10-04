"""Teacher: таблица teachers целевой схемы consultations_v2."""
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
        AIProposal,
        Consultation,
        ConsultationRequest,
        Department,
        Person,
        RoomReservation,
        Subject,
        TeacherSchedulingSettings,
        TeacherSubject,
        TimetableEventTeacher,
    )


class Teacher(Base):
    __tablename__ = 'teachers'

    __table_args__ = (
        UniqueConstraint('person_id', name='uq_teachers_person_id'),
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
        nullable=False,
    )
    person_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey('people.id', name='fk_teachers_person_id'),
        nullable=False,
    )
    department_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey('departments.id', name='fk_teachers_department_id'),
        nullable=True,
    )

    person: Mapped[Person] = relationship(
        'Person',
        back_populates='teacher',
        foreign_keys='[Teacher.person_id]',
    )

    department: Mapped[Department | None] = relationship(
        'Department',
        back_populates='teachers',
        foreign_keys='[Teacher.department_id]',
    )

    subject_links: Mapped[list[TeacherSubject]] = relationship(
        'TeacherSubject',
        back_populates='teacher',
        foreign_keys='[TeacherSubject.teacher_id]',
        passive_deletes="all",
    )

    timetable_event_links: Mapped[list[TimetableEventTeacher]] = relationship(
        'TimetableEventTeacher',
        back_populates='teacher',
        foreign_keys='[TimetableEventTeacher.teacher_id]',
        passive_deletes="all",
    )

    room_reservations: Mapped[list[RoomReservation]] = relationship(
        'RoomReservation',
        back_populates='teacher',
        foreign_keys='[RoomReservation.teacher_id]',
        passive_deletes="all",
    )

    consultations: Mapped[list[Consultation]] = relationship(
        'Consultation',
        back_populates='teacher',
        foreign_keys='[Consultation.teacher_id]',
        passive_deletes="all",
    )

    consultation_requests: Mapped[list[ConsultationRequest]] = relationship(
        'ConsultationRequest',
        back_populates='teacher',
        foreign_keys='[ConsultationRequest.teacher_id]',
        passive_deletes="all",
    )

    scheduling_settings: Mapped[TeacherSchedulingSettings | None] = relationship(
        'TeacherSchedulingSettings',
        back_populates='teacher',
        foreign_keys='[TeacherSchedulingSettings.teacher_id]',
        passive_deletes="all",
        uselist=False,
    )

    ai_proposals: Mapped[list[AIProposal]] = relationship(
        'AIProposal',
        back_populates='teacher',
        foreign_keys='[AIProposal.teacher_id]',
        passive_deletes="all",
    )

    subjects: Mapped[list[Subject]] = relationship(
        'Subject',
        secondary='teacher_subjects',
        viewonly=True,
    )

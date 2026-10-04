"""TimetableEventTeacher: таблица timetable_event_teachers целевой схемы consultations_v2."""
from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import (
    ForeignKey,
    Index,
    Integer,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models import (
        Teacher,
        TimetableEvent,
    )


class TimetableEventTeacher(Base):
    __tablename__ = 'timetable_event_teachers'

    __table_args__ = (
        Index('ix_timetable_event_teachers_teacher_id', 'teacher_id'),
    )

    event_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey('timetable_events.id', name='fk_timetable_event_teachers_event_id'),
        primary_key=True,
        autoincrement=False,
        nullable=False,
    )
    teacher_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey('teachers.id', name='fk_timetable_event_teachers_teacher_id'),
        primary_key=True,
        autoincrement=False,
        nullable=False,
    )

    event: Mapped[TimetableEvent] = relationship(
        'TimetableEvent',
        back_populates='teacher_links',
        foreign_keys='[TimetableEventTeacher.event_id]',
    )

    teacher: Mapped[Teacher] = relationship(
        'Teacher',
        back_populates='timetable_event_links',
        foreign_keys='[TimetableEventTeacher.teacher_id]',
    )

"""TimetableEventGroup: таблица timetable_event_groups целевой схемы consultations_v2."""
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
        AcademicGroup,
        TimetableEvent,
    )


class TimetableEventGroup(Base):
    __tablename__ = 'timetable_event_groups'

    __table_args__ = (
        Index('ix_timetable_event_groups_group_id', 'group_id'),
    )

    event_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey('timetable_events.id', name='fk_timetable_event_groups_event_id'),
        primary_key=True,
        autoincrement=False,
        nullable=False,
    )
    group_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey('academic_groups.id', name='fk_timetable_event_groups_group_id'),
        primary_key=True,
        autoincrement=False,
        nullable=False,
    )

    event: Mapped[TimetableEvent] = relationship(
        'TimetableEvent',
        back_populates='group_links',
        foreign_keys='[TimetableEventGroup.event_id]',
    )

    group: Mapped[AcademicGroup] = relationship(
        'AcademicGroup',
        back_populates='timetable_event_links',
        foreign_keys='[TimetableEventGroup.group_id]',
    )

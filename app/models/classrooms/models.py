"""Classroom: таблица classrooms целевой схемы consultations_v2."""
from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models import (
        Building,
        Department,
        RoomReservation,
        TimetableEvent,
    )


class Classroom(Base):
    """
    NULL capacity/has_screen — неизвестно, а не ноль/нет. Неизвестную вместимость нельзя
    считать подтвержденной пригодностью аудитории.
    """
    __tablename__ = 'classrooms'

    __table_args__ = (
        CheckConstraint('capacity > 0', name='ck_classrooms_1'),
        UniqueConstraint('building_id', 'name', name='uq_classrooms_building_id_name'),
        {
            "comment": (
                'NULL capacity/has_screen — неизвестно, а не ноль/нет. Неизвестную вместимость '
                'нельзя считать подтвержденной пригодностью аудитории.'
            )
        },
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
        nullable=False,
    )
    building_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey('buildings.id', name='fk_classrooms_building_id'),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    capacity: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )
    room_type: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )
    board_type: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )
    has_screen: Mapped[bool | None] = mapped_column(
        Boolean,
        nullable=True,
    )
    info: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    office_departments: Mapped[list[Department]] = relationship(
        'Department',
        back_populates='office_classroom',
        foreign_keys='[Department.office_classroom_id]',
        passive_deletes="all",
    )

    building: Mapped[Building] = relationship(
        'Building',
        back_populates='classrooms',
        foreign_keys='[Classroom.building_id]',
    )

    timetable_events: Mapped[list[TimetableEvent]] = relationship(
        'TimetableEvent',
        back_populates='classroom',
        foreign_keys='[TimetableEvent.classroom_id]',
        passive_deletes="all",
    )

    room_reservations: Mapped[list[RoomReservation]] = relationship(
        'RoomReservation',
        back_populates='classroom',
        foreign_keys='[RoomReservation.classroom_id]',
        passive_deletes="all",
    )

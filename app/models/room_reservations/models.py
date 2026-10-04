"""RoomReservation: таблица room_reservations целевой схемы consultations_v2."""
from __future__ import annotations

import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models import (
        AIProposal,
        Classroom,
        Consultation,
        Notification,
        PeriodSlot,
        ScheduleConflict,
        Teacher,
        TimetableEvent,
        User,
    )


class RoomReservation(Base):
    """
    Кабинет удерживается на ВЕСЬ period_slot. Одна бронь — несколько консультаций одного
    преподавателя. host_event_id: подтвержденное использование кабинета внутри своего
    занятия, не отмена занятия. active/conflicted учитываются как местная бронь; released —
    история. Пересечения проверять по реальному времени, в том числе между разными сетками
    пар, с защитой от конкурентных записей.
    """
    __tablename__ = 'room_reservations'

    __table_args__ = (
        CheckConstraint("status IN ('active', 'conflicted', 'released')", name='ck_room_reservations_1'),
        CheckConstraint('version > 0', name='ck_room_reservations_2'),
        UniqueConstraint('id', 'teacher_id', name='uq_room_reservations_id_teacher_id'),
        Index('ix_room_reservations_classroom_id_period_slot_id', 'classroom_id', 'period_slot_id'),
        Index('ix_room_reservations_teacher_id_status', 'teacher_id', 'status'),
        {
            "comment": (
                'Кабинет удерживается на ВЕСЬ period_slot. Одна бронь — несколько консультаций '
                'одного преподавателя. host_event_id: подтвержденное использование кабинета '
                'внутри своего занятия, не отмена занятия. active/conflicted учитываются как '
                'местная бронь; released — история. Пересечения проверять по реальному времени, в'
                ' том числе между разными сетками пар, с защитой от конкурентных записей.'
            )
        },
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
        nullable=False,
    )
    teacher_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey('teachers.id', name='fk_room_reservations_teacher_id'),
        nullable=False,
    )
    classroom_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey('classrooms.id', name='fk_room_reservations_classroom_id'),
        nullable=False,
    )
    period_slot_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey('period_slots.id', name='fk_room_reservations_period_slot_id'),
        nullable=False,
    )
    host_event_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey('timetable_events.id', name='fk_room_reservations_host_event_id'),
        nullable=True,
    )
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        server_default=text("'active'"),
        default='active',
    )
    created_by: Mapped[int] = mapped_column(
        Integer,
        ForeignKey('users.id', name='fk_room_reservations_created_by'),
        nullable=False,
    )
    version: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        server_default=text('1'),
        default=1,
    )
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.current_timestamp(),
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.current_timestamp(),
        onupdate=func.current_timestamp(),
    )

    # Optimistic locking for ORM flush(), not bulk DML or raw SQL.
    __mapper_args__ = {"version_id_col": version}

    teacher: Mapped[Teacher] = relationship(
        'Teacher',
        back_populates='room_reservations',
        foreign_keys='[RoomReservation.teacher_id]',
    )

    classroom: Mapped[Classroom] = relationship(
        'Classroom',
        back_populates='room_reservations',
        foreign_keys='[RoomReservation.classroom_id]',
    )

    period_slot: Mapped[PeriodSlot] = relationship(
        'PeriodSlot',
        back_populates='room_reservations',
        foreign_keys='[RoomReservation.period_slot_id]',
    )

    host_event: Mapped[TimetableEvent | None] = relationship(
        'TimetableEvent',
        back_populates='hosted_reservations',
        foreign_keys='[RoomReservation.host_event_id]',
    )

    creator: Mapped[User] = relationship(
        'User',
        back_populates='created_room_reservations',
        foreign_keys='[RoomReservation.created_by]',
    )

    # Match both FK columns; synchronize only the first to avoid changing ownership.
    consultations: Mapped[list[Consultation]] = relationship(
        'Consultation',
        back_populates='reservation',
        foreign_keys='[Consultation.reservation_id]',
        primaryjoin=(
            'and_(Consultation.reservation_id == RoomReservation.id, Consultation.teacher_id == '
            'RoomReservation.teacher_id)'
        ),
        passive_deletes="all",
    )

    conflicts: Mapped[list[ScheduleConflict]] = relationship(
        'ScheduleConflict',
        back_populates='reservation',
        foreign_keys='[ScheduleConflict.reservation_id]',
        passive_deletes="all",
    )

    ai_proposals: Mapped[list[AIProposal]] = relationship(
        'AIProposal',
        back_populates='reservation',
        foreign_keys='[AIProposal.reservation_id]',
        passive_deletes="all",
    )

    notifications: Mapped[list[Notification]] = relationship(
        'Notification',
        back_populates='reservation',
        foreign_keys='[Notification.reservation_id]',
        passive_deletes="all",
    )

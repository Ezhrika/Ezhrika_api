"""ScheduleConflict: таблица schedule_conflicts целевой схемы consultations_v2."""
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
    Text,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models import (
        AIProposal,
        Consultation,
        RoomReservation,
        ScheduleImport,
        TimetableEvent,
        User,
    )


class ScheduleConflict(Base):
    """
    Одна затронутая сущность: бронь ИЛИ консультация. Конфликт брони затрагивает все
    консультации в ней. Не создавать повторно один и тот же открытый конфликт при каждом
    опросе. dismissed не делает физический конфликт безопасным: нужны проверенное
    исправление данных или допустимое разрешение.
    """
    __tablename__ = 'schedule_conflicts'

    __table_args__ = (
        CheckConstraint(
            "kind IN ('room_busy', 'teacher_busy', 'outside_reservation', 'availability_changed',"
            " 'source_changed')",
            name='ck_schedule_conflicts_1',
        ),
        CheckConstraint("status IN ('open', 'resolved', 'dismissed')", name='ck_schedule_conflicts_2'),
        CheckConstraint(
            '(reservation_id IS NOT NULL AND consultation_id IS NULL) OR (reservation_id IS NULL '
            'AND consultation_id IS NOT NULL)',
            name='ck_schedule_conflicts_3',
        ),
        CheckConstraint(
            'consultation_id IS NULL OR conflicting_consultation_id IS NULL OR consultation_id <>'
            ' conflicting_consultation_id',
            name='ck_schedule_conflicts_4',
        ),
        Index('ix_schedule_conflicts_status_detected_at', 'status', 'detected_at'),
        Index('ix_schedule_conflicts_reservation_id', 'reservation_id'),
        Index('ix_schedule_conflicts_consultation_id', 'consultation_id'),
        {
            "comment": (
                'Одна затронутая сущность: бронь ИЛИ консультация. Конфликт брони затрагивает все'
                ' консультации в ней. Не создавать повторно один и тот же открытый конфликт при '
                'каждом опросе. dismissed не делает физический конфликт безопасным: нужны '
                'проверенное исправление данных или допустимое разрешение.'
            )
        },
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
        nullable=False,
    )
    reservation_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey('room_reservations.id', name='fk_schedule_conflicts_reservation_id'),
        nullable=True,
    )
    consultation_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey('consultations.id', name='fk_schedule_conflicts_consultation_id'),
        nullable=True,
    )
    conflicting_event_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey('timetable_events.id', name='fk_schedule_conflicts_conflicting_event_id'),
        nullable=True,
    )
    conflicting_consultation_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey('consultations.id', name='fk_schedule_conflicts_conflicting_consultation_id'),
        nullable=True,
    )
    detected_import_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey('schedule_imports.id', name='fk_schedule_conflicts_detected_import_id'),
        nullable=True,
    )
    kind: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        server_default=text("'open'"),
        default='open',
    )
    details: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    resolution_note: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    detected_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.current_timestamp(),
    )
    resolved_at: Mapped[datetime.datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    resolved_by: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey('users.id', name='fk_schedule_conflicts_resolved_by'),
        nullable=True,
    )

    reservation: Mapped[RoomReservation | None] = relationship(
        'RoomReservation',
        back_populates='conflicts',
        foreign_keys='[ScheduleConflict.reservation_id]',
    )

    consultation: Mapped[Consultation | None] = relationship(
        'Consultation',
        back_populates='conflicts',
        foreign_keys='[ScheduleConflict.consultation_id]',
    )

    conflicting_event: Mapped[TimetableEvent | None] = relationship(
        'TimetableEvent',
        back_populates='caused_conflicts',
        foreign_keys='[ScheduleConflict.conflicting_event_id]',
    )

    conflicting_consultation: Mapped[Consultation | None] = relationship(
        'Consultation',
        back_populates='caused_conflicts',
        foreign_keys='[ScheduleConflict.conflicting_consultation_id]',
    )

    detected_import: Mapped[ScheduleImport | None] = relationship(
        'ScheduleImport',
        back_populates='detected_conflicts',
        foreign_keys='[ScheduleConflict.detected_import_id]',
    )

    resolver: Mapped[User | None] = relationship(
        'User',
        back_populates='resolved_conflicts',
        foreign_keys='[ScheduleConflict.resolved_by]',
    )

    ai_proposals: Mapped[list[AIProposal]] = relationship(
        'AIProposal',
        back_populates='conflict',
        foreign_keys='[AIProposal.conflict_id]',
        passive_deletes="all",
    )

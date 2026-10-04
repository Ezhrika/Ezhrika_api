"""PeriodSlot: таблица period_slots целевой схемы consultations_v2."""
from __future__ import annotations

import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    SmallInteger,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models import (
        BellSchedule,
        RoomReservation,
    )


class PeriodSlot(Base):
    """
    Одна конкретная полная пара на дату, а не недельный шаблон. Приложение проверяет
    локальную дату в timezone сетки. Используемые слоты не менять без проверки зависимых
    броней.
    """
    __tablename__ = 'period_slots'

    __table_args__ = (
        CheckConstraint('period_number > 0', name='ck_period_slots_1'),
        CheckConstraint('ends_at > starts_at', name='ck_period_slots_2'),
        UniqueConstraint(
            'bell_schedule_id',
            'slot_date',
            'period_number',
            name='uq_period_slots_bell_schedule_id_slot_date_period_number',
        ),
        Index('ix_period_slots_starts_at', 'starts_at'),
        {
            "comment": (
                'Одна конкретная полная пара на дату, а не недельный шаблон. Приложение проверяет'
                ' локальную дату в timezone сетки. Используемые слоты не менять без проверки '
                'зависимых броней.'
            )
        },
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
        nullable=False,
    )
    bell_schedule_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey('bell_schedules.id', name='fk_period_slots_bell_schedule_id'),
        nullable=False,
    )
    slot_date: Mapped[datetime.date] = mapped_column(
        Date,
        nullable=False,
    )
    period_number: Mapped[int] = mapped_column(
        SmallInteger,
        nullable=False,
    )
    starts_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    ends_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    bell_schedule: Mapped[BellSchedule] = relationship(
        'BellSchedule',
        back_populates='period_slots',
        foreign_keys='[PeriodSlot.bell_schedule_id]',
    )

    room_reservations: Mapped[list[RoomReservation]] = relationship(
        'RoomReservation',
        back_populates='period_slot',
        foreign_keys='[RoomReservation.period_slot_id]',
        passive_deletes="all",
    )

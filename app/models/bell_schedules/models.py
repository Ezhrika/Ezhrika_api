"""BellSchedule: таблица bell_schedules целевой схемы consultations_v2."""
from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import (
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models import (
        PeriodSlot,
    )


class BellSchedule(Base):
    """
    Название сетки пар и часовой пояс IANA. Возможны разные сетки для подразделений или
    периодов обучения.
    """
    __tablename__ = 'bell_schedules'

    __table_args__ = (
        {
            "comment": (
                'Название сетки пар и часовой пояс IANA. Возможны разные сетки для подразделений '
                'или периодов обучения.'
            )
        },
    )

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
    timezone: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    period_slots: Mapped[list[PeriodSlot]] = relationship(
        'PeriodSlot',
        back_populates='bell_schedule',
        foreign_keys='[PeriodSlot.bell_schedule_id]',
        passive_deletes="all",
    )

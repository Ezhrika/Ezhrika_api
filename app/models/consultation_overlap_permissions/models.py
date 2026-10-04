"""ConsultationOverlapPermission: таблица consultation_overlap_permissions целевой схемы consultations_v2."""
from __future__ import annotations

import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models import (
        Consultation,
        TimetableEvent,
        User,
    )


class ConsultationOverlapPermission(Base):
    """
    Явное разрешение преподавателя совместить конкретную консультацию с конкретным своим
    занятием. Не разрешает чужую бронь или пересечение двух консультаций. Разрешение
    действует только для подтвержденных версий события и консультации; после изменения нужны
    повторная проверка и подтверждение.
    """
    __tablename__ = 'consultation_overlap_permissions'

    __table_args__ = (
        CheckConstraint('approved_event_version > 0', name='ck_consultation_overlap_permissions_1'),
        CheckConstraint(
            'approved_consultation_version > 0',
            name='ck_consultation_overlap_permissions_2',
        ),
        {
            "comment": (
                'Явное разрешение преподавателя совместить конкретную консультацию с конкретным '
                'своим занятием. Не разрешает чужую бронь или пересечение двух консультаций. '
                'Разрешение действует только для подтвержденных версий события и консультации; '
                'после изменения нужны повторная проверка и подтверждение.'
            )
        },
    )

    consultation_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey('consultations.id', name='fk_consultation_overlap_permissions_consultation_id'),
        primary_key=True,
        autoincrement=False,
        nullable=False,
    )
    event_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey('timetable_events.id', name='fk_consultation_overlap_permissions_event_id'),
        primary_key=True,
        autoincrement=False,
        nullable=False,
    )
    approved_by: Mapped[int] = mapped_column(
        Integer,
        ForeignKey('users.id', name='fk_consultation_overlap_permissions_approved_by'),
        nullable=False,
    )
    approved_event_version: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    approved_consultation_version: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    approved_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.current_timestamp(),
    )
    reason: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    consultation: Mapped[Consultation] = relationship(
        'Consultation',
        back_populates='overlap_permissions',
        foreign_keys='[ConsultationOverlapPermission.consultation_id]',
    )

    event: Mapped[TimetableEvent] = relationship(
        'TimetableEvent',
        back_populates='overlap_permissions',
        foreign_keys='[ConsultationOverlapPermission.event_id]',
    )

    approver: Mapped[User] = relationship(
        'User',
        back_populates='approved_overlaps',
        foreign_keys='[ConsultationOverlapPermission.approved_by]',
    )

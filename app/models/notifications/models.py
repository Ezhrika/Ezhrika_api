"""Notification: таблица notifications целевой схемы consultations_v2."""
from __future__ import annotations

import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models import (
        Consultation,
        RoomReservation,
        User,
    )


class Notification(Base):
    """
    Уведомления внутри приложения. dedupe_key предотвращает повторы одного уведомления для
    пользователя. Письма/push и повторные попытки доставки — отдельная реализация.
    """
    __tablename__ = 'notifications'

    __table_args__ = (
        Index('ix_notifications_user_id_created_at', 'user_id', 'created_at'),
        UniqueConstraint('user_id', 'dedupe_key', name='uq_notifications_user_id_dedupe_key'),
        {
            "comment": (
                'Уведомления внутри приложения. dedupe_key предотвращает повторы одного '
                'уведомления для пользователя. Письма/push и повторные попытки доставки — '
                'отдельная реализация.'
            )
        },
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
        nullable=False,
    )
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey('users.id', name='fk_notifications_user_id'),
        nullable=False,
    )
    consultation_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey('consultations.id', name='fk_notifications_consultation_id'),
        nullable=True,
    )
    reservation_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey('room_reservations.id', name='fk_notifications_reservation_id'),
        nullable=True,
    )
    kind: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    message: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    dedupe_key: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    read_at: Mapped[datetime.datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.current_timestamp(),
    )

    user: Mapped[User] = relationship(
        'User',
        back_populates='notifications',
        foreign_keys='[Notification.user_id]',
    )

    consultation: Mapped[Consultation | None] = relationship(
        'Consultation',
        back_populates='notifications',
        foreign_keys='[Notification.consultation_id]',
    )

    reservation: Mapped[RoomReservation | None] = relationship(
        'RoomReservation',
        back_populates='notifications',
        foreign_keys='[Notification.reservation_id]',
    )

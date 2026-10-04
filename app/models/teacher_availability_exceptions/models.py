"""TeacherAvailabilityException: таблица teacher_availability_exceptions целевой схемы consultations_v2."""
from __future__ import annotations

import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
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
        TeacherSchedulingSettings,
        User,
    )


class TeacherAvailabilityException(Base):
    """
    Разовые разрешения/запреты. Разовый запрет сильнее разрешений. Разовое разрешение может
    переопределить недельный запрет, но не занятость/чужую бронь. Правила сами не переносят
    уже опубликованные консультации.
    """
    __tablename__ = 'teacher_availability_exceptions'

    __table_args__ = (
        CheckConstraint(
            "kind IN ('available', 'unavailable')",
            name='ck_teacher_availability_exceptions_1',
        ),
        CheckConstraint('ends_at > starts_at', name='ck_teacher_availability_exceptions_2'),
        Index('ix_teacher_availability_exceptions_teacher_id_starts_at', 'teacher_id', 'starts_at'),
        {
            "comment": (
                'Разовые разрешения/запреты. Разовый запрет сильнее разрешений. Разовое '
                'разрешение может переопределить недельный запрет, но не занятость/чужую бронь. '
                'Правила сами не переносят уже опубликованные консультации.'
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
        ForeignKey(
            'teacher_scheduling_settings.teacher_id',
            name='fk_teacher_availability_exceptions_teacher_id',
        ),
        nullable=False,
    )
    kind: Mapped[str] = mapped_column(
        String(20),
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
    source_text: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default=text('true'),
        default=True,
    )
    confirmed_by: Mapped[int] = mapped_column(
        Integer,
        ForeignKey('users.id', name='fk_teacher_availability_exceptions_confirmed_by'),
        nullable=False,
    )
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.current_timestamp(),
    )

    settings: Mapped[TeacherSchedulingSettings] = relationship(
        'TeacherSchedulingSettings',
        back_populates='availability_exceptions',
        foreign_keys='[TeacherAvailabilityException.teacher_id]',
    )

    confirmer: Mapped[User] = relationship(
        'User',
        back_populates='confirmed_availability_exceptions',
        foreign_keys='[TeacherAvailabilityException.confirmed_by]',
    )

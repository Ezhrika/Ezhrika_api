"""TeacherAvailabilityRule: таблица teacher_availability_rules целевой схемы consultations_v2."""
from __future__ import annotations

import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    SmallInteger,
    String,
    Text,
    Time,
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


class TeacherAvailabilityRule(Base):
    """
    Подтвержденные недельные правила. 1=понедельник, 7=воскресенье; время локальное,
    valid_to включительно. available открывает окно; unavailable запрещает;
    preferred/avoided только ранжируют. Нет доступных окон — ИИ не считает человека
    доступным круглосуточно. Правила через полночь разбивать. Личные причины не показывать
    студентам.
    """
    __tablename__ = 'teacher_availability_rules'

    __table_args__ = (
        CheckConstraint(
            "kind IN ('available', 'unavailable', 'preferred', 'avoided')",
            name='ck_teacher_availability_rules_1',
        ),
        CheckConstraint('day_of_week BETWEEN 1 AND 7', name='ck_teacher_availability_rules_2'),
        CheckConstraint(
            'valid_to IS NULL OR valid_to >= valid_from',
            name='ck_teacher_availability_rules_3',
        ),
        CheckConstraint(
            '(all_day AND start_time IS NULL AND end_time IS NULL) OR (NOT all_day AND start_time'
            ' IS NOT NULL AND end_time IS NOT NULL AND start_time < end_time)',
            name='ck_teacher_availability_rules_4',
        ),
        CheckConstraint(
            "(kind IN ('preferred', 'avoided') AND weight IS NOT NULL AND weight BETWEEN 1 AND "
            "10) OR (kind IN ('available', 'unavailable') AND weight IS NULL)",
            name='ck_teacher_availability_rules_5',
        ),
        Index('ix_teacher_availability_rules_teacher_id_day_of_week', 'teacher_id', 'day_of_week'),
        {
            "comment": (
                'Подтвержденные недельные правила. 1=понедельник, 7=воскресенье; время локальное,'
                ' valid_to включительно. available открывает окно; unavailable запрещает; '
                'preferred/avoided только ранжируют. Нет доступных окон — ИИ не считает человека '
                'доступным круглосуточно. Правила через полночь разбивать. Личные причины не '
                'показывать студентам.'
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
            name='fk_teacher_availability_rules_teacher_id',
        ),
        nullable=False,
    )
    kind: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )
    day_of_week: Mapped[int] = mapped_column(
        SmallInteger,
        nullable=False,
    )
    all_day: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default=text('false'),
        default=False,
    )
    start_time: Mapped[datetime.time | None] = mapped_column(
        Time(timezone=False),
        nullable=True,
    )
    end_time: Mapped[datetime.time | None] = mapped_column(
        Time(timezone=False),
        nullable=True,
    )
    valid_from: Mapped[datetime.date] = mapped_column(
        Date,
        nullable=False,
    )
    valid_to: Mapped[datetime.date | None] = mapped_column(
        Date,
        nullable=True,
    )
    weight: Mapped[int | None] = mapped_column(
        SmallInteger,
        nullable=True,
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
        ForeignKey('users.id', name='fk_teacher_availability_rules_confirmed_by'),
        nullable=False,
    )
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.current_timestamp(),
    )

    settings: Mapped[TeacherSchedulingSettings] = relationship(
        'TeacherSchedulingSettings',
        back_populates='availability_rules',
        foreign_keys='[TeacherAvailabilityRule.teacher_id]',
    )

    confirmer: Mapped[User] = relationship(
        'User',
        back_populates='confirmed_availability_rules',
        foreign_keys='[TeacherAvailabilityRule.confirmed_by]',
    )

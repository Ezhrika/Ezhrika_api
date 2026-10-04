"""TeacherSchedulingSettings: таблица teacher_scheduling_settings целевой схемы consultations_v2."""
from __future__ import annotations

import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    String,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models import (
        Teacher,
        TeacherAvailabilityException,
        TeacherAvailabilityRule,
    )


class TeacherSchedulingSettings(Base):
    """
    Часовой пояс IANA. NULL дневного лимита — без лимита. Буфер — минимальный промежуток,
    без двойного сложения между двумя консультациями. Это настройки автоподбора и записи, не
    разрешение обходить реальную занятость. Любое изменение настроек, правил или исключений
    увеличивает version этого набора.
    """
    __tablename__ = 'teacher_scheduling_settings'

    __table_args__ = (
        CheckConstraint('default_duration_minutes > 0', name='ck_teacher_scheduling_settings_1'),
        CheckConstraint('buffer_minutes >= 0', name='ck_teacher_scheduling_settings_2'),
        CheckConstraint('min_booking_notice_minutes >= 0', name='ck_teacher_scheduling_settings_3'),
        CheckConstraint('max_consultations_per_day > 0', name='ck_teacher_scheduling_settings_4'),
        CheckConstraint('version > 0', name='ck_teacher_scheduling_settings_5'),
        {
            "comment": (
                'Часовой пояс IANA. NULL дневного лимита — без лимита. Буфер — минимальный '
                'промежуток, без двойного сложения между двумя консультациями. Это настройки '
                'автоподбора и записи, не разрешение обходить реальную занятость. Любое изменение'
                ' настроек, правил или исключений увеличивает version этого набора.'
            )
        },
    )

    teacher_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey('teachers.id', name='fk_teacher_scheduling_settings_teacher_id'),
        primary_key=True,
        autoincrement=False,
        nullable=False,
    )
    timezone: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    default_duration_minutes: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        server_default=text('30'),
        default=30,
    )
    buffer_minutes: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        server_default=text('0'),
        default=0,
    )
    min_booking_notice_minutes: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        server_default=text('0'),
        default=0,
    )
    max_consultations_per_day: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )
    version: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        server_default=text('1'),
        default=1,
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
        back_populates='scheduling_settings',
        foreign_keys='[TeacherSchedulingSettings.teacher_id]',
    )

    availability_rules: Mapped[list[TeacherAvailabilityRule]] = relationship(
        'TeacherAvailabilityRule',
        back_populates='settings',
        foreign_keys='[TeacherAvailabilityRule.teacher_id]',
        passive_deletes="all",
    )

    availability_exceptions: Mapped[list[TeacherAvailabilityException]] = relationship(
        'TeacherAvailabilityException',
        back_populates='settings',
        foreign_keys='[TeacherAvailabilityException.teacher_id]',
        passive_deletes="all",
    )

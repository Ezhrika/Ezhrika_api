"""ConsultationRegistration: таблица consultation_registrations целевой схемы consultations_v2."""
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
        Consultation,
        Student,
    )


class ConsultationRegistration(Base):
    """
    Одна текущая запись студента на консультацию. Повторная запись обновляет строку с
    повторной проверкой мест. Только cancelled не занимает место. Остаток мест вычисляется,
    отдельного счетчика нет. Проверку вместимости и запись выполнять атомарно.
    """
    __tablename__ = 'consultation_registrations'

    __table_args__ = (
        CheckConstraint(
            "status IN ('confirmed', 'cancelled', 'attended', 'no_show')",
            name='ck_consultation_registrations_1',
        ),
        CheckConstraint(
            "(status = 'cancelled' AND cancelled_at IS NOT NULL) OR (status <> 'cancelled' AND "
            'cancelled_at IS NULL)',
            name='ck_consultation_registrations_2',
        ),
        Index('ix_consultation_registrations_consultation_id_status', 'consultation_id', 'status'),
        Index('ix_consultation_registrations_student_id_status', 'student_id', 'status'),
        {
            "comment": (
                'Одна текущая запись студента на консультацию. Повторная запись обновляет строку '
                'с повторной проверкой мест. Только cancelled не занимает место. Остаток мест '
                'вычисляется, отдельного счетчика нет. Проверку вместимости и запись выполнять '
                'атомарно.'
            )
        },
    )

    consultation_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey('consultations.id', name='fk_consultation_registrations_consultation_id'),
        primary_key=True,
        autoincrement=False,
        nullable=False,
    )
    student_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey('students.id', name='fk_consultation_registrations_student_id'),
        primary_key=True,
        autoincrement=False,
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        server_default=text("'confirmed'"),
        default='confirmed',
    )
    student_question: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    registered_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.current_timestamp(),
    )
    cancelled_at: Mapped[datetime.datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.current_timestamp(),
        onupdate=func.current_timestamp(),
    )

    consultation: Mapped[Consultation] = relationship(
        'Consultation',
        back_populates='registrations',
        foreign_keys='[ConsultationRegistration.consultation_id]',
    )

    student: Mapped[Student] = relationship(
        'Student',
        back_populates='registrations',
        foreign_keys='[ConsultationRegistration.student_id]',
    )

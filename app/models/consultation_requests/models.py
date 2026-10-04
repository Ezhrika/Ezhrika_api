"""ConsultationRequest: таблица consultation_requests целевой схемы consultations_v2."""
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
        Subject,
        Teacher,
    )


class ConsultationRequest(Base):
    """
    Запрос организовать консультацию, не регистрация. Несколько запросов могут вести к одной
    консультации того же преподавателя. Студент записывается отдельно.
    """
    __tablename__ = 'consultation_requests'

    __table_args__ = (
        CheckConstraint(
            "status IN ('pending', 'planned', 'rejected', 'cancelled')",
            name='ck_consultation_requests_1',
        ),
        CheckConstraint(
            "status <> 'planned' OR consultation_id IS NOT NULL",
            name='ck_consultation_requests_2',
        ),
        Index('ix_consultation_requests_teacher_id_status', 'teacher_id', 'status'),
        Index('ix_consultation_requests_student_id', 'student_id'),
        {
            "comment": (
                'Запрос организовать консультацию, не регистрация. Несколько запросов могут вести'
                ' к одной консультации того же преподавателя. Студент записывается отдельно.'
            )
        },
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
        nullable=False,
    )
    student_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey('students.id', name='fk_consultation_requests_student_id'),
        nullable=False,
    )
    teacher_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey('teachers.id', name='fk_consultation_requests_teacher_id'),
        nullable=False,
    )
    subject_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey('subjects.id', name='fk_consultation_requests_subject_id'),
        nullable=True,
    )
    topic: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        server_default=text("'pending'"),
        default='pending',
    )
    consultation_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey('consultations.id', name='fk_consultation_requests_consultation_id'),
        nullable=True,
    )
    teacher_reply: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
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

    student: Mapped[Student] = relationship(
        'Student',
        back_populates='consultation_requests',
        foreign_keys='[ConsultationRequest.student_id]',
    )

    teacher: Mapped[Teacher] = relationship(
        'Teacher',
        back_populates='consultation_requests',
        foreign_keys='[ConsultationRequest.teacher_id]',
    )

    subject: Mapped[Subject | None] = relationship(
        'Subject',
        back_populates='consultation_requests',
        foreign_keys='[ConsultationRequest.subject_id]',
    )

    consultation: Mapped[Consultation | None] = relationship(
        'Consultation',
        back_populates='requests',
        foreign_keys='[ConsultationRequest.consultation_id]',
    )

"""AIProposal: таблица ai_proposals целевой схемы consultations_v2."""
from __future__ import annotations

import datetime
from typing import Any, TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    JSON,
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
        RoomReservation,
        ScheduleConflict,
        Teacher,
        User,
    )


class AIProposal(Base):
    """
    Только черновик изменения. Payload содержит предложенные поля и версии затронутых
    сущностей; не произвольный SQL. Применение — после подтверждения преподавателем,
    проверки прав и повторной проверки условий в транзакции. Рекомендации консультаций
    студенту не обязаны сохраняться здесь.
    """
    __tablename__ = 'ai_proposals'

    __table_args__ = (
        CheckConstraint(
            "kind IN ('availability_change', 'consultation_create', 'consultation_change', "
            "'room_change')",
            name='ck_ai_proposals_1',
        ),
        CheckConstraint('payload_version > 0', name='ck_ai_proposals_2'),
        CheckConstraint(
            "status IN ('pending', 'applied', 'rejected', 'obsolete')",
            name='ck_ai_proposals_3',
        ),
        Index('ix_ai_proposals_teacher_id_status', 'teacher_id', 'status'),
        {
            "comment": (
                'Только черновик изменения. Payload содержит предложенные поля и версии '
                'затронутых сущностей; не произвольный SQL. Применение — после подтверждения '
                'преподавателем, проверки прав и повторной проверки условий в транзакции. '
                'Рекомендации консультаций студенту не обязаны сохраняться здесь.'
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
        ForeignKey('teachers.id', name='fk_ai_proposals_teacher_id'),
        nullable=False,
    )
    requested_by: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey('users.id', name='fk_ai_proposals_requested_by'),
        nullable=True,
    )
    consultation_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey('consultations.id', name='fk_ai_proposals_consultation_id'),
        nullable=True,
    )
    reservation_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey('room_reservations.id', name='fk_ai_proposals_reservation_id'),
        nullable=True,
    )
    conflict_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey('schedule_conflicts.id', name='fk_ai_proposals_conflict_id'),
        nullable=True,
    )
    kind: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )
    source_text: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    payload_version: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        server_default=text('1'),
        default=1,
    )
    proposed_payload: Mapped[Any] = mapped_column(
        JSON(none_as_null=True),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        server_default=text("'pending'"),
        default='pending',
    )
    decided_by: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey('users.id', name='fk_ai_proposals_decided_by'),
        nullable=True,
    )
    decided_at: Mapped[datetime.datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.current_timestamp(),
    )

    teacher: Mapped[Teacher] = relationship(
        'Teacher',
        back_populates='ai_proposals',
        foreign_keys='[AIProposal.teacher_id]',
    )

    requester: Mapped[User | None] = relationship(
        'User',
        back_populates='requested_ai_proposals',
        foreign_keys='[AIProposal.requested_by]',
    )

    consultation: Mapped[Consultation | None] = relationship(
        'Consultation',
        back_populates='ai_proposals',
        foreign_keys='[AIProposal.consultation_id]',
    )

    reservation: Mapped[RoomReservation | None] = relationship(
        'RoomReservation',
        back_populates='ai_proposals',
        foreign_keys='[AIProposal.reservation_id]',
    )

    conflict: Mapped[ScheduleConflict | None] = relationship(
        'ScheduleConflict',
        back_populates='ai_proposals',
        foreign_keys='[AIProposal.conflict_id]',
    )

    decider: Mapped[User | None] = relationship(
        'User',
        back_populates='decided_ai_proposals',
        foreign_keys='[AIProposal.decided_by]',
    )

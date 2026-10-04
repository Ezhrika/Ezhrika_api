"""User: таблица users целевой схемы consultations_v2."""
from __future__ import annotations

import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models import (
        AIProposal,
        Consultation,
        ConsultationOverlapPermission,
        Notification,
        Person,
        RoomReservation,
        ScheduleConflict,
        ScheduleImport,
        ScheduleSource,
        TeacherAvailabilityException,
        TeacherAvailabilityRule,
        TimetableEvent,
        UserRoleAssignment,
    )


class User(Base):
    """
    Только аккаунт и авторизация. NULL password_hash допустим при отдельно реализованном
    внешнем входе, не означает вход без пароля.
    """
    __tablename__ = 'users'

    __table_args__ = (
        UniqueConstraint('person_id', name='uq_users_person_id'),
        UniqueConstraint('login', name='uq_users_login'),
        {
            "comment": (
                'Только аккаунт и авторизация. NULL password_hash допустим при отдельно '
                'реализованном внешнем входе, не означает вход без пароля.'
            )
        },
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
        nullable=False,
    )
    person_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey('people.id', name='fk_users_person_id'),
        nullable=False,
    )
    login: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )
    password_hash: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default=text('true'),
        default=True,
    )
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.current_timestamp(),
    )

    person: Mapped[Person] = relationship(
        'Person',
        back_populates='user',
        foreign_keys='[User.person_id]',
    )

    roles: Mapped[list[UserRoleAssignment]] = relationship(
        'UserRoleAssignment',
        back_populates='user',
        foreign_keys='[UserRoleAssignment.user_id]',
        passive_deletes="all",
    )

    personal_timetable_events: Mapped[list[TimetableEvent]] = relationship(
        'TimetableEvent',
        back_populates='owner',
        foreign_keys='[TimetableEvent.owner_user_id]',
        passive_deletes="all",
    )

    created_timetable_events: Mapped[list[TimetableEvent]] = relationship(
        'TimetableEvent',
        back_populates='creator',
        foreign_keys='[TimetableEvent.created_by]',
        passive_deletes="all",
    )

    created_room_reservations: Mapped[list[RoomReservation]] = relationship(
        'RoomReservation',
        back_populates='creator',
        foreign_keys='[RoomReservation.created_by]',
        passive_deletes="all",
    )

    created_consultations: Mapped[list[Consultation]] = relationship(
        'Consultation',
        back_populates='creator',
        foreign_keys='[Consultation.created_by]',
        passive_deletes="all",
    )

    approved_overlaps: Mapped[list[ConsultationOverlapPermission]] = relationship(
        'ConsultationOverlapPermission',
        back_populates='approver',
        foreign_keys='[ConsultationOverlapPermission.approved_by]',
        passive_deletes="all",
    )

    confirmed_availability_rules: Mapped[list[TeacherAvailabilityRule]] = relationship(
        'TeacherAvailabilityRule',
        back_populates='confirmer',
        foreign_keys='[TeacherAvailabilityRule.confirmed_by]',
        passive_deletes="all",
    )

    confirmed_availability_exceptions: Mapped[list[TeacherAvailabilityException]] = relationship(
        'TeacherAvailabilityException',
        back_populates='confirmer',
        foreign_keys='[TeacherAvailabilityException.confirmed_by]',
        passive_deletes="all",
    )

    submitted_schedule_sources: Mapped[list[ScheduleSource]] = relationship(
        'ScheduleSource',
        back_populates='submitter',
        foreign_keys='[ScheduleSource.submitted_by]',
        passive_deletes="all",
    )

    reviewed_schedule_imports: Mapped[list[ScheduleImport]] = relationship(
        'ScheduleImport',
        back_populates='reviewer',
        foreign_keys='[ScheduleImport.reviewed_by]',
        passive_deletes="all",
    )

    resolved_conflicts: Mapped[list[ScheduleConflict]] = relationship(
        'ScheduleConflict',
        back_populates='resolver',
        foreign_keys='[ScheduleConflict.resolved_by]',
        passive_deletes="all",
    )

    requested_ai_proposals: Mapped[list[AIProposal]] = relationship(
        'AIProposal',
        back_populates='requester',
        foreign_keys='[AIProposal.requested_by]',
        passive_deletes="all",
    )

    decided_ai_proposals: Mapped[list[AIProposal]] = relationship(
        'AIProposal',
        back_populates='decider',
        foreign_keys='[AIProposal.decided_by]',
        passive_deletes="all",
    )

    notifications: Mapped[list[Notification]] = relationship(
        'Notification',
        back_populates='user',
        foreign_keys='[Notification.user_id]',
        passive_deletes="all",
    )

"""Consultation: таблица consultations целевой схемы consultations_v2."""
from __future__ import annotations

import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
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
        AIProposal,
        AcademicGroup,
        ConsultationAllowedGroup,
        ConsultationOverlapPermission,
        ConsultationRegistration,
        ConsultationRequest,
        Notification,
        RoomReservation,
        ScheduleConflict,
        Subject,
        Teacher,
        User,
        VideoMeeting,
    )


class Consultation(Base):
    """
    Фактическое время консультации. Аудитория определяется через бронь. Для очной/гибридной
    публикации нужны действующая подходящая бронь и полное попадание в ее пару. Один общий
    интервал для всех мест; индивидуальные приемы — отдельные консультации с max_students=1.
    Изменение общей брони затрагивает все связанные консультации.
    """
    __tablename__ = 'consultations'

    __table_args__ = (
        CheckConstraint("format IN ('onsite', 'online', 'hybrid')", name='ck_consultations_1'),
        CheckConstraint('max_students > 0', name='ck_consultations_2'),
        CheckConstraint(
            "audience_mode IN ('all_students', 'selected_groups')",
            name='ck_consultations_3',
        ),
        CheckConstraint(
            "status IN ('draft', 'published', 'cancelled', 'completed')",
            name='ck_consultations_4',
        ),
        CheckConstraint('version > 0', name='ck_consultations_5'),
        CheckConstraint('ends_at > starts_at', name='ck_consultations_6'),
        CheckConstraint(
            "(format = 'online' AND reservation_id IS NULL) OR (format IN ('onsite', 'hybrid') "
            "AND (reservation_id IS NOT NULL OR status IN ('draft', 'cancelled')))",
            name='ck_consultations_7',
        ),
        CheckConstraint(
            'registration_opens_at IS NULL OR registration_closes_at IS NULL OR '
            'registration_opens_at < registration_closes_at',
            name='ck_consultations_8',
        ),
        CheckConstraint(
            'registration_opens_at IS NULL OR registration_opens_at < starts_at',
            name='ck_consultations_9',
        ),
        CheckConstraint(
            'registration_closes_at IS NULL OR registration_closes_at <= starts_at',
            name='ck_consultations_10',
        ),
        Index('ix_consultations_teacher_id_starts_at', 'teacher_id', 'starts_at'),
        Index('ix_consultations_status_starts_at', 'status', 'starts_at'),
        Index('ix_consultations_reservation_id', 'reservation_id'),
        ForeignKeyConstraint(
            ['reservation_id', 'teacher_id'],
            ['room_reservations.id', 'room_reservations.teacher_id'],
            name='fk_consultations_reservation_id_teacher_id',
        ),
        {
            "comment": (
                'Фактическое время консультации. Аудитория определяется через бронь. Для '
                'очной/гибридной публикации нужны действующая подходящая бронь и полное попадание'
                ' в ее пару. Один общий интервал для всех мест; индивидуальные приемы — отдельные'
                ' консультации с max_students=1. Изменение общей брони затрагивает все связанные '
                'консультации.'
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
        ForeignKey('teachers.id', name='fk_consultations_teacher_id'),
        nullable=False,
    )
    subject_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey('subjects.id', name='fk_consultations_subject_id'),
        nullable=True,
    )
    reservation_id: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )
    title: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    format: Mapped[str] = mapped_column(
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
    max_students: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    audience_mode: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        server_default=text("'all_students'"),
        default='all_students',
    )
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        server_default=text("'draft'"),
        default='draft',
    )
    registration_opens_at: Mapped[datetime.datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    registration_closes_at: Mapped[datetime.datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    created_by: Mapped[int] = mapped_column(
        Integer,
        ForeignKey('users.id', name='fk_consultations_created_by'),
        nullable=False,
    )
    version: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        server_default=text('1'),
        default=1,
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

    # Optimistic locking for ORM flush(), not bulk DML or raw SQL.
    __mapper_args__ = {"version_id_col": version}

    teacher: Mapped[Teacher] = relationship(
        'Teacher',
        back_populates='consultations',
        foreign_keys='[Consultation.teacher_id]',
    )

    subject: Mapped[Subject | None] = relationship(
        'Subject',
        back_populates='consultations',
        foreign_keys='[Consultation.subject_id]',
    )

    # Match both FK columns; synchronize only the first to avoid changing ownership.
    reservation: Mapped[RoomReservation | None] = relationship(
        'RoomReservation',
        back_populates='consultations',
        foreign_keys='[Consultation.reservation_id]',
        primaryjoin=(
            'and_(Consultation.reservation_id == RoomReservation.id, Consultation.teacher_id == '
            'RoomReservation.teacher_id)'
        ),
    )

    creator: Mapped[User] = relationship(
        'User',
        back_populates='created_consultations',
        foreign_keys='[Consultation.created_by]',
    )

    allowed_group_links: Mapped[list[ConsultationAllowedGroup]] = relationship(
        'ConsultationAllowedGroup',
        back_populates='consultation',
        foreign_keys='[ConsultationAllowedGroup.consultation_id]',
        passive_deletes="all",
    )

    registrations: Mapped[list[ConsultationRegistration]] = relationship(
        'ConsultationRegistration',
        back_populates='consultation',
        foreign_keys='[ConsultationRegistration.consultation_id]',
        passive_deletes="all",
    )

    overlap_permissions: Mapped[list[ConsultationOverlapPermission]] = relationship(
        'ConsultationOverlapPermission',
        back_populates='consultation',
        foreign_keys='[ConsultationOverlapPermission.consultation_id]',
        passive_deletes="all",
    )

    requests: Mapped[list[ConsultationRequest]] = relationship(
        'ConsultationRequest',
        back_populates='consultation',
        foreign_keys='[ConsultationRequest.consultation_id]',
        passive_deletes="all",
    )

    conflicts: Mapped[list[ScheduleConflict]] = relationship(
        'ScheduleConflict',
        back_populates='consultation',
        foreign_keys='[ScheduleConflict.consultation_id]',
        passive_deletes="all",
    )

    caused_conflicts: Mapped[list[ScheduleConflict]] = relationship(
        'ScheduleConflict',
        back_populates='conflicting_consultation',
        foreign_keys='[ScheduleConflict.conflicting_consultation_id]',
        passive_deletes="all",
    )

    ai_proposals: Mapped[list[AIProposal]] = relationship(
        'AIProposal',
        back_populates='consultation',
        foreign_keys='[AIProposal.consultation_id]',
        passive_deletes="all",
    )

    notifications: Mapped[list[Notification]] = relationship(
        'Notification',
        back_populates='consultation',
        foreign_keys='[Notification.consultation_id]',
        passive_deletes="all",
    )

    video_meeting: Mapped[VideoMeeting | None] = relationship(
        'VideoMeeting',
        back_populates='consultation',
        foreign_keys='[VideoMeeting.consultation_id]',
        passive_deletes="all",
        uselist=False,
    )

    allowed_groups: Mapped[list[AcademicGroup]] = relationship(
        'AcademicGroup',
        secondary='consultation_allowed_groups',
        viewonly=True,
    )

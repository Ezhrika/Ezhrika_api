"""TimetableEvent: таблица timetable_events целевой схемы consultations_v2."""
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
        AcademicGroup,
        Classroom,
        ConsultationOverlapPermission,
        RoomReservation,
        ScheduleConflict,
        ScheduleEventSource,
        Subject,
        Teacher,
        TimetableEventGroup,
        TimetableEventTeacher,
        User,
    )


class TimetableEvent(Base):
    """
    Только учебные/внешние события, не консультации. Интервал отражает занятость по
    расписанию вуза. Личный импорт не меняет общую занятость кабинетов. Внешние
    конфликтующие сведения разрешено сохранить для последующего разрешения конфликта.
    """
    __tablename__ = 'timetable_events'

    __table_args__ = (
        CheckConstraint(
            "kind IN ('lecture', 'practice', 'lab', 'exam', 'retake', 'other')",
            name='ck_timetable_events_1',
        ),
        CheckConstraint("status IN ('scheduled', 'cancelled')", name='ck_timetable_events_2'),
        CheckConstraint("visibility IN ('shared', 'personal')", name='ck_timetable_events_3'),
        CheckConstraint('version > 0', name='ck_timetable_events_4'),
        CheckConstraint('ends_at > starts_at', name='ck_timetable_events_5'),
        CheckConstraint(
            "(visibility = 'shared' AND owner_user_id IS NULL) OR (visibility = 'personal' AND "
            'owner_user_id IS NOT NULL)',
            name='ck_timetable_events_6',
        ),
        Index('ix_timetable_events_classroom_id_starts_at', 'classroom_id', 'starts_at'),
        Index('ix_timetable_events_owner_user_id_starts_at', 'owner_user_id', 'starts_at'),
        Index('ix_timetable_events_starts_at', 'starts_at'),
        {
            "comment": (
                'Только учебные/внешние события, не консультации. Интервал отражает занятость по '
                'расписанию вуза. Личный импорт не меняет общую занятость кабинетов. Внешние '
                'конфликтующие сведения разрешено сохранить для последующего разрешения '
                'конфликта.'
            )
        },
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
        nullable=False,
    )
    subject_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey('subjects.id', name='fk_timetable_events_subject_id'),
        nullable=True,
    )
    classroom_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey('classrooms.id', name='fk_timetable_events_classroom_id'),
        nullable=True,
    )
    title: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
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
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        server_default=text("'scheduled'"),
        default='scheduled',
    )
    visibility: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )
    owner_user_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey('users.id', name='fk_timetable_events_owner_user_id'),
        nullable=True,
    )
    created_by: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey('users.id', name='fk_timetable_events_created_by'),
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

    subject: Mapped[Subject | None] = relationship(
        'Subject',
        back_populates='timetable_events',
        foreign_keys='[TimetableEvent.subject_id]',
    )

    classroom: Mapped[Classroom | None] = relationship(
        'Classroom',
        back_populates='timetable_events',
        foreign_keys='[TimetableEvent.classroom_id]',
    )

    owner: Mapped[User | None] = relationship(
        'User',
        back_populates='personal_timetable_events',
        foreign_keys='[TimetableEvent.owner_user_id]',
    )

    creator: Mapped[User | None] = relationship(
        'User',
        back_populates='created_timetable_events',
        foreign_keys='[TimetableEvent.created_by]',
    )

    teacher_links: Mapped[list[TimetableEventTeacher]] = relationship(
        'TimetableEventTeacher',
        back_populates='event',
        foreign_keys='[TimetableEventTeacher.event_id]',
        passive_deletes="all",
    )

    group_links: Mapped[list[TimetableEventGroup]] = relationship(
        'TimetableEventGroup',
        back_populates='event',
        foreign_keys='[TimetableEventGroup.event_id]',
        passive_deletes="all",
    )

    hosted_reservations: Mapped[list[RoomReservation]] = relationship(
        'RoomReservation',
        back_populates='host_event',
        foreign_keys='[RoomReservation.host_event_id]',
        passive_deletes="all",
    )

    overlap_permissions: Mapped[list[ConsultationOverlapPermission]] = relationship(
        'ConsultationOverlapPermission',
        back_populates='event',
        foreign_keys='[ConsultationOverlapPermission.event_id]',
        passive_deletes="all",
    )

    source_links: Mapped[list[ScheduleEventSource]] = relationship(
        'ScheduleEventSource',
        back_populates='event',
        foreign_keys='[ScheduleEventSource.event_id]',
        passive_deletes="all",
    )

    caused_conflicts: Mapped[list[ScheduleConflict]] = relationship(
        'ScheduleConflict',
        back_populates='conflicting_event',
        foreign_keys='[ScheduleConflict.conflicting_event_id]',
        passive_deletes="all",
    )

    teachers: Mapped[list[Teacher]] = relationship(
        'Teacher',
        secondary='timetable_event_teachers',
        viewonly=True,
    )

    groups: Mapped[list[AcademicGroup]] = relationship(
        'AcademicGroup',
        secondary='timetable_event_groups',
        viewonly=True,
    )

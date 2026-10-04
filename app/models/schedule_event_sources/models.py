"""ScheduleEventSource: таблица schedule_event_sources целевой схемы consultations_v2."""
from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import (
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    Integer,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models import (
        ScheduleImport,
        ScheduleSource,
        TimetableEvent,
    )


class ScheduleEventSource(Base):
    """
    Одна запись источника соответствует событию; у события может быть несколько источников.
    Ключ должен позволять сопоставить повторный импорт после переноса. Без устойчивого
    внешнего ID неоднозначные совпадения требуют проверки.
    """
    __tablename__ = 'schedule_event_sources'

    __table_args__ = (
        Index('ix_schedule_event_sources_event_id', 'event_id'),
        ForeignKeyConstraint(
            ['last_seen_import_id', 'source_id'],
            ['schedule_imports.id', 'schedule_imports.source_id'],
            name='fk_schedule_event_sources_last_seen_import_id_source_id',
        ),
        {
            "comment": (
                'Одна запись источника соответствует событию; у события может быть несколько '
                'источников. Ключ должен позволять сопоставить повторный импорт после переноса. '
                'Без устойчивого внешнего ID неоднозначные совпадения требуют проверки.'
            )
        },
    )

    source_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey('schedule_sources.id', name='fk_schedule_event_sources_source_id'),
        primary_key=True,
        autoincrement=False,
        nullable=False,
    )
    source_event_key: Mapped[str] = mapped_column(
        String(255),
        primary_key=True,
        autoincrement=False,
        nullable=False,
    )
    event_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey('timetable_events.id', name='fk_schedule_event_sources_event_id'),
        nullable=False,
    )
    last_seen_import_id: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    source: Mapped[ScheduleSource] = relationship(
        'ScheduleSource',
        back_populates='event_links',
        foreign_keys='[ScheduleEventSource.source_id]',
    )

    event: Mapped[TimetableEvent] = relationship(
        'TimetableEvent',
        back_populates='source_links',
        foreign_keys='[ScheduleEventSource.event_id]',
    )

    # Match both FK columns; synchronize only the first to avoid changing ownership.
    last_seen_import: Mapped[ScheduleImport] = relationship(
        'ScheduleImport',
        back_populates='seen_event_links',
        foreign_keys='[ScheduleEventSource.last_seen_import_id]',
        primaryjoin=(
            'and_(ScheduleEventSource.last_seen_import_id == ScheduleImport.id, '
            'ScheduleEventSource.source_id == ScheduleImport.source_id)'
        ),
    )

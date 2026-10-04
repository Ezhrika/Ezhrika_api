"""ScheduleImport: таблица schedule_imports целевой схемы consultations_v2."""
from __future__ import annotations

import datetime
from typing import Any, TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    JSON,
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
        ScheduleConflict,
        ScheduleEventSource,
        ScheduleSource,
        User,
    )


class ScheduleImport(Base):
    """
    Отдельный запуск загрузки. draft_payload — распознанный черновик, не действующее
    расписание. Не отменять отсутствующие события по неуспешному/неполному импорту.
    Проверять область покрытия, роль источника и другие источники того же события.
    """
    __tablename__ = 'schedule_imports'

    __table_args__ = (
        CheckConstraint(
            "status IN ('pending', 'review', 'applied', 'failed', 'rejected')",
            name='ck_schedule_imports_1',
        ),
        CheckConstraint(
            'coverage_from IS NULL OR coverage_to IS NULL OR coverage_to >= coverage_from',
            name='ck_schedule_imports_2',
        ),
        UniqueConstraint('id', 'source_id', name='uq_schedule_imports_id_source_id'),
        Index('ix_schedule_imports_source_id_started_at', 'source_id', 'started_at'),
        {
            "comment": (
                'Отдельный запуск загрузки. draft_payload — распознанный черновик, не действующее'
                ' расписание. Не отменять отсутствующие события по неуспешному/неполному импорту.'
                ' Проверять область покрытия, роль источника и другие источники того же события.'
            )
        },
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
        nullable=False,
    )
    source_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey('schedule_sources.id', name='fk_schedule_imports_source_id'),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        server_default=text("'pending'"),
        default='pending',
    )
    coverage_from: Mapped[datetime.date | None] = mapped_column(
        Date,
        nullable=True,
    )
    coverage_to: Mapped[datetime.date | None] = mapped_column(
        Date,
        nullable=True,
    )
    is_complete: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default=text('false'),
        default=False,
    )
    raw_file_key: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    draft_payload: Mapped[Any] = mapped_column(
        JSON(none_as_null=True),
        nullable=True,
    )
    reviewed_by: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey('users.id', name='fk_schedule_imports_reviewed_by'),
        nullable=True,
    )
    started_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.current_timestamp(),
    )
    finished_at: Mapped[datetime.datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    error_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    source: Mapped[ScheduleSource] = relationship(
        'ScheduleSource',
        back_populates='imports',
        foreign_keys='[ScheduleImport.source_id]',
    )

    reviewer: Mapped[User | None] = relationship(
        'User',
        back_populates='reviewed_schedule_imports',
        foreign_keys='[ScheduleImport.reviewed_by]',
    )

    # Match both FK columns; synchronize only the first to avoid changing ownership.
    seen_event_links: Mapped[list[ScheduleEventSource]] = relationship(
        'ScheduleEventSource',
        back_populates='last_seen_import',
        foreign_keys='[ScheduleEventSource.last_seen_import_id]',
        primaryjoin=(
            'and_(ScheduleEventSource.last_seen_import_id == ScheduleImport.id, '
            'ScheduleEventSource.source_id == ScheduleImport.source_id)'
        ),
        passive_deletes="all",
    )

    detected_conflicts: Mapped[list[ScheduleConflict]] = relationship(
        'ScheduleConflict',
        back_populates='detected_import',
        foreign_keys='[ScheduleConflict.detected_import_id]',
        passive_deletes="all",
    )

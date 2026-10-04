"""ScheduleSource: таблица schedule_sources целевой схемы consultations_v2."""
from __future__ import annotations

import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
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
        ScheduleEventSource,
        ScheduleImport,
        User,
    )


class ScheduleSource(Base):
    """
    locator — URL или ключ файла, не содержимое и не секреты. Статус official назначает
    доверенная серверная логика/администратор, не модель по тексту файла. Ссылка на сайт
    сама по себе не гарантирует успешный импорт.
    """
    __tablename__ = 'schedule_sources'

    __table_args__ = (
        CheckConstraint("kind IN ('website', 'file', 'manual')", name='ck_schedule_sources_1'),
        CheckConstraint("authority IN ('official', 'user_provided')", name='ck_schedule_sources_2'),
        {
            "comment": (
                'locator — URL или ключ файла, не содержимое и не секреты. Статус official '
                'назначает доверенная серверная логика/администратор, не модель по тексту файла. '
                'Ссылка на сайт сама по себе не гарантирует успешный импорт.'
            )
        },
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
        nullable=False,
    )
    name: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    kind: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )
    locator: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    authority: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        server_default=text("'user_provided'"),
        default='user_provided',
    )
    submitted_by: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey('users.id', name='fk_schedule_sources_submitted_by'),
        nullable=True,
    )
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.current_timestamp(),
    )

    submitter: Mapped[User | None] = relationship(
        'User',
        back_populates='submitted_schedule_sources',
        foreign_keys='[ScheduleSource.submitted_by]',
    )

    imports: Mapped[list[ScheduleImport]] = relationship(
        'ScheduleImport',
        back_populates='source',
        foreign_keys='[ScheduleImport.source_id]',
        passive_deletes="all",
    )

    event_links: Mapped[list[ScheduleEventSource]] = relationship(
        'ScheduleEventSource',
        back_populates='source',
        foreign_keys='[ScheduleEventSource.source_id]',
        passive_deletes="all",
    )

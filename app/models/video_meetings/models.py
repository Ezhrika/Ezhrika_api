"""VideoMeeting: таблица video_meetings целевой схемы consultations_v2."""
from __future__ import annotations

import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models import (
        Consultation,
    )


class VideoMeeting(Base):
    """
    Метаданные видеокомнаты. Доступ выдавать участникам на сервере; постоянные секреты и
    токены здесь не хранить. Курсы, материалы и задания в эту версию не включены.
    """
    __tablename__ = 'video_meetings'

    __table_args__ = (
        UniqueConstraint('consultation_id', name='uq_video_meetings_consultation_id'),
        UniqueConstraint(
            'provider',
            'external_room_id',
            name='uq_video_meetings_provider_external_room_id',
        ),
        {
            "comment": (
                'Метаданные видеокомнаты. Доступ выдавать участникам на сервере; постоянные '
                'секреты и токены здесь не хранить. Курсы, материалы и задания в эту версию не '
                'включены.'
            )
        },
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
        nullable=False,
    )
    consultation_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey('consultations.id', name='fk_video_meetings_consultation_id'),
        nullable=False,
    )
    provider: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    external_room_id: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.current_timestamp(),
    )

    consultation: Mapped[Consultation] = relationship(
        'Consultation',
        back_populates='video_meeting',
        foreign_keys='[VideoMeeting.consultation_id]',
    )

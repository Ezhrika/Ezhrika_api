"""Building: таблица buildings целевой схемы consultations_v2."""
from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import (
    Integer,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models import (
        Classroom,
    )


class Building(Base):
    __tablename__ = 'buildings'

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
    address: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    classrooms: Mapped[list[Classroom]] = relationship(
        'Classroom',
        back_populates='building',
        foreign_keys='[Classroom.building_id]',
        passive_deletes="all",
    )

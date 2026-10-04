"""AcademicGroup: таблица academic_groups целевой схемы consultations_v2."""
from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import (
    Index,
    Integer,
    SmallInteger,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models import (
        ConsultationAllowedGroup,
        Student,
        TimetableEventGroup,
    )


class AcademicGroup(Base):
    __tablename__ = 'academic_groups'

    __table_args__ = (
        Index('ix_academic_groups_name', 'name'),
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
        nullable=False,
    )
    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    admission_year: Mapped[int | None] = mapped_column(
        SmallInteger,
        nullable=True,
    )

    students: Mapped[list[Student]] = relationship(
        'Student',
        back_populates='group',
        foreign_keys='[Student.group_id]',
        passive_deletes="all",
    )

    timetable_event_links: Mapped[list[TimetableEventGroup]] = relationship(
        'TimetableEventGroup',
        back_populates='group',
        foreign_keys='[TimetableEventGroup.group_id]',
        passive_deletes="all",
    )

    consultation_access_links: Mapped[list[ConsultationAllowedGroup]] = relationship(
        'ConsultationAllowedGroup',
        back_populates='group',
        foreign_keys='[ConsultationAllowedGroup.group_id]',
        passive_deletes="all",
    )

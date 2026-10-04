"""Department: таблица departments целевой схемы consultations_v2."""
from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import (
    ForeignKey,
    Integer,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models import (
        Classroom,
        Subject,
        Teacher,
    )


class Department(Base):
    """
    Кафедра. office_classroom_id — справочный кабинет, а не постоянная бронь.
    """
    __tablename__ = 'departments'

    __table_args__ = (
        {"comment": 'Кафедра. office_classroom_id — справочный кабинет, а не постоянная бронь.'},
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
    office_classroom_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey('classrooms.id', name='fk_departments_office_classroom_id'),
        nullable=True,
    )

    teachers: Mapped[list[Teacher]] = relationship(
        'Teacher',
        back_populates='department',
        foreign_keys='[Teacher.department_id]',
        passive_deletes="all",
    )

    office_classroom: Mapped[Classroom | None] = relationship(
        'Classroom',
        back_populates='office_departments',
        foreign_keys='[Department.office_classroom_id]',
    )

    subjects: Mapped[list[Subject]] = relationship(
        'Subject',
        back_populates='department',
        foreign_keys='[Subject.department_id]',
        passive_deletes="all",
    )

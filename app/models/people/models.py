"""Person: таблица people целевой схемы consultations_v2."""
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
        Student,
        Teacher,
        User,
    )


class Person(Base):
    """
    Человек может присутствовать в расписании без аккаунта. ФИО не уникально: однофамильцев
    не объединять автоматически.
    """
    __tablename__ = 'people'

    __table_args__ = (
        {
            "comment": (
                'Человек может присутствовать в расписании без аккаунта. ФИО не уникально: '
                'однофамильцев не объединять автоматически.'
            )
        },
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
        nullable=False,
    )
    full_name: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    user: Mapped[User | None] = relationship(
        'User',
        back_populates='person',
        foreign_keys='[User.person_id]',
        passive_deletes="all",
        uselist=False,
    )

    teacher: Mapped[Teacher | None] = relationship(
        'Teacher',
        back_populates='person',
        foreign_keys='[Teacher.person_id]',
        passive_deletes="all",
        uselist=False,
    )

    student: Mapped[Student | None] = relationship(
        'Student',
        back_populates='person',
        foreign_keys='[Student.person_id]',
        passive_deletes="all",
        uselist=False,
    )

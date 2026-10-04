"""UserRoleAssignment: таблица user_roles целевой схемы consultations_v2."""
from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models import (
        User,
    )


class UserRoleAssignment(Base):
    __tablename__ = 'user_roles'

    __table_args__ = (
        CheckConstraint("role IN ('student', 'teacher', 'admin')", name='ck_user_roles_1'),
    )

    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey('users.id', name='fk_user_roles_user_id'),
        primary_key=True,
        autoincrement=False,
        nullable=False,
    )
    role: Mapped[str] = mapped_column(
        String(20),
        primary_key=True,
        autoincrement=False,
        nullable=False,
    )

    user: Mapped[User] = relationship(
        'User',
        back_populates='roles',
        foreign_keys='[UserRoleAssignment.user_id]',
    )

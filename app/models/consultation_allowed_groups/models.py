"""ConsultationAllowedGroup: таблица consultation_allowed_groups целевой схемы consultations_v2."""
from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import (
    ForeignKey,
    Index,
    Integer,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models import (
        AcademicGroup,
        Consultation,
    )


class ConsultationAllowedGroup(Base):
    """
    Ограничение доступа, а не список участников. При selected_groups пустой список запрещает
    запись всем и не допускается при публикации. При all_students список должен быть пуст.
    """
    __tablename__ = 'consultation_allowed_groups'

    __table_args__ = (
        Index('ix_consultation_allowed_groups_group_id', 'group_id'),
        {
            "comment": (
                'Ограничение доступа, а не список участников. При selected_groups пустой список '
                'запрещает запись всем и не допускается при публикации. При all_students список '
                'должен быть пуст.'
            )
        },
    )

    consultation_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey('consultations.id', name='fk_consultation_allowed_groups_consultation_id'),
        primary_key=True,
        autoincrement=False,
        nullable=False,
    )
    group_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey('academic_groups.id', name='fk_consultation_allowed_groups_group_id'),
        primary_key=True,
        autoincrement=False,
        nullable=False,
    )

    consultation: Mapped[Consultation] = relationship(
        'Consultation',
        back_populates='allowed_group_links',
        foreign_keys='[ConsultationAllowedGroup.consultation_id]',
    )

    group: Mapped[AcademicGroup] = relationship(
        'AcademicGroup',
        back_populates='consultation_access_links',
        foreign_keys='[ConsultationAllowedGroup.group_id]',
    )

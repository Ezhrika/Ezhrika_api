"""Версии агрегатов при обычном ORM flush(). Не заменяет бизнес-проверки.

Изменение правил/исключений меняет TeacherSchedulingSettings.version.
Изменение состава преподавателей/групп события или групп доступа консультации
также делает версию соответствующего события/консультации новой.
Core/bulk DML и внешний SQL не проходят через этот обработчик.
"""
from __future__ import annotations

from typing import Any

from sqlalchemy import event, func, inspect, select
from sqlalchemy.orm import Session

from .consultation_allowed_groups.models import ConsultationAllowedGroup
from .consultations.models import Consultation
from .teacher_availability_exceptions.models import TeacherAvailabilityException
from .teacher_availability_rules.models import TeacherAvailabilityRule
from .teacher_scheduling_settings.models import TeacherSchedulingSettings
from .timetable_event_groups.models import TimetableEventGroup
from .timetable_event_teachers.models import TimetableEventTeacher
from .timetable_events.models import TimetableEvent
from .room_reservations.models import RoomReservation

# child class: (parent class, FK attribute, relationship attribute)
_VERSIONED_PARENTS = {
    TeacherAvailabilityRule: (TeacherSchedulingSettings, "teacher_id", "settings"),
    TeacherAvailabilityException: (TeacherSchedulingSettings, "teacher_id", "settings"),
    TimetableEventTeacher: (TimetableEvent, "event_id", "event"),
    TimetableEventGroup: (TimetableEvent, "event_id", "event"),
    ConsultationAllowedGroup: (Consultation, "consultation_id", "consultation"),
}
_VERSIONED_CHILDREN = {
    RoomReservation: (
        Consultation,
        "reservation_id",
    ),
}

def _touch_versioned_parents(
    session: Session, flush_context: Any, instances: Any
) -> None:
    """Touch each affected persistent parent once per flush, including reparenting."""
    parent_keys: set[tuple[type, int]] = set()
    parent_objects: set[Any] = set()
    candidates = set(session.new) | set(session.dirty) | set(session.deleted)
    with session.no_autoflush:
        for child in candidates:
            config = _VERSIONED_PARENTS.get(type(child))
            if config is None:
                continue
            if (
                child not in session.new
                and child not in session.deleted
                and not session.is_modified(child, include_collections=False)
            ):
                continue
            parent_cls, fk_name, relationship_name = config
            state = inspect(child)
            current_id = getattr(child, fk_name)
            if current_id is not None:
                parent_keys.add((parent_cls, current_id))

            # Relationship assignment may precede FK synchronization by SQLAlchemy.
            history = state.attrs[relationship_name].history
            for parent in (*history.added, *history.deleted):
                if parent is not None:
                    parent_objects.add(parent)

            if state.persistent:
                # Read the stored FK using the old identity. This also handles a
                # direct FK assignment while its previous value was expired.
                child_table = state.mapper.local_table
                old_id = session.connection().scalar(
                    select(child_table.c[fk_name]).where(
                        *[
                            col == value
                            for col, value in zip(
                                state.mapper.primary_key, state.identity, strict=True
                            )
                        ]
                    )
                )
                if old_id is not None:
                    parent_keys.add((parent_cls, old_id))

        for parent_cls, parent_id in parent_keys:
            parent = session.get(parent_cls, parent_id)
            if parent is not None:
                parent_objects.add(parent)

        for parent in parent_objects:
            if inspect(parent).persistent and parent not in session.deleted:
                # A SQL expression guarantees a real UPDATE even when the clock
                # precision would otherwise produce an unchanged datetime value.
                # version_id_col performs the increment and stale-version check.
                parent.updated_at = func.current_timestamp()
        for parent in candidates:
            config = _VERSIONED_CHILDREN.get(type(parent))
            if config is None:
                continue
            if parent not in session.deleted and (
                parent not in session.dirty
                or not session.is_modified(parent, include_collections=False)
            ):
                continue

            child_model, fk_name = config
            children = session.scalars(
                select(child_model).where(getattr(child_model, fk_name) == parent.id)
            ).all()
            for child in children:
                if child not in session.deleted:
                    child.updated_at = func.current_timestamp()


def register_model_events() -> None:
    """Install once; importing app.models does not open a database connection."""
    if not event.contains(Session, "before_flush", _touch_versioned_parents):
        event.listen(Session, "before_flush", _touch_versioned_parents)

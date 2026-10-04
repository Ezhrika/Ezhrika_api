"""Проверки версий реальных ORM-моделей на изолированной тестовой БД."""
import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from sqlalchemy.orm.exc import StaleDataError

from app import models


def test_consultation_update_increments_version(db_session, consultation):
    old_version = consultation.version
    consultation.title = "Новое название"
    db_session.commit()
    assert consultation.version == old_version + 1


def test_noop_consultation_preserves_version(db_session, consultation):
    old_version = consultation.version
    consultation.title = consultation.title
    db_session.commit()
    assert consultation.version == old_version


@pytest.mark.parametrize("operation", ["add", "delete"])
def test_allowed_group_updates_consultation_version(db_session, consultation, group, operation):
    # allowed_groups — viewonly; запись выполняется через association object.
    link = models.ConsultationAllowedGroup(consultation_id=consultation.id, group_id=group.id)
    if operation == "delete":
        db_session.add(link)
        db_session.commit()
    old_version = consultation.version
    if operation == "add":
        consultation.allowed_group_links.append(link)
    else:
        db_session.delete(link)
    db_session.commit()
    assert consultation.version == old_version + 1
    assert (group in consultation.allowed_groups) == (operation == "add")


@pytest.mark.parametrize("multiple", [False, True])
def test_reservation_updates_consultations_version(db_session, consultation, multiple):
    reservation = consultation.reservation
    consultations = [consultation]
    if multiple:
        other = models.Consultation(
            teacher_id=consultation.teacher_id, reservation_id=reservation.id,
            created_by=consultation.created_by, title="Вторая консультация",
            format="onsite", max_students=5,
            starts_at=consultation.starts_at, ends_at=consultation.ends_at,
        )
        db_session.add(other)
        db_session.commit()
        consultations.append(other)
    room = models.Classroom(building_id=1, name="102", capacity=30)
    db_session.add(room)
    db_session.commit()
    old_reservation_version = reservation.version
    old_versions = [obj.version for obj in consultations]
    reservation.classroom_id = room.id
    db_session.commit()
    assert reservation.version == old_reservation_version + 1
    assert [obj.version for obj in consultations] == [v + 1 for v in old_versions]


def test_noop_reservation_preserves_versions(db_session, consultation):
    reservation = consultation.reservation
    old_versions = reservation.version, consultation.version
    reservation.classroom_id = reservation.classroom_id
    db_session.commit()
    assert (reservation.version, consultation.version) == old_versions


@pytest.mark.parametrize("child_class", [models.TeacherAvailabilityRule, models.TeacherAvailabilityException])
@pytest.mark.parametrize("operation", ["update", "delete", "noop"])
def test_availability_changes_settings_version(db_session, child_class, operation):
    settings = db_session.get(models.TeacherSchedulingSettings, 1)
    child = db_session.get(child_class, 1)
    old_version = settings.version
    if operation == "delete":
        db_session.delete(child)
    else:
        child.is_active = child.is_active if operation == "noop" else False
    db_session.commit()
    assert settings.version == old_version + (operation != "noop")


def test_multiple_changes_increment_once_per_flush(db_session):
    with db_session.no_autoflush:
        settings = db_session.get(models.TeacherSchedulingSettings, 1)
        old_version = settings.version
        settings.buffer_minutes = 5
        db_session.get(models.TeacherAvailabilityRule, 1).is_active = False
        db_session.get(models.TeacherAvailabilityException, 1).is_active = False
    db_session.commit()
    assert settings.version == old_version + 1


def test_invalid_availability_rolls_back_version(db_session):
    settings = db_session.get(models.TeacherSchedulingSettings, 1)
    old_version = settings.version
    db_session.get(models.TeacherAvailabilityRule, 1).day_of_week = 9
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()
    assert settings.version == old_version


def test_stale_consultation_update_is_rejected(populated_engine):
    with Session(populated_engine) as first, Session(populated_engine) as second:
        current = first.get(models.Consultation, 1)
        stale = second.get(models.Consultation, 1)
        current.title = "Сохранённое изменение"
        first.commit()
        stale.title = "Устаревшее изменение"
        with pytest.raises(StaleDataError):
            second.commit()
        second.rollback()
        assert stale.title == "Сохранённое изменение"

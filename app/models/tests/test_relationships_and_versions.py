"""ORM graph persistence, ownership safety, timestamps and optimistic locking."""
import datetime as dt

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from sqlalchemy.orm.exc import StaleDataError

from app import models

START = dt.datetime(2026, 10, 5, 8, 0, tzinfo=dt.timezone.utc)
END = START + dt.timedelta(minutes=90)


def test_create_account_teacher_student_graph_from_relationships(engine):
    with Session(engine) as session:
        teacher_person = models.Person(full_name="Одинаковое ФИО")
        student_person = models.Person(full_name="Одинаковое ФИО")
        user = models.User(person=teacher_person, login="teacher", password_hash="test-only")
        user.roles.append(models.UserRoleAssignment(role=models.UserRole.teacher))
        teacher = models.Teacher(person=teacher_person)
        student = models.Student(person=student_person)
        subject = models.Subject(name="Предмет")
        teacher.subject_links.append(models.TeacherSubject(subject=subject))
        session.add_all([user, teacher, student])
        session.commit()
        assert teacher.person.user is user
        assert student.person.user is None
        assert teacher.id is not None and student.id is not None
        assert teacher.person_id != student.person_id
        assert teacher.subjects == [subject]
        assert user.roles[0].role == "teacher"


def test_teacher_reservation_and_consultation_graph(session):
    teacher = session.get(models.Teacher, 1)
    reservation = session.get(models.RoomReservation, 1)
    consultation = session.get(models.Consultation, 1)
    assert consultation.teacher is teacher
    assert consultation.reservation is reservation
    assert reservation.consultations == [consultation]
    assert consultation.allowed_groups[0].id == 1
    assert consultation.registrations[0].student.person.full_name == "Студент"
    assert consultation.video_meeting.provider == "test"
    assert teacher.subjects[0].name == "Алгоритмы"
    assert session.get(models.TimetableEvent, 1).teachers == [teacher]


def test_composite_relationship_does_not_silently_change_teacher(session):
    other_reservation = models.RoomReservation(
        teacher_id=2, classroom_id=1, period_slot_id=1, created_by=1
    )
    session.add(other_reservation)
    session.commit()
    consultation = session.get(models.Consultation, 1)
    consultation.reservation = other_reservation
    with pytest.raises(IntegrityError):
        session.flush()
    session.rollback()
    assert session.get(models.Consultation, 1).teacher_id == 1
    assert session.get(models.Consultation, 1).reservation_id == 1


def test_detaching_reservation_preserves_teacher(session):
    consultation = session.get(models.Consultation, 1)
    consultation.reservation = None
    session.commit()
    assert consultation.reservation_id is None
    assert consultation.teacher_id == 1
    assert consultation.status == "draft"


def test_same_teacher_reservation_relationship_can_be_reassigned(session):
    reservation = models.RoomReservation(
        teacher_id=1, classroom_id=1, period_slot_id=1, created_by=1
    )
    consultation = session.get(models.Consultation, 1)
    consultation.reservation = reservation
    session.add(reservation)
    session.commit()
    assert consultation.teacher_id == 1
    assert consultation.reservation_id == reservation.id


def test_import_relationship_does_not_change_source(session):
    link = session.get(models.ScheduleEventSource, (1, "event-1"))
    assert link.last_seen_import.source_id == 1
    link.last_seen_import = session.get(models.ScheduleImport, 2)
    with pytest.raises(IntegrityError):
        session.flush()
    session.rollback()
    assert session.get(models.ScheduleEventSource, (1, "event-1")).source_id == 1


def test_import_can_be_reassigned_within_same_source(session):
    new_import = models.ScheduleImport(source_id=1)
    link = session.get(models.ScheduleEventSource, (1, "event-1"))
    link.last_seen_import = new_import
    session.add(new_import)
    session.commit()
    assert link.last_seen_import_id == new_import.id
    assert link.source_id == 1


def test_deleting_referenced_parent_does_not_null_children(session):
    person = session.get(models.Person, 1)
    assert person.user is not None  # Load nullable-looking inverse relationship.
    assert person.teacher is not None
    session.delete(person)
    with pytest.raises(IntegrityError):
        session.flush()
    session.rollback()
    assert session.get(models.Teacher, 1).person_id == 1


@pytest.mark.parametrize("class_name,pk,field,value", [
    ("TimetableEvent", 1, "title", "Новое название"),
    ("RoomReservation", 1, "status", "released"),
    ("Consultation", 1, "title", "Новое название"),
    ("TeacherSchedulingSettings", 1, "buffer_minutes", 5),
])
def test_version_increments_on_orm_update(session, class_name, pk, field, value):
    obj = session.get(getattr(models, class_name), pk)
    initial = obj.version
    setattr(obj, field, value)
    session.commit()
    assert obj.version == initial + 1


def test_updated_at_changes_on_orm_update(session):
    obj = session.get(models.ConsultationRequest, 1)
    obj.updated_at = dt.datetime(2000, 1, 1, tzinfo=dt.timezone.utc)
    session.commit()
    obj.message = "Новый вопрос"
    session.commit()
    assert obj.updated_at.year > 2000


def test_stale_orm_updates_are_rejected(populated_engine):
    with Session(populated_engine) as first, Session(populated_engine) as second:
        left = first.get(models.Consultation, 1)
        right = second.get(models.Consultation, 1)
        left.title = "Первое изменение"
        first.commit()
        right.title = "Устаревшее изменение"
        with pytest.raises(StaleDataError):
            second.commit()
        second.rollback()
        assert second.get(models.Consultation, 1).title == "Первое изменение"


@pytest.mark.parametrize("class_name,field,value", [
    ("TeacherAvailabilityRule", "is_active", False),
    ("TeacherAvailabilityException", "is_active", False),
])
def test_availability_child_updates_bump_parent_version(session, class_name, field, value):
    settings = session.get(models.TeacherSchedulingSettings, 1)
    initial = settings.version
    child = session.get(getattr(models, class_name), 1)
    setattr(child, field, value)
    session.commit()
    assert settings.version == initial + 1


def test_multiple_child_changes_touch_parent_once_per_flush(session):
    with session.no_autoflush:
        settings = session.get(models.TeacherSchedulingSettings, 1)
        initial = settings.version
        settings.buffer_minutes = 10
        rule = session.get(models.TeacherAvailabilityRule, 1)
        exception = session.get(models.TeacherAvailabilityException, 1)
        rule.is_active = False
        exception.is_active = False
    session.commit()
    assert settings.version == initial + 1


def test_noop_child_assignment_does_not_increment_parent(session):
    settings = session.get(models.TeacherSchedulingSettings, 1)
    initial = settings.version
    rule = session.get(models.TeacherAvailabilityRule, 1)
    rule.is_active = rule.is_active
    session.commit()
    assert settings.version == initial


def test_new_availability_rule_bumps_existing_settings(session):
    settings = session.get(models.TeacherSchedulingSettings, 1)
    initial = settings.version
    settings.availability_rules.append(models.TeacherAvailabilityRule(
        kind="unavailable", day_of_week=2, all_day=True,
        valid_from=START.date(), confirmed_by=1,
    ))
    session.commit()
    assert settings.version == initial + 1


def test_new_settings_and_new_rule_can_be_inserted_together(engine):
    with Session(engine) as session:
        person = models.Person(full_name="Преподаватель")
        user = models.User(person=person, login="new-teacher")
        teacher = models.Teacher(person=person)
        settings = models.TeacherSchedulingSettings(teacher=teacher, timezone="Europe/Moscow")
        rule = models.TeacherAvailabilityRule(
            settings=settings, confirmer=user, kind="available",
            day_of_week=1, all_day=True, valid_from=START.date(),
        )
        session.add(rule)
        session.commit()
        assert rule.teacher_id == teacher.id
        assert settings.version == 1


@pytest.mark.parametrize("use_relationship", [False, True])
def test_reparenting_touches_old_and_new_settings(session, use_relationship):
    old_settings = session.get(models.TeacherSchedulingSettings, 1)
    new_settings = session.get(models.TeacherSchedulingSettings, 2)
    old_version, new_version = old_settings.version, new_settings.version
    rule = session.get(models.TeacherAvailabilityRule, 1)
    if use_relationship:
        rule.settings = new_settings
    else:
        session.expire(rule, ["teacher_id"])
        rule.teacher_id = 2
    session.commit()
    assert rule.teacher_id == 2
    assert old_settings.version == old_version + 1
    assert new_settings.version == new_version + 1


def test_deleting_availability_rule_touches_settings(session):
    settings = session.get(models.TeacherSchedulingSettings, 1)
    initial = settings.version
    session.delete(session.get(models.TeacherAvailabilityRule, 1))
    session.commit()
    assert settings.version == initial + 1


def test_constraint_failure_rolls_back_parent_touch(session):
    settings = session.get(models.TeacherSchedulingSettings, 1)
    initial = settings.version
    rule = session.get(models.TeacherAvailabilityRule, 1)
    rule.day_of_week = 9
    with pytest.raises(IntegrityError):
        session.flush()
    session.rollback()
    assert settings.version == initial


def test_stale_settings_block_child_update(populated_engine):
    with Session(populated_engine) as first, Session(populated_engine) as second:
        initial_settings = first.get(models.TeacherSchedulingSettings, 1)
        stale_settings = second.get(models.TeacherSchedulingSettings, 1)
        rule = second.get(models.TeacherAvailabilityRule, 1)
        initial_settings.buffer_minutes = 5
        first.commit()
        rule.is_active = False
        with pytest.raises(StaleDataError):
            second.commit()
        second.rollback()
        assert second.get(models.TeacherAvailabilityRule, 1).is_active is True


@pytest.mark.parametrize("child_class,parent_class,pk", [
    (models.TimetableEventTeacher, models.TimetableEvent, (1, 1)),
    (models.TimetableEventGroup, models.TimetableEvent, (1, 1)),
    (models.ConsultationAllowedGroup, models.Consultation, (1, 1)),
])
def test_membership_deletion_bumps_parent_version(session, child_class, parent_class, pk):
    parent = session.get(parent_class, 1)
    initial = parent.version
    session.delete(session.get(child_class, pk))
    session.commit()
    assert parent.version == initial + 1

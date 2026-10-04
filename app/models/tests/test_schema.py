"""Exact metadata contract, SQL compilation and invalid-write regression tests."""
import datetime as dt
import importlib
import json
from pathlib import Path

import pytest
from sqlalchemy import CheckConstraint, ForeignKeyConstraint, UniqueConstraint, inspect, select
from sqlalchemy.dialects import postgresql
from sqlalchemy.exc import IntegrityError, SAWarning
from sqlalchemy.orm import configure_mappers
from sqlalchemy.schema import CreateIndex, CreateTable

from app import models

CONTRACT = json.loads((Path(__file__).parent / "schema_contract.json").read_text(encoding="utf-8"))
START = dt.datetime(2026, 10, 5, 8, 0, tzinfo=dt.timezone.utc)
END = START + dt.timedelta(minutes=90)
TYPE_SQL = {
    "int": "INTEGER", "smallint": "SMALLINT", "text": "TEXT", "boolean": "BOOLEAN",
    "date": "DATE", "time": "TIME WITHOUT TIME ZONE", "timestamptz": "TIMESTAMP WITH TIME ZONE", "json": "JSON",
}


def test_package_has_exactly_the_target_tables():
    assert set(models.Base.metadata.tables) == set(CONTRACT)
    assert len(models.Base.registry.mappers) == 32


@pytest.mark.parametrize("name", CONTRACT)
def test_each_entity_has_its_own_models_module(name):
    module = importlib.import_module(f"app.models.{name}.models")
    mapped = [value for value in vars(module).values() if isinstance(value, type) and getattr(value, "__tablename__", None) == name]
    assert len(mapped) == 1
    cls = mapped[0]
    assert getattr(models, cls.__name__) is cls
    assert cls.metadata is models.Base.metadata


@pytest.mark.filterwarnings("error::sqlalchemy.exc.SAWarning")
def test_all_mappers_configure_without_warnings():
    configure_mappers()


@pytest.mark.parametrize("name,contract", CONTRACT.items())
def test_metadata_matches_dbml(name, contract):
    table = models.Base.metadata.tables[name]
    dialect = postgresql.dialect()
    assert list(table.columns.keys()) == [c["name"] for c in contract["columns"]]
    assert set(table.primary_key.columns.keys()) == {c["name"] for c in contract["columns"] if c["primary_key"]}
    for column in contract["columns"]:
        actual = table.c[column["name"]]
        assert actual.nullable == column["nullable"]
        expected_type = TYPE_SQL.get(column["type"], column["type"].upper())
        assert str(actual.type.compile(dialect=dialect)) == expected_type
        expected_default = column["default"]
        actual_default = str(actual.server_default.arg.compile(dialect=dialect)) if actual.server_default is not None else None
        assert actual_default == expected_default
        if column["name"] == "updated_at":
            assert actual.onupdate is not None
    actual_checks = {str(c.sqltext) for c in table.constraints if isinstance(c, CheckConstraint)}
    assert actual_checks == set(contract["checks"])
    expected_unique = {tuple(i["columns"]) for i in contract["indexes"] if i["kind"] == "unique"}
    expected_unique |= {(c["name"],) for c in contract["columns"] if c["unique"]}
    assert {tuple(c.columns.keys()) for c in table.constraints if isinstance(c, UniqueConstraint)} == expected_unique
    assert {tuple(i.columns.keys()) for i in table.indexes} == {tuple(i["columns"]) for i in contract["indexes"] if i["kind"] == "index"}
    expected_fk = {
        (tuple(fk["local"]), tuple(f'{fk["remote_table"]}.{c}' for c in fk["remote"]))
        for fk in contract["fks"]
    }
    actual_fk = {
        (tuple(fk.column_keys), tuple(e.target_fullname for e in fk.elements))
        for fk in table.constraints if isinstance(fk, ForeignKeyConstraint)
    }
    assert actual_fk == expected_fk
    # All names are safe for PostgreSQL's 63-byte identifier limit.
    for item in (*table.constraints, *table.indexes):
        if item.name:
            assert len(item.name.encode()) <= 63
    str(CreateTable(table).compile(dialect=dialect))
    for index in table.indexes:
        str(CreateIndex(index).compile(dialect=dialect))


@pytest.mark.parametrize("name", CONTRACT)
def test_can_select_every_table(populated_engine, name):
    table = models.Base.metadata.tables[name]
    with populated_engine.connect() as connection:
        assert connection.execute(select(table)).first() is not None


# Invalid mutation cases exercise every CHECK expression from the supplied DBML.
INVALID = [
    ("user_roles", {"role": "superuser"}),
    ("classrooms", {"capacity": 0}),
    ("period_slots", {"period_number": 0}),
    ("period_slots", {"ends_at": START}),
    ("timetable_events", {"kind": "consultation"}),
    ("timetable_events", {"status": "published"}),
    ("timetable_events", {"visibility": "public"}),
    ("timetable_events", {"version": 0}),
    ("timetable_events", {"ends_at": START}),
    ("timetable_events", {"visibility": "personal", "owner_user_id": None}),
    ("timetable_events", {"visibility": "shared", "owner_user_id": 1}),
    ("room_reservations", {"status": "cancelled"}),
    ("room_reservations", {"version": 0}),
    ("consultations", {"format": "phone"}),
    ("consultations", {"max_students": 0}),
    ("consultations", {"audience_mode": "everyone"}),
    ("consultations", {"status": "active"}),
    ("consultations", {"version": 0}),
    ("consultations", {"ends_at": START}),
    ("consultations", {"format": "online", "reservation_id": 1}),
    ("consultations", {"format": "onsite", "reservation_id": None, "status": "published"}),
    ("consultations", {"registration_opens_at": START - dt.timedelta(hours=1), "registration_closes_at": START - dt.timedelta(hours=1)}),
    ("consultations", {"registration_opens_at": START}),
    ("consultations", {"registration_closes_at": END}),
    ("consultation_registrations", {"status": "pending"}),
    ("consultation_registrations", {"status": "cancelled", "cancelled_at": None}),
    ("consultation_registrations", {"status": "confirmed", "cancelled_at": START}),
    ("consultation_overlap_permissions", {"approved_event_version": 0}),
    ("consultation_overlap_permissions", {"approved_consultation_version": 0}),
    ("consultation_requests", {"status": "confirmed"}),
    ("consultation_requests", {"status": "planned", "consultation_id": None}),
    ("teacher_scheduling_settings", {"default_duration_minutes": 0}),
    ("teacher_scheduling_settings", {"buffer_minutes": -1}),
    ("teacher_scheduling_settings", {"min_booking_notice_minutes": -1}),
    ("teacher_scheduling_settings", {"max_consultations_per_day": 0}),
    ("teacher_scheduling_settings", {"version": 0}),
    ("teacher_availability_rules", {"kind": "other"}),
    ("teacher_availability_rules", {"day_of_week": 0}),
    ("teacher_availability_rules", {"valid_to": START.date() - dt.timedelta(days=1)}),
    ("teacher_availability_rules", {"all_day": False, "start_time": None, "end_time": None}),
    ("teacher_availability_rules", {"all_day": True, "start_time": dt.time(8), "end_time": dt.time(9)}),
    ("teacher_availability_rules", {"all_day": False, "start_time": dt.time(9), "end_time": dt.time(8)}),
    ("teacher_availability_rules", {"kind": "preferred", "weight": None}),
    ("teacher_availability_rules", {"kind": "avoided", "weight": 11}),
    ("teacher_availability_rules", {"kind": "available", "weight": 1}),
    ("teacher_availability_exceptions", {"kind": "preferred"}),
    ("teacher_availability_exceptions", {"ends_at": START}),
    ("schedule_sources", {"kind": "api"}),
    ("schedule_sources", {"authority": "trusted"}),
    ("schedule_imports", {"status": "done"}),
    ("schedule_imports", {"coverage_from": START.date(), "coverage_to": START.date() - dt.timedelta(days=1)}),
    ("schedule_conflicts", {"kind": "other"}),
    ("schedule_conflicts", {"status": "pending"}),
    ("schedule_conflicts", {"reservation_id": None, "consultation_id": None}),
    ("schedule_conflicts", {"reservation_id": 1, "consultation_id": 1}),
    ("schedule_conflicts", {"reservation_id": None, "consultation_id": 1, "conflicting_consultation_id": 1}),
    ("ai_proposals", {"kind": "free_sql"}),
    ("ai_proposals", {"payload_version": 0}),
    ("ai_proposals", {"status": "confirmed"}),
]


@pytest.mark.parametrize("table,mutation", INVALID)
def test_invalid_check_values_are_rejected(populated_engine, table, mutation):
    table = models.Base.metadata.tables[table]
    with pytest.raises(IntegrityError), populated_engine.begin() as connection:
        connection.execute(table.update().values(**mutation))


@pytest.mark.parametrize("table,mutation", [
    ("consultations", {"teacher_id": 2}),
    ("schedule_event_sources", {"last_seen_import_id": 2}),
    ("consultations", {"reservation_id": 9999}),
    ("video_meetings", {"consultation_id": 9999}),
    ("teacher_availability_rules", {"teacher_id": 9999}),
])
def test_foreign_keys_are_enforced(populated_engine, table, mutation):
    table = models.Base.metadata.tables[table]
    with pytest.raises(IntegrityError), populated_engine.begin() as connection:
        connection.execute(table.update().values(**mutation))


@pytest.mark.parametrize("table,values", [
    ("user_roles", {"user_id": 1, "role": "teacher"}),
    ("consultation_registrations", {"consultation_id": 1, "student_id": 1}),
    ("classrooms", {"building_id": 1, "name": "101"}),
    ("video_meetings", {"consultation_id": 1, "provider": "another", "external_room_id": "another"}),
    ("users", {"person_id": 3, "login": "teacher"}),
    ("users", {"person_id": 1, "login": "different"}),
])
def test_duplicate_keys_are_rejected(populated_engine, table, values):
    table = models.Base.metadata.tables[table]
    with pytest.raises(IntegrityError), populated_engine.begin() as connection:
        connection.execute(table.insert().values(**values))


def test_optional_unknown_values_and_homonyms_are_not_coerced(session):
    room = session.get(models.Classroom, 1)
    room.capacity = None
    assert room.has_screen is None
    person = models.Person(full_name="Преподаватель")
    session.add(person)
    session.commit()
    assert person.id != 1
    assert room.capacity is None


def test_multiple_roles_and_notifications_without_dedupe_key(session):
    session.add(models.UserRoleAssignment(user_id=1, role=models.UserRole.admin))
    session.add_all([
        models.Notification(user_id=1, kind="test", message="one"),
        models.Notification(user_id=1, kind="test", message="two"),
    ])
    session.commit()
    assert {r.role for r in session.get(models.User, 1).roles} == {"teacher", "admin"}


def test_nonnull_json_rejects_python_none(session):
    session.get(models.AIProposal, 1).proposed_payload = None
    with pytest.raises(IntegrityError):
        session.flush()


def test_notification_dedupe_is_per_user(session):
    session.add_all([
        models.Notification(user_id=1, kind="test", message="one", dedupe_key="same"),
        models.Notification(user_id=2, kind="test", message="two", dedupe_key="same"),
    ])
    session.commit()
    session.add(models.Notification(user_id=1, kind="test", message="duplicate", dedupe_key="same"))
    with pytest.raises(IntegrityError):
        session.flush()

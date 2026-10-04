# -> tests/test_consult_registrations.py
"""Тесты записи на консультации.

Требует в conftest/refs студентов: добавь _student(client, name, group, login)
по образцу _teacher (account с role=student + POST /student) и создай в refs
пару студентов: refs["student"], refs["student2"].

Пути предполагаются приведёнными к /registrations:
  POST /registrations  (тело: consult_id, student_id)
  GET  /consult/{id}/registrations
  GET  /student/{id}/registrations
  DELETE /consult/{cid}/registrations/{sid}
Если у тебя POST висит на другом пути — поправь _REG.
"""
import pytest

from tests.conftest import _create  # поправь импорт под свой расклад

_REG = "/registrations"


@pytest.fixture()
def consult2(client, refs):
    """Консультация на 2 места в будущем (2126 год — чтобы 'уже началась' не срабатывало)."""
    row = _create(client, "/timetable", {
        "day": "2126-09-01",
        "slot": refs["slot"],
        "classroom": refs["classroom"],
        "teacher": refs["teacher"],
        "subject": refs["subject"],
        "kind": "consultation",
        "groups": [],
    })
    return _create(client, "/consult", {"timetable": row, "max_students": 2})


@pytest.fixture()
def consult_past(client, refs):
    """Консультация, которая уже началась (вчерашний день)."""
    row = _create(client, "/timetable", {
        "day": "2020-01-01",
        "slot": refs["slot2"],
        "classroom": refs["classroom"],
        "teacher": refs["teacher"],
        "subject": refs["subject"],
        "kind": "consultation",
        "groups": [],
    })
    return _create(client, "/consult", {"timetable": row, "max_students": 5})


def _reg(client, consult_id, student_id):
    return client.post(_REG, json={"consult_id": consult_id, "student_id": student_id})

def _create(client, url, json):
    resp = client.post(url, json=json)
    assert resp.status_code == 201, f"POST {url} -> {resp.status_code}: {resp.text}"
    return resp.json()["id"]


def _teacher(client, name, faculty, login):
    acc = _create(client, "/account", {
        "login": login,
        "password": "test1234",
        "role": "teacher",
    })
    return _create(client, "/teachers", {
        "name": name,
        "faculty": faculty,
        "user_id": acc,
    })


@pytest.fixture()
def refs(client):
    faculty = _create(client, "/faculty", {"name": "ФИТ"})
    corpus = _create(client, "/corpus", {"name": "Главный"})
    ctype = _create(client, "/classroom_type", {"name": "Лекционная"})
    classroom = _create(client, "/classroom",
                        {"name": "301", "corpus": corpus, "capacity": 60, "type": ctype})
    classroom2 = _create(client, "/classroom",
                         {"name": "302", "corpus": corpus, "capacity": 30, "type": ctype})
    slot = _create(client, "/slot", {"number": 1, "start_time": "09:00", "end_time": "10:30"})
    slot2 = _create(client, "/slot", {"number": 2, "start_time": "10:40", "end_time": "12:10"})
    subject = _create(client, "/subject", {"name": "Матанализ", "faculty": faculty})
    group = _create(client, "/student_group", {"name": "ИВТ-21"})
    teacher = _teacher(client, "Иванов И.И.", faculty, "ivanov")
    teacher2 = _teacher(client, "Петров П.П.", faculty, "petrov")
    student = _student(client, "Смирнов А.А.", group, "smirnov")
    student2 = _student(client, "Кузнецова М.М.", group, "kuznetsova")
    return {
        "classroom": classroom, "classroom2": classroom2,
        "slot": slot, "slot2": slot2,
        "subject": subject, "teacher": teacher, "teacher2": teacher2,
        "group": group,
        "student2" :student2,"student":student
    }

def _student(client, name, group, login):
    acc = _create(client, "/account", {
        "login": login, "password": "test1234", "role": "student",
    })
    return _create(client, "/students", {
        "name": name, "student_group": group, "user_id": acc,
    })
def _payload(refs, **overrides):
    # Ключи здесь — это поля схемы TimetableCreate, а не имена роутов!
    # Роут может называться /teachers, но поле в схеме — teacher.
    payload = {
        "day": "2026-09-01",
        "slot": refs["slot"],
        "classroom": refs["classroom"],
        "teacher": refs["teacher"],
        "subject": refs["subject"],
        "kind": "lecture",
        "groups": [refs["group"]],
    }
    payload.update(overrides)
    return payload


def test_register(client, refs, consult2):
    resp = _reg(client, consult2, refs["student"])
    assert resp.status_code == 201
    body = resp.json()
    assert body["consult_id"] == consult2
    assert body["student_id"] == refs["student"]
    assert body["registration_time"] is not None  # время проставила БД


def test_register_missing_consult_404(client, refs):
    assert _reg(client, 999999, refs["student"]).status_code == 404


def test_register_missing_student_404(client, refs, consult2):
    assert _reg(client, consult2, 999999).status_code == 404


def test_register_twice_409(client, refs, consult2):
    assert _reg(client, consult2, refs["student"]).status_code == 201
    resp = _reg(client, consult2, refs["student"])
    assert resp.status_code == 409


def test_capacity_full_409(client, refs, consult2):
    """max_students=2: третий не влезает."""
    student3 = _student_extra(client, refs)
    assert _reg(client, consult2, refs["student"]).status_code == 201
    assert _reg(client, consult2, refs["student2"]).status_code == 201
    resp = _reg(client, consult2, student3)
    assert resp.status_code == 409
    assert "Мест" in resp.json()["detail"]


def test_capacity_frees_after_unregister(client, refs, consult2):
    """Отписка освобождает место."""
    student3 = _student_extra(client, refs)
    _reg(client, consult2, refs["student"])
    _reg(client, consult2, refs["student2"])
    assert client.delete(f"/consult/{consult2}{_REG}/{refs['student']}").status_code == 204
    assert _reg(client, consult2, student3).status_code == 201


def test_list_by_consult(client, refs, consult2):
    _reg(client, consult2, refs["student"])
    _reg(client, consult2, refs["student2"])
    resp = client.get(f"/consult/{consult2}/reg")
    assert resp.status_code == 200
    assert len(resp.json()) == 2


def test_list_by_consult_missing_404(client, refs):
    assert client.get(f"/consult/999999{_REG}").status_code == 404


def test_list_by_student(client, refs, consult2, consult_past):
    """Студент видит свои записи; проверяет и _check_student (id студента != id консультации)."""
    _reg(client, consult2, refs["student"])
    resp = client.get(f"/students/{refs['student']}/reg")
    assert resp.status_code == 200
    rows = resp.json()
    assert len(rows) == 1
    assert rows[0]["consult_id"] == consult2


def test_list_by_student_missing_404(client, refs):
    assert client.get(f"/students/999999{_REG}").status_code == 404


def test_unregister(client, refs, consult2):
    _reg(client, consult2, refs["student"])
    assert client.delete(f"/consult/{consult2}{_REG}/{refs['student']}").status_code == 204
    assert client.get(f"/consult/{consult2}/reg").json() == []


def test_unregister_missing_404(client, refs, consult2):
    assert client.delete(f"/consult/{consult2}{_REG}/{refs['student']}").status_code == 404


def test_unregister_after_start_409(client, refs, consult_past):
    """Запись на прошедшую консультацию создать можно (пока не запрещали),
    а вот отписаться от начавшейся — нельзя."""
    assert _reg(client, consult_past, refs["student"]).status_code == 201
    resp = client.delete(f"/consult/{consult_past}{_REG}/{refs['student']}")
    assert resp.status_code == 409
    assert "началась" in resp.json()["detail"]


def _student_extra(client, refs):
    """Третий студент для тестов вместимости."""
    acc = _create(client, "/account", {
        "login": "student3", "password": "test1234", "role": "student",
    })
    return _create(client, "/students", {
        "name": "Сидоров С.С.", "student_group": refs["group"], "user_id": acc,
    })
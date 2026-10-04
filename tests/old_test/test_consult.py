# -> tests/test_consult.py
"""Тесты /consult.

Использует те же хелперы, что test_timetable. Если _create/_teacher/refs у тебя
ещё живут внутри test_timetable.py — самое время вынести их в conftest.py,
чтобы оба файла брали фикстуру оттуда (фикстуры из conftest видны всем тестам
автоматически). Здесь предполагается, что refs доступна как фикстура.
"""
import pytest


def _create(client, url, json):
    resp = client.post(url, json=json)
    assert resp.status_code == 201, f"POST {url} -> {resp.status_code}: {resp.text}"
    return resp.json()["id"]
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
    return {
        "classroom": classroom, "classroom2": classroom2,
        "slot": slot, "slot2": slot2,
        "subject": subject, "teacher": teacher, "teacher2": teacher2,
        "group": group,
    }


@pytest.fixture()
def tt(client, refs):
    """Три строки расписания с разными kind + маленький кабинет."""
    def make_row(kind, slot, classroom=None):
        return _create(client, "/timetable", {
            "day": "2026-09-01",
            "slot": slot,
            "classroom": classroom or refs["classroom"],   # capacity=60
            "teacher": refs["teacher"],
            "subject": refs["subject"],
            "kind": kind,
            "groups": [],
        })

    consultation_row = make_row("consultation", refs["slot"])
    practice_row = make_row("practice", refs["slot2"])
    # третий слот под лекцию
    slot3 = _create(client, "/slot", {"number": 3, "start_time": "12:40", "end_time": "14:10"})
    lecture_row = make_row("lecture", slot3)
    # маленький кабинет (capacity=30 из refs["classroom2"]) в четвёртом слоте
    slot4 = _create(client, "/slot", {"number": 4, "start_time": "14:20", "end_time": "15:50"})
    small_room_row = _create(client, "/timetable", {
        "day": "2026-09-01", "slot": slot4, "classroom": refs["classroom2"],
        "teacher": refs["teacher"], "subject": refs["subject"],
        "kind": "consultation", "groups": [],
    })
    return {
        "consultation": consultation_row,
        "practice": practice_row,
        "lecture": lecture_row,
        "small_room": small_room_row,   # кабинет на 30
    }


def test_create_on_consultation_row(client, tt):
    resp = client.post("/consult", json={
        "name": "Разбор задач", "timetable": tt["consultation"], "max_students": 10,
    })
    assert resp.status_code == 201
    body = resp.json()
    # ловит наследование ConsultOut от неправильной базы:
    assert body["timetable"] == tt["consultation"]
    assert body["max_students"] == 10
    assert body["name"] == "Разбор задач"


def test_create_on_practice_row(client, tt):
    resp = client.post("/consult", json={
        "timetable": tt["practice"], "max_students": 5,
    })
    assert resp.status_code == 201


def test_name_is_optional(client, tt):
    resp = client.post("/consult", json={
        "timetable": tt["consultation"], "max_students": 10,
    })
    assert resp.status_code == 201
    assert resp.json()["name"] is None


def test_lecture_row_rejected_422(client, tt):
    resp = client.post("/consult", json={
        "timetable": tt["lecture"], "max_students": 10,
    })
    assert resp.status_code == 422


def test_missing_timetable_404(client, tt):
    resp = client.post("/consult", json={
        "timetable": 999999, "max_students": 10,
    })
    assert resp.status_code == 404


def test_duplicate_on_row_409(client, tt):
    ok = client.post("/consult", json={"timetable": tt["consultation"], "max_students": 10})
    assert ok.status_code == 201
    resp = client.post("/consult", json={"timetable": tt["consultation"], "max_students": 5})
    assert resp.status_code == 409


def test_capacity_exceeded_422(client, tt):
    """small_room — кабинет на 30 мест."""
    resp = client.post("/consult", json={
        "timetable": tt["small_room"], "max_students": 31,
    })
    assert resp.status_code == 422
    assert "30" in resp.json()["detail"]


def test_capacity_boundary_ok(client, tt):
    """Ровно по вместимости — можно."""
    resp = client.post("/consult", json={
        "timetable": tt["small_room"], "max_students": 30,
    })
    assert resp.status_code == 201


def test_zero_max_students_422(client, tt):
    resp = client.post("/consult", json={
        "timetable": tt["consultation"], "max_students": 0,
    })
    assert resp.status_code == 422


def test_put_self_ok(client, tt):
    cid = _create(client, "/consult", {"timetable": tt["consultation"], "max_students": 10})
    resp = client.put(f"/consult/{cid}", json={
        "name": "Новое имя", "timetable": tt["consultation"], "max_students": 15,
    })
    assert resp.status_code == 200
    assert resp.json()["max_students"] == 15


def test_put_onto_taken_row_409(client, tt):
    _create(client, "/consult", {"timetable": tt["consultation"], "max_students": 10})
    cid = _create(client, "/consult", {"timetable": tt["practice"], "max_students": 10})
    resp = client.put(f"/consult/{cid}", json={
        "timetable": tt["consultation"], "max_students": 10,
    })
    assert resp.status_code == 409


def test_get_list_delete(client, tt):
    cid = _create(client, "/consult", {"timetable": tt["consultation"], "max_students": 10})
    assert client.get(f"/consult/{cid}").status_code == 200
    assert len(client.get("/consult").json()) == 1
    assert client.delete(f"/consult/{cid}").status_code == 204
    assert client.get(f"/consult/{cid}").status_code == 404
# -> tests/test_timetable.py
"""Тесты /timetable.

_create — только для фикстур (требует 201, возвращает id).
В самих тестах — client.post: тестам нужен Response со статусом и телом.
"""
import pytest


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


def test_create(client, refs):
    resp = client.post("/timetable", json=_payload(refs))
    assert resp.status_code == 201
    body = resp.json()
    assert body["kind"] == "lecture"
    assert body["groups"] == [refs["group"]]


def test_create_without_groups(client, refs):
    resp = client.post("/timetable", json=_payload(refs, groups=[]))
    assert resp.status_code == 201
    assert resp.json()["groups"] == []


def test_bad_refs_return_404(client, refs):
    assert client.post("/timetable", json=_payload(refs, slot=999999)).status_code == 404
    assert client.post("/timetable", json=_payload(refs, teacher=999999)).status_code == 404
    assert client.post("/timetable", json=_payload(refs, groups=[999999])).status_code == 404


def test_bad_kind_returns_422(client, refs):
    assert client.post("/timetable", json=_payload(refs, kind="party")).status_code == 422


def test_classroom_conflict_409(client, refs):
    """Тот же кабинет, день, слот — другой препод -> кабинет занят."""
    assert client.post("/timetable", json=_payload(refs)).status_code == 201
    resp = client.post("/timetable", json=_payload(refs, teacher=refs["teacher2"]))
    assert resp.status_code == 409
    assert "Кабинет" in resp.json()["detail"]


def test_teacher_conflict_409(client, refs):
    """Тот же препод, день, слот — другой кабинет -> преподаватель занят."""
    assert client.post("/timetable", json=_payload(refs)).status_code == 201
    resp = client.post("/timetable", json=_payload(refs, classroom=refs["classroom2"]))
    assert resp.status_code == 409
    assert "Преподаватель" in resp.json()["detail"]


def test_same_classroom_other_slot_ok(client, refs):
    assert client.post("/timetable", json=_payload(refs)).status_code == 201
    resp = client.post("/timetable", json=_payload(refs, slot=refs["slot2"]))
    assert resp.status_code == 201


def test_same_classroom_other_day_ok(client, refs):
    assert client.post("/timetable", json=_payload(refs)).status_code == 201
    resp = client.post("/timetable", json=_payload(refs, day="2026-09-02"))
    assert resp.status_code == 201


def test_put_self_no_conflict(client, refs):
    """PUT самого себя без изменений не должен ловить 409 (exclude_id)."""
    tid = _create(client, "/timetable", _payload(refs))
    resp = client.put(f"/timetable/{tid}", json=_payload(refs))
    assert resp.status_code == 200


def test_put_into_taken_slot_409(client, refs):
    _create(client, "/timetable", _payload(refs))
    tid = _create(client, "/timetable", _payload(refs, slot=refs["slot2"]))
    resp = client.put(f"/timetable/{tid}", json=_payload(refs))
    assert resp.status_code == 409


def test_put_replaces_groups(client, refs):
    tid = _create(client, "/timetable", _payload(refs))
    resp = client.put(f"/timetable/{tid}", json=_payload(refs, groups=[]))
    assert resp.status_code == 200
    assert resp.json()["groups"] == []


def test_filters(client, refs):
    _create(client, "/timetable", _payload(refs))
    _create(client, "/timetable", _payload(refs, day="2026-09-02", teacher=refs["teacher2"]))

    resp = client.get("/timetable", params={"day": "2026-09-01"})
    assert len(resp.json()) == 1

    resp = client.get("/timetable", params={"teacher": refs["teacher2"]})
    assert len(resp.json()) == 1

    resp = client.get("/timetable", params={"classroom": refs["classroom"]})
    assert len(resp.json()) == 2


def test_delete(client, refs):
    tid = _create(client, "/timetable", _payload(refs))
    assert client.delete(f"/timetable/{tid}").status_code == 204
    assert client.get(f"/timetable/{tid}").status_code == 404
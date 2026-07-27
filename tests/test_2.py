"""Smoke-тест CRUD для teacher — то же, что ты тыкал руками в /docs, но кодом.

Проверяет полный цикл: создать -> прочитать -> обновить -> удалить,
плюс граничные случаи (404 на несуществующем, 422 на кривом типе).
"""
from app import models


def seed_deps(db_session):
    """Teacher ссылается на account и faculty — создадим их заранее."""
    db_session.add(models.Account(
        login="t_login", password_hash="x", role=models.UserRole.teacher
    ))
    db_session.add(models.Faculty(name="ИМИТ"))
    db_session.commit()


def test_teacher_crud(client, db_session):
    seed_deps(db_session)

    # POST — создать
    r = client.post("/teachers", json={"name": "Иванов", "faculty": 1, "user_id": 1})
    assert r.status_code == 201
    created = r.json()
    assert created["name"] == "Иванов"
    assert "id" in created
    assert "password_hash" not in created   # лишнее наружу не утекло
    tid = created["id"]

    # GET список — наш преподаватель там
    r = client.get("/teachers")
    assert r.status_code == 200
    assert any(t["id"] == tid for t in r.json())

    # GET один — совпадает
    r = client.get(f"/teachers/{tid}")
    assert r.status_code == 200
    assert r.json()["name"] == "Иванов"

    # PUT — обновить
    r = client.put(f"/teachers/{tid}", json={"name": "Петров", "faculty": 1, "user_id": 1})
    assert r.status_code == 200
    assert r.json()["name"] == "Петров"

    # DELETE — удалить
    r = client.delete(f"/teachers/{tid}")
    assert r.status_code == 204

    # его больше нет
    r = client.get(f"/teachers/{tid}")
    assert r.status_code == 404


def test_teacher_not_found(client, db_session):
    r = client.get("/teachers/999")
    assert r.status_code == 404


def test_teacher_bad_type(client, db_session):
    # /teachers/abc — FastAPI сам отбракует по типу пути
    r = client.get("/teachers/abc")
    assert r.status_code == 422
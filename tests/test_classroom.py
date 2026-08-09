# -> tests/test_classroom.py
"""Тесты /classroom.

Предполагает фикстуру client и существующие CRUD-роуты /corpus, /classroom_type,
/faculty (создание с телом {"name": ...}). Если префиксы у тебя другие — поправь
в хелперах ниже.
"""
import pytest


@pytest.fixture()
def refs(client):
    """Создаёт корпус, тип кабинета и факультет, возвращает их id."""
    corpus_id = client.post("/corpus", json={"name": "Главный корпус"}).json()["id"]
    type_id = client.post("/classroom_type", json={"name": "Компьютерная"}).json()["id"]
    faculty_id = client.post("/faculty", json={"name": "ФИТ"}).json()["id"]
    return {"corpus": corpus_id, "type": type_id, "faculty": faculty_id}


def _payload(refs, **overrides):
    payload = {
        "name": "301а",
        "corpus": refs["corpus"],
        "capacity": 30,
        "type": refs["type"],
        "board": "marker",
        "screen": "projector",
        "faculty": refs["faculty"],
        "info": "Розетки у каждого места",
    }
    payload.update(overrides)
    return payload


def test_create_classroom(client, refs):
    resp = client.post("/classroom", json=_payload(refs))
    assert resp.status_code == 201
    body = resp.json()
    assert body["name"] == "301а"
    assert body["screen"] == "projector"
    assert isinstance(body["id"], int)


def test_create_minimal_defaults(client, refs):
    """board/faculty/info опциональны, screen по умолчанию none."""
    payload = {
        "name": "512",
        "corpus": refs["corpus"],
        "capacity": 100,
        "type": refs["type"],
    }
    resp = client.post("/classroom", json=payload)
    assert resp.status_code == 201
    body = resp.json()
    assert body["board"] is None
    assert body["screen"] == "none"
    assert body["faculty"] is None


def test_create_bad_corpus_returns_404(client, refs):
    resp = client.post("/classroom", json=_payload(refs, corpus=999999))
    assert resp.status_code == 404


def test_create_bad_type_returns_404(client, refs):
    resp = client.post("/classroom", json=_payload(refs, type=999999))
    assert resp.status_code == 404


def test_create_zero_capacity_returns_422(client, refs):
    resp = client.post("/classroom", json=_payload(refs, capacity=0))
    assert resp.status_code == 422


def test_create_bad_screen_returns_422(client, refs):
    resp = client.post("/classroom", json=_payload(refs, screen="hologram"))
    assert resp.status_code == 422


def test_duplicate_name_same_corpus_returns_409(client, refs):
    assert client.post("/classroom", json=_payload(refs)).status_code == 201
    resp = client.post("/classroom", json=_payload(refs, capacity=50))
    assert resp.status_code == 409


def test_same_name_other_corpus_is_ok(client, refs):
    assert client.post("/classroom", json=_payload(refs)).status_code == 201
    corpus2 = client.post("/corpus", json={"name": "Второй корпус"}).json()["id"]
    resp = client.post("/classroom", json=_payload(refs, corpus=corpus2))
    assert resp.status_code == 201


def test_list_filters(client, refs):
    client.post("/classroom", json=_payload(refs, name="101", capacity=20))
    client.post("/classroom", json=_payload(refs, name="102", capacity=80))

    resp = client.get("/classroom", params={"min_capacity": 50})
    assert resp.status_code == 200
    names = [c["name"] for c in resp.json()]
    assert names == ["102"]

    resp = client.get("/classroom", params={"corpus": refs["corpus"]})
    assert len(resp.json()) == 2


def test_get_by_id_and_404(client, refs):
    cid = client.post("/classroom", json=_payload(refs)).json()["id"]
    assert client.get(f"/classroom/{cid}").status_code == 200
    assert client.get("/classroom/999999").status_code == 404


def test_put_update(client, refs):
    cid = client.post("/classroom", json=_payload(refs)).json()["id"]
    resp = client.put(f"/classroom/{cid}", json=_payload(refs, name="301б", capacity=40))
    assert resp.status_code == 200
    assert resp.json()["name"] == "301б"
    assert resp.json()["capacity"] == 40


def test_put_to_taken_pair_returns_409(client, refs):
    client.post("/classroom", json=_payload(refs, name="201"))
    cid = client.post("/classroom", json=_payload(refs, name="202")).json()["id"]
    resp = client.put(f"/classroom/{cid}", json=_payload(refs, name="201"))
    assert resp.status_code == 409


def test_delete(client, refs):
    cid = client.post("/classroom", json=_payload(refs)).json()["id"]
    assert client.delete(f"/classroom/{cid}").status_code == 204
    assert client.get(f"/classroom/{cid}").status_code == 404
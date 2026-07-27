"""Один тест на всю простую четвёрку (faculty, corpus, group, classroom_type).

Раз у них одинаковая структура (id + name) и одинаковый CRUD, тест пишется
ОДИН и параметризуется: pytest прогонит его для каждой сущности из списка.
Добавил новую простую сущность — дописал строку в SIMPLE_ENTITIES.

Пока раскомментированы только те, чьи роутеры у тебя готовы. Как сделаешь
остальные — убери комментарии.
"""
import pytest
from random import choice
# (префикс пути, поле-имя) для каждой простой сущности
SIMPLE_ENTITIES = [
    "/faculty",
    "/corpus",
    "/student_group",
    "/classroom_type",
]


@pytest.mark.parametrize("prefix", SIMPLE_ENTITIES)
def test_simple_crud(client, db_session, prefix):
    # POST

    r = client.post(prefix, json={"name": "Тест"})
    assert r.status_code == 201, f"{prefix}: POST вернул {r.status_code}"
    obj = r.json()
    assert obj["name"] == "Тест"
    oid = obj["id"]

    # GET список
    r = client.get(prefix)
    assert r.status_code == 200
    assert any(x["id"] == oid for x in r.json())

    # GET один
    r = client.get(f"{prefix}/{oid}")
    assert r.status_code == 200

    # PUT
    r = client.put(f"{prefix}/{oid}", json={"name": "Изменённый"})
    assert r.status_code == 200
    assert r.json()["name"] == "Изменённый"

    # DELETE
    r = client.delete(f"{prefix}/{oid}")
    assert r.status_code == 204

    # больше нет
    r = client.get(f"{prefix}/{oid}")
    assert r.status_code == 404


@pytest.mark.parametrize("prefix", SIMPLE_ENTITIES)
def test_simple_not_found(client, db_session, prefix):
    r = client.get(f"{prefix}/999")
    assert r.status_code == 404
def test_entities_isolated(client, db_session):
    # 1. в каждую сущность кладём объект с ЕЁ узнаваемым именем
    created = {}
    for prefix in SIMPLE_ENTITIES:
        r = client.post(prefix, json={"name": f"marker{prefix}"})
        assert r.status_code == 201
        created[prefix] = r.json()["id"]

    # 2. читаем каждый по id — должно вернуться ЕГО имя, не чужое
    for prefix in SIMPLE_ENTITIES:
        r = client.get(f"{prefix}/{created[prefix]}")
        assert r.status_code == 200
        assert r.json()["name"] == f"marker{prefix}"

    # 3. в каждом списке — ровно один объект, и это его marker
    for prefix in SIMPLE_ENTITIES:
        r = client.get(prefix)
        names = [x["name"] for x in r.json()]
        assert names == [f"marker{prefix}"]   # только свой, чужих не видно
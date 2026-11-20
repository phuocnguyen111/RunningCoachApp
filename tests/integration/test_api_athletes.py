import pytest


@pytest.fixture
def groups(client):
    a = client.post("/api/groups", json={"name": "Nhóm A", "plan_id": "marathon_27w"}).get_json()["id"]
    b = client.post("/api/groups", json={"name": "Nhóm B", "plan_id": "5k_8w"}).get_json()["id"]
    return a, b


def test_names_differing_by_diacritics_are_distinct(client, groups):
    r1 = client.post("/api/athletes", json={"name": "Nguyễn Văn A", "group_id": groups[0]})
    r2 = client.post("/api/athletes", json={"name": "Nguyen Van A"})
    assert r1.status_code == 201 and r2.status_code == 201
    a1, a2 = r1.get_json(), r2.get_json()
    assert a1["id"] == "nguyen-van-a" and a2["id"] == "nguyen-van-a-2"
    assert "activities" not in a1
    names = {a["id"]: a["name"] for a in client.get("/api/athletes").get_json()}
    assert names == {"nguyen-van-a": "Nguyễn Văn A", "nguyen-van-a-2": "Nguyen Van A"}


def test_exact_duplicate_name_rejected(client):
    client.post("/api/athletes", json={"name": "Trần B"})
    r = client.post("/api/athletes", json={"name": " trần b "})
    assert r.status_code == 409


def test_move_and_remove_group(client, groups):
    a, b = groups
    aid = client.post("/api/athletes", json={"name": "Lê C", "group_id": a}).get_json()["id"]
    assert [x["id"] for x in client.get(f"/api/athletes?group_id={a}").get_json()] == [aid]

    r = client.patch(f"/api/athletes/{aid}", json={"group_id": b})
    assert r.status_code == 200 and r.get_json()["group_id"] == b
    assert client.get(f"/api/athletes?group_id={a}").get_json() == []
    counts = {g["id"]: g["athlete_count"] for g in client.get("/api/groups").get_json()}
    assert counts == {a: 0, b: 1}

    assert client.patch(f"/api/athletes/{aid}", json={"group_id": None}).get_json()["group_id"] is None


def test_athlete_validation(client):
    assert client.post("/api/athletes", json={"name": ""}).status_code == 400
    assert client.post("/api/athletes", json={"name": "X", "group_id": "nope"}).status_code == 400
    aid = client.post("/api/athletes", json={"name": "X"}).get_json()["id"]
    assert client.patch(f"/api/athletes/{aid}", json={"group_id": "nope"}).status_code == 400
    assert client.patch("/api/athletes/missing", json={"group_id": None}).status_code == 404

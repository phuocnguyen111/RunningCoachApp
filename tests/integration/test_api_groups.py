def _create(client, **kw):
    body = {"name": "Marathon Sub 4:30", "plan_id": "marathon_27w", "start_date": "2026-06-01"}
    body.update(kw)
    return client.post("/api/groups", json=body)


def test_create_and_list_group(client):
    r = _create(client)
    assert r.status_code == 201
    g = r.get_json()
    assert g["id"] == "marathon-sub-4-30" and g["plan_id"] == "marathon_27w"
    groups = client.get("/api/groups").get_json()
    assert [x["id"] for x in groups] == ["marathon-sub-4-30"]
    assert groups[0]["athlete_count"] == 0


def test_duplicate_name_gets_new_id(client):
    a = _create(client).get_json()
    b = _create(client).get_json()
    assert a["id"] != b["id"] and b["id"] == "marathon-sub-4-30-2"


def test_validation_errors(client):
    assert _create(client, name="  ").status_code == 400
    assert _create(client, plan_id="nope").status_code == 400
    assert _create(client, plan_id=None).status_code == 400
    r = _create(client, start_date="01/06/2026")
    assert r.status_code == 400 and "ngày" in r.get_json()["error"].lower()


def test_patch_group(client):
    gid = _create(client).get_json()["id"]
    r = client.patch(f"/api/groups/{gid}", json={"name": "Đổi tên", "plan_id": "5k_8w", "start_date": None, "notes": "ghi chú"})
    assert r.status_code == 200
    g = r.get_json()
    assert (g["id"], g["name"], g["plan_id"], g["start_date"], g["notes"]) == (gid, "Đổi tên", "5k_8w", None, "ghi chú")
    assert client.patch(f"/api/groups/{gid}", json={"plan_id": "nope"}).status_code == 400
    assert client.patch("/api/groups/missing", json={"name": "x"}).status_code == 404

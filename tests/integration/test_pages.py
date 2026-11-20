import io

import pytest


@pytest.fixture
def seeded(client, fixtures_dir):
    gid = client.post("/api/groups", json={"name": "Sub5", "plan_id": "marathon_27w",
                                            "start_date": "2026-06-01"}).get_json()["id"]
    aid = client.post("/api/athletes", json={"name": "Nguyễn Văn A", "group_id": gid}).get_json()["id"]
    ids = []
    for name, week, st in (("long_12k_2026-06-17.gpx", 3, "LONG"), ("easy_6k.gpx", 3, "EASY")):
        tok = client.post("/api/uploads", data={"athlete_id": aid, "file": (io.BytesIO((fixtures_dir / name).read_bytes()), name)},
                          content_type="multipart/form-data").get_json()["token"]
        saved = client.post(f"/api/uploads/{tok}/confirm", json={"items": [
            {"index": 0, "plan_id": "marathon_27w", "plan_week": week, "session_type": st}]}).get_json()["saved"]
        ids.append(saved[0]["id"])
    return aid, gid, ids


def test_summary_endpoint(client, seeded):
    aid, _, _ = seeded
    s = client.get(f"/api/athletes/{aid}/summary").get_json()
    assert s["total_sessions"] == 2 and s["total_km"] == pytest.approx(18.5, abs=0.1)
    assert s["weeks"][0]["week"] == 3
    assert client.get("/api/athletes/missing/summary").status_code == 404


def test_delete_activity_by_id(client, seeded):
    aid, _, (long_id, easy_id) = seeded
    r = client.delete(f"/api/athletes/{aid}/activities/{easy_id}")
    assert r.status_code == 200 and r.get_json() == {"ok": True, "removed_id": easy_id}
    s = client.get(f"/api/athletes/{aid}/summary").get_json()
    assert s["total_sessions"] == 1
    assert client.delete(f"/api/athletes/{aid}/activities/{easy_id}").status_code == 404


def test_athlete_page(client, seeded):
    aid, _, _ = seeded
    r = client.get(f"/athletes/{aid}")
    assert r.status_code == 200
    html = r.get_data(as_text=True)
    assert "Nguyễn Văn A" in html and "HR ≤ 148" in html
    assert client.get("/athletes/missing").status_code == 404


def test_empty_athlete_page(client):
    aid = client.post("/api/athletes", json={"name": "Mới"}).get_json()["id"]
    html = client.get(f"/athletes/{aid}").get_data(as_text=True)
    assert "Chưa có buổi tập" in html


def test_legacy_url_redirects(client, seeded):
    aid, _, _ = seeded
    r = client.get("/athlete/Nguyễn Văn A")
    assert r.status_code == 301 and r.headers["Location"].endswith(f"/athletes/{aid}")
    assert client.get("/athlete/Không Có").status_code == 404


def test_targets_survive_plan_removal_and_group_change(client, app, seeded):
    aid, _, _ = seeded
    other = client.post("/api/groups", json={"name": "5K", "plan_id": "5k_8w"}).get_json()["id"]
    client.patch(f"/api/athletes/{aid}", json={"group_id": other})
    app.extensions["coach"].catalog._plans.pop("marathon_27w")
    html = client.get(f"/athletes/{aid}").get_data(as_text=True)
    assert "HR ≤ 148" in html and "Long run 12 km" in html

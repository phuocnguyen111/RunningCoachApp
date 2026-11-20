import io

import pytest

from coach import create_app
from coach.config import Config

LONG = "long_12k_2026-06-17.gpx"


@pytest.fixture
def athlete(client):
    gid = client.post("/api/groups", json={"name": "Sub5", "plan_id": "marathon_27w",
                                            "start_date": "2026-06-01"}).get_json()["id"]
    return client.post("/api/athletes", json={"name": "Nguyễn Văn A", "group_id": gid}).get_json()["id"]


def upload(client, athlete_id, path=None, data=None, name=None):
    payload = data if data is not None else path.read_bytes()
    return client.post("/api/uploads", data={
        "athlete_id": athlete_id, "file": (io.BytesIO(payload), name or path.name),
    }, content_type="multipart/form-data")


def pending_dirs(base_dir):
    d = base_dir / "uploads" / "_pending"
    return list(d.iterdir()) if d.exists() else []


def test_preview_then_confirm(client, athlete, fixtures_dir, base_dir):
    r = upload(client, athlete, fixtures_dir / LONG)
    assert r.status_code == 200, r.get_json()
    prev = r.get_json()
    (item,) = prev["items"]
    assert (item["suggested_plan_id"], item["suggested_week"], item["suggested_session_type"]) == ("marathon_27w", 3, "LONG")
    assert item["duplicate"] is False and item["date"] == "2026-06-17"

    r = client.post(f"/api/uploads/{prev['token']}/confirm", json={"items": [
        {"index": 0, "plan_id": "marathon_27w", "plan_week": 3, "session_type": "LONG"}]})
    assert r.status_code == 200, r.get_json()
    (act,) = r.get_json()["saved"]
    assert act["analysis"]["score"] == 100 and act["analysis"]["badge"] == "🟢"
    assert act["plan_week_snapshot"]["long_run_km"] == 12
    assert act["file_path"].startswith(f"uploads/{athlete}/")
    assert (base_dir / act["file_path"]).exists()
    assert pending_dirs(base_dir) == []

    athletes = client.get("/api/athletes").get_json()
    assert athletes[0]["activity_count"] == 1


def test_duplicate_is_flagged_and_skipped(client, athlete, fixtures_dir, base_dir):
    tok = upload(client, athlete, fixtures_dir / LONG).get_json()["token"]
    client.post(f"/api/uploads/{tok}/confirm", json={"items": [
        {"index": 0, "plan_id": "marathon_27w", "plan_week": 3, "session_type": "LONG"}]})
    prev = upload(client, athlete, fixtures_dir / LONG).get_json()
    assert prev["items"][0]["duplicate"] is True
    r = client.post(f"/api/uploads/{prev['token']}/confirm", json={"items": [
        {"index": 0, "plan_id": "marathon_27w", "plan_week": 3, "session_type": "LONG"}]}).get_json()
    assert r["saved"] == [] and r["skipped"] == [{"index": 0, "reason": "duplicate"}]
    assert len(list((base_dir / "uploads" / athlete).iterdir())) == 1
    assert pending_dirs(base_dir) == []


def test_confirm_without_week_is_unscored(client, athlete, fixtures_dir):
    tok = upload(client, athlete, fixtures_dir / "easy_6k.gpx").get_json()["token"]
    r = client.post(f"/api/uploads/{tok}/confirm", json={"items": [
        {"index": 0, "plan_id": "marathon_27w", "plan_week": None, "session_type": "EASY"}]})
    act = r.get_json()["saved"][0]
    assert act["analysis"]["badge"] == "⚪" and act["plan_week"] is None


def test_csv_multi_and_partial_confirm(client, athlete, fixtures_dir):
    prev = upload(client, athlete, fixtures_dir / "strava_multi.csv").get_json()
    assert [i["date"] for i in prev["items"]] == ["2026-06-18", "2026-06-22"]
    assert [i["suggested_week"] for i in prev["items"]] == [3, 4]
    r = client.post(f"/api/uploads/{prev['token']}/confirm", json={"items": [
        {"index": 1, "plan_id": "marathon_27w", "plan_week": 4, "session_type": "LONG"}]}).get_json()
    assert [a["date"] for a in r["saved"]] == ["2026-06-22"]


def test_bad_extension(client, athlete):
    r = upload(client, athlete, data=b"hello", name="notes.txt")
    assert r.status_code == 400 and ".gpx" in r.get_json()["error"]


def test_broken_file_cleans_pending(client, athlete, fixtures_dir, base_dir):
    r = upload(client, athlete, fixtures_dir / "broken.gpx")
    assert r.status_code == 400
    assert pending_dirs(base_dir) == []


def test_missing_fields(client, athlete):
    assert client.post("/api/uploads", data={"athlete_id": athlete}).status_code == 400
    r = upload(client, "missing", data=b"x", name="a.gpx")
    assert r.status_code == 404


def test_too_large(base_dir, athlete):
    app = create_app(Config(base_dir=base_dir, ai_enabled=False, max_upload_mb=1))
    r = upload(app.test_client(), athlete, data=b"0" * (2 * 1024 * 1024), name="big.gpx")
    assert r.status_code == 413 and "MB" in r.get_json()["error"]


def test_invalid_selection_saves_nothing(client, athlete, fixtures_dir, base_dir):
    tok = upload(client, athlete, fixtures_dir / LONG).get_json()["token"]
    for bad in ({"plan_week": 28}, {"plan_id": "nope"}, {"session_type": "WALK"}, {"index": 5}):
        item = {"index": 0, "plan_id": "marathon_27w", "plan_week": 3, "session_type": "LONG", **bad}
        r = client.post(f"/api/uploads/{tok}/confirm", json={"items": [item]})
        assert r.status_code == 400, bad
    assert client.get("/api/athletes").get_json()[0]["activity_count"] == 0
    assert len(pending_dirs(base_dir)) == 1


def test_unknown_token_and_cancel(client, athlete, fixtures_dir, base_dir):
    assert client.post("/api/uploads/" + "0" * 32 + "/confirm", json={"items": []}).status_code == 404
    assert client.post("/api/uploads/../../etc/confirm", json={"items": []}).status_code == 404
    tok = upload(client, athlete, fixtures_dir / LONG).get_json()["token"]
    assert client.delete(f"/api/uploads/{tok}").status_code == 200
    assert pending_dirs(base_dir) == []

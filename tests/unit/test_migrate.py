import json
import shutil

import pytest

from coach.migrate import migrate_all
from coach.plans import PlanCatalog


@pytest.fixture
def legacy(base_dir, fixtures_dir):
    data = base_dir / "data"
    shutil.copytree(fixtures_dir / "legacy" / "data", data)
    return base_dir


def _load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def _snapshot(data_dir):
    return {str(p.relative_to(data_dir)): p.read_text(encoding="utf-8")
            for p in sorted(data_dir.rglob("*.json"))}


def test_migrate_upgrades_everything(legacy):
    data = legacy / "data"
    report = migrate_all(data, PlanCatalog(legacy / "plans"), legacy / "data_backup")

    assert report["backup"] is not None
    backup = legacy / "data_backup" / report["backup"]
    assert (backup / "athlete_cu.json").exists()

    assert not (data / "athlete_cu.json").exists()
    assert sorted(p.name for p in (data / "athletes").iterdir()) == ["le-thi-cu.json", "nguyen-van-a.json"]

    a = _load(data / "athletes" / "nguyen-van-a.json")
    assert a["schema_version"] == 2 and a["id"] == "nguyen-van-a" and a["name"] == "Nguyễn Văn A"
    assert a["group_id"] == "fmsub4_5"
    assert [act["date"] for act in a["activities"]] == ["2026-06-10", "2026-06-17"]

    no_week, long_run = a["activities"]
    assert len(long_run["id"]) == 12
    assert long_run["legacy_analysis"]["score"] == 30
    assert long_run["plan_week_snapshot"]["long_run_km"] == 12
    assert long_run["analysis"]["score"] == 100 and long_run["analysis"]["rules_version"] == 2

    assert no_week["plan_week"] is None
    assert no_week["session_type"] == "EASY"
    assert no_week["analysis"]["badge"] == "⚪"

    cu = _load(data / "athletes" / "le-thi-cu.json")
    assert cu["group_id"] == "fmsub4_5"
    assert cu["activities"][0]["plan_id"] == "marathon_27w"
    assert cu["activities"][0]["legacy_analysis"] == {"score": 100, "badge": "🟢", "flags": []}

    g = _load(data / "groups" / "fmsub4_5.json")
    assert g["schema_version"] == 2 and "athletes" not in g

    np = _load(data / "groups" / "no_plan.json")
    assert np["plan_id"] == "marathon_27w"
    assert any("no_plan" in w for w in report["warnings"])


def test_migrate_is_idempotent(legacy):
    data = legacy / "data"
    cat = PlanCatalog(legacy / "plans")
    migrate_all(data, cat, legacy / "data_backup")
    first = _snapshot(data)
    report = migrate_all(data, cat, legacy / "data_backup")
    assert report["backup"] is None
    assert _snapshot(data) == first
    assert len(list((legacy / "data_backup").iterdir())) == 1


def test_migrate_noop_on_empty(base_dir):
    report = migrate_all(base_dir / "data", PlanCatalog(base_dir / "plans"), base_dir / "data_backup")
    assert report["backup"] is None

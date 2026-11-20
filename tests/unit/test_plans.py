import json
import logging

from coach.plans import PlanCatalog


def _write(dir_, name, data):
    (dir_ / f"{name}.json").write_text(json.dumps(data), encoding="utf-8")


def _week(n, **kw):
    w = {"week": n, "phase": 1, "phase_name": "P1", "total_km": 20, "long_run_km": 8,
         "session_type": "EASY", "target_pace_min": 420, "target_pace_max": 480, "target_hr_max": 148}
    w.update(kw)
    return w


def _plan(pid="p", weeks=2, **kw):
    p = {"id": pid, "name": "Plan", "distance_target_km": 5, "total_weeks": weeks,
         "weeks": [_week(i + 1) for i in range(weeks)]}
    p.update(kw)
    return p


def test_real_plans_are_valid(base_dir):
    cat = PlanCatalog(base_dir / "plans")
    assert set(cat.ids()) == {"5k_8w", "halfmarathon_16w", "marathon_27w"}
    assert cat.errors == []
    assert cat.get_week("marathon_27w", 3)["long_run_km"] == 12
    assert cat.default_id() == "marathon_27w"


def test_optional_fields_get_defaults(tmp_path):
    _write(tmp_path, "p", _plan())
    plan = PlanCatalog(tmp_path).get("p")
    assert plan["description"] == ""
    w = plan["weeks"][0]
    assert w["note"] == "" and w["deload"] is False and w["taper"] is False and w["race_week"] is False


def test_invalid_plans_skipped_with_warning(tmp_path, caplog):
    _write(tmp_path, "ok", _plan("ok"))
    no_weeks = _plan("no_weeks"); del no_weeks["weeks"]
    _write(tmp_path, "no_weeks", no_weeks)
    _write(tmp_path, "mismatch", _plan("mismatch", total_weeks=5))
    bad_pace = _plan("bad_pace"); bad_pace["weeks"][1]["target_pace_min"] = 500
    _write(tmp_path, "bad_pace", bad_pace)
    _write(tmp_path, "id_mismatch", _plan("other"))
    (tmp_path / "broken.json").write_text("{not json", encoding="utf-8")
    with caplog.at_level(logging.WARNING):
        cat = PlanCatalog(tmp_path)
    assert cat.ids() == ["ok"]
    assert len(cat.errors) == 5
    assert "bad_pace" in caplog.text


def test_get_week_out_of_range(tmp_path):
    _write(tmp_path, "p", _plan())
    cat = PlanCatalog(tmp_path)
    assert cat.get_week("p", 0) is None
    assert cat.get_week("p", 3) is None
    assert cat.get_week("nope", 1) is None

import json

from coach.ai import ai_enabled_from_env, build_prompt
from coach.plans import PlanCatalog


def _act(i):
    return {"id": f"a{i}", "date": f"2026-06-{i + 1:02d}", "session_type": "EASY", "plan_id": "halfmarathon_16w",
            "plan_week": 2, "distance_km": 6.0, "duration_sec": 2700, "avg_pace_sec": 450, "avg_hr": 140,
            "max_hr": 155, "avg_cadence": 170, "elevation_gain_m": 10, "hr_data": [140] * 50,
            "file_path": "uploads/x/y.gpx", "filename": "y.gpx", "start_time": "2026-06-01T05:30:00+07:00",
            "analysis": {"score": 100, "badge": "🟢", "flags": [], "note": None, "criteria": {}}}


def test_prompt_uses_real_plan_and_minimal_data(base_dir):
    cat = PlanCatalog(base_dir / "plans")
    plan = cat.get("halfmarathon_16w")
    prompt = build_prompt(plan, 2, [_act(i) for i in range(12)], "Nhóm sáng thứ 7")
    assert "Half Marathon" in prompt and "Full Marathon" not in prompt
    assert "21.1" in prompt
    payload = json.loads(prompt[prompt.index("{"):])
    assert len(payload["recent_activities"]) == 8
    assert payload["recent_activities"][-1]["date"] == "2026-06-12"
    assert payload["current_week"]["week"] == 2 and payload["next_week"]["week"] == 3
    assert payload["group_notes"] == "Nhóm sáng thứ 7"
    for leaked in ("hr_data", "file_path", "filename", "start_time", "lat", "Nguyễn"):
        assert leaked not in prompt


def test_prompt_last_week_has_no_next(base_dir):
    plan = PlanCatalog(base_dir / "plans").get("5k_8w")
    payload = json.loads(build_prompt(plan, 8, [], "")[build_prompt(plan, 8, [], "").index("{"):])
    assert payload["next_week"] is None


def test_ai_enabled_from_env(monkeypatch):
    for k in ("ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN", "COACH_AI_ENABLED"):
        monkeypatch.delenv(k, raising=False)
    assert ai_enabled_from_env() is False
    monkeypatch.setenv("COACH_AI_ENABLED", "1")
    assert ai_enabled_from_env() is True
    monkeypatch.delenv("COACH_AI_ENABLED")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test")
    assert ai_enabled_from_env() is True

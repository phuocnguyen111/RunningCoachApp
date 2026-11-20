from datetime import date

import pytest

from coach.plans import PlanCatalog
from coach.summary import athlete_summary, week_summaries

GROUP = {"id": "g", "plan_id": "marathon_27w", "start_date": "2026-06-01"}


@pytest.fixture
def catalog(base_dir):
    return PlanCatalog(base_dir / "plans")


def act(week, km, plan="marathon_27w", badge="🟢", score=100, pace=450, hr=140, d="2026-06-10"):
    return {"date": d, "plan_id": plan, "plan_week": week, "distance_km": km, "avg_pace_sec": pace,
            "avg_hr": hr, "analysis": {"badge": badge, "score": score}}


def test_week_status(catalog):
    acts = [act(1, 10), act(1, 12),          # 22 / 25 → on_track
            act(2, 10),                      # 10 / 28 → under
            act(3, 40),                      # 40 / 30 → over
            act(4, 5)]                       # tuần đang diễn ra
    today = date(2026, 6, 24)                # ngày thứ 24 → tuần 4
    weeks = {(w["plan_id"], w["week"]): w for w in week_summaries(acts, catalog, GROUP, today)}
    assert weeks[("marathon_27w", 1)]["status"] == "on_track"
    assert weeks[("marathon_27w", 1)]["actual_km"] == 22 and weeks[("marathon_27w", 1)]["sessions"] == 2
    assert weeks[("marathon_27w", 1)]["target_km"] == 25
    assert weeks[("marathon_27w", 2)]["status"] == "under"
    assert weeks[("marathon_27w", 3)]["status"] == "over"
    assert weeks[("marathon_27w", 4)]["status"] == "in_progress"


def test_week_without_group_never_in_progress(catalog):
    weeks = week_summaries([act(4, 5)], catalog, None, date(2026, 6, 24))
    assert weeks[0]["status"] == "under"


def test_other_plan_and_unknown_plan(catalog):
    acts = [act(1, 15, plan="5k_8w"), act(1, 5, plan="deleted_plan"), act(None, 7)]
    weeks = week_summaries(acts, catalog, GROUP, date(2026, 12, 31))
    assert [(w["plan_id"], w["week"], w["status"]) for w in weeks] == [
        ("5k_8w", 1, "on_track"), ("deleted_plan", 1, "no_target")]


def test_unknown_plan_uses_snapshot_target(catalog):
    a = act(1, 10, plan="deleted_plan")
    a["plan_week_snapshot"] = {"total_km": 10}
    (w,) = week_summaries([a], catalog, None, date(2026, 12, 31))
    assert w["target_km"] == 10 and w["status"] == "on_track"


def test_athlete_summary(catalog):
    acts = [act(1, 10, pace=400, hr=140), act(1, 10, badge="🟡", score=70, pace=500, hr=None),
            act(2, 6, badge="🔴", score=0, pace=0, hr=150), act(None, 4, badge="⚪", score=None, hr=None)]
    s = athlete_summary({"activities": acts}, catalog, GROUP, date(2026, 12, 31))
    assert s["total_km"] == 30 and s["total_sessions"] == 4
    assert s["avg_pace_sec"] == 450
    assert s["avg_hr"] == 145
    assert s["good_pct"] == 67
    assert len(s["weeks"]) == 2


def test_athlete_summary_empty(catalog):
    s = athlete_summary({"activities": []}, catalog, None, date(2026, 12, 31))
    assert s["total_sessions"] == 0 and s["good_pct"] is None and s["weeks"] == []

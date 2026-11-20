import pytest

from coach.scoring import badge_for, matches_week_focus, score_activity

EASY_WEEK = {"week": 3, "session_type": "EASY", "total_km": 30, "long_run_km": 12,
             "target_pace_min": 420, "target_pace_max": 480, "target_hr_max": 148}
TEMPO_WEEK = {"week": 11, "session_type": "TEMPO", "total_km": 45, "long_run_km": 18,
              "target_pace_min": 360, "target_pace_max": 390, "target_hr_max": 162}
RACE_WEEK = {"week": 27, "session_type": "RACE", "total_km": 50, "long_run_km": 0,
             "target_pace_min": 380, "target_pace_max": 420, "target_hr_max": 170, "race_week": True}


def run(distance, pace, hr=None):
    return {"distance_km": distance, "avg_pace_sec": pace, "avg_hr": hr}


def test_long_run_on_target_scores_100():
    r = score_activity(run(12.5, 440, 145), "LONG", EASY_WEEK)
    assert r["score"] == 100 and r["badge"] == "🟢" and r["flags"] == []
    assert all(c["applicable"] and c["ok"] for c in r["criteria"].values())
    assert r["rules_version"] == 2


def test_easy_run_not_judged_on_distance():
    r = score_activity(run(6, 450, 140), "EASY", EASY_WEEK)
    assert r["criteria"]["distance"]["applicable"] is False
    assert r["score"] == 100
    assert not any("quãng đường" in f for f in r["flags"])


def test_short_long_run_flags_distance():
    r = score_activity(run(8, 440, 145), "LONG", EASY_WEEK)
    assert r["criteria"]["distance"]["ok"] is False
    assert "Long run thiếu quãng đường (8.0 km / 12 km)" in r["flags"]
    assert r["score"] == 70 and r["badge"] == "🟡"


def test_long_run_too_long_flagged():
    r = score_activity(run(15, 440, 145), "LONG", EASY_WEEK)
    assert "Long run vượt quãng đường (15.0 km / 12 km)" in r["flags"]


def test_easy_in_tempo_week_is_unscored_with_note():
    r = score_activity(run(8, 450, 140), "EASY", TEMPO_WEEK)
    assert r["score"] is None and r["badge"] == "⚪"
    assert r["flags"] == []
    assert r["note"] == "Giáo án tuần này không có mục tiêu cho buổi EASY"


def test_long_in_tempo_week_scores_distance_only():
    r = score_activity(run(18, 450, 150), "LONG", TEMPO_WEEK)
    c = r["criteria"]
    assert c["distance"]["applicable"] and not c["pace"]["applicable"] and not c["hr"]["applicable"]
    assert r["score"] == 100


def test_matches_week_focus():
    assert matches_week_focus("TEMPO", "TEMPO")
    assert matches_week_focus("EASY", "LONG")
    assert matches_week_focus("LONG", "EASY")
    assert not matches_week_focus("EASY", "TEMPO")
    assert not matches_week_focus("SPEED", "TEMPO")


def test_race_does_not_score_hr():
    r = score_activity(run(42.2, 400, 175), "RACE", RACE_WEEK)
    assert r["criteria"]["hr"]["applicable"] is False
    assert r["score"] == 100


def test_too_fast_and_hr_high_flags():
    r = score_activity(run(6, 370, 155), "EASY", EASY_WEEK)
    assert "Chạy QUÁ NHANH (6:10/km, mục tiêu 7:00–8:00/km)" in r["flags"]
    assert "HR cao hơn mục tiêu (155 bpm, tối đa 148 bpm)" in r["flags"]
    assert r["score"] == 0 and r["badge"] == "🔴"


def test_too_slow_flag():
    r = score_activity(run(6, 500, 140), "EASY", EASY_WEEK)
    assert "Chạy quá chậm (8:20/km, mục tiêu 7:00–8:00/km)" in r["flags"]


def test_missing_hr_is_normalised():
    r = score_activity(run(6, 450, None), "EASY", EASY_WEEK)
    assert r["criteria"]["hr"]["applicable"] is False
    assert r["score"] == 100


def test_missing_pace_not_applicable():
    r = score_activity(run(6, 0, 140), "EASY", EASY_WEEK)
    assert r["criteria"]["pace"]["applicable"] is False
    assert r["score"] == 100


def test_no_week_means_unscored():
    r = score_activity(run(6, 450, 140), "EASY", None)
    assert r["score"] is None and r["badge"] == "⚪"
    assert r["note"] == "Chưa chọn tuần giáo án"


@pytest.mark.parametrize("score,badge", [
    (100, "🟢"), (80, "🟢"), (79, "🟡"), (60, "🟡"), (59, "🟠"), (40, "🟠"), (39, "🔴"), (0, "🔴"), (None, "⚪"),
])
def test_badge_thresholds(score, badge):
    assert badge_for(score) == badge

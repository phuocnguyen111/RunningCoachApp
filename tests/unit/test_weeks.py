from coach.weeks import suggest_session_type, week_for_date


def test_week_for_date():
    assert week_for_date("2026-06-01", "2026-05-31", 27) is None
    assert week_for_date("2026-06-01", "2026-06-01", 27) == 1
    assert week_for_date("2026-06-01", "2026-06-07", 27) == 1
    assert week_for_date("2026-06-01", "2026-06-08", 27) == 2
    assert week_for_date("2026-06-01", "2026-06-17", 27) == 3
    assert week_for_date("2026-06-01", "2026-12-06", 27) == 27
    assert week_for_date("2026-06-01", "2026-12-07", 27) is None
    assert week_for_date(None, "2026-06-17", 27) is None
    assert week_for_date("", "2026-06-17", 27) is None


def test_suggest_session_type():
    week = {"long_run_km": 12, "session_type": "EASY"}
    assert suggest_session_type(12.5, week) == "LONG"
    assert suggest_session_type(9.6, week) == "LONG"
    assert suggest_session_type(9.5, week) == "EASY"
    assert suggest_session_type(20, {"long_run_km": 0}) == "EASY"
    assert suggest_session_type(20, None) == "EASY"

from datetime import date

LONG_RUN_RATIO = 0.8


def week_for_date(start_date, run_date, total_weeks):
    if not start_date or not run_date:
        return None
    try:
        days = (date.fromisoformat(run_date) - date.fromisoformat(start_date)).days
    except ValueError:
        return None
    if days < 0:
        return None
    week = days // 7 + 1
    return week if week <= total_weeks else None


def suggest_session_type(distance_km, week):
    long_km = (week or {}).get("long_run_km") or 0
    if long_km > 0 and round(distance_km or 0, 2) >= round(LONG_RUN_RATIO * long_km, 2):
        return "LONG"
    return "EASY"

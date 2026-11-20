from datetime import date, timedelta

VOLUME_TOLERANCE = 0.2
GOOD_BADGES = ("🟢", "🟡")


def _week_finished(group, plan_id, week, today):
    if not group or group.get("plan_id") != plan_id or not group.get("start_date"):
        return True
    start = date.fromisoformat(group["start_date"])
    return today >= start + timedelta(days=7 * week)


def _status(actual, target, finished):
    if not target:
        return "no_target"
    if not finished:
        return "in_progress"
    if actual < (1 - VOLUME_TOLERANCE) * target:
        return "under"
    if actual > (1 + VOLUME_TOLERANCE) * target:
        return "over"
    return "on_track"


def week_summaries(activities, catalog, group, today):
    buckets = {}
    for a in activities:
        if not a.get("plan_id") or not a.get("plan_week"):
            continue
        key = (a["plan_id"], a["plan_week"])
        b = buckets.setdefault(key, {"plan_id": key[0], "week": key[1], "actual_km": 0.0,
                                     "sessions": 0, "target_km": None})
        b["actual_km"] += a.get("distance_km") or 0
        b["sessions"] += 1
        snap = a.get("plan_week_snapshot") or {}
        if b["target_km"] is None and snap.get("total_km"):
            b["target_km"] = snap["total_km"]

    out = []
    for (plan_id, week), b in sorted(buckets.items()):
        current = catalog.get_week(plan_id, week)
        if current:
            b["target_km"] = current["total_km"]
        b["actual_km"] = round(b["actual_km"], 1)
        b["status"] = _status(b["actual_km"], b["target_km"], _week_finished(group, plan_id, week, today))
        out.append(b)
    return out


def athlete_summary(athlete, catalog, group, today):
    acts = athlete.get("activities", [])
    paces = [a["avg_pace_sec"] for a in acts if a.get("avg_pace_sec")]
    hrs = [a["avg_hr"] for a in acts if a.get("avg_hr")]
    scored = [a for a in acts if (a.get("analysis") or {}).get("score") is not None]
    good = [a for a in scored if a["analysis"].get("badge") in GOOD_BADGES]
    return {
        "total_km": round(sum(a.get("distance_km") or 0 for a in acts), 1),
        "total_sessions": len(acts),
        "avg_pace_sec": round(sum(paces) / len(paces)) if paces else 0,
        "avg_hr": round(sum(hrs) / len(hrs)) if hrs else None,
        "good_pct": round(len(good) / len(scored) * 100) if scored else None,
        "weeks": week_summaries(acts, catalog, group, today),
    }

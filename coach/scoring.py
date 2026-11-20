from .plans import AEROBIC

RULES_VERSION = 2
WEIGHTS = {"distance": 30, "pace": 40, "hr": 30}
DISTANCE_TOLERANCE = 0.2
BADGES = ((80, "🟢"), (60, "🟡"), (40, "🟠"), (0, "🔴"))
NO_SCORE_BADGE = "⚪"


def fmt_pace(sec):
    if not sec or sec <= 0:
        return "N/A"
    m, s = divmod(int(sec), 60)
    return f"{m}:{s:02d}/km"


def _fmt_range(lo, hi):
    return f"{fmt_pace(lo)[:-3]}–{fmt_pace(hi)}"


def badge_for(score):
    if score is None:
        return NO_SCORE_BADGE
    for threshold, badge in BADGES:
        if score >= threshold:
            return badge
    return BADGES[-1][1]


def matches_week_focus(session_type, week_focus):
    return session_type == week_focus or (session_type in AEROBIC and week_focus in AEROBIC)


def _criterion(applicable=False, ok=None, actual=None, target=None, key=None):
    return {"applicable": applicable, "ok": ok, "actual": actual, "target": target,
            "weight": WEIGHTS[key]}


def score_activity(metrics, session_type, week):
    criteria = {k: _criterion(key=k) for k in WEIGHTS}
    flags = []
    note = None

    if not week:
        return {"criteria": criteria, "score": None, "badge": NO_SCORE_BADGE, "flags": [],
                "note": "Chưa chọn tuần giáo án", "rules_version": RULES_VERSION}

    dist = metrics.get("distance_km") or 0
    pace = metrics.get("avg_pace_sec") or 0
    hr = metrics.get("avg_hr")
    matches = matches_week_focus(session_type, week["session_type"])

    long_km = week.get("long_run_km") or 0
    if session_type == "LONG" and long_km > 0:
        ok = (1 - DISTANCE_TOLERANCE) * long_km <= dist <= (1 + DISTANCE_TOLERANCE) * long_km
        criteria["distance"] = _criterion(True, ok, round(dist, 2), long_km, "distance")
        if not ok:
            word = "thiếu" if dist < long_km else "vượt"
            flags.append(f"Long run {word} quãng đường ({dist:.1f} km / {long_km:g} km)")

    if matches and pace > 0:
        lo, hi = week["target_pace_min"], week["target_pace_max"]
        ok = lo <= pace <= hi
        criteria["pace"] = _criterion(True, ok, pace, [lo, hi], "pace")
        if pace < lo:
            flags.append(f"Chạy QUÁ NHANH ({fmt_pace(pace)}, mục tiêu {_fmt_range(lo, hi)})")
        elif pace > hi:
            flags.append(f"Chạy quá chậm ({fmt_pace(pace)}, mục tiêu {_fmt_range(lo, hi)})")

    if matches and hr and session_type != "RACE":
        cap = week["target_hr_max"]
        ok = hr <= cap
        criteria["hr"] = _criterion(True, ok, hr, cap, "hr")
        if not ok:
            flags.append(f"HR cao hơn mục tiêu ({hr} bpm, tối đa {cap} bpm)")

    if not matches:
        note = f"Giáo án tuần này không có mục tiêu cho buổi {session_type}"

    applicable = [c for c in criteria.values() if c["applicable"]]
    if applicable:
        total = sum(c["weight"] for c in applicable)
        earned = sum(c["weight"] for c in applicable if c["ok"])
        score = round(earned / total * 100)
    else:
        score = None

    return {"criteria": criteria, "score": score, "badge": badge_for(score), "flags": flags,
            "note": note, "rules_version": RULES_VERSION}

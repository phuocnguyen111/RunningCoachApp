from fitparse import FitFile

from .common import NO_TIME_WARNING, ParseError, build, to_local


def _fields(msg):
    return {d.name: d.value for d in msg if d.name and d.value is not None}


def parse_fit(path, tz, today):
    try:
        ff = FitFile(str(path))
        sessions = [_fields(m) for m in ff.get_messages("session")]
        records = [_fields(m) for m in ff.get_messages("record")]
    except Exception as e:
        raise ParseError(f"File FIT không đọc được ({e.__class__.__name__})") from e

    hr_values = [r["heart_rate"] for r in records if r.get("heart_rate")]
    warnings = []

    if sessions:
        s = sessions[0]
        start = s.get("start_time")
        distance_m = s.get("total_distance") or 0
        duration = s.get("total_timer_time") or s.get("total_elapsed_time") or 0
        avg_hr, max_hr = s.get("avg_heart_rate"), s.get("max_heart_rate")
        cadence = s.get("avg_running_cadence") or s.get("avg_cadence")
        ascent = s.get("total_ascent") or 0
    else:
        stamps = [r["timestamp"] for r in records if r.get("timestamp")]
        dists = [r["distance"] for r in records if r.get("distance") is not None]
        if not stamps or not dists:
            raise ParseError("File FIT không có dữ liệu buổi chạy")
        start = stamps[0]
        distance_m = max(dists)
        duration = (stamps[-1] - stamps[0]).total_seconds()
        avg_hr = max_hr = cadence = None
        ascent = 0

    if not distance_m and not duration:
        raise ParseError("File FIT không có dữ liệu buổi chạy")
    if not start:
        warnings.append(NO_TIME_WARNING)

    activity = build(
        "FIT", to_local(start, tz) if start else None, today, distance_m / 1000, duration,
        avg_hr=avg_hr, max_hr=max_hr, avg_cadence=cadence, elevation_gain_m=ascent,
        hr_values=hr_values,
    )
    return [activity], warnings

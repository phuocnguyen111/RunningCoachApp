from datetime import timezone
from zoneinfo import ZoneInfo

HR_SAMPLE_EVERY = 10
HR_DATA_MAX = 2000
NO_TIME_WARNING = "File không có thời gian, ngày lấy theo hôm nay"


class ParseError(ValueError):
    pass


def to_local(dt, tz):
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(ZoneInfo(tz))


def spm(cadence):
    # Thiết bị ghi cadence một chân (~80–100); quy về bước/phút hai chân.
    if not cadence:
        return None
    cadence = int(round(cadence))
    return cadence * 2 if cadence < 120 else cadence


def sample_hr(values):
    return [int(v) for v in values[::HR_SAMPLE_EVERY]][:HR_DATA_MAX]


def build(source, start_local, today, distance_km, duration_sec, avg_hr=None, max_hr=None,
          avg_cadence=None, elevation_gain_m=0, hr_values=()):
    distance_km = round(max(distance_km or 0, 0), 2)
    duration_sec = int(max(duration_sec or 0, 0))
    hr_values = [v for v in hr_values if v]
    if avg_hr is None and hr_values:
        avg_hr = sum(hr_values) / len(hr_values)
    if max_hr is None and hr_values:
        max_hr = max(hr_values)
    return {
        "source": source,
        "date": (start_local.date() if start_local else today).isoformat(),
        "start_time": start_local.isoformat() if start_local else None,
        "distance_km": distance_km,
        "duration_sec": duration_sec,
        "avg_pace_sec": int(duration_sec / distance_km) if distance_km > 0.1 and duration_sec else 0,
        "avg_hr": int(round(avg_hr)) if avg_hr else None,
        "max_hr": int(round(max_hr)) if max_hr else None,
        "avg_cadence": spm(avg_cadence),
        "elevation_gain_m": int(round(max(elevation_gain_m or 0, 0))),
        "hr_data": sample_hr(hr_values),
    }

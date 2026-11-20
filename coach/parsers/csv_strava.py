import csv
from datetime import datetime

from .common import NO_TIME_WARNING, ParseError, build, to_local

DATE_FORMATS = ("%b %d, %Y, %I:%M:%S %p", "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S",
                "%Y-%m-%d", "%d/%m/%Y %H:%M", "%d/%m/%Y", "%Y/%m/%d")
COLUMNS = {
    "date": ("activity date", "date", "start_time"),
    "type": ("activity type", "type"),
    "distance": ("distance", "distance_km"),
    "moving": ("moving time",),
    "elapsed": ("elapsed time", "duration", "time"),
    "avg_hr": ("average heart rate", "avg_hr", "heart_rate"),
    "max_hr": ("max heart rate", "max_hr"),
    "elev": ("elevation gain", "elevation_gain"),
    "cad": ("average cadence", "cadence"),
    "pace": ("average pace", "avg_pace"),
}


def _num(v):
    try:
        return float(str(v).strip().replace(",", "."))
    except (TypeError, ValueError):
        return None


def _seconds(v):
    v = str(v or "").strip()
    if ":" in v:
        try:
            parts = [int(p) for p in v.split(":")]
        except ValueError:
            return 0
        total = 0
        for p in parts:
            total = total * 60 + p
        return total
    return int(_num(v) or 0)


def _date(v):
    v = str(v or "").strip()
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(v, fmt)
        except ValueError:
            continue
    return None


def parse_csv(path, tz, today):
    try:
        with open(path, newline="", encoding="utf-8-sig") as f:
            rows = list(csv.reader(f))
    except (OSError, UnicodeDecodeError, csv.Error) as e:
        raise ParseError(f"File CSV không đọc được ({e.__class__.__name__})") from e
    if len(rows) < 2:
        raise ParseError("File CSV rỗng")

    header = [h.strip().lower() for h in rows[0]]

    def col(key):
        # Strava có hai cột "Distance" (km rồi mét): luôn lấy cột đầu tiên.
        for name in COLUMNS[key]:
            if name in header:
                return header.index(name)
        return None

    idx = {k: col(k) for k in COLUMNS}
    if idx["distance"] is None:
        raise ParseError("File CSV thiếu cột quãng đường (Distance)")

    def get(row, key):
        i = idx[key]
        return row[i] if i is not None and i < len(row) else ""

    data_rows = [r for r in rows[1:] if any(c.strip() for c in r)]
    if idx["type"] is not None:
        data_rows = [r for r in data_rows if "run" in get(r, "type").lower()]
        if not data_rows:
            raise ParseError("File CSV không có hoạt động chạy bộ nào")

    items, warnings = [], []
    for r in data_rows:
        dist = _num(get(r, "distance")) or 0
        if dist > 200:
            dist /= 1000
        duration = _seconds(get(r, "moving")) or _seconds(get(r, "elapsed"))
        if not duration and dist:
            duration = int(_seconds(get(r, "pace")) * dist)
        start = _date(get(r, "date"))
        if start is None and NO_TIME_WARNING not in warnings:
            warnings.append(NO_TIME_WARNING)
        has_time = start is not None and (start.hour or start.minute or start.second)
        if start is not None and not has_time:
            local = None
            day = start.date()
        else:
            local = to_local(start, tz) if start else None
            day = today
        act = build("CSV", local, day, dist, duration, avg_hr=_num(get(r, "avg_hr")),
                    max_hr=_num(get(r, "max_hr")), avg_cadence=_num(get(r, "cad")),
                    elevation_gain_m=_num(get(r, "elev")) or 0)
        items.append(act)
    return items, warnings

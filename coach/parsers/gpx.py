import gpxpy

from .common import NO_TIME_WARNING, ParseError, build, to_local


def _extension_values(point):
    hr = cad = None
    stack = list(point.extensions or [])
    while stack:
        el = stack.pop()
        stack.extend(list(el))
        tag = el.tag.rsplit("}", 1)[-1].lower()
        if el.text is None:
            continue
        try:
            val = int(float(el.text))
        except ValueError:
            continue
        if tag in ("hr", "heartrate"):
            hr = val
        elif tag in ("cad", "cadence", "runcadence"):
            cad = val
    return hr, cad


def parse_gpx(path, tz, today):
    try:
        with open(path, encoding="utf-8") as f:
            g = gpxpy.parse(f)
    except Exception as e:
        raise ParseError(f"File GPX không đọc được ({e.__class__.__name__})") from e

    points = [p for t in g.tracks for s in t.segments for p in s.points]
    if len(points) < 2:
        raise ParseError("File GPX không có đủ điểm GPS")

    hrs, cads = [], []
    for p in points:
        hr, cad = _extension_values(p)
        if hr:
            hrs.append(hr)
        if cad:
            cads.append(cad)

    times = [p.time for p in points if p.time]
    warnings = []
    if len(times) >= 2:
        start = to_local(times[0], tz)
        duration = (times[-1] - times[0]).total_seconds()
    else:
        start, duration = None, 0
        warnings.append(NO_TIME_WARNING)

    uphill = g.get_uphill_downhill().uphill or 0
    activity = build(
        "GPX", start, today, (g.length_2d() or 0) / 1000, duration,
        avg_cadence=sum(cads) / len(cads) if cads else None,
        elevation_gain_m=uphill, hr_values=hrs,
    )
    return [activity], warnings

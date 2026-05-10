"""
parsers.py – đọc GPX / FIT / CSV → dict chuẩn
"""
import os, csv
from datetime import datetime, timezone

def parse_file(path, ext):
    if ext == ".gpx":
        return _parse_gpx(path)
    elif ext == ".fit":
        return _parse_fit(path)
    elif ext == ".csv":
        return _parse_csv(path)
    raise ValueError(f"Unsupported: {ext}")

# ─── GPX ────────────────────────────────────────────────────
def _parse_gpx(path):
    import gpxpy
    with open(path) as f:
        gpx = gpxpy.parse(f)

    points, times, elevations = [], [], []
    hr_vals, cad_vals = [], []

    for track in gpx.tracks:
        for seg in track.segments:
            for pt in seg.points:
                points.append((pt.latitude, pt.longitude))
                if pt.time:
                    times.append(pt.time)
                if pt.elevation:
                    elevations.append(pt.elevation)
                # extensions: HR, cadence
                for ext in (pt.extensions or []):
                    for child in list(ext):
                        tag = child.tag.lower()
                        val = child.text
                        if val is None:
                            continue
                        if "hr" in tag or "heartrate" in tag:
                            try: hr_vals.append(int(val))
                            except: pass
                        if "cad" in tag or "cadence" in tag:
                            try: cad_vals.append(int(val))
                            except: pass

    distance_km = gpx.length_3d() / 1000 if gpx.length_3d() else gpx.length_2d() / 1000
    duration_sec = 0
    if times and len(times) > 1:
        t0 = times[0].replace(tzinfo=timezone.utc) if times[0].tzinfo is None else times[0]
        t1 = times[-1].replace(tzinfo=timezone.utc) if times[-1].tzinfo is None else times[-1]
        duration_sec = int((t1 - t0).total_seconds())

    avg_pace_sec = int(duration_sec / distance_km) if distance_km > 0.1 else 0
    start_time = times[0].isoformat() if times else None
    date = times[0].strftime("%Y-%m-%d") if times else datetime.today().strftime("%Y-%m-%d")

    elev_gain = 0
    for i in range(1, len(elevations)):
        diff = elevations[i] - elevations[i-1]
        if diff > 0:
            elev_gain += diff

    return {
        "source": "GPX",
        "date": date,
        "start_time": start_time,
        "distance_km": round(distance_km, 2),
        "duration_sec": duration_sec,
        "avg_pace_sec": avg_pace_sec,
        "avg_hr": int(sum(hr_vals)/len(hr_vals)) if hr_vals else None,
        "max_hr": max(hr_vals) if hr_vals else None,
        "avg_cadence": int(sum(cad_vals)/len(cad_vals)) if cad_vals else None,
        "elevation_gain_m": round(elev_gain),
        "hr_data": hr_vals[::10],   # sample every 10
    }

# ─── FIT ────────────────────────────────────────────────────
def _parse_fit(path):
    from fitparse import FitFile
    ff = FitFile(path)

    records = []
    for msg in ff.get_messages("record"):
        r = {}
        for d in msg:
            if d.name and d.value is not None:
                r[d.name] = d.value
        if r:
            records.append(r)

    sessions = list(ff.get_messages("session"))
    if sessions:
        s = sessions[0]
        sdata = {d.name: d.value for d in s if d.value is not None}
        dist = sdata.get("total_distance", 0) or 0
        duration = sdata.get("total_elapsed_time", 0) or 0
        avg_hr   = sdata.get("avg_heart_rate")
        max_hr   = sdata.get("max_heart_rate")
        avg_cad  = sdata.get("avg_running_cadence") or sdata.get("avg_cadence")
        elev     = sdata.get("total_ascent", 0) or 0
        start_t  = sdata.get("start_time")
        date_str = start_t.strftime("%Y-%m-%d") if start_t else datetime.today().strftime("%Y-%m-%d")
        dist_km  = round(dist / 1000, 2)
        avg_pace = int(duration / dist_km) if dist_km > 0.1 else 0
    else:
        # fallback from records
        dist_km, duration, avg_hr, max_hr, avg_cad, elev = 0, 0, None, None, None, 0
        date_str = datetime.today().strftime("%Y-%m-%d")
        avg_pace = 0
        start_t  = None

    hr_vals = [r["heart_rate"] for r in records if "heart_rate" in r]

    return {
        "source": "FIT",
        "date": date_str,
        "start_time": start_t.isoformat() if start_t and hasattr(start_t, 'isoformat') else None,
        "distance_km": dist_km,
        "duration_sec": int(duration),
        "avg_pace_sec": avg_pace,
        "avg_hr": int(avg_hr) if avg_hr else (int(sum(hr_vals)/len(hr_vals)) if hr_vals else None),
        "max_hr": int(max_hr) if max_hr else (max(hr_vals) if hr_vals else None),
        "avg_cadence": int(avg_cad * 2) if avg_cad else None,  # FIT stores single-leg cadence
        "elevation_gain_m": int(elev),
        "hr_data": hr_vals[::10],
    }

# ─── CSV (Strava export) ─────────────────────────────────────
def _parse_csv(path):
    rows = []
    with open(path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)

    if not rows:
        raise ValueError("CSV rỗng")

    def _get(*keys):
        for k in keys:
            for row_k in rows[0].keys():
                if row_k.strip().lower() == k.lower():
                    return row_k
        return None

    # Strava-style columns
    dist_col  = _get("Distance", "distance", "distance_km")
    time_col  = _get("Elapsed Time", "Moving Time", "duration", "time")
    date_col  = _get("Activity Date", "Date", "date", "start_time")
    hr_col    = _get("Average Heart Rate", "avg_hr", "heart_rate")
    pace_col  = _get("Average Pace", "avg_pace")
    elev_col  = _get("Elevation Gain", "elevation_gain")
    cad_col   = _get("Average Cadence", "cadence")
    type_col  = _get("Activity Type", "type")

    # filter running rows
    running_rows = rows
    if type_col:
        running_rows = [r for r in rows if "run" in r.get(type_col, "").lower()] or rows

    def parse_dist(v):
        try:
            v = str(v).replace(",", ".")
            return float(v)
        except: return 0

    def parse_time(v):
        if not v: return 0
        v = str(v).strip()
        if ":" in v:
            parts = v.split(":")
            try:
                if len(parts) == 3: return int(parts[0])*3600 + int(parts[1])*60 + int(parts[2])
                if len(parts) == 2: return int(parts[0])*60 + int(parts[1])
            except: pass
        try: return int(float(v))
        except: return 0

    def parse_hr(v):
        try: return int(float(str(v).replace(",",".")))
        except: return None

    def parse_pace(v):
        if not v: return 0
        v = str(v).strip()
        if ":" in v:
            parts = v.split(":")
            try: return int(parts[0])*60 + int(parts[1])
            except: pass
        return 0

    if len(running_rows) == 1:
        row = running_rows[0]
        dist_km  = parse_dist(row.get(dist_col, 0) if dist_col else 0)
        # Strava distance might be in meters if >1000
        if dist_km > 200: dist_km = dist_km / 1000
        duration = parse_time(row.get(time_col, 0) if time_col else 0)
        avg_hr   = parse_hr(row.get(hr_col, "") if hr_col else "")
        avg_pace = parse_pace(row.get(pace_col, "") if pace_col else "")
        if avg_pace == 0 and dist_km > 0.1 and duration > 0:
            avg_pace = int(duration / dist_km)
        elev     = parse_dist(row.get(elev_col, 0) if elev_col else 0)
        avg_cad  = parse_hr(row.get(cad_col, "") if cad_col else "")
        date_raw = row.get(date_col, "") if date_col else ""
        date_str = _parse_date(date_raw)
    else:
        # aggregate multiple rows (weekly summary CSV)
        dist_km  = sum(parse_dist(r.get(dist_col, 0) if dist_col else 0) for r in running_rows)
        if dist_km > 200: dist_km = dist_km / 1000
        duration = sum(parse_time(r.get(time_col, 0) if time_col else 0) for r in running_rows)
        hr_vals  = [parse_hr(r.get(hr_col, "") if hr_col else "") for r in running_rows]
        hr_vals  = [h for h in hr_vals if h]
        avg_hr   = int(sum(hr_vals)/len(hr_vals)) if hr_vals else None
        avg_pace = int(duration / dist_km) if dist_km > 0.1 else 0
        elev     = sum(parse_dist(r.get(elev_col, 0) if elev_col else 0) for r in running_rows)
        avg_cad  = None
        date_raw = running_rows[-1].get(date_col, "") if date_col else ""
        date_str = _parse_date(date_raw)

    return {
        "source": "CSV",
        "date": date_str,
        "start_time": None,
        "distance_km": round(dist_km, 2),
        "duration_sec": duration,
        "avg_pace_sec": avg_pace,
        "avg_hr": avg_hr,
        "max_hr": None,
        "avg_cadence": avg_cad,
        "elevation_gain_m": int(elev),
        "hr_data": [],
    }

def _parse_date(v):
    v = str(v).strip()
    for fmt in ["%Y-%m-%d", "%b %d, %Y, %I:%M:%S %p", "%d/%m/%Y", "%m/%d/%Y", "%Y/%m/%d"]:
        try: return datetime.strptime(v[:len(fmt)+4], fmt).strftime("%Y-%m-%d")
        except: pass
    return datetime.today().strftime("%Y-%m-%d")

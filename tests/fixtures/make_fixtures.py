"""Sinh lại fixture GPX/CSV: uv run python tests/fixtures/make_fixtures.py"""
from datetime import datetime, timedelta, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
LAT0, LON0 = 10.7769, 106.7009
METERS_PER_DEG_LAT = 111_195.0


def gpx(points, with_time=True):
    head = ('<?xml version="1.0" encoding="UTF-8"?>\n'
            '<gpx version="1.1" creator="fixture" xmlns="http://www.topografix.com/GPX/1/1" '
            'xmlns:gpxtpx="http://www.garmin.com/xmlschemas/TrackPointExtension/v1">\n'
            '<trk><name>fixture</name><trkseg>\n')
    body = []
    for lat, t, hr, cad, ele in points:
        parts = [f'<trkpt lat="{lat:.7f}" lon="{LON0:.7f}"><ele>{ele:.1f}</ele>']
        if with_time:
            parts.append(f"<time>{t.strftime('%Y-%m-%dT%H:%M:%SZ')}</time>")
        if hr:
            parts.append(f"<extensions><gpxtpx:TrackPointExtension><gpxtpx:hr>{hr}</gpxtpx:hr>"
                         f"<gpxtpx:cad>{cad}</gpxtpx:cad></gpxtpx:TrackPointExtension></extensions>")
        parts.append("</trkpt>")
        body.append("".join(parts))
    return head + "\n".join(body) + "\n</trkseg></trk></gpx>\n"


def run(start_utc, km, pace, hr, cad=85, step_m=50):
    n = int(km * 1000 / step_m)
    pts = []
    for i in range(n + 1):
        lat = LAT0 + i * step_m / METERS_PER_DEG_LAT
        t = start_utc + timedelta(seconds=i * step_m * pace / 1000)
        ele = 5 + (2 if i % 20 < 10 else 0)
        pts.append((lat, t, hr, cad, ele))
    return pts


def main():
    utc = timezone.utc
    (HERE / "long_12k_2026-06-17.gpx").write_text(
        gpx(run(datetime(2026, 6, 16, 22, 30, tzinfo=utc), 12.5, 440, 145)), encoding="utf-8")
    (HERE / "easy_6k.gpx").write_text(
        gpx(run(datetime(2026, 6, 19, 23, 0, tzinfo=utc), 6.0, 450, 140)), encoding="utf-8")
    (HERE / "no_time.gpx").write_text(
        gpx(run(datetime(2026, 6, 19, 23, 0, tzinfo=utc), 3.0, 450, None), with_time=False), encoding="utf-8")
    good = gpx(run(datetime(2026, 6, 19, 23, 0, tzinfo=utc), 1.0, 450, 140))
    (HERE / "broken.gpx").write_text(good[: len(good) // 2], encoding="utf-8")
    (HERE / "strava_multi.csv").write_text(
        "Activity ID,Activity Date,Activity Name,Activity Type,Elapsed Time,Distance,Max Heart Rate,"
        "Moving Time,Distance,Elevation Gain,Average Heart Rate,Average Cadence\n"
        '1,"Jun 17, 2026, 10:30:00 PM",Easy,Run,2800,6.00,150,2700,6000.0,20,140,85\n'
        '2,"Jun 19, 2026, 11:00:00 PM",Commute,Ride,3600,25.00,130,3500,25000.0,80,120,\n'
        '3,"Jun 21, 2026, 10:00:00 PM",Long,Run,6000,13.20,160,5900,13200.0,40,146,86\n',
        encoding="utf-8")


if __name__ == "__main__":
    main()

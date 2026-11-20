from datetime import date, datetime
from types import SimpleNamespace

import pytest

from coach.parsers import ParseError, parse_file
from coach.parsers import fit as fit_parser

TZ = "Asia/Ho_Chi_Minh"
TODAY = date(2026, 7, 1)


def parse(path):
    return parse_file(path, tz=TZ, today=TODAY)


def test_gpx_long_run(fixtures_dir):
    items, warnings = parse(fixtures_dir / "long_12k_2026-06-17.gpx")
    assert warnings == []
    (a,) = items
    assert a["source"] == "GPX"
    assert a["date"] == "2026-06-17"
    assert a["start_time"].startswith("2026-06-17T05:30:00+07:00")
    assert a["distance_km"] == pytest.approx(12.5, abs=0.05)
    assert a["duration_sec"] == 5500
    assert a["avg_pace_sec"] == pytest.approx(440, abs=2)
    assert a["avg_hr"] == 145 and a["max_hr"] == 145
    assert a["avg_cadence"] == 170
    assert a["elevation_gain_m"] >= 0
    assert 0 < len(a["hr_data"]) <= 2000


def test_gpx_without_time_uses_today(fixtures_dir):
    items, warnings = parse(fixtures_dir / "no_time.gpx")
    (a,) = items
    assert a["date"] == "2026-07-01" and a["start_time"] is None
    assert a["avg_pace_sec"] == 0 and a["avg_hr"] is None
    assert any("không có thời gian" in w for w in warnings)


def test_broken_gpx_raises(fixtures_dir):
    with pytest.raises(ParseError):
        parse(fixtures_dir / "broken.gpx")


def test_unsupported_extension(tmp_path):
    p = tmp_path / "x.txt"
    p.write_text("hello")
    with pytest.raises(ParseError):
        parse(p)


def test_strava_csv_splits_runs_and_skips_rides(fixtures_dir):
    items, _ = parse(fixtures_dir / "strava_multi.csv")
    assert [a["date"] for a in items] == ["2026-06-18", "2026-06-22"]
    easy, long_ = items
    assert easy["source"] == "CSV"
    assert easy["distance_km"] == 6.0 and easy["duration_sec"] == 2700 and easy["avg_pace_sec"] == 450
    assert easy["avg_hr"] == 140 and easy["max_hr"] == 150 and easy["avg_cadence"] == 170
    assert long_["distance_km"] == 13.2 and long_["elevation_gain_m"] == 40


def test_csv_without_runs_raises(tmp_path):
    p = tmp_path / "rides.csv"
    p.write_text("Activity Date,Activity Type,Distance,Elapsed Time\n2026-06-01,Ride,20,3600\n")
    with pytest.raises(ParseError):
        parse(p)


def test_csv_distance_in_meters(tmp_path):
    p = tmp_path / "m.csv"
    p.write_text("date,distance,duration,avg_hr\n2026-06-01,10000,3000,150\n")
    (a,), _ = parse(p)
    assert a["distance_km"] == 10.0 and a["avg_pace_sec"] == 300


def _fake_fitfile(session, records):
    def msg(fields):
        return [SimpleNamespace(name=k, value=v) for k, v in fields.items()]

    class Fake:
        def __init__(self, path):
            pass

        def get_messages(self, name):
            if name == "session":
                return [msg(session)] if session else []
            return [msg(r) for r in records]

    return Fake


@pytest.mark.parametrize("cadence,expected", [(85, 170), (172, 172)])
def test_fit_session_and_cadence(monkeypatch, tmp_path, cadence, expected):
    session = {"start_time": datetime(2026, 6, 16, 22, 30), "total_distance": 10000.0,
               "total_timer_time": 3000.0, "total_elapsed_time": 3100.0, "avg_heart_rate": 150,
               "max_heart_rate": 170, "avg_running_cadence": cadence, "total_ascent": 35}
    records = [{"heart_rate": 150 + i % 3} for i in range(30)]
    monkeypatch.setattr(fit_parser, "FitFile", _fake_fitfile(session, records))
    p = tmp_path / "a.fit"
    p.write_bytes(b"x")
    (a,), _ = parse(p)
    assert a["source"] == "FIT" and a["date"] == "2026-06-17"
    assert a["distance_km"] == 10.0 and a["duration_sec"] == 3000 and a["avg_pace_sec"] == 300
    assert a["avg_hr"] == 150 and a["max_hr"] == 170 and a["avg_cadence"] == expected
    assert a["elevation_gain_m"] == 35 and len(a["hr_data"]) == 3


def test_fit_without_data_raises(monkeypatch, tmp_path):
    monkeypatch.setattr(fit_parser, "FitFile", _fake_fitfile(None, []))
    p = tmp_path / "a.fit"
    p.write_bytes(b"x")
    with pytest.raises(ParseError):
        parse(p)

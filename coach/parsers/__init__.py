from datetime import date
from pathlib import Path

from .common import ParseError
from .csv_strava import parse_csv
from .fit import parse_fit
from .gpx import parse_gpx

SUPPORTED = {".gpx": parse_gpx, ".fit": parse_fit, ".csv": parse_csv}

__all__ = ["ParseError", "SUPPORTED", "parse_file"]


def parse_file(path, tz="Asia/Ho_Chi_Minh", today=None):
    path = Path(path)
    parser = SUPPORTED.get(path.suffix.lower())
    if not parser:
        raise ParseError("Chỉ hỗ trợ file .gpx, .fit, .csv")
    return parser(path, tz, today or date.today())

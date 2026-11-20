"""Sinh dữ liệu demo để đo hiệu năng (SC-007).

uv run python scripts/seed_demo.py --base /tmp/coach-demo --athletes 50 --activities 200
rồi chạy: COACH_BASE_DIR=/tmp/coach-demo uv run python scripts/seed_demo.py --serve
"""
import argparse
import random
import shutil
import sys
import time
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from coach import create_app  # noqa: E402
from coach.config import Config  # noqa: E402
from coach.ids import new_activity_id  # noqa: E402
from coach.plans import PlanCatalog  # noqa: E402
from coach.scoring import score_activity  # noqa: E402
from coach.store import JsonStore  # noqa: E402

FIRST = ["Nguyễn", "Trần", "Lê", "Phạm", "Hoàng", "Võ", "Đặng", "Bùi"]
LAST = ["An", "Bình", "Châu", "Dũng", "Giang", "Hà", "Khoa", "Linh", "Minh", "Nam"]


def seed(base, n_athletes, n_acts):
    base.mkdir(parents=True, exist_ok=True)
    if not (base / "plans").exists():
        shutil.copytree(ROOT / "plans", base / "plans")
    catalog = PlanCatalog(base / "plans")
    store = JsonStore(base / "data")
    start = date(2026, 1, 5)
    store.write({"schema_version": 2, "id": "demo", "name": "Demo", "plan_id": "marathon_27w",
                 "start_date": start.isoformat(), "notes": "", "created_at": "2026-01-01T00:00:00"},
                "groups", "demo.json")
    rnd = random.Random(1)
    for i in range(n_athletes):
        acts = []
        for j in range(n_acts):
            day = start + timedelta(days=j * 189 // n_acts)
            week = (day - start).days // 7 + 1
            snap = catalog.get_week("marathon_27w", week)
            st = rnd.choice(["EASY", "EASY", "LONG", snap["session_type"]])
            m = {"distance_km": round(rnd.uniform(5, 25), 2), "avg_pace_sec": rnd.randint(330, 500),
                 "avg_hr": rnd.randint(130, 170)}
            acts.append({"id": new_activity_id(), "source": "GPX", "date": day.isoformat(), "start_time": None,
                         **m, "duration_sec": int(m["distance_km"] * m["avg_pace_sec"]), "max_hr": m["avg_hr"] + 15,
                         "avg_cadence": 170, "elevation_gain_m": 20, "hr_data": [m["avg_hr"]] * 100,
                         "plan_id": "marathon_27w", "plan_week": week, "session_type": st,
                         "plan_week_snapshot": snap, "analysis": score_activity(m, st, snap),
                         "legacy_analysis": None, "filename": "", "file_path": "", "uploaded_at": None})
        aid = f"hv-{i:03d}"
        store.write({"schema_version": 2, "id": aid, "name": f"{rnd.choice(FIRST)} {rnd.choice(LAST)} {i}",
                     "group_id": "demo", "created_at": "2026-01-01T00:00:00", "activities": acts},
                    "athletes", f"{aid}.json")


def measure(base):
    client = create_app(Config(base_dir=base, ai_enabled=False)).test_client()
    for path in ("/", "/athletes/hv-000"):
        client.get(path)
        t = time.perf_counter()
        r = client.get(path)
        print(f"{path:<20} {r.status_code}  {(time.perf_counter() - t) * 1000:.0f} ms  {len(r.data) // 1024} KB")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", type=Path, required=True)
    ap.add_argument("--athletes", type=int, default=50)
    ap.add_argument("--activities", type=int, default=200)
    args = ap.parse_args()
    seed(args.base, args.athletes, args.activities)
    measure(args.base)

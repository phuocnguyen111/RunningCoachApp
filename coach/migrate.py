import logging
import shutil
from datetime import datetime
from pathlib import Path

from .ids import new_activity_id, slugify, unique_id
from .plans import SESSION_TYPES
from .scoring import score_activity
from .store import LOCK, JsonStore

log = logging.getLogger(__name__)

SCHEMA_VERSION = 2
LEGACY_ACTIVITY_KEYS = ("score", "badge", "flags")
ACTIVITY_DEFAULTS = {
    "source": "", "start_time": None, "distance_km": 0, "duration_sec": 0, "avg_pace_sec": 0,
    "avg_hr": None, "max_hr": None, "avg_cadence": None, "elevation_gain_m": 0, "hr_data": [],
    "filename": "", "file_path": "", "uploaded_at": None,
}


def activity_sort_key(act):
    return (act.get("date") or "", act.get("start_time") or "")


def _needs_migration(data_dir):
    store = JsonStore(data_dir)
    if any(Path(data_dir).glob("*.json")):
        return True
    docs = store.list_dir("athletes") + store.list_dir("groups")
    return any(d.get("schema_version") != SCHEMA_VERSION for d in docs)


def _upgrade_activity(act, plan_id_fallback, catalog):
    act = dict(act)
    legacy = act.pop("analysis", None)
    top_level = {k: act.pop(k) for k in LEGACY_ACTIVITY_KEYS if k in act}
    if legacy is None and top_level:
        legacy = top_level
    act["legacy_analysis"] = legacy
    for k, v in ACTIVITY_DEFAULTS.items():
        act.setdefault(k, v)
    act["id"] = act.get("id") or new_activity_id()
    plan_id = act.get("plan_id") or plan_id_fallback or None
    if plan_id and not catalog.get(plan_id):
        plan_id = act.get("plan_id") or None
    act["plan_id"] = plan_id
    week = act.get("plan_week")
    act["plan_week"] = week if isinstance(week, int) and week >= 1 else None
    st = (act.get("session_type") or "").upper()
    act["session_type"] = st if st in SESSION_TYPES else "EASY"
    snapshot = catalog.get_week(plan_id, act["plan_week"]) if plan_id else None
    act["plan_week_snapshot"] = snapshot
    act["analysis"] = score_activity(act, act["session_type"], snapshot)
    return act


def migrate_all(data_dir, catalog, backup_root, now=None):
    data_dir, backup_root = Path(data_dir), Path(backup_root)
    report = {"backup": None, "athletes": 0, "groups": 0, "warnings": []}
    if not data_dir.exists():
        return report

    with LOCK:
        if not _needs_migration(data_dir):
            return report

        now = now or datetime.now()
        name = f"pre-migrate-{now.strftime('%Y%m%d_%H%M%S')}"
        backup_root.mkdir(parents=True, exist_ok=True)
        shutil.copytree(data_dir, backup_root / name)
        report["backup"] = name

        store = JsonStore(data_dir)
        membership = {}
        group_plans = {}

        for path in sorted((data_dir / "groups").glob("*.json")):
            g = store.read("groups", path.name)
            for athlete_name in g.pop("athletes", None) or []:
                membership.setdefault(athlete_name, g["id"])
            if not catalog.get(g.get("plan_id")):
                default = catalog.default_id()
                msg = (f"Nhóm '{g['id']}' có giáo án '{g.get('plan_id')}' không hợp lệ, "
                       f"đã gán '{default}' — vui lòng kiểm tra lại")
                log.warning(msg)
                report["warnings"].append(msg)
                g["plan_id"] = default
            g["start_date"] = g.get("start_date") or None
            g["notes"] = g.get("notes") or ""
            g.setdefault("created_at", now.isoformat(timespec="seconds"))
            g["schema_version"] = SCHEMA_VERSION
            group_plans[g["id"]] = g["plan_id"]
            store.write(g, "groups", path.name)
            report["groups"] += 1

        sources = sorted((data_dir / "athletes").glob("*.json")) + sorted(data_dir.glob("*.json"))
        taken, seen_names = set(), set()
        for d in store.list_dir("athletes"):
            if d.get("schema_version") == SCHEMA_VERSION:
                taken.add(d["id"])
                seen_names.add(d["name"])

        for path in sources:
            doc = JsonStore(path.parent).read(path.name)
            if doc.get("schema_version") == SCHEMA_VERSION:
                continue
            name_ = doc.get("name") or path.stem
            if name_ in seen_names:
                path.unlink()
                continue
            aid = doc.get("id") or unique_id(slugify(name_), taken.__contains__, fallback="hv")
            taken.add(aid)
            seen_names.add(name_)

            group_id = doc.get("group_id") or membership.get(name_)
            if group_id not in group_plans:
                group_id = None
            plan_fallback = group_plans.get(group_id)

            acts = [_upgrade_activity(a, plan_fallback, catalog) for a in doc.get("activities", [])]
            acts.sort(key=activity_sort_key)
            athlete = {
                "schema_version": SCHEMA_VERSION,
                "id": aid,
                "name": name_,
                "group_id": group_id,
                "created_at": doc.get("created_at") or now.isoformat(timespec="seconds"),
                "activities": acts,
            }
            store.write(athlete, "athletes", f"{aid}.json")
            if path.resolve() != store.path("athletes", f"{aid}.json"):
                path.unlink()
            report["athletes"] += 1

    log.info("Migration xong: %s", report)
    return report

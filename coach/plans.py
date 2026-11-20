import json
import logging
import re
from pathlib import Path

log = logging.getLogger(__name__)

SESSION_TYPES = ("EASY", "LONG", "TEMPO", "SPEED", "MP", "RACE")
AEROBIC = frozenset({"EASY", "LONG"})
PREFERRED_DEFAULT = "marathon_27w"


class PlanError(ValueError):
    pass


def _num(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def _int(v):
    return isinstance(v, int) and not isinstance(v, bool)


def _validate_week(w, expected):
    where = f"tuần {expected}"
    if not isinstance(w, dict):
        raise PlanError(f"{where}: không phải object")
    if w.get("week") != expected:
        raise PlanError(f"{where}: số tuần phải là {expected}")
    if not _int(w.get("phase")) or w["phase"] < 1:
        raise PlanError(f"{where}: phase không hợp lệ")
    if not isinstance(w.get("phase_name"), str) or not w["phase_name"].strip():
        raise PlanError(f"{where}: thiếu phase_name")
    for k in ("total_km", "long_run_km"):
        if not _num(w.get(k)) or w[k] < 0:
            raise PlanError(f"{where}: {k} không hợp lệ")
    if w.get("session_type") not in SESSION_TYPES:
        raise PlanError(f"{where}: session_type không hợp lệ")
    pmin, pmax = w.get("target_pace_min"), w.get("target_pace_max")
    if not (_int(pmin) and _int(pmax) and 0 < pmin <= pmax):
        raise PlanError(f"{where}: khoảng pace không hợp lệ")
    hr = w.get("target_hr_max")
    if not (_int(hr) and 100 <= hr <= 220):
        raise PlanError(f"{where}: target_hr_max không hợp lệ")
    out = dict(w)
    out["note"] = w.get("note") or ""
    for flag in ("deload", "taper", "race_week"):
        out[flag] = bool(w.get(flag, False))
    return out


def validate_plan(raw, file_id):
    if not isinstance(raw, dict):
        raise PlanError("không phải object")
    pid = raw.get("id")
    if not isinstance(pid, str) or not re.fullmatch(r"[a-z0-9_]+", pid):
        raise PlanError("id không hợp lệ")
    if pid != file_id:
        raise PlanError(f"id '{pid}' khác tên file '{file_id}'")
    if not isinstance(raw.get("name"), str) or not raw["name"].strip():
        raise PlanError("thiếu name")
    if not _num(raw.get("distance_target_km")) or raw["distance_target_km"] <= 0:
        raise PlanError("distance_target_km không hợp lệ")
    weeks = raw.get("weeks")
    if not isinstance(weeks, list) or not weeks:
        raise PlanError("thiếu weeks")
    if raw.get("total_weeks") != len(weeks):
        raise PlanError("total_weeks không khớp số tuần")
    plan = dict(raw)
    plan["description"] = raw.get("description") or ""
    plan["weeks"] = [_validate_week(w, i + 1) for i, w in enumerate(weeks)]
    return plan


class PlanCatalog:
    def __init__(self, plans_dir):
        self.plans_dir = Path(plans_dir)
        self._plans = {}
        self.errors = []
        self.reload()

    def reload(self):
        self._plans, self.errors = {}, []
        if not self.plans_dir.is_dir():
            return
        for p in sorted(self.plans_dir.glob("*.json")):
            try:
                with open(p, encoding="utf-8") as f:
                    raw = json.load(f)
                self._plans[p.stem] = validate_plan(raw, p.stem)
            except (OSError, json.JSONDecodeError, PlanError) as e:
                msg = f"Bỏ qua giáo án {p.name}: {e}"
                log.warning(msg)
                self.errors.append(msg)

    def ids(self):
        return list(self._plans)

    def get(self, plan_id):
        return self._plans.get(plan_id) if plan_id else None

    def get_week(self, plan_id, week):
        plan = self.get(plan_id)
        if not plan or not _int(week) or not 1 <= week <= len(plan["weeks"]):
            return None
        return plan["weeks"][week - 1]

    def default_id(self):
        if PREFERRED_DEFAULT in self._plans:
            return PREFERRED_DEFAULT
        return next(iter(self._plans), None)

    def summaries(self):
        return [
            {k: p[k] for k in ("id", "name", "description", "total_weeks", "distance_target_km")}
            for p in self._plans.values()
        ]

    def all(self):
        return list(self._plans.values())

from datetime import date, datetime

from .ids import slugify, unique_id
from .migrate import SCHEMA_VERSION, activity_sort_key
from .store import LOCK

NAME_MAX = 80
NOTES_MAX = 1000


class ValidationError(ValueError):
    pass


class NotFound(LookupError):
    pass


class Conflict(ValueError):
    pass


def _clean_name(name, label):
    name = (name or "").strip() if isinstance(name, str) else ""
    if not name:
        raise ValidationError(f"Thiếu tên {label}")
    if len(name) > NAME_MAX:
        raise ValidationError(f"Tên {label} tối đa {NAME_MAX} ký tự")
    return name


def _clean_date(value):
    if value in (None, ""):
        return None
    try:
        return date.fromisoformat(str(value)).isoformat()
    except ValueError:
        raise ValidationError("Ngày bắt đầu không hợp lệ (định dạng YYYY-MM-DD)")


def _now():
    return datetime.now().isoformat(timespec="seconds")


class GroupRepo:
    def __init__(self, store, catalog):
        self.store = store
        self.catalog = catalog

    def _check_plan(self, plan_id):
        if not self.catalog.get(plan_id):
            raise ValidationError(f"Giáo án '{plan_id}' không tồn tại")
        return plan_id

    def get(self, group_id):
        if not group_id:
            return None
        return self.store.read("groups", f"{slugify_safe(group_id)}.json")

    def require(self, group_id):
        g = self.get(group_id)
        if not g:
            raise NotFound("Không tìm thấy nhóm")
        return g

    def list(self, athlete_counts=None):
        counts = athlete_counts or {}
        groups = self.store.list_dir("groups")
        for g in groups:
            g["athlete_count"] = counts.get(g["id"], 0)
        return sorted(groups, key=lambda g: g["name"].lower())

    def create(self, body):
        name = _clean_name(body.get("name"), "nhóm")
        plan_id = self._check_plan(body.get("plan_id"))
        notes = self._clean_notes(body.get("notes"))
        with LOCK:
            gid = unique_id(slugify(name), lambda i: self.store.exists("groups", f"{i}.json"), fallback="nhom")
            g = {
                "schema_version": SCHEMA_VERSION, "id": gid, "name": name, "plan_id": plan_id,
                "start_date": _clean_date(body.get("start_date")), "notes": notes, "created_at": _now(),
            }
            self.store.write(g, "groups", f"{gid}.json")
        return g

    def update(self, group_id, body):
        with LOCK:
            g = self.require(group_id)
            if "name" in body:
                g["name"] = _clean_name(body["name"], "nhóm")
            if "plan_id" in body:
                g["plan_id"] = self._check_plan(body["plan_id"])
            if "start_date" in body:
                g["start_date"] = _clean_date(body["start_date"])
            if "notes" in body:
                g["notes"] = self._clean_notes(body["notes"])
            self.store.write(g, "groups", f"{g['id']}.json")
        return g

    @staticmethod
    def _clean_notes(notes):
        notes = (notes or "").strip() if isinstance(notes, str) else ""
        if len(notes) > NOTES_MAX:
            raise ValidationError(f"Ghi chú tối đa {NOTES_MAX} ký tự")
        return notes


def slugify_safe(value):
    return "".join(c for c in str(value) if c.isalnum() or c in "-_")


class AthleteRepo:
    def __init__(self, store, groups):
        self.store = store
        self.groups = groups

    def _path(self, athlete_id):
        return ("athletes", f"{slugify_safe(athlete_id)}.json")

    def get(self, athlete_id):
        if not athlete_id:
            return None
        return self.store.read(*self._path(athlete_id))

    def require(self, athlete_id):
        a = self.get(athlete_id)
        if not a:
            raise NotFound("Không tìm thấy học viên")
        return a

    def all(self):
        return self.store.list_dir("athletes")

    def find_by_name(self, name):
        key = (name or "").strip().lower()
        return next((a for a in self.all() if a["name"].strip().lower() == key), None)

    @staticmethod
    def summary(a):
        acts = a.get("activities", [])
        return {
            "id": a["id"], "name": a["name"], "group_id": a.get("group_id"),
            "activity_count": len(acts),
            "last_activity": acts[-1]["date"] if acts else None,
            "total_km": round(sum(x.get("distance_km") or 0 for x in acts), 1),
        }

    def list(self, group_id=None, docs=None):
        docs = self.all() if docs is None else docs
        out = [self.summary(a) for a in docs if not group_id or a.get("group_id") == group_id]
        return sorted(out, key=lambda x: x["name"].lower())

    def counts_by_group(self, docs=None):
        counts = {}
        for a in self.all() if docs is None else docs:
            if a.get("group_id"):
                counts[a["group_id"]] = counts.get(a["group_id"], 0) + 1
        return counts

    def _check_group(self, group_id):
        if group_id in (None, ""):
            return None
        if not self.groups.get(group_id):
            raise ValidationError(f"Nhóm '{group_id}' không tồn tại")
        return group_id

    def create(self, body):
        name = _clean_name(body.get("name"), "học viên")
        group_id = self._check_group(body.get("group_id"))
        with LOCK:
            if self.find_by_name(name):
                raise Conflict("Học viên đã tồn tại")
            aid = unique_id(slugify(name), lambda i: self.store.exists(*self._path(i)), fallback="hv")
            a = {"schema_version": SCHEMA_VERSION, "id": aid, "name": name, "group_id": group_id,
                 "created_at": _now(), "activities": []}
            self.store.write(a, *self._path(aid))
        return a

    def set_group(self, athlete_id, group_id):
        with LOCK:
            a = self.require(athlete_id)
            a["group_id"] = self._check_group(group_id)
            self.store.write(a, *self._path(a["id"]))
        return a

    def add_activities(self, athlete_id, activities):
        with LOCK:
            a = self.require(athlete_id)
            a["activities"].extend(activities)
            a["activities"].sort(key=activity_sort_key)
            self.store.write(a, *self._path(a["id"]))
        return a

    def remove_activity(self, athlete_id, activity_id):
        with LOCK:
            a = self.require(athlete_id)
            idx = next((i for i, x in enumerate(a["activities"]) if x.get("id") == activity_id), None)
            if idx is None:
                raise NotFound("Không tìm thấy buổi tập")
            removed = a["activities"].pop(idx)
            self.store.write(a, *self._path(a["id"]))
        return removed

    @staticmethod
    def public(a):
        return {k: v for k, v in a.items() if k != "activities"}

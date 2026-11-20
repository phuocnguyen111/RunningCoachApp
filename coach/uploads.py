import re
import shutil
import uuid
from datetime import datetime, timedelta
from pathlib import Path

from .ids import new_activity_id
from .parsers import SUPPORTED, ParseError, parse_file
from .plans import SESSION_TYPES
from .repo import NotFound, ValidationError
from .scoring import score_activity
from .store import JsonStore
from .weeks import suggest_session_type, week_for_date

DUPLICATE_KM = 0.2
TOKEN_RE = re.compile(r"[0-9a-f]{32}")
PREVIEW_KEYS = ("date", "start_time", "distance_km", "duration_sec", "avg_pace_sec", "avg_hr")


def is_duplicate(item, existing):
    return any(
        a.get("date") == item["date"] and abs((a.get("distance_km") or 0) - item["distance_km"]) < DUPLICATE_KM
        for a in existing
    )


def _safe_filename(name):
    name = Path(name or "file").name
    return re.sub(r"[^\w\-.]", "_", name)[:120] or "file"


class UploadService:
    def __init__(self, config, catalog, groups, athletes):
        self.config = config
        self.catalog = catalog
        self.groups = groups
        self.athletes = athletes
        self.pending_root = config.uploads_dir / "_pending"
        self.store = JsonStore(self.pending_root)

    def _dir(self, token):
        if not isinstance(token, str) or not TOKEN_RE.fullmatch(token):
            raise NotFound("Phiên upload đã hết hạn hoặc không tồn tại")
        return self.pending_root / token

    def _meta(self, token):
        meta = self.store.read(token, "meta.json") if self._dir(token).exists() else None
        if not meta:
            raise NotFound("Phiên upload đã hết hạn hoặc không tồn tại")
        return meta

    def create(self, athlete_id, file_storage, today=None):
        athlete = self.athletes.require(athlete_id)
        if file_storage is None or not file_storage.filename:
            raise ValidationError("Chưa chọn file")
        filename = _safe_filename(file_storage.filename)
        if Path(filename).suffix.lower() not in SUPPORTED:
            raise ValidationError("Chỉ hỗ trợ file .gpx, .fit, .csv")

        token = uuid.uuid4().hex
        d = self._dir(token)
        d.mkdir(parents=True)
        try:
            src = d / filename
            file_storage.save(src)
            if src.stat().st_size == 0:
                raise ValidationError("File rỗng")
            try:
                items, warnings = parse_file(src, tz=self.config.timezone, today=today)
            except ParseError as e:
                raise ValidationError(str(e)) from e
            if not items:
                raise ValidationError("Không tìm thấy buổi chạy nào trong file")

            group = self.groups.get(athlete.get("group_id"))
            plan = self.catalog.get(group.get("plan_id")) if group else None
            existing = list(athlete["activities"])
            for i, item in enumerate(items):
                item["index"] = i
                week = week_for_date(group.get("start_date"), item["date"], plan["total_weeks"]) if plan else None
                week_data = self.catalog.get_week(plan["id"], week) if plan and week else None
                item["suggested_plan_id"] = plan["id"] if plan else None
                item["suggested_week"] = week
                item["suggested_session_type"] = suggest_session_type(item["distance_km"], week_data)
                item["duplicate"] = is_duplicate(item, existing)
                existing.append(item)

            meta = {"token": token, "athlete_id": athlete["id"], "filename": filename,
                    "original_filename": file_storage.filename,
                    "created_at": datetime.now().isoformat(timespec="seconds"),
                    "items": items, "warnings": warnings}
            self.store.write(meta, token, "meta.json")
        except BaseException:
            shutil.rmtree(d, ignore_errors=True)
            raise

        return {
            "token": token,
            "items": [{k: it[k] for k in ("index", *PREVIEW_KEYS, "suggested_plan_id", "suggested_week",
                                          "suggested_session_type", "duplicate")} for it in items],
            "warnings": warnings,
        }

    def _validate_selection(self, sel, items):
        if not isinstance(sel, dict):
            raise ValidationError("Lựa chọn không hợp lệ")
        idx = sel.get("index")
        if not isinstance(idx, int) or not 0 <= idx < len(items):
            raise ValidationError(f"Buổi số {idx} không có trong file")
        plan_id, week = sel.get("plan_id"), sel.get("plan_week")
        if plan_id is not None and not self.catalog.get(plan_id):
            raise ValidationError(f"Giáo án '{plan_id}' không tồn tại")
        if week is not None:
            if plan_id is None:
                raise ValidationError("Chọn giáo án trước khi chọn tuần")
            if not isinstance(week, int) or not self.catalog.get_week(plan_id, week):
                raise ValidationError(f"Tuần {week} không có trong giáo án")
        if sel.get("session_type") not in SESSION_TYPES:
            raise ValidationError("Loại buổi tập không hợp lệ")
        return idx, plan_id, week, sel["session_type"]

    def confirm(self, token, selections):
        meta = self._meta(token)
        if not isinstance(selections, list):
            raise ValidationError("Thiếu danh sách buổi tập")
        items = meta["items"]
        chosen = [self._validate_selection(s, items) for s in selections]
        if len({c[0] for c in chosen}) != len(chosen):
            raise ValidationError("Một buổi được chọn nhiều lần")

        athlete = self.athletes.require(meta["athlete_id"])
        existing = list(athlete["activities"])
        saved, skipped = [], []
        stored_rel = None
        now = datetime.now()

        for idx, plan_id, week, session_type in chosen:
            item = items[idx]
            if is_duplicate(item, existing):
                skipped.append({"index": idx, "reason": "duplicate"})
                continue
            if stored_rel is None:
                dest_dir = self.config.uploads_dir / athlete["id"]
                dest_dir.mkdir(parents=True, exist_ok=True)
                dest = dest_dir / f"{now.strftime('%Y%m%d_%H%M%S')}_{meta['filename']}"
                shutil.copy2(self._dir(token) / meta["filename"], dest)
                stored_rel = dest.relative_to(self.config.base_dir).as_posix()
            snapshot = self.catalog.get_week(plan_id, week) if plan_id and week else None
            act = {k: item[k] for k in ("source", *PREVIEW_KEYS, "max_hr", "avg_cadence",
                                        "elevation_gain_m", "hr_data")}
            act.update({
                "id": new_activity_id(), "plan_id": plan_id, "plan_week": week,
                "session_type": session_type, "plan_week_snapshot": snapshot,
                "analysis": score_activity(item, session_type, snapshot), "legacy_analysis": None,
                "filename": meta["original_filename"], "file_path": stored_rel,
                "uploaded_at": now.isoformat(timespec="seconds"),
            })
            saved.append(act)
            existing.append(act)

        if saved:
            self.athletes.add_activities(athlete["id"], saved)
        shutil.rmtree(self._dir(token), ignore_errors=True)
        return {"saved": saved, "skipped": skipped}

    def cancel(self, token):
        d = self._dir(token)
        if not d.exists():
            raise NotFound("Phiên upload đã hết hạn hoặc không tồn tại")
        shutil.rmtree(d, ignore_errors=True)

    def cleanup_expired(self, now=None):
        if not self.pending_root.exists():
            return 0
        cutoff = (now or datetime.now()) - timedelta(hours=self.config.pending_ttl_hours)
        removed = 0
        for d in self.pending_root.iterdir():
            if d.is_dir() and datetime.fromtimestamp(d.stat().st_mtime) < cutoff:
                shutil.rmtree(d, ignore_errors=True)
                removed += 1
        return removed

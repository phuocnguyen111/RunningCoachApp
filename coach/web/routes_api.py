from datetime import date

from flask import jsonify, request
from werkzeug.exceptions import HTTPException

from .. import ai
from ..summary import athlete_summary
from ..repo import AthleteRepo, Conflict, NotFound, ValidationError
from .common import error, services

_HTTP_MESSAGES = {
    400: "Yêu cầu không hợp lệ",
    404: "Không tìm thấy",
    405: "Phương thức không được hỗ trợ",
    413: "File quá lớn",
    500: "Lỗi máy chủ",
}


def register_api_routes(app):
    @app.errorhandler(HTTPException)
    def _http_error(e):
        if not request.path.startswith("/api/"):
            return e
        msg = _HTTP_MESSAGES.get(e.code, e.name)
        if e.code == 413:
            msg = f"File quá lớn (tối đa {services().config.max_upload_mb} MB)"
        return error(msg, e.code)

    @app.errorhandler(ValidationError)
    def _validation(e):
        return error(str(e), 400)

    @app.errorhandler(NotFound)
    def _not_found(e):
        return error(str(e), 404)

    @app.errorhandler(Conflict)
    def _conflict(e):
        return error(str(e), 409)

    @app.get("/api/health")
    def api_health():
        s = services()
        return jsonify({"ok": True, "ai_enabled": s.config.ai_enabled, "plans": len(s.catalog.ids())})

    @app.get("/api/plans")
    def api_plans():
        return jsonify(services().catalog.summaries())

    @app.get("/api/plans/<plan_id>")
    def api_plan(plan_id):
        plan = services().catalog.get(plan_id)
        if not plan:
            return error("Không tìm thấy giáo án", 404)
        return jsonify(plan)

    def body():
        data = request.get_json(silent=True)
        if not isinstance(data, dict):
            raise ValidationError("Dữ liệu gửi lên phải là JSON object")
        return data

    @app.get("/api/groups")
    def api_groups():
        s = services()
        return jsonify(s.groups.list(s.athletes.counts_by_group()))

    @app.post("/api/groups")
    def api_create_group():
        return jsonify(services().groups.create(body())), 201

    @app.patch("/api/groups/<group_id>")
    def api_update_group(group_id):
        return jsonify(services().groups.update(group_id, body()))

    @app.get("/api/athletes")
    def api_athletes():
        return jsonify(services().athletes.list(request.args.get("group_id") or None))

    @app.post("/api/athletes")
    def api_create_athlete():
        return jsonify(AthleteRepo.public(services().athletes.create(body()))), 201

    @app.patch("/api/athletes/<athlete_id>")
    def api_update_athlete(athlete_id):
        data = body()
        if "group_id" not in data:
            raise ValidationError("Thiếu group_id")
        return jsonify(AthleteRepo.public(services().athletes.set_group(athlete_id, data["group_id"])))

    @app.post("/api/uploads")
    def api_upload_preview():
        athlete_id = (request.form.get("athlete_id") or "").strip()
        if not athlete_id:
            raise ValidationError("Thiếu học viên")
        if "file" not in request.files:
            raise ValidationError("Chưa chọn file")
        return jsonify(services().uploads.create(athlete_id, request.files["file"]))

    @app.post("/api/uploads/<token>/confirm")
    def api_upload_confirm(token):
        return jsonify(services().uploads.confirm(token, body().get("items")))

    @app.delete("/api/uploads/<token>")
    def api_upload_cancel(token):
        services().uploads.cancel(token)
        return jsonify({"ok": True})

    @app.get("/api/athletes/<athlete_id>/summary")
    def api_athlete_summary(athlete_id):
        s = services()
        a = s.athletes.require(athlete_id)
        return jsonify(athlete_summary(a, s.catalog, s.groups.get(a.get("group_id")), date.today()))

    @app.delete("/api/athletes/<athlete_id>/activities/<activity_id>")
    def api_delete_activity(athlete_id, activity_id):
        removed = services().athletes.remove_activity(athlete_id, activity_id)
        return jsonify({"ok": True, "removed_id": removed["id"]})

    @app.post("/api/athletes/<athlete_id>/ai-feedback")
    def api_ai_feedback(athlete_id):
        s = services()
        a = s.athletes.require(athlete_id)
        if not s.config.ai_enabled:
            return error("Tính năng AI chưa được cấu hình (thiếu ANTHROPIC_API_KEY)", 503)
        data = body()
        group = s.groups.get(a.get("group_id")) or {}
        latest = next((x["plan_id"] for x in reversed(a["activities"]) if x.get("plan_id")), None)
        plan = s.catalog.get(data.get("plan_id") or latest or group.get("plan_id"))
        if not plan:
            raise ValidationError("Học viên chưa có giáo án để phân tích")
        week = data.get("plan_week")
        if not s.catalog.get_week(plan["id"], week):
            raise ValidationError(f"Tuần {week} không có trong giáo án {plan['name']}")
        prompt = ai.build_prompt(plan, week, a["activities"], group.get("notes"))
        try:
            return jsonify({"feedback": ai.generate_feedback(s.config.ai_model, prompt)})
        except ai.AIError as e:
            return error(str(e), 502)

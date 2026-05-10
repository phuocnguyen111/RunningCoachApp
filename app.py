from flask import Flask, render_template, request, jsonify, session
import os, json, re, signal, shutil, sys
from datetime import datetime
from parsers import parse_file
from analyzer import analyze_activity, generate_ai_feedback

# ── Khởi tạo Flask ────────────────────────────────────────────────────────────
app = Flask(__name__)
app.secret_key = "coach-app-2026"

BASE_DIR      = os.path.dirname(__file__)
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
PLANS_FOLDER  = os.path.join(BASE_DIR, "plans")
GROUPS_FOLDER = os.path.join(BASE_DIR, "data", "groups")
ATHLETES_FOLDER = os.path.join(BASE_DIR, "data", "athletes")
DATA_FOLDER   = os.path.join(BASE_DIR, "data")          # giữ để migrate

for d in [UPLOAD_FOLDER, PLANS_FOLDER, GROUPS_FOLDER, ATHLETES_FOLDER]:
    os.makedirs(d, exist_ok=True)


# ── Migration: data/*.json → data/athletes/*.json ────────────────────────────
def _migrate_legacy_athletes():
    """Chạy 1 lần khi startup – chuyển file cũ sang data/athletes/."""
    for fn in os.listdir(DATA_FOLDER):
        if not fn.endswith(".json"):
            continue
        src = os.path.join(DATA_FOLDER, fn)
        dst = os.path.join(ATHLETES_FOLDER, fn)
        if not os.path.exists(dst):
            shutil.copy2(src, dst)
            print(f"  ↳ Migrated {fn} → data/athletes/")


# ── Plan helpers ──────────────────────────────────────────────────────────────
def list_plans():
    plans = []
    for fn in sorted(os.listdir(PLANS_FOLDER)):
        if fn.endswith(".json"):
            with open(os.path.join(PLANS_FOLDER, fn)) as f:
                p = json.load(f)
                plans.append({
                    "id":           p.get("id", fn[:-5]),
                    "name":         p.get("name", fn[:-5]),
                    "description":  p.get("description", ""),
                    "total_weeks":  p.get("total_weeks", 0),
                    "distance_target_km": p.get("distance_target_km", 0),
                })
    return plans

def load_plan(plan_id):
    """Load plan từ plans/{plan_id}.json. Trả về None nếu không tìm thấy."""
    path = os.path.join(PLANS_FOLDER, f"{plan_id}.json")
    if not os.path.exists(path):
        return None
    with open(path) as f:
        return json.load(f)

def get_plan_week(plan_id, week_num):
    """Trả về dict của tuần week_num trong plan, hoặc {} nếu không có."""
    plan = load_plan(plan_id)
    if not plan:
        return {}
    weeks = plan.get("weeks", [])
    if 1 <= week_num <= len(weeks):
        return weeks[week_num - 1]
    return {}

def default_plan_id():
    """Lấy plan_id đầu tiên có sẵn, ưu tiên marathon_27w."""
    preferred = "marathon_27w"
    if os.path.exists(os.path.join(PLANS_FOLDER, f"{preferred}.json")):
        return preferred
    plans = list_plans()
    return plans[0]["id"] if plans else None


# ── Group helpers ─────────────────────────────────────────────────────────────
def _group_path(group_id):
    safe = re.sub(r"[^a-zA-Z0-9_-]", "_", group_id)
    return os.path.join(GROUPS_FOLDER, f"{safe}.json")

def list_groups():
    groups = []
    for fn in sorted(os.listdir(GROUPS_FOLDER)):
        if fn.endswith(".json"):
            with open(os.path.join(GROUPS_FOLDER, fn)) as f:
                g = json.load(f)
                groups.append(g)
    return sorted(groups, key=lambda x: x.get("name", ""))

def load_group(group_id):
    p = _group_path(group_id)
    if os.path.exists(p):
        with open(p) as f:
            return json.load(f)
    return None

def save_group(data):
    p = _group_path(data["id"])
    with open(p, "w") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ── Athlete helpers ───────────────────────────────────────────────────────────
def _athlete_path(name):
    safe = re.sub(r"[^a-zA-Z0-9_-]", "_", name)
    return os.path.join(ATHLETES_FOLDER, f"{safe}.json")

def load_athlete(name):
    p = _athlete_path(name)
    if os.path.exists(p):
        with open(p) as f:
            return json.load(f)
    return {"name": name, "group_id": None, "activities": []}

def save_athlete(data):
    p = _athlete_path(data["name"])
    with open(p, "w") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def list_athletes(group_id=None):
    athletes = []
    for fn in os.listdir(ATHLETES_FOLDER):
        if not fn.endswith(".json"):
            continue
        with open(os.path.join(ATHLETES_FOLDER, fn)) as f:
            d = json.load(f)
        if group_id and d.get("group_id") != group_id:
            continue
        acts = d.get("activities", [])
        last_plan_id = acts[-1].get("plan_id", "") if acts else ""
        athletes.append({
            "name":           d["name"],
            "group_id":       d.get("group_id"),
            "last_plan_id":   last_plan_id,
            "activity_count": len(acts),
            "last_activity":  acts[-1]["date"] if acts else None,
            "total_km":       round(sum(a.get("distance_km", 0) for a in acts), 1),
        })
    return sorted(athletes, key=lambda x: x["name"])


# ── Routes: Pages ─────────────────────────────────────────────────────────────
@app.route("/")
def index():
    groups   = list_groups()
    athletes = list_athletes()

    # Load full plan data (with weeks) for plan overview and upload form
    plans_full = []
    for fn in sorted(os.listdir(PLANS_FOLDER)):
        if fn.endswith(".json"):
            with open(os.path.join(PLANS_FOLDER, fn)) as f:
                plans_full.append(json.load(f))

    # Default plan weeks for upload form initial state
    default_pid = default_plan_id()
    plan = []
    for p in plans_full:
        if p.get("id") == default_pid:
            plan = p.get("weeks", [])
            break
    if not plan and plans_full:
        plan = plans_full[0].get("weeks", [])

    return render_template("index.html",
                           groups=groups, athletes=athletes,
                           plans=plans_full, plan=plan,
                           default_plan_id=default_pid)

@app.route("/athlete/<name>")
def athlete_detail(name):
    data      = load_athlete(name)
    activities = data.get("activities", [])

    # Lấy plan của group học viên đang thuộc
    plan      = []
    plan_id   = None
    group     = None
    if data.get("group_id"):
        group   = load_group(data["group_id"])
        plan_id = group.get("plan_id") if group else None
        if plan_id:
            p = load_plan(plan_id)
            plan = p.get("weeks", []) if p else []

    for act in activities:
        week_num = act.get("plan_week")
        if week_num and plan and 1 <= week_num <= len(plan):
            act["plan_context"] = plan[week_num - 1]

    return render_template("athlete.html",
                           athlete=data, activities=activities,
                           plan=plan, group=group)


# ── Routes: Plans API ─────────────────────────────────────────────────────────
@app.route("/api/plans")
def api_plans():
    return jsonify(list_plans())

@app.route("/api/plans/<plan_id>")
def api_plan_detail(plan_id):
    plan = load_plan(plan_id)
    if not plan:
        return jsonify({"error": "Không tìm thấy plan"}), 404
    return jsonify(plan)

# Giữ backward-compat với code cũ dùng /api/plan
@app.route("/api/plan")
def api_plan_legacy():
    pid  = request.args.get("id", default_plan_id())
    plan = load_plan(pid)
    if not plan:
        return jsonify([])
    return jsonify(plan.get("weeks", []))


# ── Routes: Groups API ────────────────────────────────────────────────────────
@app.route("/api/groups")
def api_groups():
    return jsonify(list_groups())

@app.route("/api/groups/<group_id>")
def api_group_detail(group_id):
    g = load_group(group_id)
    if not g:
        return jsonify({"error": "Không tìm thấy group"}), 404
    g["athletes_detail"] = list_athletes(group_id=group_id)
    return jsonify(g)

@app.route("/api/groups", methods=["POST"])
def api_create_group():
    body = request.json or {}
    name = body.get("name", "").strip()
    if not name:
        return jsonify({"error": "Thiếu tên nhóm"}), 400

    plan_id = body.get("plan_id", default_plan_id())
    if plan_id and not load_plan(plan_id):
        return jsonify({"error": f"Plan '{plan_id}' không tồn tại"}), 400

    # Tạo ID từ tên (slug)
    group_id = re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")
    # Đảm bảo không trùng
    if load_group(group_id):
        group_id = f"{group_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}"

    g = {
        "id":         group_id,
        "name":       name,
        "plan_id":    plan_id,
        "start_date": body.get("start_date", ""),
        "notes":      body.get("notes", ""),
        "athletes":   [],
        "created_at": datetime.now().isoformat(),
    }
    save_group(g)
    return jsonify({"ok": True, "group": g}), 201

@app.route("/api/groups/<group_id>", methods=["PUT"])
def api_update_group(group_id):
    g = load_group(group_id)
    if not g:
        return jsonify({"error": "Không tìm thấy group"}), 404
    body = request.json or {}
    for field in ["name", "plan_id", "start_date", "notes"]:
        if field in body:
            g[field] = body[field]
    save_group(g)
    return jsonify({"ok": True, "group": g})


# ── Routes: Athletes API ──────────────────────────────────────────────────────
@app.route("/api/athletes")
def api_athletes():
    group_id = request.args.get("group_id")
    return jsonify(list_athletes(group_id=group_id))

@app.route("/api/athletes", methods=["POST"])
def api_create_athlete():
    """Tạo học viên và gán vào group."""
    body     = request.json or {}
    name     = body.get("name", "").strip()
    group_id = body.get("group_id", "")
    if not name:
        return jsonify({"error": "Thiếu tên học viên"}), 400
    if group_id and not load_group(group_id):
        return jsonify({"error": f"Group '{group_id}' không tồn tại"}), 400

    db = load_athlete(name)
    if db.get("activities"):
        return jsonify({"error": "Học viên đã tồn tại"}), 409

    db["group_id"] = group_id or None
    save_athlete(db)

    # Cập nhật danh sách athletes trong group
    if group_id:
        g = load_group(group_id)
        if g and name not in g.get("athletes", []):
            g.setdefault("athletes", []).append(name)
            save_group(g)

    return jsonify({"ok": True, "athlete": db}), 201

@app.route("/api/athletes/<name>/assign-group", methods=["PUT"])
def api_assign_group(name):
    """Gán học viên vào group khác."""
    body     = request.json or {}
    group_id = body.get("group_id", "")

    db = load_athlete(name)
    if group_id and not load_group(group_id):
        return jsonify({"error": f"Group '{group_id}' không tồn tại"}), 400

    old_group_id = db.get("group_id")
    db["group_id"] = group_id or None
    save_athlete(db)

    # Xoá khỏi group cũ
    if old_group_id and old_group_id != group_id:
        og = load_group(old_group_id)
        if og:
            og["athletes"] = [a for a in og.get("athletes", []) if a != name]
            save_group(og)

    # Thêm vào group mới
    if group_id:
        g = load_group(group_id)
        if g and name not in g.get("athletes", []):
            g.setdefault("athletes", []).append(name)
            save_group(g)

    return jsonify({"ok": True})


# ── Routes: Upload ────────────────────────────────────────────────────────────
@app.route("/api/upload", methods=["POST"])
def upload():
    athlete_name  = request.form.get("athlete_name", "").strip()
    plan_week     = request.form.get("plan_week", "0")
    session_type  = request.form.get("session_type", "")
    group_id      = request.form.get("group_id", "")
    plan_id_form  = request.form.get("plan_id", "").strip()

    if not athlete_name:
        return jsonify({"error": "Thiếu tên học viên"}), 400
    if "file" not in request.files:
        return jsonify({"error": "Không có file"}), 400

    f   = request.files["file"]
    ext = os.path.splitext(f.filename)[1].lower()
    if ext not in [".gpx", ".fit", ".csv"]:
        return jsonify({"error": "Chỉ hỗ trợ .gpx, .fit, .csv"}), 400

    # Lưu: uploads/{athlete}/{timestamp}_{original_name}
    safe_name   = re.sub(r"[^a-zA-Z0-9_-]", "_", athlete_name)
    ts          = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_fname  = re.sub(r"[^\w\-.]", "_", f.filename)
    stored_name = f"{ts}_{safe_fname}"

    athlete_upload_dir = os.path.join(UPLOAD_FOLDER, safe_name)
    os.makedirs(athlete_upload_dir, exist_ok=True)

    save_path = os.path.join(athlete_upload_dir, stored_name)
    f.save(save_path)

    try:
        parsed = parse_file(save_path, ext)
    except Exception as e:
        os.remove(save_path)
        return jsonify({"error": f"Parse thất bại: {str(e)}"}), 500

    parsed["plan_week"]    = int(plan_week) if plan_week.isdigit() else 0
    parsed["session_type"] = session_type
    parsed["filename"]     = f.filename
    parsed["file_path"]    = os.path.relpath(save_path, BASE_DIR)

    # Xác định plan: ưu tiên form > group của học viên
    db      = load_athlete(athlete_name)
    eff_gid = group_id or db.get("group_id", "")
    plan_id = plan_id_form  # từ form (do user chọn)
    if not plan_id and eff_gid:
        g = load_group(eff_gid)
        if g:
            plan_id = g.get("plan_id", "") or ""

    plan_ctx = {}
    if plan_id:
        plan_ctx = get_plan_week(plan_id, parsed["plan_week"])

    parsed["plan_id"] = plan_id  # lưu vào activity để hiển thị sau

    analysis = analyze_activity(parsed, plan_ctx)
    parsed["analysis"] = analysis

    # Deduplicate by date + distance
    exists = any(
        a["date"] == parsed["date"] and abs(a.get("distance_km", 0) - parsed.get("distance_km", 0)) < 0.2
        for a in db["activities"]
    )
    if not exists:
        # Cập nhật group_id nếu có
        if eff_gid and not db.get("group_id"):
            db["group_id"] = eff_gid
        db["activities"].append(parsed)
        db["activities"].sort(key=lambda x: x["date"])
        save_athlete(db)
    else:
        os.remove(save_path)

    return jsonify({"ok": True, "activity": parsed, "analysis": analysis, "duplicate": exists})


# ── Routes: AI Feedback ───────────────────────────────────────────────────────
@app.route("/api/ai-feedback", methods=["POST"])
def ai_feedback():
    body         = request.json
    athlete_name = body.get("athlete_name", "")
    week_num     = body.get("week_num", 0)

    db         = load_athlete(athlete_name)
    activities = db.get("activities", [])
    recent     = activities[-8:] if len(activities) >= 8 else activities

    # Lấy plan context từ group
    plan_ctx = {}
    gid = db.get("group_id")
    if gid:
        g = load_group(gid)
        if g and g.get("plan_id"):
            plan_ctx = get_plan_week(g["plan_id"], week_num)

    try:
        feedback = generate_ai_feedback(athlete_name, recent, plan_ctx, week_num)
        return jsonify({"feedback": feedback})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ── Routes: Summary ───────────────────────────────────────────────────────────
@app.route("/api/athlete/<name>/summary")
def athlete_summary(name):
    db   = load_athlete(name)
    acts = db.get("activities", [])
    if not acts:
        return jsonify({"error": "Không có dữ liệu"}), 404

    total_km  = sum(a.get("distance_km", 0) for a in acts)
    pace_vals = [a["avg_pace_sec"] for a in acts if a.get("avg_pace_sec")]
    hr_vals   = [a["avg_hr"]       for a in acts if a.get("avg_hr")]
    avg_pace  = sum(pace_vals) / len(pace_vals) if pace_vals else 0
    avg_hr    = sum(hr_vals)   / len(hr_vals)   if hr_vals   else 0

    weekly = {}
    for a in acts:
        w = a.get("plan_week", 0)
        weekly.setdefault(w, {"week": w, "km": 0, "sessions": 0})
        weekly[w]["km"]       += a.get("distance_km", 0)
        weekly[w]["sessions"] += 1

    compliant = sum(
        1 for a in acts
        if a.get("analysis", {}).get("distance_ok") and a.get("analysis", {}).get("pace_ok")
    )
    compliance_pct = round(compliant / len(acts) * 100) if acts else 0

    return jsonify({
        "total_km":       round(total_km, 1),
        "total_sessions": len(acts),
        "avg_pace_sec":   round(avg_pace),
        "avg_hr":         round(avg_hr),
        "compliance_pct": compliance_pct,
        "group_id":       db.get("group_id"),
        "weekly":         sorted(weekly.values(), key=lambda x: x["week"]),
    })


# ── Routes: Delete Activity ───────────────────────────────────────────────────
@app.route("/api/athlete/<name>/activity/<int:idx>", methods=["DELETE"])
def api_delete_activity(name, idx):
    db = load_athlete(name)
    acts = db.get("activities", [])
    if not (0 <= idx < len(acts)):
        return jsonify({"error": "Index không hợp lệ"}), 400
    removed = acts.pop(idx)
    save_athlete(db)
    return jsonify({"ok": True, "removed_date": removed.get("date", "")})


# ── Shutdown + Backup ─────────────────────────────────────────────────────────
def do_backup():
    """Backup data/ sang data_backup/{timestamp}/."""
    data_dir = os.path.join(BASE_DIR, "data")
    if not os.path.exists(data_dir):
        return
    ts         = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = os.path.join(BASE_DIR, "data_backup", ts)
    shutil.copytree(data_dir, backup_dir)
    print(f"\n💾 Đã backup dữ liệu → data_backup/{ts}/")

def handle_shutdown(sig, frame):
    print("\n⏹  Đang tắt app...")
    do_backup()
    pid_file = os.path.join(BASE_DIR, ".app.pid")
    if os.path.exists(pid_file):
        os.remove(pid_file)
    print("✅ Tắt an toàn. Dữ liệu đã được lưu.")
    sys.exit(0)


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("\n🏃 Running Coach App đang khởi động...")
    _migrate_legacy_athletes()

    pid_file = os.path.join(BASE_DIR, ".app.pid")
    with open(pid_file, "w") as f:
        f.write(str(os.getpid()))

    signal.signal(signal.SIGINT,  handle_shutdown)
    signal.signal(signal.SIGTERM, handle_shutdown)

    print("🌐 http://localhost:5050")
    print("   Nhấn Ctrl+C hoặc chạy ./stop.sh để tắt an toàn\n")
    app.run(debug=False, port=5050)

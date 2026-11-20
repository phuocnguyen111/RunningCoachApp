# CLAUDE.md — Running Coach App

## Mục đích

Web app local giúp HLV quản lý nhiều học viên chạy bộ trên nhiều giáo án: upload tracklog, app tự đề xuất
giáo án + tuần, chấm điểm theo giáo án và gợi ý AI.

## Quy trình (Spec Kit)

- Nguyên tắc dự án: `.specify/memory/constitution.md` — có hiệu lực cao hơn file này.
- Tính năng mới: `/speckit-specify` → (`/speckit-clarify`) → `/speckit-plan` → `/speckit-tasks` → (`/speckit-analyze`) → `/speckit-implement`.
- Spec hiện tại: `specs/001-coach-app-rebuild/` (spec, plan, research, data-model, contracts, quickstart, tasks).

## Chạy app

```bash
bash run.sh             # uv sync + chạy http://127.0.0.1:5050
bash stop.sh            # tắt an toàn (backup data/ → data_backup/)
uv run pytest           # toàn bộ test phải xanh trước khi merge
```

`uv` được cài bằng `pip3 install --user uv` (binary ở `$(python3 -m site --user-base)/bin`); `run.sh` tự tìm.
Sau khi sửa template/JS phải restart app (`debug=False`).

## Stack

- Python 3.12 (venv do `uv` quản lý, `pyproject.toml` + `uv.lock`), Flask, Jinja2
- gpxpy, fitparse, Anthropic SDK 1.x
- Frontend vanilla JS + Chart.js 4.4.0 vendor tại `static/vendor/` (chạy offline, không CDN)
- Lưu trữ JSON file, ghi atomic

## Cấu trúc

```
app.py                  entry point: migrate → create_app → backup khi tắt
coach/
  __init__.py           create_app(config), Services (catalog, store, repos, uploads)
  config.py             Config: đường dẫn, giới hạn upload, AI env
  ids.py                slugify (bỏ dấu tiếng Việt), unique_id, new_activity_id
  store.py              JsonStore (atomic write, LOCK chung)
  plans.py              PlanCatalog: load + validate plans/*.json
  repo.py               GroupRepo, AthleteRepo, ValidationError/NotFound/Conflict
  parsers/              gpx.py, fit.py, csv_strava.py → list[ParsedActivity]
  weeks.py              week_for_date, suggest_session_type
  scoring.py            score_activity, badge_for — NGUỒN DUY NHẤT của quy tắc chấm điểm
  summary.py            athlete_summary, week_summaries
  uploads.py            UploadService: preview → confirm (uploads/_pending/{token})
  ai.py                 build_prompt, generate_feedback
  migrate.py            nâng cấp dữ liệu cũ lên schema_version 2 (idempotent, có backup)
  web/routes_api.py     JSON API
  web/routes_pages.py   trang HTML
templates/              base.html, index.html, athlete.html
static/                 css/app.css, js/{common,dashboard,upload,plans,athlete}.js, vendor/
plans/*.json            giáo án (dữ liệu, không phải code)
tests/unit, tests/integration, tests/fixtures (make_fixtures.py sinh lại GPX/CSV)
scripts/seed_demo.py    dữ liệu demo + đo hiệu năng
data/, uploads/, data_backup/   dữ liệu học viên — gitignored
```

## Data schema (v2)

Chi tiết và ràng buộc: `specs/001-coach-app-rebuild/data-model.md`.

- **Group** `data/groups/{id}.json`: `schema_version, id, name, plan_id, start_date, notes, created_at`.
  Thành viên KHÔNG lưu ở group — lấy từ `athlete.group_id`.
- **Athlete** `data/athletes/{id}.json`: `schema_version, id (slug bỏ dấu, -2 nếu trùng), name (giữ dấu), group_id, created_at, activities[]`.
- **Activity**: chỉ số đo được + `id` (12 hex), `plan_id`, `plan_week` (null = không chấm), `session_type`,
  `plan_week_snapshot` (bản sao tuần giáo án lúc chấm), `analysis` (ScoreResult), `legacy_analysis`, `file_path`.

## API

| Method | Path | Mô tả |
|--------|------|-------|
| GET | `/` | Dashboard |
| GET | `/athletes/<id>` | Trang học viên (`/athlete/<tên>` cũ → 301) |
| GET | `/api/health` | `{ok, ai_enabled, plans}` |
| GET | `/api/plans`, `/api/plans/<id>` | Giáo án |
| GET/POST | `/api/groups` | Danh sách / tạo nhóm |
| PATCH | `/api/groups/<id>` | Sửa nhóm |
| GET/POST | `/api/athletes` | Danh sách (`?group_id=`) / tạo học viên |
| PATCH | `/api/athletes/<id>` | Đổi nhóm `{group_id}` |
| GET | `/api/athletes/<id>/summary` | Thống kê + tổng hợp tuần |
| DELETE | `/api/athletes/<id>/activities/<activity_id>` | Xóa buổi tập |
| POST | `/api/athletes/<id>/ai-feedback` | `{plan_id?, plan_week}` → `{feedback}`; 503 nếu chưa cấu hình AI |
| POST | `/api/uploads` | multipart `athlete_id`, `file` → preview `{token, items, warnings}` |
| POST | `/api/uploads/<token>/confirm` | `{items:[{index, plan_id, plan_week, session_type}]}` → `{saved, skipped}` |
| DELETE | `/api/uploads/<token>` | Hủy preview |

Contract đầy đủ: `specs/001-coach-app-rebuild/contracts/http-api.md`.

## Chấm điểm (`coach/scoring.py`)

- Buổi **khớp mục tiêu tuần** = cùng loại với `session_type` của tuần, hoặc cả hai thuộc {EASY, LONG}.
- Quãng đường (30): chỉ buổi LONG, so với `long_run_km` ±20%.
- Pace (40): buổi khớp mục tiêu tuần và có pace.
- HR (30): buổi khớp mục tiêu tuần, có HR, không phải RACE.
- Điểm = trọng số đạt / trọng số áp dụng × 100. Không tiêu chí nào áp dụng → ⚪ + `note`.
- Badge: 🟢 ≥80 · 🟡 60–79 · 🟠 40–59 · 🔴 <40 · ⚪ không chấm.
- Volume tuần (±20% `total_km`) tính riêng ở `summary.py`.

## Conventions

- Template nhận data qua Jinja2 context; JS dùng `GROUPS_DATA`, `ATHLETES_DATA`, `PLANS_DATA` (`|tojson`).
- Lọc học viên theo nhóm là client-side. Xóa buổi tập theo `activity.id`, không theo index.
- Mọi chuỗi chèn vào HTML từ JS đi qua `esc()`.
- Lỗi API luôn `{"error": "<tiếng Việt>"}`.
- Không comment giải thích WHAT — chỉ comment khi có ràng buộc ẩn.
- Đổi endpoint / schema / quy tắc chấm điểm → cập nhật file này và spec.

## Thêm giáo án

Tạo `plans/{id}.json` (id = tên file, `^[a-z0-9_]+$`) đúng schema trong data-model → restart. Giáo án sai
schema bị bỏ qua, có cảnh báo trong log và trên dashboard.

## Biến môi trường

- `ANTHROPIC_API_KEY` — bật AI feedback (hoặc `ant auth login` + `COACH_AI_ENABLED=1`).
- `COACH_AI_MODEL` — mặc định `claude-opus-5-5`.

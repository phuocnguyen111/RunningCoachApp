# Implementation Plan: Rebuild Running Coach App

**Branch**: `speckit-rebuild` | **Date**: 2026-11-20 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/001-coach-app-rebuild/spec.md`

## Summary

Viết lại app quản lý học viên chạy bộ trên cùng stack (Flask + JSON + vanilla JS), tách thành package
`coach/` có test. Thay đổi chính so với bản cũ:

- Chấm điểm theo loại buổi (long run so với `long_run_km`; volume tuần chấm riêng ở cấp tuần).
- Upload hai bước (preview → confirm) để tự điền giáo án/tuần từ ngày bắt đầu nhóm và cho HLV sửa trước khi lưu.
- Định danh ổn định cho học viên (slug giữ phân biệt tên có dấu) và buổi tập (id, không còn xóa theo index).
- Buổi tập lưu bản sao mục tiêu tuần lúc chấm; trang học viên dùng giáo án của từng buổi.
- AI prompt sinh từ giáo án thật (bỏ hardcode Full Marathon), model cấu hình qua env, mặc định `claude-opus-5-5`.
- Migration tự động, idempotent cho dữ liệu cũ; ghi file atomic; chạy được khi không có mạng.

## Technical Context

**Language/Version**: Python 3.12 (venv do `uv` quản lý) — xem research R1

**Primary Dependencies**: Flask 3.1, gpxpy, fitparse, anthropic (SDK 1.x); dev: pytest. Bỏ pandas.
Frontend: Jinja2, vanilla JS, Chart.js 4.4.0 (vendor local)

**Storage**: JSON files trong `data/` (atomic write, `schema_version`), file gốc trong `uploads/`

**Testing**: pytest (unit cho parser/scoring/weeks/summary/migrate; integration qua Flask test client với thư mục tạm)

**Target Platform**: macOS (Intel & Apple Silicon), Linux; trình duyệt desktop hiện đại

**Project Type**: Web app local một người dùng (server-rendered + JSON API)

**Performance Goals**: Trang < 1s với 50 học viên × 200 buổi (SC-007); preview upload < 3s cho file FIT 10 MB

**Constraints**: Chỉ bind 127.0.0.1; chạy offline (trừ AI); upload ≤ 25 MB; UI tiếng Việt

**Scale/Scope**: ~50 học viên, ~10k buổi tập, ~5 giáo án; 2 trang HTML, ~15 endpoint

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Nguyên tắc | Đánh giá trước Phase 0 | Sau Phase 1 |
|-----------|------------------------|-------------|
| I. Local-first & riêng tư | Bind 127.0.0.1; `data/`, `uploads/` gitignored; AI chỉ gửi chỉ số tóm tắt (FR-022) | ✅ Chart.js/font vendor local (R11); contract AI không gửi GPS/HR series |
| II. Giáo án là dữ liệu | Plan loader + validator, không sửa code khi thêm plan | ✅ data-model Plan/PlanWeek là schema kiểm tra |
| III. Logic tất định có test | scoring/weeks/parsers/summary là hàm thuần, test trước | ✅ `today` được truyền vào summary; hằng số chấm điểm ở một nơi (R7) |
| IV. Đơn giản | Giữ Flask + JSON + vanilla JS; không DB, không framework JS, không blueprint | ✅ Thêm `uv` + package `coach/` — xem Complexity Tracking |
| V. Không mất dữ liệu | Atomic write, migration idempotent có backup, backup khi tắt | ✅ R3, R12 |
| VI. AI tùy chọn | `ai_enabled` flag, UI vô hiệu khi tắt, lỗi AI → 502/503 thân thiện | ✅ R10 |

Kết luận: PASS, không có vi phạm chưa biện minh.

## Project Structure

### Documentation (this feature)

```text
specs/001-coach-app-rebuild/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/http-api.md
├── checklists/requirements.md
└── tasks.md
```

### Source Code (repository root)

```text
app.py                     # entry point: migrate → create_app → signal/backup → run(127.0.0.1:5050)
pyproject.toml, uv.lock
run.sh, stop.sh
coach/
├── __init__.py            # create_app(config)
├── config.py              # đường dẫn, giới hạn upload, AI env
├── ids.py                 # slugify, unique_id, new_activity_id
├── store.py               # JsonStore: atomic read/write, lock
├── plans.py               # load + validate plans, get_week
├── repo.py                # GroupRepo, AthleteRepo (CRUD trên JsonStore)
├── parsers/
│   ├── __init__.py        # parse_file(path) -> list[ParsedActivity]
│   ├── gpx.py
│   ├── fit.py
│   └── csv_strava.py
├── weeks.py               # week_for_date, suggest_session_type
├── scoring.py             # score_activity, badge_for, hằng số trọng số/ngưỡng
├── summary.py             # athlete_summary, week_summaries(today)
├── uploads.py             # pending upload: create/preview/confirm/cancel/cleanup
├── ai.py                  # build_prompt, generate_feedback, ai_enabled
├── migrate.py             # migrate_all (idempotent) + backup
└── web/
    ├── routes_pages.py    # register_page_routes(app)
    └── routes_api.py      # register_api_routes(app), error handlers
templates/
├── base.html
├── index.html
└── athlete.html
static/
├── css/app.css
├── js/common.js, dashboard.js, athlete.js
└── vendor/chart.umd.min.js
plans/*.json               # giữ nguyên dữ liệu
scripts/seed_demo.py
tests/
├── conftest.py            # app/client fixture với tmp data dir, plan fixtures
├── fixtures/              # *.gpx, *.fit, *.csv, legacy_athlete.json
├── unit/test_ids.py, test_plans.py, test_weeks.py, test_scoring.py, test_summary.py,
│        test_parsers.py, test_migrate.py, test_ai_prompt.py, test_store.py
└── integration/test_api_groups.py, test_api_athletes.py, test_api_uploads.py, test_api_ai.py, test_pages.py
```

Xóa: `parsers.py`, `analyzer.py`, `plan.py` (logic chuyển vào `coach/`).

**Structure Decision**: Một project, package `coach/` ở gốc repo cạnh `templates/`, `static/`, `plans/`;
test chia unit/integration. Không tách backend/frontend vì frontend là template server-rendered.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Thêm `uv` + `pyproject.toml` | Cần Python ≥ 3.10 cho SDK Anthropic 1.x mà không đụng Python hệ thống; cài đặt tái lập | `pip install` toàn cục trên Python 3.9 đã hết hỗ trợ |
| Upload hai bước + thư mục pending | Ngày chạy chỉ biết sau khi parse; FR-011 yêu cầu HLV sửa tuần trước khi lưu | Lưu ngay rồi sửa: điểm bị chấm sai trước, HLV thêm thao tác |

---

description: "Task list for Rebuild Running Coach App"
---

# Tasks: Rebuild Running Coach App

**Input**: Design documents from `/specs/001-coach-app-rebuild/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/http-api.md, quickstart.md

**Tests**: Bắt buộc theo Constitution III — test cho logic thuần viết trước và phải FAIL trước khi hiện thực.

**Organization**: Theo user story. US2 làm trước US1 (cả hai P1) vì upload cần học viên/nhóm tồn tại.
Chấm điểm và migration nằm ở Foundational vì app phải đọc được dữ liệu cũ ngay từ lần chạy đầu (Constitution V).

## Format: `[ID] [P?] [Story] Description`

- **[P]**: chạy song song được (file khác nhau, không phụ thuộc task chưa xong)
- **[Story]**: US1..US5 theo spec.md

---

## Phase 1: Setup

- [X] T001 Tạo `pyproject.toml` (Python >=3.12; deps flask, gpxpy, fitparse, anthropic>=1; dev pytest) và sinh `uv.lock` bằng `uv lock`
- [X] T002 [P] Tạo khung thư mục `coach/`, `coach/parsers/`, `coach/web/`, `static/{css,js,vendor}/`, `tests/{unit,integration,fixtures}/`, `scripts/` theo plan.md
- [X] T003 [P] Vendor Chart.js 4.4.0 vào `static/vendor/chart.umd.min.js` (research R11)
- [X] T004 [P] Sửa `.gitignore`: thay dòng `.claude/` bằng `.claude/*` + `!.claude/skills/` (git không mở lại được file con khi cả thư mục cha bị ignore); thêm `.venv/`, `uploads/_pending/`
- [X] T005 Cập nhật `run.sh` dùng `uv sync` + `uv run python app.py`, bỏ `pip install` toàn cục; giữ kiểm tra `.app.pid`

---

## Phase 2: Foundational (Blocking)

**⚠️ CRITICAL**: Không user story nào bắt đầu trước khi phase này xong

### Tests trước

- [X] T006 [P] Test slugify/unique id (có dấu, `đ`, trùng → `-2`, chuỗi rỗng) trong `tests/unit/test_ids.py` — theo research R4
- [X] T007 [P] Test atomic write + đọc lại + không để file tạm khi lỗi + chặn path ra ngoài thư mục gốc trong `tests/unit/test_store.py`
- [X] T008 [P] Test load + validate giáo án (3 plan thật hợp lệ; plan thiếu `weeks`, `total_weeks` lệch, pace min > max bị loại kèm cảnh báo; trường tùy chọn nhận mặc định) trong `tests/unit/test_plans.py`
- [X] T009 [P] Test bảng chấm điểm FR-013/FR-014 trong `tests/unit/test_scoring.py`: các ca spec US1 #2–#4 và #6 (EASY trong tuần TEMPO → ⚪ kèm ghi chú); "khớp mục tiêu tuần" (cùng loại, cả hai aerobic, khác loại); LONG trong tuần TEMPO có `long_run_km` → chỉ chấm quãng đường; RACE không chấm HR; thiếu HR/pace → chuẩn hóa; `plan_week=None` → null/⚪; ngưỡng biên 79/80, 59/60, 39/40; nội dung cảnh báo FR-015
- [X] T010 [P] Tạo fixture `tests/fixtures/legacy/data/` mô phỏng dữ liệu cũ: `athlete_cu.json` ở gốc `data/` (định dạng cũ, tên có dấu, có `analysis` cũ), `athletes/Nguy_n_V_n_A.json`, `groups/fmsub4_5.json` (có `athletes`, không `schema_version`), một group có `plan_id: null`
- [X] T011 Test migrate trong `tests/unit/test_migrate.py`: idempotent (chạy 2 lần cùng kết quả), backup tạo trước khi sửa, activity có `id` + `legacy_analysis` + chấm lại, `group.athletes` hợp nhất vào `athlete.group_id`, group `plan_id: null` nhận giáo án mặc định kèm cảnh báo log, không mất bản ghi
- [X] T012 Tạo `tests/conftest.py`: fixture `app`/`client` với `tmp_path` làm data/uploads, copy `plans/` thật

### Hiện thực

- [X] T013 [P] `coach/config.py`: đường dẫn gốc, `MAX_CONTENT_LENGTH=25MB`, `PENDING_TTL_HOURS=24`, `HOST=127.0.0.1`, đọc `COACH_AI_MODEL`, `COACH_AI_ENABLED`
- [X] T014 [P] `coach/ids.py`: `slugify`, `unique_id(base, exists)`, `new_activity_id` — `data-model.md` `Athlete.id`, `Group.id`, `Activity.id`
- [X] T015 [P] `coach/store.py`: `JsonStore` atomic write + global lock + kiểm tra path nằm trong thư mục gốc (research R3, R13)
- [X] T016 [P] `coach/plans.py`: `load_plans()`, `get_plan()`, `get_week()` với validator theo `data-model.md` `Plan.id`, `Plan.name`, `Plan.description`, `Plan.distance_target_km`, `Plan.total_weeks`, `Plan.weeks`, `PlanWeek.week`, `PlanWeek.phase`, `PlanWeek.phase_name`, `PlanWeek.total_km`, `PlanWeek.long_run_km`, `PlanWeek.session_type`, `PlanWeek.target_pace_min`, `PlanWeek.target_pace_max`, `PlanWeek.target_hr_max`, `PlanWeek.note`, `PlanWeek.deload`, `PlanWeek.taper`, `PlanWeek.race_week`; log cảnh báo plan bị bỏ qua
- [X] T017 [P] `coach/scoring.py`: hằng số trọng số/ngưỡng, `matches_week_focus`, `score_activity`, `badge_for` theo spec FR-013/FR-014 — `data-model.md` `ScoreResult.criteria`, `ScoreResult.score`, `ScoreResult.badge`, `ScoreResult.flags`, `ScoreResult.rules_version`
- [X] T018 `coach/migrate.py` theo research R12 (backup trước, idempotent) — `data-model.md` `Athlete.schema_version`, `Group.schema_version`, `Group.plan_id`, `Activity.id`, `Activity.analysis`, `Activity.legacy_analysis`, `Activity.plan_week_snapshot`
- [X] T019 `coach/__init__.py`: `create_app(config)` — load plans, gắn store, đăng ký routes, error handler JSON `{"error"}` cho 400/404/413/500; không đặt `secret_key` (không dùng session, R13)
- [X] T020 [P] `templates/base.html` + `static/css/app.css` (dark theme hiện tại, font hệ thống) + `static/js/common.js` (`fmtPace`, `showToast`, `api()` wrapper)
- [X] T021 `GET /api/health`, `GET /api/plans`, `GET /api/plans/<id>` trong `coach/web/routes_api.py` theo `contracts/http-api.md`
- [X] T022 `app.py` mới: `migrate_all()` → tạo app → ghi `.app.pid` → signal handler backup `data/` → `data_backup/{ts}/` (FR-026) → `app.run(host="127.0.0.1", port=5050)`

**Checkpoint**: `uv run pytest tests/unit` xanh; chạy `app.py` trên `data/` thật → `fmsub4_5.json` được nâng cấp lên `schema_version: 2`, có backup; `GET /api/health` trả về số plan (quickstart V13)

---

## Phase 3: User Story 2 - Quản lý nhóm và học viên (P1)

**Goal**: Tạo/sửa nhóm, tạo học viên, chuyển nhóm, lọc theo nhóm

**Independent Test**: quickstart V1, V2

### Tests

- [X] T023 [P] [US2] Integration test nhóm: tạo, trùng tên → id khác, plan không tồn tại → 400, PATCH, ngày sai định dạng → 400 trong `tests/integration/test_api_groups.py`
- [X] T024 [P] [US2] Integration test học viên: "Nguyễn Văn A" và "Nguyen Van A" là 2 hồ sơ, chuyển nhóm, bỏ nhóm, group không tồn tại → 400 trong `tests/integration/test_api_athletes.py`

### Implementation

- [X] T025 [US2] `coach/repo.py`: `GroupRepo` (list kèm `athlete_count`, get, create, update) — `data-model.md` `Group.id`, `Group.name`, `Group.plan_id`, `Group.start_date`, `Group.notes`, `Group.schema_version`, `Group.created_at`
- [X] T026 [US2] `coach/repo.py`: `AthleteRepo` (list tóm tắt, get, create, set_group, add_activity giữ thứ tự, remove_activity) — `data-model.md` `Athlete.id`, `Athlete.name`, `Athlete.group_id`, `Athlete.schema_version`, `Athlete.created_at`, `Athlete.activities`
- [X] T027 [US2] Routes `GET/POST /api/groups`, `PATCH /api/groups/<id>`, `GET/POST /api/athletes`, `PATCH /api/athletes/<id>` trong `coach/web/routes_api.py`
- [X] T028 [US2] `GET /` trong `coach/web/routes_pages.py` + `templates/index.html` phần nhóm/học viên, modal tạo/sửa nhóm, inject `GROUPS_DATA`, `ATHLETES_DATA`, `PLANS_DATA` qua `tojson`
- [X] T029 [US2] `static/js/dashboard.js`: lọc học viên theo nhóm client-side (FR-008), tạo/sửa nhóm, tạo học viên, chuyển nhóm

**Checkpoint**: V1, V2 đạt

---

## Phase 4: User Story 1 - Upload và đánh giá ngay (P1) 🎯 MVP

**Goal**: Upload GPX/FIT/CSV → preview với giáo án/tuần đề xuất → xác nhận → điểm/badge/cảnh báo

**Independent Test**: quickstart V3–V7

### Tests (viết trước, phải FAIL)

- [X] T030 [P] [US1] Tạo fixtures: `tests/fixtures/long_12k_2026-06-17.gpx` (có HR, cadence), `easy_6k.gpx`, `no_time.gpx`, `broken.gpx`, `strava_multi.csv` (3 dòng: 2 Run, 1 Ride), `sample.fit` (HLV cung cấp file thật đã ẩn danh, hoặc mẫu từ bộ test của fitparse)
- [X] T031 [P] [US1] Test parser trong `tests/unit/test_parsers.py`: GPX dùng `length_2d`, ngày địa phương, HR/cadence; `no_time.gpx` → ngày hôm nay + cảnh báo, pace = 0; FIT cadence ×2 chỉ khi < 120; CSV tách 2 buổi chạy, bỏ dòng Ride, quãng đường mét → km
- [X] T032 [P] [US1] Test `week_for_date` (trước start → None, ngày 0 → 1, ngày 16 → 3, sau tuần cuối → None, thiếu start → None) và `suggest_session_type` trong `tests/unit/test_weeks.py`
- [X] T033 [P] [US1] Integration test upload trong `tests/integration/test_api_uploads.py`: preview đề xuất plan/tuần, confirm lưu + chuyển file sang `uploads/{athlete_id}/`, confirm với `plan_week=null` → lưu và ⚪, trùng → skipped, đuôi sai → 400, file hỏng → 400 và không còn file pending, > 25MB → 413, token sai → 404, `plan_week` ngoài phạm vi → 400 không lưu gì

### Implementation

- [X] T034 [P] [US1] `coach/parsers/gpx.py` → `ParsedActivity` — `data-model.md` `Activity.source`, `Activity.date`, `Activity.start_time`, `Activity.distance_km`, `Activity.duration_sec`, `Activity.avg_pace_sec`, `Activity.avg_hr`, `Activity.max_hr`, `Activity.avg_cadence`, `Activity.elevation_gain_m`, `Activity.hr_data`
- [X] T035 [P] [US1] `coach/parsers/fit.py` — `data-model.md` `Activity.source`, `Activity.date`, `Activity.start_time`, `Activity.distance_km`, `Activity.duration_sec`, `Activity.avg_pace_sec`, `Activity.avg_hr`, `Activity.max_hr`, `Activity.avg_cadence`, `Activity.elevation_gain_m`, `Activity.hr_data`
- [X] T036 [P] [US1] `coach/parsers/csv_strava.py` trả nhiều buổi — `data-model.md` `Activity.source`, `Activity.date`, `Activity.start_time`, `Activity.distance_km`, `Activity.duration_sec`, `Activity.avg_pace_sec`, `Activity.avg_hr`, `Activity.max_hr`, `Activity.avg_cadence`, `Activity.elevation_gain_m`, `Activity.hr_data`
- [X] T037 [US1] `coach/parsers/__init__.py`: `parse_file(path) -> (list[ParsedActivity], warnings)`, chọn parser theo đuôi, gói lỗi thành `ParseError` tiếng Việt
- [X] T038 [P] [US1] `coach/weeks.py`: `week_for_date`, `suggest_session_type` (research R8; contract `suggested_session_type`)
- [X] T039 [US1] `coach/uploads.py`: `create_pending` (lưu file + meta, gắn đề xuất + cờ trùng), `confirm` (validate tất cả item trước rồi mới lưu; chấm bằng `scoring.score_activity`), `cancel`, `cleanup_expired` — `data-model.md` PendingUpload, `Activity.id`, `Activity.plan_id`, `Activity.plan_week`, `Activity.session_type`, `Activity.plan_week_snapshot`, `Activity.analysis`, `Activity.filename`, `Activity.file_path`, `Activity.uploaded_at`
- [X] T040 [US1] Routes `POST /api/uploads`, `POST /api/uploads/<token>/confirm`, `DELETE /api/uploads/<token>` trong `coach/web/routes_api.py`; gọi `cleanup_expired()` khi khởi động trong `app.py`
- [X] T041 [US1] Form upload trong `templates/index.html` + `static/js/dashboard.js`: chọn học viên (tạo mới inline nếu chưa có) → chọn file → bảng preview mỗi buổi (giáo án, tuần có lựa chọn "không chọn", loại buổi sửa được, đánh dấu trùng) → Xác nhận/Hủy → hiển thị kết quả điểm/badge/cảnh báo

**Checkpoint**: V3–V7 đạt — MVP dùng được

---

## Phase 5: User Story 3 - Tiến độ học viên (P2)

**Goal**: Thống kê, km tuần vs mục tiêu, xu hướng HR, lịch sử, xóa buổi

**Independent Test**: quickstart V8, V9

### Tests

- [X] T042 [P] [US3] Test `week_summaries` (on_track/under/over ±20%, in_progress với `today` truyền vào, no_target, nhiều plan) và `athlete_summary` (good_pct đếm 🟢/🟡) trong `tests/unit/test_summary.py`
- [X] T043 [P] [US3] Integration test trong `tests/integration/test_pages.py`: summary, xóa theo `activity_id` (đúng buổi, id sai → 404), trang `/athletes/<id>` 200/404, redirect `/athlete/<legacy_name>`, buổi vẫn hiển thị mục tiêu đã lưu khi giáo án bị xóa hoặc học viên đổi nhóm

### Implementation

- [X] T044 [US3] `coach/summary.py`: `athlete_summary`, `week_summaries(activities, plans, group, today)` — `data-model.md` `WeekSummary.plan_id`, `WeekSummary.week`, `WeekSummary.actual_km`, `WeekSummary.sessions`, `WeekSummary.target_km`, `WeekSummary.status`
- [X] T045 [US3] Routes `GET /api/athletes/<id>/summary`, `DELETE /api/athletes/<id>/activities/<activity_id>` trong `coach/web/routes_api.py`
- [X] T046 [US3] Route `GET /athletes/<id>` và redirect `/athlete/<name>` trong `coach/web/routes_pages.py`
- [X] T047 [US3] `templates/athlete.html`: stats, lịch sử (mục tiêu lấy từ `plan_week_snapshot` của từng buổi), trạng thái trống
- [X] T048 [US3] `static/js/athlete.js`: biểu đồ km thực tế vs mục tiêu theo tuần, xu hướng HR, xóa buổi có xác nhận rồi tải lại dữ liệu

**Checkpoint**: V8, V9 đạt

---

## Phase 6: User Story 4 - Gợi ý AI (P3)

**Goal**: Nhận xét AI tiếng Việt theo giáo án thật; app chạy bình thường khi không có AI

**Independent Test**: quickstart V10, V11

### Tests

- [X] T049 [P] [US4] Test `build_prompt`: dùng tên/cự ly giáo án thật (không chứa "Full Marathon" với plan half), tối đa 8 buổi, không có `hr_data`/`file_path`/tọa độ; `ai_enabled` theo env trong `tests/unit/test_ai_prompt.py`
- [X] T050 [P] [US4] Integration test `POST /api/athletes/<id>/ai-feedback`: AI tắt → 503; client giả lập lỗi → 502; refusal → 502 thông báo; thành công → `{feedback}` (mock `coach.ai` client) trong `tests/integration/test_api_ai.py`

### Implementation

- [X] T051 [US4] `coach/ai.py`: `ai_enabled()`, `build_prompt(...)`, `generate_feedback(...)` theo research R10 (model từ `COACH_AI_MODEL` mặc định `claude-opus-5-5`, effort medium, fallbacks default, kiểm tra `stop_reason`, chuỗi bắt lỗi)
- [X] T052 [US4] Route `POST /api/athletes/<id>/ai-feedback` trong `coach/web/routes_api.py` (chọn plan: body → buổi gần nhất → nhóm)
- [X] T053 [US4] Khối AI trong `templates/athlete.html` + `static/js/athlete.js`: chọn tuần, nút vô hiệu khi `ai_enabled=false` kèm hướng dẫn, loading, thử lại, render markdown đơn giản

**Checkpoint**: V10, V11 đạt

---

## Phase 7: User Story 5 - Tổng quan giáo án (P3)

**Goal**: Xem phase, km/tuần, deload/taper/race của từng giáo án

**Independent Test**: quickstart V12

- [X] T054 [US5] Tab tổng quan giáo án trong `templates/index.html` + `static/js/dashboard.js`: biểu đồ km/tuần tô màu theo phase, đánh dấu deload/taper/race, chi tiết tuần
- [X] T055 [US5] Hiển thị số plan bị bỏ qua do sai schema trên dashboard (`coach/plans.py` trả danh sách lỗi, `templates/index.html`)

**Checkpoint**: V12 đạt

---

## Phase 8: Polish & Cross-Cutting

- [X] T056 Xóa `parsers.py`, `analyzer.py`, `plan.py`; xác nhận không còn import
- [X] T057 [P] `scripts/seed_demo.py` (50 học viên × 200 buổi vào thư mục chỉ định); đo SC-007 và thời gian preview FIT 10 MB
- [X] T058 [P] Cập nhật `CLAUDE.md` (cấu trúc mới, endpoint mới, quy tắc chấm điểm, ngưỡng badge, quy trình Spec Kit) và `README.md` (cài bằng uv, biến môi trường AI)
- [X] T059 [P] Cập nhật `stop.sh` nếu cần cho `.app.pid` mới
- [ ] T060 Chạy toàn bộ quickstart V1–V15 thủ công (kèm bấm giờ SC-001), ghi kết quả vào PR — đã chạy qua HTTP: V1–V10, V12–V15 đạt; còn lại: V11 (cần API key thật) và thao tác UI trên trình duyệt

---

## Dependencies & Execution Order

- Setup (P1) → Foundational (P2, gồm scoring + migration) → US2 (P3) → US1 (P4, MVP) → US3 (P5) → US4, US5 (P6, P7 song song) → Polish (P8)
- T018 (migrate) cần T016 (plans) và T017 (scoring). T022 (`app.py`) cần T018.
- US3 cần dữ liệu từ US1. US4 cần US3 (trang học viên). US5 chỉ cần Foundational.
- Trong mỗi story: test → logic thuần → repo/service → route → template/JS.

## Parallel Examples

- Foundational: T006–T010 cùng lúc; sau đó T013–T017 và T020 cùng lúc.
- US1: T030–T033 cùng lúc; sau đó T034, T035, T036, T038 cùng lúc.
- US4 và US5 có thể làm song song sau US3.

## Implementation Strategy

1. **MVP** = Phase 1–4: dữ liệu cũ được nâng cấp an toàn, tạo nhóm/học viên, upload với tuần tự động, chấm điểm đúng. Dừng, chạy V1–V7 và V13, demo với HLV.
2. Thêm US3 (tiến độ) → demo.
3. Thêm US4 + US5 → Polish.
4. Mỗi phase một commit (hoặc nhiều), `uv run pytest` xanh trước khi sang phase sau.

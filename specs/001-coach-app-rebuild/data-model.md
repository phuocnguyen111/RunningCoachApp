# Data Model: Rebuild Running Coach App

**Feature**: [spec.md](spec.md) · **Research**: [research.md](research.md)

Lưu trữ: JSON UTF-8 (`ensure_ascii=False`, indent 2), ghi atomic. Ngày: `YYYY-MM-DD`. Pace: giây/km.
Đây là nguồn chuẩn cho ràng buộc trường; tasks.md trích dẫn theo dạng `Entity.field`.

## Plan — `plans/{id}.json` (chỉ đọc)

| Field | Type | Ràng buộc |
|-------|------|-----------|
| `Plan.id` | string | bắt buộc; `^[a-z0-9_]+$`; trùng tên file |
| `Plan.name` | string | bắt buộc, không rỗng |
| `Plan.description` | string | tùy chọn, mặc định `""` |
| `Plan.distance_target_km` | number | bắt buộc, > 0 |
| `Plan.total_weeks` | int | bắt buộc, ≥ 1, = `len(weeks)` |
| `Plan.weeks` | PlanWeek[] | bắt buộc, sắp theo `week` tăng dần, liên tục từ 1 |

## PlanWeek

| Field | Type | Ràng buộc |
|-------|------|-----------|
| `PlanWeek.week` | int | 1..total_weeks |
| `PlanWeek.phase` | int | ≥ 1 |
| `PlanWeek.phase_name` | string | không rỗng |
| `PlanWeek.total_km` | number | ≥ 0 |
| `PlanWeek.long_run_km` | number | ≥ 0; 0 = tuần không có long run |
| `PlanWeek.session_type` | enum SessionType | loại buổi trọng tâm |
| `PlanWeek.target_pace_min` | int | > 0, ≤ `target_pace_max` |
| `PlanWeek.target_pace_max` | int | > 0 |
| `PlanWeek.target_hr_max` | int | 100..220 |
| `PlanWeek.note` | string | tùy chọn |
| `PlanWeek.deload` / `taper` / `race_week` | bool | tùy chọn, mặc định false |

**SessionType** = `EASY | LONG | TEMPO | SPEED | MP | RACE`. Nhóm aerobic = `{EASY, LONG}`.

## Group — `data/groups/{id}.json`

| Field | Type | Ràng buộc |
|-------|------|-----------|
| `Group.schema_version` | int | = 2 |
| `Group.id` | string | nhóm mới: slug `^[a-z0-9-]+$` sinh từ tên (+ hậu tố `-2`.. nếu trùng); nhóm cũ giữ id cũ (có thể có `_`); duy nhất, bất biến |
| `Group.name` | string | bắt buộc, 1..80 ký tự sau trim |
| `Group.plan_id` | string | bắt buộc, phải tồn tại trong Plan khi tạo/sửa |
| `Group.start_date` | date \| null | tùy chọn |
| `Group.notes` | string | tùy chọn, ≤ 1000 ký tự |
| `Group.created_at` | datetime ISO | tự sinh |

Thành viên nhóm **không** lưu ở Group; dẫn xuất từ `Athlete.group_id`. Trường `athletes` của bản cũ bị bỏ khi migrate.

## Athlete — `data/athletes/{id}.json`

| Field | Type | Ràng buộc |
|-------|------|-----------|
| `Athlete.schema_version` | int | = 2 |
| `Athlete.id` | string | slug theo research R4, duy nhất, bất biến |
| `Athlete.name` | string | bắt buộc, 1..80 ký tự sau trim, giữ dấu |
| `Athlete.group_id` | string \| null | nếu có, phải tồn tại trong Group |
| `Athlete.created_at` | datetime ISO | tự sinh |
| `Athlete.activities` | Activity[] | sắp theo `date`, rồi `start_time` |

## Activity (nhúng trong Athlete)

| Field | Type | Ràng buộc |
|-------|------|-----------|
| `Activity.id` | string | 12 hex, duy nhất trong athlete |
| `Activity.source` | enum | `GPX \| FIT \| CSV` |
| `Activity.date` | date | ngày địa phương của buổi chạy |
| `Activity.start_time` | datetime ISO \| null | |
| `Activity.distance_km` | number | ≥ 0, làm tròn 2 chữ số |
| `Activity.duration_sec` | int | ≥ 0 |
| `Activity.avg_pace_sec` | int | ≥ 0; 0 = không tính được |
| `Activity.avg_hr` / `max_hr` | int \| null | 30..250 nếu có |
| `Activity.avg_cadence` | int \| null | spm (hai chân) |
| `Activity.elevation_gain_m` | int | ≥ 0 |
| `Activity.hr_data` | int[] | lấy mẫu mỗi 10 điểm, ≤ 2000 phần tử |
| `Activity.plan_id` | string \| null | |
| `Activity.plan_week` | int \| null | null hoặc 1..Plan.total_weeks; null (kể cả khi có `plan_id`) → không chấm, badge ⚪ |
| `Activity.session_type` | enum SessionType | bắt buộc |
| `Activity.plan_week_snapshot` | PlanWeek \| null | bản sao tuần giáo án lúc chấm |
| `Activity.analysis` | ScoreResult | |
| `Activity.legacy_analysis` | object \| null | chỉ có ở dữ liệu migrate |
| `Activity.filename` | string | tên file gốc |
| `Activity.file_path` | string | tương đối so với gốc repo, nằm trong `uploads/{athlete_id}/` |
| `Activity.uploaded_at` | datetime ISO | |

Trùng lặp: cùng athlete, cùng `date`, `|distance_km − khác| < 0.2`.

## ScoreResult (nhúng trong Activity)

| Field | Type | Ghi chú |
|-------|------|--------|
| `ScoreResult.criteria` | object | khóa `distance`, `pace`, `hr`; mỗi khóa `{applicable: bool, ok: bool\|null, actual, target, weight}` |
| `ScoreResult.score` | int \| null | 0..100; null khi không tiêu chí nào áp dụng |
| `ScoreResult.badge` | enum | `🟢 \| 🟡 \| 🟠 \| 🔴 \| ⚪` theo FR-014 |
| `ScoreResult.flags` | string[] | cảnh báo tiếng Việt theo FR-015 |
| `ScoreResult.note` | string \| null | ghi chú khi không chấm được (chưa chọn tuần, giáo án không có mục tiêu cho loại buổi) |
| `ScoreResult.rules_version` | int | = 2; tăng khi đổi quy tắc chấm |

## WeekSummary (dẫn xuất, không lưu)

| Field | Type | Ghi chú |
|-------|------|--------|
| `WeekSummary.plan_id`, `week` | | khóa nhóm |
| `WeekSummary.actual_km` | number | tổng `distance_km` |
| `WeekSummary.sessions` | int | |
| `WeekSummary.target_km` | number \| null | `PlanWeek.total_km` |
| `WeekSummary.status` | enum | `on_track` (±20%) \| `under` \| `over` \| `in_progress` (tuần chưa kết thúc theo ngày nhóm) \| `no_target` |

## PendingUpload — `uploads/_pending/{token}/`

`meta.json`: `{token, athlete_id, created_at, filename, items: [ParsedActivity + suggested_plan_id, suggested_week, duplicate]}`
cùng file gốc. Hết hạn sau 24h; bị xóa sau khi confirm hoặc hủy.

## State transitions

- PendingUpload: `created → confirmed` (file chuyển sang `uploads/{athlete_id}/`, activity được lưu) hoặc
  `created → cancelled/expired` (xóa thư mục).
- Athlete.group_id: `null ↔ group A ↔ group B`; không ảnh hưởng activity đã chấm.

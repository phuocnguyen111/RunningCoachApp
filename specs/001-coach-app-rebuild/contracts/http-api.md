# HTTP Contract: Running Coach App v2

Base: `http://127.0.0.1:5050`. JSON UTF-8. Lỗi luôn có dạng `{"error": "<thông báo tiếng Việt>"}`.
Kiểu dữ liệu: xem [data-model.md](../data-model.md).

## Trang (HTML)

| Method | Path | Nội dung |
|--------|------|---------|
| GET | `/` | Dashboard: upload, nhóm, học viên (lọc client-side), tổng quan giáo án |
| GET | `/athletes/<athlete_id>` | Trang học viên; 404 nếu không có |
| GET | `/athlete/<legacy_name>` | 301 → `/athletes/<id>` (tương thích link cũ) |

## Hệ thống

| Method | Path | Response 200 |
|--------|------|--------------|
| GET | `/api/health` | `{"ok": true, "ai_enabled": bool, "plans": int}` |

## Giáo án

| Method | Path | Response |
|--------|------|----------|
| GET | `/api/plans` | `[{id, name, description, total_weeks, distance_target_km}]` |
| GET | `/api/plans/<plan_id>` | Plan đầy đủ; 404 |

## Nhóm

| Method | Path | Body | Response |
|--------|------|------|----------|
| GET | `/api/groups` | | `[Group + {athlete_count}]` sắp theo tên |
| POST | `/api/groups` | `{name, plan_id, start_date?, notes?}` | 201 `Group`; 400 thiếu tên / plan không tồn tại / ngày sai |
| PATCH | `/api/groups/<id>` | bất kỳ trong `{name, plan_id, start_date, notes}` | 200 `Group`; 400; 404 |

## Học viên

| Method | Path | Body / Query | Response |
|--------|------|--------------|----------|
| GET | `/api/athletes` | `?group_id=` | `[{id, name, group_id, activity_count, last_activity, total_km}]` |
| POST | `/api/athletes` | `{name, group_id?}` | 201 `Athlete` (không kèm activities); 400; 409 trùng tên y hệt (không phân biệt hoa thường, đã trim) |
| PATCH | `/api/athletes/<id>` | `{group_id: string\|null}` | 200 `Athlete`; 400 group không tồn tại; 404 |
| GET | `/api/athletes/<id>/summary` | | `{total_km, total_sessions, avg_pace_sec, avg_hr, good_pct, weeks: WeekSummary[]}` |
| DELETE | `/api/athletes/<id>/activities/<activity_id>` | | 200 `{ok, removed_id}`; 404 |
| POST | `/api/athletes/<id>/ai-feedback` | `{plan_id?, plan_week}` | 200 `{feedback: markdown}`; 503 AI chưa cấu hình; 502 lỗi dịch vụ AI; 404 |

`plan_id` cho AI mặc định là `plan_id` của buổi tập gần nhất, rồi đến giáo án của nhóm.

## Upload (hai bước)

### `POST /api/uploads` — multipart

Fields: `athlete_id` (bắt buộc), `file` (bắt buộc, `.gpx|.fit|.csv`, ≤ 25 MB).

200:
```json
{
  "token": "a1b2c3...",
  "items": [
    {
      "index": 0,
      "date": "2026-06-17", "distance_km": 12.5, "duration_sec": 5500,
      "avg_pace_sec": 440, "avg_hr": 145,
      "suggested_plan_id": "marathon_27w", "suggested_week": 3,
      "suggested_session_type": "LONG",
      "duplicate": false
    }
  ],
  "warnings": ["File không có thời gian, ngày lấy theo hôm nay"]
}
```
Lỗi: 400 thiếu trường / sai đuôi / file rỗng hoặc không đọc được; 404 athlete; 413 quá lớn.

`suggested_session_type`: `LONG` nếu `distance_km ≥ 0.8 × long_run_km` của tuần đề xuất, ngược lại `EASY`.

### `POST /api/uploads/<token>/confirm` — JSON

```json
{"items": [{"index": 0, "plan_id": "marathon_27w", "plan_week": 3, "session_type": "LONG"}]}
```
Chỉ các `index` được gửi mới được lưu. `plan_id` và/hoặc `plan_week` có thể `null` (không chấm, badge ⚪);
`plan_week` khác null phải nằm trong 1..total_weeks của giáo án, nếu không trả 400.

200: `{"saved": [Activity], "skipped": [{"index": 1, "reason": "duplicate"}]}`.
Lỗi: 400 plan/tuần/loại buổi không hợp lệ (không lưu gì); 404 token hết hạn/không tồn tại.

### `DELETE /api/uploads/<token>`

200 `{ok: true}` — xóa file pending.

## Endpoint bị bỏ

`/api/upload`, `/api/plan`, `/api/ai-feedback`, `/api/athlete/<name>/...`, `PUT /api/groups/<id>`,
`PUT /api/athletes/<name>/assign-group`. Không có client ngoài app dùng các endpoint này.

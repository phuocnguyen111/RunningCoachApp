# CLAUDE.md — Running Coach App

## Mục đích

Web app local quản lý nhiều học viên chạy bộ trên nhiều training plan. HLV upload tracklog, chọn giáo án + tuần, app phân tích tự động và gợi ý AI.

## Chạy app

```bash
python3 app.py          # http://localhost:5050
# hoặc
bash run.sh
bash stop.sh            # tắt an toàn
```

Sau khi sửa template HTML phải restart app (Flask debug=False không auto-reload).

## Stack

- **Backend:** Python 3.9, Flask (không dùng blueprint), Jinja2 templates
- **Frontend:** Vanilla JS, Chart.js, dark theme — không có JS framework
- **AI:** Anthropic Claude API qua biến môi trường `ANTHROPIC_API_KEY`
- **Lưu trữ:** JSON files (không có database)

## Cấu trúc thư mục

```
app.py              – Flask routes + helpers chính
parsers.py          – Parse GPX / FIT / CSV → dict chuẩn
analyzer.py         – So sánh activity với plan, tính score, AI feedback
plan.py             – Legacy data (không dùng chính, dùng plans/*.json)
plans/
  marathon_27w.json
  halfmarathon_16w.json
  5k_8w.json
templates/
  index.html        – Dashboard chính (upload + groups + athletes + plan overview)
  athlete.html      – Chi tiết học viên
data/
  athletes/         – {name}.json mỗi học viên
  groups/           – {id}.json mỗi nhóm
uploads/            – File tạm khi upload (tự xóa sau parse)
```

## Data schema

**Athlete** (`data/athletes/{name}.json`):
```json
{
  "name": "Nguyen Van A",
  "group_id": "fmsub4_5",
  "activities": [
    {
      "date": "2026-05-10",
      "plan_id": "marathon_27w",
      "plan_week": 3,
      "session_type": "EASY",
      "distance_km": 10.2,
      "avg_pace_sec": 390,
      "avg_hr": 145,
      "score": 82,
      "badge": "🟢",
      "flags": []
    }
  ]
}
```

**Group** (`data/groups/{id}.json`):
```json
{
  "id": "fmsub4_5",
  "name": "Marathon Sub 4:30",
  "plan_id": "marathon_27w",
  "start_date": "2026-01-01",
  "athletes": ["Nguyen Van A", "Tran Thi B"]
}
```

**Plan week** (trong `plans/*.json`):
```json
{
  "week": 3, "phase": 1, "phase_name": "Xây Nền Tảng",
  "total_km": 30, "long_run_km": 12, "session_type": "EASY",
  "target_pace_min": 420, "target_pace_max": 480,
  "target_hr_max": 148, "note": "..."
}
```

## API endpoints

| Method | Path | Mô tả |
|--------|------|-------|
| GET | `/` | Dashboard chính |
| GET | `/athlete/<name>` | Chi tiết học viên |
| POST | `/api/upload` | Upload + phân tích tracklog |
| DELETE | `/api/athlete/<name>/activity/<idx>` | Xóa 1 activity |
| GET | `/api/plans` | Danh sách plans |
| GET | `/api/groups` | Danh sách groups |
| POST | `/api/groups` | Tạo group mới |
| GET | `/api/athletes` | Danh sách athletes |
| POST | `/api/athletes` | Tạo athlete mới |
| POST | `/api/athlete/<name>/assign-group` | Gán athlete vào group |
| POST | `/api/ai-feedback` | AI feedback cho athlete |
| GET | `/api/athlete/<name>/summary` | Tóm tắt stats |

## Upload flow

Form fields: `athlete_name`, `plan_id` (bắt buộc), `plan_week`, `session_type`, `group_id` (tùy chọn), `file`

`plan_id` trong form được ưu tiên hơn plan của group. Mỗi activity lưu `plan_id` riêng để độc lập với group.

## Scoring

- Score 0–100 dựa trên: distance ±20%, pace trong target zone, HR max
- Badge: 🟢 ≥80 · 🟡 60–79 · 🟠 40–59 · 🔴 <40

## Conventions

- Template nhận data qua Jinja2 context (không AJAX cho page render)
- JS dùng `PLANS_DATA` và `ATHLETES_DATA` (inject qua `{{ ... | tojson }}`) để client-side logic
- Index xóa activity dùng `orig_idx = activities|length - 1 - loop.index0` vì list đảo ngược khi hiển thị
- Group filter athletes là client-side JS (không server round-trip)
- Không dùng comment giải thích WHAT — chỉ comment khi có constraint ẩn

## Thêm giáo án mới

1. Tạo file `plans/{id}.json` với cấu trúc giống các file hiện có
2. App tự detect và hiển thị — không cần sửa code

## Biến môi trường

- `ANTHROPIC_API_KEY` — cần để dùng AI feedback (tính năng vẫn chạy nếu thiếu, chỉ disable AI)

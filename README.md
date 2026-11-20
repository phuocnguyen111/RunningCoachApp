# Running Coach App

Web app chạy trên máy HLV để quản lý nhiều học viên chạy bộ theo nhiều giáo án: upload tracklog,
app tự đề xuất giáo án + tuần theo nhóm, chấm điểm buổi tập và gợi ý AI.

## Cài đặt & chạy

```bash
# 1. Cài uv (một lần)
pip3 install --user uv            # hoặc xem https://docs.astral.sh/uv/

# 2. (Tùy chọn) bật AI feedback
export ANTHROPIC_API_KEY="sk-ant-..."
# export COACH_AI_MODEL="claude-sonnet-5-5"   # mặc định claude-opus-5-5

# 3. Chạy — uv tự tải Python 3.12 và dependency
bash run.sh                       # mở http://127.0.0.1:5050
bash stop.sh                      # tắt an toàn + backup dữ liệu
```

App chỉ nghe trên `127.0.0.1` và chạy được không cần mạng (trừ AI). Dữ liệu cũ được tự nâng cấp khi khởi
động; bản sao trước khi nâng cấp nằm ở `data_backup/pre-migrate-*`.

## Tính năng

- **Nhóm & học viên**: mỗi nhóm gắn một giáo án và ngày bắt đầu; lọc học viên theo nhóm; đổi nhóm không làm
  thay đổi kết quả chấm của buổi cũ.
- **Upload GPX / FIT / CSV (Strava)**: bước xem trước tự điền giáo án, tuần (theo ngày bắt đầu của nhóm) và loại
  buổi; HLV sửa rồi mới lưu. CSV nhiều hoạt động được tách thành từng buổi; buổi trùng được đánh dấu.
- **Chấm điểm theo loại buổi**: long run so với km long run; pace/HR so với mục tiêu khi buổi khớp trọng tâm tuần.
  Badge 🟢 ≥80 · 🟡 60–79 · 🟠 40–59 · 🔴 <40 · ⚪ không chấm.
- **Trang học viên**: tổng km, pace/HR TB, tỷ lệ buổi đạt, km tuần so với mục tiêu, xu hướng HR, lịch sử, xóa buổi.
- **AI feedback**: đánh giá 8 buổi gần nhất theo giáo án thật và gợi ý tuần kế tiếp. Chỉ gửi chỉ số tóm tắt —
  không gửi tên học viên, file, GPS hay chuỗi HR.
- **Giáo án**: Marathon 27 tuần, Half Marathon 16 tuần, 5K 8 tuần; thêm giáo án bằng một file JSON trong `plans/`.

## Lấy file tracklog

- **Strava**: Activity → "…" → Export GPX; hoặc Settings → My Account → Download your data (activities.csv)
- **Garmin Connect**: Activity → ⚙ → Export Original (.fit)
- **Coros**: Activity → Share → Export (.fit)

## Phát triển

```bash
uv run pytest                                   # test
uv run python tests/fixtures/make_fixtures.py   # sinh lại fixture GPX/CSV
uv run python scripts/seed_demo.py --base /tmp/coach-demo   # dữ liệu demo + đo tốc độ trang
```

Quy trình Spec Kit và kiến trúc: xem `CLAUDE.md` và `specs/001-coach-app-rebuild/`.

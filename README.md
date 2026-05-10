# Running Coach App

Web app local quản lý nhiều học viên trên nhiều plan training. Upload tracklog, chọn giáo án + tuần, phân tích tự động, gợi ý AI.

## Cài đặt

```bash
# 1. Cài Python dependencies
pip3 install flask fitparse gpxpy pandas anthropic

# 2. Set API key Claude (để dùng AI feedback)
export ANTHROPIC_API_KEY="sk-ant-..."

# 3. Chạy app
python app.py
# hoặc
bash run.sh

# 4. Mở trình duyệt
# http://localhost:5050
```

## Tính năng

### Quản lý Nhóm & Học viên
- Tạo nhiều nhóm (VD: "Nhóm Marathon A", "Nhóm 5K Mới")
- Mỗi nhóm gán với một giáo án
- Thêm học viên vào nhóm, lọc danh sách theo nhóm

### Upload & Phân tích
- Hỗ trợ **GPX** (Strava, Coros, Suunto, Garmin export)
- Hỗ trợ **FIT** (Garmin native, Coros)
- Hỗ trợ **CSV** (Strava bulk export)
- Khi upload: chọn **giáo án** + **tuần** cụ thể (độc lập với nhóm)
- Tự động parse: distance, pace, HR, cadence, elevation

### Giáo án (Plans)
| Plan | Thời gian | Mục tiêu |
|------|-----------|----------|
| Marathon 27 Tuần | 27 tuần | Full Marathon 42.195km |
| Half Marathon 16 Tuần | 16 tuần | Half Marathon 21.1km |
| 5K 8 Tuần | 8 tuần | 5km |

### So sánh Giáo án
- Map buổi tập vào đúng tuần trong giáo án đã chọn
- Kiểm tra: distance ±20%, pace zone, HR max
- Score 0–100 + badge 🟢🟡🟠🔴
- Cảnh báo cụ thể: quá nhanh, thiếu km, HR cao

### Dashboard
- Tổng km, pace TB, HR TB, compliance %
- Biểu đồ km theo tuần
- Biểu đồ HR trend
- Lọc học viên theo nhóm
- Overview tất cả giáo án với phase visualization

### AI Feedback (cần ANTHROPIC_API_KEY)
- Phân tích 8 buổi gần nhất
- Đánh giá theo từng tuần trong plan
- Gợi ý điều chỉnh bài tập kế tiếp
- Cảnh báo overtraining / undertraining

## Cấu trúc thư mục

```
running-coach-app/
├── app.py              – Flask app chính
├── parsers.py          – Đọc GPX/FIT/CSV
├── analyzer.py         – Phân tích + AI feedback
├── plan.py             – Helpers giáo án
├── plans/
│   ├── marathon_27w.json
│   ├── halfmarathon_16w.json
│   └── 5k_8w.json
├── templates/
│   ├── index.html      – Dashboard chính
│   └── athlete.html    – Chi tiết học viên
├── data/
│   ├── athletes/       – Dữ liệu học viên (JSON)
│   └── groups/         – Dữ liệu nhóm (JSON)
├── uploads/            – File tracklog upload tạm
└── run.sh              – Script khởi động
```

## Luồng sử dụng

### Tạo nhóm mới
1. Mở http://localhost:5050
2. Nhấn **+ Tạo nhóm** → nhập tên, chọn giáo án, ngày bắt đầu
3. Nhóm xuất hiện trong danh sách bên trái

### Upload tracklog
1. Nhập tên học viên (mới hoặc có sẵn)
2. Chọn nhóm (tùy chọn — nếu chọn, giáo án tự điền)
3. Chọn **Giáo án** (bắt buộc: Marathon / Half Marathon / 5K)
4. Chọn **tuần** trong giáo án
5. Chọn loại buổi tập
6. Upload file tracklog → xem kết quả phân tích ngay

### Xem tiến độ học viên
1. Click tên học viên trong danh sách
2. Xem stats tổng hợp, biểu đồ, lịch sử buổi tập
3. Chọn tuần → nhấn **✨ Phân tích ngay** để nhận AI feedback

## Lấy file tracklog

**Strava:**
1. Mở Strava app/web → Activity → "..." → Export GPX

**Garmin:**
- Garmin Connect → Activity → Export Original (.fit)

**Coros:**
- Coros app → Activity → Share → Export (.fit)

## Yêu cầu hệ thống

- Python 3.8+
- macOS / Linux / Windows (WSL)
- RAM: 256MB là đủ
- Không cần internet (trừ AI feedback)

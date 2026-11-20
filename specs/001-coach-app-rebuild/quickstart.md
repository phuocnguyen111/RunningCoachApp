# Quickstart & Validation: Rebuild Running Coach App

Liên quan: [contracts/http-api.md](contracts/http-api.md) · [data-model.md](data-model.md)

## Chuẩn bị

```bash
uv sync                      # tạo .venv Python 3.12 + cài dependency theo uv.lock
uv run pytest                # toàn bộ test phải xanh
bash run.sh                  # http://127.0.0.1:5050
```

AI (tùy chọn): `export ANTHROPIC_API_KEY=...` (hoặc `ant auth login` + `COACH_AI_ENABLED=1`),
tùy chọn `export COACH_AI_MODEL=claude-sonnet-5-5`.

## Kịch bản kiểm tra

| # | Story | Bước | Kết quả mong đợi |
|---|-------|------|------------------|
| V1 | US2 | Tạo nhóm "Test Sub5", giáo án Marathon 27w, bắt đầu 2026-06-01 | Nhóm hiện trong danh sách |
| V2 | US2 | Tạo học viên "Nguyễn Văn A" và "Nguyen Van A" vào nhóm | Hai hồ sơ riêng (`nguyen-van-a`, `nguyen-van-a-2`) |
| V3 | US1 | Upload `tests/fixtures/long_12k_2026-06-17.gpx` cho học viên 1 | Preview đề xuất Marathon 27w, Tuần 3, LONG |
| V4 | US1 | Xác nhận | Badge 🟢, không cảnh báo |
| V5 | US1 | Upload lại cùng file | Preview đánh dấu trùng; xác nhận → `skipped: duplicate` |
| V6 | US1 | Upload `tests/fixtures/easy_6k.gpx` loại EASY | Không có cảnh báo quãng đường |
| V7 | US1 | Upload file `.txt` / GPX hỏng | Thông báo lỗi tiếng Việt, không có file mới trong `uploads/` |
| V8 | US3 | Mở trang học viên 1 | Tổng km, biểu đồ km tuần có cột mục tiêu, lịch sử 2 buổi |
| V9 | US3 | Xóa một buổi, xác nhận | Buổi biến mất, thống kê cập nhật |
| V10 | US4 | Không có thông tin xác thực AI | Nút AI bị vô hiệu kèm giải thích; trang khác bình thường |
| V11 | US4 | Có AI, học viên theo Half Marathon | Nhận xét 4 phần tiếng Việt nói về Half Marathon |
| V12 | US5 | Copy `plans/5k_8w.json` → `plans/test_bad.json`, xóa `weeks`; restart | Log cảnh báo; 3 giáo án hợp lệ vẫn hiện |
| V13 | FR-025 | Copy một file athlete định dạng cũ vào `data/athletes/`; restart | File được nâng cấp (`schema_version: 2`, activity có `id`, `legacy_analysis`); có backup trước migrate |
| V14 | FR-026 | `bash stop.sh` | Thư mục mới trong `data_backup/` |
| V15 | FR-027 | Truy cập từ máy khác trong LAN | Không kết nối được |

## Kiểm tra hiệu năng (SC-007)

`uv run python scripts/seed_demo.py --athletes 50 --activities 200` rồi mở dashboard và một trang học viên:
mỗi trang < 1 giây (DevTools → Network → DOMContentLoaded).

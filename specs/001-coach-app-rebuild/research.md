# Research: Rebuild Running Coach App

**Feature**: [spec.md](spec.md) · **Plan**: [plan.md](plan.md) · **Date**: 2026-11-20

Mỗi mục: Decision / Rationale / Alternatives considered.

## R1. Phiên bản Python & quản lý môi trường

- **Decision**: Python 3.12 trong virtualenv do `uv` quản lý; khai báo dependency trong
  `pyproject.toml` + `uv.lock`. `run.sh` chạy `uv run python app.py`.
- **Rationale**: Python 3.9 đã hết hỗ trợ (10/2025). Anthropic Python SDK 1.x yêu cầu Python ≥ 3.10;
  SDK đang cài là 0.100.0. `uv` đã có sẵn trên máy (cài khi init Spec Kit) và tự tải Python 3.12
  mà không đụng Python hệ thống. Lock file giúp cài lại giống hệt.
- **Alternatives**: Giữ 3.9 + ghim `anthropic<1` — bị loại vì runtime hết hỗ trợ bảo mật và kẹt SDK cũ.
  `pip install` toàn cục như `run.sh` cũ — bị loại vì không tái lập được và cần `--trusted-host`.

## R2. Cấu trúc code

- **Decision**: Package `coach/` với các module một-trách-nhiệm, Flask app factory `create_app(config)`;
  `app.py` ở gốc chỉ là entry point (signal, backup, chạy server).
- **Rationale**: Constitution IV (mỗi module một trách nhiệm) và III (hàm thuần dễ test). App factory
  cho phép test với thư mục dữ liệu tạm. CLAUDE.md cấm blueprint là quy ước cũ cho file đơn; với một
  package nhỏ vẫn đăng ký route trong `coach/web/routes.py` bằng một hàm `register_routes(app)`,
  không cần blueprint.
- **Alternatives**: Giữ `app.py` 500+ dòng — bị loại vì khó test và trộn I/O với logic.

## R3. Lưu trữ JSON an toàn

- **Decision**: Lớp `JsonStore` ghi atomic (`tempfile` cùng thư mục → `os.replace`), một
  `threading.Lock` toàn cục cho mọi thao tác ghi; mỗi document có `schema_version`.
- **Rationale**: Flask dev server chạy đa luồng; ghi đè trực tiếp có thể để lại file nửa vời khi tắt đột ngột
  (Constitution V). Một lock toàn cục đủ cho một người dùng.
- **Alternatives**: SQLite — HLV đã chọn giữ JSON. Lock theo file — phức tạp không cần thiết ở quy mô này.

## R4. Định danh học viên

- **Decision**: `athlete.id` = slug ASCII từ tên (Unicode NFKD bỏ dấu, `đ/Đ → d`, chữ thường,
  ký tự khác `[a-z0-9]` → `-`, gộp `-`), nếu trùng thì thêm hậu tố `-2`, `-3`... Tên gốc có dấu lưu ở
  `athlete.name`. URL và file dùng `id`.
- **Rationale**: Bản cũ thay mọi ký tự không phải ASCII bằng `_`, nên "Nguyễn" và "Nguyen" (và cả
  "Trần"/"Trân") ghi đè cùng một file — vi phạm FR-007/SC-004. ID ổn định cũng an toàn cho đường dẫn.
- **Alternatives**: UUID — an toàn nhưng URL/file khó đọc khi HLV mở thư mục `data/`.

## R5. Định danh buổi tập & xóa

- **Decision**: `activity.id` = 12 ký tự hex ngẫu nhiên (`uuid4().hex[:12]`); API xóa theo id.
- **Rationale**: Bản cũ xóa theo index với phép đảo `orig_idx = len - 1 - loop.index0`, dễ xóa nhầm khi
  danh sách thay đổi giữa lúc render và lúc bấm (FR-021).

## R6. Luồng upload hai bước (preview → confirm)

- **Decision**: `POST /api/uploads` parse file và trả về danh sách buổi tập kèm giáo án/tuần đề xuất
  và cờ trùng; file nằm ở `uploads/_pending/{token}/`. `POST /api/uploads/{token}/confirm` nhận
  lựa chọn cuối cùng của HLV cho từng buổi rồi chấm điểm và lưu. Token pending quá 24h bị dọn khi khởi động.
- **Rationale**: Ngày chạy chỉ biết sau khi parse file, nên muốn tự điền tuần (FR-011) mà vẫn cho HLV
  sửa trước khi lưu thì phải có bước xem trước. Cũng giải quyết CSV nhiều buổi (mỗi buổi chọn loại riêng).
- **Alternatives**: Đọc ngày file ở trình duyệt bằng JS — phải viết lại parser GPX/FIT/CSV bằng JS, bị loại.
  Lưu ngay rồi cho sửa sau — HLV phải sửa thêm một bước, và điểm bị chấm sai trước đó.

## R7. Quy tắc chấm điểm

- **Decision**: Hàm thuần `score_activity(metrics, session_type, week) -> ScoreResult` hiện thực đúng bảng
  FR-013 và ngưỡng FR-014. Hằng số trọng số và ngưỡng đặt trong `coach/scoring.py` (một nơi duy nhất).
  Nhóm loại buổi "aerobic" = {EASY, LONG}. "Khớp mục tiêu tuần" và quy tắc RACE (không chấm HR)
  định nghĩa trong spec FR-013; đây là nguồn duy nhất, research không thêm quy tắc riêng.
- **Rationale**: Theo quyết định của HLV (chấm theo loại buổi). Chuẩn hóa trên tiêu chí áp dụng để buổi
  thiếu HR không bị phạt 30 điểm oan. Không chấm pace/HR cho buổi khác loại trọng tâm, vì nếu so buổi
  EASY với HR tối đa của tuần TEMPO thì gần như luôn đạt, cho 🟢 sai.
- **Thay đổi so với bản cũ**: ngưỡng badge 90/60/30 (code) → 80/60/40 (theo CLAUDE.md, spec FR-014).

## R8. Tính tuần giáo án

- **Decision**: `week_for_date(start_date, run_date, total_weeks) -> int | None`
  = `(run_date - start_date).days // 7 + 1`, trả `None` nếu < 1 hoặc > total_weeks hoặc thiếu start_date.
- **Rationale**: FR-011; ngày tính theo giờ địa phương của buổi chạy (lấy từ `start_time`, đổi sang
  `Asia/Ho_Chi_Minh` nếu file lưu UTC) để buổi chạy sáng sớm không bị lùi một ngày.

## R9. Parser

- **Decision**: Giữ `gpxpy` (GPX) và `fitparse` (FIT); CSV dùng `csv` chuẩn. Mỗi parser trả về
  `list[ParsedActivity]` (GPX/FIT: 1 phần tử, CSV: n phần tử, chỉ lấy dòng chạy bộ). Bỏ `pandas`
  (không dùng). Quãng đường GPX: dùng `length_2d` (bản cũ dùng `length_3d` làm phồng quãng đường khi
  độ cao nhiễu). Cadence FIT: nhân 2 chỉ khi giá trị < 120 (đơn vị một chân).
- **Rationale**: Ít phụ thuộc hơn; CSV nhiều buổi không còn bị gộp thành một buổi giả (spec Edge Cases).

## R10. AI feedback

- **Decision**: Anthropic Python SDK 1.x, `client.beta.messages.create` với model mặc định
  `claude-opus-5-5`, ghi đè qua biến môi trường `COACH_AI_MODEL`; `output_config={"effort": "medium"}`;
  `max_tokens=16000`; bật fallback khi bị từ chối (`betas=["server-side-fallback-2026-07-01"]`,
  `fallbacks="default"`); kiểm tra `stop_reason == "refusal"` trước khi đọc nội dung. System prompt cố định
  (vai trò HLV, cấu trúc 4 phần, tiếng Việt); dữ liệu học viên đặt trong message user dạng JSON.
  Bắt lỗi theo chuỗi: `AuthenticationError` → `RateLimitError` → `APIStatusError` → `APIConnectionError`.
- **Bật/tắt**: `ai_enabled` = có `ANTHROPIC_API_KEY` hoặc `ANTHROPIC_AUTH_TOKEN`, hoặc `COACH_AI_ENABLED=1`
  (dùng khi đã `ant auth login`). Nếu tắt, UI vô hiệu nút (FR-024).
- **Rationale**: Prompt cũ hardcode "Full Marathon ngày 06/12/2026, target 4:30–5:00" cho mọi học viên và
  dùng model đã cũ (`claude-sonnet-4-20250514`). Model cấu hình được theo Constitution VI. Dữ liệu gửi đi
  tối thiểu theo FR-022 / Constitution I.
- **Alternatives**: `claude-sonnet-5-5` rẻ hơn — để HLV tự chọn qua `COACH_AI_MODEL`, không tự hạ model.

## R11. Frontend

- **Decision**: Jinja2 + vanilla JS, tách JS/CSS ra `static/js/*.js`, `static/css/app.css`. Chart.js 4.4.0
  được vendor vào `static/vendor/chart.umd.min.js`; font dùng font hệ thống thay cho Google Fonts.
- **Rationale**: Constitution I/VI — app chạy được khi không có mạng; bản cũ tải Chart.js và font từ CDN.
  Template nhỏ lại, JS test thủ công dễ hơn.

## R12. Migration dữ liệu cũ

- **Decision**: `coach/migrate.py` chạy khi khởi động, idempotent: (1) backup `data/` trước khi đổi;
  (2) chuyển `data/*.json` cũ vào `data/athletes/`; (3) gán `id`, `schema_version: 2` cho athlete/group;
  (4) mỗi activity: gán `id`, chuyển `analysis` cũ sang `legacy_analysis`, chụp `plan_week_snapshot`
  từ giáo án nếu có, chấm lại theo R7; (5) bỏ trường `group.athletes` (thành viên lấy từ `athlete.group_id`,
  hợp nhất nếu hai nơi lệch nhau: ưu tiên `athlete.group_id`); (6) group có `plan_id` null hoặc trỏ tới
  giáo án không tồn tại → gán giáo án mặc định (`marathon_27w` nếu có, không thì giáo án đầu tiên) và
  ghi cảnh báo log để HLV sửa lại.
- **Rationale**: FR-025, Constitution V. Hiện `data/athletes/` trống và có 1 group, nhưng migration vẫn
  phải chạy đúng cho máy khác/backup cũ.

## R13. Bảo mật cơ bản

- **Decision**: Bind `127.0.0.1`; `MAX_CONTENT_LENGTH = 25 MB`; bỏ `app.secret_key` hardcode (không dùng session);
  chuẩn hóa mọi id trước khi ghép đường dẫn và kiểm tra đường dẫn nằm trong thư mục gốc.

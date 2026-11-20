<!--
Sync Impact Report
- Version change: (template) → 1.0.0
- Modified principles: n/a (lần đầu ratify)
- Added sections: Core Principles I–VI, Ràng buộc kỹ thuật, Quy trình phát triển, Governance
- Removed sections: none
- Templates requiring updates: none (plan/spec/tasks templates đọc constitution lúc chạy)
- Follow-up TODOs: none
-->

# Running Coach App Constitution

## Core Principles

### I. Local-first & Riêng tư dữ liệu học viên

- App MUST chạy hoàn toàn trên máy HLV, chỉ lắng nghe `127.0.0.1`.
- Dữ liệu học viên (tên, tracklog, chỉ số sức khỏe) MUST nằm trong `data/` và `uploads/`,
  không được commit vào git, không được gửi ra ngoài.
- Ngoại lệ duy nhất là lời gọi AI feedback: chỉ gửi dữ liệu tối thiểu cần cho phân tích
  (chỉ số buổi tập + tuần giáo án), và chỉ khi HLV chủ động bấm yêu cầu.

Lý do: đây là dữ liệu sức khỏe cá nhân của người khác, HLV là người chịu trách nhiệm.

### II. Giáo án là dữ liệu, không phải code

- Mỗi giáo án là một file `plans/{id}.json` theo một schema được kiểm tra khi khởi động.
- Thêm/sửa giáo án MUST NOT đòi hỏi sửa code Python hoặc template.
- Giáo án sai schema MUST bị bỏ qua kèm cảnh báo rõ ràng, không làm sập app.

### III. Logic phân tích tất định và có test (NON-NEGOTIABLE)

- Parse tracklog, tính tuần giáo án, chấm điểm, tổng hợp tuần MUST là hàm thuần
  (không I/O, không phụ thuộc thời gian thực trừ khi được truyền vào).
- Mọi thay đổi ở các hàm này MUST có test pytest viết trước (red → green).
- Quy tắc chấm điểm (trọng số, ngưỡng badge) MUST được định nghĩa ở một chỗ duy nhất
  và tài liệu (spec/CLAUDE.md) MUST khớp với code.

Lý do: HLV ra quyết định huấn luyện dựa trên điểm số; điểm sai âm thầm là lỗi nghiêm trọng nhất.

### IV. Đơn giản trước

- Stack: Python + Flask + Jinja2, lưu trữ JSON file, frontend vanilla JS + Chart.js.
- Không thêm database, JS framework, build step hay dịch vụ nền nếu chưa có lý do
  được ghi trong mục Complexity Tracking của plan.
- Mỗi module có một trách nhiệm: storage, parsing, analysis, AI, web routes.

### V. Không bao giờ mất dữ liệu

- Ghi file JSON MUST atomic (ghi file tạm rồi rename).
- Thay đổi schema MUST tương thích ngược hoặc có migration tự động, idempotent,
  chạy khi khởi động; dữ liệu cũ MUST đọc được.
- Thao tác xóa MUST có xác nhận ở UI; backup `data/` MUST được tạo khi tắt app an toàn.

### VI. AI là tùy chọn

- Toàn bộ tính năng (upload, phân tích, dashboard) MUST hoạt động khi không có
  thông tin xác thực Anthropic hoặc không có mạng.
- Lỗi AI MUST hiển thị thông báo thân thiện, không làm hỏng trang.
- Model AI MUST cấu hình được qua biến môi trường, có mặc định hợp lý.

## Ràng buộc kỹ thuật

- Ngôn ngữ giao diện và thông báo lỗi: tiếng Việt.
- Không có xác thực người dùng (app một người dùng, local). Không expose ra mạng LAN.
- File upload: chỉ `.gpx`, `.fit`, `.csv`; giới hạn kích thước; tên file và định danh
  MUST được chuẩn hóa để chống path traversal.
- Không có secret hardcode trong code.
- Không comment giải thích WHAT; chỉ comment khi có ràng buộc ẩn.

## Quy trình phát triển

- Tính năng mới đi theo Spec Kit: `/speckit-specify` → (`/speckit-clarify`) →
  `/speckit-plan` → `/speckit-tasks` → (`/speckit-analyze`) → `/speckit-implement`.
- Mỗi feature làm trên branch riêng; `pytest` MUST xanh trước khi merge.
- Sửa template HTML: restart app để kiểm tra (Flask chạy `debug=False`).
- CLAUDE.md MUST được cập nhật khi đổi endpoint, schema dữ liệu hoặc quy tắc chấm điểm.

## Governance

- Constitution này có hiệu lực cao hơn các quy ước khác trong repo; CLAUDE.md là hướng dẫn
  vận hành hằng ngày và không được mâu thuẫn với nó.
- Sửa đổi: cập nhật file này qua `/speckit-constitution`, ghi lý do, tăng version theo
  semver (MAJOR: bỏ/định nghĩa lại nguyên tắc; MINOR: thêm nguyên tắc/mục; PATCH: diễn đạt).
- Mỗi plan MUST có mục Constitution Check; vi phạm phải được biện minh trong Complexity Tracking.

**Version**: 1.0.0 | **Ratified**: 2026-11-20 | **Last Amended**: 2026-11-20

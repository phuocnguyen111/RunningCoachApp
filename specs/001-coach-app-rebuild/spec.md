# Feature Specification: Rebuild Running Coach App

**Feature Branch**: `speckit-rebuild`

**Created**: 2026-11-20

**Status**: Draft — chờ HLV duyệt

**Input**: User description: "Áp dụng Spec Kit làm lại project Running Coach App: web app local giúp
HLV quản lý nhiều học viên chạy bộ trên nhiều giáo án, upload tracklog, so sánh với giáo án,
chấm điểm và gợi ý AI. Chấm quãng đường theo loại buổi; tự tính tuần giáo án từ ngày bắt đầu
của nhóm (cho sửa tay); giữ stack hiện tại."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Upload buổi tập và nhận đánh giá ngay (Priority: P1)

HLV nhận file tracklog (GPX/FIT/CSV) từ học viên, chọn học viên, giáo án, tuần và loại buổi,
rồi upload. App đọc file, so sánh với mục tiêu của tuần đó trong giáo án và trả về điểm,
badge màu và các cảnh báo cụ thể (chạy quá nhanh, HR cao, long run thiếu km...).

**Why this priority**: Đây là giá trị cốt lõi — thay việc HLV tự mở từng file và so tay với giáo án.

**Independent Test**: Với một giáo án có sẵn và một file GPX mẫu, upload cho học viên mới →
thấy kết quả phân tích và buổi tập được lưu vào hồ sơ học viên.

**Acceptance Scenarios**:

1. **Given** học viên thuộc nhóm có ngày bắt đầu 2026-06-01 theo giáo án Marathon 27 tuần,
   **When** HLV chọn file chạy ngày 2026-06-17, **Then** ô tuần được điền sẵn "Tuần 3" và HLV
   vẫn có thể đổi sang tuần khác trước khi lưu.
2. **Given** tuần 3 có long run 12 km, pace mục tiêu 7:00–8:00/km, HR tối đa 148,
   **When** upload buổi LONG 12.5 km, pace 7:20/km, HR TB 145, **Then** điểm là 100, badge 🟢,
   không có cảnh báo.
3. **Given** cùng tuần đó, **When** upload buổi EASY 6 km (không phải long run), **Then** quãng
   đường không bị chấm là "thiếu"; chỉ pace và HR được chấm.
4. **Given** buổi LONG 8 km so với mục tiêu 12 km, **When** upload, **Then** có cảnh báo
   "Long run thiếu quãng đường (8.0 km / 12 km)" và tiêu chí quãng đường không đạt.
5. **Given** học viên đã có buổi cùng ngày với quãng đường lệch < 0.2 km, **When** upload lại
   cùng file, **Then** app báo trùng và không tạo bản ghi mới.
6. **Given** tuần 11 của Marathon 27 tuần có loại trọng tâm TEMPO, **When** upload buổi EASY 8 km
   vào tuần 11, **Then** buổi nhận ⚪ với ghi chú "Giáo án tuần này không có mục tiêu cho buổi EASY",
   không có cảnh báo pace/HR.
7. **Given** file bị hỏng hoặc sai định dạng, **When** upload, **Then** thấy thông báo lỗi tiếng
   Việt dễ hiểu, không có dữ liệu rác được lưu.

---

### User Story 2 - Quản lý nhóm và học viên (Priority: P1)

HLV tạo nhóm (tên, giáo án, ngày bắt đầu, ghi chú), thêm học viên vào nhóm, chuyển học viên
giữa các nhóm, sửa thông tin nhóm, và lọc danh sách học viên theo nhóm trên dashboard.

**Why this priority**: Tuần tự động và giáo án mặc định khi upload phụ thuộc vào nhóm.

**Independent Test**: Tạo nhóm → thêm 2 học viên → chuyển 1 người sang nhóm khác → bộ lọc
dashboard hiển thị đúng thành viên mỗi nhóm.

**Acceptance Scenarios**:

1. **Given** dashboard trống, **When** tạo nhóm "Marathon Sub 4:30" với giáo án Marathon 27 tuần,
   **Then** nhóm xuất hiện trong danh sách kèm giáo án và ngày bắt đầu.
2. **Given** hai học viên "Nguyễn Văn A" và "Nguyen Van A", **When** tạo cả hai, **Then** app
   giữ hai hồ sơ riêng biệt, không ghi đè lẫn nhau.
3. **Given** học viên đang ở nhóm X, **When** chuyển sang nhóm Y, **Then** học viên chỉ còn xuất
   hiện trong nhóm Y; các buổi tập cũ giữ nguyên giáo án đã chấm lúc upload.
4. **Given** tạo nhóm trùng tên với nhóm đã có, **Then** cả hai nhóm tồn tại với định danh khác nhau.

---

### User Story 3 - Xem tiến độ một học viên (Priority: P2)

HLV mở trang học viên để xem: tổng km, số buổi, pace TB, HR TB, tỷ lệ tuân thủ; biểu đồ km
theo tuần (so với mục tiêu tuần) và xu hướng HR; lịch sử buổi tập với điểm, badge, cảnh báo;
và xóa buổi tập nhập nhầm.

**Why this priority**: Biến dữ liệu đã upload thành bức tranh tiến độ để HLV điều chỉnh.

**Independent Test**: Với học viên có ≥ 3 buổi ở 2 tuần khác nhau, trang hiển thị đúng tổng
và biểu đồ km/tuần có cột mục tiêu.

**Acceptance Scenarios**:

1. **Given** học viên có các buổi thuộc 2 giáo án khác nhau, **When** mở trang, **Then** mỗi buổi
   hiển thị mục tiêu của chính giáo án/tuần mà buổi đó được chấm.
2. **Given** tuần 3 mục tiêu 30 km và học viên đã chạy 26 km trong tuần 3, **Then** tuần 3
   được đánh dấu đạt volume (trong ±20%); 20 km thì đánh dấu thiếu volume.
3. **Given** HLV bấm xóa một buổi và xác nhận, **Then** buổi đó biến mất, thống kê và biểu đồ
   cập nhật; nếu không xác nhận thì không có gì thay đổi.
4. **Given** học viên chưa có buổi nào, **Then** trang hiển thị trạng thái trống có hướng dẫn upload.

---

### User Story 4 - Gợi ý AI cho tuần kế tiếp (Priority: P3)

Trên trang học viên, HLV chọn tuần và yêu cầu AI phân tích các buổi gần nhất so với giáo án,
nhận đánh giá tổng quan, phân tích volume/pace/HR, đề xuất điều chỉnh tuần kế tiếp và long run kế tiếp.

**Why this priority**: Có giá trị nhưng là tùy chọn; app phải dùng được hoàn toàn khi không có AI.

**Independent Test**: Có thông tin xác thực → nhận được nhận xét tiếng Việt; không có → thấy
thông báo tính năng AI chưa được cấu hình, phần còn lại của trang vẫn hoạt động.

**Acceptance Scenarios**:

1. **Given** học viên theo giáo án Half Marathon 16 tuần, **When** yêu cầu AI, **Then** nhận xét
   nói về mục tiêu Half Marathon (không mặc định là Full Marathon).
2. **Given** chưa cấu hình AI, **When** mở trang học viên, **Then** nút AI bị vô hiệu hóa kèm giải thích.
3. **Given** dịch vụ AI lỗi hoặc mất mạng, **When** yêu cầu, **Then** thấy thông báo lỗi thân thiện
   và có thể thử lại.

---

### User Story 5 - Xem tổng quan giáo án (Priority: P3)

Trên dashboard, HLV xem từng giáo án: các phase, km mỗi tuần, tuần giảm tải, tuần taper, tuần race.

**Why this priority**: Hỗ trợ tham khảo; không ảnh hưởng luồng chính.

**Independent Test**: Thêm một file giáo án mới đúng schema → khởi động lại → giáo án xuất hiện
trong tổng quan và trong form upload mà không sửa code.

**Acceptance Scenarios**:

1. **Given** 3 giáo án có sẵn, **When** chọn từng giáo án, **Then** biểu đồ km/tuần hiển thị đúng
   số tuần và tô màu theo phase.
2. **Given** một file giáo án sai schema, **When** khởi động, **Then** giáo án đó không xuất hiện,
   có cảnh báo trong log, các giáo án khác vẫn hoạt động.

---

### Edge Cases

- Ngày chạy trước ngày bắt đầu của nhóm hoặc sau tuần cuối giáo án → không tự điền tuần;
  HLV có thể chọn tay hoặc để trống tuần; buổi có giáo án nhưng không có tuần được lưu và
  không được chấm (badge ⚪).
- Học viên không thuộc nhóm nào → không tự tính tuần; HLV chọn giáo án và tuần tay.
- File không có dữ liệu HR → tiêu chí HR bị bỏ qua, điểm tính trên các tiêu chí còn lại.
- File không có thời gian → không tính được pace; ngày lấy theo ngày upload và báo cho HLV.
- Không có tiêu chí nào áp dụng được → không chấm điểm (⚪ "Không có tiêu chí so sánh").
- CSV chứa nhiều hoạt động → mỗi hoạt động chạy bộ trở thành một buổi riêng (không gộp).
- File quá lớn (> 25 MB) → từ chối với thông báo.
- Tên học viên có dấu tiếng Việt, khoảng trắng, ký tự đặc biệt → được hỗ trợ đầy đủ.
- Giáo án mà buổi tập tham chiếu đã bị xóa → buổi tập vẫn hiển thị với kết quả đã lưu.

## Requirements *(mandatory)*

### Functional Requirements

**Giáo án**

- **FR-001**: System MUST tự nhận các giáo án đặt trong thư mục giáo án, kiểm tra schema, và bỏ
  qua giáo án không hợp lệ kèm cảnh báo.
- **FR-002**: Mỗi tuần giáo án MUST có: số tuần, phase, tên phase, tổng km tuần, km long run,
  loại buổi trọng tâm, khoảng pace mục tiêu, HR tối đa, ghi chú; tùy chọn cờ giảm tải/taper/race.

**Nhóm & học viên**

- **FR-003**: HLV MUST tạo được nhóm với tên (bắt buộc), giáo án (bắt buộc), ngày bắt đầu (tùy chọn), ghi chú.
- **FR-004**: HLV MUST sửa được tên, giáo án, ngày bắt đầu, ghi chú của nhóm.
- **FR-005**: HLV MUST tạo được học viên, tùy chọn gán vào một nhóm; mỗi học viên thuộc tối đa một nhóm.
- **FR-006**: HLV MUST chuyển được học viên sang nhóm khác hoặc bỏ khỏi nhóm.
- **FR-007**: Hai tên học viên khác nhau (kể cả chỉ khác dấu) MUST là hai hồ sơ khác nhau.
- **FR-008**: Dashboard MUST lọc được học viên theo nhóm mà không tải lại trang.

**Upload & phân tích**

- **FR-009**: System MUST chấp nhận file GPX, FIT và CSV (định dạng export Strava), tối đa 25 MB.
- **FR-010**: System MUST trích xuất: ngày, giờ bắt đầu, quãng đường, thời lượng, pace TB, HR TB,
  HR max, cadence TB, độ cao tích lũy, chuỗi HR rút gọn (nếu có).
- **FR-011**: Khi HLV chọn học viên thuộc nhóm có ngày bắt đầu, System MUST đề xuất sẵn giáo án
  của nhóm và tuần = ⌊(ngày chạy − ngày bắt đầu) / 7⌋ + 1 nếu nằm trong phạm vi giáo án;
  HLV MUST sửa được cả hai trước khi lưu.
- **FR-012**: Giáo án chọn ở form MUST được ưu tiên hơn giáo án của nhóm; mỗi buổi tập MUST
  lưu giáo án, tuần và mục tiêu của tuần tại thời điểm chấm.
- **FR-013**: System MUST chấm điểm theo bảng tiêu chí sau, chỉ trên các tiêu chí áp dụng được,
  quy về thang 0–100:

  Một buổi **khớp mục tiêu tuần** khi loại buổi trùng loại trọng tâm của tuần, hoặc cả hai cùng
  thuộc nhóm aerobic {EASY, LONG}.

  | Tiêu chí | Trọng số | Áp dụng khi | Đạt khi |
  |----------|----------|-------------|---------|
  | Quãng đường | 30 | Buổi LONG và tuần có km long run > 0 | trong ±20% km long run |
  | Pace | 40 | Buổi khớp mục tiêu tuần và tính được pace | pace TB nằm trong khoảng mục tiêu |
  | HR | 30 | Buổi khớp mục tiêu tuần, có HR, và không phải buổi RACE | HR TB ≤ HR tối đa |

  Điểm = tổng trọng số đạt / tổng trọng số áp dụng × 100, làm tròn. Buổi không khớp mục tiêu tuần
  (vd EASY trong tuần trọng tâm TEMPO) không được chấm pace/HR vì giáo án không có mục tiêu cho loại
  buổi đó; nếu cũng không có tiêu chí quãng đường thì buổi nhận ⚪ kèm ghi chú
  "Giáo án tuần này không có mục tiêu cho buổi <loại>".
- **FR-014**: Badge MUST theo ngưỡng: 🟢 ≥ 80 · 🟡 60–79 · 🟠 40–59 · 🔴 < 40 · ⚪ không chấm được.
- **FR-015**: Mỗi tiêu chí không đạt MUST sinh một cảnh báo tiếng Việt nêu giá trị thực tế và mục tiêu
  (vd "Chạy QUÁ NHANH (6:10/km, mục tiêu 7:00–8:00/km)").
- **FR-016**: System MUST phát hiện buổi trùng (cùng học viên, cùng ngày, quãng đường lệch < 0.2 km)
  và không lưu lại.
- **FR-017**: File tracklog gốc MUST được lưu theo học viên để tra cứu sau; file của lần upload thất bại
  hoặc trùng MUST bị xóa.

**Tiến độ học viên**

- **FR-018**: Trang học viên MUST hiển thị tổng km, số buổi, pace TB, HR TB, tỷ lệ buổi đạt (badge 🟢/🟡).
- **FR-019**: System MUST tổng hợp theo (giáo án, tuần): km thực tế, số buổi, km mục tiêu, và trạng thái
  volume tuần (đạt nếu trong ±20% tổng km tuần; thiếu; vượt; đang diễn ra nếu tuần chưa kết thúc).
- **FR-020**: Trang học viên MUST có biểu đồ km thực tế so với mục tiêu theo tuần và biểu đồ xu hướng HR.
- **FR-021**: HLV MUST xóa được một buổi tập sau khi xác nhận; định danh buổi tập MUST ổn định
  (không phụ thuộc thứ tự hiển thị).

**AI**

- **FR-022**: HLV MUST yêu cầu được nhận xét AI cho một học viên và một tuần; dữ liệu gửi đi gồm
  tối đa 8 buổi gần nhất (chỉ số + kết quả chấm), mục tiêu tuần đó và tuần kế, thông tin giáo án
  (tên, cự ly mục tiêu) và ghi chú nhóm. Không gửi file tracklog, tọa độ GPS hay chuỗi HR.
- **FR-023**: Nhận xét MUST bằng tiếng Việt, gồm 4 phần: đánh giá tổng quan, phân tích chi tiết
  (volume/pace/HR), điều chỉnh tuần kế tiếp, gợi ý long run kế tiếp.
- **FR-024**: Khi AI chưa cấu hình, UI MUST vô hiệu hóa tính năng kèm giải thích; khi lỗi, MUST hiển thị
  thông báo và cho thử lại.

**Vận hành & dữ liệu**

- **FR-025**: Dữ liệu hiện có (học viên, nhóm, buổi tập ở định dạng cũ) MUST được đọc và nâng cấp
  tự động khi khởi động, không mất bản ghi nào; điểm của buổi cũ MUST được chấm lại theo quy tắc mới
  và giữ lại điểm cũ để tham khảo.
- **FR-026**: Khi tắt app an toàn, System MUST sao lưu toàn bộ dữ liệu vào một thư mục có dấu thời gian.
- **FR-027**: App MUST chỉ truy cập được từ chính máy HLV.

### Key Entities

- **Plan (Giáo án)**: định danh, tên, mô tả, cự ly mục tiêu, số tuần, danh sách tuần.
- **PlanWeek (Tuần giáo án)**: số tuần, phase, tổng km, km long run, loại buổi trọng tâm, khoảng pace,
  HR tối đa, ghi chú, cờ giảm tải/taper/race.
- **Group (Nhóm)**: định danh, tên, giáo án, ngày bắt đầu, ghi chú. Có nhiều học viên.
- **Athlete (Học viên)**: định danh ổn định, tên hiển thị (giữ dấu), nhóm hiện tại (tùy chọn), danh sách buổi tập.
- **Activity (Buổi tập)**: định danh ổn định, chỉ số đo được, giáo án + tuần + loại buổi, ảnh chụp mục tiêu
  tuần lúc chấm, kết quả chấm (điểm, badge, từng tiêu chí, cảnh báo), file gốc.
- **WeekSummary (Tổng hợp tuần)**: dẫn xuất — km thực tế/mục tiêu, số buổi, trạng thái volume.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: HLV upload và xem kết quả chấm một buổi tập trong dưới 30 giây kể từ khi mở dashboard,
  không cần chọn tuần thủ công khi học viên thuộc nhóm có ngày bắt đầu.
- **SC-002**: 100% buổi EASY/TEMPO/SPEED/MP không còn bị cảnh báo "thiếu quãng đường" do so với km cả tuần.
- **SC-003**: Kết quả chấm điểm khớp bảng FR-013/FR-014 trên 100% ca kiểm thử chuẩn (bộ ca mẫu cố định).
- **SC-004**: 0 bản ghi bị mất hoặc ghi đè khi nâng cấp từ dữ liệu cũ và khi có hai học viên trùng tên không dấu.
- **SC-005**: Mọi trang và chức năng không liên quan AI hoạt động bình thường khi không có cấu hình AI.
- **SC-006**: Thêm giáo án mới chỉ bằng một file dữ liệu, không sửa code, trong dưới 10 phút.
- **SC-007**: Trang dashboard và trang học viên tải trong dưới 1 giây với 50 học viên × 200 buổi tập.

## Assumptions

- Một HLV duy nhất dùng app trên máy cá nhân; không có đăng nhập, không có nhiều người dùng đồng thời.
- Giáo án hiện chỉ có một khoảng pace/HR cho loại buổi trọng tâm của tuần; buổi khác loại không có
  mục tiêu riêng nên không được chấm pace/HR (chỉ LONG còn được chấm quãng đường). Mở rộng giáo án
  theo từng buổi là ngoài phạm vi bản rebuild này.
- Buổi RACE không chấm HR vì nhịp tim khi thi đấu vượt ngưỡng tập luyện là bình thường.
- Loại buổi gồm: EASY, LONG, TEMPO, SPEED, MP, RACE.
- Tuần giáo án tính từ ngày bắt đầu của nhóm; tuần 1 gồm 7 ngày kể từ ngày bắt đầu.
- CSV theo định dạng export của Strava; các định dạng CSV khác được hỗ trợ ở mức tốt nhất có thể.
- Ngoài phạm vi: đồng bộ tự động từ Strava/Garmin/Coros, ứng dụng di động, xuất báo cáo PDF,
  sửa nội dung giáo án qua UI, đổi tên học viên.

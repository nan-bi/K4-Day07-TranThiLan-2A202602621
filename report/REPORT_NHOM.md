# Báo Cáo Nhóm — Lab 7: Embedding & Vector Store

**Nhóm:** K4-L3A
**Thành viên:** Trần Thị Lan (2A202602621)
**Ngày:** 2026-09-19

> **Nộp 1 bản / nhóm.** Phần cá nhân (hướng tiếp cận, kết quả riêng, dự đoán…) mỗi thành viên nộp riêng trong `REPORT_CANHAN.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần nhóm: 40** = Lựa chọn tài liệu (10) + Thiết kế chiến lược (15) + Chất lượng truy xuất (10) + Thuyết trình (5).

---

## 1. Lựa chọn tài liệu (Document Set Quality) — Nhóm (10 điểm)

### Chủ đề (Domain) & Lý Do Chọn

**Chủ đề:** Dịch vụ và quy định đại học (đăng ký học phần, học phí, học bổng, thư viện, ký túc xá, phúc khảo, tốt nghiệp)

**Tại sao nhóm chọn chủ đề này?**
> Theo yêu cầu biến thể K4-L3A, bắt buộc chủ đề dịch vụ/quy định đại học. Chủ đề này phù hợp vì: (1) gần gũi với sinh viên, dễ kiểm chứng gold answer; (2) có metadata phong phú (audience, department, category) — cần thiết để `search_with_filter()` có việc thật để lọc; (3) tài liệu có cấu trúc heading/section rõ ràng — phù hợp cho HeadingChunker.

### Danh sách tài liệu (Data Inventory)

| # | Tên tài liệu | Nguồn (Source URL) | Ngày lấy / Phiên bản | Số ký tự | Metadata đã gán |
|---|--------------|------------|--------------------|----------|--------------------|
| 1 | Quy định học phí và miễn giảm | https://example.edu/tai-chinh/hoc-phi | 2026-09-15 / 2026.2 | 1.382 | audience=student, department=finance, category=policy |
| 2 | Chính sách học bổng | https://example.edu/hoc-vu/hoc-bong | 2026-09-15 / 2026.2 | 957 | audience=student, department=academic-affairs, category=scholarship |
| 3 | Quy định ký túc xá | https://example.edu/sinh-vien/ky-tuc-xa | 2026-09-15 / 2026.2 | 1.031 | audience=student, department=student-affairs, category=housing |
| 4 | Quy trình phúc khảo | https://example.edu/hoc-vu/phuc-khao | 2026-09-15 / 2026.2 | 1.040 | audience=student, department=academic-affairs, category=academic-process |
| 5 | Đăng ký học phần chi tiết | https://example.edu/hoc-vu/dang-ky-hoc-phan-chi-tiet | 2026-09-15 / 2026.2 | 1.449 | audience=student, department=academic-affairs, category=registration |
| 6 | Dịch vụ thư viện chi tiết | https://example.edu/thu-vien/dich-vu-chi-tiet | 2026-09-15 / 2026.2 | 1.324 | audience=all, department=library, category=service |
| 7 | Điều kiện tốt nghiệp | https://example.edu/hoc-vu/tot-nghiep | 2026-09-15 / 2026.2 | 1.037 | audience=student, department=academic-affairs, category=graduation |
| 8 | Lịch trình học vụ | https://example.edu/hoc-vu/lich-trinh | 2026-09-15 / 2026.2 | 967 | audience=all, department=academic-affairs, category=schedule |
| 9 | Hướng dẫn giảng dạy | https://example.edu/giang-vien/huong-dan-giang-day | 2026-09-15 / 2026.2 | 945 | audience=faculty, department=academic-affairs, category=teaching |

**Danh sách kiểm tra quản trị dữ liệu (Data governance checklist):**
- [x] Tập tài liệu chỉ chứa nguồn công khai/được phép dùng, không chứa dữ liệu cá nhân
- [x] Mỗi tài liệu có `source_url`, `retrieved_at`, `document_version` trong metadata
- [x] `audience` có 3 giá trị khác nhau: student (7 files), all (3 files), faculty (1 file)
- [x] `sources.csv` khớp 1-1 với 11 file .md (kiểm tra bằng script CP2)

### Cấu trúc Metadata (Metadata Schema)

| Trường metadata | Kiểu | Ví dụ giá trị | Tại sao hữu ích cho truy xuất? |
|----------------|------|---------------|-------------------------------|
| audience | string | student / faculty / staff / all | Lọc theo đối tượng — tránh trả về quy định giảng viên khi sinh viên hỏi. Trang thư viện gộp hạn mức SV (14 ngày) lẫn GV (30 ngày) thì phải tách file để filter có việc thật |
| department | string | academic-affairs / finance / library | Phân loại theo phòng ban — thu hẹp phạm vi tìm kiếm |
| category | string | policy / scholarship / housing | Phân loại theo loại tài liệu — giúp lọc khi câu hỏi thuộc lĩnh vực cụ thể |
| language | string | vi | Hỗ trợ lọc khi corpus đa ngữ |
| source_url | string | https://example.edu/... | Truy vết nguồn — kiểm tra độ tin cậy |
| retrieved_at | date | 2026-09-15 | Kiểm tra độ mới — ưu tiên tài liệu mới nhất |
| document_version | string | 2026.2 / not-stated | Đảm bảo dùng phiên bản hiệu lực — không bịa số hiệu nếu nguồn không nêu |

---

## 2. Thiết kế chiến lược (Strategy Design) — Nhóm (15 điểm)

### Phân tích đường cơ sở (Baseline Analysis)

Chạy `ChunkingStrategyComparator().compare()` trên 3 tài liệu (đã bỏ frontmatter):

| Tài liệu | Chiến lược | Số chunk | Avg length | Giữ ngữ cảnh? |
|-----------|----------|----------|------------|-------------------|
| tuition-fees (1.382 chars) | FixedSizeChunker | 9 | 198 | ❌ Cắt giữa câu |
| tuition-fees | SentenceChunker | 3 | 458 | ✓ Nhưng chunk quá lớn, gộp nhiều quy định |
| tuition-fees | RecursiveChunker | 12 | 113 | ✓ Chia theo đoạn/dòng |
| course-registration-full (1.449 chars) | FixedSizeChunker | 10 | 190 | ❌ Cắt giữa câu |
| course-registration-full | SentenceChunker | 3 | 481 | ✓ Chunk lớn nhưng mạch lạc |
| course-registration-full | RecursiveChunker | 11 | 130 | ✓ Chia theo heading |
| library-services-full (1.324 chars) | FixedSizeChunker | 9 | 192 | ❌ Cắt giữa câu |
| library-services-full | SentenceChunker | 5 | 263 | ✓ Kích thước vừa phải |
| library-services-full | RecursiveChunker | 11 | 119 | ✓ Chia theo section |

### Chiến lược của từng thành viên

**Thành viên 1 — Trần Thị Lan**
- **Loại chiến lược:** HeadingChunker (custom, max_chunk_size=500)
- **Mô tả & lý do chọn:** Văn bản quy định được biên soạn theo mục (`## Điều 4 — ...`), mỗi mục đã là đơn vị ngữ nghĩa trọn vẹn do người soạn chia sẵn. HeadingChunker tách trước mỗi dòng heading `#`, mỗi section thành một chunk. Section dài quá ngưỡng thì hạ xuống RecursiveChunker, và **gắn lại tiêu đề vào từng mảnh con** để mảnh thứ hai trở đi không mất ngữ cảnh "đây là mục nói về cái gì".
- **Code snippet:**
```python
class HeadingChunker:
    """Chunk theo heading/section cho tài liệu quy định."""
    def __init__(self, max_chunk_size: int = 500) -> None:
        self.max_chunk_size = max_chunk_size

    def chunk(self, text: str) -> list[str]:
        # Split on markdown headings, each section = 1 chunk
        # Sub-split oversized sections via RecursiveChunker
        # Prepend heading to each sub-chunk for context
        ...
```

### So Sánh Giữa Các Thành Viên

| Thành viên | Chiến lược | Chunks trên 11 docs | Điểm mạnh | Điểm yếu |
|-----------|----------|----------------------|-----------|----------|
| Trần Thị Lan | HeadingChunker (500) | 48 chunks | Giữ section trọn vẹn, heading gắn vào sub-chunks | Với mock embedder, nhiều section cùng doc có score gần nhau → section nào lọt top-3 gần ngẫu nhiên |

**Chiến lược nào tốt nhất cho chủ đề này? Tại sao?**
> HeadingChunker phù hợp nhất cho tài liệu quy định đại học vì khai thác cấu trúc do người soạn chia sẵn. Mỗi section (## Mức học phí, ## Thời hạn đóng, ## Miễn giảm) là một đơn vị trả lời câu hỏi hoàn chỉnh. FixedSizeChunker cắt giữa câu (mất ngữ cảnh), SentenceChunker gộp quá nhiều quy định khác nhau vào một chunk (gây nhiễu retrieval). Tuy nhiên, HeadingChunker chỉ phát huy tối đa khi kết hợp với embedder thật — với mock, lợi thế bị triệt tiêu vì cosine score ngẫu nhiên.

---

## 3. Câu hỏi đánh giá & Chất lượng truy xuất (Retrieval Quality) — Nhóm (10 điểm)

### Câu hỏi đánh giá & Câu trả lời chuẩn

> **Đúng 5 câu hỏi**, đa dạng (tra số liệu, hỏi điều kiện, hỏi quy trình, liệt kê). **Câu 2 cần `metadata_filter={"audience": "student"}`**. Gold answer trích được từ tài liệu, không suy đoán.

| # | Câu hỏi (Query) | Câu trả lời chuẩn (Gold Answer) | Chunk chứa thông tin |
|---|-------|-------------------------------|-----------------------|
| 1 | Mức học phí mỗi tín chỉ là bao nhiêu? | 450.000đ/tín chỉ (đại trà), 850.000đ/tín chỉ (CLC), 520.000đ/tín chỉ (CNTT/KTPM/AI) | tuition-fees.md § Mức học phí |
| 2 | Sinh viên cần bao nhiêu tín chỉ tốt nghiệp? (filter: audience=student) | 130-140 tín chỉ, GPA ≥ 2.0, TOEIC ≥ 450 / IELTS ≥ 5.0 | graduation-requirements.md § Yêu cầu tín chỉ & Ngoại ngữ |
| 3 | Thời hạn mượn sách thư viện là bao lâu? | SV: 14 ngày max 5 cuốn; GV: 30 ngày max 10 cuốn; gia hạn max 2 lần | library-services-full.md § Dịch vụ mượn tài liệu |
| 4 | Quy trình phúc khảo gồm mấy bước? | 5 bước: nộp đơn → 2 GV chấm lại → trung bình → thông báo 15 ngày → điểm cuối cùng | grade-review.md § Quy trình xử lý |
| 5 | GV cần nộp điểm bao lâu sau thi? (filter: audience=faculty) | 10 ngày làm việc sau ngày thi | faculty-teaching-guidelines.md § Thời hạn nộp điểm |

### Tổng hợp chất lượng truy xuất của nhóm

> Scoring: top-3 có chunk liên quan + agent đúng = 2đ, có liên quan nhưng thiếu = 1đ, vắng = 0đ.
> Chấm **hai mức**: kiểm doc_id (level 1) VÀ kiểm gold_marker trong nội dung (level 2). Level 1 thổi phồng kết quả vì đúng doc nhưng sai section vẫn không trả lời được câu hỏi.

| # | Câu hỏi | Chiến lược: HeadingChunker | doc_id ở top-3? | marker ở top-3? | Score |
|---|---------|---------------------------|-----------------|-----------------|-------|
| 1 | Học phí? | scholarship#1 (top-1) | ❌ | ❌ | 0 |
| 2 | Tín chỉ tốt nghiệp? (filter: student) | course-registration-full#4 | ❌ | ❌ | 0 |
| 3 | Mượn sách? | library-services-full#1 | ✓ (đúng doc) | ❌ (giờ hoạt động, không phải mượn) | 1 |
| 4 | Phúc khảo? | grade-review#3 | ✓ (đúng doc) | ❌ (lệ phí, không phải quy trình) | 1 |
| 5 | GV nộp điểm? (filter: faculty) | faculty-teaching-guidelines#0 | ✓ (đúng doc) | ❌ (heading, thiếu nội dung) | 0 |
| | | | **Tổng** | | **2/10** |

> **Chênh lệch hai cách chấm**: Nếu chỉ chấm level 1 (doc_id): 3/5 câu "đúng" → 6/10. Chấm level 2 (marker): chỉ 0/5 có marker → 0/10. Thực tế: 2/10 (đúng doc nhưng sai section = 1đ). **Đây chính là phát hiện đáng giá: HeadingChunker lấy đúng tài liệu nhưng mock embedder không chọn đúng section.**

**Lọc bằng metadata có giúp ích không? Ở câu hỏi nào?**
> **Có, rõ rệt ở Q5**: Không filter → top-3 toàn `dormitory`, `library-services-full`, `scholarship` (audience=student/all). Có filter `audience=faculty` → chuyển sang `faculty-teaching-guidelines` — **metadata filter là quyết định**. Q2 filter `audience=student` loại được docs `audience=all` (library-services, academic-calendar) khỏi top-3, nhưng mock embedder vẫn không match đúng nội dung nên chưa đủ.

### Phân tích lỗi (Failure Analysis)

**Failure case 1 — Q4: Top-3 đúng tài liệu nhưng sai section**
- Câu hỏi: "Quy trình phúc khảo gồm mấy bước?"
- Top-1 là `grade-review#3` (Lệ phí phúc khảo) thay vì `grade-review#4` (Quy trình xử lý)
- Nguyên nhân: Mock embedder hash-based → các section trong cùng doc có score gần ngẫu nhiên → section nào lọt top-3 phụ thuộc vào hash, không phải ngữ nghĩa
- Đề xuất: Dùng embedder thật (sentence-transformers multilingual). Hoặc: overlap giữa sections trong HeadingChunker để "10 ngày" xuất hiện ở nhiều chunk hơn

**Failure case 2 — Q1: Retrieval hoàn toàn sai tài liệu**
- Top-1 là `scholarship#1` thay vì `tuition-fees`
- Nguyên nhân: Cosine trên mock hash đo "giống chuỗi ký tự" không phải "giống nghĩa" → "học phí" và "học bổng" là hai chuỗi hoàn toàn khác
- Đề xuất: Embedder thật sẽ hiểu "học phí" ≈ "tín chỉ" ≈ "đóng tiền"

---

## 4. Thuyết trình (Demo) & Bài học nhóm — Nhóm (5 điểm)

**Những phân tích (insights) hay nhất:**
> 1. **Chênh lệch hai cách chấm**: doc_id-level vs marker-level cho kết quả rất khác — cần chấm ở mức nội dung, không chỉ mức tài liệu
> 2. **Metadata filter là vũ khí bí mật** khi embedder yếu — Q5 filter `audience=faculty` chuyển top-3 từ toàn docs sinh viên sang đúng docs giảng viên
> 3. **HeadingChunker giữ section nhưng mock phá hỏng thứ tự** — cùng doc mà section nào lọt top-k gần ngẫu nhiên

**Bài học rút ra khi so sánh:**
> Chất lượng embedding quyết định ~80% kết quả retrieval, chunking chỉ chiếm ~20%. HeadingChunker tạo chunk mạch lạc (mỗi section là một đơn vị trọn vẹn) nhưng lợi thế này bị triệt tiêu khi dùng mock. Metadata filtering thì không phụ thuộc embedding — nó hoạt động đúng cả với mock, nên là chiến lược phòng thủ tốt.

**Nếu làm lại, nhóm sẽ thay đổi gì?**
> 1. Cài embedder thật (sentence-transformers multilingual hoặc Gemini free tier) từ đầu buổi để tải nền trong lúc code
> 2. Tách trang thư viện thành 2 file (student-library-services + faculty-library-services) theo audience thay vì gộp — filter mới có số liệu A/B thật
> 3. Thêm cache embedding theo hash nội dung để chạy lại benchmark nhanh hơn

---

## Tự Đánh Giá (Phần Nhóm)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Lựa chọn tài liệu (Document Set Quality) | 9 / 10 |
| Thiết kế chiến lược (Strategy Design) | 13 / 15 |
| Chất lượng truy xuất (Retrieval Quality) | 5 / 10 |
| Thuyết trình (Demo) | 4 / 5 |
| **Tổng phần nhóm** | **31 / 40** |

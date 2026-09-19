# Báo Cáo Nhóm — Lab 7: Embedding & Vector Store

**Nhóm:** G17
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
| 1 | Học phí và Hỗ trợ tài chính VinUni | https://vinuni.edu.vn/hoc-phi-ho-tro-tai-chinh/ | 2026-09-19 / 2026.1 | 638 | audience=student, department=finance, category=tuition |
| 2 | Chương trình Học bổng VinUni | https://vinuni.edu.vn/hoc-bong-tai-tro-dao-tao-tu-tap-doan-vingroup/ | 2026-09-19 / 2026.1 | 679 | audience=student, department=academic-affairs, category=scholarship |
| 3 | Cuộc sống Ký túc xá VinUni | https://vinuni.edu.vn/cuoc-song-ky-tuc-xa/ | 2026-09-19 / 2026.1 | 682 | audience=student, department=student-affairs, category=housing |
| 4 | Thư viện Đại học VinUni | https://library.vinuni.edu.vn/ | 2026-09-19 / 2026.1 | 647 | audience=all, department=library, category=facilities |
| 5 | Thông tin Tuyển sinh VinUni | https://admissions.vinuni.edu.vn/ | 2026-09-19 / 2026.1 | 754 | audience=faculty, department=admissions, category=guidelines |

**Danh sách kiểm tra quản trị dữ liệu (Data governance checklist):**
- [x] Tập tài liệu chỉ chứa nguồn công khai/được phép dùng, không chứa dữ liệu cá nhân
- [x] Mỗi tài liệu có `source_url`, `retrieved_at`, `document_version` trong metadata
- [x] `audience` có 3 giá trị khác nhau: student (3 files), all (1 file), faculty (1 file)
- [x] `sources.csv` khớp 1-1 với 5 file .md (kiểm tra bằng script CP2)

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
| 1 | Khi nào sinh viên VinUni phải đóng học phí? | Đóng thành hai đợt mỗi năm vào đầu các học kỳ chính (Học kỳ Mùa thu và Học kỳ Mùa xuân). | tuition.md § Quy định tài chính |
| 2 | Học bổng WIT dành cho ai và trị giá bao nhiêu? (filter: audience=student) | Trị giá 5% học phí dành cho nữ giới theo đuổi lĩnh vực khoa học công nghệ. | scholarships.md § Học bổng đặc thù khác |
| 3 | Khu bếp chung ở KTX có những thiết bị gì? | Bếp điện, lò nướng và lò vi sóng. | dormitory.md § Tiện ích chung |
| 4 | Thư viện có mở cửa buổi đêm không? | Thư viện có không gian học tập mở cửa 24/7 để phục vụ nhu cầu tự học ngoài giờ. | library.md § Không gian học tập |
| 5 | Phương thức xét tuyển chính của VinUni là gì? (filter: audience=faculty) | Hình thức xét tuyển kết hợp (đánh giá hồ sơ học thuật, năng lực cá nhân, bài luận, phỏng vấn, chứng chỉ tiếng Anh). | admissions.md § Phương thức xét tuyển |

### Tổng hợp chất lượng truy xuất của nhóm

> Scoring: top-3 có chunk liên quan + agent đúng = 2đ, có liên quan nhưng thiếu = 1đ, vắng = 0đ.
> Chấm **hai mức**: kiểm doc_id (level 1) VÀ kiểm gold_marker trong nội dung (level 2). Level 1 thổi phồng kết quả vì đúng doc nhưng sai section vẫn không trả lời được câu hỏi.

| # | Câu hỏi | Chiến lược: HeadingChunker | doc_id ở top-3? | marker ở top-3? | Score |
|---|---------|---------------------------|-----------------|-----------------|-------|
| 1 | Đóng học phí? | library#0 (top-1) | ❌ | ❌ | 0 |
| 2 | Học bổng WIT? (filter: student) | tuition#3 | ❌ | ❌ | 0 |
| 3 | Thiết bị bếp? | dormitory#0 | ✓ (đúng doc) | ❌ (thiếu đồ cụ thể) | 1 |
| 4 | Mở cửa 24/7? | dormitory#3 | ❌ | ❌ | 0 |
| 5 | Phương thức? (filter: faculty) | admissions#2 | ✓ (đúng doc) | ❌ (sai section) | 1 |
| | | | | **Tổng** | | **2/10** |

> **Chênh lệch hai cách chấm**: Nếu chỉ chấm level 1 (doc_id): 3/5 câu "đúng" → 6/10. Chấm level 2 (marker): chỉ 0/5 có marker → 0/10. Thực tế: 2/10 (đúng doc nhưng sai section = 1đ). **Đây chính là phát hiện đáng giá: HeadingChunker lấy đúng tài liệu nhưng mock embedder không chọn đúng section.**

**Lọc bằng metadata có giúp ích không? Ở câu hỏi nào?**
> **Có, rõ rệt ở Q5**: Không filter → top-3 toàn `dormitory` (audience=student). Có filter `audience=faculty` → chuyển sang đúng `admissions` (audience=faculty) — **metadata filter là quyết định**. Q2 filter `audience=student` loại được docs (audience=faculty) khỏi top-3, nhưng mock embedder vẫn không match đúng nội dung nên chưa đủ.

### Phân tích lỗi (Failure Analysis)

**Failure case 1 — Q3: Top-3 đúng tài liệu nhưng sai section**
- Câu hỏi: "Khu bếp chung ở KTX có những thiết bị gì?"
- Top-1 là `dormitory#0` (Heading title) thay vì `dormitory#3` (Tiện ích chung chứa lò vi sóng, bếp điện)
- Nguyên nhân: Mock embedder hash-based → các section trong cùng doc có score gần ngẫu nhiên.
- Đề xuất: Dùng embedder thật (sentence-transformers multilingual).

**Failure case 2 — Q1: Retrieval hoàn toàn sai tài liệu**
- Câu hỏi: "Khi nào sinh viên VinUni phải đóng học phí?"
- Top-1 là `library#0` thay vì `tuition`
- Nguyên nhân: Cosine trên mock hash đo "giống chuỗi ký tự" không phải "giống nghĩa" → hash chuỗi query vô tình gần với hash của nội dung thư viện.
- Đề xuất: Embedder thật sẽ hiểu ngữ nghĩa của "đóng học phí".

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

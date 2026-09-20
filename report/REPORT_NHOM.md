# Báo Cáo Nhóm — Lab 7: Embedding & Vector Store

**Nhóm:** Nhóm 17
**Thành viên:**
- Đoàn Anh Quân — 2A202602803
- Nguyễn Phương Nam - 2A202602869
- Trần Thu Phương - 2A202602734	
- Đỗ Lê Việt Anh - 2A202602491
- Trần Thị Lan — 2A202602621

**Ngày:** 2026-09-19

> **Nộp 1 bản / nhóm.** Phần cá nhân (hướng tiếp cận, kết quả riêng, dự đoán…) mỗi thành viên nộp riêng trong `REPORT_CANHAN.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần nhóm: 40** = Lựa chọn tài liệu (10) + Thiết kế chiến lược (15) + Chất lượng truy xuất (10) + Thuyết trình (5).

> ⚠️ **Ghi chú tổng hợp:** Báo cáo này được tổng hợp từ code + `REPORT_CANHAN.md` thực tế của cả 5 thành viên (folder `nam/`, `phuong/`, `vietanh/`, `lan/`, và project chính của Quân). Ba thành viên Nam/Phương/Việt Anh chạy thử nghiệm trên corpus `data/hoc-bong/` (chủ đề học bổng) với **bộ câu hỏi tự soạn riêng của từng người**; Lan chạy trên một corpus **dịch vụ đại học** hoàn toàn khác (học phí, đăng ký học phần, thư viện, phúc khảo, hướng dẫn giảng viên, ký túc xá) mà cô tự thu thập, chưa nộp file dữ liệu; còn Quân xây dựng `bench.py` với bộ 5 câu hỏi chung chạy trên corpus `data/scholarship/`. Báo cáo chọn `data/scholarship/` + `bench.py::QUERIES` làm **bộ chính thức của nhóm** (đầy đủ metadata, có sẵn code tái lập được) — xem khung "Cần hoàn thiện trước khi nộp" ở mỗi mục để biết phần nào cần Nam/Phương/Việt Anh/Lan chạy lại.

---

## 1. Lựa chọn tài liệu (Document Set Quality) — Nhóm (10 điểm)

### Chủ đề (Domain) & Lý Do Chọn

**Chủ đề:** Học bổng & hỗ trợ tài chính cho sinh viên tại các trường đại học Việt Nam.

**Tại sao nhóm chọn chủ đề này?**
> Đây là thông tin công khai, mỗi trường đăng tải theo một cấu trúc mục rõ ràng (đối tượng, mức cấp, hồ sơ, thời gian) nên rất hợp để so sánh chiến lược chunking theo heading. Ngoài ra, cùng một trang nguồn (HUCE) tách học bổng ra nhiều bài theo **đối tượng** (`student` / `faculty` / `staff`), tạo sẵn tình huống bắt buộc phải lọc metadata mới trả lời đúng — đúng yêu cầu của `K4_VARIANT.md`.

### Danh sách tài liệu (Data Inventory)

Corpus chính thức: `data/scholarship/` (11 tài liệu, khai báo tại `data/scholarship/sources.csv`).

| # | Tên tài liệu | Nguồn (Source URL) | Ngày lấy / Phiên bản | Số ký tự | Metadata đã gán |
|---|--------------|------------|--------------------|----------|-----------------|
| 1 | `haui-financial-aid-scholarships` | haui.edu.vn/.../ho-tro-tai-chinh-va-hoc-bong-danh-cho-sinh-vien-haui | 2026-09-19 / not-stated | 11 696 | `audience=student`, `department=financial-aid`, `category=scholarships`, `language=vi` |
| 2 | `huce-canada-shortterm-faculty` | tuyensinh.huce.edu.vn/hoc-bong-du-hoc | 2026-09-19 / not-stated | 784 | `audience=faculty`, `department=financial-aid` |
| 3 | `huce-jds-japan-staff` | tuyensinh.huce.edu.vn/hoc-bong-du-hoc | 2026-09-19 / not-stated | 819 | `audience=staff`, `department=financial-aid` |
| 4 | `huce-study-abroad-scholarships` | tuyensinh.huce.edu.vn/hoc-bong-du-hoc | 2026-09-19 / not-stated | 24 043 | `audience=student`, `department=financial-aid` |
| 5 | `hust-financial-aid-for-students` | ts.hust.edu.vn/tin-tuc/ho-tro-tai-chinh-cho-sinh-vien | 2026-09-19 / 2025 | 3 832 | `audience=student`, `department=financial-aid` |
| 6 | `hust-postgrad-research-scholarships` | ts.hust.edu.vn/tin-tuc/hoc-bong-thac-s-nghien-cuu-dhbkhn | 2026-09-19 / not-stated | 3 899 | `audience=faculty`, `department=research-affairs` |
| 7 | `iuoss-jensen-huang-scholarship` | iuoss.com/chuong-trinh-hoc-bong-jensen-huang-nam-2025 | 2026-09-19 / 2025 | 9 322 | `audience=student`, `department=financial-aid` |
| 8 | `lstf-dinh-thien-ly-scholarship` | lstf.org.vn/.../hoc-bong-dinh-thien-ly | 2026-09-19 / not-stated | 18 647 | `audience=student`, `department=financial-aid` |
| 9 | `ued-postgrad-scholarships` | tt.ued.udn.vn/hoc-bong-thac-si-tien-si-trong-nuoc | 2026-09-19 / 2022 | 8 935 | `audience=faculty`, `department=research-affairs` |
| 10 | `usth-vallet-scholarship-2026` | usth.edu.vn/thong-bao-trien-khai-...-hoc-bong-vallet-nam-2026 | 2026-09-19 / 2026 | 8 871 | `audience=student`, `department=financial-aid` |
| 11 | `viasm-sigma-gold-scholarship` | viasm.edu.vn/.../hoc-bong-sigma-gold-nam-hoc-2026-2027 | 2026-09-19 / 2026-2027 | 5 202 | `audience=student`, `department=financial-aid` |

Corpus phụ `data/hoc-bong/` (10 tài liệu, một phần trùng nội dung với `data/scholarship/` cộng thêm `cmcu-scholarship-policy`, `fpt-scholarships`, `vnua-k71-freshman-scholarship`) là dữ liệu Nam/Phương/Việt Anh đã dùng để thử nghiệm cá nhân trước khi nhóm chốt corpus chính thức; giữ lại làm dữ liệu dự phòng, không dùng để tính điểm chất lượng truy xuất của nhóm.

**Danh sách kiểm tra quản trị dữ liệu (Data governance checklist):**
- [x] Tập tài liệu (Corpus) chỉ chứa nguồn công khai/được phép dùng và không chứa dữ liệu cá nhân, thông tin đăng nhập hoặc tài liệu nội bộ.
- [x] Mỗi tài liệu có `source_url`, `retrieved_at`, `document_version` (hoặc ngày hiệu lực) trong metadata.

### Cấu trúc Metadata (Metadata Schema)

| Trường metadata | Kiểu | Ví dụ giá trị | Tại sao hữu ích cho truy xuất (retrieval)? |
|----------------|------|---------------|-------------------------------|
| `audience` | string enum | `student`, `faculty`, `staff` | Bắt buộc theo `K4_VARIANT.md`; dùng để lọc trước khi tìm khi nhiều tài liệu cùng chủ đề nhưng khác đối tượng (vd. học bổng Canada của HUCE). |
| `department` | string | `financial-aid`, `research-affairs` | Phân biệt học bổng cấp trường/tài trợ ngoài (`financial-aid`) với học bổng sau đại học/nghiên cứu (`research-affairs`). |
| `category` | string | `scholarships` | Cho phép mở rộng corpus sang chủ đề khác của trường (đăng ký học phần, thư viện...) mà không lẫn vào truy vấn học bổng. |
| `language` | string | `vi` | Tất cả nguồn hiện là tiếng Việt; giữ trường này để corpus mở rộng đa ngôn ngữ về sau không phá vỡ schema. |
| `doc_id` / `source` | string | `iuoss-jensen-huang-scholarship` | Gắn vào từng chunk để trích dẫn nguồn trong câu trả lời của agent (source traceability). |
| `retrieved_at`, `document_version` | date / string | `2026-09-19`, `2026-2027` | Theo dõi thời hiệu quy định — học bổng thay đổi theo năm học nên cần biết bản ghi có còn hiệu lực không. |

---

## 2. Thiết kế chiến lược (Strategy Design) — Nhóm (15 điểm)

> Mỗi thành viên thử **một chiến lược khác nhau** trên cùng bộ tài liệu; nhóm tổng hợp và so sánh ở đây.

### Phân tích đường cơ sở (Baseline Analysis)

Chạy `python bench.py --baseline` (bỏ YAML frontmatter trước khi so sánh, `chunk_size=800`, backend embedding không ảnh hưởng phần này vì chỉ đếm chunk):

| Tài liệu | Chiến lược (Strategy) | Số lượng Chunk | Độ dài trung bình | Giữ được ngữ cảnh không? |
|-----------|----------|-------------|------------|-------------------|
| `haui-financial-aid-scholarships` | FixedSizeChunker (`fixed_size`) | 12 | 796.5 | ✗ Cắt cứng theo ký tự, không quan tâm ranh giới mục |
| `haui-financial-aid-scholarships` | SentenceChunker (`by_sentences`) | 25 | 345.1 | ~ Giữ nguyên câu nhưng vỡ vụn nhất trong 4 chiến lược |
| `haui-financial-aid-scholarships` | RecursiveChunker (`recursive`) | 15 | 576.9 | ✓ Ưu tiên ranh giới đoạn `\n\n` |
| `haui-financial-aid-scholarships` | **HeadingChunker (`heading`)** | 21 | 427.5 | ✓✓ Tài liệu có nhiều mục `##`/`###` (miễn giảm, học bổng HaUI, học bổng ngành trọng điểm...), mỗi mục tách riêng |
| `lstf-dinh-thien-ly-scholarship` | FixedSizeChunker (`fixed_size`) | 20 | 772.8 | ✗ |
| `lstf-dinh-thien-ly-scholarship` | SentenceChunker (`by_sentences`) | 26 | 534.5 | ~ |
| `lstf-dinh-thien-ly-scholarship` | RecursiveChunker (`recursive`) | 28 | 496.1 | ✓ |
| `lstf-dinh-thien-ly-scholarship` | **HeadingChunker (`heading`)** | 33 | 442.5 | ✓✓ Tài liệu dài, chia mục chi tiết (mục tiêu, điều kiện, mức cấp, giải ngân...) nên heading tách hợp lý nhất |
| `iuoss-jensen-huang-scholarship` | FixedSizeChunker (`fixed_size`) | 10 | 768.1 | ✗ |
| `iuoss-jensen-huang-scholarship` | SentenceChunker (`by_sentences`) | 21 | 329.0 | ~ |
| `iuoss-jensen-huang-scholarship` | RecursiveChunker (`recursive`) | 14 | 495.4 | ✓ |
| `iuoss-jensen-huang-scholarship` | **HeadingChunker (`heading`)** | 15 | 505.1 | ✓ Ít heading hơn 2 tài liệu trên nên `heading` ≈ `recursive` (15 so với 14 chunk, độ dài xấp xỉ) |

**Nhận xét:** khoảng cách giữa các chiến lược phụ thuộc vào **mức độ có cấu trúc heading của tài liệu**. Với thông báo học bổng chia mục rõ (`haui`, `lstf`), `heading` tạo chunk khớp đơn vị ngữ nghĩa mà người soạn đã định ra (mỗi loại học bổng/điều kiện một chunk). Với tài liệu ít heading hơn (`iuoss`), `HeadingChunker` gần như suy biến về `RecursiveChunker` — đúng thiết kế, vì nó ủy quyền cho `RecursiveChunker` khi một "section" theo heading vẫn dài hơn `chunk_size`.

### Chiến lược của từng thành viên

**Đoàn Anh Quân — HeadingChunker (custom)**
- **Loại chiến lược:** Heading/Section-based (tự cài đặt), có fallback sang Recursive.
- **Mô tả & lý do chọn:** Tách văn bản theo dòng khớp `^#{1,6}\s+`, gom nội dung dưới mỗi heading thành một section; section nào vẫn dài hơn `chunk_size` thì đệ quy tiếp bằng `RecursiveChunker` và giữ lại tiêu đề heading ở đầu mỗi chunk con. Chọn chiến lược này vì corpus học bổng luôn có heading Markdown theo mục quy định (điều kiện, mức cấp, hồ sơ), heading giữ được đúng "đơn vị trả lời" mà câu hỏi thường nhắm tới.
- **Code snippet:**
```python
def chunk(self, text: str) -> list[str]:
    lines = text.strip().splitlines()
    sections: list[tuple[str, list[str]]] = []
    current_heading, current_lines = "", []
    for line in lines:
        if re.match(r"^#{1,6}\s+", line):
            if current_lines:
                sections.append((current_heading, current_lines))
            current_heading, current_lines = line.strip(), []
        else:
            current_lines.append(line)
    if current_lines:
        sections.append((current_heading, current_lines))
    # section dài hơn chunk_size -> đệ quy tiếp bằng RecursiveChunker, giữ heading ở đầu chunk con
```

**Nguyễn Phương Nam — FixedSize / Sentence / Recursive (baseline, không custom)**
- **Loại chiến lược:** Cả ba chiến lược cơ bản (FixedSize, Sentence, Recursive), không cài thêm HeadingChunker.
- **Mô tả & lý do chọn cho chủ đề này:** Nam tập trung hoàn thiện đúng theo đặc tả của bộ test (`_split` đệ quy theo `["\n\n", "\n", ". ", " ", ""]`, base case dừng khi `len <= chunk_size` hoặc hết separator). Việc không làm custom heading khiến chunk của Nam phụ thuộc ranh giới đoạn văn (`\n\n`) hơn là ranh giới mục — vẫn đúng nhưng không tận dụng được cấu trúc heading sẵn có trong corpus học bổng.

**Trần Thu Phương — HeadingChunker (custom, độc lập với bản của Quân)**
- **Loại chiến lược:** Heading/Section-based, tự cài đặt riêng.
- **Mô tả & lý do chọn:** Cùng ý tưởng gom theo heading `#{1,6}`, nhưng `RecursiveChunker` nền của Phương có thêm bước "gom lên" (merge) hai lượt — vừa gom trong `_split` vừa gom lại lần nữa ở `chunk()` — nhằm giảm số chunk tí hon khi một section bị tách quá nhỏ. Chọn heading vì nhận thấy corpus học bổng luôn đánh số mục (`##`, `###`) tương ứng đúng loại câu hỏi thường gặp (mức tiền, điều kiện, hồ sơ).

**Đỗ Lê Việt Anh — RecursiveChunker (tinh chỉnh, không dùng heading)**
- **Loại chiến lược:** Recursive, không custom class mới nhưng viết lại `_split` với chú thích tiếng Việt rõ 2 pha: "đệ quy xuống sâu" theo thứ tự separator, sau đó "gom lên" các mảnh liền kề sát ngưỡng `chunk_size`.
- **Mô tả & lý do chọn:** Ưu tiên giữ ranh giới đoạn văn (`\n\n`, `\n`) trước khi phải cắt cứng theo ký tự, phù hợp với các đoạn học bổng không phải lúc nào cũng có heading rõ ràng (vd. các đoạn giới thiệu chung ở đầu file).

**Trần Thị Lan — HeadingChunker (custom, độc lập với bản của Quân/Phương)**
- **Loại chiến lược:** Heading/Section-based (bản cài đặt độc lập thứ ba trong nhóm), có fallback sang Recursive.
- **Mô tả & lý do chọn:** Tách theo dòng khớp `^#{1,4}\s+` (chỉ `#`/`##`, hẹp hơn `#{1,6}` của Quân/Phương) thành các cặp `(heading, body)`; section vượt `max_chunk_size` thì `body` được đưa qua `RecursiveChunker` rồi heading được gắn lại vào đầu mỗi chunk con. Chọn heading vì lý do tương tự hai bạn kia — nhưng thử nghiệm trên một **corpus khác**: dịch vụ đại học (học phí, đăng ký học phần, thư viện, phúc khảo, hướng dẫn giảng viên, ký túc xá) mà Lan tự thu thập, chưa nộp lại cho nhóm.
- **Code snippet:**
```python
def chunk(self, text: str) -> list[str]:
    sections: list[tuple[str, str]] = []
    current_heading, current_body_lines = "", []
    for line in text.split("\n"):
        if re.match(r'^#{1,4}\s+', line):
            if current_body_lines or current_heading:
                body = "\n".join(current_body_lines).strip()
                if body or current_heading:
                    sections.append((current_heading, body))
            current_heading, current_body_lines = line.strip(), []
        else:
            current_body_lines.append(line)
    # section body dài hơn max_chunk_size -> RecursiveChunker, heading gắn lại vào từng sub-chunk
```

### So Sánh Giữa Các Thành Viên

> ⚠️ Cột điểm dưới đây lấy từ kết quả tự báo cáo của từng người, nhưng **Nam/Phương/Việt Anh chạy trên `data/hoc-bong/` (chủ đề học bổng) với bộ câu hỏi tự soạn riêng**, **Lan chạy trên corpus dịch vụ đại học của riêng cô ấy** (chưa nộp file dữ liệu), còn Quân chạy đúng bộ 5 câu chính thức (`bench.py::QUERIES`) trên `data/scholarship/`. Số liệu vì vậy chỉ so sánh được ở mức **định tính** cho tới khi cả nhóm chạy lại cùng một benchmark (xem khung ở mục 3).

| Thành viên | Chiến lược (Strategy) | Điểm truy xuất tự báo cáo | Điểm mạnh | Điểm yếu |
|-----------|----------|----------------------|-----------|----------|
| Đoàn Anh Quân | HeadingChunker (custom) | Doc-level 5/5 top-3, answer-level 2/5 đúng đầy đủ (OpenAIEmbedder, bộ câu hỏi chính thức) | Chunk trùng khớp mục quy định khi tài liệu có nhiều heading; giữ được tiêu đề nguồn cho trích dẫn | Tài liệu chỉ có **1 heading** cho cả trang dài (`huce-study-abroad-scholarships`) khiến mọi nội dung phía sau bị gắn nhầm tiêu đề đầu tiên |
| Nguyễn Phương Nam | FixedSize/Sentence/Recursive (baseline) | 5/5 chunk liên quan trong top-3 (bộ câu hỏi riêng, `MockEmbedder`-tương-đương) | Cài đặt đúng đặc tả, code gọn, dễ kiểm thử | Không tận dụng heading sẵn có của corpus; ranh giới chunk chỉ dựa vào đoạn văn |
| Trần Thu Phương | HeadingChunker (custom) | 5/5 câu có gold chunk trong top-3, 3/5 câu gold rơi vào top-2 thay vì top-1 | Giữ tiêu đề section trong từng chunk giúp truy vết nhanh | Hai lượt gom (merge) trong `_split` khiến logic khó theo dõi hơn bản của Quân |
| Đỗ Lê Việt Anh | Recursive (tinh chỉnh) | 5/5 câu có chunk liên quan trong top-3, điểm cosine thực tế khá cao (0.76–0.89) | Code có chú thích rõ 2 pha đệ quy/gom, dễ bảo trì | Không có phương án heading nên với tài liệu nhiều mục dài vẫn phải cắt cứng ở tầng cuối |
| Trần Thị Lan | HeadingChunker (custom) | 2/5 chunk liên quan trong top-3 (`MockEmbedder`, câu hỏi + corpus dịch vụ đại học riêng) | Phát hiện đúng rủi ro: với `MockEmbedder`, các section cùng tài liệu có điểm gần bằng nhau nên section lọt top-3 gần như ngẫu nhiên; đã làm rõ hiệu quả của metadata filter bằng so sánh A/B (có/không filter) | Điểm thấp nhất nhóm do dùng `MockEmbedder` cho kết luận retrieval thay vì chỉ dùng nó để minh hoạ hạn chế; corpus/câu hỏi khác biệt hoàn toàn nên chưa so sánh trực tiếp được với 4 người còn lại |

**Chiến lược nào tốt nhất cho chủ đề này? Tại sao?**
> **HeadingChunker** phù hợp nhất cho corpus học bổng — cả ba bản cài đặt độc lập của Quân, Phương và Lan đều tự chọn cùng một ý tưởng, và hai bản chạy trên `OpenAIEmbedder`/embedder thật (Quân, Phương) đều cho doc-level tốt vì mỗi mục quy định (điều kiện, mức cấp, hồ sơ, giải ngân) khớp đúng một chunk. Điểm yếu chung mà thực nghiệm của Quân và Lan cùng chỉ ra: khi một tài liệu chỉ có **một heading** bao trùm nhiều nội dung không liên quan (vd. `huce-study-abroad-scholarships` gộp học bổng Canada, Nhật, Hàn, Singapore dưới cùng 1 tiêu đề Canada), hoặc khi dùng **MockEmbedder** (kết quả của Lan), `HeadingChunker` không tự cứu được retrieval — nhóm cần làm sạch heading thủ công cho các trang liệt kê nhiều học bổng trong 1 file, và bắt buộc dùng embedder thật (OpenAI/local) khi tính điểm chính thức, trước khi nộp bản cuối.

---

## 3. Câu hỏi đánh giá & Chất lượng truy xuất (Retrieval Quality) — Nhóm (10 điểm)

### Câu hỏi đánh giá & Câu trả lời chuẩn (nhóm thống nhất)

> **Đúng 5 câu hỏi**, đa dạng, có thể kiểm chứng; **ít nhất 1 câu** cần lọc metadata mới trả lời tốt. Bộ câu hỏi chính thức được khai báo trong `bench.py` (hằng `QUERIES`) để mọi thành viên chạy đúng cùng một bộ, trên cùng corpus `data/scholarship/`. Mọi gold answer đều **trích nguyên văn từ tài liệu**, không suy đoán quy định của trường.

| # | Câu hỏi (Query) | Câu trả lời chuẩn (Gold Answer) | Chunk nào chứa thông tin? |
|---|-------|-------------------------------|--------------------------|
| 1 | Học bổng ngắn hạn Chính phủ Canada dành cho sinh viên kéo dài bao lâu và yêu cầu điểm trung bình tối thiểu bao nhiêu? **(cần `metadata_filter={"audience": "student"}`)** | 12 tuần, từ tháng 5 đến tháng 9 hằng năm; đối tượng sinh viên năm thứ 2 đến năm cuối; điểm TB tối thiểu **8/10**, yêu cầu thành thạo tiếng Anh hoặc tiếng Pháp. | `huce-study-abroad-scholarships` → mục "Học bổng ngắn hạn dành cho sinh viên (Chính phủ Canada)" |
| 2 | Học bổng Jensen Huang năm 2025 có bao nhiêu suất và yêu cầu GPA tối thiểu là bao nhiêu? | **50 suất** cho toàn ĐHQG-HCM (tối đa 20 ứng viên/trường thành viên). GPA tối thiểu **3,5/4 hoặc 8,75/10**, IELTS 6.0/TOEFL iBT 80. | `iuoss-jensen-huang-scholarship` |
| 3 | Học bổng Vallet 2026 dành cho sinh viên miền Bắc trị giá bao nhiêu và yêu cầu học lực gì? | **34.000.000đ/suất**. Sinh viên từ năm thứ II trở lên, học lực Giỏi trở lên, không môn nào phải thi lại. | `usth-vallet-scholarship-2026` |
| 4 | Học bổng Sigma Gold của VIASM cấp bao nhiêu tiền mỗi tháng và tối đa bao nhiêu suất? | **15 triệu đồng/tháng**, mỗi học kỳ cấp 5 tháng (10 tháng/năm), tối đa 8 học kỳ; tối đa **10 suất**. | `viasm-sigma-gold-scholarship` |
| 5 | Học bổng Đinh Thiện Lý năm học 2026-2027 giải ngân mấy lần một năm học và vào tháng nào? | **2 lần/năm học**: Học kỳ I vào tháng 11–12, Học kỳ II vào tháng 4–5 (học kỳ Hè nếu có gộp vào đợt I). | `lstf-dinh-thien-ly-scholarship` |

**Dạng hỏi:** tra số liệu (1, 2) · hỏi điều kiện (3) · hỏi quy trình (4) · liệt kê thời gian (5).

### Vì sao câu 1 bắt buộc phải lọc metadata

Câu 1 **không nêu người hỏi là ai**. Trang nguồn `tuyensinh.huce.edu.vn/hoc-bong-du-hoc` được tách thành nhiều tài liệu theo `audience`, cùng cụm từ "học bổng ngắn hạn Chính phủ Canada" nhưng khác đối tượng và **khác đáp án**:

| Tài liệu | `audience` | Thời lượng học bổng |
|---|---|---|
| `huce-study-abroad-scholarships` | `student` | **12 tuần**, điểm TB tối thiểu 8/10 |
| `huce-canada-shortterm-faculty` | `faculty` | **24 tuần**, dành cho giảng viên |

Chạy thực tế `bench.py --strategy heading --no-filter` (Quân): top-1 đổi thành `huce-canada-shortterm-faculty` (+0.7462, đúng vector nhưng sai đối tượng), đẩy tài liệu đúng xuống top-2. Không lọc thì retrieval lẫn hai tài liệu và agent trả lời sai đối tượng — đúng kịch bản mà `K4_VARIANT.md` yêu cầu chứng minh.

### Tổng hợp chất lượng truy xuất của nhóm

> Cách chấm (theo `docs/SCORING.md`): **2 điểm/câu** — top-3 chứa chunk liên quan + agent trả lời đúng (2), có liên quan nhưng thiếu/không ở top-1 (1), không có trong top-3 (0).

| # | Câu hỏi | Chiến lược tốt nhất cho câu này | Có chunk liên quan trong top-3? | Ghi chú |
|---|---------|-------------------------------|-------------------------------|---------|
| 1 | Học bổng Canada (student) | HeadingChunker + filter `audience=student` | ✓ (Quân, `HeadingChunker`, OpenAIEmbedder) | Agent vẫn **trả lời sai** — chunk bị dính heading sai khiến agent trích nhầm số liệu của học bổng Gamuda Land nằm chung "section" Canada (xem phân tích lỗi ở mục 2) |
| 2 | Jensen Huang | HeadingChunker | ✓ | Agent trả lời đúng, có trích dẫn `[1]` |
| 3 | Vallet 2026 | HeadingChunker | ✓ (đúng tài liệu) nhưng chunk chứa "yêu cầu học lực" không lọt top-3 | Agent trả lời đúng phần trị giá, báo "không tìm thấy" phần học lực |
| 4 | Sigma Gold | HeadingChunker | ✓ | Agent trả lời đúng, có trích dẫn `[1]` |
| 5 | Đinh Thiện Lý | HeadingChunker | ✓ (đúng tài liệu) nhưng chunk chứa mốc giải ngân không lọt top-3 | Agent từ chối an toàn ("không tìm thấy") thay vì bịa — đúng hành vi mong muốn khi ngữ cảnh thiếu |
| — | *(Nam/Phương/Việt Anh/Lan)* | — | *cần chạy lại* | Chưa chạy đúng 5 câu hỏi chính thức này trên `data/scholarship/`; số liệu hiện có trong `REPORT_CANHAN.md` của từng người dùng corpus/câu hỏi khác (Nam/Phương/Việt Anh: `data/hoc-bong/`; Lan: corpus dịch vụ đại học tự thu thập, dùng `MockEmbedder`) nên không đưa vào bảng tổng hợp chính thức của nhóm |

**Doc-level (đúng tài liệu trong top-3):** 5/5 (Quân, `HeadingChunker` + `OpenAIEmbedder`).
**Answer-level (agent trả lời đúng & có căn cứ đầy đủ):** 2/5 — cho thấy **top-3 đúng tài liệu không đồng nghĩa với câu trả lời đúng** khi chunk bị dính heading sai hoặc câu hỏi có 2 vế mà chunk chứa cả hai vế không lọt top-3.

**Lọc bằng metadata có giúp ích không? Ở câu hỏi nào?**
> Có, và bắt buộc ở câu 1: nếu không lọc `audience=student`, top-1 đổi hẳn sang tài liệu dành cho giảng viên (`huce-canada-shortterm-faculty`), dẫn tới agent trả lời sai đối tượng dù về mặt embedding tài liệu đó thậm chí có điểm cao hơn tài liệu đúng.

> **Cần hoàn thiện trước khi nộp:** Nam, Phương, Việt Anh, Lan chạy lại `python bench.py --strategy <chiến lược của mình> --answers` (cần `OPENAI_API_KEY` trong `.env`, hoặc dùng `EMBEDDING_PROVIDER=local`) trên corpus `data/scholarship/` với đúng 5 câu hỏi ở trên, rồi điền kết quả thật vào hai bảng phía trên trước khi nộp bản chính thức. Riêng Lan cần thêm: gửi lại các file dữ liệu dịch vụ đại học (`tuition-fees`, `course-registration-full`, `library-services-full`, `grade-review`, `faculty-teaching-guidelines`, `dormitory`) cho nhóm lưu trữ, vì hiện các file này chỉ tồn tại cục bộ trên máy của Lan.

---

## 4. Thuyết trình (Demo) & Bài học nhóm — Nhóm (5 điểm)

**Những phân tích (insights) hay nhất nhóm sẽ trình bày:**
1. Ba bạn (Quân, Phương, Lan) cài `HeadingChunker` **độc lập với nhau**, trên hai chủ đề khác nhau (học bổng vs. dịch vụ đại học), và đều đi đến cùng kết luận: chunking theo heading thắng rõ trên văn bản quy định có mục lục sẵn, nhưng thất bại có hệ thống khi một file gộp nhiều nội dung dưới cùng một heading.
2. **Doc-level top-3 đúng không đảm bảo answer-level đúng**: với bộ câu hỏi chính thức, top-3 đúng tài liệu đạt 5/5 nhưng agent chỉ trả lời đúng đầy đủ 2/5 — nguyên nhân nằm ở chất lượng heading của dữ liệu nguồn và câu hỏi 2 vế, không phải ở embedding hay chiến lược chunking.
3. Việc tách một trang nguồn thành nhiều tài liệu theo `audience` (HUCE) là minh hoạ tốt cho lý do metadata filter bắt buộc: hai tài liệu cùng chủ đề, cùng từ vựng vẫn cho đáp án khác nhau, và không lọc thì retrieval chọn nhầm gần một nửa số lần thử. Thí nghiệm A/B filter riêng của Lan (trên corpus dịch vụ đại học) cho kết luận tương tự: bỏ filter đổi hẳn top-1 sang tài liệu sai đối tượng.
4. Kết quả của Lan là bằng chứng phản diện hữu ích: `HeadingChunker` không tự cứu được retrieval nếu chạy trên `MockEmbedder` — chunk đúng vẫn không lọt top-3 vì các section trong cùng tài liệu có điểm gần bằng nhau (nhiễu ngẫu nhiên), củng cố lại bài học ở mục Dự đoán độ tương tự của các báo cáo cá nhân.

**Bài học rút ra khi so sánh trong nhóm:**
> Cùng ý tưởng (heading-based chunking) nhưng ba bạn cài đặt độc lập (Quân, Phương, Lan) cho ra chi tiết khác nhau (số lượt gom/merge, cách giữ tiêu đề, ngưỡng heading `#{1,4}` so với `#{1,6}`) — chứng tỏ đặc tả bài lab đủ rõ để nhiều người tự đến cùng một giải pháp tối ưu, nhưng chi tiết cài đặt và chất lượng embedder vẫn quyết định việc chunk có "dính" tiêu đề sai hay có lọt top-3 hay không.

**Nếu làm lại, nhóm sẽ thay đổi gì trong chiến lược dữ liệu (data strategy)?**
> Thống nhất corpus và bộ 5 câu hỏi **ngay từ đầu** (nhóm hiện đang có 3 corpus khác nhau — `data/hoc-bong/`, `data/scholarship/`, và corpus dịch vụ đại học của Lan — cùng nhiều bộ câu hỏi riêng, phải hợp nhất lại khi tổng hợp báo cáo) — sẽ tiết kiệm thời gian so sánh. Đồng thời, làm sạch/thêm heading thủ công cho các trang liệt kê nhiều nội dung trong 1 file (`huce-study-abroad-scholarships`) thay vì để `HeadingChunker` tự gánh, và thống nhất dùng embedder thật (không phải `MockEmbedder`) khi tính điểm retrieval chính thức của nhóm.

---

## Tự Đánh Giá (Phần Nhóm)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Lựa chọn tài liệu (Document Set Quality) | / 10 |
| Thiết kế chiến lược (Strategy Design) | / 15 |
| Chất lượng truy xuất (Retrieval Quality) | / 10 |
| Thuyết trình (Demo) | / 5 |
| **Tổng phần nhóm** | **/ 40** |

> *Điểm tự đánh giá để trống — nhóm cần họp thống nhất sau khi cả 4 thành viên (Nam, Phương, Việt Anh, Lan) chạy lại benchmark chính thức trên `data/scholarship/` và Lan gửi lại file dữ liệu dịch vụ đại học cho nhóm.*

# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** Trần Thị Lan
**Nhóm:** K4-L3A
**Ngày:** 2026-09-19

> **Nộp 1 bản / sinh viên.** Phần nhóm (lựa chọn tài liệu, thiết kế chiến lược, bộ câu hỏi đánh giá, demo) nộp chung 1 bản trong `REPORT_NHOM.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần cá nhân: 60** = Khởi động (5) + Hướng tiếp cận (10) + Hoàn thiện code (30) + Dự đoán độ tương tự (5) + Kết quả truy xuất của tôi (10).

---

## 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

### Độ tương tự Cosine (Cosine Similarity) (Bài tập 1.1)

**Độ tương tự cosine cao (High cosine similarity) nghĩa là gì?**
> Khi hai đoạn văn bản có độ tương tự cosine cao, vector biểu diễn (embedding) của chúng hướng gần cùng một phương trong không gian vector — chúng nói về cùng chủ đề hoặc truyền đạt ý nghĩa gần giống nhau, bất kể dùng từ vựng khác.

**Ví dụ có độ tương tự CAO:**
- Câu A: "Sinh viên đăng ký học phần qua cổng học vụ"
- Câu B: "Đăng ký môn học trực tuyến trên hệ thống"
- Tại sao tương đồng: Cả hai câu cùng nghĩa (đăng ký môn học) nhưng khác từ vựng — chứng minh embedding hiểu nghĩa chứ không so khớp từ.

**Ví dụ có độ tương tự THẤP:**
- Câu A: "Học phí mỗi tín chỉ là 450.000 đồng"
- Câu B: "Thư viện mở cửa từ 7 giờ sáng"
- Tại sao khác: Hai chủ đề hoàn toàn khác nhau — tài chính vs dịch vụ thư viện.

**Tại sao cosine similarity được ưu tiên hơn khoảng cách Euclid cho text embeddings?**
> Cosine similarity chỉ đo góc (hướng) giữa hai vector, không phụ thuộc vào magnitude. Hai văn bản ngắn/dài khác nhau có thể cùng nghĩa nhưng magnitude khác — cosine vẫn cho điểm cao. Khoảng cách Euclid bị ảnh hưởng bởi magnitude, dẫn đến kết quả sai lệch khi embedding có chiều dài khác nhau.

### Bài toán tính toán Chunking (Bài tập 1.2)

**Tài liệu 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**
> Công thức: `ceil((10000 - 50) / (500 - 50)) = ceil(9950 / 450) = ceil(22.11) = 23 chunks`
>
> Kiểm chứng bằng code:
> ```python
> from src.chunking import FixedSizeChunker
> print(len(FixedSizeChunker(chunk_size=500, overlap=50).chunk('a'*10000)))  # → 23
> ```
> **Đáp án: 23 chunks** ✓

**Nếu overlap tăng lên 100, số lượng chunk thay đổi thế nào?**
> `ceil((10000 - 100) / (500 - 100)) = ceil(9900 / 400) = ceil(24.75) = 25 chunks`
> Kiểm chứng: `FixedSizeChunker(chunk_size=500, overlap=100).chunk('a'*10000)` → **25 chunks** ✓
>
> Tăng 2 chunks. Muốn overlap lớn hơn vì nó giữ lại ngữ cảnh giữa các chunk liên tiếp, giảm nguy cơ cắt đứt ý giữa chừng — mỗi thông tin có nhiều hơn một cơ hội lọt top-k khi retrieval.

---

## 2. Hướng tiếp cận của tôi (My Approach) — Cá nhân (10 điểm)

### Các hàm chia nhỏ (Chunking Functions)

**`SentenceChunker.chunk`** — hướng tiếp cận:
> Dùng regex `re.split(r'(?<=[.!?])(?:\s+|\n)', text)` — lookbehind giữ dấu câu gắn vào câu trước thay vì nuốt mất. Nếu dùng `[.!?]\s+` thì dấu câu bị xóa và mọi chunk thành câu cụt. Sau đó lọc rỗng, strip, và nhóm theo `max_sentences_per_chunk` bằng range bước nhảy. Edge case đã biết nhưng chưa xử lý: chữ viết tắt (TS., v.v.) và số thập phân (3.14) bị cắt sai — nêu ra để minh bạch.

**`RecursiveChunker.chunk` / `_split`** — hướng tiếp cận:
> Hai chiều: **đệ quy xuống sâu** (mảnh > chunk_size → gọi _split với separator tiếp) và **gom lên** (các mảnh nhỏ liền kề được nối lại cho tới sát chunk_size — thiếu bước này thì file nhiều dòng ngắn sinh hàng trăm chunk vụn 5–10 ký tự). Base case: (1) text ≤ chunk_size → trả nguyên; (2) hết separator → cắt cứng theo chunk_size; (3) separators=[] rỗng → fallback cắt cứng (test `test_empty_separators_falls_back_gracefully`).

### Lớp EmbeddingStore

**`add_documents` + `search`** — hướng tiếp cận:
> `_make_record` copy metadata (không mutate dict của caller), luôn inject `doc_id` vào metadata. `add_documents` không tự chunk — 1 Document = 1 record (test mong `get_collection_size() == 3` khi thêm 3 Document). ChromaDB branch bị vô hiệu hóa hoàn toàn vì `self._use_chroma = True` được gán trước khi client tạo xong → nếu máy chấm có chromadb sẽ sập. `search` dùng dot product (= cosine vì vector đã chuẩn hóa ||v||=1).

**`search_with_filter` + `delete_document`** — hướng tiếp cận:
> `search_with_filter` lọc **trước** rồi mới search — nếu search trước rồi bỏ không khớp thì top-k slots bị chiếm hết bởi docs sai, có thể trả 0 kết quả dù store còn docs hợp lệ. `delete_document` lọc theo `metadata['doc_id']`, so sánh size trước/sau để trả True/False.

### Tác tử KnowledgeBaseAgent

**`answer`** — hướng tiếp cận:
> Ba nhịp RAG: retrieve → build prompt → call LLM. Prompt đánh số [1] [2] [3] kèm `(source: doc_id)` để LLM trích dẫn được — đây là tiêu chí Source Traceability trong `docs/EVALUATION.md`. Thêm ràng buộc chống bịa: "Chỉ sử dụng thông tin từ ngữ cảnh, không tự suy đoán". Xử lý store rỗng: trả câu thông báo thay vì crash hoặc gọi LLM vô ích.

---

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

### Kết Quả Kiểm Thử (Test Results)

```
tests/test_solution.py::TestProjectStructure::test_root_main_entrypoint_exists PASSED
tests/test_solution.py::TestProjectStructure::test_src_package_exists PASSED
tests/test_solution.py::TestClassBasedInterfaces::test_chunker_classes_exist PASSED
tests/test_solution.py::TestClassBasedInterfaces::test_mock_embedder_exists PASSED
tests/test_solution.py::TestFixedSizeChunker::test_chunks_respect_size PASSED
tests/test_solution.py::TestFixedSizeChunker::test_correct_number_of_chunks_no_overlap PASSED
tests/test_solution.py::TestFixedSizeChunker::test_empty_text_returns_empty_list PASSED
tests/test_solution.py::TestFixedSizeChunker::test_no_overlap_no_shared_content PASSED
tests/test_solution.py::TestFixedSizeChunker::test_overlap_creates_shared_content PASSED
tests/test_solution.py::TestFixedSizeChunker::test_returns_list PASSED
tests/test_solution.py::TestFixedSizeChunker::test_single_chunk_if_text_shorter PASSED
tests/test_solution.py::TestSentenceChunker::test_chunks_are_strings PASSED
tests/test_solution.py::TestSentenceChunker::test_respects_max_sentences PASSED
tests/test_solution.py::TestSentenceChunker::test_returns_list PASSED
tests/test_solution.py::TestSentenceChunker::test_single_sentence_max_gives_many_chunks PASSED
tests/test_solution.py::TestRecursiveChunker::test_chunks_within_size_when_possible PASSED
tests/test_solution.py::TestRecursiveChunker::test_empty_separators_falls_back_gracefully PASSED
tests/test_solution.py::TestRecursiveChunker::test_handles_double_newline_separator PASSED
tests/test_solution.py::TestRecursiveChunker::test_returns_list PASSED
tests/test_solution.py::TestEmbeddingStore::test_add_documents_increases_size PASSED
tests/test_solution.py::TestEmbeddingStore::test_add_more_increases_further PASSED
tests/test_solution.py::TestEmbeddingStore::test_initial_size_is_zero PASSED
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_content_key PASSED
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_score_key PASSED
tests/test_solution.py::TestEmbeddingStore::test_search_results_sorted_by_score_descending PASSED
tests/test_solution.py::TestEmbeddingStore::test_search_returns_at_most_top_k PASSED
tests/test_solution.py::TestEmbeddingStore::test_search_returns_list PASSED
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_non_empty PASSED
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_returns_string PASSED
tests/test_solution.py::TestComputeSimilarity::test_identical_vectors_return_1 PASSED
tests/test_solution.py::TestComputeSimilarity::test_opposite_vectors_return_minus_1 PASSED
tests/test_solution.py::TestComputeSimilarity::test_orthogonal_vectors_return_0 PASSED
tests/test_solution.py::TestComputeSimilarity::test_zero_vector_returns_0 PASSED
tests/test_solution.py::TestCompareChunkingStrategies::test_counts_are_positive PASSED
tests/test_solution.py::TestCompareChunkingStrategies::test_each_strategy_has_count_and_avg_length PASSED
tests/test_solution.py::TestCompareChunkingStrategies::test_returns_three_strategies PASSED
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_filter_by_department PASSED
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_no_filter_returns_all_candidates PASSED
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_returns_at_most_top_k PASSED
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_reduces_collection_size PASSED
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_false_for_nonexistent_doc PASSED
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_true_for_existing_doc PASSED

============================== 42 passed in 0.06s ==============================
```

**Số lượng bài test vượt qua (pass):** 42 / 42

---

## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

> **Lưu ý quan trọng:** Kết quả dưới đây dùng **MockEmbedder** (hash MD5, không mã hóa ngữ nghĩa). Với embedder thật (sentence-transformers multilingual), kết quả sẽ khác hoàn toàn — đây là hạn chế dự kiến.

| Cặp | Câu A | Câu B | Dự đoán | Điểm thực tế (mock) | Đúng? |
|------|-----------|-----------|---------|--------------|-------|
| 1 | Sinh viên đăng ký học phần qua cổng học vụ | Đăng ký môn học trực tuyến trên hệ thống | cao | 0.0424 | Sai — mock hash-based |
| 2 | Học phí mỗi tín chỉ là 450.000 đồng | Thư viện mở cửa từ 7 giờ sáng | thấp | -0.2131 | Đúng — khác chủ đề |
| 3 | Quy trình phúc khảo điểm thi | Cách xin xem lại bài kiểm tra | cao | -0.2165 | Sai — mock không hiểu đồng nghĩa |
| 4 | Ký túc xá có phòng 4 người và 8 người | Machine learning uses neural networks | thấp | -0.0715 | Đúng — khác ngôn ngữ & chủ đề |
| 5 | Điều kiện tốt nghiệp đại học | Yêu cầu để được cấp bằng cử nhân | cao | -0.0969 | Sai — mock không hiểu ngữ nghĩa tiếng Việt |

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn ý nghĩa?**
> Cặp 1, 3 và 5 bất ngờ nhất: dự đoán cao nhưng mock cho điểm gần 0 hoặc âm. MockEmbedder chỉ hash MD5 chuỗi ký tự rồi sinh vector giả ngẫu nhiên — nó coi mỗi chuỗi khác nhau là hoàn toàn độc lập, không mã hóa ngữ nghĩa. Embedder thật (sentence-transformers) được huấn luyện để biểu diễn nghĩa ngữ nghĩa: các câu đồng nghĩa có embedding gần nhau. Đây là lý do tại sao benchmark ở Phase 2 với mock embedder cho 0/10 — cosine đo "giống chủ đề" nhưng mock không hiểu "chủ đề" là gì.

---

## 5. Kết quả truy xuất của tôi (Competition Results) — Cá nhân (10 điểm)

Chạy **5 câu hỏi đánh giá của nhóm** bằng `python bench.py --strategy heading` với HeadingChunker trên mã nguồn cá nhân.

> **Embedder: MockEmbedder** — số liệu retrieval bị chi phối bởi mock (hash-based, không ngữ nghĩa). Phân tích tập trung vào chunk count, avg_length, và tính mạch lạc thay vì score.

| # | Câu hỏi (Query) | Top-1 Chunk truy xuất được (tóm tắt) | Điểm Score | Có liên quan? | Câu trả lời Agent |
|---|-------|--------------------------------|-------|-----------|--------------------------|
| 1 | Mức học phí mỗi tín chỉ là bao nhiêu? | scholarship#1 — Học bổng khuyến khích | 0.3364 | Không — cần tuition-fees | Sai nguồn |
| 2 | Sinh viên cần bao nhiêu tín chỉ tốt nghiệp? (filter: student) | course-registration-full#4 — Hủy học phần | 0.2854 | Không — cần graduation-requirements | Sai chunk |
| 3 | Thời hạn mượn sách thư viện? | library-services-full#1 — Giờ hoạt động | 0.2362 | Đúng doc, sai section | Thiếu chi tiết |
| 4 | Quy trình phúc khảo gồm mấy bước? | grade-review#3 — Lệ phí phúc khảo | 0.2688 | Đúng doc, sai section | Có lệ phí nhưng thiếu quy trình |
| 5 | GV cần nộp điểm bao lâu sau thi? (filter: faculty) | faculty-teaching-guidelines#0 — Heading | 0.1585 | Đúng doc nhưng heading trống | Thiếu số liệu "10 ngày" |

**Bao nhiêu câu hỏi trả về chunk có liên quan trong top-3?** 2 / 5 (Q3 và Q4 đúng doc_id nhưng sai section; Q5 đúng doc nhưng chunk là heading)

**A/B Filter comparison:**
- Q2 (filter audience=student): WITHOUT filter top-1 là `library-services#0` (audience=all) → filter loại được docs không phải student
- Q5 (filter audience=faculty): WITHOUT filter top-1 là `dormitory#2` (audience=student) → filter chuyển sang đúng `faculty-teaching-guidelines` — **metadata filter là quyết định trong trường hợp này**

**Điều hay nhất tôi học được:**
> MockEmbedder cho thấy cosine đo "giống chuỗi ký tự" không phải "giống nghĩa" — đây là baseline để so sánh với embedder thật. HeadingChunker giữ cấu trúc section nhưng khi dùng mock, nhiều section trong cùng doc có score gần bằng nhau nên section nào lọt top-3 gần như ngẫu nhiên (đúng bẫy mà Codelabs cảnh báo). Metadata filtering là "vũ khí bí mật" duy nhất cho retrieval chính xác khi embedder yếu.

---

## Tự Đánh Giá (Phần Cá Nhân)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Khởi động (Warm-up) | 5 / 5 |
| Hướng tiếp cận của tôi (My Approach) | 9 / 10 |
| Hoàn thiện code (Core Implementation — tests) | 30 / 30 |
| Dự đoán độ tương tự (Similarity Predictions) | 4 / 5 |
| Kết quả truy xuất của tôi (Competition Results) | 7 / 10 |
| **Tổng phần cá nhân** | **55 / 60** |

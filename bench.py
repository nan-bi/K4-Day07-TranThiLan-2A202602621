"""Run the shared scholarship retrieval benchmark."""

from __future__ import annotations

import re
import sys
from pathlib import Path

from src import Document, EmbeddingStore, HeadingChunker, _mock_embed


DATA_DIR = Path(__file__).parent / "data" / "hoc-bong"

# Change only this line when comparing a different chunking strategy.
CHUNKER = HeadingChunker(max_chunk_size=800)

QUERIES = [
    {
        "question": "Học bổng Sigma Gold có mức bao nhiêu mỗi tháng?",
        "gold": "15 triệu đồng/tháng.",
        "metadata_filter": None,
    },
    {
        "question": "Học bổng CMC Khai Phóng yêu cầu chứng chỉ tiếng Anh IELTS từ bao nhiêu?",
        "gold": "IELTS 7.5 trở lên hoặc tương đương.",
        "metadata_filter": None,
    },
    {
        "question": "Hồ sơ học bổng Sigma Gold cho sinh viên năm thứ nhất gồm những giấy tờ nào?",
        "gold": "Bản sao học bạ lớp 12 và bản sao giấy chứng nhận đạt giải nhất, nhì cấp tỉnh/thành phố trở lên ở cấp THPT; ngoài ra hồ sơ có thể kèm thành tích, chứng chỉ học thuật và bài luận toán học theo tài liệu.",
        "metadata_filter": None,
    },
    {
        "question": "Những đối tượng nào được miễn 100% học phí tại Đại học Công nghiệp Hà Nội?",
        "gold": "Sinh viên là người có công hoặc con của người có công; mồ côi cả cha và mẹ; người dân tộc thiểu số thuộc hộ nghèo/cận nghèo; hoặc người dân tộc thiểu số rất ít người ở vùng khó khăn/đặc biệt khó khăn.",
        "metadata_filter": None,
    },
    {
        "question": "Học bổng dành cho sinh viên ngành Toán được cấp theo tháng ở mức nào?",
        "gold": "Học bổng Sigma Gold dành cho sinh viên đại học chính quy ngành Toán, mức 15 triệu đồng/tháng.",
        "metadata_filter": {"audience": "student"},
    },
]


def parse_frontmatter(text: str) -> tuple[dict[str, str], str]:
    match = re.match(r"\A---\s*\n(.*?)\n---\s*\n?(.*)\Z", text, re.DOTALL)
    if not match:
        return {}, text

    metadata: dict[str, str] = {}
    for line in match.group(1).splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        metadata[key.strip()] = value.strip().strip('"').strip("'")
    return metadata, match.group(2).strip()


def load_documents() -> list[Document]:
    documents: list[Document] = []
    for path in sorted(DATA_DIR.glob("*.md")):
        metadata, content = parse_frontmatter(path.read_text(encoding="utf-8"))
        for index, chunk in enumerate(CHUNKER.chunk(content)):
            documents.append(
                Document(
                    id=f"{path.stem}#{index}",
                    content=chunk,
                    metadata={**metadata, "doc_id": path.stem, "chunk_index": index},
                )
            )
    return documents


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    documents = load_documents()
    store = EmbeddingStore(collection_name="scholarship_benchmark", embedding_fn=_mock_embed)
    store.add_documents(documents)
    print(f"Chunker: {CHUNKER.__class__.__name__}")
    print(f"Loaded {len(documents)} chunks from {len({doc.metadata['doc_id'] for doc in documents})} files")

    for index, query in enumerate(QUERIES, start=1):
        results = store.search_with_filter(
            query["question"], top_k=3, metadata_filter=query["metadata_filter"]
        )
        print(f"\n[{index}] {query['question']}")
        print(f"Gold: {query['gold']}")
        print(f"Filter: {query['metadata_filter'] or 'none'}")
        for rank, result in enumerate(results, start=1):
            print(
                f"  {rank}. score={result['score']:.4f} "
                f"doc_id={result['metadata'].get('doc_id')}"
            )
            print(f"     {result['content'][:220].replace(chr(10), ' ')}...")


if __name__ == "__main__":
    main()

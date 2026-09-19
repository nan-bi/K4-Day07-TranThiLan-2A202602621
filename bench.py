"""
bench.py — Benchmark script for Lab 7 Phase 2

Usage:
    python bench.py                          # default: HeadingChunker
    python bench.py --strategy recursive     # use RecursiveChunker
    python bench.py --strategy fixed         # use FixedSizeChunker
    python bench.py --strategy sentence      # use SentenceChunker

This script:
1. Reads .md files from data/university/, parses YAML frontmatter into metadata
2. Chunks the body (not frontmatter!) using the chosen strategy
3. Creates a Document per chunk: Document(id="file#i", content=chunk, metadata=frontmatter)
4. Loads into EmbeddingStore, runs 5 benchmark queries via search_with_filter()
5. Prints top-3 results with score, doc_id, and content preview
6. Runs A/B comparison: with filter vs without filter for metadata-dependent queries
"""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(override=False)

from src.chunking import (
    FixedSizeChunker,
    HeadingChunker,
    RecursiveChunker,
    SentenceChunker,
)
from src.embeddings import (
    EMBEDDING_PROVIDER_ENV,
    GeminiEmbedder,
    LocalEmbedder,
    OpenAIEmbedder,
    _mock_embed,
)
from src.models import Document
from src.store import EmbeddingStore
from src.agent import KnowledgeBaseAgent


# ─── Config ───────────────────────────────────────────────────────────

DATA_DIR = Path("data/university")

# 5 benchmark queries with gold answers (team-agreed)
# At least one requires metadata_filter={"audience": "student"}
BENCHMARK_QUERIES = [
    {
        "query": "Khi nào sinh viên VinUni phải đóng học phí?",
        "gold_answer": "Đóng thành hai đợt mỗi năm vào đầu các học kỳ chính (Học kỳ Mùa thu và Học kỳ Mùa xuân).",
        "gold_doc_id": "tuition",
        "gold_marker": "Mùa thu",
        "filter": None,
    },
    {
        "query": "Học bổng WIT dành cho ai và trị giá bao nhiêu?",
        "gold_answer": "Trị giá 5% học phí dành cho nữ giới theo đuổi lĩnh vực khoa học công nghệ.",
        "gold_doc_id": "scholarships",
        "gold_marker": "nữ giới",
        "filter": {"audience": "student"},
    },
    {
        "query": "Khu bếp chung ở KTX có những thiết bị gì?",
        "gold_answer": "Bếp điện, lò nướng và lò vi sóng.",
        "gold_doc_id": "dormitory",
        "gold_marker": "lò nướng",
        "filter": None,
    },
    {
        "query": "Thư viện có mở cửa buổi đêm không?",
        "gold_answer": "Thư viện có không gian học tập mở cửa 24/7 để phục vụ nhu cầu tự học ngoài giờ.",
        "gold_doc_id": "library",
        "gold_marker": "24/7",
        "filter": None,
    },
    {
        "query": "Phương thức xét tuyển chính của VinUni là gì?",
        "gold_answer": "Hình thức xét tuyển kết hợp (đánh giá hồ sơ học thuật, năng lực cá nhân, bài luận, phỏng vấn, chứng chỉ tiếng Anh).",
        "gold_doc_id": "admissions",
        "gold_marker": "phỏng vấn",
        "filter": {"audience": "faculty"},
    },
]


# ─── Helpers ──────────────────────────────────────────────────────────

def parse_frontmatter(text: str) -> tuple[dict, str]:
    """Parse YAML front matter from .md file. Returns (metadata_dict, body_text)."""
    if not text.startswith("---"):
        return {}, text

    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}, text

    meta = {}
    for line in parts[1].strip().split("\n"):
        if ":" in line:
            key, value = line.split(":", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            # Remove inline comments (e.g. "student  # student | faculty | ...")
            if "#" in value:
                value = value.split("#")[0].strip()
            meta[key] = value

    body = parts[2].strip()
    return meta, body


def get_chunker(strategy: str):
    """Return a chunker instance based on strategy name."""
    if strategy == "heading":
        return HeadingChunker(max_chunk_size=500)
    elif strategy == "recursive":
        return RecursiveChunker(chunk_size=300)
    elif strategy == "fixed":
        return FixedSizeChunker(chunk_size=300, overlap=50)
    elif strategy == "sentence":
        return SentenceChunker(max_sentences_per_chunk=3)
    else:
        raise ValueError(f"Unknown strategy: {strategy}")


def get_embedder():
    """Get the configured embedding backend."""
    provider = os.getenv(EMBEDDING_PROVIDER_ENV, "mock").strip().lower()
    if provider == "local":
        try:
            return LocalEmbedder()
        except Exception:
            pass
    elif provider == "openai":
        try:
            return OpenAIEmbedder()
        except Exception:
            pass
    elif provider == "gemini":
        try:
            return GeminiEmbedder()
        except Exception:
            pass
    return _mock_embed


# ─── Main ─────────────────────────────────────────────────────────────

def main():
    strategy = "heading"
    if "--strategy" in sys.argv:
        idx = sys.argv.index("--strategy")
        if idx + 1 < len(sys.argv):
            strategy = sys.argv[idx + 1]

    print(f"{'='*60}")
    print(f"Lab 7 Benchmark — Strategy: {strategy}")
    print(f"{'='*60}\n")

    # 1. Load and parse documents
    chunker = get_chunker(strategy)
    embedder = get_embedder()
    print(f"Chunker: {chunker.__class__.__name__}")
    print(f"Embedder: {getattr(embedder, '_backend_name', embedder.__class__.__name__)}\n")

    all_docs: list[Document] = []
    md_files = sorted(DATA_DIR.glob("*.md"))

    for path in md_files:
        text = path.read_text(encoding="utf-8")
        meta, body = parse_frontmatter(text)
        doc_id = meta.get("doc_id", path.stem)

        if not body.strip():
            print(f"  SKIP {path.name} — empty body")
            continue

        # 2. Chunk the BODY (not frontmatter!) — chunking happens outside store
        chunks = chunker.chunk(body)

        # 3. Each chunk becomes a separate Document
        #    id = "file#i" for each chunk, doc_id in metadata points to source file
        for i, chunk_text in enumerate(chunks):
            chunk_doc = Document(
                id=f"{doc_id}#{i}",
                content=chunk_text,
                metadata={**meta, "doc_id": doc_id},
            )
            all_docs.append(chunk_doc)

    print(f"Loaded {len(md_files)} files → {len(all_docs)} chunks\n")

    # 4. Load into EmbeddingStore
    store = EmbeddingStore("university_bench", embedding_fn=embedder)
    store.add_documents(all_docs)
    print(f"Store size: {store.get_collection_size()}\n")

    # 5. Run benchmark queries
    print(f"{'='*60}")
    print("BENCHMARK RESULTS")
    print(f"{'='*60}\n")

    total_score = 0

    for i, bq in enumerate(BENCHMARK_QUERIES, 1):
        query = bq["query"]
        gold_doc = bq["gold_doc_id"]
        gold_marker = bq["gold_marker"]
        filt = bq["filter"]

        print(f"Q{i}: {query}")
        if filt:
            print(f"    Filter: {filt}")

        # Run with filter
        if filt:
            results = store.search_with_filter(query, top_k=3, metadata_filter=filt)
        else:
            results = store.search(query, top_k=3)

        # Check results
        has_gold_in_top3 = False
        has_marker_in_top3 = False
        for j, r in enumerate(results[:3], 1):
            rid = r["metadata"].get("doc_id", "?")
            score = r["score"]
            preview = r["content"][:120].replace("\n", " ")
            is_gold = "✓" if rid == gold_doc else " "
            has_marker = gold_marker in r["content"]
            print(f"    [{j}] score={score:.4f} doc={rid} {is_gold} | {preview}...")
            if rid == gold_doc:
                has_gold_in_top3 = True
            if has_marker:
                has_marker_in_top3 = True

        # Two-level scoring per SCORING.md
        if has_gold_in_top3 and has_marker_in_top3:
            q_score = 2
            status = "FULL (2/2)"
        elif has_gold_in_top3:
            q_score = 1
            status = "PARTIAL (1/2) — doc found but marker missing"
        else:
            q_score = 0
            status = "MISS (0/2)"

        total_score += q_score
        print(f"    → {status}")
        print(f"    Gold: {bq['gold_answer'][:80]}...")
        print()

    print(f"{'='*60}")
    print(f"TOTAL SCORE: {total_score} / 10")
    print(f"{'='*60}\n")

    # 6. A/B comparison: with filter vs without filter
    print(f"{'='*60}")
    print("A/B COMPARISON: Filter vs No Filter")
    print(f"{'='*60}\n")

    for i, bq in enumerate(BENCHMARK_QUERIES, 1):
        if not bq["filter"]:
            continue

        query = bq["query"]
        filt = bq["filter"]

        results_no_filter = store.search(query, top_k=3)
        results_with_filter = store.search_with_filter(query, top_k=3, metadata_filter=filt)

        print(f"Q{i}: {query}")
        print(f"  WITHOUT filter:")
        for j, r in enumerate(results_no_filter[:3], 1):
            rid = r["metadata"].get("doc_id", "?")
            aud = r["metadata"].get("audience", "?")
            print(f"    [{j}] score={r['score']:.4f} doc={rid} audience={aud}")

        print(f"  WITH filter {filt}:")
        for j, r in enumerate(results_with_filter[:3], 1):
            rid = r["metadata"].get("doc_id", "?")
            aud = r["metadata"].get("audience", "?")
            print(f"    [{j}] score={r['score']:.4f} doc={rid} audience={aud}")

        # Compare
        no_filter_docs = {r["metadata"].get("doc_id") for r in results_no_filter[:3]}
        with_filter_docs = {r["metadata"].get("doc_id") for r in results_with_filter[:3]}
        same = "SAME" if no_filter_docs == with_filter_docs else "DIFFERENT"
        print(f"  → Results are {same}")
        print()

    # 7. Agent test
    print(f"{'='*60}")
    print("AGENT ANSWERS")
    print(f"{'='*60}\n")

    def demo_llm(prompt):
        return f"[DEMO LLM] {prompt[:300]}..."

    agent = KnowledgeBaseAgent(store=store, llm_fn=demo_llm)
    for i, bq in enumerate(BENCHMARK_QUERIES, 1):
        ans = agent.answer(bq["query"])
        print(f"Q{i}: {bq['query']}")
        print(f"A{i}: {ans[:150]}...")
        print()


if __name__ == "__main__":
    main()

from typing import Callable

from .store import EmbeddingStore


class KnowledgeBaseAgent:
    """
    An agent that answers questions using a vector knowledge base.

    Retrieval-augmented generation (RAG) pattern:
        1. Retrieve top-k relevant chunks from the store.
        2. Build a prompt with the chunks as context (numbered, with source).
        3. Call the LLM to generate an answer.
    """

    def __init__(self, store: EmbeddingStore, llm_fn: Callable[[str], str]) -> None:
        self.store = store
        self.llm_fn = llm_fn

    def answer(self, question: str, top_k: int = 3) -> str:
        # Step 1: Retrieve top-k relevant chunks from the store
        results = self.store.search(question, top_k=top_k)

        # Handle empty store — don't call LLM uselessly
        if not results:
            return "Không tìm thấy tài liệu liên quan trong cơ sở tri thức để trả lời câu hỏi này."

        # Step 2: Build a prompt with numbered chunks and source info
        # Number each chunk with [i] and include doc_id for traceability
        context_parts = []
        for i, result in enumerate(results, start=1):
            source = result["metadata"].get("doc_id", "unknown")
            context_parts.append(f"[{i}] (source: {source}) {result['content']}")

        context = "\n\n".join(context_parts)

        prompt = (
            "Dựa trên ngữ cảnh được cung cấp bên dưới, hãy trả lời câu hỏi. "
            "Chỉ sử dụng thông tin từ ngữ cảnh, không tự suy đoán. "
            "Khi trả lời, hãy trích dẫn số nguồn [1], [2], [3] tương ứng. "
            "Nếu ngữ cảnh không chứa đủ thông tin, hãy nói rõ là không tìm thấy.\n\n"
            f"Ngữ cảnh:\n{context}\n\n"
            f"Câu hỏi: {question}\n\n"
            "Trả lời:"
        )

        # Step 3: Call the LLM to generate an answer
        return self.llm_fn(prompt)

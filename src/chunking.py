from __future__ import annotations

import math
import re


class FixedSizeChunker:
    """
    Split text into fixed-size chunks with optional overlap.

    Rules:
        - Each chunk is at most chunk_size characters long.
        - Consecutive chunks share overlap characters.
        - The last chunk contains whatever remains.
        - If text is shorter than chunk_size, return [text].
    """

    def __init__(self, chunk_size: int = 500, overlap: int = 50) -> None:
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk(self, text: str) -> list[str]:
        if not text:
            return []
        if len(text) <= self.chunk_size:
            return [text]

        step = self.chunk_size - self.overlap
        chunks: list[str] = []
        for start in range(0, len(text), step):
            chunk = text[start : start + self.chunk_size]
            chunks.append(chunk)
            if start + self.chunk_size >= len(text):
                break
        return chunks


class SentenceChunker:
    """
    Split text into chunks of at most max_sentences_per_chunk sentences.

    Sentence detection: split on ". ", "! ", "? " or ".\n".
    Strip extra whitespace from each chunk.
    """

    def __init__(self, max_sentences_per_chunk: int = 3) -> None:
        self.max_sentences_per_chunk = max(1, max_sentences_per_chunk)

    def chunk(self, text: str) -> list[str]:
        if not text or not text.strip():
            return []

        # Split on sentence boundaries: ". ", "! ", "? ", or ".\n"
        # We use a regex that splits while keeping the delimiter attached to the preceding sentence.
        sentences = re.split(r'(?<=[.!?])(?:\s+|\n)', text)

        # Filter out empty strings and strip whitespace
        sentences = [s.strip() for s in sentences if s.strip()]

        if not sentences:
            return []

        # Group sentences into chunks
        chunks: list[str] = []
        for i in range(0, len(sentences), self.max_sentences_per_chunk):
            group = sentences[i : i + self.max_sentences_per_chunk]
            chunk_text = " ".join(group).strip()
            if chunk_text:
                chunks.append(chunk_text)

        return chunks


class RecursiveChunker:
    """
    Recursively split text using separators in priority order.

    Default separator priority:
        ["\\n\\n", "\\n", ". ", " ", ""]
    """

    DEFAULT_SEPARATORS = ["\n\n", "\n", ". ", " ", ""]

    def __init__(self, separators: list[str] | None = None, chunk_size: int = 500) -> None:
        self.separators = self.DEFAULT_SEPARATORS if separators is None else list(separators)
        self.chunk_size = chunk_size

    def chunk(self, text: str) -> list[str]:
        if not text:
            return []
        if len(text) <= self.chunk_size:
            return [text]
        return self._split(text, self.separators)

    def _split(self, current_text: str, remaining_separators: list[str]) -> list[str]:
        # Base case: text fits within chunk_size
        if len(current_text) <= self.chunk_size:
            return [current_text] if current_text else []

        # Base case: no separators left — force-split by character
        if not remaining_separators:
            chunks: list[str] = []
            for i in range(0, len(current_text), self.chunk_size):
                piece = current_text[i : i + self.chunk_size]
                if piece:
                    chunks.append(piece)
            return chunks

        separator = remaining_separators[0]
        next_separators = remaining_separators[1:]

        # If separator is empty string, split character-by-character (force split)
        if separator == "":
            chunks = []
            for i in range(0, len(current_text), self.chunk_size):
                piece = current_text[i : i + self.chunk_size]
                if piece:
                    chunks.append(piece)
            return chunks

        parts = current_text.split(separator)

        # If the separator didn't produce a split, try next separator
        if len(parts) <= 1:
            return self._split(current_text, next_separators)

        # Merge parts back together, keeping chunks under chunk_size
        chunks = []
        current_chunk = parts[0]

        for part in parts[1:]:
            # Check if adding this part (with separator) would exceed chunk_size
            candidate = current_chunk + separator + part
            if len(candidate) <= self.chunk_size:
                current_chunk = candidate
            else:
                # Save current chunk (recursively split if too large)
                if current_chunk:
                    if len(current_chunk) <= self.chunk_size:
                        chunks.append(current_chunk)
                    else:
                        chunks.extend(self._split(current_chunk, next_separators))
                current_chunk = part

        # Handle the last chunk
        if current_chunk:
            if len(current_chunk) <= self.chunk_size:
                chunks.append(current_chunk)
            else:
                chunks.extend(self._split(current_chunk, next_separators))

        return chunks


def _dot(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


def compute_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    """
    Compute cosine similarity between two vectors.

    cosine_similarity = dot(a, b) / (||a|| * ||b||)

    Returns 0.0 if either vector has zero magnitude.
    """
    dot_product = _dot(vec_a, vec_b)
    magnitude_a = math.sqrt(sum(x * x for x in vec_a))
    magnitude_b = math.sqrt(sum(x * x for x in vec_b))

    if magnitude_a == 0.0 or magnitude_b == 0.0:
        return 0.0

    return dot_product / (magnitude_a * magnitude_b)


class ChunkingStrategyComparator:
    """Run all built-in chunking strategies and compare their results."""

    def compare(self, text: str, chunk_size: int = 200) -> dict:
        # Run all three strategies
        fixed_chunker = FixedSizeChunker(chunk_size=chunk_size, overlap=50)
        sentence_chunker = SentenceChunker(max_sentences_per_chunk=3)
        recursive_chunker = RecursiveChunker(chunk_size=chunk_size)

        fixed_chunks = fixed_chunker.chunk(text)
        sentence_chunks = sentence_chunker.chunk(text)
        recursive_chunks = recursive_chunker.chunk(text)

        def compute_stats(chunks: list[str]) -> dict:
            count = len(chunks)
            avg_length = sum(len(c) for c in chunks) / count if count > 0 else 0.0
            return {
                "count": count,
                "avg_length": avg_length,
                "chunks": chunks,
            }

        return {
            "fixed_size": compute_stats(fixed_chunks),
            "by_sentences": compute_stats(sentence_chunks),
            "recursive": compute_stats(recursive_chunks),
        }


class HeadingChunker:
    """Split text by markdown headings (## or #), each section as one chunk.

    Design rationale: University regulation documents are structured by
    sections/articles (## Điều 4 — ...). Each section is a self-contained
    semantic unit already divided by the author. This chunker exploits that
    structure instead of cutting arbitrarily.

    When a section exceeds max_chunk_size, it is sub-split using
    RecursiveChunker, and the heading is prepended to each sub-chunk
    to preserve context.
    """

    def __init__(self, max_chunk_size: int = 500) -> None:
        self.max_chunk_size = max_chunk_size

    def chunk(self, text: str) -> list[str]:
        if not text or not text.strip():
            return []

        # Split on markdown headings (lines starting with # or ##)
        sections: list[tuple[str, str]] = []  # (heading, body)
        current_heading = ""
        current_body_lines: list[str] = []

        for line in text.split("\n"):
            if re.match(r'^#{1,4}\s+', line):
                # Save previous section
                if current_body_lines or current_heading:
                    body = "\n".join(current_body_lines).strip()
                    if body or current_heading:
                        sections.append((current_heading, body))
                current_heading = line.strip()
                current_body_lines = []
            else:
                current_body_lines.append(line)

        # Save last section
        body = "\n".join(current_body_lines).strip()
        if body or current_heading:
            sections.append((current_heading, body))

        # Build chunks, sub-splitting oversized sections
        chunks: list[str] = []
        recursive = RecursiveChunker(chunk_size=self.max_chunk_size)

        for heading, body in sections:
            if heading and body:
                section_text = f"{heading}\n\n{body}"
            elif heading:
                section_text = heading
            else:
                section_text = body

            if not section_text.strip():
                continue

            if len(section_text) <= self.max_chunk_size:
                chunks.append(section_text)
            else:
                # Sub-split long sections but prepend heading to each sub-chunk
                sub_chunks = recursive.chunk(body if body else section_text)
                for sub in sub_chunks:
                    if heading:
                        prefixed = f"{heading}\n\n{sub}"
                        chunks.append(prefixed)
                    else:
                        chunks.append(sub)

        return chunks if chunks else [text]

"""Text chunking with overlap, preserving page metadata."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterator


@dataclass
class TextChunk:
    chunk_id: str
    content: str
    page_number: int
    chunk_index: int
    char_start: int
    char_end: int
    document_id: str = ""
    document_name: str = ""
    content_type: str = "text"
    metadata: dict = field(default_factory=dict)


class TextChunker:
    """Split page text into overlapping chunks.

    Splits on paragraph boundaries first, then sentences, then hard character
    limits so chunks stay semantically coherent.
    """

    def __init__(self, chunk_size: int = 500, overlap: int = 80) -> None:
        if chunk_size <= 0:
            raise ValueError("chunk_size must be positive")
        if overlap < 0 or overlap >= chunk_size:
            raise ValueError("overlap must be >= 0 and < chunk_size")
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk_page(
        self, text: str, page_number: int, document_id: str, document_name: str
    ) -> list[TextChunk]:
        text = text.strip()
        if not text:
            return []
        pieces = self._split(text)
        chunks: list[TextChunk] = []
        pos = 0
        for piece in pieces:
            start = text.find(piece, pos)
            if start == -1:
                start = pos
            end = start + len(piece)
            pos = end
            chunk_id = f"{document_id}_p{page_number:04d}_c{len(chunks):04d}"
            chunks.append(
                TextChunk(
                    chunk_id=chunk_id,
                    content=piece,
                    page_number=page_number,
                    chunk_index=len(chunks),
                    char_start=start,
                    char_end=end,
                    document_id=document_id,
                    document_name=document_name,
                    metadata={
                        "document_id": document_id,
                        "document_name": document_name,
                        "page_number": page_number,
                        "content_type": "text",
                        "chunk_id": chunk_id,
                        "content": piece,
                        "source": document_name,
                    },
                )
            )
        return chunks

    def _split(self, text: str) -> list[str]:
        paragraphs = self._split_paragraphs(text)
        pieces: list[list[str]] = []
        current: list[str] = []
        current_len = 0
        for para in paragraphs:
            if not para:
                continue
            if len(para) > self.chunk_size:
                # flush current buffer first
                if current:
                    pieces.append(" ".join(current))
                    current, current_len = [], 0
                pieces.extend(self._hard_split(para))
                continue
            if current_len + len(para) + 1 > self.chunk_size and current:
                pieces.append(" ".join(current))
                # overlap: keep tail sentences of current buffer
                tail = self._overlap_tail(" ".join(current))
                current = [tail] if tail else []
                current_len = len(current[0]) if current else 0
            current.append(para)
            current_len += len(para) + 1
        if current:
            pieces.append(" ".join(current))
        return [p for p in pieces if p.strip()]

    def _split_paragraphs(self, text: str) -> list[str]:
        # Split on blank lines first
        blocks = [b.strip() for b in re.split(r"\n\s*\n", text) if b.strip()]
        out: list[str] = []
        for block in blocks:
            # Further split long single-line blocks on sentence boundaries
            if len(block) <= self.chunk_size:
                out.append(block)
            else:
                out.extend(self._split_sentences(block))
        return out

    def _split_sentences(self, text: str) -> list[str]:
        import re

        parts = re.split(r"(?<=[.!?])\s+", text)
        return [p for p in parts if p.strip()]

    def _hard_split(self, text: str) -> list[str]:
        """Force-split an over-long paragraph into chunk_size pieces with overlap."""
        out: list[str] = []
        step = self.chunk_size - self.overlap
        i = 0
        while i < len(text):
            piece = text[i : i + self.chunk_size]
            if piece.strip():
                out.append(piece.strip())
            i += step
        return out

    def _overlap_tail(self, text: str) -> str:
        if self.overlap <= 0:
            return ""
        tail = text[-self.overlap :]
        # try to start at a sentence boundary
        idx = tail.find(". ")
        if idx != -1:
            return tail[idx + 2 :]
        return tail


import re  # noqa: E402  (kept at bottom to avoid confusion; used by _split_paragraphs)

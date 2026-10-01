"""Tests for text chunking logic."""

from __future__ import annotations

from app.services.text_chunker import TextChunker


def test_chunk_page_basic():
    chunker = TextChunker(chunk_size=100, overlap=20)
    text = "This is a sentence. " * 10  # ~200 chars
    chunks = chunker.chunk_page(text, page_number=1, document_id="doc1", document_name="test.pdf")
    assert len(chunks) > 0
    for c in chunks:
        assert c.page_number == 1
        assert c.document_id == "doc1"
        assert c.content_type == "text"
        assert c.chunk_id.startswith("doc1_p0001")


def test_chunk_page_empty_text():
    chunker = TextChunker(chunk_size=100, overlap=20)
    assert chunker.chunk_page("", 1, "d", "n.pdf") == []
    assert chunker.chunk_page("   ", 1, "d", "n.pdf") == []


def test_chunk_respects_size():
    chunker = TextChunker(chunk_size=50, overlap=10)
    text = "word " * 100  # 500 chars
    chunks = chunker.chunk_page(text, 1, "d", "n.pdf")
    for c in chunks:
        assert len(c.content) <= 60  # small tolerance


def test_chunk_metadata_preserved():
    chunker = TextChunker(chunk_size=100, overlap=20)
    chunks = chunker.chunk_page("Some content here.", 3, "doc42", "paper.pdf")
    assert chunks[0].metadata["document_id"] == "doc42"
    assert chunks[0].metadata["document_name"] == "paper.pdf"
    assert chunks[0].metadata["page_number"] == 3
    assert chunks[0].metadata["source"] == "paper.pdf"


def test_invalid_params():
    import pytest

    with pytest.raises(ValueError):
        TextChunker(chunk_size=0)
    with pytest.raises(ValueError):
        TextChunker(chunk_size=100, overlap=100)
    with pytest.raises(ValueError):
        TextChunker(chunk_size=100, overlap=-5)

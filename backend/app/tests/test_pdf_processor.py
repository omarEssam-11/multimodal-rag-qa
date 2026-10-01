"""Tests for PDF processing: text extraction, image extraction, captions."""

from __future__ import annotations

import io

import pytest
from PIL import Image

from app.services.pdf_processor import PDFProcessingError, PDFProcessor


def test_process_extracts_text(sample_pdf_path):
    proc = PDFProcessor()
    result = proc.process(sample_pdf_path, "doc1", "sample.pdf")
    assert result.num_pages == 2
    assert len(result.pages) == 2
    assert "transformer" in result.pages[0].text.lower()
    assert result.pages[0].page_number == 1


def test_process_extracts_images(sample_pdf_path):
    proc = PDFProcessor()
    result = proc.process(sample_pdf_path, "doc1", "sample.pdf")
    assert len(result.images) >= 1
    img = result.images[0]
    assert img.page_number == 2
    assert img.image_path.exists()
    assert img.width == 120
    assert img.height == 80
    assert img.metadata["content_type"] == "image"


def test_process_caption_association(sample_pdf_path):
    proc = PDFProcessor()
    result = proc.process(sample_pdf_path, "doc1", "sample.pdf")
    # Page 2 has "Figure 1: The overall system diagram." which should be
    # associated with the image on that page
    assert len(result.images) >= 1
    img = result.images[0]
    assert img.caption is not None
    assert "Figure 1" in img.caption


def test_invalid_pdf(tmp_path):
    proc = PDFProcessor()
    bad = tmp_path / "bad.pdf"
    bad.write_bytes(b"this is not a pdf at all")
    with pytest.raises(PDFProcessingError):
        proc.process(bad, "d", "bad.pdf")


def test_blank_page_pdf(tmp_path):
    """A PDF with a single blank page (no extractable text) should process cleanly."""
    import fitz

    proc = PDFProcessor()
    blank = tmp_path / "blank.pdf"
    doc = fitz.open()
    doc.new_page()  # one blank page
    doc.save(str(blank))
    doc.close()
    result = proc.process(blank, "d", "blank.pdf")
    assert result.num_pages == 1
    assert result.pages[0].text.strip() == ""
    assert result.images == []


def test_missing_file(tmp_path):
    proc = PDFProcessor()
    with pytest.raises(PDFProcessingError):
        proc.process(tmp_path / "nope.pdf", "d", "nope.pdf")


def test_image_saved_to_disk(sample_pdf_path):
    proc = PDFProcessor()
    result = proc.process(sample_pdf_path, "docXYZ", "sample.pdf")
    for img in result.images:
        assert img.image_path.parent.name == "docXYZ"
        # verify it's a valid image
        pil = Image.open(img.image_path)
        assert pil.format in {"PNG", "JPEG", "WEBP", "GIF", "BMP"}

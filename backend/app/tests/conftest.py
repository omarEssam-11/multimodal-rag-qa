"""Shared pytest fixtures."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Ensure backend/ is on sys.path so `app` is importable
BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))


@pytest.fixture
def sample_pdf_path(tmp_path: Path) -> Path:
    """Generate a real PDF with text and an image using PyMuPDF."""
    import fitz

    pdf_path = tmp_path / "sample.pdf"
    doc = fitz.open()

    # Page 1: text
    page1 = doc.new_page()
    page1.insert_text((72, 72), "The transformer architecture uses self-attention.", fontsize=12)
    page1.insert_text((72, 100), "It consists of an encoder and a decoder.", fontsize=12)

    # Page 2: text + a simple image (draw a colored rectangle as an image)
    page2 = doc.new_page()
    page2.insert_text((72, 72), "Figure 1: The overall system diagram.", fontsize=12)
    page2.insert_text((72, 100), "The diagram shows the data flow.", fontsize=12)
    # embed a small PNG image
    import io
    from PIL import Image

    img = Image.new("RGB", (120, 80), color=(30, 120, 200))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    img_bytes = buf.getvalue()
    rect = fitz.Rect(72, 150, 72 + 120, 150 + 80)
    page2.insert_image(rect, stream=img_bytes)

    doc.save(str(pdf_path))
    doc.close()
    return pdf_path

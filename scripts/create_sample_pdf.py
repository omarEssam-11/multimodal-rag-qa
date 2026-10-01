"""Generate a sample PDF for testing Multimodal RAG QA.

Creates a multi-page PDF with text paragraphs, a figure (diagram),
a chart, and figure captions — perfect for demonstrating cross-modal
retrieval (e.g. asking "transformer architecture" retrieves the diagram).

Usage:
    python scripts/create_sample_pdf.py [output_path]
"""

from __future__ import annotations

import io
import sys
from pathlib import Path

import fitz  # PyMuPDF
from PIL import Image, ImageDraw


def make_diagram_image() -> bytes:
    """Draw a simple 'architecture diagram' (boxes + arrows)."""
    img = Image.new("RGB", (480, 320), "white")
    d = ImageDraw.Draw(img)
    # boxes
    d.rectangle([40, 40, 160, 100], fill=(200, 220, 255), outline="black", width=2)
    d.rectangle([180, 40, 300, 100], fill=(220, 255, 220), outline="black", width=2)
    d.rectangle([320, 40, 440, 100], fill=(255, 220, 220), outline="black", width=2)
    d.rectangle([180, 160, 300, 220], fill=(255, 240, 200), outline="black", width=2)
    # labels
    d.text((70, 65), "Encoder", fill="black")
    d.text((210, 65), "Attention", fill="black")
    d.text((350, 65), "Decoder", fill="black")
    d.text((200, 185), "Output", fill="black")
    # arrows
    d.line([160, 70, 180, 70], fill="black", width=2)
    d.line([300, 70, 320, 70], fill="black", width=2)
    d.line([380, 100, 380, 140], fill="black", width=2)
    d.line([380, 140, 240, 160], fill="black", width=2)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def make_chart_image() -> bytes:
    """Draw a simple bar chart."""
    img = Image.new("RGB", (400, 260), "white")
    d = ImageDraw.Draw(img)
    bars = [("Q1", 120, (70, 130, 200)), ("Q2", 180, (70, 180, 120)), ("Q3", 90, (200, 130, 70)), ("Q4", 220, (180, 70, 130))]
    for i, (label, h, color) in enumerate(bars):
        x = 50 + i * 85
        d.rectangle([x, 220 - h, x + 50, 220], fill=color, outline="black")
        d.text((x + 15, 228), label, fill="black")
    d.line([30, 220, 380, 220], fill="black", width=2)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def build_pdf(output: Path) -> None:
    doc = fitz.open()

    # Page 1: intro text
    p1 = doc.new_page()
    p1.insert_text((72, 72), "Multimodal RAG QA — Sample Document", fontsize=16)
    p1.insert_text((72, 110), "This document describes a transformer-based architecture for", fontsize=11)
    p1.insert_text((72, 128), "multimodal question answering. The system combines text and", fontsize=11)
    p1.insert_text((72, 146), "visual evidence to produce grounded answers.", fontsize=11)
    p1.insert_text((72, 180), "The architecture consists of an encoder, an attention mechanism,", fontsize=11)
    p1.insert_text((72, 198), "and a decoder. The encoder processes the input, the attention", fontsize=11)
    p1.insert_text((72, 216), "layer computes relevance weights, and the decoder generates output.", fontsize=11)

    # Page 2: architecture diagram + caption
    p2 = doc.new_page()
    p2.insert_text((72, 72), "2. System Architecture", fontsize=14)
    p2.insert_text((72, 100), "The figure below shows the overall system design.", fontsize=11)
    p2.insert_image(fitz.Rect(72, 130, 72 + 360, 130 + 240), stream=make_diagram_image())
    p2.insert_text((72, 400), "Figure 1: The overall system architecture showing encoder,", fontsize=10)
    p2.insert_text((72, 416), "attention, and decoder components.", fontsize=10)

    # Page 3: attention explanation + chart
    p3 = doc.new_page()
    p3.insert_text((72, 72), "3. Attention Mechanism", fontsize=14)
    p3.insert_text((72, 100), "The attention layer computes a weighted sum of values based", fontsize=11)
    p3.insert_text((72, 118), "on query-key similarity. This allows the model to focus on the", fontsize=11)
    p3.insert_text((72, 136), "most relevant parts of the input when producing each output token.", fontsize=11)
    p3.insert_text((72, 170), "Performance improved significantly after adding multi-head attention.", fontsize=11)
    p3.insert_image(fitz.Rect(72, 200, 72 + 300, 200 + 195), stream=make_chart_image())
    p3.insert_text((72, 420), "Figure 2: Quarterly accuracy after introducing multi-head attention.", fontsize=10)

    # Page 4: table-like text
    p4 = doc.new_page()
    p4.insert_text((72, 72), "4. Results", fontsize=14)
    p4.insert_text((72, 110), "Table 1: Model comparison on the test set.", fontsize=11)
    p4.insert_text((72, 140), "Model            | Accuracy | Latency", fontsize=11)
    p4.insert_text((72, 165), "Transformer      | 92.3%    | 45ms", fontsize=11)
    p4.insert_text((72, 190), "LSTM             | 85.1%    | 30ms", fontsize=11)
    p4.insert_text((72, 215), "CNN              | 78.4%    | 20ms", fontsize=11)
    p4.insert_text((72, 250), "The transformer achieves the highest accuracy, though with", fontsize=11)
    p4.insert_text((72, 268), "higher latency due to the attention computation.", fontsize=11)

    doc.save(str(output))
    doc.close()
    print(f"Sample PDF created: {output}")


if __name__ == "__main__":
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("data/uploads/sample.pdf")
    out.parent.mkdir(parents=True, exist_ok=True)
    build_pdf(out)

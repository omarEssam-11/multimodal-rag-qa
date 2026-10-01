"""Generate a sample query image for testing image-only / text+image queries.

Creates a diagram image similar to the one in the sample PDF, so you can
upload it and verify CLIP-based cross-modal retrieval finds the matching
figure in the indexed document.

Usage:
    python scripts/create_sample_query_image.py [output_path]
"""

from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image, ImageDraw


def make_query_image() -> bytes:
    img = Image.new("RGB", (480, 320), "white")
    d = ImageDraw.Draw(img)
    d.rectangle([40, 40, 160, 100], fill=(200, 220, 255), outline="black", width=2)
    d.rectangle([180, 40, 300, 100], fill=(220, 255, 220), outline="black", width=2)
    d.rectangle([320, 40, 440, 100], fill=(255, 220, 220), outline="black", width=2)
    d.rectangle([180, 160, 300, 220], fill=(255, 240, 200), outline="black", width=2)
    d.text((70, 65), "Encoder", fill="black")
    d.text((210, 65), "Attention", fill="black")
    d.text((350, 65), "Decoder", fill="black")
    d.text((200, 185), "Output", fill="black")
    d.line([160, 70, 180, 70], fill="black", width=2)
    d.line([300, 70, 320, 70], fill="black", width=2)
    d.line([380, 100, 380, 140], fill="black", width=2)
    d.line([380, 140, 240, 160], fill="black", width=2)
    import io

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


if __name__ == "__main__":
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("data/sample_query.png")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(make_query_image())
    print(f"Sample query image created: {out}")

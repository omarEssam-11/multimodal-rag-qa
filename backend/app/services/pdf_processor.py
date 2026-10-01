"""PDF processing: text extraction, image extraction, caption association."""

from __future__ import annotations

import io
import re
from dataclasses import dataclass, field
from pathlib import Path

import fitz  # PyMuPDF
from PIL import Image

from app.config import settings
from app.utils.logger import get_logger
from app.utils.security import safe_image_path

logger = get_logger(__name__)

# Caption patterns: "Figure 1: ...", "Fig. 2 ...", "Table 3 ..."
_CAPTION_RE = re.compile(
    r"^\s*(?:(figure|fig\.?|table|tab\.?)\s*(\d+))\s*[:.\-–]?\s*(.*)$",
    re.IGNORECASE,
)


class PDFProcessingError(Exception):
    pass


@dataclass
class ExtractedImage:
    image_id: str
    page_number: int
    image_path: Path
    ext: str
    width: int
    height: int
    caption: str | None = None
    caption_page: int | None = None
    metadata: dict = field(default_factory=dict)


@dataclass
class PageText:
    page_number: int
    text: str
    word_count: int


@dataclass
class ProcessedDocument:
    document_id: str
    document_name: str
    num_pages: int
    pages: list[PageText]
    images: list[ExtractedImage]
    full_text: str


class PDFProcessor:
    """Extract text (page-by-page) and images from a PDF using PyMuPDF."""

    MIN_IMAGE_SIZE = 64  # ignore tiny embedded images (icons, bullets)

    def __init__(self, min_image_size: int | None = None) -> None:
        self.min_image_size = min_image_size or self.MIN_IMAGE_SIZE

    def process(self, pdf_path: Path, document_id: str, document_name: str) -> ProcessedDocument:
        if not pdf_path.exists():
            raise PDFProcessingError(f"File not found: {pdf_path}")
        try:
            doc = fitz.open(str(pdf_path))
        except Exception as e:
            raise PDFProcessingError(f"Cannot open PDF (corrupted or invalid): {e}") from e

        if doc.is_encrypted:
            # try empty password
            if not doc.authenticate(""):
                doc.close()
                raise PDFProcessingError("PDF is password-protected")

        if doc.page_count == 0:
            doc.close()
            raise PDFProcessingError("PDF has no pages")

        if doc.page_count > settings.allowed_pdf_max_pages:
            doc.close()
            raise PDFProcessingError(
                f"PDF has {doc.page_count} pages, exceeding limit of {settings.allowed_pdf_max_pages}"
            )

        pages: list[PageText] = []
        images: list[ExtractedImage] = []

        for page_idx in range(doc.page_count):
            page = doc.load_page(page_idx)
            page_number = page_idx + 1
            text = page.get_text("text")
            pages.append(
                PageText(
                    page_number=page_number,
                    text=text,
                    word_count=len(text.split()),
                )
            )
            page_images = self._extract_page_images(
                page, page_number, document_id, document_name
            )
            images.extend(page_images)

        # Associate captions with images
        self._associate_captions(pages, images)

        full_text = "\n\n".join(p.text for p in pages)
        doc.close()

        logger.info(
            "PDF processed: %s | pages=%d | images=%d | words=%d",
            document_name,
            len(pages),
            len(images),
            sum(p.word_count for p in pages),
        )
        return ProcessedDocument(
            document_id=document_id,
            document_name=document_name,
            num_pages=len(pages),
            pages=pages,
            images=images,
            full_text=full_text,
        )

    def _extract_page_images(
        self, page: fitz.Page, page_number: int, document_id: str, document_name: str
    ) -> list[ExtractedImage]:
        out: list[ExtractedImage] = []
        seen_hashes: set[str] = set()
        try:
            image_list = page.get_images(full=True)
        except Exception:
            return out

        for img_idx, img in enumerate(image_list):
            xref = img[0]
            try:
                base = page.parent.extract_image(xref)
            except Exception:
                continue
            if base is None:
                continue
            ext = base["ext"]
            data = base["image"]
            width = base.get("width", 0)
            height = base.get("height", 0)

            if width < self.min_image_size or height < self.min_image_size:
                continue

            # dedupe identical images on the same page
            import hashlib

            h = hashlib.md5(data).hexdigest()
            if h in seen_hashes:
                continue
            seen_hashes.add(h)

            image_id = f"{document_id}_p{page_number:04d}_i{img_idx:03d}"
            try:
                out_path = safe_image_path(document_id, image_id, ext)
                out_path.parent.mkdir(parents=True, exist_ok=True)
                out_path.write_bytes(data)
            except Exception as e:
                logger.warning("Failed to save image %s: %s", image_id, e)
                continue

            out.append(
                ExtractedImage(
                    image_id=image_id,
                    page_number=page_number,
                    image_path=out_path,
                    ext=ext,
                    width=width,
                    height=height,
                    metadata={
                        "document_id": document_id,
                        "document_name": document_name,
                        "page_number": page_number,
                        "content_type": "image",
                        "image_id": image_id,
                        "image_path": str(out_path),
                        "source": document_name,
                    },
                )
            )
        return out

    def _associate_captions(self, pages: list[PageText], images: list[ExtractedImage]) -> None:
        """Find caption lines near images and attach them to the image metadata."""
        if not images:
            return
        page_map = {p.page_number: p.text for p in pages}

        for img in images:
            page_text = page_map.get(img.page_number, "")
            lines = page_text.splitlines()
            caption = None
            # search lines for a caption pattern; prefer captions after the image
            for i, line in enumerate(lines):
                m = _CAPTION_RE.match(line)
                if m:
                    label, number, rest = m.group(1), m.group(2), m.group(3).strip()
                    # caption text may continue on following lines
                    caption_text = rest
                    j = i + 1
                    while j < len(lines) and j < i + 4 and not _CAPTION_RE.match(lines[j]):
                        nxt = lines[j].strip()
                        if nxt and not nxt[0].isupper() or (nxt and len(nxt) < 200):
                            caption_text += " " + nxt
                        else:
                            break
                        j += 1
                    caption = f"{label.capitalize()} {number}: {caption_text}".strip()
                    break
            if caption:
                img.caption = caption
                img.caption_page = img.page_number
                img.metadata["caption"] = caption
